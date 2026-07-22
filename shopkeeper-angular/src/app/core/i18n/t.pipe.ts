import { Pipe, PipeTransform, inject } from '@angular/core';
import { TranslateService } from './translate.service';

/**
 * Translation pipe: `{{ 'nav.dashboard' | t }}`. Impure so it re-evaluates when
 * the active language changes (it reads the language signal each run).
 */
@Pipe({ name: 't', standalone: true, pure: false })
export class TPipe implements PipeTransform {
  private readonly i18n = inject(TranslateService);
  transform(key: string): string {
    return this.i18n.t(key);
  }
}
