import 'package:intl/intl.dart';

final _inr = NumberFormat.currency(locale: 'en_IN', symbol: '₹ ', decimalDigits: 2);
final _plain = NumberFormat('#,##0.##', 'en_IN');

/// Format as Indian-rupee currency (₹, Indian grouping).
String money(num? v, {bool symbol = true}) {
  final n = (v ?? 0).toDouble();
  return symbol ? _inr.format(n) : _plain.format(n);
}

String qty(num? v) => _plain.format((v ?? 0).toDouble());
