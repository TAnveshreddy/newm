import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { TranslateService } from '../../core/i18n/translate.service';
import { LANGUAGES, Lang } from '../../core/i18n/translations';
import { TPipe } from '../../core/i18n/t.pipe';

/** First-run language chooser. Shown before the app when no language is set. */
@Component({
  selector: 'app-language-picker',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [TPipe],
  template: `
    <div class="login-wrap">
      <div class="login-card">
        <div class="login-logo">🌐</div>
        <h1 class="login-title">{{ 'lang.choose' | t }}</h1>
        <p class="login-sub">{{ 'lang.chooseSub' | t }}</p>
        <div class="lang-list">
          @for (l of languages; track l.code) {
            <button class="lang-opt" [class.active]="sel() === l.code" (click)="choose(l.code)">
              <span class="lang-native">{{ l.label }}</span>
              <span class="lang-en">{{ l.english }}</span>
            </button>
          }
        </div>
        <button class="btn primary login-btn" (click)="confirm()">{{ 'lang.continue' | t }}</button>
      </div>
    </div>
  `,
  styles: [`
    .lang-list { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 14px 0; }
    .lang-opt { border: 1px solid var(--baseline); background: var(--surface); border-radius: 12px;
      padding: 12px; cursor: pointer; display: flex; flex-direction: column; align-items: flex-start; }
    .lang-opt.active { border-color: var(--primary); box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary) 25%, transparent); }
    .lang-native { font-size: 17px; font-weight: 700; color: var(--ink); }
    .lang-en { font-size: 12px; color: var(--muted); }
  `],
})
export class LanguagePickerComponent {
  private readonly i18n = inject(TranslateService);
  readonly languages = LANGUAGES;
  readonly sel = signal<Lang>(this.i18n.lang());

  constructor() {
    // live-preview the highlighted language on the picker itself
  }

  choose(l: Lang): void { this.sel.set(l); this.i18n.setLang(l, false); }
  confirm(): void { this.i18n.setLang(this.sel(), true); }
}
