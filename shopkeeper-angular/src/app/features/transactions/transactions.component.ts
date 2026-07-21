import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { toSignal } from '@angular/core/rxjs-interop';
import { map } from 'rxjs';

import { BusinessStore } from '../../core/services/business-store.service';
import { PrintService } from '../../core/services/print.service';
import { ToastService } from '../../core/services/toast.service';
import { InrPipe } from '../../shared/pipes/inr.pipe';
import { Transaction, TxnType, TxnLine, Item } from '../../core/models';
import { TXN_TYPES } from '../../core/domain/txn-config';
import { num, round2, todayISO } from '../../core/util/num';

export interface TxPageConfig {
  title: string;
  subtitle: string;
  show: TxnType[];
  create: TxnType[];
}

const LINE_BASED: TxnType[] = ['PURCHASE', 'ESTIMATE', 'SALE_RETURN', 'PURCHASE_RETURN'];
const PAY_MODES = ['Cash', 'UPI', 'Card', 'Bank Transfer', 'Credit'];
const EXPENSE_CATS = ['Rent', 'Salary', 'Electricity', 'Transport', 'Supplies', 'Misc'];

interface Draft {
  type: TxnType;
  date: string;
  partyId: string | null;
  lines: TxnLine[];
  amount: number | null;
  paid: number | null;
  mode: string;
  category: string;
  notes: string;
}

/**
 * Generic transactions screen (list + create). One component serves purchases,
 * estimates, payments and expenses — behaviour is driven by the route's `tx`
 * config, so all these pages share one well-tested implementation.
 */
@Component({
  selector: 'app-transactions',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, InrPipe],
  template: `
    <div class="page-head">
      <div><h2>{{ config().title }}</h2><div class="sub">{{ config().subtitle }}</div></div>
      <div class="head-actions">
        @for (t of config().create; track t) {
          <button class="btn primary" (click)="openNew(t)">+ {{ meta(t).label }}</button>
        }
      </div>
    </div>

    <div class="card">
      <div class="table-wrap"><table>
        <thead><tr><th>Date</th><th>Type</th><th>Number</th><th>Party / Category</th><th class="r">Total</th><th>Status</th><th class="r">Actions</th></tr></thead>
        <tbody>
          @for (t of rows(); track t.id) {
            <tr>
              <td>{{ t.date }}</td>
              <td><span class="tag">{{ meta(t.type).label }}</span></td>
              <td>{{ t.number }}</td>
              <td>{{ t.partyId ? store.partyName(t.partyId) : (t.category || '—') }}</td>
              <td class="r">{{ t.total | inr }}</td>
              <td><span class="badge" [class.ok]="status(t)==='Paid'||status(t)==='Converted'" [class.warn]="status(t)==='Partial'||status(t)==='Open'" [class.bad]="status(t)==='Unpaid'">{{ status(t) }}</span></td>
              <td class="r">
                @if (t.lines?.length) { <button class="btn tiny ghost" (click)="print.invoice(t)">🖨 Print</button> }
                <button class="btn tiny danger-ghost" (click)="remove(t)">Delete</button>
              </td>
            </tr>
          } @empty { <tr><td colspan="7" class="empty">Nothing here yet.</td></tr> }
        </tbody>
      </table></div>
    </div>

    @if (draft(); as d) {
      <div class="modal-overlay" (mousedown)="close($event)">
        <div class="modal">
          <div class="modal-head"><h3>{{ meta(d.type).label }}</h3><button class="x" (click)="draft.set(null)">×</button></div>
          <div class="modal-body">
            <div class="form-grid">
              <label>Date<input type="date" [(ngModel)]="d.date" /></label>
              <label>{{ meta(d.type).party === 'supplier' ? 'Supplier' : 'Customer' }}
                <select [(ngModel)]="d.partyId">
                  <option [ngValue]="null">— none —</option>
                  @for (p of parties(d.type); track p.id) { <option [ngValue]="p.id">{{ p.name }}</option> }
                </select></label>
              @if (d.type === 'EXPENSE') {
                <label>Category<input list="exp-cats" [(ngModel)]="d.category" /></label>
                <datalist id="exp-cats">@for (c of expenseCats; track c) { <option [value]="c"></option> }</datalist>
              }
            </div>

            @if (isLineBased(d.type)) {
              <div class="add-item" style="margin-top:10px">
                <label>Add item
                  <select (change)="addLine($any($event.target).value); $any($event.target).value=''">
                    <option value="">— select item —</option>
                    @for (it of store.items(); track it.id) { <option [value]="it.id">{{ it.name }}</option> }
                  </select></label>
              </div>
              <div class="table-wrap" style="margin-top:8px"><table>
                <thead><tr><th>Item</th><th class="r">Qty</th><th class="r">Rate</th><th class="r">GST%</th><th class="r">Total</th><th></th></tr></thead>
                <tbody>
                  @for (l of d.lines; track l.itemId; let i = $index) {
                    <tr><td>{{ l.name }}</td>
                      <td class="r"><input class="qty" type="number" [(ngModel)]="l.qty" /></td>
                      <td class="r"><input class="qty" type="number" [(ngModel)]="l.rate" /></td>
                      <td class="r">{{ l.taxRate || 0 }}%</td>
                      <td class="r">{{ lineTotal(l) | inr }}</td>
                      <td class="r"><button class="btn tiny danger-ghost" (click)="d.lines.splice(i,1)">×</button></td></tr>
                  } @empty { <tr><td colspan="6" class="empty">Add items to this {{ meta(d.type).label.toLowerCase() }}.</td></tr> }
                </tbody>
              </table></div>
              <div class="tp-row grand" style="max-width:280px;margin-left:auto"><span>Total</span><span>{{ linesTotal(d) | inr }}</span></div>
              <label class="fld">Amount Paid<input type="number" [(ngModel)]="d.paid" /></label>
            } @else {
              <div class="form-grid" style="margin-top:8px">
                <label>Amount (₹)<input type="number" [(ngModel)]="d.amount" /></label>
                <label>Mode<select [(ngModel)]="d.mode">@for (m of payModes; track m) { <option [value]="m">{{ m }}</option> }</select></label>
                <label class="span2">Notes<input [(ngModel)]="d.notes" /></label>
              </div>
            }
          </div>
          <div class="modal-foot">
            <button class="btn ghost" (click)="draft.set(null)">Cancel</button>
            <button class="btn primary" (click)="save()">Save</button>
          </div>
        </div>
      </div>
    }
  `,
})
export class TransactionsComponent {
  readonly store = inject(BusinessStore);
  readonly print = inject(PrintService);
  private readonly toast = inject(ToastService);
  private readonly route = inject(ActivatedRoute);

  readonly payModes = PAY_MODES;
  readonly expenseCats = EXPENSE_CATS;

  readonly config = toSignal(
    this.route.data.pipe(map((d) => d['tx'] as TxPageConfig)),
    { initialValue: { title: '', subtitle: '', show: [], create: [] } as TxPageConfig },
  );

  readonly draft = signal<Draft | null>(null);

  readonly rows = computed(() => {
    const show = new Set(this.config().show);
    return this.store.txns()
      .filter((t) => show.has(t.type))
      .sort((a, b) => (b.createdAt ?? 0) - (a.createdAt ?? 0));
  });

  meta(type: TxnType) { return TXN_TYPES[type]; }
  isLineBased(type: TxnType): boolean { return LINE_BASED.includes(type); }
  status(t: Transaction): string { return this.store.txnStatus(t); }

  parties(type: TxnType) {
    const want = TXN_TYPES[type].party;
    return this.store.parties().filter((p) => (want === 'supplier' ? p.type === 'supplier' : p.type !== 'supplier'));
  }

  openNew(type: TxnType): void {
    this.draft.set({ type, date: todayISO(), partyId: null, lines: [], amount: null, paid: null, mode: 'Cash', category: '', notes: '' });
  }
  close(e: MouseEvent): void { if ((e.target as HTMLElement).classList.contains('modal-overlay')) this.draft.set(null); }

  addLine(itemId: string): void {
    const d = this.draft();
    if (!d || !itemId) return;
    const it: Item | null = this.store.getItem(itemId);
    if (!it) return;
    const isPurchase = d.type === 'PURCHASE' || d.type === 'PURCHASE_RETURN';
    const found = d.lines.find((l) => l.itemId === it.id);
    if (found) { found.qty = num(found.qty) + 1; this.draft.set({ ...d }); return; }
    d.lines.push({
      itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: 1,
      rate: num(isPurchase ? it.purchasePrice : it.salePrice), disc: 0,
      taxRate: this.store.settings().taxEnabled ? num(it.taxRate) : 0, cost: num(it.purchasePrice),
    });
    this.draft.set({ ...d });
  }

  lineTotal(l: TxnLine): number {
    const base = num(l.qty) * num(l.rate);
    return round2(base + (this.store.settings().taxEnabled ? (base * num(l.taxRate)) / 100 : 0));
  }
  linesTotal(d: Draft): number {
    return round2(d.lines.reduce((s, l) => s + this.lineTotal(l), 0));
  }
  private linesSubtotal(d: Draft): number {
    return round2(d.lines.reduce((s, l) => s + num(l.qty) * num(l.rate), 0));
  }

  async save(): Promise<void> {
    const d = this.draft();
    if (!d) return;
    let txn: Transaction;
    if (this.isLineBased(d.type)) {
      if (!d.lines.length) { this.toast.error('Add at least one item'); return; }
      const total = this.linesTotal(d);
      txn = {
        id: '', type: d.type, number: this.store.nextNumber(d.type), date: d.date, partyId: d.partyId,
        lines: d.lines, subtotal: this.linesSubtotal(d), discount: 0, total,
        paid: d.paid == null ? total : num(d.paid), mode: d.mode,
      };
    } else {
      const amount = num(d.amount);
      if (amount <= 0) { this.toast.error('Enter an amount'); return; }
      txn = {
        id: '', type: d.type, number: this.store.nextNumber(d.type), date: d.date, partyId: d.partyId,
        total: amount, paid: amount, mode: d.mode, category: d.category, notes: d.notes,
      };
    }
    try {
      await this.store.saveTxn(txn);
      this.toast.success(this.meta(d.type).label + ' ' + txn.number + ' saved');
      this.draft.set(null);
    } catch (e) {
      this.toast.error('Could not save: ' + (e as Error).message);
    }
  }

  async remove(t: Transaction): Promise<void> {
    if (!confirm('Delete ' + t.number + '?')) return;
    await this.store.deleteTxn(t.id);
    this.toast.success('Deleted');
  }
}
