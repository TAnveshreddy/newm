import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { BusinessStore } from '../../core/services/business-store.service';
import { AuthService } from '../../core/services/auth.service';
import { ThemeService } from '../../core/services/theme.service';
import { ToastService } from '../../core/services/toast.service';
import { BusinessSettings } from '../../core/models';

@Component({
  selector: 'app-settings',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule],
  template: `
    <div class="page-head"><div><h2>Settings</h2><div class="sub">Business profile &amp; account</div></div></div>

    <div class="grid-2">
      <div class="card">
        <h3 class="card-title">Business Profile (shown on invoices)</h3>
        <div class="form-grid">
          <label class="span2">Business Name<input [(ngModel)]="draft().businessName" /></label>
          <label class="span2">Address<textarea rows="2" [(ngModel)]="draft().address"></textarea></label>
          <label>Phone<input [(ngModel)]="draft().phone" /></label>
          <label>Email<input [(ngModel)]="draft().email" /></label>
          <label>GSTIN<input [(ngModel)]="draft().gstin" /></label>
          <label>UPI ID<input [(ngModel)]="draft().upiId" /></label>
        </div>
        <div style="margin-top:12px"><button class="btn primary" (click)="save()">Save Profile</button></div>
      </div>

      <div>
        <div class="card">
          <h3 class="card-title">Preferences</h3>
          <label class="switch-row"><input type="checkbox" [(ngModel)]="draft().taxEnabled" (change)="save()" /> Enable GST on transactions</label>
          <label class="switch-row"><input type="checkbox" [checked]="theme.mode()==='dark'" (change)="theme.toggle()" /> Dark theme</label>
        </div>

        <div class="card">
          <h3 class="card-title">☁️ Account &amp; Subscription</h3>
          <p class="sub">Signed in as <strong>{{ identity() }}</strong></p>
          <div class="head-actions" style="margin:8px 0;flex-wrap:wrap">
            <span class="badge info">Plan: {{ auth.profile()?.plan || 'free' }}</span>
            <span class="badge" [class.warn]="auth.isAdmin()" [class.ok]="!auth.isAdmin()">Role: {{ auth.profile()?.role || 'user' }}</span>
            <span class="badge" [class.bad]="auth.profile()?.active===false" [class.ok]="auth.profile()?.active!==false">
              {{ auth.profile()?.active===false ? 'Inactive' : 'Active' }}</span>
          </div>
          @if (auth.isAdmin()) { <p class="sub">You have admin access — manage users from the Admin console.</p> }
          @else { <p class="sub">To change your subscription plan, contact your administrator.</p> }
        </div>

        <div class="card">
          <h3 class="card-title">🔐 Login</h3>
          <p class="sub">Logged in as <strong>{{ identity() }}</strong></p>
          <div class="head-actions" style="margin-top:10px"><button class="btn ghost" (click)="auth.logout()">Log Out</button></div>
        </div>
      </div>
    </div>
  `,
})
export class SettingsComponent {
  readonly store = inject(BusinessStore);
  readonly auth = inject(AuthService);
  readonly theme = inject(ThemeService);
  private readonly toast = inject(ToastService);

  readonly draft = signal<BusinessSettings>({ ...this.store.settings() });

  identity(): string {
    const p = this.auth.profile();
    return p?.displayName || (p?.phone ? '+91 ' + p.phone : p?.email || 'Account');
  }

  async save(): Promise<void> {
    try {
      await this.store.saveSettings(this.draft());
      this.toast.success('Settings saved');
    } catch (e) {
      this.toast.error('Save failed: ' + (e as Error).message);
    }
  }
}
