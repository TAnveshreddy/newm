// Data models for Vyapar Lite.

enum TxnType { sale, purchase, paymentIn, paymentOut, expense }

extension TxnTypeInfo on TxnType {
  String get label {
    switch (this) {
      case TxnType.sale:
        return 'Sale';
      case TxnType.purchase:
        return 'Purchase';
      case TxnType.paymentIn:
        return 'Payment In';
      case TxnType.paymentOut:
        return 'Payment Out';
      case TxnType.expense:
        return 'Expense';
    }
  }
}

/// Sentinel party id used for cash transactions (no party ledger involved).
const String cashPartyId = 'CASH';

String newId() => DateTime.now().microsecondsSinceEpoch.toString();

String money(num v) => '₹${v.toStringAsFixed(2)}';

String dateText(DateTime d) =>
    '${d.day.toString().padLeft(2, '0')}-${d.month.toString().padLeft(2, '0')}-${d.year}';

class Party {
  Party({
    required this.id,
    required this.name,
    this.phone = '',
    this.isSupplier = false,
    this.balance = 0,
  });

  final String id;
  String name;
  String phone;
  bool isSupplier;

  /// Positive: party owes us (receivable). Negative: we owe the party.
  double balance;

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'phone': phone,
        'isSupplier': isSupplier,
        'balance': balance,
      };

  factory Party.fromJson(Map<String, dynamic> j) => Party(
        id: j['id'] as String,
        name: j['name'] as String,
        phone: (j['phone'] ?? '') as String,
        isSupplier: (j['isSupplier'] ?? false) as bool,
        balance: ((j['balance'] ?? 0) as num).toDouble(),
      );
}

class Item {
  Item({
    required this.id,
    required this.name,
    this.unit = 'PCS',
    this.salePrice = 0,
    this.purchasePrice = 0,
    this.gstRate = 0,
    this.stock = 0,
    this.lowStockAt = 0,
  });

  final String id;
  String name;
  String unit;
  double salePrice;
  double purchasePrice;
  double gstRate;
  double stock;
  double lowStockAt;

  bool get isLowStock => lowStockAt > 0 && stock <= lowStockAt;

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'unit': unit,
        'salePrice': salePrice,
        'purchasePrice': purchasePrice,
        'gstRate': gstRate,
        'stock': stock,
        'lowStockAt': lowStockAt,
      };

  factory Item.fromJson(Map<String, dynamic> j) => Item(
        id: j['id'] as String,
        name: j['name'] as String,
        unit: (j['unit'] ?? 'PCS') as String,
        salePrice: ((j['salePrice'] ?? 0) as num).toDouble(),
        purchasePrice: ((j['purchasePrice'] ?? 0) as num).toDouble(),
        gstRate: ((j['gstRate'] ?? 0) as num).toDouble(),
        stock: ((j['stock'] ?? 0) as num).toDouble(),
        lowStockAt: ((j['lowStockAt'] ?? 0) as num).toDouble(),
      );
}

class LineItem {
  LineItem({
    required this.itemId,
    required this.name,
    required this.qty,
    required this.price,
    required this.gstRate,
  });

  final String itemId;
  final String name;
  final double qty;
  final double price;
  final double gstRate;

  double get amount => qty * price;
  double get tax => amount * gstRate / 100;
  double get total => amount + tax;

  Map<String, dynamic> toJson() => {
        'itemId': itemId,
        'name': name,
        'qty': qty,
        'price': price,
        'gstRate': gstRate,
      };

  factory LineItem.fromJson(Map<String, dynamic> j) => LineItem(
        itemId: j['itemId'] as String,
        name: j['name'] as String,
        qty: ((j['qty'] ?? 0) as num).toDouble(),
        price: ((j['price'] ?? 0) as num).toDouble(),
        gstRate: ((j['gstRate'] ?? 0) as num).toDouble(),
      );
}

class Txn {
  Txn({
    required this.id,
    required this.type,
    required this.partyId,
    required this.partyName,
    required this.date,
    this.lines = const [],
    this.total = 0,
    this.paid = 0,
    this.note = '',
  });

  final String id;
  final TxnType type;
  final String partyId; // cashPartyId for cash/no-party transactions
  final String partyName;
  final DateTime date;
  final List<LineItem> lines;
  final double total;
  final double paid;
  final String note;

  double get subtotal =>
      lines.fold(0, (sum, l) => sum + l.amount);
  double get tax => lines.fold(0, (sum, l) => sum + l.tax);
  double get due => total - paid;

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': type.name,
        'partyId': partyId,
        'partyName': partyName,
        'date': date.millisecondsSinceEpoch,
        'lines': lines.map((l) => l.toJson()).toList(),
        'total': total,
        'paid': paid,
        'note': note,
      };

  factory Txn.fromJson(Map<String, dynamic> j) => Txn(
        id: j['id'] as String,
        type: TxnType.values.byName(j['type'] as String),
        partyId: (j['partyId'] ?? cashPartyId) as String,
        partyName: (j['partyName'] ?? 'Cash') as String,
        date: DateTime.fromMillisecondsSinceEpoch(j['date'] as int),
        lines: ((j['lines'] ?? []) as List)
            .map((e) => LineItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        total: ((j['total'] ?? 0) as num).toDouble(),
        paid: ((j['paid'] ?? 0) as num).toDouble(),
        note: (j['note'] ?? '') as String,
      );
}
