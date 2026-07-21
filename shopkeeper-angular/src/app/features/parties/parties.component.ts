import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { BusinessStore } from '../../core/services/business-store.service';
import { ToastService } from '../../core/services/toast.service';
import { InrPipe } from '../../shared/pipes/inr.pipe';
import { Party, PartyType } from '../../core/models';

type Draft = Partial<Party> & { name: string; type: PartyType };

@Component({
  selector: 'app-parties',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, InrPipe],
  template: `
    <div class="page-head">
      <div><h2>Khata</h2><div class="sub">Customers &amp; suppliers ledger</div></div>
      <div class="head-actions">
        <input class="search" placeholder="Search…" [(ngModel)]="queryText" />
        <button class="btn primary" (click)="openNew()">+ Add Party</button>
      </div>
    </div>

    <div class="tabs">
      <button class="tab" [class.active]="tab() === 'customer'" (click)="tab.set('customer')">Customers <span class="badge info">{{ counts().customer }}</span></button>
      <button class="tab" [class.active]="tab() === 'supplier'" (click)="tab.set('supplier')">Suppliers <span class="badge info">{{ counts().supplier }}</span></button>
    </div>

    <div class="card">
      <div class="table-wrap"><table>
        <thead><tr><th>Name</th><th>Phone</th><th>GSTIN</th><th class="r">Balance</th><th class="r">Actions</th></tr></thead>
        <tbody>
          @for (p of filtered(); track p.id) {
            <tr>
              <td><strong>{{ p.name }}</strong><div class="sub">{{ p.address }}</div></td>
              <td>{{ p.phone || '—' }}</td>
              <td>{{ p.gstin || '—' }}</td>
              <td class="r" [class.pos]="store.partyBalance(p.id) > 0" [class.neg]="store.partyBalance(p.id) < 0">
                {{ balanceLabel(p) }}
              </td>
              <td class="r">
                <button class="btn tiny ghost" (click)="openEdit(p)">Edit</button>
                <button class="btn tiny danger-ghost" (click)="remove(p)">Delete</button>
              </td>
            </tr>
          } @empty { <tr><td colspan="5" class="empty">No {{ tab() }}s yet.</td></tr> }
        </tbody>
      </table></div>
    </div>

    @if (draft()) {
      <div class="modal-overlay" (mousedown)="close($event)">
        <div class="modal">
          <div class="modal-head"><h3>{{ draft()!.id ? 'Edit' : 'Add' }} Party</h3><button class="x" (click)="draft.set(null)">×</button></div>
          <div class="modal-body"><div class="form-grid">
            <label class="span2">Name *<input [(ngModel)]="draft()!.name" /></label>
            <label>Type<select [(ngModel)]="draft()!.type"><option value="customer">Customer</option><option value="supplier">Supplier</option></select></label>
            <label>Phone<input [(ngModel)]="draft()!.phone" maxlength="10" /></label>
            <label>GSTIN<input [(ngModel)]="draft()!.gstin" /></label>
            <label>Email<input [(ngModel)]="draft()!.email" /></label>
            <label class="span2">Address<textarea rows="2" [(ngModel)]="draft()!.address"></textarea></label>
            <label>Opening Balance<input type="number" [(ngModel)]="draft()!.openingBalance" /></label>
            <label>Type<select [(ngModel)]="draft()!.openingType">
              <option value="receive">To Receive (they owe you)</option>
              <option value="pay">To Pay (you owe them)</option></select></label>
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
export class PartiesComponent {
  readonly store = inject(BusinessStore);
  private readonly toast = inject(ToastService);

  readonly tab = signal<PartyType>('customer');
  readonly queryText = signal('');
  readonly draft = signal<Draft | null>(null);

  readonly counts = computed(() => ({
    customer: this.store.parties().filter((p) => p.type !== 'supplier').length,
    supplier: this.store.parties().filter((p) => p.type === 'supplier').length,
  }));

  readonly filtered = computed(() => {
    const q = this.queryText().trim().toLowerCase();
    const t = this.tab();
    return this.store.parties()
      .filter((p) => (t === 'supplier' ? p.type === 'supplier' : p.type !== 'supplier'))
      .filter((p) => !q || p.name.toLowerCase().includes(q) || (p.phone ?? '').includes(q))
      .sort((a, b) => a.name.localeCompare(b.name));
  });

  balanceLabel(p: Party): string {
    const b = this.store.partyBalance(p.id);
    const inr = new InrPipe().transform(Math.abs(b));
    if (b > 0) return inr + ' Dr';
    if (b < 0) return inr + ' Cr';
    return inr;
  }

  openNew(): void { this.draft.set({ name: '', type: this.tab(), openingBalance: 0, openingType: 'receive' }); }
  openEdit(p: Party): void { this.draft.set({ ...p }); }
  close(e: MouseEvent): void { if ((e.target as HTMLElement).classList.contains('modal-overlay')) this.draft.set(null); }

  async saveDraft(): Promise<void> {
    const d = this.draft();
    if (!d || !d.name.trim()) { this.toast.error('Name is required'); return; }
    await this.store.saveParty({ ...d, name: d.name.trim() });
    this.draft.set(null);
    this.toast.success('Party saved');
  }

  async remove(p: Party): Promise<void> {
    const used = this.store.txns().some((t) => t.partyId === p.id);
    if (used) { this.toast.error('Cannot delete: party has transactions.'); return; }
    if (!confirm('Delete this party?')) return;
    await this.store.deleteParty(p.id);
    this.toast.success('Party deleted');
  }
}
