import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { BusinessStore } from '../../core/services/business-store.service';
import { KpiCardComponent } from '../../shared/components/kpi-card.component';
import { BarChartComponent, BarDatum } from '../../shared/components/bar-chart.component';
import { InrPipe } from '../../shared/pipes/inr.pipe';
import { Transaction } from '../../core/models';
import { num, todayISO, addDays } from '../../core/util/num';

type Period = 'thisMonth' | 'lastMonth' | 'thisYear';
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

interface Sums { sales: number; profit: number; purch: number; exp: number; bills: number; }

@Component({
  selector: 'app-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, KpiCardComponent, BarChartComponent, InrPipe],
  template: `
    <div class="page-head">
      <div><h2>Dashboard</h2><div class="sub">Overview of your business</div></div>
      <div class="head-actions">
        <a class="btn primary" routerLink="/billing">+ New Bill</a>
        <a class="btn ghost" routerLink="/parties">+ Party</a>
        <a class="btn ghost" routerLink="/inventory">+ Product</a>
      </div>
    </div>

    <div class="kpis">
      <app-kpi-card tone="blue" icon="🛍️" label="Today's Sales" [value]="today().sales | inr">
        <span [innerHTML]="delta(today().sales, yday().sales)"></span> <span class="muted">vs yesterday</span>
      </app-kpi-card>
      <app-kpi-card tone="green" icon="📈" label="Today's Profit" [value]="today().profit | inr">
        <span [innerHTML]="delta(today().profit, yday().profit)"></span> <span class="muted">vs yesterday</span>
      </app-kpi-card>
      <app-kpi-card tone="indigo" icon="🧾" label="Bills Created Today" [value]="today().bills">
        <span [innerHTML]="delta(today().bills, yday().bills, true)"></span> <span class="muted">vs yesterday</span>
      </app-kpi-card>
      <app-kpi-card tone="amber" icon="📦" label="Low Stock Items" [value]="store.lowStockItems().length">
        <a class="klink" routerLink="/inventory">View items</a>
      </app-kpi-card>
      <app-kpi-card tone="green" icon="⬇️" label="To Collect" [value]="store.receivablePayable().receivable | inr">
        <a class="klink" routerLink="/parties">View details</a>
      </app-kpi-card>
      <app-kpi-card tone="red" icon="⬆️" label="To Pay" [value]="store.receivablePayable().payable | inr">
        <a class="klink" routerLink="/parties">View details</a>
      </app-kpi-card>
    </div>

    <div class="dash-grid">
      <div class="card">
        <div class="card-head">
          <div><h3>Sales Overview</h3><div class="sub">{{ periodLabel() }} · Total {{ cur().sales | inr }}</div></div>
          <select class="mini-select" [value]="period()" (change)="setPeriod($any($event.target).value)">
            <option value="thisMonth">This Month</option>
            <option value="lastMonth">Last Month</option>
            <option value="thisYear">This Year</option>
          </select>
        </div>
        <app-bar-chart [data]="bars()" [height]="240"></app-bar-chart>
      </div>

      <div class="card">
        <div class="card-head"><h3>Business Summary</h3></div>
        <div class="biz-row"><div class="biz-left"><div class="biz-ico tone-blue">🛍️</div><span class="biz-name">Total Sales</span></div>
          <div><span class="biz-val">{{ cur().sales | inr }}</span><span class="biz-delta" [innerHTML]="delta(cur().sales, prev().sales)"></span></div></div>
        <div class="biz-row"><div class="biz-left"><div class="biz-ico tone-green">📈</div><span class="biz-name">Total Profit</span></div>
          <div><span class="biz-val">{{ cur().profit | inr }}</span><span class="biz-delta" [innerHTML]="delta(cur().profit, prev().profit)"></span></div></div>
        <div class="biz-row"><div class="biz-left"><div class="biz-ico tone-amber">🛒</div><span class="biz-name">Total Purchases</span></div>
          <div><span class="biz-val">{{ cur().purch | inr }}</span><span class="biz-delta" [innerHTML]="delta(cur().purch, prev().purch)"></span></div></div>
        <div class="biz-row"><div class="biz-left"><div class="biz-ico tone-red">🧾</div><span class="biz-name">Total Expenses</span></div>
          <div><span class="biz-val">{{ cur().exp | inr }}</span><span class="biz-delta" [innerHTML]="delta(cur().exp, prev().exp)"></span></div></div>
        <div style="margin-top:12px"><a class="klink" routerLink="/reports">View full report →</a></div>
      </div>
    </div>

    <div class="dash-grid" style="margin-top:16px">
      <div class="card">
        <div class="card-head"><h3>Low Stock Items
          @if (store.lowStockItems().length) { <span class="badge bad">{{ store.lowStockItems().length }} need attention</span> }
        </h3><a class="klink" routerLink="/inventory">View all items →</a></div>
        @if (store.lowStockItems().length) {
          <div class="table-wrap"><table>
            <thead><tr><th>Item</th><th>Category</th><th class="r">Available</th><th class="r">Reorder</th><th class="r">Status</th></tr></thead>
            <tbody>
              @for (it of store.lowStockItems().slice(0, 6); track it.id) {
                <tr><td><div class="ls-cell"><div class="ls-thumb">📦</div><strong>{{ it.name }}</strong></div></td>
                  <td>{{ it.category || '—' }}</td>
                  <td class="r">{{ store.itemStock(it.id) }} {{ it.unit }}</td>
                  <td class="r">{{ it.minStock || 0 }}</td>
                  <td class="r">@if (store.itemStock(it.id) <= 0) { <span class="badge bad">No Stock</span> } @else { <span class="badge warn">Low</span> }</td></tr>
              }
            </tbody>
          </table></div>
        } @else { <p class="empty">🎉 All items are well stocked.</p> }
      </div>

      <div class="card">
        <div class="card-head"><h3>Recent Transactions</h3><a class="klink" routerLink="/reports">View all →</a></div>
        @if (recent().length) {
          <div class="txn-list">
            @for (t of recent(); track t.id) {
              <div class="txn-item">
                <div class="txn-ico" [class]="'tone-' + meta(t).tone">{{ meta(t).ic }}</div>
                <div class="txn-main">
                  <div class="txn-title">{{ meta(t).label }} · {{ store.partyName(t.partyId) }}</div>
                  <div class="txn-meta">{{ t.number }} · {{ ago(t.createdAt) }}</div>
                </div>
                <div class="txn-amt" [class.pos]="meta(t).sign === '+'" [class.neg]="meta(t).sign === '-'">
                  {{ meta(t).sign }} {{ t.total | inr: false }}
                </div>
              </div>
            }
          </div>
        } @else { <p class="empty">No transactions yet.</p> }
      </div>
    </div>
  `,
})
export class DashboardComponent {
  readonly store = inject(BusinessStore);
  readonly period = signal<Period>('thisMonth');

  readonly today = computed(() => this.sum(todayISO(), todayISO()));
  readonly yday = computed(() => this.sum(addDays(todayISO(), -1), addDays(todayISO(), -1)));

  private readonly range = computed(() => this.resolve(this.period()));
  readonly cur = computed(() => this.sum(this.range().start, this.range().end));
  readonly prev = computed(() => this.sum(this.range().prevStart, this.range().prevEnd));
  readonly bars = computed<BarDatum[]>(() => this.range().bars);
  readonly periodLabel = computed(() => this.range().label);

  readonly recent = computed(() =>
    this.store.txns().slice().sort((a, b) => (b.createdAt ?? 0) - (a.createdAt ?? 0)).slice(0, 6),
  );

  setPeriod(p: Period): void { this.period.set(p); }

  private sum(start: string, end: string): Sums {
    let sales = 0, profit = 0, purch = 0, exp = 0, bills = 0;
    for (const t of this.store.txns()) {
      if (t.date < start || t.date > end) continue;
      if (t.type === 'SALE') { sales += num(t.total); profit += this.store.txnProfit(t); bills++; }
      else if (t.type === 'SALE_RETURN') profit += this.store.txnProfit(t);
      else if (t.type === 'PURCHASE') purch += num(t.total);
      else if (t.type === 'EXPENSE') exp += num(t.total);
    }
    return { sales, profit, purch, exp, bills };
  }

  private resolve(p: Period) {
    const now = new Date(); const Y = now.getFullYear(); const Mo = now.getMonth();
    const iso = (y: number, m: number, d: number) =>
      `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;

    if (p === 'thisYear') {
      const bars: BarDatum[] = [];
      for (let m = 0; m < 12; m++) {
        let s = 0;
        for (const t of this.store.txns()) {
          if (t.type !== 'SALE') continue;
          const dt = new Date(t.date + 'T00:00:00');
          if (dt.getFullYear() === Y && dt.getMonth() === m) s += num(t.total);
        }
        bars.push({ label: MONTHS[m], value: s });
      }
      return { label: 'Year ' + Y, start: iso(Y, 0, 1), end: iso(Y, 11, 31), prevStart: iso(Y - 1, 0, 1), prevEnd: iso(Y - 1, 11, 31), bars };
    }

    let y = Y, m = Mo;
    if (p === 'lastMonth') { m = Mo - 1; if (m < 0) { m = 11; y = Y - 1; } }
    const days = new Date(y, m + 1, 0).getDate();
    const start = iso(y, m, 1), end = iso(y, m, days);
    let py = y, pm = m - 1; if (pm < 0) { pm = 11; py = y - 1; }
    const pdays = new Date(py, pm + 1, 0).getDate();
    const byDay: Record<string, number> = {};
    for (let i = 0; i < days; i++) byDay[addDays(start, i)] = 0;
    for (const t of this.store.txns()) if (t.type === 'SALE' && byDay[t.date] !== undefined) byDay[t.date] += num(t.total);
    const bars = Object.keys(byDay).sort().map((dt) => ({ label: dt.slice(8), value: byDay[dt] }));
    return { label: `${MONTHS[m]} ${y}`, start, end, prevStart: iso(py, pm, 1), prevEnd: iso(py, pm, pdays), bars };
  }

  delta(curV: number, prevV: number, abs = false): string {
    if (abs) {
      const d = Math.round(curV) - Math.round(prevV);
      if (!d) return '<span class="muted">no change</span>';
      return `<span class="delta ${d > 0 ? 'up' : 'down'}">${d > 0 ? '↑ ' : '↓ '}${Math.abs(d)}</span>`;
    }
    if (!prevV) return curV ? '<span class="delta up">↑ new</span>' : '<span class="muted">—</span>';
    const pct = Math.round(((curV - prevV) / Math.abs(prevV)) * 1000) / 10;
    if (!pct) return '<span class="muted">no change</span>';
    return `<span class="delta ${pct > 0 ? 'up' : 'down'}">${pct > 0 ? '↑ ' : '↓ '}${Math.abs(pct)}%</span>`;
  }

  meta(t: Transaction): { ic: string; tone: string; label: string; sign: string } {
    const map: Record<string, { ic: string; tone: string; label: string; sign: string }> = {
      SALE: { ic: '🛒', tone: 'green', label: 'Sale', sign: '+' },
      SALE_RETURN: { ic: '↩️', tone: 'red', label: 'Sale Return', sign: '-' },
      PURCHASE: { ic: '📦', tone: 'blue', label: 'Purchase', sign: '-' },
      PURCHASE_RETURN: { ic: '↩️', tone: 'blue', label: 'Purchase Return', sign: '+' },
      PAYMENT_IN: { ic: '⬇️', tone: 'green', label: 'Payment Received', sign: '+' },
      PAYMENT_OUT: { ic: '⬆️', tone: 'red', label: 'Payment Made', sign: '-' },
      EXPENSE: { ic: '🧾', tone: 'red', label: 'Expense', sign: '-' },
    };
    return map[t.type] ?? { ic: '•', tone: 'blue', label: t.type, sign: '' };
  }

  ago(ts?: number): string {
    if (!ts) return '';
    const s = (Date.now() - ts) / 1000;
    if (s < 60) return 'just now';
    if (s < 3600) return Math.floor(s / 60) + ' min ago';
    if (s < 86400) return Math.floor(s / 3600) + 'h ago';
    const d = Math.floor(s / 86400);
    if (d === 1) return 'Yesterday';
    if (d < 7) return d + ' days ago';
    const dt = new Date(ts);
    return `${dt.getDate()}/${dt.getMonth() + 1}/${dt.getFullYear()}`;
  }
}
