import { VisualSpecService } from '../src/services/visualization/visualSpecService';
import { QueryPlan, QueryResult } from '../src/models/types';

const svc = new VisualSpecService();

const plan: QueryPlan = {
  modelId: 'sales-analytics',
  groupBy: ['Sales.Region'],
  measures: ['Total Sales'],
  filters: [{ field: 'Sales.Year', operator: '=', value: 2026 }],
};

function result(rowCount: number, dims = 1, measures = 1): QueryResult {
  const columns = [
    ...(dims ? [{ name: 'Region', role: 'dimension' as const, dataType: 'string' }] : []),
    ...Array.from({ length: measures }, (_, i) => ({
      name: i === 0 ? 'Total Sales' : `Measure${i}`,
      role: 'measure' as const,
      dataType: 'decimal',
    })),
  ];
  const rows = Array.from({ length: rowCount }, (_, i) => [
    ...(dims ? [`R${i}`] : []),
    ...Array.from({ length: measures }, () => 100),
  ]);
  return { columns, rows, rowCount, durationMs: 1, truncated: false };
}

describe('VisualSpecService', () => {
  it('honors a supported requested type', () => {
    const spec = svc.build(plan, result(4), { type: 'bar', title: 'Sales by Region' });
    expect(spec.type).toBe('bar');
    expect(spec.category).toBe('Region');
    expect(spec.measures).toEqual(['Total Sales']);
    expect(spec.title).toBe('Sales by Region');
  });

  it('downgrades a KPI request that has a dimension to a table', () => {
    const spec = svc.build(plan, result(4), { type: 'kpi', title: '', measures: [] });
    expect(spec.type).toBe('table');
  });

  it('infers a KPI for a single value with no dimension', () => {
    const noDimPlan = { ...plan, groupBy: [] };
    const spec = svc.build(noDimPlan, result(1, 0, 1));
    expect(spec.type).toBe('kpi');
    expect(spec.category).toBeUndefined();
  });

  it('generates a default title when none is provided', () => {
    const spec = svc.build(plan, result(4), { type: 'bar', measures: [] });
    expect(spec.title).toBe('Total Sales by Region');
  });

  it('carries the plan filters onto the spec', () => {
    const spec = svc.build(plan, result(4), { type: 'bar', title: 't', measures: [] });
    expect(spec.filters).toEqual(plan.filters);
  });

  it('changeType switches the visual type without touching data', () => {
    const spec = svc.build(plan, result(4), { type: 'bar', title: 't', measures: ['Total Sales'] });
    const changed = svc.changeType(spec, 'line');
    expect(changed.type).toBe('line');
    expect(changed.measures).toEqual(spec.measures);
    expect(changed.title).toBe(spec.title);
  });

  it('changeType ignores an unsupported type', () => {
    const spec = svc.build(plan, result(4), { type: 'bar', title: 't', measures: [] });
    expect(svc.changeType(spec, 'radar').type).toBe('bar');
  });

  it('drops a requested measure that is not in the result', () => {
    const spec = svc.build(plan, result(4), { type: 'bar', title: 't', measures: ['Nonexistent'] });
    expect(spec.measures).toEqual(['Total Sales']); // fell back to result measures
  });
});
