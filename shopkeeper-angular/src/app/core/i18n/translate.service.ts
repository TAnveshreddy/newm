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
    this.lang.set(lang);
    document.documentElement.setAttribute('lang', lang);
    if (persist) {
      try { localStorage.setItem(STORAGE_KEY, lang); } catch { /* ignore */ }
      this.chosen.set(true);
    }
  }

  t(key: string): string {
    const l = this.lang();
    return TRANSLATIONS[l][key] ?? TRANSLATIONS.en[key] ?? key;
  }
}
