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
    <div class="page-head"><div><h2>{{ 'bill.title' | t }}</h2>
      <div class="sub">@if (editing()) { <span class="badge info">Editing {{ editing()!.number }}</span> } @else { {{ 'bill.createInvoice' | t }} }</div></div>
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
          @for (l of lines(); track $index; let i = $index) {
            <tr>
              <td><strong>{{ l.name }}</strong>
                <div class="sub">{{ lineSub(l) }}</div></td>
              <td class="r"><input class="qty" type="number" min="1" [ngModel]="l.qty" (ngModelChange)="setQty(i, $event)" /></td>
              <td class="r"><input class="qty" type="number" [ngModel]="l.rate" (ngModelChange)="setRate(i, $event)" /></td>
              <td class="r">
                <select class="qty" [ngModel]="taxSelectValue(l)" (ngModelChange)="onTaxSelect(i, $event)" style="width:80px">
                  @for (r of gstRates; track r) { <option [ngValue]="r">{{ r }}%</option> }
                  <option [ngValue]="-1">Custom…</option>
                </select>
                @if (isManualTax(l)) {
                  <input class="qty" type="number" min="0" max="100" step="0.01"
                         [ngModel]="l.taxRate" (ngModelChange)="setTax(i, $event)"
                         placeholder="%" style="width:64px;margin-top:4px" />
                }
              </td>
              <td class="r">{{ lineTotal(l) | inr }}</td>
              <td class="r"><button class="btn tiny danger-ghost" (click)="removeLine(i)">×</button></td>
            </tr>
          } @empty { <tr><td colspan="6" class="empty">{{ 'bill.startBill' | t }}</td></tr> }
        </tbody>
      </table></div>

      <div class="bill-foot">
        <div class="totals-panel">
          <div class="tp-row"><span>{{ 'common.subtotal' | t }}</span><span>{{ subtotal() | inr }}</span></div>
          <div class="tp-row"><span>Discount on entire bill</span>
            <span style="display:flex;gap:4px;align-items:center">
              <input class="qty" type="number" min="0" [ngModel]="discount()" (ngModelChange)="discount.set($event)" style="width:66px" />
              <select [ngModel]="discountType()" (ngModelChange)="discountType.set($event)" style="width:56px">
                <option value="pct">%</option><option value="flat">₹</option></select>
              <span class="muted">− {{ discountAmount() | inr }}</span>
            </span>
          </div>
          @if (store.settings().taxEnabled) { <div class="tp-row"><span>{{ 'common.gst' | t }}</span><span>+ {{ tax() | inr }}</span></div> }
          <div class="tp-row grand"><span>{{ 'common.total' | t }}</span><span>{{ total() | inr }}</span></div>
          <div class="tp-row"><span>Received</span>
            <span style="display:flex;gap:6px;align-items:center">
              <button class="btn tiny ghost" (click)="paid.set(total())">Full</button>
              <input class="qty" type="number" [ngModel]="paid()" (ngModelChange)="paid.set($event)" style="width:96px" />
            </span>
          </div>
          <div class="tp-row" style="color:var(--bad);font-weight:700"><span>Balance Due</span><span>{{ balanceDue() | inr }}</span></div>
        </div>
      </div>
      <div class="head-actions" style="justify-content:flex-end;margin-top:12px">
        <button class="btn ghost" (click)="save(false)" [disabled]="!lines().length">💾 {{ editing() ? 'Update Bill' : ('bill.saveBill' | t) }}</button>
        <button class="btn primary" (click)="save(true)" [disabled]="!lines().length">🖨 {{ 'bill.savePrint' | t }}</button>
      </div>
    </div>

    <div class="card">
      <div class="card-head"><h3>Recent Bills</h3>
        <input class="search" placeholder="Search bill no / customer…" [ngModel]="billSearch()" (ngModelChange)="billSearch.set($event)" /></div>
      <div class="table-wrap"><table>
        <thead><tr><th>Date</th><th>Bill No</th><th>Customer</th><th class="r">Total</th><th>Status</th><th class="r">Actions</th></tr></thead>
        <tbody>
          @for (t of recentBills(); track t.id) {
            <tr>
              <td>{{ fmtDate(t.date) }}</td>
              <td>{{ t.number }}</td>
              <td>{{ store.partyName(t.partyId) }}</td>
              <td class="r">{{ t.total | inr }}</td>
              <td><span class="badge" [class.ok]="status(t)==='Paid'" [class.warn]="status(t)==='Partial'" [class.bad]="status(t)==='Unpaid'">{{ status(t) }}</span></td>
              <td class="r" style="white-space:nowrap">
                <button class="btn tiny wa" (click)="whatsapp(t)">WhatsApp</button>
                <button class="btn tiny ghost" (click)="print.invoice(t)">Print</button>
                <button class="btn tiny ghost" (click)="edit(t)">Edit</button>
                <button class="btn tiny danger-ghost" (click)="remove(t)">Delete</button>
              </td>
            </tr>
          } @empty { <tr><td colspan="6" class="empty">No bills yet.</td></tr> }
        </tbody>
      </table></div>
    </div>
  `,
  styles: [`.btn.wa { background:#25D366; color:#fff; }`],
})
export class BillingComponent {
  readonly store = inject(BusinessStore);
  private readonly toast = inject(ToastService);
  readonly print = inject(PrintService);

  readonly payModes = PAY_MODES;
  readonly customer = signal('');
  readonly mobile = signal('');
  readonly mode = signal('Cash');
  readonly scan = signal('');
  readonly queryText = signal('');
  readonly paid = signal<number | null>(null);
  readonly lines = signal<TxnLine[]>([]);
  readonly discount = signal<number>(0);
  readonly discountType = signal<'pct' | 'flat'>('pct');
  readonly editing = signal<Transaction | null>(null);
  readonly billSearch = signal('');

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
  readonly discountAmount = computed(() => {
    const st = this.subtotal();
    const d = num(this.discount());
    return this.discountType() === 'pct' ? round2((st * d) / 100) : Math.min(round2(d), st);
  });
  readonly tax = computed(() =>
    this.store.settings().taxEnabled
      ? round2(this.lines().reduce((s, l) => s + (num(l.qty) * num(l.rate) * num(l.taxRate)) / 100, 0))
      : 0,
  );
  readonly total = computed(() => round2(this.subtotal() - this.discountAmount() + this.tax()));
  readonly paidVal = computed(() => (this.paid() == null ? this.total() : num(this.paid())));
  readonly balanceDue = computed(() => round2(this.total() - this.paidVal()));

  readonly recentBills = computed(() => {
    const q = this.billSearch().trim().toLowerCase();
    return this.store.txns()
      .filter((t) => t.type === 'SALE')
      .filter((t) => !q || (t.number ?? '').toLowerCase().includes(q) || this.store.partyName(t.partyId).toLowerCase().includes(q))
      .sort((a, b) => (b.createdAt ?? 0) - (a.createdAt ?? 0))
      .slice(0, 20);
  });

  lineTotal(l: TxnLine): number {
    const base = num(l.qty) * num(l.rate);
    return round2(base + (this.store.settings().taxEnabled ? (base * num(l.taxRate)) / 100 : 0));
  }
  lineSub(l: TxnLine): string {
    return [l.brand, l.unit, l.description].filter((x) => !!x).join(' · ');
  }
  status(t: Transaction): string { return this.store.txnStatus(t); }
  fmtDate(iso: string): string {
    const [y, m, d] = (iso ?? '').split('-');
    return d ? `${d}/${m}/${y}` : iso;
  }

  onCat(): void { this.itemSel.set(''); this.brand.set(''); this.desc.set(''); }
  itemSelected(id: string): void {
    const it = this.store.getItem(id);
    this.brand.set(it?.brand ?? '');
    this.desc.set(it?.description ?? '');
  }

  addSelected(): void {
    const it = this.store.getItem(this.itemSel());
    if (!it) { this.toast.error('Select an item first'); return; }
    const brand = this.brand().trim();
    const desc = this.desc().trim();
    this.lines.update((ls) => {
      const found = ls.find((l) => l.itemId === it.id && (l.brand ?? '') === brand && (l.description ?? '') === desc);
      if (found) return ls.map((l) => (l === found ? { ...l, qty: num(l.qty) + 1 } : l));
      return [...ls, {
        itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: 1, rate: num(it.salePrice), disc: 0,
        taxRate: this.store.settings().taxEnabled ? num(it.taxRate) : 0,
        brand, description: desc, cost: num(it.purchasePrice),
      }];
    });
    this.itemSel.set(''); this.brand.set(''); this.desc.set('');
  }

  add(it: Item): void {
    this.lines.update((ls) => {
      const found = ls.find((l) => l.itemId === it.id);
      if (found) return ls.map((l) => (l.itemId === it.id ? { ...l, qty: num(l.qty) + 1 } : l));
      return [...ls, {
        itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: 1, rate: num(it.salePrice), disc: 0,
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

  /** Standard Indian GST slabs offered in the dropdown; "Custom…" enables manual entry. */
  readonly gstRates = [0, 5, 12, 18, 28];
  isManualTax(l: TxnLine): boolean {
    return l.taxManual === true || !this.gstRates.includes(num(l.taxRate));
  }
  /** Value bound to the slab dropdown: -1 means the manual field is in use. */
  taxSelectValue(l: TxnLine): number { return this.isManualTax(l) ? -1 : num(l.taxRate); }
  onTaxSelect(i: number, v: number): void {
    this.lines.update((ls) => ls.map((l, idx) => {
      if (idx !== i) return l;
      // "Custom…" (-1) switches the row to manual entry; a slab sets the rate directly.
      return v === -1 ? { ...l, taxManual: true } : { ...l, taxRate: num(v), taxManual: false };
    }));
  }
  setTax(i: number, v: number): void {
    this.lines.update((ls) => ls.map((l, idx) => (idx === i ? { ...l, taxRate: num(v), taxManual: true } : l)));
  }

  clear(): void {
    this.lines.set([]); this.customer.set(''); this.mobile.set(''); this.paid.set(null);
    this.discount.set(0); this.discountType.set('pct'); this.editing.set(null);
    this.itemSel.set(''); this.brand.set(''); this.desc.set('');
  }

  async save(printAfter: boolean): Promise<void> {
    if (!this.lines().length) return;
    const party = this.store.parties().find(
      (p) => p.type !== 'supplier' && p.name.toLowerCase() === this.customer().trim().toLowerCase(),
    );
    const base = {
      partyId: party?.id ?? null, lines: this.lines(),
      subtotal: this.subtotal(), discount: this.discountAmount(),
      discountPct: this.discountType() === 'pct' ? num(this.discount()) : 0,
      total: this.total(), paid: this.paidVal(), mode: this.mode(),
    };
    const ed = this.editing();
    let txn: Transaction;
    try {
      if (ed) {
        txn = { ...ed, ...base };
        await this.store.save('txns', txn);
        this.toast.success('Bill ' + txn.number + ' updated');
      } else {
        txn = { id: makeId(), type: 'SALE', number: this.store.nextNumber('SALE'), date: todayISO(), createdAt: Date.now(), ...base };
        await this.store.saveTxn(txn);
        this.toast.success('Bill ' + txn.number + ' saved');
      }
      if (printAfter) this.print.invoice(txn);
      this.clear();
    } catch (e) {
      this.toast.error('Could not save: ' + (e as Error).message);
    }
  }

  edit(t: Transaction): void {
    this.editing.set(t);
    this.lines.set((t.lines ?? []).map((l) => ({ ...l })));
    const party = this.store.getParty(t.partyId);
    this.customer.set(party?.name ?? '');
    this.mobile.set(party?.phone ?? '');
    this.mode.set(t.mode ?? 'Cash');
    this.paid.set(num(t.paid));
    if (num(t.discountPct) > 0) { this.discountType.set('pct'); this.discount.set(num(t.discountPct)); }
    else { this.discountType.set('flat'); this.discount.set(num(t.discount)); }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  remove(t: Transaction): void {
    if (!confirm('Delete bill ' + t.number + '?')) return;
    this.store.deleteTxn(t.id).then(() => this.toast.success('Deleted'));
  }

  /** Share the bill with the customer on WhatsApp (opens WhatsApp with a text invoice). */
  whatsapp(t: Transaction): void {
    const s = this.store.settings();
    const party = this.store.getParty(t.partyId);
    const phone = (party?.phone ?? '').replace(/\D/g, '');
    const due = round2(num(t.total) - num(t.paid));
    let msg = `*${s.businessName}*\n`;
    msg += `Invoice: ${t.number}\nDate: ${this.fmtDate(t.date)}\n\n`;
    for (const l of t.lines ?? []) {
      msg += `${l.name} × ${num(l.qty)} = ₹${(num(l.qty) * num(l.rate)).toFixed(2)}\n`;
    }
    msg += `\nTotal: ₹${num(t.total).toFixed(2)}\nReceived: ₹${num(t.paid).toFixed(2)}\nBalance Due: ₹${due.toFixed(2)}\n`;
    if (s.upiId) msg += `\nPay via UPI: ${s.upiId}\n`;
    msg += `\nThank you for your business!`;
    const target = phone ? '91' + phone : '';
    window.open(`https://wa.me/${target}?text=${encodeURIComponent(msg)}`, '_blank');
  }
}
