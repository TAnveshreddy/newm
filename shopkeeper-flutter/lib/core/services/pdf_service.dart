import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';

import '../models/models.dart';
import '../util/money.dart';

/// Builds and prints/shares a GST invoice PDF for a transaction.
class PdfService {
  Future<void> printInvoice({
    required Txn txn,
    required BusinessSettings settings,
    required String partyName,
    required bool taxEnabled,
  }) async {
    final doc = pw.Document();
    final due = (txn.total - txn.paid).clamp(0, double.infinity).toDouble();

    doc.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        build: (context) => pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Row(
              mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
                  pw.Text(settings.businessName, style: pw.TextStyle(fontSize: 20, fontWeight: pw.FontWeight.bold)),
                  if (settings.address.isNotEmpty) pw.Text(settings.address, style: const pw.TextStyle(fontSize: 10)),
                  if (settings.gstin.isNotEmpty) pw.Text('GSTIN: ${settings.gstin}', style: const pw.TextStyle(fontSize: 10)),
                ]),
                pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.end, children: [
                  pw.Text('INVOICE', style: pw.TextStyle(fontSize: 16, fontWeight: pw.FontWeight.bold)),
                  pw.Text('#${txn.number}'),
                  pw.Text(txn.date, style: const pw.TextStyle(fontSize: 10)),
                ]),
              ],
            ),
            pw.Divider(),
            pw.Text('Bill To: $partyName', style: pw.TextStyle(fontWeight: pw.FontWeight.bold)),
            pw.SizedBox(height: 8),
            pw.TableHelper.fromTextArray(
              headers: ['#', 'Item', 'Qty', 'Rate', 'Taxable', if (taxEnabled) 'GST', 'Amount'],
              cellAlignment: pw.Alignment.centerLeft,
              headerDecoration: const pw.BoxDecoration(color: PdfColors.grey200),
              data: [
                for (var i = 0; i < txn.lines.length; i++)
                  _row(i + 1, txn.lines[i], taxEnabled),
              ],
            ),
            pw.SizedBox(height: 10),
            pw.Align(
              alignment: pw.Alignment.centerRight,
              child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.end, children: [
                pw.Text('Total: ${money(txn.total)}', style: pw.TextStyle(fontWeight: pw.FontWeight.bold)),
                pw.Text('Paid: ${money(txn.paid)}'),
                pw.Text('Balance Due: ${money(due)}'),
              ]),
            ),
          ],
        ),
      ),
    );

    await Printing.layoutPdf(onLayout: (format) async => doc.save());
  }

  List<String> _row(int n, TxnLine l, bool taxEnabled) {
    final taxable = l.qty * l.rate;
    final tax = taxEnabled ? taxable * l.taxRate / 100 : 0;
    return [
      '$n',
      l.name,
      '${l.qty} ${l.unit}',
      money(l.rate, symbol: false),
      money(taxable, symbol: false),
      if (taxEnabled) '${l.taxRate}%',
      money(taxable + tax, symbol: false),
    ];
  }
}
