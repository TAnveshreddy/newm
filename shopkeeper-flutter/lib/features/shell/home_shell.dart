import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/i18n/locale_provider.dart';
import '../billing/billing_screen.dart';
import '../dashboard/dashboard_screen.dart';
import '../inventory/inventory_screen.dart';
import '../parties/parties_screen.dart';
import 'more_screen.dart';

/// Authenticated shell with a bottom navigation bar. Tabs are kept alive via
/// IndexedStack so switching is instant and scroll state is preserved.
class HomeShell extends ConsumerStatefulWidget {
  const HomeShell({super.key});
  @override
  ConsumerState<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends ConsumerState<HomeShell> {
  int _index = 0;

  static const _tabs = [
    DashboardScreen(),
    BillingScreen(),
    InventoryScreen(),
    PartiesScreen(),
    MoreScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _index, children: _tabs),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: [
          NavigationDestination(icon: const Icon(Icons.home_outlined), selectedIcon: const Icon(Icons.home), label: ref.tr('nav.dashboard')),
          NavigationDestination(icon: const Icon(Icons.receipt_long_outlined), selectedIcon: const Icon(Icons.receipt_long), label: ref.tr('nav.billing')),
          NavigationDestination(icon: const Icon(Icons.inventory_2_outlined), selectedIcon: const Icon(Icons.inventory_2), label: ref.tr('nav.inventory')),
          NavigationDestination(icon: const Icon(Icons.menu_book_outlined), selectedIcon: const Icon(Icons.menu_book), label: ref.tr('nav.khata')),
          NavigationDestination(icon: const Icon(Icons.more_horiz), label: ref.tr('nav.more')),
        ],
      ),
    );
  }
}
