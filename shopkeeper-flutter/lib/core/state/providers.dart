import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/models.dart';
import '../services/admin_service.dart';
import '../services/auth_service.dart';
import '../services/firestore_service.dart';

// ---- services ----
final authServiceProvider = Provider<AuthService>((_) => AuthService());
final firestoreServiceProvider = Provider<FirestoreService>((_) => FirestoreService());
final adminServiceProvider = Provider<AdminService>((_) => AdminService());

// ---- auth ----
final authStateProvider = StreamProvider<User?>((ref) => ref.watch(authServiceProvider).authState());
final profileProvider = StreamProvider<UserProfile?>((ref) => ref.watch(authServiceProvider).profile());

final uidProvider = Provider<String?>((ref) => ref.watch(authStateProvider).value?.uid);
final isAdminProvider = Provider<bool>((ref) => ref.watch(profileProvider).value?.role == 'admin');

// ---- business data (live) ----
Stream<T> _scoped<T>(Ref ref, Stream<T> Function(String uid) fn, T empty) {
  final uid = ref.watch(uidProvider);
  if (uid == null) return Stream<T>.value(empty);
  return fn(uid);
}

final partiesProvider = StreamProvider<List<Party>>(
    (ref) => _scoped(ref, (u) => ref.watch(firestoreServiceProvider).parties(u), const []));
final itemsProvider = StreamProvider<List<Item>>(
    (ref) => _scoped(ref, (u) => ref.watch(firestoreServiceProvider).items(u), const []));
final txnsProvider = StreamProvider<List<Txn>>(
    (ref) => _scoped(ref, (u) => ref.watch(firestoreServiceProvider).txns(u), const []));
final adjustmentsProvider = StreamProvider<List<StockAdjustment>>(
    (ref) => _scoped(ref, (u) => ref.watch(firestoreServiceProvider).adjustments(u), const []));
final settingsProvider = StreamProvider<BusinessSettings>(
    (ref) => _scoped(ref, (u) => ref.watch(firestoreServiceProvider).settings(u), BusinessSettings()));
final countersProvider = StreamProvider<Map<String, dynamic>>(
    (ref) => _scoped(ref, (u) => ref.watch(firestoreServiceProvider).counters(u), const {}));
