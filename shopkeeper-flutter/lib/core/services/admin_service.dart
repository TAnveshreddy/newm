import 'package:cloud_firestore/cloud_firestore.dart';

import '../models/models.dart';

/// Admin operations over `users/*`. Every write is also authorised by the
/// Firestore rules (admin-only), so the UI only exposes permitted actions.
class AdminService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  Stream<List<UserProfile>> users() => _db
      .collection('users')
      .orderBy('createdAt', descending: true)
      .snapshots()
      .map((s) => s.docs.map((d) => UserProfile.fromMap(d.id, d.data())).toList());

  Future<void> setActive(String uid, bool active) => _db.collection('users').doc(uid).set({
        'active': active,
        if (active) 'activatedAt': FieldValue.serverTimestamp(),
      }, SetOptions(merge: true));

  Future<void> setRole(String uid, String role) =>
      _db.collection('users').doc(uid).set({'role': role}, SetOptions(merge: true));

  Future<void> setPlan(String uid, String plan) => _db.collection('users').doc(uid).set(
      {'plan': plan, 'planUpdatedAt': FieldValue.serverTimestamp()}, SetOptions(merge: true));

  Future<void> deleteUser(String uid) async {
    for (final col in ['parties', 'items', 'txns', 'adjustments']) {
      final snap = await _db.collection('userData').doc(uid).collection(col).get();
      for (final d in snap.docs) {
        await d.reference.delete();
      }
    }
    final meta = await _db.collection('userData').doc(uid).collection('meta').get();
    for (final d in meta.docs) {
      await d.reference.delete();
    }
    await _db.collection('users').doc(uid).delete();
  }
}
