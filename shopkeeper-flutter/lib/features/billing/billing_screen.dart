import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';

import '../../core/domain/txn_config.dart';
import '../../core/models/models.dart';
import '../../core/state/providers.dart';
import '../../core/util/money.dart';
import '../../core/util/num_util.dart';
import '../scan/scan_screen.dart';

const List<double> kGstSlabs = [0, 5, 12, 18, 28];

class BillingScreen extends ConsumerStatefulWidget {
  const BillingScreen({super.key});
  @override
  ConsumerState<BillingScreen> createState() => _BillingScreenState();
}

class _BillingScreenState extends ConsumerState<BillingScreen> {
  final _customer = TextEditingController();
  final _contact = TextEditingController();
  final _search = TextEditingController();
  final _brand = TextEditingController();
  final _desc = TextEditingController();

  final List<TxnLine> _lines = [];
  String _mode = 'Cash';
  double _discount = 0;
  bool _discountPct = true;
  double? _paid; // null = pay full
  String? _editingId;

  // structured add-item row
  String? _cat;
  String? _selItemId;
  double _newGst = 18;
  bool _newGstManual = false;

  static const _payModes = ['Cash', 'UPI', 'Card', 'Bank Transfer', 'Credit'];

  @override
  void dispose() {
    _customer.dispose();
    _contact.dispose();
    _search.dispose();
    _brand.dispose();
    _desc.dispose();
    super.dispose();
  }

  // ---- totals ----
  double get _subtotal => round2(_lines.fold(0.0, (s, l) => s + l.qty * l.rate));
  double get _discountAmount {
    final st = _subtotal;
    return _discountPct ? round2(st * _discount / 100) : (_discount < st ? _discount : st);
  }

  double _tax(bool enabled) =>
      enabled ? round2(_lines.fold(0.0, (s, l) => s + l.qty * l.rate * l.taxRate / 100)) : 0;
  double _total(bool enabled) => round2(_subtotal - _discountAmount + _tax(enabled));
  double _paidVal(bool enabled) => _paid ?? _total(enabled);
  double _balanceDue(bool enabled) => round2(_total(enabled) - _paidVal(enabled));

  // ---- line ops ----
  void _add(Item it, bool taxEnabled, {double? gst, bool manual = false, String brand = '', String desc = ''}) {
    setState(() {
      final i = _lines.indexWhere((l) => l.itemId == it.id && l.brand == brand && l.description == desc);
      if (i >= 0) {
        _lines[i] = _lines[i].copyWith(qty: _lines[i].qty + 1);
      } else {
        _lines.add(TxnLine(
          itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: 1, rate: it.salePrice,
          taxRate: taxEnabled ? (gst ?? it.taxRate) : 0, taxManual: manual,
          brand: brand, description: desc, cost: it.purchasePrice,
        ));
      }
    });
  }

  void _addSelected(List<Item> items, bool taxEnabled) {
    final it = items.where((i) => i.id == _selItemId).firstOrNull;
    if (it == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Select an item first')));
      return;
    }
    _add(it, taxEnabled, gst: _newGst, manual: _newGstManual, brand: _brand.text.trim(), desc: _desc.text.trim());
    setState(() {
      _selItemId = null;
      _brand.clear();
      _desc.clear();
      _newGst = 18;
      _newGstManual = false;
    });
  }

  void _setQty(int i, double q) {
    if (q <= 0) {
      setState(() => _lines.removeAt(i));
      return;
    }
    setState(() => _lines[i] = _lines[i].copyWith(qty: q));
  }

  Future<void> _editRate(int i) async {
    final ctrl = TextEditingController(text: _lines[i].rate.toString());
    final v = await showDialog<double>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Rate'),
        content: TextField(
          controller: ctrl, autofocus: true,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(prefixText: '₹ '),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, double.tryParse(ctrl.text) ?? _lines[i].rate), child: const Text('OK')),
        ],
      ),
    );
    if (v != null) setState(() => _lines[i] = _lines[i].copyWith(rate: v));
  }

  Future<void> _customGst({required double current, required ValueChanged<double> onSet}) async {
    final ctrl = TextEditingController(text: current.toString());
    final v = await showDialog<double>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Custom GST %'),
        content: TextField(
          controller: ctrl, autofocus: true,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(suffixText: '%'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, double.tryParse(ctrl.text) ?? current), child: const Text('OK')),
        ],
      ),
    );
    if (v != null) onSet(v);
  }

  Future<void> _scan(bool taxEnabled) async {
    final code = await Navigator.of(context).push<String>(
      MaterialPageRoute(builder: (_) => const ScanScreen(title: 'Scan to add to bill')),
    );
    if (code == null) return;
    final items = ref.read(itemsProvider).value ?? const [];
    final it = items.where((i) => i.barcode.trim() == code.trim()).firstOrNull;
    if (!mounted) return;
    if (it == null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('No item has barcode $code')));
      return;
    }
    _add(it, taxEnabled);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Added ${it.name}')));
  }

  void _clear() {
    setState(() {
      _lines.clear();
      _customer.clear();
      _contact.clear();
      _discount = 0;
      _discountPct = true;
      _paid = null;
      _mode = 'Cash';
      _editingId = null;
    });
  }

  Future<void> _save(BusinessSettings settings, {bool printAfter = false}) async {
    final uid = ref.read(uidProvider);
    if (uid == null || _lines.isEmpty) return;
    final taxEnabled = settings.taxEnabled;
    final parties = ref.read(partiesProvider).value ?? const [];
    final counters = ref.read(countersProvider).value ?? const {};
    final party = parties
        .where((p) => p.type != 'supplier' && p.name.toLowerCase() == _customer.text.trim().toLowerCase())
        .firstOrNull;

    String number;
    int? createdAt;
    if (_editingId != null) {
      final existing = (ref.read(txnsProvider).value ?? const []).where((t) => t.id == _editingId).firstOrNull;
      number = existing?.number ?? '';
      createdAt = existing?.createdAt;
    } else {
      final n = (counters['SALE'] is num) ? (counters['SALE'] as num).toInt() : 1;
      number = '${kTxnTypes['SALE']!.prefix}-${n.toString().padLeft(4, '0')}';
      createdAt = DateTime.now().millisecondsSinceEpoch;
    }

    final txn = Txn(
      id: _editingId ?? makeId(), type: 'SALE', number: number, date: todayIso(),
      partyId: party?.id, lines: List.of(_lines),
      subtotal: _subtotal, discount: _discountAmount,
      total: _total(taxEnabled), paid: _paidVal(taxEnabled), mode: _mode,
      createdAt: createdAt,
    );

    try {
      if (_editingId != null) {
        // Update in place without bumping the counter.
        await ref.read(firestoreServiceProvider).deleteTxn(uid, _editingId!);
      }
      await ref.read(firestoreServiceProvider).saveTxn(uid, txn);
      if (printAfter) {
        await ref.read(pdfServiceProvider).printInvoice(
              txn: txn, settings: settings, partyName: party?.name ?? 'Cash Sale', taxEnabled: taxEnabled,
            );
      }
      if (mounted) {
        _clear();
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Bill ${txn.number} saved')));
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Could not save: $e')));
    }
  }

  void _edit(Txn t) {
    final party = (ref.read(partiesProvider).value ?? const []).where((p) => p.id == t.partyId).firstOrNull;
    setState(() {
      _editingId = t.id;
      _lines
        ..clear()
        ..addAll(t.lines);
      _customer.text = party?.name ?? '';
      _contact.text = party?.phone ?? '';
      _mode = t.mode;
      _discount = t.discount;
      _discountPct = false; // stored as an amount
      _paid = t.paid;
    });
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Editing ${t.number}')));
  }

  Future<void> _delete(Txn t) async {
    final uid = ref.read(uidProvider);
    if (uid == null) return;
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text('Delete ${t.number}?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Delete')),
        ],
      ),
    );
    if (ok == true) {
      await ref.read(firestoreServiceProvider).deleteTxn(uid, t.id);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Deleted')));
    }
  }

  void _whatsapp(Txn t, BusinessSettings s) {
    final party = (ref.read(partiesProvider).value ?? const []).where((p) => p.id == t.partyId).firstOrNull;
    final due = round2(t.total - t.paid);
    final b = StringBuffer('*${s.businessName}*\n');
    b.write('Invoice: ${t.number}\nDate: ${t.date}\n\n');
    for (final l in t.lines) {
      b.write('${l.name} x ${qty(l.qty)} = ${money(l.qty * l.rate)}\n');
    }
    b.write('\nTotal: ${money(t.total)}\nReceived: ${money(t.paid)}\nBalance Due: ${money(due)}\n');
    if (s.upiId.isNotEmpty) b.write('\nPay via UPI: ${s.upiId}\n');
    b.write('\nThank you for your business!');
    final subject = 'Invoice ${t.number}${party != null ? ' — ${party.name}' : ''}';
    Share.share(b.toString(), subject: subject);
  }

  String _status(Txn t) {
    final due = t.total - t.paid;
    if (due <= 0.005) return 'Paid';
    return t.paid > 0 ? 'Partial' : 'Unpaid';
  }

  @override
  Widget build(BuildContext context) {
    final items = ref.watch(itemsProvider).value ?? const [];
    final parties = ref.watch(partiesProvider).value ?? const [];
    final settings = ref.watch(settingsProvider).value ?? BusinessSettings();
    final taxEnabled = settings.taxEnabled;
    final txns = ref.watch(txnsProvider).value ?? const [];

    final categories = <String>{for (final i in items) if (i.category.isNotEmpty) i.category}.toList()..sort();
    final itemsInCat = items.where((i) => _cat == null || i.category == _cat).toList()
      ..sort((a, b) => a.name.compareTo(b.name));

    final q = _search.text.toLowerCase();
    final matches = items
        .where((i) => q.isNotEmpty && (i.name.toLowerCase().contains(q) || i.barcode.contains(q)))
        .take(8)
        .toList();

    final recent = txns.where((t) => t.type == 'SALE').toList()
      ..sort((a, b) => (b.createdAt ?? 0).compareTo(a.createdAt ?? 0));
    final recentBills = recent.take(20).toList();

    String partyName(String? id) => parties.where((p) => p.id == id).firstOrNull?.name ?? 'Cash Sale';

    return Scaffold(
      appBar: AppBar(title: Text(_editingId == null ? 'Billing' : 'Editing bill'), actions: [
        IconButton(icon: const Icon(Icons.qr_code_scanner), tooltip: 'Scan barcode', onPressed: () => _scan(taxEnabled)),
        if (_lines.isNotEmpty || _editingId != null) TextButton(onPressed: _clear, child: const Text('Clear')),
      ]),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          // customer + contact + mode
          TextField(controller: _customer, decoration: const InputDecoration(labelText: 'Customer (optional)', prefixIcon: Icon(Icons.person_outline))),
          const SizedBox(height: 8),
          Row(children: [
            Expanded(child: TextField(controller: _contact, keyboardType: TextInputType.phone, maxLength: 10, decoration: const InputDecoration(labelText: 'Contact', counterText: ''))),
            const SizedBox(width: 8),
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _mode,
                decoration: const InputDecoration(labelText: 'Payment Mode'),
                items: [for (final m in _payModes) DropdownMenuItem(value: m, child: Text(m))],
                onChanged: (v) => setState(() => _mode = v ?? 'Cash'),
              ),
            ),
          ]),
          const Divider(height: 24),

          // structured add-item row
          Text('Add item', style: Theme.of(context).textTheme.labelLarge),
          const SizedBox(height: 8),
          Row(children: [
            Expanded(
              child: DropdownButtonFormField<String?>(
                value: _cat,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Category'),
                items: [
                  const DropdownMenuItem<String?>(value: null, child: Text('All')),
                  for (final c in categories) DropdownMenuItem<String?>(value: c, child: Text(c, overflow: TextOverflow.ellipsis)),
                ],
                onChanged: (v) => setState(() { _cat = v; _selItemId = null; }),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: DropdownButtonFormField<String?>(
                value: _selItemId,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Item'),
                items: [
                  const DropdownMenuItem<String?>(value: null, child: Text('Select item')),
                  for (final it in itemsInCat)
                    DropdownMenuItem<String?>(value: it.id, child: Text(it.brand.isNotEmpty ? '${it.name} (${it.brand})' : it.name, overflow: TextOverflow.ellipsis)),
                ],
                onChanged: (v) {
                  final it = items.where((i) => i.id == v).firstOrNull;
                  setState(() {
                    _selItemId = v;
                    _brand.text = it?.brand ?? '';
                    _desc.text = it?.description ?? '';
                    final g = taxEnabled ? (it?.taxRate ?? 18) : 0;
                    _newGst = g.toDouble();
                    _newGstManual = !kGstSlabs.contains(g);
                  });
                },
              ),
            ),
          ]),
          const SizedBox(height: 8),
          Row(children: [
            Expanded(child: TextField(controller: _brand, decoration: const InputDecoration(labelText: 'Brand'))),
            const SizedBox(width: 8),
            Expanded(child: TextField(controller: _desc, decoration: const InputDecoration(labelText: 'Description'))),
          ]),
          const SizedBox(height: 8),
          Row(children: [
            Expanded(
              child: _GstDropdown(
                rate: _newGst,
                manual: _newGstManual,
                label: 'GST %',
                onSlab: (r) => setState(() { _newGst = r; _newGstManual = false; }),
                onCustom: () => _customGst(current: _newGst, onSet: (v) => setState(() { _newGst = v; _newGstManual = true; })),
              ),
            ),
            const SizedBox(width: 8),
            FilledButton.icon(onPressed: () => _addSelected(items, taxEnabled), icon: const Icon(Icons.add), label: const Text('Add to Bill')),
          ]),
          const SizedBox(height: 12),

          // quick search add
          TextField(
            controller: _search,
            decoration: const InputDecoration(labelText: 'Search product (quick add)', prefixIcon: Icon(Icons.search)),
            onChanged: (_) => setState(() {}),
          ),
          ...matches.map((it) => ListTile(
                dense: true,
                title: Text(it.name),
                trailing: Text(money(it.salePrice)),
                onTap: () {
                  _add(it, taxEnabled);
                  _search.clear();
                  setState(() {});
                },
              )),
          const Divider(height: 24),

          // lines
          if (_lines.isEmpty)
            Padding(padding: const EdgeInsets.symmetric(vertical: 24), child: Center(child: Text('Add products to start the bill.', style: TextStyle(color: Colors.grey.shade600))))
          else
            ...List.generate(_lines.length, (i) => _lineCard(i, taxEnabled)),

          if (_lines.isNotEmpty) ...[
            const Divider(height: 24),
            _totalsPanel(taxEnabled),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(child: OutlinedButton(onPressed: () => _save(settings), child: Text(_editingId == null ? 'Save Bill' : 'Update Bill'))),
              const SizedBox(width: 8),
              Expanded(child: FilledButton.icon(onPressed: () => _save(settings, printAfter: true), icon: const Icon(Icons.print_outlined), label: const Text('Save & Print'))),
            ]),
          ],

          // recent bills
          const Divider(height: 32),
          Text('Recent Bills', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          if (recentBills.isEmpty)
            Padding(padding: const EdgeInsets.all(8), child: Text('No bills yet.', style: TextStyle(color: Colors.grey.shade600)))
          else
            ...recentBills.map((t) => _recentTile(t, partyName(t.partyId), settings)),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _lineCard(int i, bool taxEnabled) {
    final l = _lines[i];
    final tot = round2(l.qty * l.rate * (taxEnabled ? (1 + l.taxRate / 100) : 1));
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 4, 8),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Text(l.name, style: const TextStyle(fontWeight: FontWeight.w700))),
            IconButton(icon: const Icon(Icons.close, size: 20), onPressed: () => setState(() => _lines.removeAt(i))),
          ]),
          if (l.brand.isNotEmpty || l.description.isNotEmpty)
            Text([l.brand, l.unit, l.description].where((x) => x.isNotEmpty).join(' · '), style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
          const SizedBox(height: 4),
          Row(children: [
            IconButton(icon: const Icon(Icons.remove_circle_outline), onPressed: () => _setQty(i, l.qty - 1)),
            Text(qty(l.qty)),
            IconButton(icon: const Icon(Icons.add_circle_outline), onPressed: () => _setQty(i, l.qty + 1)),
            const Spacer(),
            TextButton(onPressed: () => _editRate(i), child: Text('₹ ${money(l.rate, symbol: false)}')),
          ]),
          Row(children: [
            SizedBox(
              width: 150,
              child: _GstDropdown(
                rate: l.taxRate,
                manual: l.taxManual,
                label: 'GST %',
                enabled: taxEnabled,
                onSlab: (r) => setState(() => _lines[i] = _lines[i].copyWith(taxRate: r, taxManual: false)),
                onCustom: () => _customGst(current: l.taxRate, onSet: (v) => setState(() => _lines[i] = _lines[i].copyWith(taxRate: v, taxManual: true))),
              ),
            ),
            const Spacer(),
            Text(money(tot), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          ]),
        ]),
      ),
    );
  }

  Widget _totalsPanel(bool taxEnabled) {
    Widget row(String label, String value, {bool bold = false, Color? color}) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 3),
          child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text(label, style: TextStyle(color: color, fontWeight: bold ? FontWeight.w800 : FontWeight.normal)),
            Text(value, style: TextStyle(color: color, fontWeight: bold ? FontWeight.w800 : FontWeight.w600, fontSize: bold ? 18 : 14)),
          ]),
        );
    return Column(children: [
      row('Subtotal', money(_subtotal)),
      Row(children: [
        const Expanded(child: Text('Discount')),
        SizedBox(
          width: 80,
          child: TextField(
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(isDense: true),
            onChanged: (v) => setState(() => _discount = double.tryParse(v) ?? 0),
            controller: TextEditingController(text: _discount == 0 ? '' : _discount.toString())
              ..selection = TextSelection.collapsed(offset: (_discount == 0 ? '' : _discount.toString()).length),
          ),
        ),
        const SizedBox(width: 6),
        DropdownButton<bool>(
          value: _discountPct,
          items: const [DropdownMenuItem(value: true, child: Text('%')), DropdownMenuItem(value: false, child: Text('₹'))],
          onChanged: (v) => setState(() => _discountPct = v ?? true),
        ),
        const SizedBox(width: 10),
        Text('- ${money(_discountAmount)}', style: TextStyle(color: Colors.grey.shade700)),
      ]),
      if (taxEnabled) row('GST', '+ ${money(_tax(taxEnabled))}'),
      const Divider(),
      row('Total', money(_total(taxEnabled)), bold: true),
      Row(children: [
        const Expanded(child: Text('Received')),
        TextButton(onPressed: () => setState(() => _paid = _total(taxEnabled)), child: const Text('Full')),
        SizedBox(
          width: 110,
          child: TextField(
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            textAlign: TextAlign.right,
            decoration: const InputDecoration(isDense: true, hintText: 'Full'),
            onChanged: (v) => setState(() => _paid = v.trim().isEmpty ? null : (double.tryParse(v) ?? 0)),
            controller: TextEditingController(text: _paid?.toString() ?? '')
              ..selection = TextSelection.collapsed(offset: (_paid?.toString() ?? '').length),
          ),
        ),
      ]),
      row('Balance Due', money(_balanceDue(taxEnabled)), color: Colors.red.shade700, bold: true),
    ]);
  }

  Widget _recentTile(Txn t, String customer, BusinessSettings settings) {
    final st = _status(t);
    final color = st == 'Paid' ? Colors.green : (st == 'Partial' ? Colors.orange : Colors.red);
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 8, 4),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Text('${t.number} · $customer', style: const TextStyle(fontWeight: FontWeight.w700))),
            Text(money(t.total), style: const TextStyle(fontWeight: FontWeight.w700)),
          ]),
          Row(children: [
            Text(t.date, style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(20)),
              child: Text(st, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w700)),
            ),
          ]),
          Row(mainAxisAlignment: MainAxisAlignment.end, children: [
            TextButton.icon(onPressed: () => _whatsapp(t, settings), icon: const Icon(Icons.share, size: 18), label: const Text('WhatsApp')),
            IconButton(tooltip: 'Print', icon: const Icon(Icons.print_outlined), onPressed: () async {
              final party = (ref.read(partiesProvider).value ?? const []).where((p) => p.id == t.partyId).firstOrNull;
              await ref.read(pdfServiceProvider).printInvoice(txn: t, settings: settings, partyName: party?.name ?? 'Cash Sale', taxEnabled: settings.taxEnabled);
            }),
            IconButton(tooltip: 'Edit', icon: const Icon(Icons.edit_outlined), onPressed: () => _edit(t)),
            IconButton(tooltip: 'Delete', icon: const Icon(Icons.delete_outline), onPressed: () => _delete(t)),
          ]),
        ]),
      ),
    );
  }
}

/// A GST slab dropdown (0/5/12/18/28) with a "Custom…" option for a manual rate.
class _GstDropdown extends StatelessWidget {
  const _GstDropdown({
    required this.rate,
    required this.manual,
    required this.label,
    required this.onSlab,
    required this.onCustom,
    this.enabled = true,
  });

  final double rate;
  final bool manual;
  final String label;
  final ValueChanged<double> onSlab;
  final VoidCallback onCustom;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    final isCustom = manual || !kGstSlabs.contains(rate);
    return DropdownButtonFormField<double>(
      value: isCustom ? -1 : rate,
      isExpanded: true,
      decoration: InputDecoration(labelText: label, isDense: true),
      items: [
        for (final r in kGstSlabs) DropdownMenuItem(value: r, child: Text('${r % 1 == 0 ? r.toInt() : r}%')),
        DropdownMenuItem(value: -1, child: Text(isCustom ? 'Custom (${rate % 1 == 0 ? rate.toInt() : rate}%)' : 'Custom…')),
      ],
      onChanged: !enabled
          ? null
          : (v) {
              if (v == null) return;
              if (v == -1) {
                onCustom();
              } else {
                onSlab(v);
              }
            },
    );
  }
}

extension _FirstOrNull<E> on Iterable<E> {
  E? get firstOrNull {
    final it = iterator;
    return it.moveNext() ? it.current : null;
  }
}
