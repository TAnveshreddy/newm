import 'package:flutter/material.dart';

/// Blue-primary Material 3 theme (light + dark), matching the web apps.
class AppTheme {
  static const primary = Color(0xFF2563EB);
  static const sidebar = Color(0xFF0F1C3D);

  static ThemeData light = _base(Brightness.light);
  static ThemeData dark = _base(Brightness.dark);

  static ThemeData _base(Brightness b) {
    final scheme = ColorScheme.fromSeed(seedColor: primary, brightness: b);
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: b == Brightness.light ? const Color(0xFFF4F6FB) : const Color(0xFF0C1214),
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        color: b == Brightness.light ? Colors.white : const Color(0xFF161F22),
      ),
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
        isDense: true,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
        ),
      ),
      appBarTheme: const AppBarTheme(centerTitle: false),
    );
  }
}

class Tones {
  static const blue = Color(0xFF2563EB);
  static const green = Color(0xFF0A9D54);
  static const indigo = Color(0xFF5B57D6);
  static const amber = Color(0xFFD98A10);
  static const red = Color(0xFFE0483F);
}
