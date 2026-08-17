import { useEffect, useMemo, useRef } from 'react';
import * as echarts from 'echarts';
import { QueryResult, VisualSpec } from '../models/types';

/**
 * Ad-hoc visual engine (Phase 9). Renders a structured VisualSpec + normalized
 * QueryResult using Apache ECharts. Supported first-release visuals: KPI card,
 * table, bar, column, line, pie/donut and stacked charts.
 *
 * This component only renders data the backend already validated and executed —
 * it never fetches data or talks to Power BI directly.
 */
export function Visualization({ spec, result }: { spec: VisualSpec; result: QueryResult }) {
  if (spec.type === 'kpi') return <KpiCard spec={spec} result={result} />;
  if (spec.type === 'table') return <DataTable result={result} />;
  return <EChart spec={spec} result={result} />;
}

function measureIndexes(result: QueryResult): number[] {
  return result.columns.map((c, i) => (c.role === 'measure' ? i : -1)).filter((i) => i >= 0);
}

function dimensionIndex(result: QueryResult): number {
  return result.columns.findIndex((c) => c.role === 'dimension');
}

function KpiCard({ spec, result }: { spec: VisualSpec; result: QueryResult }) {
  const measures = measureIndexes(result);
  const value = result.rows[0]?.[measures[0]] ?? '—';
  const formatted = typeof value === 'number' ? value.toLocaleString('en-US') : String(value);
  return (
    <div className="kpi-card" role="figure" aria-label={spec.title}>
      <div className="kpi-title">{spec.title}</div>
      <div className="kpi-value">{formatted}</div>
    </div>
  );
}

function DataTable({ result }: { result: QueryResult }) {
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {result.columns.map((c) => (
              <th key={c.name}>{c.name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {result.rows.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <td key={ci}>{typeof cell === 'number' ? cell.toLocaleString('en-US') : String(cell ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {result.truncated && <div className="table-note">Results limited to protect performance.</div>}
    </div>
  );
}

function EChart({ spec, result }: { spec: VisualSpec; result: QueryResult }) {
  const ref = useRef<HTMLDivElement>(null);
  const option = useMemo(() => buildOption(spec, result), [spec, result]);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    chart.setOption(option);
    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chart.dispose();
    };
  }, [option]);

  return <div ref={ref} className="echart" role="img" aria-label={spec.title} />;
}

function buildOption(spec: VisualSpec, result: QueryResult): echarts.EChartsOption {
  const dimIdx = dimensionIndex(result);
  const measures = measureIndexes(result);
  const categories = result.rows.map((r) => String(r[dimIdx] ?? ''));

  const isPie = spec.type === 'pie' || spec.type === 'donut';
  if (isPie) {
    const mi = measures[0];
    return {
      title: { text: spec.title, left: 'center' },
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [
        {
          type: 'pie',
          radius: spec.type === 'donut' ? ['40%', '70%'] : '65%',
          data: result.rows.map((r) => ({ name: String(r[dimIdx] ?? ''), value: Number(r[mi] ?? 0) })),
        },
      ],
    };
  }

  const isLine = spec.type === 'line';
  const stacked = spec.type === 'stacked' || spec.stacked === true;

  const series: echarts.SeriesOption[] = measures.map((mi) => ({
    name: result.columns[mi].name,
    type: isLine ? 'line' : 'bar',
    stack: stacked ? 'total' : undefined,
    smooth: isLine,
    data: result.rows.map((r) => Number(r[mi] ?? 0)),
  }));

  // "column" and "bar" both map to a vertical bar chart here; ECharts uses
  // category on the x-axis for vertical bars.
  return {
    title: { text: spec.title, left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { bottom: 0, show: measures.length > 1 },
    grid: { left: '3%', right: '4%', bottom: 48, containLabel: true },
    xAxis: { type: 'category', data: categories },
    yAxis: { type: 'value' },
    series,
  };
}
