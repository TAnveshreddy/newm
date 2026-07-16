/* VyaparOpen — store.js : persistence + business calculations */
'use strict';

const STORE_KEY = 'vyaparopen_data_v1';

const TXN_TYPES = {
  SALE:            { label: 'Sale Invoice',   prefix: 'INV',  party: 'customer', stock: -1, balance: +1 },
  SALE_RETURN:     { label: 'Credit Note',    prefix: 'CRN',  party: 'customer', stock: +1, balance: -1 },
  ESTIMATE:        { label: 'Estimate',       prefix: 'EST',  party: 'customer', stock: 0,  balance: 0 },
  PURCHASE:        { label: 'Purchase Bill',  prefix: 'PUR',  party: 'supplier', stock: +1, balance: -1 },
  PURCHASE_RETURN: { label: 'Debit Note',     prefix: 'DBN',  party: 'supplier', stock: -1, balance: +1 },
  PAYMENT_IN:      { label: 'Payment In',     prefix: 'RCPT', party: 'customer', stock: 0,  balance: -1 },
  PAYMENT_OUT:     { label: 'Payment Out',    prefix: 'PAY',  party: 'supplier', stock: 0,  balance: +1 },
  EXPENSE:         { label: 'Expense',        prefix: 'EXP',  party: 'supplier', stock: 0,  balance: 0 }
};

const PAY_MODES = ['Cash', 'UPI', 'Bank Transfer', 'Card', 'Cheque', 'Credit'];
const UNITS = ['PCS', 'KG', 'GM', 'LTR', 'ML', 'MTR', 'BOX', 'DOZEN', 'BAG', 'BOTTLE', 'PACKET', 'PAIR', 'SET', 'HOUR', 'DAY', 'SERVICE'];
const GST_RATES = [0, 0.25, 3, 5, 12, 18, 28];
const EXPENSE_CATEGORIES = ['Rent', 'Salary', 'Electricity', 'Transport', 'Telephone & Internet', 'Tea & Refreshments', 'Repairs', 'Marketing', 'Stationery', 'Fuel', 'Insurance', 'Other'];

function defaultState() {
  return {
    version: 1,
    settings: {
      businessName: 'My Business',
      tagline: '',
      address: '',
      phone: '',
      email: '',
      gstin: '',
      taxEnabled: true,
      theme: 'light',
      terms: 'Thanks for doing business with us!',
      upiId: '',
      signatureName: ''
    },
    counters: { SALE: 1, SALE_RETURN: 1, ESTIMATE: 1, PURCHASE: 1, PURCHASE_RETURN: 1, PAYMENT_IN: 1, PAYMENT_OUT: 1, EXPENSE: 1 },
    parties: [],
    items: [],
    txns: [],
    adjustments: []
  };
}

let state = load();

function load() {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) {
      const s = JSON.parse(raw);
      // merge over defaults so new fields appear after upgrades
      const d = defaultState();
      s.settings = Object.assign(d.settings, s.settings || {});
      s.counters = Object.assign(d.counters, s.counters || {});
      s.parties = s.parties || []; s.items = s.items || [];
      s.txns = s.txns || []; s.adjustments = s.adjustments || [];
      return s;
    }
  } catch (e) { console.error('load failed', e); }
  return defaultState();
}

function save() {
  try {
    state.meta = state.meta || {};
    state.meta.updatedAt = Date.now();
    localStorage.setItem(STORE_KEY, JSON.stringify(state));
  } catch (e) {
    toast('Could not save data: ' + e.message, 'error');
  }
}

function nextNumber(type) {
  return TXN_TYPES[type].prefix + '-' + String(state.counters[type]).padStart(4, '0');
}

function bumpCounter(type) {
  state.counters[type]++;
}

/* ---------- lookups ---------- */
function getParty(id) { return state.parties.find(p => p.id === id) || null; }
function getItem(id) { return state.items.find(i => i.id === id) || null; }
function getTxn(id) { return state.txns.find(t => t.id === id) || null; }
function partyName(id) {
  const p = getParty(id);
  return p ? p.name : 'Cash Sale';
}

/* ---------- balances ----------
   Party balance sign convention: positive = party owes us (receivable),
   negative = we owe the party (payable). */
function partyOpening(p) {
  const v = num(p.openingBalance);
  return p.openingType === 'pay' ? -v : v;
}

function txnDue(t) {
  const cfg = TXN_TYPES[t.type];
  if (cfg.balance === 0) return 0;
  if (t.type === 'PAYMENT_IN') return -num(t.total);
  if (t.type === 'PAYMENT_OUT') return num(t.total);
  return cfg.balance * (num(t.total) - num(t.paid));
}

function partyBalance(partyId) {
  const p = getParty(partyId);
  if (!p) return 0;
  let bal = partyOpening(p);
  for (const t of state.txns) {
    if (t.partyId === partyId) bal += txnDue(t);
  }
  return round2(bal);
}

function totalsReceivablePayable() {
  let recv = 0, pay = 0;
  for (const p of state.parties) {
    const b = partyBalance(p.id);
    if (b > 0) recv += b; else pay += -b;
  }
  return { receivable: round2(recv), payable: round2(pay) };
}

/* ---------- stock ---------- */
function itemStock(itemId) {
  const it = getItem(itemId);
  if (!it || it.type === 'service') return 0;
  let qty = num(it.openingStock);
  for (const t of state.txns) {
    const dir = TXN_TYPES[t.type].stock;
    if (!dir || !t.lines) continue;
    for (const l of t.lines) {
      if (l.itemId === itemId) qty += dir * num(l.qty);
    }
  }
  for (const a of state.adjustments) {
    if (a.itemId === itemId) qty += num(a.delta);
  }
  return round2(qty);
}

function stockValue() {
  let v = 0;
  for (const it of state.items) {
    if (it.type === 'service') continue;
    v += Math.max(0, itemStock(it.id)) * num(it.purchasePrice || it.salePrice);
  }
  return round2(v);
}

function isLowStock(it) {
  if (it.type === 'service') return false;
  const stock = itemStock(it.id);
  // out of stock always alerts; otherwise alert at/below the item's min level
  return stock <= 0 || (num(it.minStock) > 0 && stock <= num(it.minStock));
}

function lowStockItems() {
  return state.items.filter(isLowStock);
}

/* ---------- txn helpers ---------- */
function txnStatus(t) {
  const cfg = TXN_TYPES[t.type];
  if (t.type === 'ESTIMATE') return t.convertedTo ? 'Converted' : 'Open';
  if (cfg.balance === 0 || t.type === 'PAYMENT_IN' || t.type === 'PAYMENT_OUT') return 'Paid';
  const due = num(t.total) - num(t.paid);
  if (due <= 0.005) return 'Paid';
  if (num(t.paid) > 0) return 'Partial';
  return 'Unpaid';
}

/* ---------- profit ----------
   Profit on a sale = net taxable revenue (after discounts, excl. GST)
   minus cost of goods. Cost is snapshotted on the line at billing time
   (l.cost); falls back to the item's current purchase price. */
function lineCost(l) {
  if (l.cost != null) return num(l.cost);
  const it = getItem(l.itemId);
  return it ? num(it.purchasePrice) : 0;
}

function txnProfit(t) {
  if (t.type !== 'SALE' && t.type !== 'SALE_RETURN') return 0;
  const revenue = num(t.subtotal) - num(t.discount);
  let cost = 0;
  for (const l of (t.lines || [])) cost += lineCost(l) * num(l.qty);
  const p = round2(revenue - cost);
  return t.type === 'SALE' ? p : -p;
}

/* GST split: if both GSTINs exist and state codes (first 2 digits) differ → IGST, else CGST+SGST */
function taxSplitFor(t) {
  const p = t.partyId ? getParty(t.partyId) : null;
  const biz = (state.settings.gstin || '').slice(0, 2);
  const par = (p && p.gstin ? p.gstin : '').slice(0, 2);
  if (biz && par && biz !== par) return 'IGST';
  return 'CGST_SGST';
}

/* compute line + txn totals from a draft txn's lines & discount */
function computeTotals(lines, discountPct, taxEnabled) {
  let subtotal = 0, taxAmount = 0;
  for (const l of lines) {
    const gross = num(l.qty) * num(l.rate);
    const lineDisc = gross * num(l.disc || 0) / 100;
    const taxable = gross - lineDisc;
    const tax = taxEnabled ? taxable * num(l.taxRate || 0) / 100 : 0;
    l.amount = round2(taxable);
    l.tax = round2(tax);
    subtotal += taxable;
    taxAmount += tax;
  }
  const discount = subtotal * num(discountPct || 0) / 100;
  // overall discount applied on taxable value proportionally reduces tax too
  const taxAfter = subtotal > 0 ? taxAmount * (1 - num(discountPct || 0) / 100) : 0;
  const raw = subtotal - discount + taxAfter;
  const total = Math.round(raw);
  return {
    subtotal: round2(subtotal),
    discount: round2(discount),
    taxAmount: round2(taxAfter),
    roundOff: round2(total - raw),
    total: round2(total)
  };
}

function deleteTxn(id) {
  state.txns = state.txns.filter(t => t.id !== id);
  save();
}

/* ---------- backup / restore ---------- */
function exportBackup() {
  downloadFile('shopkeeper-backup-' + todayStr() + '.json', JSON.stringify(state, null, 2), 'application/json');
  toast('Backup downloaded');
}

function importBackup(file, done) {
  const r = new FileReader();
  r.onload = () => {
    try {
      const s = JSON.parse(r.result);
      if (!s || !s.settings || !Array.isArray(s.txns)) throw new Error('Not a Shopkeeper backup file');
      state = s;
      // re-merge defaults for forward compatibility
      const d = defaultState();
      state.settings = Object.assign(d.settings, state.settings);
      state.counters = Object.assign(d.counters, state.counters || {});
      state.parties = state.parties || []; state.items = state.items || [];
      state.txns = state.txns || []; state.adjustments = state.adjustments || [];
      save();
      done(true);
    } catch (e) {
      done(false, e.message);
    }
  };
  r.readAsText(file);
}

/* ---------- demo data ---------- */
function loadDemoData() {
  const s = defaultState();
  s.settings.businessName = 'Shree Ganesh Traders';
  s.settings.address = '12, MG Road, Bengaluru, Karnataka - 560001';
  s.settings.phone = '9876543210';
  s.settings.email = 'shreeganesh@example.com';
  s.settings.gstin = '29ABCDE1234F1Z5';

  const cust1 = { id: uid(), name: 'Rahul Enterprises', phone: '9812345670', email: '', gstin: '29AAAPL1234C1ZV', address: 'Jayanagar, Bengaluru', type: 'customer', openingBalance: 0, openingType: 'receive', createdAt: Date.now() };
  const cust2 = { id: uid(), name: 'Sneha Retail Mart', phone: '9898989898', email: '', gstin: '', address: 'Indiranagar, Bengaluru', type: 'customer', openingBalance: 2500, openingType: 'receive', createdAt: Date.now() };
  const supp1 = { id: uid(), name: 'Mahalaxmi Wholesalers', phone: '9765432109', email: '', gstin: '27AABCM9999Q1Z2', address: 'Crawford Market, Mumbai', type: 'supplier', openingBalance: 0, openingType: 'pay', createdAt: Date.now() };
  s.parties = [cust1, cust2, supp1];

  const it1 = { id: uid(), name: 'Basmati Rice 5kg', hsn: '1006', category: 'Grocery', unit: 'BAG', salePrice: 550, purchasePrice: 470, taxRate: 5, openingStock: 40, minStock: 10, type: 'product', createdAt: Date.now() };
  const it2 = { id: uid(), name: 'Sunflower Oil 1L', hsn: '1512', category: 'Grocery', unit: 'BOTTLE', salePrice: 160, purchasePrice: 138, taxRate: 5, openingStock: 60, minStock: 12, type: 'product', createdAt: Date.now() };
  const it3 = { id: uid(), name: 'Detergent Powder 1kg', hsn: '3402', category: 'Home Care', unit: 'PACKET', salePrice: 120, purchasePrice: 95, taxRate: 18, openingStock: 25, minStock: 8, type: 'product', createdAt: Date.now() };
  const it4 = { id: uid(), name: 'Home Delivery Charge', hsn: '9965', category: 'Services', unit: 'SERVICE', salePrice: 50, purchasePrice: 0, taxRate: 18, openingStock: 0, minStock: 0, type: 'service', createdAt: Date.now() };
  s.items = [it1, it2, it3, it4];

  function mkLines(specs) {
    return specs.map(([it, qty, rate]) => ({ itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: qty, rate: rate, disc: 0, taxRate: it.taxRate }));
  }
  function mkTxn(type, daysAgo, partyId, lines, paid, mode) {
    const totals = computeTotals(lines, 0, true);
    const t = Object.assign({
      id: uid(), type: type, number: nextNumberFor(s, type), date: addDays(todayStr(), -daysAgo),
      partyId: partyId, lines: lines, discountPct: 0,
      paid: paid == null ? totals.total : paid, mode: mode || 'Cash', notes: '', createdAt: Date.now()
    }, totals);
    s.counters[type]++;
    return t;
  }
  function nextNumberFor(st, type) {
    return TXN_TYPES[type].prefix + '-' + String(st.counters[type]).padStart(4, '0');
  }

  s.txns.push(mkTxn('PURCHASE', 20, supp1.id, mkLines([[it1, 30, 470], [it2, 50, 138]]), 10000, 'Bank Transfer'));
  s.txns.push(mkTxn('SALE', 15, cust1.id, mkLines([[it1, 10, 550], [it2, 12, 160]]), 5000, 'UPI'));
  s.txns.push(mkTxn('SALE', 9, cust2.id, mkLines([[it2, 6, 160], [it3, 4, 120]]), null, 'Cash'));
  s.txns.push(mkTxn('SALE', 4, cust1.id, mkLines([[it3, 10, 120], [it4, 1, 50]]), 0, 'Credit'));
  s.txns.push(mkTxn('SALE', 1, cust2.id, mkLines([[it1, 2, 550]]), null, 'UPI'));
  const pay = { id: uid(), type: 'PAYMENT_IN', number: nextNumberFor(s, 'PAYMENT_IN'), date: addDays(todayStr(), -2), partyId: cust1.id, total: 2000, paid: 2000, mode: 'UPI', notes: 'Part payment', createdAt: Date.now() };
  s.counters.PAYMENT_IN++;
  s.txns.push(pay);
  const exp = { id: uid(), type: 'EXPENSE', number: nextNumberFor(s, 'EXPENSE'), date: addDays(todayStr(), -3), partyId: null, category: 'Rent', total: 8000, paid: 8000, mode: 'Bank Transfer', notes: 'Shop rent', createdAt: Date.now() };
  s.counters.EXPENSE++;
  s.txns.push(exp);

  state = s;
  save();
}
