import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/domain/txn_config.dart';
import '../../core/models/models.dart';
import '../../core/state/calc.dart';
import '../../core/state/providers.dart';
import '../../core/util/money.dart';
import '../../core/util/num_util.dart';

class TxPageConfig {
  final String title;
  final List<String> show;
  final List<String> create;
  const TxPageConfig({required this.title, required this.show, required this.create});
}

const kLineBased = {'PURCHASE', 'ESTIMATE', 'SALE_RETURN', 'PURCHASE_RETURN'};

/// Generic list + create screen for purchases, estimates, payments, expenses
/// and returns — driven by [TxPageConfig] so one screen serves them all.
class TransactionsScreen extends ConsumerWidget {
  final TxPageConfig config;
  const TransactionsScreen({super.key, required this.config});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final txns = ref.watch(txnsProvider).value ?? const [];
    final parties = ref.watch(partiesProvider).value ?? const [];
    final calc = Calc(parties: parties, items: const [], txns: txns, adjustments: const []);
    final rows = txns.where((t) => config.show.contains(t.type)).toList()
      ..sort((a, b) => (b.createdAt ?? 0).compareTo(a.createdAt ?? 0));

    return Scaffold(
      appBar: AppBar(title: Text(config.title)),
      floatingActionButton: config.create.length == 1
          ? FloatingActionButton.extended(
              onPressed: () => _openForm(context, config.create.first),
              icon: const Icon(Icons.add),
              label: Text(kTxnTypes[config.create.first]!.label),
            )
          : FloatingActionButton.extended(
              onPressed: () => _pickType(context),
              icon: const Icon(Icons.add),
              label: const Text('New'),
            ),
      body: rows.isEmpty
          ? Center(child: Text('Nothing here yet.', style: TextStyle(color: Colors.grey.shade600)))
          : ListView.builder(
              itemCount: rows.length,
              itemBuilder: (_, i) {
                final t = rows[i];
                return ListTile(
                  title: Text('${kTxnTypes[t.type]!.label} · ${t.number}'),
                  subtitle: Text('${t.date} · ${t.partyId != null ? calc.partyName(t.partyId) : (t.category.isEmpty ? '—' : t.category)}'),
                  trailing: Text(money(t.total), style: const TextStyle(fontWeight: FontWeight.w700)),
                );
              },
            ),
    );
  }

  void _pickType(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (_) => Column(
        mainAxisSize: MainAxisSize.min,
        children: config.create
            .map((t) => ListTile(title: Text(kTxnTypes[t]!.label), onTap: () {
                  Navigator.pop(context);
                  _openForm(context, t);
                }))
            .toList(),
      ),
    );
  }

  void _openForm(BuildContext context, String type) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => _TxnForm(type: type),
    );
  }
}

class _TxnForm extends ConsumerStatefulWidget {
  final String type;
  const _TxnForm({required this.type});
  @override
  ConsumerState<_TxnForm> createState() => _TxnFormState();
}

class _TxnFormState extends ConsumerState<_TxnForm> {
  String? _partyId;
  final _amount = TextEditingController();
  final _category = TextEditingController();
  final List<TxnLine> _lines = [];

  bool get _lineBased => kLineBased.contains(widget.type);

  @override
  void dispose() {
    _amount.dispose();
    _category.dispose();
    super.dispose();
  }

  double get _total {
    final taxEnabled = (ref.read(settingsProvider).value ?? BusinessSettings()).taxEnabled;
    return round2(_lines.fold(0.0, (s, l) => s + l.qty * l.rate * (taxEnabled ? (1 + l.taxRate / 100) : 1)));
  }

  Future<void> _save() async {
    final uid = ref.read(uidProvider);
    if (uid == null) return;
    final counters = ref.read(countersProvider).value ?? const {};
    final n = (counters[widget.type] is num) ? (counters[widget.type] as num).toInt() : 1;
    final number = '${kTxnTypes[widget.type]!.prefix}-${n.toString().padLeft(4, '0')}';
    Txn txn;
    if (_lineBased) {
      if (_lines.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Add at least one item')));
        return;
      }
      final subtotal = round2(_lines.fold(0.0, (s, l) => s + l.qty * l.rate));
      txn = Txn(id: makeId(), type: widget.type, number: number, date: todayIso(), partyId: _partyId,
          lines: List.of(_lines), subtotal: subtotal, total: _total, paid: _total,
          createdAt: DateTime.now().millisecondsSinceEpoch);
    } else {
      final amt = toNum(_amount.text);
      if (amt <= 0) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Enter an amount')));
        return;
      }
      txn = Txn(id: makeId(), type: widget.type, number: number, date: todayIso(), partyId: _partyId,
          total: amt, paid: amt, category: _category.text.trim(),
          createdAt: DateTime.now().millisecondsSinceEpoch);
    }
    await ref.read(firestoreServiceProvider).saveTxn(uid, txn);
    if (mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final meta = kTxnTypes[widget.type]!;
    final items = ref.watch(itemsProvider).value ?? const [];
    final parties = (ref.watch(partiesProvider).value ?? const [])
        .where((p) => meta.party == 'supplier' ? p.type == 'supplier' : p.type != 'supplier')
        .toList();

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(meta.label, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 12),
            DropdownButtonFormField<String?>(
              initialValue: _partyId,
              decoration: InputDecoration(labelText: meta.party == 'supplier' ? 'Supplier' : 'Customer'),
              items: [
                const DropdownMenuItem(value: null, child: Text('— none —')),
                ...parties.map((p) => DropdownMenuItem(value: p.id, child: Text(p.name))),
              ],
              onChanged: (v) => setState(() => _partyId = v),
            ),
            const SizedBox(height: 10),
            if (widget.type == 'EXPENSE')
              TextField(controller: _category, decoration: const InputDecoration(labelText: 'Category')),
            if (_lineBased) ...[
              DropdownButtonFormField<String>(
                initialValue: null,
                decoration: const InputDecoration(labelText: 'Add item'),
                items: items.map((it) => DropdownMenuItem(value: it.id, child: Text(it.name))).toList(),
                onChanged: (id) {
                  if (id == null) return;
                  final it = items.firstWhere((e) => e.id == id);
                  final isPur = widget.type == 'PURCHASE' || widget.type == 'PURCHASE_RETURN';
                  setState(() => _lines.add(TxnLine(
                        itemId: it.id, name: it.name, hsn: it.hsn, unit: it.unit, qty: 1,
                        rate: isPur ? it.purchasePrice : it.salePrice, taxRate: it.taxRate, cost: it.purchasePrice)));
                },
              ),
              ..._lines.asMap().entries.map((e) => ListTile(
                    dense: true,
                    title: Text(e.value.name),
                    subtitle: Text('${qty(e.value.qty)} × ${money(e.value.rate)}'),
                    trailing: IconButton(icon: const Icon(Icons.delete_outline), onPressed: () => setState(() => _lines.removeAt(e.key))),
                  )),
              Align(alignment: Alignment.centerRight, child: Text('Total: ${money(_total)}', style: const TextStyle(fontWeight: FontWeight.w800))),
            ] else ...[
              const SizedBox(height: 10),
              TextField(controller: _amount, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Amount (₹)')),
            ],
            const SizedBox(height: 16),
            Align(alignment: Alignment.centerRight, child: FilledButton(onPressed: _save, child: const Text('Save'))),
          ],
        ),
      ),
    );
  }
}
