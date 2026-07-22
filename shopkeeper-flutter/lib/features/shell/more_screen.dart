import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/state/providers.dart';
import '../transactions/transactions_screen.dart';

class MoreScreen extends ConsumerWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileProvider).value;
    final isAdmin = ref.watch(isAdminProvider);
    final ident = profile?.displayName.isNotEmpty == true
        ? profile!.displayName
        : (profile?.phone.isNotEmpty == true ? '+91 ${profile!.phone}' : profile?.email ?? 'Account');

    return Scaffold(
      appBar: AppBar(title: const Text('More')),
      body: ListView(
        children: [
          Card(
            margin: const EdgeInsets.all(12),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(children: [
                    CircleAvatar(radius: 22, child: Text(ident.isNotEmpty ? ident[0].toUpperCase() : 'U')),
                    const SizedBox(width: 12),
                    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(ident, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                      Text('Signed in', style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
                    ])),
                  ]),
                  const SizedBox(height: 12),
                  Wrap(spacing: 8, children: [
                    Chip(label: Text('Plan: ${profile?.plan ?? 'free'}')),
                    Chip(label: Text('Role: ${profile?.role ?? 'user'}')),
                    Chip(label: Text(profile?.active == false ? 'Inactive' : 'Active')),
                  ]),
                ],
              ),
            ),
          ),
          _txnTile(context, Icons.shopping_cart_outlined, 'Purchases',
              const TxPageConfig(title: 'Purchases', show: ['PURCHASE'], create: ['PURCHASE'])),
          _txnTile(context, Icons.description_outlined, 'Estimates',
              const TxPageConfig(title: 'Estimates', show: ['ESTIMATE'], create: ['ESTIMATE'])),
          _txnTile(context, Icons.payments_outlined, 'Payments',
              const TxPageConfig(title: 'Payments', show: ['PAYMENT_IN', 'PAYMENT_OUT'], create: ['PAYMENT_IN', 'PAYMENT_OUT'])),
          _txnTile(context, Icons.money_off, 'Expenses',
              const TxPageConfig(title: 'Expenses', show: ['EXPENSE'], create: ['EXPENSE'])),
          _txnTile(context, Icons.assignment_return_outlined, 'Returns',
              const TxPageConfig(title: 'Returns', show: ['SALE_RETURN', 'PURCHASE_RETURN'], create: ['SALE_RETURN', 'PURCHASE_RETURN'])),
          const Divider(),
          if (isAdmin)
            ListTile(
              leading: const Icon(Icons.shield_outlined),
              title: const Text('Admin Console'),
              subtitle: const Text('Manage users, roles & subscriptions'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/admin'),
            ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Sign out'),
            onTap: () => ref.read(authServiceProvider).signOut(),
          ),
        ],
      ),
    );
  }

  Widget _txnTile(BuildContext context, IconData icon, String label, TxPageConfig config) {
    return ListTile(
      leading: Icon(icon),
      title: Text(label),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(builder: (_) => TransactionsScreen(config: config)),
      ),
    );
  }
}
