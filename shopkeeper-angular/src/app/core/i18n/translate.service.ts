import { Injectable, signal } from '@angular/core';
import { Lang, TRANSLATIONS } from './translations';

const STORAGE_KEY = 'shopkeeper_lang';

/** Runtime translation service. Holds the active language as a signal and
 *  persists the user's choice. `t(key)` resolves with English → key fallback. */
@Injectable({ providedIn: 'root' })
export class TranslateService {
  readonly lang = signal<Lang>(this.initial());
  readonly chosen = signal<boolean>(this.hasChosen());

  private initial(): Lang {
    try {
      const v = localStorage.getItem(STORAGE_KEY) as Lang | null;
      if (v && TRANSLATIONS[v]) return v;
    } catch { /* ignore */ }
    return 'en';
  }
  private hasChosen(): boolean {
    try { return !!localStorage.getItem(STORAGE_KEY); } catch { return false; }
  }

  setLang(lang: Lang, persist = true): void {
    const wasChosen = this.chosen();
    if (lang === this.lang() && persist && wasChosen) return;
    this.lang.set(lang);
    document.documentElement.setAttribute('lang', lang);
    if (persist) {
      try { localStorage.setItem(STORAGE_KEY, lang); } catch { /* ignore */ }
      this.chosen.set(true);
      // A mid-session change must re-render the whole app. OnPush components read
      // translations through a pipe, so the cleanest, bullet-proof way to apply
      // the new language everywhere is a reload (the choice is already persisted).
      if (wasChosen && typeof location !== 'undefined') location.reload();
    }
  }

  t(key: string): string {
    const l = this.lang();
    return TRANSLATIONS[l][key] ?? TRANSLATIONS.en[key] ?? key;
  }
}
