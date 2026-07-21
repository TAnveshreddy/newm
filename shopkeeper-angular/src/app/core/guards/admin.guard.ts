import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Auth, authState } from '@angular/fire/auth';
import { Firestore, doc, docData } from '@angular/fire/firestore';
import { Observable, map, of, switchMap, take } from 'rxjs';

import { UserProfile } from '../models';

/**
 * Restricts the Admin module to users whose Firestore profile has role
 * `admin`. Non-admins are bounced to the dashboard. The Firestore rules also
 * enforce admin-only access to `users/*`, so this is defence-in-depth, not the
 * only line of protection.
 */
export const adminGuard: CanActivateFn = () => {
  const auth = inject(Auth);
  const fs = inject(Firestore);
  const router = inject(Router);
  return authState(auth).pipe(
    take(1),
    switchMap((user) => {
      if (!user) return of(router.createUrlTree(['/login']));
      return (docData(doc(fs, 'users', user.uid)) as Observable<UserProfile>).pipe(
        take(1),
        map((profile) => (profile?.role === 'admin' ? true : router.createUrlTree(['/dashboard']))),
      );
    }),
  );
};
