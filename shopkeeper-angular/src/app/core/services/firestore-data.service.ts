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
    return setDoc(doc(this.fs, `userData/${uid}/${name}`, record.id), record);
  }
  remove(uid: string, name: BusinessCollection, id: string): Promise<void> {
    return deleteDoc(doc(this.fs, `userData/${uid}/${name}`, id));
  }
  saveSettings(uid: string, settings: BusinessSettings): Promise<void> {
    return setDoc(doc(this.fs, `userData/${uid}/meta/settings`), settings, { merge: true });
  }
  saveCounters(uid: string, counters: Counters): Promise<void> {
    return setDoc(doc(this.fs, `userData/${uid}/meta/counters`), counters, { merge: true });
  }
}
