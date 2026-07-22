import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/state/providers.dart';

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
}
