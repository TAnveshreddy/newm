import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { BusinessStore } from '../../core/services/business-store.service';
import { ThemeService } from '../../core/services/theme.service';
import { TranslateService } from '../../core/i18n/translate.service';
import { LANGUAGES, Lang } from '../../core/i18n/translations';
import { TPipe } from '../../core/i18n/t.pipe';

interface NavItem {
  path: string;
  icon: string;
  labelKey: string;
  admin?: boolean;
}

/**
 * Authenticated application shell: fixed dark sidebar + top bar with a
 * `<router-outlet>` for lazy-loaded features. Presentational only — all data
 * comes from injected services.
 */
@Component({
  selector: 'app-shell',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, TPipe],
  template: `
    <div class="app-layout" [class.nav-open]="menuOpen()">
      <aside class="sidebar">
        <div class="brand">
          <div class="logo">S</div>
          <div>
            <div class="brand-name">Shopkeeper</div>
            <div class="brand-biz">{{ store.settings().businessName }}</div>
          </div>
        </div>
        <nav>
          @for (n of visibleNav(); track n.path) {
            <a class="nav-item" [routerLink]="n.path" routerLinkActive="active" (click)="menuOpen.set(false)">
              <span class="ico">{{ n.icon }}</span>{{ n.labelKey | t }}
            </a>
          }
        </nav>
        <div class="sidebar-foot">Synced across your devices</div>
      </aside>

      <div class="main">
        <header class="topbar">
          <button class="hamburger" (click)="menuOpen.set(!menuOpen())" aria-label="Menu">☰</button>
          <div class="topbar-title">{{ store.settings().businessName }}</div>
          <span class="sync-chip" [class.offline]="!online()" [title]="online() ? 'Live-synced with the cloud' : 'Offline — changes sync when you reconnect'">
            {{ online() ? '☁️ Synced' : '⚠️ Offline' }}
          </span>
          <select class="lang-select" title="Language" [value]="i18n.lang()" (change)="onLang($any($event.target).value)">
            @for (l of languages; track l.code) { <option [value]="l.code">🌐 {{ l.label }}</option> }
          </select>
          <button class="icon-btn" (click)="theme.toggle()" title="Toggle theme">
            {{ theme.mode() === 'dark' ? '☀️' : '🌙' }}
          </button>
          <div class="user-chip" title="{{ auth.profile()?.email || auth.profile()?.phone }}">
            <span class="avatar">{{ initial() }}</span>
            <span class="user-meta">
              <span class="user-name">{{ displayName() }}</span>
              <span class="user-role">{{ auth.profile()?.role || 'user' }}</span>
            </span>
          </div>
          <button class="btn ghost tiny" (click)="logout()">{{ 'common.logout' | t }}</button>
        </header>
        <main class="view"><router-outlet></router-outlet></main>
      </div>
    </div>
  `,
})
export class ShellComponent {
  readonly auth = inject(AuthService);
  readonly store = inject(BusinessStore);
  readonly theme = inject(ThemeService);
  readonly i18n = inject(TranslateService);
  private readonly router = inject(Router);

  readonly languages = LANGUAGES;
  onLang(code: Lang): void { this.i18n.setLang(code); }

  readonly menuOpen = signal(false);
  readonly online = signal(typeof navigator !== 'undefined' ? navigator.onLine : true);

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('online', () => this.online.set(true));
      window.addEventListener('offline', () => this.online.set(false));
    }
  }

  private readonly nav: NavItem[] = [
    { path: '/dashboard', icon: '🏠', labelKey: 'nav.dashboard' },
    { path: '/billing', icon: '🧾', labelKey: 'nav.billing' },
    { path: '/inventory', icon: '📦', labelKey: 'nav.inventory' },
    { path: '/parties', icon: '📒', labelKey: 'nav.khata' },
    { path: '/reports', icon: '📊', labelKey: 'nav.reports' },
    { path: '/settings', icon: '⚙️', labelKey: 'nav.settings' },
    { path: '/admin', icon: '🛡️', labelKey: 'nav.admin', admin: true },
  ];

  visibleNav(): NavItem[] {
    const admin = this.auth.isAdmin();
    return this.nav.filter((n) => !n.admin || admin);
  }

  displayName(): string {
    const p = this.auth.profile();
    return p?.displayName || p?.phone || p?.email || 'User';
  }
  initial(): string {
    return (this.displayName()[0] || 'U').toUpperCase();
  }

  async logout(): Promise<void> {
    await this.auth.logout();
    this.router.navigate(['/login']);
  }
}
