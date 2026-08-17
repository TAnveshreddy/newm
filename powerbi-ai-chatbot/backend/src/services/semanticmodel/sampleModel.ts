import { ModelRegistryEntry, SemanticModelMetadata } from '../../models/types';

/**
 * Sample semantic model used in mock mode so the pipeline is fully runnable
 * without a live Power BI dataset. In production these come from the Power BI
 * metadata discovery API (see metadataService).
 *
 * The shape mirrors the SalesAnalytics dataset used elsewhere in this repo:
 * a Sales fact with Region/Product/Date dimensions and pre-built measures.
 */

export const SAMPLE_MODEL_ID = 'sales-analytics';

export const sampleRegistryEntry: ModelRegistryEntry = {
  modelId: SAMPLE_MODEL_ID,
  displayName: 'Sales Analytics',
  description: 'Governed sales semantic model with revenue, profit and regional measures.',
  workspaceId: 'ws-sales-dev',
  datasetId: 'ds-sales-analytics',
  // Empty lists => available to any authenticated user (dev default).
  allowedRoles: [],
  allowedGroups: [],
};

/** A second model that is gated behind a role, to exercise authorization. */
export const restrictedRegistryEntry: ModelRegistryEntry = {
  modelId: 'finance-executive',
  displayName: 'Finance Executive',
  description: 'Executive finance model with margin and forecast measures.',
  workspaceId: 'ws-finance-dev',
  datasetId: 'ds-finance-exec',
  allowedRoles: ['Finance.Executive'],
  allowedGroups: [],
};

export const sampleMetadata: SemanticModelMetadata = {
  modelId: SAMPLE_MODEL_ID,
  displayName: 'Sales Analytics',
  description: 'Governed sales semantic model.',
  workspaceId: 'ws-sales-dev',
  datasetId: 'ds-sales-analytics',
  lastRefreshed: Date.now(),
  tables: [
    {
      name: 'Sales',
      description: 'Sales fact table (one row per order line).',
      columns: [
        { name: 'OrderId', dataType: 'string', isDimension: true },
        { name: 'Region', dataType: 'string', description: 'Sales region', isDimension: true },
        { name: 'Product', dataType: 'string', description: 'Product name', isDimension: true },
        { name: 'Category', dataType: 'string', description: 'Product category', isDimension: true },
        { name: 'Year', dataType: 'int64', description: 'Calendar year', isDimension: true },
        { name: 'Quantity', dataType: 'int64' },
        { name: 'Revenue', dataType: 'decimal', description: 'Line revenue' },
        { name: 'Cost', dataType: 'decimal', description: 'Line cost' },
      ],
      measures: [
        { name: 'Total Sales', description: 'Sum of revenue', formatHint: 'currency' },
        { name: 'Total Cost', description: 'Sum of cost', formatHint: 'currency' },
        { name: 'Total Profit', description: 'Total Sales - Total Cost', formatHint: 'currency' },
        { name: 'Profit Margin', description: 'Total Profit / Total Sales', formatHint: 'percent' },
        { name: 'Order Count', description: 'Distinct order count', formatHint: 'number' },
      ],
    },
    {
      name: 'Geography',
      description: 'Region/geography dimension.',
      columns: [
        { name: 'RegionName', dataType: 'string', isDimension: true },
        { name: 'Country', dataType: 'string', isDimension: true },
        { name: 'SalesRep', dataType: 'string', isDimension: true },
      ],
      measures: [],
    },
  ],
  relationships: [
    {
      fromTable: 'Sales',
      fromColumn: 'Region',
      toTable: 'Geography',
      toColumn: 'RegionName',
      cardinality: 'manyToOne',
    },
  ],
};
