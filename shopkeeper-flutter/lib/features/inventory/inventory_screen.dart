import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/models.dart';
import '../../core/state/calc.dart';
import '../../core/state/providers.dart';
import '../../core/theme/app_theme.dart';
import '../../core/util/money.dart';
import '../../core/util/num_util.dart';

class InventoryScreen extends ConsumerStatefulWidget {
  const InventoryScreen({super.key});
  @override
  ConsumerState<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends ConsumerState<InventoryScreen> {
  String _q = '';

  @override
  Widget build(BuildContext context) {
    final items = ref.watch(itemsProvider).value ?? const [];
    final txns = ref.watch(txnsProvider).value ?? const [];
    final adj = ref.watch(adjustmentsProvider).value ?? const [];
    final calc = Calc(parties: const [], items: items, txns: txns, adjustments: adj);

    final list = items
        .where((i) => _q.isEmpty || i.name.toLowerCase().contains(_q) || i.category.toLowerCase().contains(_q) || i.barcode.contains(_q))
        .toList()
      ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));

    return Scaffold(
      appBar: AppBar(title: const Text('Inventory')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openForm(null),
        icon: const Icon(Icons.add),
        label: const Text('Add Product'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'Search products…'),
              onChanged: (v) => setState(() => _q = v.toLowerCase()),
            ),
          ),
          Expanded(
            child: list.isEmpty
                ? Center(child: Text('No products yet.', style: TextStyle(color: Colors.grey.shade600)))
                : ListView.builder(
                    itemCount: list.length,
                    itemBuilder: (_, i) {
                      final it = list[i];
                      final stock = calc.itemStock(it.id);
                      final low = calc.isLowStock(it);
                      return ListTile(
                        title: Text(it.name),
                        subtitle: Text([it.brand, it.category, if (it.barcode.isNotEmpty) '▏|▏ ${it.barcode}'].where((s) => s.isNotEmpty).join(' · ')),
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(money(it.salePrice), style: const TextStyle(fontWeight: FontWeight.w700)),
                            if (it.type != 'service')
                              Text(stock <= 0 ? 'No Stock' : '${qty(stock)} ${it.unit}',
                                  style: TextStyle(fontSize: 12, color: low ? Tones.red : Colors.grey.shade600)),
                          ],
                        ),
                        onTap: () => _openForm(it),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  void _openForm(Item? existing) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => _ItemForm(existing: existing),
    );
  }
}

class _ItemForm extends ConsumerStatefulWidget {
  final Item? existing;
  const _ItemForm({this.existing});
  @override
  ConsumerState<_ItemForm> createState() => _ItemFormState();
}

class _ItemFormState extends ConsumerState<_ItemForm> {
  late final TextEditingController _name;
  late final TextEditingController _category;
  late final TextEditingController _brand;
  late final TextEditingController _hsn;
  late final TextEditingController _barcode;
  late final TextEditingController _sale;
  late final TextEditingController _purchase;
  late final TextEditingController _openStock;
  late final TextEditingController _minStock;
  String _type = 'product';
  double _tax = 18;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    _name = TextEditingController(text: e?.name ?? '');
    _category = TextEditingController(text: e?.category ?? '');
    _brand = TextEditingController(text: e?.brand ?? '');
    _hsn = TextEditingController(text: e?.hsn ?? '');
    _barcode = TextEditingController(text: e?.barcode ?? '');
    _sale = TextEditingController(text: e != null ? '${e.salePrice}' : '');
    _purchase = TextEditingController(text: e != null ? '${e.purchasePrice}' : '');
    _openStock = TextEditingController(text: e != null ? '${e.openingStock}' : '0');
    _minStock = TextEditingController(text: e != null ? '${e.minStock}' : '0');
    _type = e?.type ?? 'product';
    _tax = e?.taxRate ?? 18;
  }

  @override
  void dispose() {
    for (final c in [_name, _category, _brand, _hsn, _barcode, _sale, _purchase, _openStock, _minStock]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    final uid = ref.read(uidProvider);
    if (uid == null) return;
    if (_name.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Item name is required')));
      return;
    }
    final e = widget.existing;
    final item = Item(
      id: e?.id ?? makeId(),
      createdAt: e?.createdAt ?? DateTime.now().millisecondsSinceEpoch,
      name: _name.text.trim(),
      type: _type,
      category: _category.text.trim(),
      brand: _brand.text.trim(),
      hsn: _hsn.text.trim(),
      barcode: _barcode.text.trim(),
      unit: e?.unit ?? 'PCS',
      salePrice: toNum(_sale.text),
      purchasePrice: toNum(_purchase.text),
      taxRate: _tax,
      openingStock: toNum(_openStock.text),
      minStock: toNum(_minStock.text),
    );
    await ref.read(firestoreServiceProvider).saveItem(uid, item);
    if (mounted) Navigator.pop(context);
  }

  Future<void> _delete() async {
    final uid = ref.read(uidProvider);
    final e = widget.existing;
    if (uid == null || e == null) return;
    await ref.read(firestoreServiceProvider).deleteItem(uid, e.id);
    if (mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(widget.existing == null ? 'Add Item' : 'Edit Item', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 12),
            TextField(controller: _name, decoration: const InputDecoration(labelText: 'Item Name *')),
            const SizedBox(height: 10),
            Row(children: [
              Expanded(child: DropdownButtonFormField<String>(
                initialValue: _type,
                decoration: const InputDecoration(labelText: 'Type'),
                items: const [DropdownMenuItem(value: 'product', child: Text('Product')), DropdownMenuItem(value: 'service', child: Text('Service'))],
                onChanged: (v) => setState(() => _type = v ?? 'product'),
              )),
              const SizedBox(width: 10),
              Expanded(child: DropdownButtonFormField<double>(
                initialValue: _tax,
                decoration: const InputDecoration(labelText: 'GST %'),
                items: const <double>[0, 5, 12, 18, 28].map((r) => DropdownMenuItem<double>(value: r, child: Text('$r%'))).toList(),
                onChanged: (v) => setState(() => _tax = v ?? 18),
              )),
            ]),
            const SizedBox(height: 10),
            Row(children: [
              Expanded(child: TextField(controller: _category, decoration: const InputDecoration(labelText: 'Category'))),
              const SizedBox(width: 10),
              Expanded(child: TextField(controller: _brand, decoration: const InputDecoration(labelText: 'Brand'))),
            ]),
            const SizedBox(height: 10),
            Row(children: [
              Expanded(child: TextField(controller: _hsn, decoration: const InputDecoration(labelText: 'HSN'))),
              const SizedBox(width: 10),
              Expanded(child: TextField(controller: _barcode, decoration: const InputDecoration(labelText: 'Barcode'))),
            ]),
            const SizedBox(height: 10),
            Row(children: [
              Expanded(child: TextField(controller: _sale, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Sale Price'))),
              const SizedBox(width: 10),
              Expanded(child: TextField(controller: _purchase, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Purchase Price'))),
            ]),
            if (_type != 'service') ...[
              const SizedBox(height: 10),
              Row(children: [
                Expanded(child: TextField(controller: _openStock, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Opening Stock'))),
                const SizedBox(width: 10),
                Expanded(child: TextField(controller: _minStock, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Low Stock Alert'))),
              ]),
            ],
            const SizedBox(height: 16),
            Row(children: [
              if (widget.existing != null)
                TextButton(onPressed: _delete, child: const Text('Delete', style: TextStyle(color: Tones.red))),
              const Spacer(),
              FilledButton(onPressed: _save, child: const Text('Save')),
            ]),
          ],
        ),
      ),
    );
  }
}
