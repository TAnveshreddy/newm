import 'dart:math';

/// Generate a unique 12-digit numeric barcode not present in [existing].
String generateBarcode(Iterable<String> existing) {
  final used = existing.toSet();
  final rnd = Random();
  String code;
  do {
    code = (200000000000 + (rnd.nextDouble() * 799999999999)).floor().toString();
  } while (used.contains(code));
  return code;
}
