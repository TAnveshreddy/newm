// Small pure helpers shared across the app.

double toNum(dynamic v) {
  if (v is num) return v.toDouble();
  return double.tryParse('${v ?? ''}') ?? 0;
}

double round2(double v) => (v * 100).roundToDouble() / 100;

String todayIso([DateTime? d]) {
  d ??= DateTime.now();
  return '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';
}

String addDays(String iso, int days) {
  final d = DateTime.parse('${iso}T00:00:00').add(Duration(days: days));
  return todayIso(d);
}

String makeId() {
  final now = DateTime.now().microsecondsSinceEpoch.toRadixString(36);
  final rnd = (DateTime.now().microsecond * 7919).toRadixString(36);
  return '$now$rnd';
}
