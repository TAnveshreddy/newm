import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/models/models.dart';
import '../../core/state/providers.dart';

/// Edit the logged-in owner's business profile. These details are stored per
/// user at userData/{uid}/meta/settings and appear on every invoice.
class BusinessProfileScreen extends ConsumerStatefulWidget {
  const BusinessProfileScreen({super.key});
  @override
  ConsumerState<BusinessProfileScreen> createState() => _BusinessProfileScreenState();
}

class _BusinessProfileScreenState extends ConsumerState<BusinessProfileScreen> {
  final _name = TextEditingController();
  final _phone = TextEditingController();
  final _email = TextEditingController();
  final _gstin = TextEditingController();
  final _address = TextEditingController();
  final _upi = TextEditingController();
  bool _taxEnabled = true;
  bool _seeded = false;
  bool _dirty = false;
  bool _saving = false;

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    _email.dispose();
    _gstin.dispose();
    _address.dispose();
    _upi.dispose();
    super.dispose();
  }

  void _seed(BusinessSettings s) {
    if (_seeded && _dirty) return; // don't clobber in-progress edits
    _name.text = s.businessName == 'My Business' ? '' : s.businessName;
    _phone.text = s.phone;
    _email.text = s.email;
    _gstin.text = s.gstin;
    _address.text = s.address;
    _upi.text = s.upiId;
    _taxEnabled = s.taxEnabled;
    _seeded = true;
  }

  Future<void> _save() async {
    final uid = ref.read(uidProvider);
    if (uid == null) return;
    setState(() => _saving = true);
    final s = BusinessSettings(
      businessName: _name.text.trim().isEmpty ? 'My Business' : _name.text.trim(),
      phone: _phone.text.trim(),
      email: _email.text.trim(),
      gstin: _gstin.text.trim(),
      address: _address.text.trim(),
      upiId: _upi.text.trim(),
      taxEnabled: _taxEnabled,
    );
    try {
      await ref.read(firestoreServiceProvider).saveSettings(uid, s);
      _dirty = false;
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Business profile saved')));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Save failed: $e')));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    // Keep the form in sync with the loaded profile until the user edits it.
    final loaded = ref.watch(settingsProvider).value;
    if (loaded != null) _seed(loaded);

    InputDecoration dec(String label) => InputDecoration(labelText: label, border: const OutlineInputBorder());
    void mark(String _) => _dirty = true;

    return Scaffold(
      appBar: AppBar(title: const Text('Business Profile')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text('These details appear on every invoice you print or share.', style: TextStyle(color: Colors.grey.shade600)),
          const SizedBox(height: 16),
          TextField(controller: _name, onChanged: mark, decoration: dec('Business Name')),
          const SizedBox(height: 12),
          TextField(controller: _phone, onChanged: mark, keyboardType: TextInputType.phone, decoration: dec('Phone')),
          const SizedBox(height: 12),
          TextField(controller: _email, onChanged: mark, keyboardType: TextInputType.emailAddress, decoration: dec('Email')),
          const SizedBox(height: 12),
          TextField(controller: _gstin, onChanged: mark, textCapitalization: TextCapitalization.characters, decoration: dec('GSTIN')),
          const SizedBox(height: 12),
          TextField(controller: _address, onChanged: mark, maxLines: 3, decoration: dec('Address')),
          const SizedBox(height: 12),
          TextField(controller: _upi, onChanged: mark, decoration: dec('UPI ID (optional)')),
          const SizedBox(height: 8),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('Enable GST on invoices'),
            value: _taxEnabled,
            onChanged: (v) => setState(() { _taxEnabled = v; _dirty = true; }),
          ),
          const SizedBox(height: 16),
          FilledButton(onPressed: _saving ? null : _save, child: Text(_saving ? 'Saving…' : 'Save Profile')),
        ],
      ),
    );
  }
}
