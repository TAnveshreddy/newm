import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/models.dart';
import '../../core/state/providers.dart';

class AdminScreen extends ConsumerWidget {
  const AdminScreen({super.key});

  String _ts(Timestamp? t) {
    if (t == null) return '—';
    final d = t.toDate();
    return '${d.day}/${d.month}/${d.year}';
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final admin = ref.watch(adminServiceProvider);
    final myUid = ref.watch(uidProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Admin — Users')),
      body: StreamBuilder<List<UserProfile>>(
        stream: admin.users(),
        builder: (context, snap) {
          if (snap.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError) {
            return Center(child: Padding(padding: const EdgeInsets.all(24), child: Text('Could not load users.\nEnsure your role is admin and rules are deployed.\n\n${snap.error}', textAlign: TextAlign.center)));
          }
          final users = snap.data ?? [];
          final active = users.where((u) => u.active).length;
          final admins = users.where((u) => u.role == 'admin').length;
          return ListView(
            padding: const EdgeInsets.all(12),
            children: [
              Wrap(spacing: 8, children: [
                Chip(label: Text('Total: ${users.length}')),
                Chip(label: Text('Active: $active')),
                Chip(label: Text('Inactive: ${users.length - active}')),
                Chip(label: Text('Admins: $admins')),
              ]),
              const SizedBox(height: 8),
              ...users.map((u) => _userCard(context, ref, admin, u, u.uid == myUid)),
            ],
          );
        },
      ),
    );
  }

  Widget _userCard(BuildContext context, WidgetRef ref, admin, UserProfile u, bool isSelf) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Expanded(child: Text(u.displayName.isNotEmpty ? u.displayName : (u.phone.isNotEmpty ? '+91 ${u.phone}' : u.email),
                  style: const TextStyle(fontWeight: FontWeight.w700))),
              if (isSelf) const Chip(label: Text('you')),
              Chip(
                label: Text(u.active ? 'Active' : 'Inactive'),
                backgroundColor: (u.active ? Colors.green : Colors.red).withValues(alpha: 0.12),
              ),
            ]),
            Text('${u.email} ${u.phone.isNotEmpty ? '· +91 ${u.phone}' : ''}', style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
            Text('Registered ${_ts(u.createdAt)} · Last login ${_ts(u.lastLogin)}', style: TextStyle(color: Colors.grey.shade600, fontSize: 11)),
            const SizedBox(height: 8),
            Row(children: [
              Expanded(child: DropdownButtonFormField<String>(
                initialValue: kRoles.contains(u.role) ? u.role : 'user',
                decoration: const InputDecoration(labelText: 'Role', isDense: true),
                items: kRoles.map((r) => DropdownMenuItem(value: r, child: Text(r))).toList(),
                onChanged: isSelf ? null : (v) { if (v != null) admin.setRole(u.uid, v); },
              )),
              const SizedBox(width: 8),
              Expanded(child: DropdownButtonFormField<String>(
                initialValue: kPlans.contains(u.plan) ? u.plan : 'free',
                decoration: const InputDecoration(labelText: 'Plan', isDense: true),
                items: kPlans.map((p) => DropdownMenuItem(value: p, child: Text(p))).toList(),
                onChanged: (v) { if (v != null) admin.setPlan(u.uid, v); },
              )),
            ]),
            const SizedBox(height: 8),
            if (!isSelf)
              Row(mainAxisAlignment: MainAxisAlignment.end, children: [
                TextButton(
                  onPressed: () => admin.setActive(u.uid, !u.active),
                  child: Text(u.active ? 'Deactivate' : 'Activate'),
                ),
                const SizedBox(width: 8),
                TextButton(
                  onPressed: () async {
                    final ok = await showDialog<bool>(
                      context: context,
                      builder: (c) => AlertDialog(
                        title: const Text('Delete user?'),
                        content: Text('Remove ${u.displayName.isNotEmpty ? u.displayName : u.email} and all their data. This cannot be undone.'),
                        actions: [
                          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('Cancel')),
                          FilledButton(onPressed: () => Navigator.pop(c, true), child: const Text('Delete')),
                        ],
                      ),
                    );
                    if (ok == true) await admin.deleteUser(u.uid);
                  },
                  child: const Text('Delete', style: TextStyle(color: Colors.red)),
                ),
              ]),
          ],
        ),
      ),
    );
  }
}
