import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/domain/txn_config.dart';
import '../../core/models/models.dart';
import '../../core/state/providers.dart';
import '../../core/util/money.dart';
import '../../core/util/num_util.dart';

class BillingScreen extends ConsumerStatefulWidget {
  const BillingScreen({super.key});
  @override
  ConsumerState<BillingScreen> createState() => _BillingScreenState();
}

class _BillingScreenState extends ConsumerState<BillingScreen> {
  final _customer = TextEditingController();
  final _search = TextEditingController();
  final List<TxnLine> _lines = [];

  @override
  void dispose() {
    _customer.dispose();
    _search.dispose();
    super.dispose();
  }

  double get _subtotal => round2(_lines.fold(0.0, (s, l) => s + l.qty * l.rate));
  double _tax(bool enabled) => enabled ? round2(_lines.fold(0.0, (s, l) => s + l.qty * l.rate * l.taxRate / 100)) : 0;
  double _total(bool enabled) => round2(_subtotal + _tax(enabled));

  void _add(Item it, bool taxEnabled) {
    setState(() {
      final i = _lines.indexWhere((l) => l.itemId == it.id);
      if (i >= 0) {
        _lines[i] = TxnLine(itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: _lines[i].qty + 1, rate: _lines[i].rate, taxRate: _lines[i].taxRate, cost: _lines[i].cost);
      } else {
        _lines.add(TxnLine(itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: 1, rate: it.salePrice, taxRate: taxEnabled ? it.taxRate : 0, cost: it.purchasePrice));
      }
    });
  }

  void _setQty(int i, double q) {
    if (q <= 0) {
      setState(() => _lines.removeAt(i));
      return;
    }
    final l = _lines[i];
    setState(() => _lines[i] = TxnLine(itemId: l.itemId, name: l.name, hsn: l.hsn, unit: l.unit, qty: q, rate: l.rate, taxRate: l.taxRate, cost: l.cost));
  }

  Future<void> _save() async {
    final uid = ref.read(uidProvider);
    if (uid == null || _lines.isEmpty) return;
    final parties = ref.read(partiesProvider).value ?? const [];
    final counters = ref.read(countersProvider).value ?? const {};
    final taxEnabled = (ref.read(settingsProvider).value ?? BusinessSettings()).taxEnabled;
    final party = parties.where((p) => p.type != 'supplier' && p.name.toLowerCase() == _customer.text.trim().toLowerCase()).firstOrNull;
    final n = (counters['SALE'] is num) ? (counters['SALE'] as num).toInt() : 1;
    final txn = Txn(
      id: makeId(), type: 'SALE',
      number: '${kTxnTypes['SALE']!.prefix}-${n.toString().padLeft(4, '0')}',
      date: todayIso(), partyId: party?.id, lines: List.of(_lines),
      subtotal: _subtotal, discount: 0, total: _total(taxEnabled), paid: _total(taxEnabled), mode: 'Cash',
      createdAt: DateTime.now().millisecondsSinceEpoch,
    );
    await ref.read(firestoreServiceProvider).saveTxn(uid, txn);
    if (mounted) {
      setState(() {
        _lines.clear();
        _customer.clear();
      });
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Bill ${txn.number} saved')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final items = ref.watch(itemsProvider).value ?? const [];
    final taxEnabled = (ref.watch(settingsProvider).value ?? BusinessSettings()).taxEnabled;
    final q = _search.text.toLowerCase();
    final matches = items.where((i) => q.isNotEmpty && (i.name.toLowerCase().contains(q) || i.barcode.contains(q))).take(8).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Billing'), actions: [
        if (_lines.isNotEmpty) TextButton(onPressed: () => setState(_lines.clear), child: const Text('Clear')),
      ]),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Column(children: [
              TextField(controller: _customer, decoration: const InputDecoration(labelText: 'Customer (optional)', prefixIcon: Icon(Icons.person_outline))),
              const SizedBox(height: 8),
              TextField(
                controller: _search,
                decoration: const InputDecoration(labelText: 'Search product to add', prefixIcon: Icon(Icons.search)),
                onChanged: (_) => setState(() {}),
              ),
              if (matches.isNotEmpty)
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
            ]),
          ),
          const Divider(height: 1),
          Expanded(
            child: _lines.isEmpty
                ? Center(child: Text('Add products to start the bill.', style: TextStyle(color: Colors.grey.shade600)))
                : ListView.builder(
                    itemCount: _lines.length,
                    itemBuilder: (_, i) {
                      final l = _lines[i];
                      final tot = round2(l.qty * l.rate * (taxEnabled ? (1 + l.taxRate / 100) : 1));
                      return ListTile(
                        title: Text(l.name),
                        subtitle: Text('${money(l.rate)} · GST ${l.taxRate}%'),
                        trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                          IconButton(icon: const Icon(Icons.remove_circle_outline), onPressed: () => _setQty(i, l.qty - 1)),
                          Text(qty(l.qty)),
                          IconButton(icon: const Icon(Icons.add_circle_outline), onPressed: () => _setQty(i, l.qty + 1)),
                          SizedBox(width: 72, child: Text(money(tot, symbol: false), textAlign: TextAlign.right, style: const TextStyle(fontWeight: FontWeight.w700))),
                        ]),
                      );
                    },
                  ),
          ),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(children: [
                Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                  Text('Total', style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
                  Text(money(_total(taxEnabled)), style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
                ]),
                const Spacer(),
                FilledButton.icon(onPressed: _lines.isEmpty ? null : _save, icon: const Icon(Icons.save_outlined), label: const Text('Save Bill')),
              ]),
            ),
          ),
        ],
      ),
    );
  }
}

extension _FirstOrNull<E> on Iterable<E> {
  E? get firstOrNull {
    final it = iterator;
    return it.moveNext() ? it.current : null;
  }
}
