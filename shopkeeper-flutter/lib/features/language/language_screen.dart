import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/i18n/locale_provider.dart';
import '../../core/i18n/translations.dart';
import '../../core/theme/app_theme.dart';

/// First-run language chooser. Live-previews as the user selects.
class LanguageScreen extends ConsumerStatefulWidget {
  const LanguageScreen({super.key});
  @override
  ConsumerState<LanguageScreen> createState() => _LanguageScreenState();
}

class _LanguageScreenState extends ConsumerState<LanguageScreen> {
  String _sel = 'en';

  @override
  Widget build(BuildContext context) {
    final lang = _sel;
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 56, height: 56,
                      decoration: BoxDecoration(color: AppTheme.primary, borderRadius: BorderRadius.circular(16)),
                      alignment: Alignment.center,
                      child: const Text('🌐', style: TextStyle(fontSize: 28)),
                    ),
                    const SizedBox(height: 12),
                    Text(translate(lang, 'lang.choose'),
                        style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800), textAlign: TextAlign.center),
                    const SizedBox(height: 6),
                    Text(translate(lang, 'lang.chooseSub'),
                        style: TextStyle(color: Colors.grey.shade600, fontSize: 13), textAlign: TextAlign.center),
                    const SizedBox(height: 16),
                    GridView.count(
                      crossAxisCount: 2,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      childAspectRatio: 2.6,
                      mainAxisSpacing: 10,
                      crossAxisSpacing: 10,
                      children: kLanguages.map((l) {
                        final active = _sel == l.code;
                        return InkWell(
                          onTap: () => setState(() => _sel = l.code),
                          borderRadius: BorderRadius.circular(12),
                          child: Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: active ? AppTheme.primary : Colors.grey.shade300, width: active ? 2 : 1),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(l.label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                                Text(l.english, style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
                              ],
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: () {
                        ref.read(langProvider.notifier).setLang(_sel);
                        context.go('/');
                      },
                      style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(48)),
                      child: Text(translate(lang, 'lang.continue')),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
