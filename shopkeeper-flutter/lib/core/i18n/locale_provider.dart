import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'translations.dart';

/// Holds the chosen language code (null until the user picks one on first run)
/// and persists it. Exposed via [langProvider] (overridden in main with real
/// SharedPreferences).
class LangController extends StateNotifier<String?> {
  final SharedPreferences prefs;
  LangController(this.prefs) : super(prefs.getString('lang'));

  bool get chosen => state != null;

  void setLang(String code) {
    state = code;
    prefs.setString('lang', code);
  }
}

final langProvider = StateNotifierProvider<LangController, String?>((ref) {
  throw UnimplementedError('langProvider must be overridden in main()');
});

/// Convenience translation lookup for widgets: `ref.tr('nav.dashboard')`.
extension L10n on WidgetRef {
  String tr(String key) => translate(watch(langProvider) ?? 'en', key);
}
