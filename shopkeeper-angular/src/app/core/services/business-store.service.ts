import { Injectable, inject, computed } from '@angular/core';
import { Auth, authState } from '@angular/fire/auth';
import { toSignal } from '@angular/core/rxjs-interop';
import { of, switchMap, map, distinctUntilChanged, Observable } from 'rxjs';

import { FirestoreDataService, BusinessCollection } from './firestore-data.service';
import {
  Party, Item, Transaction, StockAdjustment,
  BusinessSettings, Counters, DEFAULT_SETTINGS, DEFAULT_COUNTERS,
} from '../models';
import { TXN_TYPES } from '../domain/txn-config';
import { num, round2, makeId } from '../util/num';

/**
 * Central reactive store for the signed-in user's business data.
 *
 * Collections are streamed live from Firestore into signals; components read
 * them synchronously and stay in sync across devices automatically. All the
 * domain math (stock, party balances, profit, low-stock, receivable/payable)
 * is ported verbatim from the original app so results are identical.
 */
@Injectable({ providedIn: 'root' })
export class BusinessStore {
  private readonly auth = inject(Auth);
  private readonly data = inject(FirestoreDataService);

  private readonly uid$ = authState(this.auth).pipe(
    map((u) => u?.uid ?? null),
    distinctUntilChanged(),
  );

  private bind<T>(fn: (uid: string) => Observable<T>, fallback: T) {
    return toSignal(
      this.uid$.pipe(switchMap((uid) => (uid ? fn(uid) : of(fallback)))),
      { initialValue: fallback },
    );
  }

  readonly parties = this.bind<Party[]>((uid) => this.data.parties$(uid), []);
  readonly items = this.bind<Item[]>((uid) => this.data.items$(uid), []);
  readonly txns = this.bind<Transaction[]>((uid) => this.data.txns$(uid), []);
  readonly adjustments = this.bind<StockAdjustment[]>((uid) => this.data.adjustments$(uid), []);
  readonly settings = this.bind<BusinessSettings>(
    (uid) => this.data.settings$(uid).pipe(map((s) => ({ ...DEFAULT_SETTINGS, ...(s ?? {}) }))),
    DEFAULT_SETTINGS,
  );
  readonly counters = this.bind<Counters>(
    (uid) => this.data.counters$(uid).pipe(map((c) => ({ ...DEFAULT_COUNTERS, ...(c ?? {}) }))),
    DEFAULT_COUNTERS,
  );

  readonly lowStockItems = computed(() => this.items().filter((it) => this.isLowStock(it)));
  readonly receivablePayable = computed(() => {
    let receivable = 0, payable = 0;
    for (const p of this.parties()) {
      const b = this.partyBalance(p.id);
      if (b > 0) receivable += b;
      else payable += -b;
    }
    return { receivable: round2(receivable), payable: round2(payable) };
  });

  private uid(): string {
    const uid = this.auth.currentUser?.uid;
    if (!uid) throw new Error('Not signed in');
    return uid;
  }

  // ---- lookups ----
  getParty(id: string | null | undefined): Party | null {
    return this.parties().find((p) => p.id === id) ?? null;
  }
  getItem(id: string): Item | null {
    return this.items().find((i) => i.id === id) ?? null;
  }
  partyName(id: string | null | undefined): string {
    return this.getParty(id)?.name ?? 'Cash Sale';
  }
  findItemByBarcode(code: string): Item | null {
    const c = (code ?? '').trim();
    return c ? this.items().find((i) => (i.barcode ?? '').trim() === c) ?? null : null;
  }

  // ---- stock ----
  itemStock(itemId: string): number {
    const it = this.getItem(itemId);
    if (!it || it.type === 'service') return 0;
    let qty = num(it.openingStock);
    for (const t of this.txns()) {
      const dir = TXN_TYPES[t.type].stock;
      if (!dir || !t.lines) continue;
      for (const l of t.lines) if (l.itemId === itemId) qty += dir * num(l.qty);
    }
    for (const a of this.adjustments()) if (a.itemId === itemId) qty += num(a.delta);
    return round2(qty);
  }
  isLowStock(it: Item): boolean {
    if (it.type === 'service') return false;
    const stock = this.itemStock(it.id);
    return stock <= 0 || (num(it.minStock) > 0 && stock <= num(it.minStock));
  }
  stockValue(): number {
    let v = 0;
    for (const it of this.items()) {
      if (it.type === 'service') continue;
      v += Math.max(0, this.itemStock(it.id)) * num(it.purchasePrice || it.salePrice);
    }
    return round2(v);
  }

  // ---- balances ----
  private partyOpening(p: Party): number {
    const v = num(p.openingBalance);
    return p.openingType === 'pay' ? -v : v;
  }
  private txnDue(t: Transaction): number {
    const cfg = TXN_TYPES[t.type];
    if (cfg.balance === 0) return 0;
    if (t.type === 'PAYMENT_IN') return -num(t.total);
    if (t.type === 'PAYMENT_OUT') return num(t.total);
    return cfg.balance * (num(t.total) - num(t.paid));
  }
  partyBalance(partyId: string): number {
    const p = this.getParty(partyId);
    if (!p) return 0;
    let bal = this.partyOpening(p);
    for (const t of this.txns()) if (t.partyId === partyId) bal += this.txnDue(t);
    return round2(bal);
  }

  // ---- profit ----
  private lineCost(l: { cost?: number; itemId: string; qty: number }): number {
    if (l.cost != null) return num(l.cost);
    const it = this.getItem(l.itemId);
    return it ? num(it.purchasePrice) : 0;
  }
  txnProfit(t: Transaction): number {
    if (t.type !== 'SALE' && t.type !== 'SALE_RETURN') return 0;
    const revenue = num(t.subtotal) - num(t.discount);
    let cost = 0;
    for (const l of t.lines ?? []) cost += this.lineCost(l) * num(l.qty);
    const p = round2(revenue - cost);
    return t.type === 'SALE' ? p : -p;
  }

  // ---- numbering ----
  nextNumber(type: Transaction['type']): string {
    return TXN_TYPES[type].prefix + '-' + String(this.counters()[type]).padStart(4, '0');
  }

  // ---- status ----
  txnStatus(t: Transaction): 'Paid' | 'Partial' | 'Unpaid' | 'Open' | 'Converted' {
    const cfg = TXN_TYPES[t.type];
    if (t.type === 'ESTIMATE') return t.convertedTo ? 'Converted' : 'Open';
    if (cfg.balance === 0 || t.type === 'PAYMENT_IN' || t.type === 'PAYMENT_OUT') return 'Paid';
    const dueAmt = num(t.total) - num(t.paid);
    if (dueAmt <= 0.005) return 'Paid';
    return num(t.paid) > 0 ? 'Partial' : 'Unpaid';
  }

  // ---- mutations (write straight through to Firestore) ----
  saveItem(item: Partial<Item> & { name: string; type: Item['type'] }): Promise<void> {
    const rec: Item = {
      id: item.id ?? makeId(),
      createdAt: item.createdAt ?? Date.now(),
      ...item,
    } as Item;
    return this.data.upsert(this.uid(), 'items', rec);
  }
  deleteItem(id: string): Promise<void> {
    return this.data.remove(this.uid(), 'items', id);
  }
  saveParty(party: Partial<Party> & { name: string; type: Party['type'] }): Promise<void> {
    const rec: Party = {
      id: party.id ?? makeId(),
      createdAt: party.createdAt ?? Date.now(),
      ...party,
    } as Party;
    return this.data.upsert(this.uid(), 'parties', rec);
  }
  deleteParty(id: string): Promise<void> {
    return this.data.remove(this.uid(), 'parties', id);
  }
  async saveTxn(txn: Transaction): Promise<void> {
    const rec: Transaction = { ...txn, id: txn.id ?? makeId(), createdAt: txn.createdAt ?? Date.now() };
    await this.data.upsert(this.uid(), 'txns', rec);
    const c = { ...this.counters() };
    if (c[rec.type] != null) {
      c[rec.type] = num(c[rec.type]) + 1;
      await this.data.saveCounters(this.uid(), c);
    }
  }
  deleteTxn(id: string): Promise<void> {
    return this.data.remove(this.uid(), 'txns', id);
  }
  saveSettings(settings: BusinessSettings): Promise<void> {
    return this.data.saveSettings(this.uid(), settings);
  }
  save(name: BusinessCollection, record: { id: string }): Promise<void> {
    return this.data.upsert(this.uid(), name, record);
  }
}
