import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../store.dart';
import 'transactions_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final store = context.watch<AppStore>();
    final recent = store.txnsNewestFirst.take(8).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Vyapar Lite')),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          Row(
            children: [
              Expanded(
                child: _StatCard(
                  label: 'To Collect',
                  value: money(store.toCollect),
                  color: Colors.green,
                  icon: Icons.south_west,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _StatCard(
                  label: 'To Pay',
                  value: money(store.toPay),
                  color: Colors.red,
                  icon: Icons.north_east,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _StatCard(
                  label: 'Sales (this month)',
                  value: money(store.salesThisMonth),
                  color: Colors.blue,
                  icon: Icons.trending_up,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _StatCard(
                  label: 'Stock Value',
                  value: money(store.stockValue),
                  color: Colors.orange,
                  icon: Icons.inventory_2,
                ),
              ),
            ],
          ),
          if (store.lowStockCount > 0) ...[
            const SizedBox(height: 12),
            Card(
              color: Colors.amber.shade100,
              child: ListTile(
                leading: const Icon(Icons.warning_amber, color: Colors.brown),
                title: Text(
                    '${store.lowStockCount} item(s) are low on stock'),
              ),
            ),
          ],
          const SizedBox(height: 20),
          Text('Recent Transactions',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          if (recent.isEmpty)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(
                child: Text(
                  'No transactions yet.\nUse the + button to create your first sale.',
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          for (final txn in recent) TxnTile(txn: txn),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.label,
    required this.value,
    required this.color,
    required this.icon,
  });

  final String label;
  final String value;
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, size: 18, color: color),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    label,
                    style: Theme.of(context).textTheme.bodySmall,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              value,
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(color: color, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }
}
