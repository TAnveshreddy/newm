import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../store.dart';

/// Full-screen form for creating a Sale invoice or Purchase bill.
class InvoiceFormScreen extends StatefulWidget {
  const InvoiceFormScreen({super.key, required this.type});

  /// TxnType.sale or TxnType.purchase
  final TxnType type;

  @override
  State<InvoiceFormScreen> createState() => _InvoiceFormScreenState();
}

class _InvoiceFormScreenState extends State<InvoiceFormScreen> {
  String partyId = cashPartyId;
  final List<LineItem> lines = [];
  final paidCtrl = TextEditingController();
  final noteCtrl = TextEditingController();
  bool fullyPaid = true;

  bool get isSale => widget.type == TxnType.sale;

  double get subtotal => lines.fold(0, (sum, l) => sum + l.amount);
  double get tax => lines.fold(0, (sum, l) => sum + l.tax);
  double get total => subtotal + tax;

  @override
  Widget build(BuildContext context) {
    final store = context.watch<AppStore>();
    final parties = store.parties.toList()
      ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));

    return Scaffold(
      appBar: AppBar(
          title: Text(isSale ? 'New Sale Invoice' : 'New Purchase Bill')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          DropdownButtonFormField<String>(
            value: partyId,
            decoration: InputDecoration(
              labelText: isSale ? 'Customer' : 'Supplier',
              border: const OutlineInputBorder(),
            ),
            items: [
              const DropdownMenuItem(
                  value: cashPartyId, child: Text('Cash (no party)')),
              for (final p in parties)
                DropdownMenuItem(value: p.id, child: Text(p.name)),
            ],
            onChanged: (v) => setState(() => partyId = v ?? cashPartyId),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Text('Items', style: Theme.of(context).textTheme.titleMedium),
              const Spacer(),
              TextButton.icon(
                icon: const Icon(Icons.add),
                label: const Text('Add item'),
                onPressed: store.items.isEmpty
                    ? null
                    : () async {
                        final line = await _pickLine(context, store);
                        if (line != null) {
                          setState(() => lines.add(line));
                        }
                      },
              ),
            ],
          ),
          if (store.items.isEmpty)
            const Padding(
              padding: EdgeInsets.all(8),
              child: Text(
                'No items in inventory yet. Add items from the Items tab first.',
                style: TextStyle(color: Colors.red),
              ),
            ),
          for (int i = 0; i < lines.length; i++)
            Card(
              child: ListTile(
                dense: true,
                title: Text(lines[i].name),
                subtitle: Text(
                    '${lines[i].qty.toStringAsFixed(lines[i].qty % 1 == 0 ? 0 : 2)}'
                    ' × ${money(lines[i].price)}'
                    '${lines[i].gstRate > 0 ? ' + ${lines[i].gstRate.toStringAsFixed(0)}% GST' : ''}'),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(money(lines[i].total),
                        style: const TextStyle(fontWeight: FontWeight.bold)),
                    IconButton(
                      icon: const Icon(Icons.close, size: 18),
                      onPressed: () => setState(() => lines.removeAt(i)),
                    ),
                  ],
                ),
              ),
            ),
          const Divider(height: 32),
          _totalRow('Subtotal', money(subtotal)),
          _totalRow('GST', money(tax)),
          _totalRow('Total', money(total), bold: true),
          const SizedBox(height: 8),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(isSale ? 'Received in full' : 'Paid in full'),
            value: fullyPaid,
            onChanged: (v) => setState(() => fullyPaid = v),
          ),
          if (!fullyPaid)
            TextField(
              controller: paidCtrl,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: isSale ? 'Amount received (₹)' : 'Amount paid (₹)',
                border: const OutlineInputBorder(),
              ),
              onChanged: (_) => setState(() {}),
            ),
          const SizedBox(height: 12),
          TextField(
            controller: noteCtrl,
            decoration: const InputDecoration(
              labelText: 'Note (optional)',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 20),
          FilledButton.icon(
            icon: const Icon(Icons.save),
            label: Text(isSale ? 'Save Sale' : 'Save Purchase'),
            onPressed: lines.isEmpty ? null : () => _save(store),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _totalRow(String label, String value, {bool bold = false}) {
    final style = TextStyle(
        fontSize: bold ? 18 : 14,
        fontWeight: bold ? FontWeight.bold : FontWeight.normal);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [Text(label, style: style), Text(value, style: style)],
      ),
    );
  }

  void _save(AppStore store) {
    double paid = fullyPaid
        ? total
        : (double.tryParse(paidCtrl.text.trim()) ?? 0)
            .clamp(0, total)
            .toDouble();
    // Cash transactions are always settled immediately.
    if (partyId == cashPartyId) paid = total;

    final party = store.partyById(partyId);
    store.addTxn(Txn(
      id: newId(),
      type: widget.type,
      partyId: partyId,
      partyName: party?.name ?? 'Cash',
      date: DateTime.now(),
      lines: List.of(lines),
      total: total,
      paid: paid,
      note: noteCtrl.text.trim(),
    ));
    Navigator.of(context).pop();
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(
            '${isSale ? 'Sale' : 'Purchase'} of ${money(total)} saved')));
  }

  /// Dialog to choose an item, quantity and price for one invoice line.
  Future<LineItem?> _pickLine(BuildContext context, AppStore store) async {
    final sorted = store.items.toList()
      ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
    Item selected = sorted.first;
    final qtyCtrl = TextEditingController(text: '1');
    final priceCtrl = TextEditingController(
        text: '${isSale ? selected.salePrice : selected.purchasePrice}');

    return showDialog<LineItem>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => AlertDialog(
          title: const Text('Add Item'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: selected.id,
                decoration: const InputDecoration(labelText: 'Item'),
                items: [
                  for (final i in sorted)
                    DropdownMenuItem(value: i.id, child: Text(i.name)),
                ],
                onChanged: (id) {
                  final item = store.itemById(id ?? '');
                  if (item != null) {
                    setState(() {
                      selected = item;
                      priceCtrl.text =
                          '${isSale ? item.salePrice : item.purchasePrice}';
                    });
                  }
                },
              ),
              TextField(
                controller: qtyCtrl,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                    labelText: 'Quantity (${selected.unit})',
                    helperText: isSale
                        ? 'In stock: ${selected.stock.toStringAsFixed(selected.stock % 1 == 0 ? 0 : 2)}'
                        : null),
              ),
              TextField(
                controller: priceCtrl,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(
                    labelText:
                        'Price per ${selected.unit} (₹) • GST ${selected.gstRate.toStringAsFixed(0)}%'),
              ),
            ],
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Cancel')),
            FilledButton(
              onPressed: () {
                final qty = double.tryParse(qtyCtrl.text.trim()) ?? 0;
                final price = double.tryParse(priceCtrl.text.trim()) ?? 0;
                if (qty <= 0) return;
                Navigator.pop(
                  ctx,
                  LineItem(
                    itemId: selected.id,
                    name: selected.name,
                    qty: qty,
                    price: price,
                    gstRate: selected.gstRate,
                  ),
                );
              },
              child: const Text('Add'),
            ),
          ],
        ),
      ),
    );
  }
}

/// Dialog for Payment In / Payment Out against a party.
Future<void> showPaymentDialog(BuildContext context,
    {required bool isIn}) async {
  final store = context.read<AppStore>();
  if (store.parties.isEmpty) {
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Add a party first (Parties tab).')));
    return;
  }
  final sorted = store.parties.toList()
    ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
  String partyId = sorted.first.id;
  final amountCtrl = TextEditingController();
  final noteCtrl = TextEditingController();

  await showDialog<void>(
    context: context,
    builder: (ctx) => StatefulBuilder(
      builder: (ctx, setState) => AlertDialog(
        title: Text(isIn ? 'Payment In (received)' : 'Payment Out (given)'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DropdownButtonFormField<String>(
              value: partyId,
              decoration: const InputDecoration(labelText: 'Party'),
              items: [
                for (final p in sorted)
                  DropdownMenuItem(value: p.id, child: Text(p.name)),
              ],
              onChanged: (v) => setState(() => partyId = v ?? partyId),
            ),
            TextField(
              controller: amountCtrl,
              autofocus: true,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Amount (₹) *'),
            ),
            TextField(
              controller: noteCtrl,
              decoration: const InputDecoration(labelText: 'Note (optional)'),
            ),
          ],
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              final amount = double.tryParse(amountCtrl.text.trim()) ?? 0;
              if (amount <= 0) return;
              final party = store.partyById(partyId);
              store.addTxn(Txn(
                id: newId(),
                type: isIn ? TxnType.paymentIn : TxnType.paymentOut,
                partyId: partyId,
                partyName: party?.name ?? '',
                date: DateTime.now(),
                total: amount,
                paid: amount,
                note: noteCtrl.text.trim(),
              ));
              Navigator.pop(ctx);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    ),
  );
}

/// Dialog for recording a business expense.
Future<void> showExpenseDialog(BuildContext context) async {
  final store = context.read<AppStore>();
  final amountCtrl = TextEditingController();
  final noteCtrl = TextEditingController();

  await showDialog<void>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: const Text('Record Expense'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: noteCtrl,
            autofocus: true,
            decoration:
                const InputDecoration(labelText: 'What was it for? *'),
          ),
          TextField(
            controller: amountCtrl,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Amount (₹) *'),
          ),
        ],
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
        FilledButton(
          onPressed: () {
            final amount = double.tryParse(amountCtrl.text.trim()) ?? 0;
            final note = noteCtrl.text.trim();
            if (amount <= 0 || note.isEmpty) return;
            store.addTxn(Txn(
              id: newId(),
              type: TxnType.expense,
              partyId: cashPartyId,
              partyName: note,
              date: DateTime.now(),
              total: amount,
              paid: amount,
              note: note,
            ));
            Navigator.pop(ctx);
          },
          child: const Text('Save'),
        ),
      ],
    ),
  );
}
