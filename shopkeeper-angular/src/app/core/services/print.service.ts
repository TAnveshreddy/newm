import { Injectable, inject } from '@angular/core';

import { BusinessStore } from './business-store.service';
import { BarcodeService } from './barcode.service';
import { ToastService } from './toast.service';
import { Item, Transaction } from '../models';
import { num, round2 } from '../util/num';

/**
 * Client-side printing: opens a print window with self-contained HTML.
 * Handles GST invoices and Code-128 barcode label sheets — no server, no
 * external libraries.
 */
@Injectable({ providedIn: 'root' })
export class PrintService {
  private readonly store = inject(BusinessStore);
  private readonly barcode = inject(BarcodeService);
  private readonly toast = inject(ToastService);

  private money(n: unknown, symbol = true): string {
    const v = round2(num(n));
    const s = Math.abs(v).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    return (v < 0 ? '-' : '') + (symbol ? '₹ ' : '') + s;
  }
  private esc(s: unknown): string {
    return String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c] as string));
  }

  /** Print a GST invoice / voucher for a saved transaction. */
  invoice(txn: Transaction): void {
    const s = this.store.settings();
    const party = txn.partyId ? this.store.getParty(txn.partyId) : null;
    const taxEnabled = s.taxEnabled;
    const due = round2(Math.max(0, num(txn.total) - num(txn.paid)));

    const rows = (txn.lines ?? []).map((l, i) => {
      const taxable = num(l.qty) * num(l.rate);
      const tax = taxEnabled ? (taxable * num(l.taxRate)) / 100 : 0;
      return `<tr>
        <td>${i + 1}</td>
        <td>${this.esc(l.name)}${l.description ? '<div class="mut">' + this.esc(l.description) + '</div>' : ''}</td>
        <td>${this.esc(l.hsn ?? '')}</td>
        <td class="r">${num(l.qty)} ${this.esc(l.unit ?? '')}</td>
        <td class="r">${this.money(l.rate, false)}</td>
        <td class="r">${this.money(taxable, false)}</td>
        ${taxEnabled ? `<td class="r">${num(l.taxRate)}%</td>` : ''}
        <td class="r">${this.money(taxable + tax, false)}</td>
      </tr>`;
    }).join('');

    const cols = taxEnabled ? 8 : 7;
    const html = `<!doctype html><html><head><meta charset="utf-8"><title>${this.esc(txn.number)}</title>
      <style>
        *{box-sizing:border-box}body{font:13px/1.5 Arial,Helvetica,sans-serif;color:#111;margin:0;padding:24px}
        h1{font-size:20px;margin:0}.head{display:flex;justify-content:space-between;border-bottom:2px solid #222;padding-bottom:10px;margin-bottom:12px}
        .mut{color:#666;font-size:11px}table{width:100%;border-collapse:collapse;margin-top:10px}
        th,td{border:1px solid #ccc;padding:6px 8px;text-align:left}.r{text-align:right}
        thead th{background:#f2f4f8}tfoot td{font-weight:700}.title{font-size:16px;font-weight:800;margin:6px 0}
        .two{display:flex;justify-content:space-between;gap:20px;margin-top:8px}
        @media print{body{padding:0}}
      </style></head><body>
      <div class="head">
        <div>
          <h1>${this.esc(s.businessName)}</h1>
          ${s.phone ? `<div class="mut">${this.esc(s.phone)}</div>` : ''}
          ${s.email ? `<div class="mut">${this.esc(s.email)}</div>` : ''}
          ${s.gstin ? `<div class="mut">GSTIN: ${this.esc(s.gstin)}</div>` : ''}
          ${s.address ? `<div class="mut">${this.esc(s.address).replace(/\n/g, '<br>')}</div>` : ''}
        </div>
        <div style="text-align:right"><div class="title">Invoice</div><div>#${this.esc(txn.number)}</div><div class="mut">${this.esc(txn.date)}</div></div>
      </div>
      <div class="two"><div><strong>Bill To:</strong><br>${this.esc(party?.name ?? 'Cash Sale')}<br>
        <span class="mut">${this.esc(party?.phone ?? '')} ${party?.gstin ? '· GSTIN ' + this.esc(party.gstin) : ''}</span></div></div>
      <table><thead><tr><th>#</th><th>Item</th><th>HSN</th><th class="r">Qty</th><th class="r">Rate</th><th class="r">Taxable</th>${taxEnabled ? '<th class="r">GST</th>' : ''}<th class="r">Amount</th></tr></thead>
        <tbody>${rows}</tbody>
        <tfoot>
          <tr><td colspan="${cols - 1}" class="r">Total</td><td class="r">${this.money(txn.total, false)}</td></tr>
          <tr><td colspan="${cols - 1}" class="r">Paid</td><td class="r">${this.money(txn.paid, false)}</td></tr>
          <tr><td colspan="${cols - 1}" class="r">Balance Due</td><td class="r">${this.money(due, false)}</td></tr>
        </tfoot></table>
      ${s.upiId ? `<p class="mut">Pay via UPI: <strong>${this.esc(s.upiId)}</strong></p>` : ''}
      ${s.terms ? `<p class="mut"><strong>Terms:</strong> ${this.esc(s.terms)}</p>` : ''}
      <p style="text-align:right;margin-top:40px">For <strong>${this.esc(s.signatureName || s.businessName)}</strong><br><br>Authorised Signatory</p>
      <script>window.onload=function(){window.print()}<\/script></body></html>`;
    this.open(html);
  }

  /** Print a sheet of Code-128 barcode labels. */
  labels(picks: { item: Item; copies: number }[]): void {
    const s = this.store.settings();
    let cells = '';
    for (const { item, copies } of picks) {
      const price = this.money(item.salePrice) + (item.unit ? ' / ' + this.esc(item.unit) : '');
      for (let k = 0; k < copies; k++) {
        cells += `<div class="label">
          <div class="l-shop">${this.esc(s.businessName)}</div>
          <div class="l-name">${this.esc(item.name)}${item.brand ? ' · ' + this.esc(item.brand) : ''}</div>
          ${this.barcode.svg(item.barcode ?? '', { module: 1.5, height: 34 })}
          <div class="l-code">${this.esc(item.barcode ?? '')}</div>
          <div class="l-price">${price}</div>
        </div>`;
      }
    }
    const html = `<!doctype html><html><head><meta charset="utf-8"><title>Barcode Labels</title><style>
      *{box-sizing:border-box}body{margin:0;font-family:Arial,Helvetica,sans-serif}
      .sheet{display:flex;flex-wrap:wrap;gap:4px;padding:6px}
      .label{width:150px;height:100px;border:1px dashed #bbb;padding:4px 6px;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center;page-break-inside:avoid}
      .l-shop{font-size:9px;color:#333;font-weight:700;text-transform:uppercase;width:100%;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
      .l-name{font-size:10px;margin:1px 0 2px;width:100%;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
      svg{display:block;margin:0 auto}.l-code{font-size:9px;letter-spacing:1px;margin-top:1px}.l-price{font-size:13px;font-weight:800;margin-top:2px}
      @media print{.label{border:none}@page{margin:6mm}}
    </style></head><body><div class="sheet">${cells}</div><script>window.onload=function(){window.print()}<\/script></body></html>`;
    this.open(html);
  }

  private open(html: string): void {
    const w = window.open('', '_blank');
    if (!w) {
      this.toast.error('Pop-up blocked — allow pop-ups to print.');
      return;
    }
    w.document.write(html);
    w.document.close();
  }
}
