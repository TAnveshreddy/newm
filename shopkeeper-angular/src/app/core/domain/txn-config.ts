import { TxnType } from '../models';

/**
 * Per-transaction-type metadata — identical to the original app's TXN_TYPES.
 *   stock:   effect on inventory (+1 adds, -1 removes, 0 none)
 *   balance: effect on the party ledger (+1 receivable, -1 payable, 0 none)
 */
export interface TxnMeta {
  label: string;
  prefix: string;
  party: 'customer' | 'supplier';
  stock: -1 | 0 | 1;
  balance: -1 | 0 | 1;
}

export const TXN_TYPES: Record<TxnType, TxnMeta> = {
  SALE:            { label: 'Sale Invoice',   prefix: 'INV',  party: 'customer', stock: -1, balance: 1 },
  SALE_RETURN:     { label: 'Credit Note',    prefix: 'CRN',  party: 'customer', stock: 1,  balance: -1 },
  ESTIMATE:        { label: 'Estimate',       prefix: 'EST',  party: 'customer', stock: 0,  balance: 0 },
  PURCHASE:        { label: 'Purchase Bill',  prefix: 'PUR',  party: 'supplier', stock: 1,  balance: -1 },
  PURCHASE_RETURN: { label: 'Debit Note',     prefix: 'DBN',  party: 'supplier', stock: -1, balance: 1 },
  PAYMENT_IN:      { label: 'Payment In',     prefix: 'RCPT', party: 'customer', stock: 0,  balance: -1 },
  PAYMENT_OUT:     { label: 'Payment Out',    prefix: 'PAY',  party: 'supplier', stock: 0,  balance: 1 },
  EXPENSE:         { label: 'Expense',        prefix: 'EXP',  party: 'supplier', stock: 0,  balance: 0 },
};
