import { QueryValidator } from '../src/validators/queryValidator';
import { sampleMetadata } from '../src/services/semanticmodel/sampleModel';
import { QueryPlan } from '../src/models/types';

const validator = new QueryValidator(1000);

function plan(overrides: Partial<QueryPlan> = {}): QueryPlan {
  return {
    modelId: sampleMetadata.modelId,
    groupBy: [],
    measures: ['Total Sales'],
    filters: [],
    ...overrides,
  };
}

describe('QueryValidator', () => {
  it('accepts a valid plan and canonicalizes field names', () => {
    const result = validator.validate(plan({ groupBy: ['region'], measures: ['total sales'] }), sampleMetadata);
    expect(result.valid).toBe(true);
    expect(result.normalizedPlan?.groupBy).toEqual(['Sales.Region']);
    expect(result.normalizedPlan?.measures).toEqual(['Total Sales']);
  });

  it('rejects an unknown measure (AI must not invent measures)', () => {
    const result = validator.validate(plan({ measures: ['Inventory Turnover'] }), sampleMetadata);
    expect(result.valid).toBe(false);
    expect(result.issues.some((i) => i.code === 'unknown_measure')).toBe(true);
    expect(result.normalizedPlan).toBeUndefined();
  });

  it('rejects an unknown grouping field', () => {
    const result = validator.validate(plan({ groupBy: ['Sentiment'] }), sampleMetadata);
    expect(result.valid).toBe(false);
    expect(result.issues.some((i) => i.code === 'unknown_field')).toBe(true);
  });

  it('rejects a plan whose modelId does not match the authorized metadata', () => {
    const result = validator.validate(plan({ modelId: 'some-other-model' }), sampleMetadata);
    expect(result.valid).toBe(false);
    expect(result.issues[0].code).toBe('unauthorized_model');
  });

  it('flags an empty plan (no measures and no grouping)', () => {
    const result = validator.validate(plan({ measures: [], groupBy: [] }), sampleMetadata);
    expect(result.valid).toBe(false);
    expect(result.issues.some((i) => i.code === 'empty_plan')).toBe(true);
  });

  it('validates filter fields and canonicalizes them', () => {
    const result = validator.validate(
      plan({ filters: [{ field: 'year', operator: '=', value: 2026 }] }),
      sampleMetadata,
    );
    expect(result.valid).toBe(true);
    expect(result.normalizedPlan?.filters[0].field).toBe('Sales.Year');
  });

  it('rejects a filter on an unknown field', () => {
    const result = validator.validate(
      plan({ filters: [{ field: 'Sentiment', operator: '=', value: 'x' }] }),
      sampleMetadata,
    );
    expect(result.valid).toBe(false);
    expect(result.issues.some((i) => i.code === 'unknown_field')).toBe(true);
  });

  it('rejects an invalid operator', () => {
    const result = validator.validate(
      // @ts-expect-error deliberately invalid operator
      plan({ filters: [{ field: 'Year', operator: 'LIKE', value: 2026 }] }),
      sampleMetadata,
    );
    expect(result.valid).toBe(false);
    expect(result.issues.some((i) => i.code === 'invalid_operator')).toBe(true);
  });

  it('clamps a limit above the server maximum', () => {
    const result = validator.validate(plan({ groupBy: ['Region'], limit: 999999 }), sampleMetadata);
    expect(result.valid).toBe(true);
    expect(result.normalizedPlan?.limit).toBe(1000);
  });

  it('applies the default limit when none is provided', () => {
    const result = validator.validate(plan({ groupBy: ['Region'] }), sampleMetadata);
    expect(result.normalizedPlan?.limit).toBe(1000);
  });
});
