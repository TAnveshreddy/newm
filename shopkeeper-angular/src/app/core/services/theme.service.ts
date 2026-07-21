import { Injectable, signal, effect } from '@angular/core';

export type ThemeMode = 'light' | 'dark';
const STORAGE_KEY = 'shopkeeper_theme';

/** Applies and persists the light/dark theme via a `data-theme` attribute. */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly mode = signal<ThemeMode>(this.initial());

  constructor() {
    effect(() => {
      const m = this.mode();
      document.documentElement.setAttribute('data-theme', m);
      try {
        localStorage.setItem(STORAGE_KEY, m);
      } catch {
        /* storage may be unavailable in private mode */
      }
    });
  }

  set(mode: ThemeMode): void {
    this.mode.set(mode);
  }

  toggle(): void {
    this.mode.update((m) => (m === 'dark' ? 'light' : 'dark'));
  }

  private initial(): ThemeMode {
    try {
      const saved = localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
      if (saved === 'light' || saved === 'dark') return saved;
    } catch {
      /* ignore */
    }
    return matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
}
