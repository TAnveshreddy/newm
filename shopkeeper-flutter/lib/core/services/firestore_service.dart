import 'package:cloud_firestore/cloud_firestore.dart';

import '../models/models.dart';

/// Typed, uid-scoped gateway to the user's business data under
/// `userData/{uid}/…` — the same paths the web apps use. Reads are real-time
/// snapshot streams; writes are per-record so devices merge rather than clobber.
class FirestoreService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  CollectionReference<Map<String, dynamic>> _col(String uid, String name) =>
      _db.collection('userData').doc(uid).collection(name);

  Stream<List<Party>> parties(String uid) => _col(uid, 'parties')
      .snapshots()
      .map((s) => s.docs.map((d) => Party.fromMap(d.id, d.data())).toList());

  Stream<List<Item>> items(String uid) => _col(uid, 'items')
      .snapshots()
      .map((s) => s.docs.map((d) => Item.fromMap(d.id, d.data())).toList());

  Stream<List<Txn>> txns(String uid) => _col(uid, 'txns')
      .snapshots()
      .map((s) => s.docs.map((d) => Txn.fromMap(d.id, d.data())).toList());

  Stream<List<StockAdjustment>> adjustments(String uid) => _col(uid, 'adjustments')
      .snapshots()
      .map((s) => s.docs.map((d) => StockAdjustment.fromMap(d.id, d.data())).toList());

  Stream<BusinessSettings> settings(String uid) => _db
      .collection('userData')
      .doc(uid)
      .collection('meta')
      .doc('settings')
      .snapshots()
      .map((d) => BusinessSettings.fromMap(d.data() ?? {}));

  Stream<Map<String, dynamic>> counters(String uid) => _db
      .collection('userData')
      .doc(uid)
      .collection('meta')
      .doc('counters')
      .snapshots()
      .map((d) => d.data() ?? {});

  Future<void> saveItem(String uid, Item it) =>
      _col(uid, 'items').doc(it.id).set(it.toMap());
  Future<void> deleteItem(String uid, String id) => _col(uid, 'items').doc(id).delete();

  Future<void> saveParty(String uid, Party p) =>
      _col(uid, 'parties').doc(p.id).set(p.toMap());
  Future<void> deleteParty(String uid, String id) => _col(uid, 'parties').doc(id).delete();

  Future<void> saveTxn(String uid, Txn t) async {
    await _col(uid, 'txns').doc(t.id).set(t.toMap());
    final ref = _db.collection('userData').doc(uid).collection('meta').doc('counters');
    await ref.set({t.type: FieldValue.increment(1)}, SetOptions(merge: true));
  }

  Future<void> deleteTxn(String uid, String id) => _col(uid, 'txns').doc(id).delete();
}
