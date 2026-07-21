import { Injectable, inject } from '@angular/core';
import {
  Firestore, collection, collectionData, doc, setDoc, deleteDoc,
  getDocs, query, orderBy, serverTimestamp, CollectionReference,
} from '@angular/fire/firestore';
import { Observable } from 'rxjs';

import { UserProfile, Role, Plan } from '../models';

/**
 * Admin operations over the `users/*` collection. Every write here is also
 * authorised by the Firestore rules (admin-only), so the UI only exposes what
 * an admin is already permitted to do.
 */
@Injectable({ providedIn: 'root' })
export class AdminService {
  private readonly fs = inject(Firestore);
  private readonly businessCols = ['parties', 'items', 'txns', 'adjustments'];

  /** Live list of all registered users, newest first. */
  users$(): Observable<UserProfile[]> {
    const ref = collection(this.fs, 'users') as CollectionReference<UserProfile>;
    return collectionData<UserProfile>(query(ref, orderBy('createdAt', 'desc')));
  }

  setActive(uid: string, active: boolean): Promise<void> {
    const patch: Record<string, unknown> = { active };
    if (active) patch['activatedAt'] = serverTimestamp();
    return setDoc(doc(this.fs, 'users', uid), patch, { merge: true });
  }

  setRole(uid: string, role: Role): Promise<void> {
    return setDoc(doc(this.fs, 'users', uid), { role }, { merge: true });
  }

  setPlan(uid: string, plan: Plan): Promise<void> {
    return setDoc(doc(this.fs, 'users', uid), { plan, planUpdatedAt: serverTimestamp() }, { merge: true });
  }

  /** Remove the profile and the user's whole business-data subtree. */
  async deleteUser(uid: string): Promise<void> {
    for (const col of this.businessCols) {
      const snap = await getDocs(collection(this.fs, `userData/${uid}/${col}`));
      await Promise.all(snap.docs.map((d) => deleteDoc(d.ref)));
    }
    const meta = await getDocs(collection(this.fs, `userData/${uid}/meta`));
    await Promise.all(meta.docs.map((d) => deleteDoc(d.ref)));
    await deleteDoc(doc(this.fs, 'users', uid));
  }
}
