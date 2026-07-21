import { Pipe, PipeTransform } from '@angular/core';
import { num } from '../../core/util/num';

/**
 * Formats a number as Indian-rupee currency (₹, Indian digit grouping).
 * Pure pipe — memoised by Angular for efficient change detection.
 */
@Pipe({ name: 'inr', standalone: true })
export class InrPipe implements PipeTransform {
  transform(value: unknown, symbol = true): string {
    const n = round2(num(value));
    const s = Math.abs(n).toLocaleString('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return (n < 0 ? '-' : '') + (symbol ? '₹ ' : '') + s;
  }
}

function round2(v: number): number {
  return Math.round((v + Number.EPSILON) * 100) / 100;
}
