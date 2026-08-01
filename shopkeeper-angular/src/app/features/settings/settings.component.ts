import { ChangeDetectionStrategy, Component, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { BusinessStore } from '../../core/services/business-store.service';
import { AuthService } from '../../core/services/auth.service';
import { ThemeService } from '../../core/services/theme.service';
import { ToastService } from '../../core/services/toast.service';
import { BackupService } from '../../core/services/backup.service';
import { TranslateService } from '../../core/i18n/translate.service';
import { LANGUAGES, Lang } from '../../core/i18n/translations';
import { TPipe } from '../../core/i18n/t.pipe';
import { BusinessSettings } from '../../core/models';

@Component({
  selector: 'app-settings',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, TPipe],
  template: `
    <div class="page-head"><div><h2>{{ 'set.title' | t }}</h2></div></div>

    <div class="grid-2">
      <div class="card">
        <h3 class="card-title">{{ 'set.businessProfile' | t }}</h3>
        <p class="sub">These details appear on every invoice you print or share.</p>
        <div class="form-grid" (input)="dirty.set(true)">
          <label class="span2">{{ 'set.businessName' | t }}<input [(ngModel)]="draft().businessName" /></label>
          <label class="span2">Address<textarea rows="2" [(ngModel)]="draft().address"></textarea></label>
          <label>Phone<input [(ngModel)]="draft().phone" /></label>
          <label>Email<input [(ngModel)]="draft().email" /></label>
          <label>GSTIN<input [(ngModel)]="draft().gstin" /></label>
          <label>UPI ID<input [(ngModel)]="draft().upiId" /></label>
        </div>
        <div style="margin-top:12px"><button class="btn primary" (click)="save()">{{ 'set.saveProfile' | t }}</button></div>
      </div>

      <div>
        <div class="card">
          <h3 class="card-title">{{ 'set.preferences' | t }}</h3>
          <label class="fld">🌐 {{ 'lang.label' | t }}
            <select [value]="i18n.lang()" (change)="setLang($any($event.target).value)">
              @for (l of languages; track l.code) { <option [value]="l.code">{{ l.label }} ({{ l.english }})</option> }
            </select>
          </label>
          <label class="switch-row" style="margin-top:10px"><input type="checkbox" [(ngModel)]="draft().taxEnabled" (change)="save()" /> {{ 'set.gstEnable' | t }}</label>
          <label class="switch-row"><input type="checkbox" [checked]="theme.mode()==='dark'" (change)="theme.toggle()" /> {{ 'set.darkTheme' | t }}</label>
        </div>

        <div class="card">
          <h3 class="card-title">💾 Backup &amp; Restore</h3>
          <p class="sub">Your data is stored in the cloud and synced across devices. Download a copy for your records, or restore from a backup file.</p>
          <div class="head-actions" style="margin-top:10px;flex-wrap:wrap">
            <button class="btn primary" (click)="backup.exportJson()">⬇ Download Backup (JSON)</button>
            <button class="btn ghost" (click)="fileInput.click()">⬆ Restore from Backup</button>
            <input #fileInput type="file" accept=".json,application/json" hidden (change)="onRestore($event)" />
          </div>
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
  readonly i18n = inject(TranslateService);
  readonly backup = inject(BackupService);
  private readonly toast = inject(ToastService);

  readonly languages = LANGUAGES;
  setLang(code: Lang): void { this.i18n.setLang(code); }

  onRestore(e: Event): void {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) this.backup.restore(file);
    input.value = '';
  }

  /** Working copy of the profile form. */
  readonly draft = signal<BusinessSettings>({ ...this.store.settings() });
  /** Becomes true once the user edits the form, so the async profile load
   *  below never clobbers in-progress edits. */
  readonly dirty = signal(false);

  constructor() {
    // The profile streams in from Firestore (userData/{uid}/meta/settings)
    // shortly after login. Keep the form in sync with the logged-in owner's
    // saved profile until they start editing — so returning users see their
    // real business details, not the defaults captured at construction.
    effect(() => {
      const loaded = this.store.settings();
      if (!this.dirty()) this.draft.set({ ...loaded });
    }, { allowSignalWrites: true });
  }

  identity(): string {
    const p = this.auth.profile();
    return p?.displayName || (p?.phone ? '+91 ' + p.phone : p?.email || 'Account');
  }

  async save(): Promise<void> {
    try {
      await this.store.saveSettings(this.draft());
      this.dirty.set(false);
      this.toast.success('Settings saved');
    } catch (e) {
      this.toast.error('Save failed: ' + (e as Error).message);
    }
  }
}
