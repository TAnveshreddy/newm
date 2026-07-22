import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/models.dart';
import '../../core/state/calc.dart';
import '../../core/state/providers.dart';
import '../../core/theme/app_theme.dart';
import '../../core/util/money.dart';
import '../../core/util/num_util.dart';

class PartiesScreen extends ConsumerStatefulWidget {
  const PartiesScreen({super.key});
  @override
  ConsumerState<PartiesScreen> createState() => _PartiesScreenState();
}

class _PartiesScreenState extends ConsumerState<PartiesScreen> {
  String _tab = 'customer';

  @override
  Widget build(BuildContext context) {
    final parties = ref.watch(partiesProvider).value ?? const [];
    final txns = ref.watch(txnsProvider).value ?? const [];
    final calc = Calc(parties: parties, items: const [], txns: txns, adjustments: const []);

    final list = parties
        .where((p) => _tab == 'supplier' ? p.type == 'supplier' : p.type != 'supplier')
        .toList()
      ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));

    return Scaffold(
      appBar: AppBar(title: const Text('Khata')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openForm(null),
        icon: const Icon(Icons.person_add_alt),
        label: const Text('Add Party'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'customer', label: Text('Customers')),
                ButtonSegment(value: 'supplier', label: Text('Suppliers')),
              ],
              selected: {_tab},
              onSelectionChanged: (s) => setState(() => _tab = s.first),
            ),
          ),
          Expanded(
            child: list.isEmpty
                ? Center(child: Text('No ${_tab}s yet.', style: TextStyle(color: Colors.grey.shade600)))
                : ListView.builder(
                    itemCount: list.length,
                    itemBuilder: (_, i) {
                      final p = list[i];
                      final bal = calc.partyBalance(p.id);
                      return ListTile(
                        leading: CircleAvatar(child: Text(p.name.isNotEmpty ? p.name[0].toUpperCase() : '?')),
                        title: Text(p.name),
                        subtitle: Text(p.phone.isEmpty ? p.address : p.phone),
                        trailing: Text(
                          bal == 0 ? money(0) : '${money(bal.abs())} ${bal > 0 ? 'Dr' : 'Cr'}',
                          style: TextStyle(fontWeight: FontWeight.w700, color: bal > 0 ? Tones.green : (bal < 0 ? Tones.red : null)),
                        ),
                        onTap: () => _openForm(p),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  void _openForm(Party? existing) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (_) => _PartyForm(existing: existing, defaultType: _tab),
    );
  }
}

class _PartyForm extends ConsumerStatefulWidget {
  final Party? existing;
  final String defaultType;
  const _PartyForm({this.existing, required this.defaultType});
  @override
  ConsumerState<_PartyForm> createState() => _PartyFormState();
}

class _PartyFormState extends ConsumerState<_PartyForm> {
  late final TextEditingController _name;
  late final TextEditingController _phone;
  late final TextEditingController _gstin;
  late final TextEditingController _address;
  late final TextEditingController _opening;
  late String _type;
  String _openingType = 'receive';

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    _name = TextEditingController(text: e?.name ?? '');
    _phone = TextEditingController(text: e?.phone ?? '');
    _gstin = TextEditingController(text: e?.gstin ?? '');
    _address = TextEditingController(text: e?.address ?? '');
    _opening = TextEditingController(text: e != null ? '${e.openingBalance}' : '0');
    _type = e?.type ?? widget.defaultType;
    _openingType = e?.openingType ?? 'receive';
  }

  @override
  void dispose() {
    for (final c in [_name, _phone, _gstin, _address, _opening]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _save() async {
    final uid = ref.read(uidProvider);
    if (uid == null) return;
    if (_name.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Name is required')));
      return;
    }
    final e = widget.existing;
    final p = Party(
      id: e?.id ?? makeId(),
      createdAt: e?.createdAt ?? DateTime.now().millisecondsSinceEpoch,
      name: _name.text.trim(),
      phone: _phone.text.trim(),
      gstin: _gstin.text.trim(),
      address: _address.text.trim(),
      type: _type,
      openingBalance: toNum(_opening.text),
      openingType: _openingType,
    );
    await ref.read(firestoreServiceProvider).saveParty(uid, p);
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
            Text(widget.existing == null ? 'Add Party' : 'Edit Party', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 12),
            TextField(controller: _name, decoration: const InputDecoration(labelText: 'Name *')),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              initialValue: _type,
              decoration: const InputDecoration(labelText: 'Type'),
              items: const [DropdownMenuItem(value: 'customer', child: Text('Customer')), DropdownMenuItem(value: 'supplier', child: Text('Supplier'))],
              onChanged: (v) => setState(() => _type = v ?? 'customer'),
            ),
            const SizedBox(height: 10),
            Row(children: [
              Expanded(child: TextField(controller: _phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Phone'))),
              const SizedBox(width: 10),
              Expanded(child: TextField(controller: _gstin, decoration: const InputDecoration(labelText: 'GSTIN'))),
            ]),
            const SizedBox(height: 10),
            TextField(controller: _address, decoration: const InputDecoration(labelText: 'Address')),
            const SizedBox(height: 10),
            Row(children: [
              Expanded(child: TextField(controller: _opening, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Opening Balance'))),
              const SizedBox(width: 10),
              Expanded(child: DropdownButtonFormField<String>(
                initialValue: _openingType,
                decoration: const InputDecoration(labelText: 'Type'),
                items: const [DropdownMenuItem(value: 'receive', child: Text('To Receive')), DropdownMenuItem(value: 'pay', child: Text('To Pay'))],
                onChanged: (v) => setState(() => _openingType = v ?? 'receive'),
              )),
            ]),
            const SizedBox(height: 16),
            Align(alignment: Alignment.centerRight, child: FilledButton(onPressed: _save, child: const Text('Save'))),
          ],
        ),
      ),
    );
  }
}
