import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

import 'models.dart';

/// Single source of truth for all app data. Persists everything as one JSON
/// file in the app documents directory (offline-first, no server needed).
class AppStore extends ChangeNotifier {
  final List<Party> parties = [];
  final List<Item> items = [];
  final List<Txn> txns = [];

  bool loaded = false;

  // ---------- Dashboard metrics ----------

  double get toCollect => parties
      .where((p) => p.balance > 0)
      .fold(0, (sum, p) => sum + p.balance);

  double get toPay => parties
      .where((p) => p.balance < 0)
      .fold(0, (sum, p) => sum + p.balance.abs());

  double get salesThisMonth {
    final now = DateTime.now();
    return txns
        .where((t) =>
            t.type == TxnType.sale &&
            t.date.year == now.year &&
            t.date.month == now.month)
        .fold(0, (sum, t) => sum + t.total);
  }

  double get expensesThisMonth {
    final now = DateTime.now();
    return txns
        .where((t) =>
            t.type == TxnType.expense &&
            t.date.year == now.year &&
            t.date.month == now.month)
        .fold(0, (sum, t) => sum + t.total);
  }

  double get stockValue =>
      items.fold(0, (sum, i) => sum + i.stock * i.purchasePrice);

  int get lowStockCount => items.where((i) => i.isLowStock).length;

  // ---------- Lookups ----------

  Party? partyById(String id) {
    for (final p in parties) {
      if (p.id == id) return p;
    }
    return null;
  }

  Item? itemById(String id) {
    for (final i in items) {
      if (i.id == id) return i;
    }
    return null;
  }

  List<Txn> txnsOfParty(String partyId) =>
      txns.where((t) => t.partyId == partyId).toList()
        ..sort((a, b) => b.date.compareTo(a.date));

  List<Txn> get txnsNewestFirst =>
      txns.toList()..sort((a, b) => b.date.compareTo(a.date));

  bool partyHasTxns(String partyId) =>
      txns.any((t) => t.partyId == partyId);

  bool itemHasTxns(String itemId) =>
      txns.any((t) => t.lines.any((l) => l.itemId == itemId));

  // ---------- Mutations ----------

  void upsertParty(Party party) {
    final idx = parties.indexWhere((p) => p.id == party.id);
    if (idx >= 0) {
      parties[idx] = party;
    } else {
      parties.add(party);
    }
    _saveAndNotify();
  }

  void deleteParty(String id) {
    parties.removeWhere((p) => p.id == id);
    _saveAndNotify();
  }

  void upsertItem(Item item) {
    final idx = items.indexWhere((i) => i.id == item.id);
    if (idx >= 0) {
      items[idx] = item;
    } else {
      items.add(item);
    }
    _saveAndNotify();
  }

  void deleteItem(String id) {
    items.removeWhere((i) => i.id == id);
    _saveAndNotify();
  }

  void addTxn(Txn txn) {
    txns.add(txn);
    _applyEffects(txn, 1);
    _saveAndNotify();
  }

  void deleteTxn(String id) {
    final idx = txns.indexWhere((t) => t.id == id);
    if (idx < 0) return;
    final txn = txns.removeAt(idx);
    _applyEffects(txn, -1);
    _saveAndNotify();
  }

  /// Applies (sign = 1) or reverses (sign = -1) a transaction's effect on
  /// party balance and item stock.
  void _applyEffects(Txn txn, int sign) {
    final party = txn.partyId == cashPartyId ? null : partyById(txn.partyId);
    switch (txn.type) {
      case TxnType.sale:
        if (party != null) party.balance += sign * txn.due;
        for (final line in txn.lines) {
          final item = itemById(line.itemId);
          if (item != null) item.stock -= sign * line.qty;
        }
        break;
      case TxnType.purchase:
        if (party != null) party.balance -= sign * txn.due;
        for (final line in txn.lines) {
          final item = itemById(line.itemId);
          if (item != null) item.stock += sign * line.qty;
        }
        break;
      case TxnType.paymentIn:
        if (party != null) party.balance -= sign * txn.total;
        break;
      case TxnType.paymentOut:
        if (party != null) party.balance += sign * txn.total;
        break;
      case TxnType.expense:
        break;
    }
  }

  // ---------- Persistence ----------

  Future<File?> _dataFile() async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      return File('${dir.path}${Platform.pathSeparator}vyapar_lite_data.json');
    } catch (_) {
      return null; // Unsupported platform: run in-memory only.
    }
  }

  Future<void> load() async {
    try {
      final file = await _dataFile();
      if (file != null && await file.exists()) {
        final data =
            jsonDecode(await file.readAsString()) as Map<String, dynamic>;
        parties
          ..clear()
          ..addAll(((data['parties'] ?? []) as List)
              .map((e) => Party.fromJson(e as Map<String, dynamic>)));
        items
          ..clear()
          ..addAll(((data['items'] ?? []) as List)
              .map((e) => Item.fromJson(e as Map<String, dynamic>)));
        txns
          ..clear()
          ..addAll(((data['txns'] ?? []) as List)
              .map((e) => Txn.fromJson(e as Map<String, dynamic>)));
      }
    } catch (e) {
      debugPrint('Failed to load data: $e');
    }
    loaded = true;
    notifyListeners();
  }

  Future<void> _save() async {
    try {
      final file = await _dataFile();
      if (file == null) return;
      final data = {
        'parties': parties.map((p) => p.toJson()).toList(),
        'items': items.map((i) => i.toJson()).toList(),
        'txns': txns.map((t) => t.toJson()).toList(),
      };
      await file.writeAsString(jsonEncode(data));
    } catch (e) {
      debugPrint('Failed to save data: $e');
    }
  }

  void _saveAndNotify() {
    _save();
    notifyListeners();
  }
}
