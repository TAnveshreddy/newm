import { Injectable, inject } from '@angular/core';
import {
  Firestore,
  collection,
  collectionData,
  doc,
  docData,
  setDoc,
  deleteDoc,
  CollectionReference,
} from '@angular/fire/firestore';
import { Observable } from 'rxjs';

import {
  Party, Item, Transaction, StockAdjustment,
  BusinessSettings, Counters,
} from '../models';

export type BusinessCollection = 'parties' | 'items' | 'txns' | 'adjustments';

/**
 * Recursively removes properties whose value is `undefined`. Firestore's
 * `setDoc()` throws "Unsupported field value: undefined" for any such field
 * (e.g. an item's optional hsn/brand/description on a bill line). Stripping
 * them client-side keeps saves working even if a browser is running a cached
 * bundle built before `ignoreUndefinedProperties` was enabled.
 */
function stripUndefined<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map((v) => stripUndefined(v)) as unknown as T;
  }
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value as Record<string, unknown>)) {
      if (v !== undefined) out[k] = stripUndefined(v);
    }
    return out as T;
  }
  return value;
}

/**
 * Low-level, typed gateway to a user's business data. Every path is scoped to
 * `userData/{uid}/…`, matching the existing schema, so the same documents are
 * shared with the original app. Real-time reads use `collectionData`/`docData`
 * (onSnapshot under the hood); writes are per-record so multiple devices merge
 * instead of overwriting each other.
 */
@Injectable({ providedIn: 'root' })
export class FirestoreDataService {
  private readonly fs = inject(Firestore);

  private col<T>(uid: string, name: BusinessCollection): CollectionReference<T> {
    return collection(this.fs, `userData/${uid}/${name}`) as CollectionReference<T>;
  }

  parties$(uid: string): Observable<Party[]> {
    return collectionData<Party>(this.col<Party>(uid, 'parties'));
  }
  items$(uid: string): Observable<Item[]> {
    return collectionData<Item>(this.col<Item>(uid, 'items'));
  }
  txns$(uid: string): Observable<Transaction[]> {
    return collectionData<Transaction>(this.col<Transaction>(uid, 'txns'));
  }
  adjustments$(uid: string): Observable<StockAdjustment[]> {
    return collectionData<StockAdjustment>(this.col<StockAdjustment>(uid, 'adjustments'));
  }
  settings$(uid: string): Observable<BusinessSettings> {
    return docData(doc(this.fs, `userData/${uid}/meta/settings`)) as Observable<BusinessSettings>;
  }
  counters$(uid: string): Observable<Counters> {
    return docData(doc(this.fs, `userData/${uid}/meta/counters`)) as Observable<Counters>;
  }

  upsert(uid: string, name: BusinessCollection, record: { id: string }): Promise<void> {
    return setDoc(doc(this.fs, `userData/${uid}/${name}`, record.id), stripUndefined(record));
  }
  remove(uid: string, name: BusinessCollection, id: string): Promise<void> {
    return deleteDoc(doc(this.fs, `userData/${uid}/${name}`, id));
  }
  saveSettings(uid: string, settings: BusinessSettings): Promise<void> {
    return setDoc(doc(this.fs, `userData/${uid}/meta/settings`), stripUndefined(settings), { merge: true });
  }
  saveCounters(uid: string, counters: Counters): Promise<void> {
    return setDoc(doc(this.fs, `userData/${uid}/meta/counters`), stripUndefined(counters), { merge: true });
  }
}
