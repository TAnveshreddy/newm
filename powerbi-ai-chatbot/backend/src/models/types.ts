/**
 * Shared domain types for the Power BI AI Chatbot backend.
 *
 * These types define the contracts that flow through the controlled AI
 * orchestration pipeline (Phase 7 of the implementation guide):
 *
 *   user prompt -> intent -> field selection -> query plan -> validation
 *   -> execution -> result -> visual specification -> typed response
 */

/** Authenticated user identity derived from a validated Entra ID token. */
export interface UserContext {
  /** Object ID (oid) claim — stable per-user identifier. */
  userId: string;
  /** User principal name / preferred_username. */
  username: string;
  name?: string;
  /** Tenant ID (tid) claim. */
  tenantId: string;
  /** App roles / group memberships used for authorization. */
  roles: string[];
  groups: string[];
}

/* ---------------------------------------------------------------------------
 * Semantic model metadata (Phase 6)
 * ------------------------------------------------------------------------- */

export interface ColumnMetadata {
  name: string;
  /** Data type, e.g. "string" | "int64" | "decimal" | "dateTime" | "boolean". */
  dataType: string;
  description?: string;
  /** True when the column may be used as a filter/grouping dimension. */
  isDimension?: boolean;
}

export interface MeasureMetadata {
  name: string;
  description?: string;
  /** Optional display format hint, e.g. "currency", "percent", "number". */
  formatHint?: string;
}

export interface TableMetadata {
  name: string;
  description?: string;
  columns: ColumnMetadata[];
  measures: MeasureMetadata[];
}

export interface RelationshipMetadata {
  fromTable: string;
  fromColumn: string;
  toTable: string;
  toColumn: string;
  /** Cardinality, e.g. "manyToOne" | "oneToMany" | "oneToOne". */
  cardinality: string;
}

/**
 * A semantic model as exposed to the AI orchestration layer. Only metadata the
 * current user is authorized to see should ever reach this shape.
 */
export interface SemanticModelMetadata {
  /** Stable internal model ID assigned by the model registry. */
  modelId: string;
  displayName: string;
  description?: string;
  /** Underlying Power BI workspace and dataset identifiers (never sent raw to the client). */
  workspaceId: string;
  datasetId: string;
  tables: TableMetadata[];
  relationships: RelationshipMetadata[];
  /** Epoch millis when the metadata was last refreshed. */
  lastRefreshed: number;
}

/** An approved model entry, including the authorization rule that gates it. */
export interface ModelRegistryEntry {
  modelId: string;
  displayName: string;
  description?: string;
  workspaceId: string;
  datasetId: string;
  /**
   * Authorization rule: the user must hold at least one of these roles or
   * groups. An empty list means "any authenticated user".
   */
  allowedRoles: string[];
  allowedGroups: string[];
}

/* ---------------------------------------------------------------------------
 * Query plan (Phase 7 / Phase 8)
 * ------------------------------------------------------------------------- */

export type FilterOperator = '=' | '!=' | '>' | '>=' | '<' | '<=' | 'in' | 'contains';

export interface QueryFilter {
  /** "Table.Column" or just "Column" if unambiguous. */
  field: string;
  operator: FilterOperator;
  value: string | number | boolean | Array<string | number>;
}

export type SortDirection = 'asc' | 'desc';

export interface QuerySort {
  field: string;
  direction: SortDirection;
}

/**
 * A structured, declarative query plan. The AI proposes this shape — it never
 * emits executable DAX/SQL directly. The validator checks every referenced
 * field against the semantic metadata before anything is executed.
 */
export interface QueryPlan {
  modelId: string;
  /** Grouping dimensions, e.g. ["Sales.Region"]. */
  groupBy: string[];
  /** Measures to aggregate, e.g. ["Total Sales"]. */
  measures: string[];
  filters: QueryFilter[];
  sort?: QuerySort[];
  /** Server-enforced row cap; requests above the max are clamped. */
  limit?: number;
}

export interface ValidationIssue {
  code:
    | 'unknown_model'
    | 'unauthorized_model'
    | 'unknown_field'
    | 'unknown_measure'
    | 'empty_plan'
    | 'invalid_operator'
    | 'limit_exceeded';
  message: string;
  /** The offending field/measure/model, when applicable. */
  target?: string;
}

export interface ValidationResult {
  valid: boolean;
  issues: ValidationIssue[];
  /** The plan after normalization (clamped limit, canonicalized field names). */
  normalizedPlan?: QueryPlan;
}

/* ---------------------------------------------------------------------------
 * Query execution result (Phase 8)
 * ------------------------------------------------------------------------- */

export interface ResultColumn {
  name: string;
  /** "dimension" | "measure". */
  role: 'dimension' | 'measure';
  dataType: string;
}

/**
 * Normalized, tabular result schema returned to the visualization layer.
 * Rows are arrays aligned to `columns` order.
 */
export interface QueryResult {
  columns: ResultColumn[];
  rows: Array<Array<string | number | boolean | null>>;
  rowCount: number;
  /** Execution duration in milliseconds (safe diagnostic). */
  durationMs: number;
  truncated: boolean;
}

/* ---------------------------------------------------------------------------
 * Visualization specification (Phase 9)
 * ------------------------------------------------------------------------- */

export type VisualType =
  | 'kpi'
  | 'table'
  | 'bar'
  | 'column'
  | 'line'
  | 'pie'
  | 'donut'
  | 'stacked';

export interface VisualSpec {
  type: VisualType;
  title: string;
  /** Category / dimension field name for cartesian and pie charts. */
  category?: string;
  measures: string[];
  filters?: QueryFilter[];
  /** Whether the series should stack (bar/column/stacked). */
  stacked?: boolean;
}

/* ---------------------------------------------------------------------------
 * AI orchestration + chat contract
 * ------------------------------------------------------------------------- */

export type IntentType =
  | 'data_question'
  | 'create_visual'
  | 'modify_visual'
  | 'change_filter'
  | 'add_measure'
  | 'clarification_needed'
  | 'unavailable';

/** The structured plan the AI returns from a prompt (never executable code). */
export interface AiPlan {
  intent: IntentType;
  /** Present when the model can build a data query. */
  queryPlan?: QueryPlan;
  /** Present when the model proposes a visualization. */
  visual?: VisualSpec;
  /** A concise clarification question when intent is clarification_needed. */
  clarification?: string;
  /** A user-facing explanation when a requested field/measure is unavailable. */
  unavailableReason?: string;
  /** Whether this request can reuse existing state without re-querying. */
  reuseLastResult?: boolean;
}

/** Persisted per-conversation state (Phase 10). */
export interface ConversationState {
  conversationId: string;
  userId: string;
  modelId?: string;
  lastQueryPlan?: QueryPlan;
  lastResult?: QueryResult;
  lastVisual?: VisualSpec;
  lastFilters: QueryFilter[];
  updatedAt: number;
}

export type ChatResponseStatus =
  | 'answer'
  | 'visual'
  | 'clarification'
  | 'unavailable'
  | 'error';

/** The typed response returned to the frontend from POST /api/chat. */
export interface ChatResponse {
  conversationId: string;
  status: ChatResponseStatus;
  intent: IntentType;
  /** Human-readable assistant message. */
  message: string;
  visual?: VisualSpec;
  result?: QueryResult;
  clarification?: string;
}
