import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { BusinessStore } from '../../core/services/business-store.service';
import { InrPipe } from '../../shared/pipes/inr.pipe';
import { num, todayISO, addDays } from '../../core/util/num';
import { TXN_TYPES } from '../../core/domain/txn-config';

@Component({
  selector: 'app-reports',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, InrPipe],
  template: `
    <div class="page-head"><div><h2>Reports</h2><div class="sub">Business performance</div></div>
      <div class="head-actions">
        <label class="fld inline">From<input type="date" [(ngModel)]="from" /></label>
        <label class="fld inline">To<input type="date" [(ngModel)]="to" /></label>
      </div>
    </div>

    <div class="kpis" style="grid-template-columns:repeat(4,1fr)">
      <div class="card"><div class="kpi-label">Sales</div><div class="kpi-value">{{ agg().sales | inr }}</div></div>
      <div class="card"><div class="kpi-label">Purchases</div><div class="kpi-value">{{ agg().purch | inr }}</div></div>
      <div class="card"><div class="kpi-label">Expenses</div><div class="kpi-value">{{ agg().exp | inr }}</div></div>
      <div class="card"><div class="kpi-label">Gross Profit</div><div class="kpi-value" [class.pos]="agg().profit>=0" [class.neg]="agg().profit<0">{{ agg().profit | inr }}</div></div>
    </div>

    <div class="card">
      <div class="card-head"><h3>Transactions</h3><div class="sub">{{ rows().length }} in range</div></div>
      <div class="table-wrap"><table>
        <thead><tr><th>Date</th><th>Type</th><th>Number</th><th>Party</th><th class="r">Total</th><th class="r">Paid</th></tr></thead>
        <tbody>
          @for (t of rows(); track t.id) {
            <tr><td>{{ t.date }}</td><td><span class="tag">{{ label(t.type) }}</span></td><td>{{ t.number }}</td>
              <td>{{ store.partyName(t.partyId) }}</td><td class="r">{{ t.total | inr }}</td><td class="r">{{ t.paid | inr }}</td></tr>
          } @empty { <tr><td colspan="6" class="empty">No transactions in this range.</td></tr> }
        </tbody>
      </table></div>
    </div>
  `,
})
export class ReportsComponent {
  readonly store = inject(BusinessStore);
  readonly from = signal(addDays(todayISO(), -30));
  readonly to = signal(todayISO());

  readonly rows = computed(() =>
    this.store.txns()
      .filter((t) => t.date >= this.from() && t.date <= this.to())
      .sort((a, b) => (b.createdAt ?? 0) - (a.createdAt ?? 0)),
  );

  readonly agg = computed(() => {
    let sales = 0, purch = 0, exp = 0, profit = 0;
    for (const t of this.rows()) {
      if (t.type === 'SALE') { sales += num(t.total); profit += this.store.txnProfit(t); }
      else if (t.type === 'SALE_RETURN') profit += this.store.txnProfit(t);
      else if (t.type === 'PURCHASE') purch += num(t.total);
      else if (t.type === 'EXPENSE') exp += num(t.total);
    }
    return { sales, purch, exp, profit };
  });

  label(type: keyof typeof TXN_TYPES): string {
    return TXN_TYPES[type].label;
  }
}
