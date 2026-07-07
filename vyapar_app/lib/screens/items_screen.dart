import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../store.dart';

class ItemsScreen extends StatelessWidget {
  const ItemsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final store = context.watch<AppStore>();
    final items = store.items.toList()
      ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Items'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_box),
            tooltip: 'Add item',
            onPressed: () => showItemDialog(context),
          ),
        ],
      ),
      body: items.isEmpty
          ? const Center(
              child: Text('No items yet.\nTap the icon above to add one.',
                  textAlign: TextAlign.center),
            )
          : ListView.builder(
              itemCount: items.length,
              itemBuilder: (context, index) {
                final item = items[index];
                return ListTile(
                  leading: CircleAvatar(
                    backgroundColor:
                        item.isLowStock ? Colors.red.shade100 : null,
                    child: Icon(
                      Icons.inventory_2,
                      color: item.isLowStock ? Colors.red : null,
                    ),
                  ),
                  title: Text(item.name),
                  subtitle: Text(
                      'Sale: ${money(item.salePrice)} • Purchase: ${money(item.purchasePrice)} • GST ${item.gstRate.toStringAsFixed(0)}%'),
                  trailing: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        '${item.stock.toStringAsFixed(item.stock % 1 == 0 ? 0 : 2)} ${item.unit}',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: item.isLowStock ? Colors.red : Colors.green,
                        ),
                      ),
                      Text('in stock',
                          style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                  onTap: () => showItemDialog(context, item: item),
                  onLongPress: () async {
                    if (store.itemHasTxns(item.id)) {
                      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                          content: Text(
                              'Cannot delete: item is used in transactions.')));
                      return;
                    }
                    final ok = await showDialog<bool>(
                      context: context,
                      builder: (ctx) => AlertDialog(
                        title: const Text('Delete item?'),
                        content: Text('Delete "${item.name}" permanently?'),
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
                      store.deleteItem(item.id);
                    }
                  },
                );
              },
            ),
    );
  }
}

/// Add / edit item dialog.
Future<void> showItemDialog(BuildContext context, {Item? item}) async {
  final store = context.read<AppStore>();
  final nameCtrl = TextEditingController(text: item?.name ?? '');
  final unitCtrl = TextEditingController(text: item?.unit ?? 'PCS');
  final saleCtrl =
      TextEditingController(text: item == null ? '' : '${item.salePrice}');
  final purchaseCtrl =
      TextEditingController(text: item == null ? '' : '${item.purchasePrice}');
  final gstCtrl =
      TextEditingController(text: item == null ? '' : '${item.gstRate}');
  final stockCtrl =
      TextEditingController(text: item == null ? '' : '${item.stock}');
  final lowCtrl =
      TextEditingController(text: item == null ? '' : '${item.lowStockAt}');

  double parseNum(TextEditingController c) =>
      double.tryParse(c.text.trim()) ?? 0;

  await showDialog<void>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: Text(item == null ? 'Add Item' : 'Edit Item'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameCtrl,
              autofocus: true,
              decoration: const InputDecoration(labelText: 'Item name *'),
            ),
            TextField(
              controller: unitCtrl,
              decoration:
                  const InputDecoration(labelText: 'Unit (PCS, KG, ...)'),
            ),
            TextField(
              controller: saleCtrl,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Sale price (₹)'),
            ),
            TextField(
              controller: purchaseCtrl,
              keyboardType: TextInputType.number,
              decoration:
                  const InputDecoration(labelText: 'Purchase price (₹)'),
            ),
            TextField(
              controller: gstCtrl,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'GST rate (%)'),
            ),
            TextField(
              controller: stockCtrl,
              keyboardType: TextInputType.number,
              decoration:
                  const InputDecoration(labelText: 'Opening stock quantity'),
            ),
            TextField(
              controller: lowCtrl,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                  labelText: 'Low stock alert at (0 = off)'),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
            onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
        FilledButton(
          onPressed: () {
            final name = nameCtrl.text.trim();
            if (name.isEmpty) return;
            if (item == null) {
              store.upsertItem(Item(
                id: newId(),
                name: name,
                unit: unitCtrl.text.trim().isEmpty
                    ? 'PCS'
                    : unitCtrl.text.trim(),
                salePrice: parseNum(saleCtrl),
                purchasePrice: parseNum(purchaseCtrl),
                gstRate: parseNum(gstCtrl),
                stock: parseNum(stockCtrl),
                lowStockAt: parseNum(lowCtrl),
              ));
            } else {
              item.name = name;
              item.unit =
                  unitCtrl.text.trim().isEmpty ? 'PCS' : unitCtrl.text.trim();
              item.salePrice = parseNum(saleCtrl);
              item.purchasePrice = parseNum(purchaseCtrl);
              item.gstRate = parseNum(gstCtrl);
              item.stock = parseNum(stockCtrl);
              item.lowStockAt = parseNum(lowCtrl);
              store.upsertItem(item);
            }
            Navigator.pop(ctx);
          },
          child: const Text('Save'),
        ),
      ],
    ),
  );
}
