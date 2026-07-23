import { Injectable, inject } from '@angular/core';
import { Auth } from '@angular/fire/auth';

import { BusinessStore } from './business-store.service';
import { FirestoreDataService } from './firestore-data.service';
import { ToastService } from './toast.service';
import { BusinessSettings } from '../models';

interface BackupPayload {
  app: 'shopkeeper';
  version: number;
  exportedAt: string;
  settings: BusinessSettings;
  parties: unknown[];
  items: unknown[];
  txns: unknown[];
  adjustments: unknown[];
}

/**
 * Export the signed-in user's full dataset to a JSON file, and restore it back
 * into Firestore. (Data already lives in the cloud and syncs across devices;
 * this is for an offline copy / manual migration.)
 */
@Injectable({ providedIn: 'root' })
export class BackupService {
  private readonly store = inject(BusinessStore);
  private readonly data = inject(FirestoreDataService);
  private readonly auth = inject(Auth);
  private readonly toast = inject(ToastService);

  /** Download all data as a JSON file. */
  exportJson(): void {
    const payload: BackupPayload = {
      app: 'shopkeeper',
      version: 1,
      exportedAt: new Date().toISOString(),
      settings: this.store.settings(),
      parties: this.store.parties(),
      items: this.store.items(),
      txns: this.store.txns(),
      adjustments: this.store.adjustments(),
    };
    const stamp = new Date().toISOString().slice(0, 10);
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `shopkeeper-backup-${stamp}.json`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
    this.toast.success('Backup downloaded');
  }

  /** Restore from a backup file, writing every record back to Firestore. */
  async restore(file: File): Promise<void> {
    const uid = this.auth.currentUser?.uid;
    if (!uid) { this.toast.error('Not signed in'); return; }
    let payload: BackupPayload;
    try {
      payload = JSON.parse(await file.text());
    } catch {
      this.toast.error('Invalid backup file');
      return;
    }
    if (payload.app !== 'shopkeeper') { this.toast.error('Not a Shopkeeper backup'); return; }
    try {
      const writes: Promise<void>[] = [];
      for (const p of payload.parties ?? []) writes.push(this.data.upsert(uid, 'parties', p as { id: string }));
      for (const it of payload.items ?? []) writes.push(this.data.upsert(uid, 'items', it as { id: string }));
      for (const t of payload.txns ?? []) writes.push(this.data.upsert(uid, 'txns', t as { id: string }));
      for (const a of payload.adjustments ?? []) writes.push(this.data.upsert(uid, 'adjustments', a as { id: string }));
      if (payload.settings) writes.push(this.data.saveSettings(uid, payload.settings));
      await Promise.all(writes);
      this.toast.success('Backup restored');
    } catch (e) {
      this.toast.error('Restore failed: ' + (e as Error).message);
    }
  }
}
