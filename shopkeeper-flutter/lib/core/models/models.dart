// Domain models — mirror the EXISTING Firestore schema 1:1 so this mobile app
// reads/writes the same documents as the web apps (no migration).
import 'package:cloud_firestore/cloud_firestore.dart';

double _d(dynamic v) {
  if (v is num) return v.toDouble();
  return double.tryParse('${v ?? ''}') ?? 0;
}

int _i(dynamic v) {
  if (v is num) return v.toInt();
  return int.tryParse('${v ?? ''}') ?? 0;
}

const List<String> kPlans = ['free', 'basic', 'premium', 'enterprise'];
const List<String> kRoles = ['user', 'admin'];

class UserProfile {
  final String uid;
  final String phone;
  final String email;
  final String displayName;
  final String provider;
  final String role;
  final String plan;
  final bool active;
  final Timestamp? createdAt;
  final Timestamp? activatedAt;
  final Timestamp? lastLogin;

  UserProfile({
    required this.uid,
    this.phone = '',
    this.email = '',
    this.displayName = '',
    this.provider = '',
    this.role = 'user',
    this.plan = 'free',
    this.active = true,
    this.createdAt,
    this.activatedAt,
    this.lastLogin,
  });

  factory UserProfile.fromMap(String id, Map<String, dynamic> m) => UserProfile(
        uid: (m['uid'] ?? id).toString(),
        phone: (m['phone'] ?? '').toString(),
        email: (m['email'] ?? '').toString(),
        displayName: (m['displayName'] ?? '').toString(),
        provider: (m['provider'] ?? '').toString(),
        role: (m['role'] ?? 'user').toString(),
        plan: (m['plan'] ?? 'free').toString(),
        active: m['active'] != false,
        createdAt: m['createdAt'] is Timestamp ? m['createdAt'] as Timestamp : null,
        activatedAt: m['activatedAt'] is Timestamp ? m['activatedAt'] as Timestamp : null,
        lastLogin: m['lastLogin'] is Timestamp ? m['lastLogin'] as Timestamp : null,
      );
}

class Party {
  final String id;
  final String name;
  final String phone;
  final String email;
  final String gstin;
  final String address;
  final String type; // 'customer' | 'supplier'
  final double openingBalance;
  final String openingType; // 'receive' | 'pay'
  final int? createdAt;

  Party({
    required this.id,
    required this.name,
    this.phone = '',
    this.email = '',
    this.gstin = '',
    this.address = '',
    this.type = 'customer',
    this.openingBalance = 0,
    this.openingType = 'receive',
    this.createdAt,
  });

  factory Party.fromMap(String id, Map<String, dynamic> m) => Party(
        id: (m['id'] ?? id).toString(),
        name: (m['name'] ?? '').toString(),
        phone: (m['phone'] ?? '').toString(),
        email: (m['email'] ?? '').toString(),
        gstin: (m['gstin'] ?? '').toString(),
        address: (m['address'] ?? '').toString(),
        type: (m['type'] ?? 'customer').toString(),
        openingBalance: _d(m['openingBalance']),
        openingType: (m['openingType'] ?? 'receive').toString(),
        createdAt: m['createdAt'] is num ? _i(m['createdAt']) : null,
      );

  Map<String, dynamic> toMap() => {
        'id': id, 'name': name, 'phone': phone, 'email': email, 'gstin': gstin,
        'address': address, 'type': type, 'openingBalance': openingBalance,
        'openingType': openingType, 'createdAt': createdAt,
      };
}

class Item {
  final String id;
  final String name;
  final String hsn;
  final String barcode;
  final String category;
  final String brand;
  final String unit;
  final String description;
  final double salePrice;
  final double purchasePrice;
  final double taxRate;
  final double openingStock;
  final double minStock;
  final String type; // 'product' | 'service'
  final int? createdAt;

  Item({
    required this.id,
    required this.name,
    this.hsn = '',
    this.barcode = '',
    this.category = '',
    this.brand = '',
    this.unit = 'PCS',
    this.description = '',
    this.salePrice = 0,
    this.purchasePrice = 0,
    this.taxRate = 0,
    this.openingStock = 0,
    this.minStock = 0,
    this.type = 'product',
    this.createdAt,
  });

  factory Item.fromMap(String id, Map<String, dynamic> m) => Item(
        id: (m['id'] ?? id).toString(),
        name: (m['name'] ?? '').toString(),
        hsn: (m['hsn'] ?? '').toString(),
        barcode: (m['barcode'] ?? '').toString(),
        category: (m['category'] ?? '').toString(),
        brand: (m['brand'] ?? '').toString(),
        unit: (m['unit'] ?? 'PCS').toString(),
        description: (m['description'] ?? '').toString(),
        salePrice: _d(m['salePrice']),
        purchasePrice: _d(m['purchasePrice']),
        taxRate: _d(m['taxRate']),
        openingStock: _d(m['openingStock']),
        minStock: _d(m['minStock']),
        type: (m['type'] ?? 'product').toString(),
        createdAt: m['createdAt'] is num ? _i(m['createdAt']) : null,
      );

  Map<String, dynamic> toMap() => {
        'id': id, 'name': name, 'hsn': hsn, 'barcode': barcode, 'category': category,
        'brand': brand, 'unit': unit, 'description': description, 'salePrice': salePrice,
        'purchasePrice': purchasePrice, 'taxRate': taxRate, 'openingStock': openingStock,
        'minStock': minStock, 'type': type, 'createdAt': createdAt,
      };

  Item copyWith({String? barcode}) => Item(
        id: id, name: name, hsn: hsn, barcode: barcode ?? this.barcode,
        category: category, brand: brand, unit: unit, description: description,
        salePrice: salePrice, purchasePrice: purchasePrice, taxRate: taxRate,
        openingStock: openingStock, minStock: minStock, type: type, createdAt: createdAt,
      );
}

class TxnLine {
  final String itemId;
  final String name;
  final String hsn;
  final String unit;
  final double qty;
  final double rate;
  final double taxRate;
  final bool taxManual; // GST typed manually vs. picked from a slab
  final String brand;
  final String description;
  final double cost;

  TxnLine({
    required this.itemId,
    required this.name,
    this.hsn = '',
    this.unit = '',
    this.qty = 1,
    this.rate = 0,
    this.taxRate = 0,
    this.taxManual = false,
    this.brand = '',
    this.description = '',
    this.cost = 0,
  });

  factory TxnLine.fromMap(Map<String, dynamic> m) => TxnLine(
        itemId: (m['itemId'] ?? '').toString(),
        name: (m['name'] ?? '').toString(),
        hsn: (m['hsn'] ?? '').toString(),
        unit: (m['unit'] ?? '').toString(),
        qty: _d(m['qty']),
        rate: _d(m['rate']),
        taxRate: _d(m['taxRate']),
        taxManual: m['taxManual'] == true,
        brand: (m['brand'] ?? '').toString(),
        description: (m['description'] ?? '').toString(),
        cost: _d(m['cost']),
      );

  Map<String, dynamic> toMap() => {
        'itemId': itemId, 'name': name, 'hsn': hsn, 'unit': unit,
        'qty': qty, 'rate': rate, 'taxRate': taxRate, 'taxManual': taxManual,
        'brand': brand, 'description': description, 'cost': cost,
      };

  TxnLine copyWith({
    double? qty, double? rate, double? taxRate, bool? taxManual,
    String? brand, String? description,
  }) =>
      TxnLine(
        itemId: itemId, name: name, hsn: hsn, unit: unit,
        qty: qty ?? this.qty, rate: rate ?? this.rate,
        taxRate: taxRate ?? this.taxRate, taxManual: taxManual ?? this.taxManual,
        brand: brand ?? this.brand, description: description ?? this.description,
        cost: cost,
      );
}

class Txn {
  final String id;
  final String type;
  final String number;
  final String date; // yyyy-mm-dd
  final String? partyId;
  final List<TxnLine> lines;
  final double subtotal;
  final double discount;
  final double total;
  final double paid;
  final String mode;
  final String category;
  final String notes;
  final int? createdAt;

  Txn({
    required this.id,
    required this.type,
    required this.number,
    required this.date,
    this.partyId,
    this.lines = const [],
    this.subtotal = 0,
    this.discount = 0,
    this.total = 0,
    this.paid = 0,
    this.mode = 'Cash',
    this.category = '',
    this.notes = '',
    this.createdAt,
  });

  factory Txn.fromMap(String id, Map<String, dynamic> m) => Txn(
        id: (m['id'] ?? id).toString(),
        type: (m['type'] ?? 'SALE').toString(),
        number: (m['number'] ?? '').toString(),
        date: (m['date'] ?? '').toString(),
        partyId: m['partyId']?.toString(),
        lines: (m['lines'] as List<dynamic>? ?? [])
            .map((e) => TxnLine.fromMap(Map<String, dynamic>.from(e as Map)))
            .toList(),
        subtotal: _d(m['subtotal']),
        discount: _d(m['discount']),
        total: _d(m['total']),
        paid: _d(m['paid']),
        mode: (m['mode'] ?? 'Cash').toString(),
        category: (m['category'] ?? '').toString(),
        notes: (m['notes'] ?? '').toString(),
        createdAt: m['createdAt'] is num ? _i(m['createdAt']) : null,
      );

  Map<String, dynamic> toMap() => {
        'id': id, 'type': type, 'number': number, 'date': date, 'partyId': partyId,
        'lines': lines.map((l) => l.toMap()).toList(), 'subtotal': subtotal,
        'discount': discount, 'total': total, 'paid': paid, 'mode': mode,
        'category': category, 'notes': notes, 'createdAt': createdAt,
      };
}

class StockAdjustment {
  final String id;
  final String itemId;
  final double delta;
  StockAdjustment({required this.id, required this.itemId, this.delta = 0});
  factory StockAdjustment.fromMap(String id, Map<String, dynamic> m) =>
      StockAdjustment(id: (m['id'] ?? id).toString(), itemId: (m['itemId'] ?? '').toString(), delta: _d(m['delta']));
}

class BusinessSettings {
  final String businessName;
  final String address;
  final String phone;
  final String email;
  final String gstin;
  final String upiId;
  final bool taxEnabled;

  BusinessSettings({
    this.businessName = 'My Business',
    this.address = '',
    this.phone = '',
    this.email = '',
    this.gstin = '',
    this.upiId = '',
    this.taxEnabled = true,
  });

  factory BusinessSettings.fromMap(Map<String, dynamic> m) => BusinessSettings(
        businessName: (m['businessName'] ?? 'My Business').toString(),
        address: (m['address'] ?? '').toString(),
        phone: (m['phone'] ?? '').toString(),
        email: (m['email'] ?? '').toString(),
        gstin: (m['gstin'] ?? '').toString(),
        upiId: (m['upiId'] ?? '').toString(),
        taxEnabled: m['taxEnabled'] != false,
      );

  Map<String, dynamic> toMap() => {
        'businessName': businessName, 'address': address, 'phone': phone,
        'email': email, 'gstin': gstin, 'upiId': upiId, 'taxEnabled': taxEnabled,
      };

  BusinessSettings copyWith({
    String? businessName, String? address, String? phone,
    String? email, String? gstin, String? upiId, bool? taxEnabled,
  }) =>
      BusinessSettings(
        businessName: businessName ?? this.businessName,
        address: address ?? this.address,
        phone: phone ?? this.phone,
        email: email ?? this.email,
        gstin: gstin ?? this.gstin,
        upiId: upiId ?? this.upiId,
        taxEnabled: taxEnabled ?? this.taxEnabled,
      );
}
