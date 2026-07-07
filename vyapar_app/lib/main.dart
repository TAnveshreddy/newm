import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'models.dart';
import 'store.dart';
import 'screens/dashboard_screen.dart';
import 'screens/invoice_form.dart';
import 'screens/items_screen.dart';
import 'screens/parties_screen.dart';
import 'screens/transactions_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const VyaparLiteApp());
}

class VyaparLiteApp extends StatelessWidget {
  const VyaparLiteApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppStore()..load(),
      child: MaterialApp(
        title: 'Vyapar Lite',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorSchemeSeed: const Color(0xFFB71C1C),
          useMaterial3: true,
        ),
        home: const HomeShell(),
      ),
    );
  }
}

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int tab = 0;

  @override
  Widget build(BuildContext context) {
    final store = context.watch<AppStore>();
    if (!store.loaded) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return Scaffold(
      body: IndexedStack(
        index: tab,
        children: const [
          DashboardScreen(),
          PartiesScreen(),
          ItemsScreen(),
          TransactionsScreen(),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        tooltip: 'New transaction',
        onPressed: () => _showNewTxnSheet(context),
        child: const Icon(Icons.add),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: tab,
        onDestinationSelected: (i) => setState(() => tab = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.people), label: 'Parties'),
          NavigationDestination(icon: Icon(Icons.inventory_2), label: 'Items'),
          NavigationDestination(
              icon: Icon(Icons.receipt_long), label: 'Transactions'),
        ],
      ),
    );
  }

  void _showNewTxnSheet(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.receipt_long, color: Colors.green),
              title: const Text('New Sale Invoice'),
              onTap: () {
                Navigator.pop(ctx);
                Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) =>
                        const InvoiceFormScreen(type: TxnType.sale)));
              },
            ),
            ListTile(
              leading: const Icon(Icons.shopping_cart, color: Colors.blue),
              title: const Text('New Purchase Bill'),
              onTap: () {
                Navigator.pop(ctx);
                Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) =>
                        const InvoiceFormScreen(type: TxnType.purchase)));
              },
            ),
            ListTile(
              leading: const Icon(Icons.south_west, color: Colors.teal),
              title: const Text('Payment In (money received)'),
              onTap: () {
                Navigator.pop(ctx);
                showPaymentDialog(context, isIn: true);
              },
            ),
            ListTile(
              leading: const Icon(Icons.north_east, color: Colors.deepOrange),
              title: const Text('Payment Out (money given)'),
              onTap: () {
                Navigator.pop(ctx);
                showPaymentDialog(context, isIn: false);
              },
            ),
            ListTile(
              leading: const Icon(Icons.money_off, color: Colors.red),
              title: const Text('Record Expense'),
              onTap: () {
                Navigator.pop(ctx);
                showExpenseDialog(context);
              },
            ),
          ],
        ),
      ),
    );
  }
}
