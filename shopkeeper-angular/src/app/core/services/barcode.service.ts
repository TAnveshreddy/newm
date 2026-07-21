import { Injectable } from '@angular/core';

// Code 128 symbol width patterns (values 0..106); index 106 is Stop (7 modules).
const C128 = [
  '212222','222122','222221','121223','121322','131222','122213','122312','132212','221213',
  '221312','231212','112232','122132','122231','113222','123122','123221','223211','221132',
  '221231','213212','223112','312131','311222','321122','321221','312212','322112','322211',
  '212123','212321','232121','111323','131123','131321','112313','132113','132311','211313',
  '231113','231311','112133','112331','132131','113123','113321','133121','313121','211331',
  '231131','213113','213311','213131','311123','311321','331121','312113','312311','332111',
  '314111','221411','431111','111224','111422','121124','121421','141122','141221','112214',
  '112412','122114','122411','142112','142211','241211','221114','413111','241112','134111',
  '111242','121142','121241','114212','124112','124211','411212','421112','421211','212141',
  '214121','412121','111143','111341','131141','114113','114311','411113','411311','113141',
  '114131','311141','411131','211412','211214','211232','2331112',
];

/**
 * Code 128-B barcode generation. Pure/offline, no external library — renders an
 * inline SVG that the browser can print and a USB/Bluetooth scanner reads back.
 */
@Injectable({ providedIn: 'root' })
export class BarcodeService {
  /** Render an ASCII string as a Code 128-B SVG barcode. */
  svg(text: string, opts: { module?: number; height?: number } = {}): string {
    const mod = opts.module ?? 1.5;
    const H = opts.height ?? 40;
    const s = String(text ?? '');
    if (!s) return '';
    const codes = [104];
    let sum = 104;
    for (let i = 0; i < s.length; i++) {
      let v = s.charCodeAt(i) - 32;
      if (v < 0 || v > 94) v = 0;
      codes.push(v);
      sum += v * (i + 1);
    }
    codes.push(sum % 103);
    codes.push(106);
    let x = 0, rects = '';
    for (const c of codes) {
      const pat = C128[c];
      let bar = true;
      for (const ch of pat) {
        const w = Number(ch) * mod;
        if (bar) rects += `<rect x="${x.toFixed(2)}" y="0" width="${w.toFixed(2)}" height="${H}"/>`;
        x += w;
        bar = !bar;
      }
    }
    return `<svg width="${x.toFixed(2)}" height="${H}" viewBox="0 0 ${x.toFixed(2)} ${H}" xmlns="http://www.w3.org/2000/svg" fill="#000">${rects}</svg>`;
  }

  /** Unique 12-digit numeric code not already used by `existing`. */
  generate(existing: string[]): string {
    const used = new Set(existing);
    let code: string;
    do {
      code = String(Math.floor(200000000000 + Math.random() * 799999999999));
    } while (used.has(code));
    return code;
  }
}
