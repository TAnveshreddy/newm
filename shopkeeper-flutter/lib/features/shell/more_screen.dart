import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/i18n/locale_provider.dart';
import '../../core/i18n/translations.dart';
import '../../core/state/providers.dart';
import '../settings/business_profile_screen.dart';

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
                      Text(ref.tr('more.signedIn'), style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
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
          ListTile(
            leading: const Icon(Icons.storefront_outlined),
            title: const Text('Business Profile'),
            subtitle: const Text('Name, phone, GSTIN & address on invoices'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const BusinessProfileScreen())),
          ),
          ListTile(
            leading: const Icon(Icons.language),
            title: Text(ref.tr('set.language')),
            subtitle: Text(_langName(ref.watch(langProvider) ?? 'en')),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _pickLanguage(context, ref),
          ),
          ListTile(
            leading: const Icon(Icons.cloud_download_outlined),
            title: const Text('Download Backup'),
            subtitle: const Text('Share all your data as a JSON file'),
            onTap: () async {
              final uid = ref.read(uidProvider);
              if (uid != null) {
                try {
                  await ref.read(backupServiceProvider).export(uid);
                } catch (e) {
                  if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Backup failed: $e')));
                }
              }
            },
          ),
          ListTile(
            leading: const Icon(Icons.cloud_upload_outlined),
            title: const Text('Restore from Backup'),
            subtitle: const Text('Load data from a backup file'),
            onTap: () async {
              final uid = ref.read(uidProvider);
              if (uid == null) return;
              try {
                final ok = await ref.read(backupServiceProvider).restore(uid);
                if (ok && context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Backup restored')));
                }
              } catch (e) {
                if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Restore failed: $e')));
              }
            },
          ),
          const Divider(),
          if (isAdmin)
            ListTile(
              leading: const Icon(Icons.shield_outlined),
              title: Text(ref.tr('nav.admin')),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push('/admin'),
            ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: Text(ref.tr('common.logout')),
            onTap: () => ref.read(authServiceProvider).signOut(),
          ),
        ],
      ),
    );
  }

  String _langName(String code) {
    final l = kLanguages.where((x) => x.code == code);
    return l.isNotEmpty ? '${l.first.label} (${l.first.english})' : code;
  }

  void _pickLanguage(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      builder: (_) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: kLanguages.map((l) => ListTile(
                title: Text(l.label),
                subtitle: Text(l.english),
                trailing: (ref.read(langProvider) ?? 'en') == l.code ? const Icon(Icons.check) : null,
                onTap: () {
                  ref.read(langProvider.notifier).setLang(l.code);
                  Navigator.pop(context);
                },
              )).toList(),
        ),
      ),
    );
  }
}
