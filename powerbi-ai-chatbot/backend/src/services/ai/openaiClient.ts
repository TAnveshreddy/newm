import { getConfig } from '../../config';
import { AiPlan, QueryFilter, SemanticModelMetadata, VisualType } from '../../models/types';
import { CORE_SYSTEM_PROMPT, metadataToPromptContext } from './systemPrompt';

export interface PlanRequest {
  prompt: string;
  metadata: SemanticModelMetadata;
  /** Prior filters for follow-up handling. */
  priorFilters?: QueryFilter[];
  hasPriorResult: boolean;
  lastVisualType?: string;
}

/**
 * Wraps the LLM used to turn a natural-language prompt into a structured plan.
 * The model NEVER executes queries — it only proposes an AiPlan that the
 * backend validates and executes.
 */
export interface AiClient {
  plan(req: PlanRequest): Promise<AiPlan>;
}

/* -------------------------------------------------------------------------- */

/**
 * Deterministic rules-based planner used in mock mode. It reproduces the
 * behavior the Core Rules require for the example scenarios (Guide §26) without
 * a live model, so the end-to-end pipeline is testable and runnable offline.
 */
export class MockAiClient implements AiClient {
  async plan(req: PlanRequest): Promise<AiPlan> {
    const text = req.prompt.toLowerCase();
    const { metadata } = req;

    const measures = allMeasures(metadata);
    const dimensions = allDimensions(metadata);

    // 1. Follow-up: change chart type only (no re-query).
    const chartType = detectChartType(text);
    if (req.hasPriorResult && /change|switch|make it|turn it into|as a/.test(text) && chartType) {
      return { intent: 'modify_visual', visual: { type: chartType, title: '', measures: [] }, reuseLastResult: true };
    }

    // 2. Detect an explicitly named field that does not exist -> unavailable.
    const unavailable = detectUnavailableField(text, metadata);
    if (unavailable) {
      return {
        intent: 'unavailable',
        unavailableReason: `"${unavailable}" is not available in the ${metadata.displayName} model. ` +
          `Available measures include: ${measures.map((m) => m.name).slice(0, 6).join(', ')}.`,
      };
    }

    // 3. Resolve measures mentioned in the prompt (fall back to first measure).
    const matchedMeasures = matchByName(text, measures.map((m) => m.name));
    const matchedDimension = matchByName(text, dimensions.map((d) => d.canonical), dimensions.map((d) => d.short))[0];

    // 4. Filter-only follow-up (e.g. "only 2026", "only show APAC").
    const filter = detectFilter(text, metadata);
    if (req.hasPriorResult && /^(only|filter|just|show only)\b/.test(text.trim()) && filter) {
      return {
        intent: 'change_filter',
        queryPlan: {
          modelId: metadata.modelId,
          groupBy: [],
          measures: [],
          filters: [filter],
        },
        reuseLastResult: false,
      };
    }

    // 5. Ambiguity: no measure and no dimension recognizable.
    if (matchedMeasures.length === 0 && !matchedDimension && !filter) {
      return {
        intent: 'clarification_needed',
        clarification:
          'Which measure would you like to see (for example ' +
          `${measures.slice(0, 3).map((m) => m.name).join(', ')})?`,
      };
    }

    const chosenMeasures = matchedMeasures.length > 0 ? matchedMeasures : [measures[0].name];
    const wantsVisual = /chart|graph|plot|visual|bar|line|column|pie|donut|trend|by /.test(text);
    const groupBy = matchedDimension ? [matchedDimension] : [];
    const filters = filter ? [filter] : [];

    const queryPlan = {
      modelId: metadata.modelId,
      groupBy,
      measures: chosenMeasures,
      filters,
    };

    if (wantsVisual || groupBy.length > 0) {
      const type = chartType ?? (groupBy.length > 0 ? 'bar' : 'kpi');
      return {
        intent: 'create_visual',
        queryPlan,
        visual: { type, title: '', category: groupBy[0], measures: chosenMeasures },
      };
    }

    // Pure data question (KPI-style single value).
    return { intent: 'data_question', queryPlan };
  }
}

/* -------------------------------------------------------------------------- */

/**
 * Live Azure OpenAI client. Sends the core system prompt + whitelisted
 * metadata + user prompt and parses the JSON plan. Auth uses either an API key
 * (if configured) or a bearer token from managed identity (integration point).
 */
export class AzureOpenAiClient implements AiClient {
  async plan(req: PlanRequest): Promise<AiPlan> {
    const cfg = getConfig();
    const url = `${cfg.azureOpenAI.endpoint}/openai/deployments/${cfg.azureOpenAI.deployment}/chat/completions?api-version=${cfg.azureOpenAI.apiVersion}`;

    const body = {
      messages: [
        { role: 'system', content: CORE_SYSTEM_PROMPT },
        { role: 'system', content: metadataToPromptContext(req.metadata) },
        { role: 'user', content: req.prompt },
      ],
      temperature: 0,
      response_format: { type: 'json_object' },
    };

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (cfg.azureOpenAI.apiKey) {
      headers['api-key'] = cfg.azureOpenAI.apiKey;
    } else {
      // Integration point: acquire a bearer token from managed identity for
      // https://cognitiveservices.azure.com/.default and set Authorization.
      headers['Authorization'] = `Bearer ${await acquireManagedIdentityToken()}`;
    }

    const res = await fetch(url, { method: 'POST', headers, body: JSON.stringify(body) });
    if (!res.ok) {
      throw new AiUnavailableError(`Azure OpenAI returned ${res.status}`);
    }
    const json = (await res.json()) as { choices?: Array<{ message?: { content?: string } }> };
    const content = json.choices?.[0]?.message?.content;
    if (!content) throw new AiUnavailableError('Azure OpenAI returned an empty completion.');

    try {
      return JSON.parse(content) as AiPlan;
    } catch {
      throw new AiUnavailableError('Azure OpenAI returned malformed JSON.');
    }
  }
}

export class AiUnavailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'AiUnavailableError';
  }
}

async function acquireManagedIdentityToken(): Promise<string> {
  throw new AiUnavailableError(
    'Managed-identity token acquisition not implemented: use @azure/identity DefaultAzureCredential ' +
      'to get a token for https://cognitiveservices.azure.com/.default, or configure AZURE_OPENAI_API_KEY.',
  );
}

/* -------------------------------------------------------------------------- */

let client: AiClient | undefined;

export function getAiClient(): AiClient {
  if (!client) client = getConfig().mockMode ? new MockAiClient() : new AzureOpenAiClient();
  return client;
}

export function setAiClientForTests(c: AiClient | undefined): void {
  client = c;
}

/* --------------------------- helper heuristics ---------------------------- */

interface DimEntry {
  canonical: string;
  short: string;
}

function allMeasures(m: SemanticModelMetadata): Array<{ name: string }> {
  return m.tables.flatMap((t) => t.measures.map((x) => ({ name: x.name })));
}

function allDimensions(m: SemanticModelMetadata): DimEntry[] {
  const out: DimEntry[] = [];
  for (const t of m.tables) {
    for (const c of t.columns) {
      if (c.isDimension) out.push({ canonical: `${t.name}.${c.name}`, short: c.name });
    }
  }
  return out;
}

function matchByName(text: string, names: string[], shorts?: string[]): string[] {
  const matches: string[] = [];
  names.forEach((name, i) => {
    const needle = (shorts?.[i] ?? name).toLowerCase();
    if (needle && text.includes(needle)) matches.push(name);
  });
  return matches;
}

function detectChartType(text: string): VisualType | undefined {
  if (/\bline\b/.test(text)) return 'line';
  if (/\bcolumn\b/.test(text)) return 'column';
  if (/\bstacked\b/.test(text)) return 'stacked';
  if (/\bdonut\b/.test(text)) return 'donut';
  if (/\bpie\b/.test(text)) return 'pie';
  if (/\bbar\b/.test(text)) return 'bar';
  if (/\bkpi\b|\bcard\b|\bsingle (value|number)\b/.test(text)) return 'kpi';
  if (/\btable\b/.test(text)) return 'table';
  return undefined;
}

/**
 * Detect a field the user explicitly asks for that is NOT in the model. Uses a
 * small set of common "not available" terms plus any capitalized-looking token
 * that isn't a known field. Kept intentionally conservative.
 */
function detectUnavailableField(text: string, m: SemanticModelMetadata): string | undefined {
  const known = new Set<string>();
  for (const t of m.tables) {
    for (const c of t.columns) known.add(c.name.toLowerCase());
    for (const me of t.measures) known.add(me.name.toLowerCase());
  }
  const commonlyRequestedButAbsent = ['inventory turnover', 'churn rate', 'nps', 'headcount', 'inventory'];
  for (const term of commonlyRequestedButAbsent) {
    if (text.includes(term) && !known.has(term)) return term;
  }
  return undefined;
}

function detectFilter(text: string, m: SemanticModelMetadata):
  | { field: string; operator: '='; value: string | number }
  | undefined {
  // Year filter: a 4-digit year.
  const yearMatch = text.match(/\b(20\d{2})\b/);
  const hasYear = m.tables.some((t) => t.columns.some((c) => c.name.toLowerCase() === 'year'));
  if (yearMatch && hasYear) return { field: 'Year', operator: '=', value: parseInt(yearMatch[1], 10) };

  // Dimension value filter: match a known region/category/product value token.
  const regionValues = ['apac', 'emea', 'latam', 'north america', 'na'];
  for (const rv of regionValues) {
    if (text.includes(rv)) {
      const value = rv === 'na' ? 'North America' : rv.toUpperCase() === rv.toUpperCase() ? titleize(rv) : rv;
      if (m.tables.some((t) => t.columns.some((c) => c.name.toLowerCase() === 'region'))) {
        return { field: 'Region', operator: '=', value };
      }
    }
  }
  return undefined;
}

function titleize(s: string): string {
  return s.replace(/\b\w/g, (c) => c.toUpperCase());
}
