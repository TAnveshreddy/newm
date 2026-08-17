import { getConfig } from '../../config';
import {
  ModelRegistryEntry,
  QueryPlan,
  QueryResult,
  ResultColumn,
  SemanticModelMetadata,
} from '../../models/types';
import { sampleMetadata } from '../semanticmodel/sampleModel';

/**
 * Abstraction over the Power BI semantic-model query mechanism (Phase 6/8).
 *
 * Two implementations are provided:
 *  - MockPowerBiClient: deterministic, in-process data so the pipeline runs
 *    without a live dataset or credentials.
 *  - LivePowerBiClient: a thin placeholder wired to the Power BI REST API
 *    endpoint shape; the actual auth (managed identity / delegated token) and
 *    the executeQueries DAX call are marked as integration points.
 *
 * Neither client ever concatenates raw user input into query text — the plan is
 * translated field-by-field from validated metadata references only.
 */
export interface PowerBiClient {
  /** Discover metadata for an approved model (tables, columns, measures, relationships). */
  discoverMetadata(entry: ModelRegistryEntry): Promise<SemanticModelMetadata>;
  /** Execute a validated query plan and return a normalized tabular result. */
  executeQuery(entry: ModelRegistryEntry, plan: QueryPlan): Promise<QueryResult>;
}

/* -------------------------------------------------------------------------- */

export class MockPowerBiClient implements PowerBiClient {
  async discoverMetadata(entry: ModelRegistryEntry): Promise<SemanticModelMetadata> {
    // Only the sample model has canned metadata; others return an empty shell
    // with the registry identity so validation still functions.
    if (entry.modelId === sampleMetadata.modelId) {
      return { ...sampleMetadata, lastRefreshed: Date.now() };
    }
    return {
      modelId: entry.modelId,
      displayName: entry.displayName,
      description: entry.description,
      workspaceId: entry.workspaceId,
      datasetId: entry.datasetId,
      tables: [],
      relationships: [],
      lastRefreshed: Date.now(),
    };
  }

  async executeQuery(entry: ModelRegistryEntry, plan: QueryPlan): Promise<QueryResult> {
    const start = Date.now();
    const columns: ResultColumn[] = [
      ...plan.groupBy.map<ResultColumn>((g) => ({
        name: shortName(g),
        role: 'dimension',
        dataType: 'string',
      })),
      ...plan.measures.map<ResultColumn>((m) => ({ name: m, role: 'measure', dataType: 'decimal' })),
    ];

    const rows = this.synthesizeRows(plan);
    const limit = plan.limit ?? getConfig().limits.maxRows;
    const truncated = rows.length > limit;

    return {
      columns,
      rows: rows.slice(0, limit),
      rowCount: Math.min(rows.length, limit),
      durationMs: Date.now() - start,
      truncated,
    };
  }

  /**
   * Produce deterministic sample rows for the sample model so charts render.
   * Values are pseudo-random but stable per (dimension value, measure).
   */
  private synthesizeRows(plan: QueryPlan): Array<Array<string | number | boolean | null>> {
    const dimensionValues = this.dimensionDomain(plan.groupBy[0]);
    const yearFilter = plan.filters.find((f) => shortName(f.field).toLowerCase() === 'year');

    if (plan.groupBy.length === 0) {
      // Single aggregate row (KPI).
      return [plan.measures.map((m) => this.measureValue(m, 'ALL', yearFilter))];
    }

    return dimensionValues.map((dv) => [
      dv,
      ...plan.measures.map((m) => this.measureValue(m, dv, yearFilter)),
    ]);
  }

  private dimensionDomain(field?: string): string[] {
    const name = field ? shortName(field).toLowerCase() : '';
    if (name === 'region') return ['North America', 'EMEA', 'APAC', 'LATAM'];
    if (name === 'category') return ['Hardware', 'Software', 'Services'];
    if (name === 'product') return ['Alpha', 'Beta', 'Gamma', 'Delta'];
    if (name === 'year') return ['2024', '2025', '2026'];
    return ['Group A', 'Group B', 'Group C'];
  }

  private measureValue(measure: string, key: string, yearFilter?: { value: unknown }): number {
    const seed = hash(`${measure}|${key}|${yearFilter ? String(yearFilter.value) : ''}`);
    const base = 10000 + (seed % 90000);
    if (/margin/i.test(measure)) return Math.round((base % 4000) / 100) / 100; // 0..0.40
    if (/count/i.test(measure)) return 50 + (seed % 950);
    return base;
  }
}

/* -------------------------------------------------------------------------- */

/**
 * Live client placeholder. The two integration points marked below are where
 * a token (managed identity or delegated user token) and the actual REST call
 * to `POST /datasets/{id}/executeQueries` (or the XMLA/DAX equivalent) go.
 */
export class LivePowerBiClient implements PowerBiClient {
  async discoverMetadata(_entry: ModelRegistryEntry): Promise<SemanticModelMetadata> {
    throw new Error(
      'LivePowerBiClient.discoverMetadata not implemented: wire the Power BI metadata API ' +
        '(e.g. the dataset schema / DMV query) using a least-privilege token here.',
    );
  }

  async executeQuery(_entry: ModelRegistryEntry, _plan: QueryPlan): Promise<QueryResult> {
    throw new Error(
      'LivePowerBiClient.executeQuery not implemented: translate the validated QueryPlan into a ' +
        'parameterized DAX query and call executeQueries with a server-side token.',
    );
  }
}

/* -------------------------------------------------------------------------- */

let client: PowerBiClient | undefined;

export function getPowerBiClient(): PowerBiClient {
  if (!client) {
    client = getConfig().mockMode ? new MockPowerBiClient() : new LivePowerBiClient();
  }
  return client;
}

/** For tests. */
export function setPowerBiClientForTests(c: PowerBiClient | undefined): void {
  client = c;
}

function shortName(field: string): string {
  const idx = field.lastIndexOf('.');
  return idx >= 0 ? field.slice(idx + 1) : field;
}

function hash(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h);
}
