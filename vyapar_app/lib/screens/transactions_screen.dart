import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../store.dart';

class TransactionsScreen extends StatefulWidget {
  const TransactionsScreen({super.key});

  @override
  State<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends State<TransactionsScreen> {
  TxnType? filter;

  @override
  Widget build(BuildContext context) {
    final store = context.watch<AppStore>();
    final txns = store.txnsNewestFirst
        .where((t) => filter == null || t.type == filter)
        .toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Transactions')),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                ChoiceChip(
                  label: const Text('All'),
                  selected: filter == null,
                  onSelected: (_) => setState(() => filter = null),
                ),
                for (final type in TxnType.values) ...[
                  const SizedBox(width: 8),
                  ChoiceChip(
                    label: Text(type.label),
                    selected: filter == type,
                    onSelected: (_) => setState(() => filter = type),
                  ),
                ],
              ],
            ),
          ),
          Expanded(
            child: txns.isEmpty
                ? const Center(child: Text('No transactions'))
                : ListView(
                    children: [for (final txn in txns) TxnTile(txn: txn)],
                  ),
          ),
        ],
      ),
    );
  }
}

/// Shared list tile for a transaction. Tap for details, long-press to delete.
class TxnTile extends StatelessWidget {
  const TxnTile({super.key, required this.txn});

  final Txn txn;

  Color _color(TxnType type) {
    switch (type) {
      case TxnType.sale:
        return Colors.green;
      case TxnType.purchase:
        return Colors.blue;
      case TxnType.paymentIn:
        return Colors.teal;
      case TxnType.paymentOut:
        return Colors.deepOrange;
      case TxnType.expense:
        return Colors.red;
    }
  }

  IconData _icon(TxnType type) {
    switch (type) {
      case TxnType.sale:
        return Icons.receipt_long;
      case TxnType.purchase:
        return Icons.shopping_cart;
      case TxnType.paymentIn:
        return Icons.south_west;
      case TxnType.paymentOut:
        return Icons.north_east;
      case TxnType.expense:
        return Icons.money_off;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _color(txn.type);
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withValues(alpha: 0.15),
          child: Icon(_icon(txn.type), color: color, size: 20),
        ),
        title: Text(txn.partyName),
        subtitle: Text('${txn.type.label} • ${dateText(txn.date)}'
            '${txn.due > 0.005 ? ' • Due ${money(txn.due)}' : ''}'),
        trailing: Text(
          money(txn.total),
          style: TextStyle(fontWeight: FontWeight.bold, color: color),
        ),
        onTap: () => _showDetails(context),
        onLongPress: () => _confirmDelete(context),
      ),
    );
  }

  void _showDetails(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('${txn.type.label} — ${txn.partyName}'),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('Date: ${dateText(txn.date)}'),
              if (txn.note.isNotEmpty) Text('Note: ${txn.note}'),
              const SizedBox(height: 8),
              if (txn.lines.isNotEmpty) ...[
                const Divider(),
                for (final line in txn.lines)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: Text(
                        '${line.name}  ×${line.qty.toStringAsFixed(line.qty % 1 == 0 ? 0 : 2)}'
                        ' @ ${money(line.price)}'
                        '${line.gstRate > 0 ? ' +${line.gstRate.toStringAsFixed(0)}% GST' : ''}'
                        '  =  ${money(line.total)}'),
                  ),
                const Divider(),
                Text('Subtotal: ${money(txn.subtotal)}'),
                Text('GST: ${money(txn.tax)}'),
              ],
              Text('Total: ${money(txn.total)}',
                  style: const TextStyle(fontWeight: FontWeight.bold)),
              if (txn.lines.isNotEmpty) ...[
                Text('Paid: ${money(txn.paid)}'),
                Text('Due: ${money(txn.due)}',
                    style: TextStyle(
                        color: txn.due > 0.005 ? Colors.red : Colors.green)),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Close')),
        ],
      ),
    );
  }

  Future<void> _confirmDelete(BuildContext context) async {
    final store = context.read<AppStore>();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Delete transaction?'),
        content: const Text(
            'This will reverse its effect on stock and party balance.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Delete')),
        ],
      ),
    );
    if (ok == true) {
      store.deleteTxn(txn.id);
    }
  }
}
