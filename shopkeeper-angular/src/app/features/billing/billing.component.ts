import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { BusinessStore } from '../../core/services/business-store.service';
import { ToastService } from '../../core/services/toast.service';
import { PrintService } from '../../core/services/print.service';
import { InrPipe } from '../../shared/pipes/inr.pipe';
import { TPipe } from '../../core/i18n/t.pipe';
import { Item, TxnLine, Transaction } from '../../core/models';
import { num, round2, todayISO, makeId } from '../../core/util/num';

const PAY_MODES = ['Cash', 'UPI', 'Card', 'Bank Transfer', 'Credit'];

@Component({
  selector: 'app-billing',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, InrPipe, TPipe],
  template: `
    <div class="page-head"><div><h2>{{ 'bill.title' | t }}</h2><div class="sub">{{ 'bill.createInvoice' | t }}</div></div>
      <div class="head-actions"><button class="btn ghost" (click)="clear()">{{ 'bill.clearBill' | t }}</button></div></div>

    <div class="card">
      <div class="form-grid form-grid-3">
        <label>{{ 'bill.customer' | t }}<input [(ngModel)]="customer" list="cust-names" [placeholder]="'bill.cashSale' | t" /></label>
        <datalist id="cust-names">@for (p of customers(); track p.id) { <option [value]="p.name"></option> }</datalist>
        <label>{{ 'bill.contact' | t }}<input [(ngModel)]="mobile" maxlength="10" placeholder="10-digit mobile" /></label>
        <label>{{ 'bill.payMode' | t }}<select [(ngModel)]="mode">@for (m of payModes; track m) { <option [value]="m">{{ m }}</option> }</select></label>
      </div>

      <div class="add-item-row" style="display:grid;grid-template-columns:1fr 1.4fr 1fr 1.4fr auto;gap:10px;align-items:end;margin-top:12px">
        <label>{{ 'bill.category' | t }}
          <select [(ngModel)]="catFilter" (ngModelChange)="onCat()">
            <option value="">{{ 'bill.allCategories' | t }}</option>
            @for (c of categories(); track c) { <option [value]="c">{{ c }}</option> }
          </select></label>
        <label>{{ 'bill.item' | t }}
          <select [(ngModel)]="itemSel" (ngModelChange)="itemSelected($event)">
            <option value="">{{ 'bill.selectItem' | t }}</option>
            @for (it of itemsInCat(); track it.id) { <option [value]="it.id">{{ it.name }}@if (it.brand) { ({{ it.brand }}) }</option> }
          </select></label>
        <label>{{ 'bill.brand' | t }}<input [(ngModel)]="brand" [placeholder]="'bill.brandHint' | t" /></label>
        <label>{{ 'bill.desc' | t }}<input [(ngModel)]="desc" [placeholder]="'bill.descHint' | t" /></label>
        <button class="btn primary" (click)="addSelected()">+ {{ 'bill.addToBill' | t }}</button>
      </div>

      <label class="fld" style="margin-top:10px">📷 {{ 'bill.scan' | t }}
        <input [(ngModel)]="scan" (keyup.enter)="onScan()" [placeholder]="'bill.scanHint' | t" autocomplete="off" /></label>

      <label class="fld" style="margin-top:10px">{{ 'bill.searchProduct' | t }}
        <input [(ngModel)]="queryText" [placeholder]="'bill.searchHint' | t" /></label>
      <div class="product-picker">
        @for (it of matches(); track it.id) {
          <button class="product-chip" [class.out]="it.type !== 'service' && store.itemStock(it.id) <= 0" (click)="add(it)">
            <span class="pc-name">{{ it.name }}</span>
            <span class="pc-meta">{{ it.salePrice | inr }}@if (it.type !== 'service') { · {{ store.itemStock(it.id) }} {{ it.unit }} }</span>
          </button>
        } @empty { <p class="empty">{{ 'bill.noMatch' | t }}</p> }
      </div>
    </div>

    <div class="card">
      <div class="table-wrap"><table>
        <thead><tr><th>{{ 'bill.product' | t }}</th><th class="r">{{ 'bill.qty' | t }}</th><th class="r">{{ 'bill.rate' | t }}</th><th class="r">{{ 'common.gst' | t }}%</th><th class="r">{{ 'common.total' | t }}</th><th></th></tr></thead>
        <tbody>
          @for (l of lines(); track l.itemId; let i = $index) {
            <tr>
              <td><strong>{{ l.name }}</strong>
                <div class="sub">{{ lineSub(l) }}</div></td>
              <td class="r"><input class="qty" type="number" min="1" [ngModel]="l.qty" (ngModelChange)="setQty(i, $event)" /></td>
              <td class="r"><input class="qty" type="number" [ngModel]="l.rate" (ngModelChange)="setRate(i, $event)" /></td>
              <td class="r">{{ l.taxRate || 0 }}%</td>
              <td class="r">{{ lineTotal(l) | inr }}</td>
              <td class="r"><button class="btn tiny danger-ghost" (click)="removeLine(i)">×</button></td>
            </tr>
          } @empty { <tr><td colspan="6" class="empty">{{ 'bill.startBill' | t }}</td></tr> }
        </tbody>
      </table></div>

      <div class="bill-foot">
        <div class="totals-panel">
          <div class="tp-row"><span>{{ 'common.subtotal' | t }}</span><span>{{ subtotal() | inr }}</span></div>
          @if (store.settings().taxEnabled) { <div class="tp-row"><span>{{ 'common.gst' | t }}</span><span>{{ tax() | inr }}</span></div> }
          <div class="tp-row grand"><span>{{ 'common.total' | t }}</span><span>{{ total() | inr }}</span></div>
          <label class="fld">{{ 'bill.amountPaid' | t }}<input type="number" [(ngModel)]="paid" /></label>
        </div>
      </div>
      <div class="head-actions" style="justify-content:flex-end;margin-top:12px">
        <button class="btn ghost" (click)="save(false)" [disabled]="!lines().length">💾 {{ 'bill.saveBill' | t }}</button>
        <button class="btn primary" (click)="save(true)" [disabled]="!lines().length">🖨 {{ 'bill.savePrint' | t }}</button>
      </div>
    </div>
  `,
})
export class BillingComponent {
  readonly store = inject(BusinessStore);
  private readonly toast = inject(ToastService);
  private readonly print = inject(PrintService);

  readonly payModes = PAY_MODES;
  readonly customer = signal('');
  readonly mobile = signal('');
  readonly mode = signal('Cash');
  readonly scan = signal('');
  readonly queryText = signal('');
  readonly paid = signal<number | null>(null);
  readonly lines = signal<TxnLine[]>([]);

  // structured add-item row
  readonly catFilter = signal('');
  readonly itemSel = signal('');
  readonly brand = signal('');
  readonly desc = signal('');

  readonly customers = computed(() => this.store.parties().filter((p) => p.type !== 'supplier'));

  readonly categories = computed(() =>
    [...new Set(this.store.items().map((i) => i.category).filter((c): c is string => !!c))].sort(),
  );
  readonly itemsInCat = computed(() => {
    const cat = this.catFilter();
    return this.store.items()
      .filter((i) => !cat || i.category === cat)
      .sort((a, b) => a.name.localeCompare(b.name));
  });

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

  lineSub(l: TxnLine): string {
    return [l.brand, l.unit, l.description].filter((x) => !!x).join(' · ');
  }

  onCat(): void {
    this.itemSel.set('');
    this.brand.set('');
    this.desc.set('');
  }

  itemSelected(id: string): void {
    const it = this.store.getItem(id);
    this.brand.set(it?.brand ?? '');
    this.desc.set(it?.description ?? '');
  }

  /** "+ Add to Bill" — adds the selected item with the chosen brand/description. */
  addSelected(): void {
    const it = this.store.getItem(this.itemSel());
    if (!it) { this.toast.error('Select an item first'); return; }
    const brand = this.brand().trim();
    const desc = this.desc().trim();
    this.lines.update((ls) => {
      const found = ls.find((l) => l.itemId === it.id && (l.brand ?? '') === brand && (l.description ?? '') === desc);
      if (found) return ls.map((l) => (l === found ? { ...l, qty: num(l.qty) + 1 } : l));
      return [...ls, {
        itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: 1,
        rate: num(it.salePrice), disc: 0,
        taxRate: this.store.settings().taxEnabled ? num(it.taxRate) : 0,
        brand, description: desc, cost: num(it.purchasePrice),
      }];
    });
    this.itemSel.set('');
    this.brand.set('');
    this.desc.set('');
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

  async save(printAfter: boolean): Promise<void> {
    if (!this.lines().length) return;
    const party = this.store.parties().find(
      (p) => p.type !== 'supplier' && p.name.toLowerCase() === this.customer().trim().toLowerCase(),
    );
    const txn: Transaction = {
      id: makeId(), type: 'SALE', number: this.store.nextNumber('SALE'), date: todayISO(),
      partyId: party?.id ?? null, lines: this.lines(),
      subtotal: this.subtotal(), discount: 0, total: this.total(),
      paid: this.paid() == null ? this.total() : num(this.paid()),
      mode: this.mode(),
    };
    try {
      await this.store.saveTxn(txn);
      this.toast.success('Bill ' + txn.number + ' saved');
      if (printAfter) this.print.invoice(txn);
      this.clear();
    } catch (e) {
      this.toast.error('Could not save: ' + (e as Error).message);
    }
  }
}
