import '../domain/txn_config.dart';
import '../models/models.dart';
import '../util/num_util.dart';

/// Pure derived business logic (stock, balances, profit, low-stock,
/// receivable/payable) — ported verbatim from the web apps so results match.
class Calc {
  final List<Party> parties;
  final List<Item> items;
  final List<Txn> txns;
  final List<StockAdjustment> adjustments;

  Calc({required this.parties, required this.items, required this.txns, required this.adjustments});

  Item? item(String id) => items.where((i) => i.id == id).firstOrNull;
  Party? party(String? id) => id == null ? null : parties.where((p) => p.id == id).firstOrNull;
  String partyName(String? id) => party(id)?.name ?? 'Cash Sale';

  double itemStock(String itemId) {
    final it = item(itemId);
    if (it == null || it.type == 'service') return 0;
    double qty = it.openingStock;
    for (final t in txns) {
      final dir = kTxnTypes[t.type]?.stock ?? 0;
      if (dir == 0) continue;
      for (final l in t.lines) {
        if (l.itemId == itemId) qty += dir * l.qty;
      }
    }
    for (final a in adjustments) {
      if (a.itemId == itemId) qty += a.delta;
    }
    return round2(qty);
  }

  bool isLowStock(Item it) {
    if (it.type == 'service') return false;
    final s = itemStock(it.id);
    return s <= 0 || (it.minStock > 0 && s <= it.minStock);
  }

  List<Item> lowStockItems() => items.where(isLowStock).toList();

  double stockValue() {
    double v = 0;
    for (final it in items) {
      if (it.type == 'service') continue;
      final s = itemStock(it.id);
      v += (s > 0 ? s : 0) * (it.purchasePrice != 0 ? it.purchasePrice : it.salePrice);
    }
    return round2(v);
  }

  double _partyOpening(Party p) => p.openingType == 'pay' ? -p.openingBalance : p.openingBalance;

  double _txnDue(Txn t) {
    final cfg = kTxnTypes[t.type]!;
    if (cfg.balance == 0) return 0;
    if (t.type == 'PAYMENT_IN') return -t.total;
    if (t.type == 'PAYMENT_OUT') return t.total;
    return cfg.balance * (t.total - t.paid);
  }

  double partyBalance(String partyId) {
    final p = party(partyId);
    if (p == null) return 0;
    double bal = _partyOpening(p);
    for (final t in txns) {
      if (t.partyId == partyId) bal += _txnDue(t);
    }
    return round2(bal);
  }

  ({double receivable, double payable}) receivablePayable() {
    double r = 0, pay = 0;
    for (final p in parties) {
      final b = partyBalance(p.id);
      if (b > 0) {
        r += b;
      } else {
        pay += -b;
      }
    }
    return (receivable: round2(r), payable: round2(pay));
  }

  double _lineCost(TxnLine l) {
    if (l.cost != 0) return l.cost;
    return item(l.itemId)?.purchasePrice ?? 0;
  }

  double txnProfit(Txn t) {
    if (t.type != 'SALE' && t.type != 'SALE_RETURN') return 0;
    final revenue = t.subtotal - t.discount;
    double cost = 0;
    for (final l in t.lines) {
      cost += _lineCost(l) * l.qty;
    }
    final p = round2(revenue - cost);
    return t.type == 'SALE' ? p : -p;
  }

  String txnStatus(Txn t) {
    final cfg = kTxnTypes[t.type]!;
    if (t.type == 'ESTIMATE') return 'Open';
    if (cfg.balance == 0 || t.type == 'PAYMENT_IN' || t.type == 'PAYMENT_OUT') return 'Paid';
    final due = t.total - t.paid;
    if (due <= 0.005) return 'Paid';
    return t.paid > 0 ? 'Partial' : 'Unpaid';
  }
}

extension _FirstOrNull<E> on Iterable<E> {
  E? get firstOrNull {
    final it = iterator;
    return it.moveNext() ? it.current : null;
  }
}
