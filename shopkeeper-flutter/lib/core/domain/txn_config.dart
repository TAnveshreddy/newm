// Per-transaction-type metadata — identical to the web apps' TXN_TYPES.
class TxnMeta {
  final String label;
  final String prefix;
  final String party; // 'customer' | 'supplier'
  final int stock; // -1 removes, +1 adds, 0 none
  final int balance; // +1 receivable, -1 payable, 0 none
  const TxnMeta(this.label, this.prefix, this.party, this.stock, this.balance);
}

const Map<String, TxnMeta> kTxnTypes = {
  'SALE': TxnMeta('Sale Invoice', 'INV', 'customer', -1, 1),
  'SALE_RETURN': TxnMeta('Credit Note', 'CRN', 'customer', 1, -1),
  'ESTIMATE': TxnMeta('Estimate', 'EST', 'customer', 0, 0),
  'PURCHASE': TxnMeta('Purchase Bill', 'PUR', 'supplier', 1, -1),
  'PURCHASE_RETURN': TxnMeta('Debit Note', 'DBN', 'supplier', -1, 1),
  'PAYMENT_IN': TxnMeta('Payment In', 'RCPT', 'customer', 0, -1),
  'PAYMENT_OUT': TxnMeta('Payment Out', 'PAY', 'supplier', 0, 1),
  'EXPENSE': TxnMeta('Expense', 'EXP', 'supplier', 0, 0),
};
