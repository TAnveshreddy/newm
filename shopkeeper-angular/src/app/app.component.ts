import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ThemeService } from './core/services/theme.service';
import { TranslateService } from './core/i18n/translate.service';
import { ToastComponent } from './shared/components/toast.component';
import { LanguagePickerComponent } from './features/language/language-picker.component';

@Component({
  selector: 'app-root',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterOutlet, ToastComponent, LanguagePickerComponent],
  template: `
    @if (i18n.chosen()) {
      <!-- Re-create the routed view whenever the language changes so every
           OnPush screen re-renders in the new language (incl. back to English),
           with no page reload. -->
      @for (lang of [i18n.lang()]; track lang) {
        <router-outlet></router-outlet>
      }
    } @else {
      <app-language-picker></app-language-picker>
    }
    <app-toast></app-toast>
  `,
})
export class AppComponent {
  // Instantiating ThemeService here applies the persisted theme app-wide on boot.
  private readonly theme = inject(ThemeService);
  readonly i18n = inject(TranslateService);
}
