/**
 * Domain models — mirror the EXISTING Firestore schema 1:1 so this Angular
 * client reads/writes the same documents as the original app with no migration.
 *
 *   users/{uid}                      -> UserProfile
 *   userData/{uid}/parties/{id}      -> Party
 *   userData/{uid}/items/{id}        -> Item
 *   userData/{uid}/txns/{id}         -> Transaction
 *   userData/{uid}/adjustments/{id}  -> StockAdjustment
 *   userData/{uid}/meta/settings     -> BusinessSettings
 *   userData/{uid}/meta/counters     -> Counters
 */
import type { Timestamp } from '@angular/fire/firestore';

export type Role = 'user' | 'admin';
export type Plan = 'free' | 'basic' | 'premium' | 'enterprise';

export const PLANS: Plan[] = ['free', 'basic', 'premium', 'enterprise'];
export const ROLES: Role[] = ['user', 'admin'];

export interface UserProfile {
  uid: string;
  phone?: string;
  email?: string;
  displayName?: string;
  provider?: string;
  role: Role;
  plan: Plan;
  active: boolean;
  createdAt?: Timestamp | null;
  activatedAt?: Timestamp | null;
  lastLogin?: Timestamp | null;
  planUpdatedAt?: Timestamp | null;
}

export type PartyType = 'customer' | 'supplier';
export type OpeningType = 'receive' | 'pay';

export interface Party {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  gstin?: string;
  address?: string;
  type: PartyType;
  openingBalance?: number;
  openingType?: OpeningType;
  createdAt?: number;
}

export type ItemType = 'product' | 'service';

export interface Item {
  id: string;
  name: string;
  hsn?: string;
  barcode?: string;
  category?: string;
  brand?: string;
  unit?: string;
  description?: string;
  salePrice?: number;
  purchasePrice?: number;
  taxRate?: number;
  openingStock?: number;
  minStock?: number;
  type: ItemType;
  createdAt?: number;
}

export type TxnType =
  | 'SALE' | 'SALE_RETURN' | 'ESTIMATE'
  | 'PURCHASE' | 'PURCHASE_RETURN'
  | 'PAYMENT_IN' | 'PAYMENT_OUT' | 'EXPENSE';

export interface TxnLine {
  itemId: string;
  name: string;
  hsn?: string;
  unit?: string;
  qty: number;
  rate: number;
  disc?: number;
  taxRate?: number;
  /** True when the GST % was typed manually rather than picked from a slab. */
  taxManual?: boolean;
  brand?: string;
  description?: string;
  cost?: number;
}

export interface Transaction {
  id: string;
  type: TxnType;
  number: string;
  date: string;              // ISO yyyy-mm-dd
  partyId?: string | null;
  lines?: TxnLine[];
  subtotal?: number;
  discount?: number;
  discountPct?: number;
  total: number;
  paid: number;
  mode?: string;
  notes?: string;
  category?: string;
  referredBy?: string;
  convertedTo?: string | null;
  createdAt?: number;
}

export interface StockAdjustment {
  id: string;
  itemId: string;
  delta: number;
  reason?: string;
  date: string;
  createdAt?: number;
}

export interface BusinessSettings {
  businessName: string;
  tagline?: string;
  address?: string;
  phone?: string;
  email?: string;
  gstin?: string;
  taxEnabled: boolean;
  theme: 'light' | 'dark';
  terms?: string;
  upiId?: string;
  signatureName?: string;
}

export interface Counters {
  SALE: number; SALE_RETURN: number; ESTIMATE: number;
  PURCHASE: number; PURCHASE_RETURN: number;
  PAYMENT_IN: number; PAYMENT_OUT: number; EXPENSE: number;
}

export const DEFAULT_SETTINGS: BusinessSettings = {
  businessName: 'My Business',
  tagline: '',
  address: '',
  phone: '',
  email: '',
  gstin: '',
  taxEnabled: true,
  theme: 'light',
  terms: 'Thanks for doing business with us!',
  upiId: '',
  signatureName: '',
};

export const DEFAULT_COUNTERS: Counters = {
  SALE: 1, SALE_RETURN: 1, ESTIMATE: 1, PURCHASE: 1,
  PURCHASE_RETURN: 1, PAYMENT_IN: 1, PAYMENT_OUT: 1, EXPENSE: 1,
};
