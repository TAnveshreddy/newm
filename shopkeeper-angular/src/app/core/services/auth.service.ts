import { Injectable, inject, signal, computed } from '@angular/core';
import {
  Auth,
  GoogleAuthProvider,
  RecaptchaVerifier,
  signInWithPopup,
  signInWithPhoneNumber,
  signOut,
  authState,
  type User,
  type ConfirmationResult,
} from '@angular/fire/auth';
import {
  Firestore,
  doc,
  docData,
  getDoc,
  setDoc,
  serverTimestamp,
} from '@angular/fire/firestore';
import { Observable, of, switchMap } from 'rxjs';
import { toSignal } from '@angular/core/rxjs-interop';

import { UserProfile } from '../models';

/**
 * Authentication + account-profile service.
 *
 * Mirrors the original app's behaviour: on first sign-in a `users/{uid}` profile
 * is created as a plain `user`/`free`/`active` account (admins are promoted in
 * Firestore later); `lastLogin` is stamped on every sign-in. Phone OTP uses
 * Firebase's built-in SMS via invisible reCAPTCHA (no backend required).
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly auth = inject(Auth);
  private readonly fs = inject(Firestore);

  /** The raw Firebase user (null when signed out). */
  readonly user = toSignal(authState(this.auth), { initialValue: null as User | null });

  /** The signed-in user's account profile, kept live from Firestore. */
  readonly profile = toSignal(this.profile$(), { initialValue: null as UserProfile | null });

  readonly isAuthenticated = computed(() => !!this.user());
  readonly isAdmin = computed(() => this.profile()?.role === 'admin');

  private confirmation: ConfirmationResult | null = null;
  private recaptcha: RecaptchaVerifier | null = null;

  private profile$(): Observable<UserProfile | null> {
    return authState(this.auth).pipe(
      switchMap((u) => {
        if (!u) return of(null);
        return docData(doc(this.fs, 'users', u.uid)) as Observable<UserProfile>;
      }),
    );
  }

  /** Google sign-in (permission is requested by Firebase only on first login). */
  async loginWithGoogle(): Promise<void> {
    const cred = await signInWithPopup(this.auth, new GoogleAuthProvider());
    await this.ensureProfile(cred.user);
  }

  /** Send an OTP by SMS. `containerId` hosts the invisible reCAPTCHA. */
  async sendOtp(phoneE164: string, containerId: string): Promise<void> {
    if (!this.recaptcha) {
      this.recaptcha = new RecaptchaVerifier(this.auth, containerId, { size: 'invisible' });
    }
    this.confirmation = await signInWithPhoneNumber(this.auth, phoneE164, this.recaptcha);
  }

  /** Verify the OTP code; creates/updates the profile on success. */
  async confirmOtp(code: string): Promise<void> {
    if (!this.confirmation) throw new Error('Request an OTP first');
    const cred = await this.confirmation.confirm(code);
    await this.ensureProfile(cred.user);
  }

  async logout(): Promise<void> {
    await signOut(this.auth);
    this.confirmation = null;
  }

  /** Create the profile on first login; stamp lastLogin on subsequent logins. */
  private async ensureProfile(user: User): Promise<void> {
    const ref = doc(this.fs, 'users', user.uid);
    const snap = await getDoc(ref);
    const now = serverTimestamp();
    if (!snap.exists()) {
      const profile = {
        uid: user.uid,
        phone: user.phoneNumber ?? '',
        email: user.email ?? '',
        displayName: user.displayName ?? '',
        provider: user.providerData[0]?.providerId ?? '',
        plan: 'free',
        role: 'user',
        active: true,
        createdAt: now,
        activatedAt: now,
        lastLogin: now,
      };
      await setDoc(ref, profile);
      return;
    }
    await setDoc(ref, { lastLogin: now }, { merge: true });
  }
}
