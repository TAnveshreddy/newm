import {
  QueryPlan,
  QueryResult,
  VisualSpec,
  VisualType,
} from '../../models/types';

const SUPPORTED: VisualType[] = ['kpi', 'table', 'bar', 'column', 'line', 'pie', 'donut', 'stacked'];

/**
 * Converts a validated query plan + result into a structured visual
 * specification (Phase 9). The AI proposes a visual type; this service
 * validates it, applies sensible fallbacks, and guarantees the referenced
 * category/measures actually exist in the result — so the frontend renders a
 * spec that always matches the data.
 */
export class VisualSpecService {
  isSupported(type: string): type is VisualType {
    return (SUPPORTED as string[]).includes(type);
  }

  /**
   * Build a final, render-ready visual spec. `requested` is the AI proposal
   * (may be partial/absent). The result is reconciled against the query plan
   * and result columns.
   */
  build(plan: QueryPlan, result: QueryResult, requested?: Partial<VisualSpec>): VisualSpec {
    const measures = result.columns.filter((c) => c.role === 'measure').map((c) => c.name);
    const dimensions = result.columns.filter((c) => c.role === 'dimension').map((c) => c.name);

    let type: VisualType = requested?.type && this.isSupported(requested.type)
      ? requested.type
      : this.inferType(dimensions.length, measures.length, result.rowCount);

    // A KPI needs exactly one aggregate value with no dimension; downgrade if not applicable.
    if (type === 'kpi' && (dimensions.length > 0 || measures.length !== 1)) {
      type = 'table';
    }

    const category = requested?.category && dimensions.includes(shortName(requested.category))
      ? shortName(requested.category)
      : dimensions[0];

    const specMeasures = (requested?.measures ?? [])
      .map(shortName)
      .filter((m) => measures.includes(m));

    return {
      type,
      title: requested?.title?.trim() || this.defaultTitle(type, category, measures),
      category: type === 'kpi' ? undefined : category,
      measures: specMeasures.length > 0 ? specMeasures : measures,
      filters: plan.filters,
      stacked: type === 'stacked' || requested?.stacked === true,
    };
  }

  /** Change only the visual type/formatting without re-querying (Phase 10). */
  changeType(previous: VisualSpec, newType: string): VisualSpec {
    if (!this.isSupported(newType)) return previous;
    return { ...previous, type: newType, stacked: newType === 'stacked' };
  }

  private inferType(dimensions: number, measures: number, rowCount: number): VisualType {
    if (dimensions === 0 && measures === 1) return 'kpi';
    if (dimensions === 0) return 'table';
    if (measures >= 2) return 'bar';
    if (rowCount <= 6) return 'pie';
    if (rowCount > 12) return 'line';
    return 'bar';
  }

  private defaultTitle(type: VisualType, category: string | undefined, measures: string[]): string {
    const measurePart = measures.slice(0, 2).join(' & ') || 'Value';
    if (type === 'kpi' || !category) return measurePart;
    return `${measurePart} by ${category}`;
  }
}

function shortName(field: string): string {
  const idx = field.lastIndexOf('.');
  return idx >= 0 ? field.slice(idx + 1) : field;
}

export const visualSpecService = new VisualSpecService();
