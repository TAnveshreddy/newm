import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/i18n/locale_provider.dart';
import '../../core/models/models.dart';
import '../../core/state/calc.dart';
import '../../core/state/providers.dart';
import '../../core/theme/app_theme.dart';
import '../../core/util/money.dart';
import '../../core/util/num_util.dart';
import '../../shared/widgets/kpi_card.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(itemsProvider).value ?? const [];
    final txns = ref.watch(txnsProvider).value ?? const [];
    final parties = ref.watch(partiesProvider).value ?? const [];
    final adj = ref.watch(adjustmentsProvider).value ?? const [];
    final settings = ref.watch(settingsProvider).value ?? BusinessSettings();
    final calc = Calc(parties: parties, items: items, txns: txns, adjustments: adj);

    final today = todayIso();
    double todaySales = 0, todayProfit = 0;
    int todayBills = 0;
    for (final t in txns) {
      if (t.date != today) continue;
      if (t.type == 'SALE') {
        todaySales += t.total;
        todayProfit += calc.txnProfit(t);
        todayBills++;
      } else if (t.type == 'SALE_RETURN') {
        todayProfit += calc.txnProfit(t);
      }
    }
    final rp = calc.receivablePayable();
    final low = calc.lowStockItems();
    final recent = [...txns]..sort((a, b) => (b.createdAt ?? 0).compareTo(a.createdAt ?? 0));

    return Scaffold(
      appBar: AppBar(title: Text(settings.businessName), titleTextStyle: Theme.of(context).textTheme.titleMedium),
      body: ListView(
        padding: const EdgeInsets.all(14),
        children: [
          Text(ref.tr('dash.title'), style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
          Text(ref.tr('dash.overview'), style: TextStyle(color: Colors.grey.shade600)),
          const SizedBox(height: 14),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.55,
            children: [
              KpiCard(icon: Icons.shopping_bag_outlined, tone: Tones.blue, label: ref.tr('dash.todaySales'), value: money(todaySales)),
              KpiCard(icon: Icons.trending_up, tone: Tones.green, label: ref.tr('dash.todayProfit'), value: money(todayProfit)),
              KpiCard(icon: Icons.receipt_long_outlined, tone: Tones.indigo, label: ref.tr('dash.billsToday'), value: '$todayBills'),
              KpiCard(icon: Icons.inventory_2_outlined, tone: Tones.amber, label: ref.tr('dash.lowStock'), value: '${low.length}'),
              KpiCard(icon: Icons.south_west, tone: Tones.green, label: ref.tr('dash.toCollect'), value: money(rp.receivable)),
              KpiCard(icon: Icons.north_east, tone: Tones.red, label: ref.tr('dash.toPay'), value: money(rp.payable)),
            ],
          ),
          const SizedBox(height: 8),
          _Section(
            title: ref.tr('dash.lowStockItems'),
            child: low.isEmpty
                ? _Empty(ref.tr('dash.wellStocked'))
                : Column(
                    children: low.take(6).map((it) => ListTile(
                          dense: true,
                          leading: const CircleAvatar(child: Icon(Icons.inventory_2_outlined, size: 18)),
                          title: Text(it.name),
                          subtitle: Text(it.category),
                          trailing: Text('${qty(calc.itemStock(it.id))} ${it.unit}',
                              style: const TextStyle(color: Tones.red, fontWeight: FontWeight.w700)),
                        )).toList(),
                  ),
          ),
          _Section(
            title: ref.tr('dash.recentTxns'),
            child: recent.isEmpty
                ? _Empty(ref.tr('dash.noTxns'))
                : Column(children: recent.take(6).map((t) => _txnTile(t, calc)).toList()),
          ),
        ],
      ),
    );
  }

  Widget _txnTile(Txn t, Calc calc) {
    final inflow = t.type == 'SALE' || t.type == 'PAYMENT_IN' || t.type == 'PURCHASE_RETURN';
    return ListTile(
      dense: true,
      leading: CircleAvatar(
        backgroundColor: (inflow ? Tones.green : Tones.red).withValues(alpha: 0.14),
        child: Icon(inflow ? Icons.south_west : Icons.north_east, size: 18, color: inflow ? Tones.green : Tones.red),
      ),
      title: Text('${t.type} · ${calc.partyName(t.partyId)}', maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Text(t.number),
      trailing: Text('${inflow ? '+' : '-'} ${money(t.total, symbol: false)}',
          style: TextStyle(fontWeight: FontWeight.w800, color: inflow ? Tones.green : Tones.red)),
    );
  }
}

class _Section extends StatelessWidget {
  final String title;
  final Widget child;
  const _Section({required this.title, required this.child});
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)), const SizedBox(height: 6), child],
        ),
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  final String text;
  const _Empty(this.text);
  @override
  Widget build(BuildContext context) =>
      Padding(padding: const EdgeInsets.all(20), child: Center(child: Text(text, style: TextStyle(color: Colors.grey.shade600))));
}
