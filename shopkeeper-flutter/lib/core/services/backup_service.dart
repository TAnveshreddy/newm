import 'dart:convert';
import 'dart:io';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

/// Export the user's full dataset to a JSON file (shared via the system sheet)
/// and restore it back into Firestore. Data already lives in the cloud and
/// syncs across devices; this is for an offline copy / manual migration.
class BackupService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  Future<void> export(String uid) async {
    final root = _db.collection('userData').doc(uid);
    final payload = <String, dynamic>{
      'app': 'shopkeeper',
      'version': 1,
      'exportedAt': DateTime.now().toIso8601String(),
    };
    for (final col in ['parties', 'items', 'txns', 'adjustments']) {
      final snap = await root.collection(col).get();
      payload[col] = snap.docs.map((d) => d.data()).toList();
    }
    final settings = await root.collection('meta').doc('settings').get();
    payload['settings'] = settings.data() ?? {};

    final dir = await getTemporaryDirectory();
    final stamp = DateTime.now().toIso8601String().substring(0, 10);
    final file = File('${dir.path}/shopkeeper-backup-$stamp.json');
    await file.writeAsString(const JsonEncoder.withIndent('  ').convert(payload));
    await Share.shareXFiles([XFile(file.path)], text: 'Shopkeeper backup');
  }

  /// Returns true on success. Picks a JSON file and writes it back to Firestore.
  Future<bool> restore(String uid) async {
    final result = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['json']);
    if (result == null || result.files.single.path == null) return false;
    final text = await File(result.files.single.path!).readAsString();
    final data = jsonDecode(text) as Map<String, dynamic>;
    if (data['app'] != 'shopkeeper') throw Exception('Not a Shopkeeper backup');

    final root = _db.collection('userData').doc(uid);
    for (final col in ['parties', 'items', 'txns', 'adjustments']) {
      for (final rec in (data[col] as List<dynamic>? ?? [])) {
        final m = Map<String, dynamic>.from(rec as Map);
        await root.collection(col).doc(m['id'].toString()).set(m);
      }
    }
    if (data['settings'] is Map) {
      await root.collection('meta').doc('settings').set(
            Map<String, dynamic>.from(data['settings'] as Map),
            SetOptions(merge: true),
          );
    }
    return true;
  }
}
