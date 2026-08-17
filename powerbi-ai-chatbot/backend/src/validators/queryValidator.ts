import { getConfig } from '../config';
import {
  FilterOperator,
  QueryPlan,
  SemanticModelMetadata,
  ValidationIssue,
  ValidationResult,
} from '../models/types';

const VALID_OPERATORS: FilterOperator[] = ['=', '!=', '>', '>=', '<', '<=', 'in', 'contains'];

/**
 * Validates an AI-generated query plan against cached semantic metadata BEFORE
 * execution (Phase 8). This is the enforcement point for NFR §3: the AI must
 * not invent tables, columns or measures, and every referenced field must
 * exist in the known metadata.
 *
 * The validator is pure and deterministic — no I/O — so it is fully unit
 * tested. It also normalizes the plan: canonicalizes field names to
 * "Table.Column" form and clamps the row limit to the server maximum.
 */
export class QueryValidator {
  constructor(private readonly maxRows = getConfig().limits.maxRows) {}

  validate(plan: QueryPlan, metadata: SemanticModelMetadata): ValidationResult {
    const issues: ValidationIssue[] = [];

    // Model identity must match the metadata being validated against.
    if (plan.modelId !== metadata.modelId) {
      issues.push({
        code: 'unauthorized_model',
        message: `Query plan model "${plan.modelId}" does not match the authorized model "${metadata.modelId}".`,
        target: plan.modelId,
      });
      return { valid: false, issues };
    }

    // A plan with nothing to compute is meaningless.
    if (plan.groupBy.length === 0 && plan.measures.length === 0) {
      issues.push({ code: 'empty_plan', message: 'Query plan has no measures and no grouping.' });
    }

    const columnIndex = buildColumnIndex(metadata);
    const measureIndex = buildMeasureIndex(metadata);

    const normalizedGroupBy: string[] = [];
    for (const field of plan.groupBy) {
      const canonical = columnIndex.get(normalizeKey(field));
      if (!canonical) {
        issues.push({
          code: 'unknown_field',
          message: `Field "${field}" does not exist in model "${metadata.displayName}".`,
          target: field,
        });
      } else {
        normalizedGroupBy.push(canonical);
      }
    }

    const normalizedMeasures: string[] = [];
    for (const measure of plan.measures) {
      const canonical = measureIndex.get(normalizeKey(measure));
      if (!canonical) {
        issues.push({
          code: 'unknown_measure',
          message: `Measure "${measure}" does not exist in model "${metadata.displayName}".`,
          target: measure,
        });
      } else {
        normalizedMeasures.push(canonical);
      }
    }

    const normalizedFilters = plan.filters.map((filter) => {
      if (!VALID_OPERATORS.includes(filter.operator)) {
        issues.push({
          code: 'invalid_operator',
          message: `Operator "${filter.operator}" is not allowed.`,
          target: filter.field,
        });
      }
      // Filters may reference a column OR a measure (e.g. HAVING-style).
      const canonicalCol = columnIndex.get(normalizeKey(filter.field));
      const canonicalMeasure = measureIndex.get(normalizeKey(filter.field));
      const canonical = canonicalCol ?? canonicalMeasure;
      if (!canonical) {
        issues.push({
          code: 'unknown_field',
          message: `Filter field "${filter.field}" does not exist in model "${metadata.displayName}".`,
          target: filter.field,
        });
        return filter;
      }
      return { ...filter, field: canonical };
    });

    // Clamp the limit rather than reject — huge result sets are prevented, not errored.
    let limit = plan.limit ?? this.maxRows;
    if (limit > this.maxRows) limit = this.maxRows;
    if (limit <= 0) limit = this.maxRows;

    const valid = issues.length === 0;
    const normalizedPlan: QueryPlan = {
      modelId: plan.modelId,
      groupBy: normalizedGroupBy,
      measures: normalizedMeasures,
      filters: normalizedFilters,
      sort: plan.sort,
      limit,
    };

    return { valid, issues, normalizedPlan: valid ? normalizedPlan : undefined };
  }
}

/* -------------------------------------------------------------------------- */

/**
 * Build a lookup from normalized "table.column" AND bare "column" keys to the
 * canonical "Table.Column" form. Bare column names are only registered when
 * unambiguous across tables.
 */
function buildColumnIndex(metadata: SemanticModelMetadata): Map<string, string> {
  const index = new Map<string, string>();
  const bareCounts = new Map<string, number>();

  for (const table of metadata.tables) {
    for (const column of table.columns) {
      const canonical = `${table.name}.${column.name}`;
      index.set(normalizeKey(canonical), canonical);
      const bare = normalizeKey(column.name);
      bareCounts.set(bare, (bareCounts.get(bare) ?? 0) + 1);
    }
  }
  // Register bare names only when unambiguous.
  for (const table of metadata.tables) {
    for (const column of table.columns) {
      const bare = normalizeKey(column.name);
      if (bareCounts.get(bare) === 1) index.set(bare, `${table.name}.${column.name}`);
    }
  }
  return index;
}

/** Measures are model-global; register both bare and "Table.Measure" keys. */
function buildMeasureIndex(metadata: SemanticModelMetadata): Map<string, string> {
  const index = new Map<string, string>();
  for (const table of metadata.tables) {
    for (const measure of table.measures) {
      index.set(normalizeKey(measure.name), measure.name);
      index.set(normalizeKey(`${table.name}.${measure.name}`), measure.name);
    }
  }
  return index;
}

function normalizeKey(name: string): string {
  return name.trim().toLowerCase();
}

export const queryValidator = new QueryValidator();
