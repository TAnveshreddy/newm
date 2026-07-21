import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { BusinessStore } from '../../core/services/business-store.service';
import { ToastService } from '../../core/services/toast.service';
import { InrPipe } from '../../shared/pipes/inr.pipe';
import { Item, TxnLine, Transaction } from '../../core/models';
import { num, round2, todayISO } from '../../core/util/num';

const PAY_MODES = ['Cash', 'UPI', 'Card', 'Bank Transfer', 'Credit'];

@Component({
  selector: 'app-billing',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, InrPipe],
  template: `
    <div class="page-head"><div><h2>Billing</h2><div class="sub">Create a sale invoice</div></div>
      <div class="head-actions"><button class="btn ghost" (click)="clear()">Clear Bill</button></div></div>

    <div class="card">
      <div class="form-grid form-grid-3">
        <label>Customer Name<input [(ngModel)]="customer" list="cust-names" placeholder="Cash sale (optional)" /></label>
        <datalist id="cust-names">@for (p of customers(); track p.id) { <option [value]="p.name"></option> }</datalist>
        <label>Contact Number<input [(ngModel)]="mobile" maxlength="10" placeholder="10-digit mobile" /></label>
        <label>Payment Mode<select [(ngModel)]="mode">@for (m of payModes; track m) { <option [value]="m">{{ m }}</option> }</select></label>
      </div>

      <label class="fld" style="margin-top:10px">📷 Scan Barcode
        <input [(ngModel)]="scan" (keyup.enter)="onScan()" placeholder="Click here, then scan — item is added automatically" autocomplete="off" /></label>

      <label class="fld" style="margin-top:10px">Search product (quick add)
        <input [(ngModel)]="queryText" placeholder="Type to search, click a product to add…" /></label>
      <div class="product-picker">
        @for (it of matches(); track it.id) {
          <button class="product-chip" [class.out]="it.type !== 'service' && store.itemStock(it.id) <= 0" (click)="add(it)">
            <span class="pc-name">{{ it.name }}</span>
            <span class="pc-meta">{{ it.salePrice | inr }}@if (it.type !== 'service') { · {{ store.itemStock(it.id) }} {{ it.unit }} }</span>
          </button>
        } @empty { <p class="empty">No matching products.</p> }
      </div>
    </div>

    <div class="card">
      <div class="table-wrap"><table>
        <thead><tr><th>Product</th><th class="r">Qty</th><th class="r">Rate</th><th class="r">GST%</th><th class="r">Total</th><th></th></tr></thead>
        <tbody>
          @for (l of lines(); track l.itemId; let i = $index) {
            <tr>
              <td><strong>{{ l.name }}</strong><div class="sub">{{ l.unit }}</div></td>
              <td class="r"><input class="qty" type="number" min="1" [ngModel]="l.qty" (ngModelChange)="setQty(i, $event)" /></td>
              <td class="r"><input class="qty" type="number" [ngModel]="l.rate" (ngModelChange)="setRate(i, $event)" /></td>
              <td class="r">{{ l.taxRate || 0 }}%</td>
              <td class="r">{{ lineTotal(l) | inr }}</td>
              <td class="r"><button class="btn tiny danger-ghost" (click)="removeLine(i)">×</button></td>
            </tr>
          } @empty { <tr><td colspan="6" class="empty">Scan or add products to start the bill.</td></tr> }
        </tbody>
      </table></div>

      <div class="bill-foot">
        <div class="totals-panel">
          <div class="tp-row"><span>Subtotal</span><span>{{ subtotal() | inr }}</span></div>
          @if (store.settings().taxEnabled) { <div class="tp-row"><span>GST</span><span>{{ tax() | inr }}</span></div> }
          <div class="tp-row grand"><span>Total</span><span>{{ total() | inr }}</span></div>
          <label class="fld">Amount Paid<input type="number" [(ngModel)]="paid" /></label>
        </div>
      </div>
      <div class="head-actions" style="justify-content:flex-end;margin-top:12px">
        <button class="btn primary" (click)="save()" [disabled]="!lines().length">💾 Save Bill</button>
      </div>
    </div>
  `,
})
export class BillingComponent {
  readonly store = inject(BusinessStore);
  private readonly toast = inject(ToastService);

  readonly payModes = PAY_MODES;
  readonly customer = signal('');
  readonly mobile = signal('');
  readonly mode = signal('Cash');
  readonly scan = signal('');
  readonly queryText = signal('');
  readonly paid = signal<number | null>(null);
  readonly lines = signal<TxnLine[]>([]);

  readonly customers = computed(() => this.store.parties().filter((p) => p.type !== 'supplier'));

  readonly matches = computed(() => {
    const q = this.queryText().trim().toLowerCase();
    return this.store.items()
      .filter((i) => !q || i.name.toLowerCase().includes(q) || (i.barcode ?? '').includes(q))
      .sort((a, b) => a.name.localeCompare(b.name))
      .slice(0, 12);
  });

  readonly subtotal = computed(() => round2(this.lines().reduce((s, l) => s + num(l.qty) * num(l.rate), 0)));
  readonly tax = computed(() =>
    this.store.settings().taxEnabled
      ? round2(this.lines().reduce((s, l) => s + (num(l.qty) * num(l.rate) * num(l.taxRate)) / 100, 0))
      : 0,
  );
  readonly total = computed(() => round2(this.subtotal() + this.tax()));

  lineTotal(l: TxnLine): number {
    const base = num(l.qty) * num(l.rate);
    return round2(base + (this.store.settings().taxEnabled ? (base * num(l.taxRate)) / 100 : 0));
  }

  add(it: Item): void {
    this.lines.update((ls) => {
      const found = ls.find((l) => l.itemId === it.id);
      if (found) return ls.map((l) => (l.itemId === it.id ? { ...l, qty: num(l.qty) + 1 } : l));
      return [...ls, {
        itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: 1,
        rate: num(it.salePrice), disc: 0,
        taxRate: this.store.settings().taxEnabled ? num(it.taxRate) : 0,
        brand: it.brand, description: it.description, cost: num(it.purchasePrice),
      }];
    });
  }

  onScan(): void {
    const code = this.scan().trim();
    this.scan.set('');
    if (!code) return;
    const it = this.store.findItemByBarcode(code);
    if (!it) { this.toast.error('No item has barcode ' + code); return; }
    this.add(it);
    this.toast.success('Added ' + it.name);
  }

  setQty(i: number, v: number): void { this.lines.update((ls) => ls.map((l, idx) => (idx === i ? { ...l, qty: num(v) } : l))); }
  setRate(i: number, v: number): void { this.lines.update((ls) => ls.map((l, idx) => (idx === i ? { ...l, rate: num(v) } : l))); }
  removeLine(i: number): void { this.lines.update((ls) => ls.filter((_, idx) => idx !== i)); }
  clear(): void { this.lines.set([]); this.customer.set(''); this.mobile.set(''); this.paid.set(null); }

  async save(): Promise<void> {
    if (!this.lines().length) return;
    const party = this.store.parties().find(
      (p) => p.type !== 'supplier' && p.name.toLowerCase() === this.customer().trim().toLowerCase(),
    );
    const txn: Transaction = {
      id: '', type: 'SALE', number: this.store.nextNumber('SALE'), date: todayISO(),
      partyId: party?.id ?? null, lines: this.lines(),
      subtotal: this.subtotal(), discount: 0, total: this.total(),
      paid: this.paid() == null ? this.total() : num(this.paid()),
      mode: this.mode(),
    };
    try {
      await this.store.saveTxn(txn);
      this.toast.success('Bill ' + txn.number + ' saved');
      this.clear();
    } catch (e) {
      this.toast.error('Could not save: ' + (e as Error).message);
    }
  }
}
