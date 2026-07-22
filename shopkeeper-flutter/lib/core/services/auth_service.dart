import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../models/models.dart';

/// Authentication + account-profile provisioning.
///
/// Mirrors the web apps: on first sign-in a `users/{uid}` profile is created as
/// a plain user/free/active account; `lastLogin` is stamped on each sign-in.
/// Google uses native Google Sign-In; phone uses Firebase's SMS OTP.
class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  Stream<User?> authState() => _auth.authStateChanges();
  User? get currentUser => _auth.currentUser;

  Stream<UserProfile?> profile() => _auth.authStateChanges().asyncExpand((u) {
        if (u == null) return Stream<UserProfile?>.value(null);
        return _db.collection('users').doc(u.uid).snapshots().map(
              (d) => d.exists ? UserProfile.fromMap(d.id, d.data()!) : null,
            );
      });

  Future<void> signInWithGoogle() async {
    final googleUser = await GoogleSignIn().signIn();
    if (googleUser == null) throw Exception('Sign-in cancelled');
    final gAuth = await googleUser.authentication;
    final cred = GoogleAuthProvider.credential(
      idToken: gAuth.idToken,
      accessToken: gAuth.accessToken,
    );
    final res = await _auth.signInWithCredential(cred);
    await _ensureProfile(res.user!);
  }

  /// Start phone verification. On Android auto-retrieval may complete sign-in
  /// automatically; otherwise [codeSent] fires with a verificationId.
  Future<void> verifyPhone({
    required String phoneE164,
    required void Function(String verificationId) codeSent,
    required void Function(FirebaseAuthException e) onError,
    void Function()? onAutoVerified,
  }) async {
    await _auth.verifyPhoneNumber(
      phoneNumber: phoneE164,
      verificationCompleted: (cred) async {
        final res = await _auth.signInWithCredential(cred);
        await _ensureProfile(res.user!);
        onAutoVerified?.call();
      },
      verificationFailed: onError,
      codeSent: (id, _) => codeSent(id),
      codeAutoRetrievalTimeout: (_) {},
    );
  }

  Future<void> confirmOtp(String verificationId, String smsCode) async {
    final cred = PhoneAuthProvider.credential(
      verificationId: verificationId,
      smsCode: smsCode,
    );
    final res = await _auth.signInWithCredential(cred);
    await _ensureProfile(res.user!);
  }

  Future<void> signOut() async {
    await GoogleSignIn().signOut();
    await _auth.signOut();
  }

  Future<void> _ensureProfile(User user) async {
    final ref = _db.collection('users').doc(user.uid);
    final snap = await ref.get();
    final now = FieldValue.serverTimestamp();
    if (!snap.exists) {
      await ref.set({
        'uid': user.uid,
        'phone': user.phoneNumber ?? '',
        'email': user.email ?? '',
        'displayName': user.displayName ?? '',
        'provider': user.providerData.isNotEmpty ? user.providerData.first.providerId : '',
        'plan': 'free',
        'role': 'user',
        'active': true,
        'createdAt': now,
        'activatedAt': now,
        'lastLogin': now,
      });
    } else {
      await ref.set({'lastLogin': now}, SetOptions(merge: true));
    }
  }
}
