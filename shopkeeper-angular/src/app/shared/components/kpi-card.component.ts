import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

export type KpiTone = 'blue' | 'green' | 'indigo' | 'amber' | 'red';

/** Presentational KPI tile: coloured icon, label, value and a sub/delta line. */
@Component({
  selector: 'app-kpi-card',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="kpi">
      <div class="kpi-top">
        <div class="kpi-ico" [class]="'tone-' + tone">{{ icon }}</div>
        <div>
          <div class="kpi-label">{{ label }}</div>
          <div class="kpi-value">{{ value }}</div>
        </div>
      </div>
      <div class="kpi-sub"><ng-content></ng-content></div>
    </div>
  `,
})
export class KpiCardComponent {
  @Input({ required: true }) icon = '';
  @Input({ required: true }) label = '';
  @Input({ required: true }) value: string | number = '';
  @Input() tone: KpiTone = 'blue';
}
