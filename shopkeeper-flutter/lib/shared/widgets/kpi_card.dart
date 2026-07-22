import 'package:flutter/material.dart';

/// Compact KPI tile: coloured icon chip, label, value and optional sub-line.
class KpiCard extends StatelessWidget {
  final IconData icon;
  final Color tone;
  final String label;
  final String value;
  final Widget? sub;
  final VoidCallback? onTap;

  const KpiCard({
    super.key,
    required this.icon,
    required this.tone,
    required this.label,
    required this.value,
    this.sub,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(children: [
                Container(
                  width: 42, height: 42,
                  decoration: BoxDecoration(color: tone.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(12)),
                  child: Icon(icon, color: tone, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(label, style: TextStyle(fontSize: 12, color: Colors.grey.shade600), overflow: TextOverflow.ellipsis),
                      Text(value, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w800), overflow: TextOverflow.ellipsis),
                    ],
                  ),
                ),
              ]),
              if (sub != null) Padding(padding: const EdgeInsets.only(top: 8), child: sub!),
            ],
          ),
        ),
      ),
    );
  }
}
