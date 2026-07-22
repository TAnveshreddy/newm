import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/i18n/locale_provider.dart';
import 'core/state/providers.dart';
import 'core/theme/app_theme.dart';
import 'features/admin/admin_screen.dart';
import 'features/auth/login_screen.dart';
import 'features/language/language_screen.dart';
import 'features/shell/home_shell.dart';

/// Router with an auth redirect guard. Unauthenticated users are sent to
/// /login; the admin route additionally requires an admin profile. The router
/// refreshes whenever Firebase auth state changes.
final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    refreshListenable: GoRouterRefreshStream(ref.watch(authServiceProvider).authState()),
    redirect: (context, state) {
      final loc = state.matchedLocation;
      // First run: pick a language before anything else.
      final chosenLang = ref.read(langProvider) != null;
      if (!chosenLang) return loc == '/language' ? null : '/language';

      final loggedIn = ref.read(authStateProvider).value != null;
      final loggingIn = loc == '/login';
      if (!loggedIn) return loggingIn ? null : '/login';
      if (loggingIn || loc == '/language') return '/';
      if (loc == '/admin' && !ref.read(isAdminProvider)) return '/';
      return null;
    },
    routes: [
      GoRoute(path: '/language', builder: (_, _) => const LanguageScreen()),
      GoRoute(path: '/login', builder: (_, _) => const LoginScreen()),
      GoRoute(path: '/', builder: (_, _) => const HomeShell()),
      GoRoute(path: '/admin', builder: (_, _) => const AdminScreen()),
    ],
  );
});

class ShopkeeperApp extends ConsumerWidget {
  const ShopkeeperApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'Shopkeeper',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,
      routerConfig: router,
    );
  }
}

/// Bridges a [Stream] to a [Listenable] for GoRouter's refreshListenable.
class GoRouterRefreshStream extends ChangeNotifier {
  GoRouterRefreshStream(Stream<dynamic> stream) {
    notifyListeners();
    _sub = stream.asBroadcastStream().listen((_) => notifyListeners());
  }
  late final dynamic _sub;

  @override
  void dispose() {
    _sub.cancel();
    super.dispose();
  }
}
