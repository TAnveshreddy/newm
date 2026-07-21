import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { BusinessStore } from '../../core/services/business-store.service';
import { ToastService } from '../../core/services/toast.service';
import { InrPipe } from '../../shared/pipes/inr.pipe';
import { Item, ItemType } from '../../core/models';
import { makeId } from '../../core/util/num';

const UNITS = ['PCS', 'BOX', 'KG', 'GRAM', 'LITRE', 'ML', 'BAG', 'BOTTLE', 'PACKET', 'METER', 'SERVICE'];
const GST_RATES = [0, 5, 12, 18, 28];

type Draft = Partial<Item> & { name: string; type: ItemType };

@Component({
  selector: 'app-inventory',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, InrPipe],
  template: `
    <div class="page-head">
      <div><h2>Inventory</h2><div class="sub">{{ store.items().length }} products &amp; services</div></div>
      <div class="head-actions">
        <input class="search" placeholder="📷 Scan barcode…" [(ngModel)]="scan" (keyup.enter)="onScan()" autocomplete="off" />
        <input class="search" placeholder="Search products…" [(ngModel)]="queryText" />
        <button class="btn primary" (click)="openNew()">+ Add Product</button>
      </div>
    </div>

    <div class="kpis" style="grid-template-columns:repeat(2,1fr);max-width:520px">
      <div class="card"><div class="kpi-label">Stock Value (at cost)</div><div class="kpi-value">{{ store.stockValue() | inr }}</div></div>
      <div class="card"><div class="kpi-label">Low Stock Items</div><div class="kpi-value" [class.neg]="store.lowStockItems().length">{{ store.lowStockItems().length }}</div></div>
    </div>

    <div class="card">
      <div class="table-wrap"><table>
        <thead><tr><th>Product</th><th>Type</th><th class="r">Sale</th><th class="r">Purchase</th><th class="r">GST</th><th class="r">Stock</th><th class="r">Actions</th></tr></thead>
        <tbody>
          @for (it of filtered(); track it.id) {
            <tr>
              <td><strong>{{ it.name }}</strong>
                <div class="sub">{{ subLine(it) }}</div>
              </td>
              <td><span class="tag">{{ it.type === 'service' ? 'Service' : 'Product' }}</span></td>
              <td class="r">{{ it.salePrice | inr }}</td>
              <td class="r">{{ it.purchasePrice | inr }}</td>
              <td class="r">{{ it.taxRate || 0 }}%</td>
              <td class="r">
                @if (it.type === 'service') { — }
                @else if (store.itemStock(it.id) <= 0) { <span class="badge bad">No Stock</span> }
                @else if (store.isLowStock(it)) { <span class="badge warn">▲ {{ store.itemStock(it.id) }} {{ it.unit }}</span> }
                @else { {{ store.itemStock(it.id) }} {{ it.unit }} }
              </td>
              <td class="r">
                <button class="btn tiny ghost" (click)="openEdit(it)">Edit</button>
                <button class="btn tiny danger-ghost" (click)="remove(it)">Delete</button>
              </td>
            </tr>
          } @empty {
            <tr><td colspan="7" class="empty">No products yet — add the products or services you sell.</td></tr>
          }
        </tbody>
      </table></div>
    </div>

    @if (draft()) {
      <div class="modal-overlay" (mousedown)="close($event)">
        <div class="modal">
          <div class="modal-head"><h3>{{ draft()!.id ? 'Edit' : 'Add' }} Item</h3><button class="x" (click)="draft.set(null)">×</button></div>
          <div class="modal-body"><div class="form-grid">
            <label class="span2">Item Name *<input [(ngModel)]="draft()!.name" /></label>
            <label>Type<select [(ngModel)]="draft()!.type">
              <option value="product">Product</option><option value="service">Service</option></select></label>
            <label>Category<input [(ngModel)]="draft()!.category" /></label>
            <label>Brand<input [(ngModel)]="draft()!.brand" /></label>
            <label>Unit<select [(ngModel)]="draft()!.unit">@for (u of units; track u) { <option [value]="u">{{ u }}</option> }</select></label>
            <label>HSN / SAC<input [(ngModel)]="draft()!.hsn" /></label>
            <label>Barcode
              <span style="display:flex;gap:6px">
                <input style="flex:1" [(ngModel)]="draft()!.barcode" autocomplete="off" />
                <button type="button" class="btn ghost tiny" (click)="genBarcode()">Generate</button>
              </span>
            </label>
            <label>Sale Price (₹) *<input type="number" [(ngModel)]="draft()!.salePrice" /></label>
            <label>Purchase Price (₹)<input type="number" [(ngModel)]="draft()!.purchasePrice" /></label>
            <label>GST %<select [(ngModel)]="draft()!.taxRate">@for (r of gstRates; track r) { <option [value]="r">{{ r }}%</option> }</select></label>
            @if (draft()!.type !== 'service') {
              <label>Opening Stock<input type="number" [(ngModel)]="draft()!.openingStock" /></label>
              <label>Low Stock Alert At<input type="number" [(ngModel)]="draft()!.minStock" /></label>
            }
          </div></div>
          <div class="modal-foot">
            <button class="btn ghost" (click)="draft.set(null)">Cancel</button>
            <button class="btn primary" (click)="saveDraft()">Save</button>
          </div>
        </div>
      </div>
    }
  `,
})
export class InventoryComponent {
  readonly store = inject(BusinessStore);
  private readonly toast = inject(ToastService);

  readonly units = UNITS;
  readonly gstRates = GST_RATES;

  readonly queryText = signal('');
  readonly scan = signal('');
  readonly draft = signal<Draft | null>(null);

  readonly filtered = computed(() => {
    const q = this.queryText().trim().toLowerCase();
    return this.store.items()
      .filter((i) => !q || i.name.toLowerCase().includes(q) || (i.category ?? '').toLowerCase().includes(q) || (i.barcode ?? '').toLowerCase().includes(q))
      .sort((a, b) => a.name.localeCompare(b.name));
  });

  subLine(it: Item): string {
    return [it.brand, it.category, it.hsn ? 'HSN ' + it.hsn : '', it.barcode ? '▏|▏ ' + it.barcode : '']
      .filter(Boolean)
      .join(' · ');
  }

  openNew(): void {
    this.draft.set({ name: '', type: 'product', unit: 'PCS', taxRate: 18, openingStock: 0, minStock: 0 });
  }
  openEdit(it: Item): void {
    this.draft.set({ ...it });
  }
  close(e: MouseEvent): void {
    if ((e.target as HTMLElement).classList.contains('modal-overlay')) this.draft.set(null);
  }

  async saveDraft(): Promise<void> {
    const d = this.draft();
    if (!d || !d.name.trim()) { this.toast.error('Item name is required'); return; }
    try {
      await this.store.saveItem({ ...d, name: d.name.trim() });
      this.draft.set(null);
      this.toast.success('Item saved');
    } catch (e) {
      this.toast.error('Save failed: ' + (e as Error).message);
    }
  }

  async remove(it: Item): Promise<void> {
    const used = this.store.txns().some((t) => (t.lines ?? []).some((l) => l.itemId === it.id));
    if (used) { this.toast.error('Cannot delete: item is used in transactions.'); return; }
    if (!confirm('Delete this item permanently?')) return;
    await this.store.deleteItem(it.id);
    this.toast.success('Item deleted');
  }

  genBarcode(): void {
    const d = this.draft();
    if (!d) return;
    let code: string;
    do { code = String(Math.floor(200000000000 + Math.random() * 799999999999)); }
    while (this.store.items().some((i) => (i.barcode ?? '') === code));
    this.draft.set({ ...d, barcode: code });
  }

  onScan(): void {
    const code = this.scan().trim();
    this.scan.set('');
    if (!code) return;
    const it = this.store.findItemByBarcode(code);
    if (it) this.openEdit(it);
    else { this.toast.error('New barcode ' + code + ' — add this product'); this.draft.set({ name: '', type: 'product', unit: 'PCS', taxRate: 18, openingStock: 0, minStock: 0, barcode: code }); }
  }
}
