/* VyaparOpen — import.js : bulk import Items & Parties from Excel (.xlsx) or CSV */
'use strict';

/* ---------- CSV parsing (handles quotes, commas, CRLF, embedded newlines) ---------- */
function parseCSV(text) {
  const rows = [];
  let row = [], field = '', inQ = false;
  if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1); // strip BOM
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else inQ = false;
      } else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(field); field = '';
      rows.push(row); row = [];
    } else field += c;
  }
  if (field !== '' || row.length) { row.push(field); rows.push(row); }
  return rows.filter(r => r.some(c => String(c).trim() !== ''));
}

/* ---------- minimal XLSX reader (first worksheet) ----------
   A .xlsx is a ZIP of XML files. We parse the ZIP central directory,
   inflate entries with the browser's DecompressionStream, and read
   xl/worksheets/sheetN.xml + xl/sharedStrings.xml. No libraries. */
async function readXlsxRows(arrayBuffer) {
  const bytes = new Uint8Array(arrayBuffer);
  const view = new DataView(arrayBuffer);

  // find End Of Central Directory record (scan back for signature 0x06054b50)
  let eocd = -1;
  for (let i = bytes.length - 22; i >= Math.max(0, bytes.length - 22 - 65535); i--) {
    if (view.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error('Not a valid .xlsx file (ZIP directory not found)');
  const count = view.getUint16(eocd + 10, true);
  let off = view.getUint32(eocd + 16, true);

  const entries = {};
  const dec = new TextDecoder();
  for (let n = 0; n < count; n++) {
    if (view.getUint32(off, true) !== 0x02014b50) break;
    const method = view.getUint16(off + 10, true);
    const csize = view.getUint32(off + 20, true);
    const nameLen = view.getUint16(off + 28, true);
    const extraLen = view.getUint16(off + 30, true);
    const commentLen = view.getUint16(off + 32, true);
    const localOff = view.getUint32(off + 42, true);
    const name = dec.decode(bytes.subarray(off + 46, off + 46 + nameLen));
    entries[name] = { method, csize, localOff };
    off += 46 + nameLen + extraLen + commentLen;
  }

  async function extract(name) {
    const e = entries[name];
    if (!e) return null;
    const nLen = view.getUint16(e.localOff + 26, true);
    const xLen = view.getUint16(e.localOff + 28, true);
    const start = e.localOff + 30 + nLen + xLen;
    const data = bytes.subarray(start, start + e.csize);
    if (e.method === 0) return dec.decode(data);
    if (e.method === 8) {
      const ds = new DecompressionStream('deflate-raw');
      const stream = new Blob([data]).stream().pipeThrough(ds);
      return await new Response(stream).text();
    }
    throw new Error('Unsupported compression in .xlsx');
  }

  // first worksheet (lowest sheet number)
  const sheetName = Object.keys(entries)
    .filter(n => /^xl\/worksheets\/sheet\d+\.xml$/.test(n))
    .sort((a, b) => parseInt(a.match(/\d+/)[0]) - parseInt(b.match(/\d+/)[0]))[0];
  if (!sheetName) throw new Error('No worksheet found in the Excel file');

  const sheetXml = await extract(sheetName);
  const sharedXml = await extract('xl/sharedStrings.xml');

  const parser = new DOMParser();
  const shared = [];
  if (sharedXml) {
    const sdoc = parser.parseFromString(sharedXml, 'application/xml');
    sdoc.querySelectorAll('si').forEach(si => {
      let s = '';
      si.querySelectorAll('t').forEach(t => { s += t.textContent; });
      shared.push(s);
    });
  }

  const doc = parser.parseFromString(sheetXml, 'application/xml');
  const rows = [];
  doc.querySelectorAll('row').forEach(rEl => {
    const cells = [];
    rEl.querySelectorAll('c').forEach(cEl => {
      const ref = cEl.getAttribute('r') || '';
      const colLetters = ref.replace(/\d+/g, '');
      let col = 0;
      for (const ch of colLetters) col = col * 26 + (ch.charCodeAt(0) - 64);
      col = Math.max(1, col) - 1;
      const t = cEl.getAttribute('t');
      let val = '';
      if (t === 'inlineStr') {
        val = cEl.textContent;
      } else {
        const v = cEl.querySelector('v');
        val = v ? v.textContent : '';
        if (t === 's') val = shared[parseInt(val)] != null ? shared[parseInt(val)] : '';
        if (t === 'b') val = val === '1' ? 'TRUE' : 'FALSE';
      }
      cells[col] = val;
    });
    for (let i = 0; i < cells.length; i++) if (cells[i] === undefined) cells[i] = '';
    if (cells.some(c => String(c).trim() !== '')) rows.push(cells);
  });
  return rows;
}

/* ---------- column definitions & header matching ---------- */
const IMPORT_DEFS = {
  items: {
    title: 'Import Items',
    template: 'items-import-template.csv',
    columns: [
      { key: 'name', label: 'Item Name', required: true, match: ['name', 'itemname', 'item', 'product', 'productname'] },
      { key: 'category', label: 'Category', match: ['category', 'group', 'itemcategory'] },
      { key: 'unit', label: 'Unit', match: ['unit', 'uom', 'baseunit'] },
      { key: 'hsn', label: 'HSN', match: ['hsn', 'hsncode', 'hsnsac', 'sac', 'saccode', 'code', 'itemcode'] },
      { key: 'description', label: 'Description', match: ['description', 'desc', 'productdescription', 'itemdescription', 'details'] },
      { key: 'salePrice', label: 'Sale Price', num: true, match: ['saleprice', 'sellingprice', 'price', 'rate', 'mrp', 'salerate'] },
      { key: 'purchasePrice', label: 'Purchase Price', num: true, match: ['purchaseprice', 'costprice', 'cost', 'purchaserate', 'buyprice'] },
      { key: 'taxRate', label: 'GST %', num: true, match: ['gst', 'gstrate', 'tax', 'taxrate', 'gstpercent', 'igst'] },
      { key: 'openingStock', label: 'Opening Stock', num: true, match: ['openingstock', 'stock', 'qty', 'quantity', 'currentstock', 'openingqty'] },
      { key: 'minStock', label: 'Min Stock', num: true, match: ['minstock', 'minimumstock', 'reorderlevel', 'lowstock', 'minqty'] },
      { key: 'type', label: 'Type', match: ['type', 'itemtype'] }
    ],
    sample: [['Item Name', 'Category', 'Unit', 'HSN', 'Description', 'Sale Price', 'Purchase Price', 'GST %', 'Opening Stock', 'Min Stock', 'Type'],
      ['Basmati Rice 5kg', 'Grocery', 'BAG', '1006', 'Premium aged basmati', '550', '470', '5', '40', '10', 'product'],
      ['Home Delivery', 'Services', 'SERVICE', '9965', 'Delivery within city limits', '50', '0', '18', '', '', 'service']]
  },
  parties: {
    title: 'Import Parties',
    template: 'parties-import-template.csv',
    columns: [
      { key: 'name', label: 'Party Name', required: true, match: ['name', 'partyname', 'party', 'customername', 'customer', 'suppliername', 'businessname'] },
      { key: 'phone', label: 'Phone', match: ['phone', 'mobile', 'phonenumber', 'mobilenumber', 'contact', 'contactno'] },
      { key: 'email', label: 'Email', match: ['email', 'emailid', 'mail'] },
      { key: 'gstin', label: 'GSTIN', match: ['gstin', 'gst', 'gstno', 'gstnumber', 'gstinno'] },
      { key: 'type', label: 'Type', match: ['type', 'partytype'] },
      { key: 'address', label: 'Address', match: ['address', 'billingaddress', 'city', 'location'] },
      { key: 'openingBalance', label: 'Opening Balance', num: true, match: ['openingbalance', 'balance', 'openingamount', 'openbalance'] },
      { key: 'openingType', label: 'Balance Type', match: ['balancetype', 'openingtype', 'drcr', 'direction'] }
    ],
    sample: [['Party Name', 'Phone', 'Email', 'GSTIN', 'Type', 'Address', 'Opening Balance', 'Balance Type'],
      ['Rahul Enterprises', '9812345670', '', '29AAAPL1234C1ZV', 'customer', 'Jayanagar, Bengaluru', '5000', 'receive'],
      ['Mahalaxmi Wholesalers', '9765432109', '', '27AABCM9999Q1Z2', 'supplier', 'Mumbai', '12000', 'pay']]
  }
};

function normHeader(hd) {
  return String(hd || '').toLowerCase().replace(/[^a-z0-9]/g, '');
}

function mapHeaders(def, headerRow) {
  const map = {}; // colIndex -> key
  headerRow.forEach((hd, i) => {
    const n = normHeader(hd);
    if (!n) return;
    for (const col of def.columns) {
      if (col.match.includes(n) && !Object.values(map).includes(col.key)) { map[i] = col.key; break; }
    }
  });
  return map;
}

/* ---------- import UI ---------- */
let _importCtx = null;

function openImportModal(kind) {
  const def = IMPORT_DEFS[kind];
  _importCtx = { kind: kind, rows: null, map: null };
  openModal(
    '<div class="modal-head"><h3>' + def.title + ' from Excel / CSV</h3><button class="x" onclick="closeModal()">×</button></div>' +
    '<div class="modal-body">' +
    '<p class="sub">Upload an Excel file (<strong>.xlsx</strong>) or CSV with a header row. Columns are matched by name — download the template to see the expected format. From Excel you can also use <em>File → Save As → CSV</em>.</p>' +
    '<div class="head-actions" style="margin:12px 0">' +
    '<button class="btn ghost" onclick="downloadImportTemplate(\'' + kind + '\')">⬇ Download Template</button>' +
    '<button class="btn primary" onclick="el(\'imp_file\').click()">Choose File…</button>' +
    '<input type="file" id="imp_file" accept=".xlsx,.csv,text/csv" style="display:none" onchange="handleImportFile(this)">' +
    '</div>' +
    '<div id="imp_preview"></div>' +
    '</div>' +
    '<div class="modal-foot">' +
    '<label class="switch-row" style="margin-right:auto"><input type="checkbox" id="imp_update"> Update existing (matched by name)</label>' +
    '<button class="btn ghost" onclick="closeModal()">Cancel</button>' +
    '<button class="btn primary" id="imp_go" disabled onclick="runImport()">Import</button></div>',
    true
  );
}

function downloadImportTemplate(kind) {
  const def = IMPORT_DEFS[kind];
  downloadFile(def.template, toCSV(def.sample), 'text/csv;charset=utf-8');
  toast('Template downloaded — fill it in Excel and upload it back (as .xlsx or .csv)');
}

async function handleImportFile(input) {
  const f = input.files && input.files[0];
  if (!f) return;
  const def = IMPORT_DEFS[_importCtx.kind];
  try {
    let rows;
    if (/\.xlsx$/i.test(f.name)) {
      rows = await readXlsxRows(await f.arrayBuffer());
    } else {
      rows = parseCSV(await f.text());
    }
    if (!rows || rows.length < 2) throw new Error('File needs a header row plus at least one data row');
    const map = mapHeaders(def, rows[0]);
    const nameCol = Object.keys(map).find(i => map[i] === 'name');
    if (nameCol === undefined) throw new Error('Could not find a "' + def.columns[0].label + '" column in the header row');
    _importCtx.rows = rows;
    _importCtx.map = map;
    renderImportPreview();
  } catch (e) {
    el('imp_preview').innerHTML = '<p class="empty" style="color:var(--bad)">⚠ ' + esc(e.message) + '</p>';
    el('imp_go').disabled = true;
  }
  input.value = '';
}

function renderImportPreview() {
  const def = IMPORT_DEFS[_importCtx.kind];
  const { rows, map } = _importCtx;
  const cols = Object.keys(map).map(Number);
  const data = rows.slice(1);
  const valid = data.filter(r => String(r[cols.find(c => map[c] === 'name')] || '').trim() !== '');

  let html = '<p><strong>' + valid.length + '</strong> of ' + data.length + ' rows ready to import. Matched columns: ' +
    cols.map(c => '<span class="tag">' + esc(rows[0][c]) + ' → ' + def.columns.find(x => x.key === map[c]).label + '</span>').join(' ') + '</p>';
  html += '<div class="table-wrap" style="max-height:260px;overflow-y:auto"><table><thead><tr>' +
    cols.map(c => '<th>' + esc(def.columns.find(x => x.key === map[c]).label) + '</th>').join('') + '</tr></thead><tbody>' +
    valid.slice(0, 8).map(r => '<tr>' + cols.map(c => '<td>' + esc(r[c] == null ? '' : r[c]) + '</td>').join('') + '</tr>').join('') +
    '</tbody></table></div>';
  if (valid.length > 8) html += '<p class="sub">…and ' + (valid.length - 8) + ' more rows.</p>';
  el('imp_preview').innerHTML = html;
  el('imp_go').disabled = valid.length === 0;
}

function runImport() {
  const kind = _importCtx.kind;
  const def = IMPORT_DEFS[kind];
  const { rows, map } = _importCtx;
  const cols = Object.keys(map).map(Number);
  const updateExisting = el('imp_update').checked;
  let added = 0, updated = 0, skipped = 0;

  for (const r of rows.slice(1)) {
    const rec = {};
    for (const c of cols) {
      const colDef = def.columns.find(x => x.key === map[c]);
      let v = r[c] == null ? '' : String(r[c]).trim();
      rec[colDef.key] = colDef.num ? num(v) : v;
    }
    if (!rec.name) { skipped++; continue; }

    if (kind === 'items') {
      rec.type = /^s/i.test(rec.type || '') ? 'service' : 'product';
      rec.unit = (rec.unit || 'PCS').toUpperCase();
      rec.taxRate = GST_RATES.includes(num(rec.taxRate)) ? num(rec.taxRate) : num(rec.taxRate) || 0;
      const existing = state.items.find(i => i.name.toLowerCase() === rec.name.toLowerCase());
      if (existing) {
        if (updateExisting) { Object.assign(existing, rec); updated++; } else skipped++;
      } else {
        state.items.push(Object.assign({ id: uid(), createdAt: Date.now(), category: '', hsn: '', description: '', salePrice: 0, purchasePrice: 0, taxRate: 0, openingStock: 0, minStock: 0 }, rec));
        added++;
      }
    } else {
      const t = (rec.type || '').toLowerCase();
      rec.type = t.startsWith('s') ? 'supplier' : t.startsWith('b') ? 'both' : 'customer';
      const ot = (rec.openingType || '').toLowerCase();
      rec.openingType = (ot.startsWith('p') || ot.startsWith('cr') || ot === 'topay') ? 'pay' : 'receive';
      rec.gstin = (rec.gstin || '').toUpperCase();
      const existing = state.parties.find(p => p.name.toLowerCase() === rec.name.toLowerCase());
      if (existing) {
        if (updateExisting) { Object.assign(existing, rec); updated++; } else skipped++;
      } else {
        state.parties.push(Object.assign({ id: uid(), createdAt: Date.now(), phone: '', email: '', gstin: '', address: '', openingBalance: 0, openingType: 'receive' }, rec));
        added++;
      }
    }
  }
  save();
  closeModal();
  toast('Imported: ' + added + ' added' + (updated ? ', ' + updated + ' updated' : '') + (skipped ? ', ' + skipped + ' skipped' : ''));
  route();
}
