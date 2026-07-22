import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/state/providers.dart';
import '../../core/theme/app_theme.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _phone = TextEditingController();
  final _otp = TextEditingController();
  bool _otpStep = false;
  bool _busy = false;
  String? _verificationId;

  @override
  void dispose() {
    _phone.dispose();
    _otp.dispose();
    super.dispose();
  }

  void _snack(String m) {
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(m)));
  }

  Future<void> _google() async {
    setState(() => _busy = true);
    try {
      await ref.read(authServiceProvider).signInWithGoogle();
    } catch (e) {
      _snack('Google sign-in failed: $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _sendOtp() async {
    final p = _phone.text.replaceAll(RegExp(r'\D'), '');
    if (!RegExp(r'^[6-9]\d{9}$').hasMatch(p)) {
      _snack('Enter a valid 10-digit mobile number');
      return;
    }
    setState(() => _busy = true);
    try {
      await ref.read(authServiceProvider).verifyPhone(
            phoneE164: '+91$p',
            codeSent: (id) => setState(() {
              _verificationId = id;
              _otpStep = true;
              _busy = false;
            }),
            onError: (FirebaseAuthException e) {
              _snack('Could not send OTP: ${e.message}');
              setState(() => _busy = false);
            },
          );
    } catch (e) {
      _snack('Could not send OTP: $e');
      setState(() => _busy = false);
    }
  }

  Future<void> _verify() async {
    if (_verificationId == null) return;
    if (!RegExp(r'^\d{6}$').hasMatch(_otp.text)) {
      _snack('Enter the 6-digit OTP');
      return;
    }
    setState(() => _busy = true);
    try {
      await ref.read(authServiceProvider).confirmOtp(_verificationId!, _otp.text);
    } catch (_) {
      _snack('Wrong or expired OTP — try again');
      setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 380),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 56, height: 56,
                      decoration: BoxDecoration(color: AppTheme.primary, borderRadius: BorderRadius.circular(16)),
                      alignment: Alignment.center,
                      child: const Text('S', style: TextStyle(color: Colors.white, fontSize: 30, fontWeight: FontWeight.w800)),
                    ),
                    const SizedBox(height: 12),
                    const Text('Shopkeeper', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 4),
                    Text('Billing · Inventory · Khata — synced across your devices',
                        textAlign: TextAlign.center, style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
                    const SizedBox(height: 20),
                    if (!_otpStep) ...[
                      OutlinedButton.icon(
                        onPressed: _busy ? null : _google,
                        icon: const Icon(Icons.g_mobiledata, size: 28),
                        label: const Text('Continue with Google'),
                        style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(46)),
                      ),
                      const SizedBox(height: 14),
                      Row(children: [
                        const Expanded(child: Divider()),
                        Padding(padding: const EdgeInsets.symmetric(horizontal: 8), child: Text('OR', style: TextStyle(color: Colors.grey.shade500))),
                        const Expanded(child: Divider()),
                      ]),
                      const SizedBox(height: 14),
                      TextField(
                        controller: _phone,
                        keyboardType: TextInputType.phone,
                        maxLength: 10,
                        decoration: const InputDecoration(prefixText: '+91  ', labelText: 'Mobile Number', counterText: ''),
                      ),
                      const SizedBox(height: 12),
                      FilledButton(
                        onPressed: _busy ? null : _sendOtp,
                        style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(46)),
                        child: _busy ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Get OTP'),
                      ),
                    ] else ...[
                      Text('Code sent to +91 ${_phone.text}', style: TextStyle(color: Colors.grey.shade600)),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _otp,
                        keyboardType: TextInputType.number,
                        maxLength: 6,
                        textAlign: TextAlign.center,
                        style: const TextStyle(letterSpacing: 8, fontSize: 18),
                        decoration: const InputDecoration(labelText: 'Enter OTP', counterText: ''),
                      ),
                      const SizedBox(height: 12),
                      FilledButton(
                        onPressed: _busy ? null : _verify,
                        style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(46)),
                        child: const Text('Verify & Login'),
                      ),
                      TextButton(onPressed: () => setState(() => _otpStep = false), child: const Text('← Change number')),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
