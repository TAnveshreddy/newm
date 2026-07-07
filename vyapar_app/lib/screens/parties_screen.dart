import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models.dart';
import '../store.dart';
import 'transactions_screen.dart';

class PartiesScreen extends StatelessWidget {
  const PartiesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final store = context.watch<AppStore>();
    final parties = store.parties.toList()
      ..sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Parties'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_add),
            tooltip: 'Add party',
            onPressed: () => showPartyDialog(context),
          ),
        ],
      ),
      body: parties.isEmpty
          ? const Center(
              child: Text('No parties yet.\nTap the icon above to add one.',
                  textAlign: TextAlign.center),
            )
          : ListView.builder(
              itemCount: parties.length,
              itemBuilder: (context, index) {
                final party = parties[index];
                final owesUs = party.balance >= 0;
                return ListTile(
                  leading: CircleAvatar(
                    child: Text(party.name.isEmpty
                        ? '?'
                        : party.name[0].toUpperCase()),
                  ),
                  title: Text(party.name),
                  subtitle: Text(
                      '${party.isSupplier ? 'Supplier' : 'Customer'}'
                      '${party.phone.isEmpty ? '' : ' • ${party.phone}'}'),
                  trailing: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        money(party.balance.abs()),
                        style: TextStyle(
                          color: owesUs ? Colors.green : Colors.red,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        owesUs ? 'You will get' : 'You will pay',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => PartyDetailScreen(partyId: party.id),
                    ),
                  ),
                  onLongPress: () => showPartyDialog(context, party: party),
                );
              },
            ),
    );
  }
}

class PartyDetailScreen extends StatelessWidget {
  const PartyDetailScreen({super.key, required this.partyId});

  final String partyId;

  @override
  Widget build(BuildContext context) {
    final store = context.watch<AppStore>();
    final party = store.partyById(partyId);
    if (party == null) {
      return Scaffold(
        appBar: AppBar(),
        body: const Center(child: Text('Party not found')),
      );
    }
    final history = store.txnsOfParty(partyId);
    final owesUs = party.balance >= 0;

    return Scaffold(
      appBar: AppBar(
        title: Text(party.name),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () => showPartyDialog(context, party: party),
          ),
          IconButton(
            icon: const Icon(Icons.delete),
            onPressed: () async {
              if (store.partyHasTxns(partyId)) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                    content: Text(
                        'Cannot delete: party has transactions. Delete those first.')));
                return;
              }
              final ok = await showDialog<bool>(
                context: context,
                builder: (ctx) => AlertDialog(
                  title: const Text('Delete party?'),
                  content: Text('Delete "${party.name}" permanently?'),
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
              if (ok == true && context.mounted) {
                store.deleteParty(partyId);
                Navigator.of(context).pop();
              }
            },
          ),
        ],
      ),
      body: Column(
        children: [
          Card(
            margin: const EdgeInsets.all(12),
            child: ListTile(
              title: Text(owesUs ? 'You will get' : 'You will pay'),
              trailing: Text(
                money(party.balance.abs()),
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: owesUs ? Colors.green : Colors.red,
                ),
              ),
            ),
          ),
          Expanded(
            child: history.isEmpty
                ? const Center(child: Text('No transactions with this party'))
                : ListView(
                    children: [for (final txn in history) TxnTile(txn: txn)],
                  ),
          ),
        ],
      ),
    );
  }
}

/// Add / edit party dialog.
Future<void> showPartyDialog(BuildContext context, {Party? party}) async {
  final store = context.read<AppStore>();
  final nameCtrl = TextEditingController(text: party?.name ?? '');
  final phoneCtrl = TextEditingController(text: party?.phone ?? '');
  final openingCtrl = TextEditingController();
  bool isSupplier = party?.isSupplier ?? false;

  await showDialog<void>(
    context: context,
    builder: (ctx) => StatefulBuilder(
      builder: (ctx, setState) => AlertDialog(
        title: Text(party == null ? 'Add Party' : 'Edit Party'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                autofocus: true,
                decoration: const InputDecoration(labelText: 'Name *'),
              ),
              TextField(
                controller: phoneCtrl,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(labelText: 'Phone'),
              ),
              if (party == null)
                TextField(
                  controller: openingCtrl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Opening balance (they owe you)',
                    hintText: '0',
                  ),
                ),
              const SizedBox(height: 8),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Is a supplier'),
                value: isSupplier,
                onChanged: (v) => setState(() => isSupplier = v),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              final name = nameCtrl.text.trim();
              if (name.isEmpty) return;
              if (party == null) {
                store.upsertParty(Party(
                  id: newId(),
                  name: name,
                  phone: phoneCtrl.text.trim(),
                  isSupplier: isSupplier,
                  balance: double.tryParse(openingCtrl.text.trim()) ?? 0,
                ));
              } else {
                party.name = name;
                party.phone = phoneCtrl.text.trim();
                party.isSupplier = isSupplier;
                store.upsertParty(party);
              }
              Navigator.pop(ctx);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    ),
  );
}
