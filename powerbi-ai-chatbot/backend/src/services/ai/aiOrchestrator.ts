import {
  AiPlan,
  ChatResponse,
  ConversationState,
  QueryFilter,
  QueryPlan,
  UserContext,
} from '../../models/types';
import { MetadataService, metadataService } from '../semanticmodel/metadataService';
import { QueryValidator, queryValidator } from '../../validators/queryValidator';
import { getPowerBiClient } from '../powerbi/powerbiClient';
import { modelRegistry, ModelRegistry } from '../semanticmodel/modelRegistry';
import { VisualSpecService, visualSpecService } from '../visualization/visualSpecService';
import { ConversationStore, conversationStore } from '../conversation/conversationStore';
import { AiClient, AiUnavailableError, getAiClient } from './openaiClient';

export interface ChatRequest {
  user: UserContext;
  modelId: string;
  prompt: string;
  conversationId?: string;
}

/**
 * The controlled AI orchestration pipeline (Guide §14 / Phase 7):
 *
 *   prompt -> intent -> field selection -> query plan -> VALIDATE -> execute
 *          -> result -> visual spec -> typed response
 *
 * The LLM only proposes a plan. This class enforces validation, executes only
 * validated plans, maintains server-side conversation state, and shapes the
 * typed response. It never trusts the LLM for authorization or state.
 */
export class AiOrchestrator {
  constructor(
    private readonly deps: {
      registry: ModelRegistry;
      metadata: MetadataService;
      validator: QueryValidator;
      visuals: VisualSpecService;
      conversations: ConversationStore;
      ai: () => AiClient;
    } = {
      registry: modelRegistry,
      metadata: metadataService,
      validator: queryValidator,
      visuals: visualSpecService,
      conversations: conversationStore,
      ai: getAiClient,
    },
  ) {}

  async handleChat(req: ChatRequest): Promise<ChatResponse> {
    const { user, prompt } = req;

    // Authorization + existence are enforced here: getMetadata throws
    // ModelNotFoundError / ModelUnauthorizedError, which the controller maps to
    // 404 / 403 (Guide §25). Metadata is only ever returned for models the user
    // is authorized to use.
    const metadata = await this.deps.metadata.getMetadata(user, req.modelId);
    const convo = this.deps.conversations.getOrCreate(user.userId, req.conversationId, req.modelId);

    let plan: AiPlan;
    try {
      plan = await this.deps.ai().plan({
        prompt,
        metadata,
        priorFilters: convo.lastFilters,
        hasPriorResult: Boolean(convo.lastResult),
        lastVisualType: convo.lastVisual?.type,
      });
    } catch (err) {
      if (err instanceof AiUnavailableError) {
        return {
          conversationId: convo.conversationId,
          status: 'error',
          intent: 'unavailable',
          message: 'The AI service is temporarily unavailable.',
        };
      }
      throw err;
    }

    switch (plan.intent) {
      case 'clarification_needed':
        return {
          conversationId: convo.conversationId,
          status: 'clarification',
          intent: plan.intent,
          message: plan.clarification ?? 'Could you clarify your request?',
          clarification: plan.clarification,
        };

      case 'unavailable':
        return {
          conversationId: convo.conversationId,
          status: 'unavailable',
          intent: plan.intent,
          message: plan.unavailableReason ?? 'That data element is not available in the selected model.',
        };

      case 'modify_visual':
        return this.handleModifyVisual(convo, plan);

      default:
        return this.handleDataOrVisual(user, convo, metadata.modelId, plan);
    }
  }

  /** Change chart type without re-querying when we already have a result (Phase 10). */
  private handleModifyVisual(convo: ConversationState, plan: AiPlan): ChatResponse {
    if (!convo.lastResult || !convo.lastVisual) {
      return {
        conversationId: convo.conversationId,
        status: 'clarification',
        intent: 'clarification_needed',
        message: 'There is no existing chart to modify yet. What would you like to see?',
      };
    }
    const newType = plan.visual?.type ?? convo.lastVisual.type;
    const visual = this.deps.visuals.changeType(convo.lastVisual, newType);
    this.deps.conversations.setVisual(convo.conversationId, visual);
    return {
      conversationId: convo.conversationId,
      status: 'visual',
      intent: 'modify_visual',
      message: `Updated the chart to a ${visual.type} chart.`,
      visual,
      result: convo.lastResult,
    };
  }

  /** Validate + execute a data/visual request and build the typed response. */
  private async handleDataOrVisual(
    user: UserContext,
    convo: ConversationState,
    modelId: string,
    plan: AiPlan,
  ): Promise<ChatResponse> {
    // Compose the effective plan. change_filter merges the new filter into the
    // previous plan and re-queries; add_measure/create_visual use the AI plan.
    const effectivePlan = this.composePlan(convo, modelId, plan);
    if (!effectivePlan) {
      return {
        conversationId: convo.conversationId,
        status: 'clarification',
        intent: 'clarification_needed',
        message: 'Could you clarify what you would like to see?',
      };
    }

    const metadata = await this.deps.metadata.getMetadata(user, modelId);
    const validation = this.deps.validator.validate(effectivePlan, metadata);
    if (!validation.valid || !validation.normalizedPlan) {
      const first = validation.issues[0];
      const message =
        first?.code === 'unknown_field' || first?.code === 'unknown_measure'
          ? 'That field/measure is not available in the selected model.'
          : first?.message ?? 'The query could not be validated.';
      return {
        conversationId: convo.conversationId,
        status: 'unavailable',
        intent: 'unavailable',
        message,
      };
    }

    const entry = this.deps.registry.get(modelId)!;
    const result = await getPowerBiClient().executeQuery(entry, validation.normalizedPlan);
    this.deps.conversations.setResult(
      convo.conversationId,
      validation.normalizedPlan,
      result,
      validation.normalizedPlan.filters,
    );

    // Only build a visual when the user wanted one (create_visual / add_measure
    // / change_filter that carried a prior visual).
    const wantsVisual =
      plan.intent === 'create_visual' ||
      plan.intent === 'add_measure' ||
      plan.intent === 'change_filter' ||
      Boolean(plan.visual);

    if (wantsVisual) {
      const visual = this.deps.visuals.build(validation.normalizedPlan, result, plan.visual ?? convo.lastVisual);
      this.deps.conversations.setVisual(convo.conversationId, visual);
      return {
        conversationId: convo.conversationId,
        status: 'visual',
        intent: plan.intent,
        message: this.describeResult(result, visual.title),
        visual,
        result,
      };
    }

    // Pure data answer (KPI-style).
    return {
      conversationId: convo.conversationId,
      status: 'answer',
      intent: plan.intent,
      message: this.describeAnswer(result),
      result,
    };
  }

  /**
   * Build the plan to execute from the AI proposal + prior state. Handles
   * follow-ups that reuse the previous grouping/measures.
   */
  private composePlan(convo: ConversationState, modelId: string, plan: AiPlan): QueryPlan | undefined {
    const prior = convo.lastQueryPlan;

    if (plan.intent === 'change_filter') {
      if (!prior) return plan.queryPlan; // no prior context, use the AI plan as-is
      const newFilters = mergeFilters(prior.filters, plan.queryPlan?.filters ?? []);
      return { ...prior, modelId, filters: newFilters };
    }

    if (plan.intent === 'add_measure' && prior) {
      const added = plan.queryPlan?.measures ?? [];
      const measures = Array.from(new Set([...prior.measures, ...added]));
      return { ...prior, modelId, measures };
    }

    if (plan.queryPlan) {
      return { ...plan.queryPlan, modelId };
    }
    return undefined;
  }

  private describeResult(result: { rowCount: number; truncated: boolean }, title: string): string {
    const base = `Here is "${title}" (${result.rowCount} row${result.rowCount === 1 ? '' : 's'}).`;
    return result.truncated ? `${base} Results were limited to protect performance.` : base;
  }

  private describeAnswer(result: {
    columns: Array<{ name: string; role: string }>;
    rows: Array<Array<string | number | boolean | null>>;
    rowCount: number;
  }): string {
    if (result.rowCount === 0) return 'No data matched the selected filters.';
    const measureCols = result.columns.filter((c) => c.role === 'measure');
    if (result.rowCount === 1 && measureCols.length >= 1) {
      const idx = result.columns.findIndex((c) => c.name === measureCols[0].name);
      const value = result.rows[0][idx];
      return `${measureCols[0].name}: ${formatValue(value)}.`;
    }
    return `Returned ${result.rowCount} rows.`;
  }

}

function mergeFilters(existing: QueryFilter[], incoming: QueryFilter[]): QueryFilter[] {
  const byField = new Map<string, QueryFilter>();
  for (const f of existing) byField.set(f.field.toLowerCase(), f);
  for (const f of incoming) byField.set(f.field.toLowerCase(), f); // incoming overrides same field
  return [...byField.values()];
}

function formatValue(value: string | number | boolean | null): string {
  if (typeof value === 'number') return value.toLocaleString('en-US');
  return String(value);
}

export const aiOrchestrator = new AiOrchestrator();
