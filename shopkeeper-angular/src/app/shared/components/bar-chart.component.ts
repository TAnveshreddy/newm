import { ChangeDetectionStrategy, Component, Input, computed, signal } from '@angular/core';

export interface BarDatum {
  label: string;
  value: number;
}

/** Dependency-free responsive SVG bar chart (single series). */
@Component({
  selector: 'app-bar-chart',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <svg class="chart" [attr.viewBox]="'0 0 ' + W + ' ' + H" preserveAspectRatio="none"
         role="img" aria-label="Bar chart">
      @for (g of gridlines(); track g.i) {
        <line [attr.x1]="padL" [attr.y1]="g.y" [attr.x2]="W - padR" [attr.y2]="g.y" class="grid" />
        <text [attr.x]="padL - 8" [attr.y]="g.y + 4" class="axis-label" text-anchor="end">{{ g.label }}</text>
      }
      @for (b of bars(); track b.i) {
        @if (b.h > 0) {
          <rect [attr.x]="b.x" [attr.y]="b.y" [attr.width]="barW" [attr.height]="b.h" rx="3" class="bar">
            <title>{{ b.label }}: {{ b.value }}</title>
          </rect>
        }
        @if (b.showLabel) {
          <text [attr.x]="b.x + barW / 2" [attr.y]="H - 8" class="axis-label" text-anchor="middle">{{ b.label }}</text>
        }
      }
      <line [attr.x1]="padL" [attr.y1]="padT + ih" [attr.x2]="W - padR" [attr.y2]="padT + ih" class="baseline" />
    </svg>
  `,
})
export class BarChartComponent {
  readonly W = 720;
  readonly padL = 56; readonly padR = 12; readonly padT = 14; readonly padB = 30;
  @Input() set height(v: number) { this.H = v; }
  H = 240;

  private readonly _data = signal<BarDatum[]>([]);
  @Input() set data(v: BarDatum[]) { this._data.set(v ?? []); }

  get iw(): number { return this.W - this.padL - this.padR; }
  get ih(): number { return this.H - this.padT - this.padB; }
  get max(): number { return Math.max(1, ...this._data().map((d) => d.value)); }
  get step(): number { return this.iw / Math.max(1, this._data().length); }
  get barW(): number { return Math.max(4, Math.min(34, this.step - 4)); }

  readonly bars = computed(() => {
    const data = this._data();
    const every = Math.ceil(data.length / 10) || 1;
    return data.map((d, i) => {
      const x = this.padL + i * this.step + (this.step - this.barW) / 2;
      const h = Math.round(this.ih * d.value / this.max);
      return { i, x, y: this.padT + this.ih - h, h, value: this.short(d.value), label: d.label, showLabel: i % every === 0 };
    });
  });

  readonly gridlines = computed(() => {
    const out = [];
    for (let i = 0; i <= 4; i++) {
      const y = this.padT + this.ih - (this.ih * i) / 4;
      out.push({ i, y, label: this.short((this.max * i) / 4) });
    }
    return out;
  });

  private short(v: number): string {
    const a = Math.abs(v);
    if (a >= 1e7) return (v / 1e7).toFixed(1).replace(/\.0$/, '') + 'Cr';
    if (a >= 1e5) return (v / 1e5).toFixed(1).replace(/\.0$/, '') + 'L';
    if (a >= 1e3) return (v / 1e3).toFixed(1).replace(/\.0$/, '') + 'k';
    return String(Math.round(v));
  }
}
