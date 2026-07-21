import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';

/** Sign-in screen: Google, or Indian mobile number + SMS OTP. */
@Component({
  selector: 'app-login',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule],
  template: `
    <div class="login-wrap">
      <div class="login-card">
        <div class="login-logo">S</div>
        <h1 class="login-title">Shopkeeper</h1>
        <p class="login-sub">Billing · Inventory · Khata — synced across your devices</p>

        @if (phase() === 'phone') {
          <button class="btn ghost login-btn" (click)="google()" [disabled]="busy()">Continue with Google</button>
          <div class="or"><span></span>OR<span></span></div>
          <label class="fld">Mobile Number
            <div class="phone-row"><span>+91</span>
              <input inputmode="numeric" maxlength="10" placeholder="10-digit mobile number"
                     [(ngModel)]="phone" (keyup.enter)="sendOtp()" autocomplete="tel" />
            </div>
          </label>
          <button class="btn primary login-btn" (click)="sendOtp()" [disabled]="busy()">Get OTP</button>
          <p class="login-note">A one-time code is sent by SMS to verify your number.</p>
        } @else {
          <h2 class="otp-h">Verify OTP</h2>
          <p class="login-sub">Code sent to <strong>+91 {{ phone() }}</strong></p>
          <label class="fld">Enter OTP
            <input class="otp-input" inputmode="numeric" maxlength="6" placeholder="6-digit OTP"
                   [(ngModel)]="otp" (keyup.enter)="verify()" />
          </label>
          <button class="btn primary login-btn" (click)="verify()" [disabled]="busy()">Verify &amp; Login</button>
          <a class="login-link" (click)="reset()">← Change number</a>
        }
        <div id="recaptcha-container"></div>
      </div>
    </div>
  `,
})
export class LoginComponent {
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);

  readonly phase = signal<'phone' | 'otp'>('phone');
  readonly phone = signal('');
  readonly otp = signal('');
  readonly busy = signal(false);

  constructor() {
    // If already authenticated (e.g. returning session), skip the login screen.
    effect(() => {
      if (this.auth.user()) this.router.navigate(['/dashboard']);
    });
  }

  async google(): Promise<void> {
    this.busy.set(true);
    try {
      await this.auth.loginWithGoogle();
      this.router.navigate(['/dashboard']);
    } catch (e) {
      this.toast.error('Google sign-in failed: ' + (e as Error).message);
    } finally {
      this.busy.set(false);
    }
  }

  async sendOtp(): Promise<void> {
    const p = this.phone().replace(/\D/g, '');
    if (!/^[6-9]\d{9}$/.test(p)) {
      this.toast.error('Enter a valid 10-digit mobile number');
      return;
    }
    this.busy.set(true);
    try {
      await this.auth.sendOtp('+91' + p, 'recaptcha-container');
      this.phase.set('otp');
    } catch (e) {
      this.toast.error('Could not send OTP: ' + (e as Error).message);
    } finally {
      this.busy.set(false);
    }
  }

  async verify(): Promise<void> {
    if (!/^\d{6}$/.test(this.otp())) {
      this.toast.error('Enter the 6-digit OTP');
      return;
    }
    this.busy.set(true);
    try {
      await this.auth.confirmOtp(this.otp());
      this.router.navigate(['/dashboard']);
    } catch {
      this.toast.error('Wrong or expired OTP — please try again');
    } finally {
      this.busy.set(false);
    }
  }

  reset(): void {
    this.phase.set('phone');
    this.otp.set('');
  }
}
