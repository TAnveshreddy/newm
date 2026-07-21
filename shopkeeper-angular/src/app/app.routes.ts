import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { adminGuard } from './core/guards/admin.guard';
import { ShellComponent } from './shared/layout/shell.component';

/**
 * Top-level routing. Everything behind the shell is protected by `authGuard`
 * and lazy-loaded (code-splitting) so each feature ships as its own chunk and
 * is only fetched when first visited.
 */
export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login.component').then((m) => m.LoginComponent),
  },
  {
    path: '',
    component: ShellComponent,
    canActivate: [authGuard],
    canActivateChild: [authGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
      {
        path: 'dashboard',
        title: 'Dashboard · Shopkeeper',
        loadComponent: () =>
          import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      {
        path: 'inventory',
        title: 'Inventory · Shopkeeper',
        loadComponent: () =>
          import('./features/inventory/inventory.component').then((m) => m.InventoryComponent),
      },
      {
        path: 'billing',
        title: 'Billing · Shopkeeper',
        loadComponent: () =>
          import('./features/billing/billing.component').then((m) => m.BillingComponent),
      },
      {
        path: 'parties',
        title: 'Khata · Shopkeeper',
        loadComponent: () =>
          import('./features/parties/parties.component').then((m) => m.PartiesComponent),
      },
      {
        path: 'purchases',
        title: 'Purchases · Shopkeeper',
        data: { tx: { title: 'Purchases', subtitle: 'Purchase bills from suppliers', show: ['PURCHASE'], create: ['PURCHASE'] } },
        loadComponent: () => import('./features/transactions/transactions.component').then((m) => m.TransactionsComponent),
      },
      {
        path: 'estimates',
        title: 'Estimates · Shopkeeper',
        data: { tx: { title: 'Estimates', subtitle: 'Quotations for customers', show: ['ESTIMATE'], create: ['ESTIMATE'] } },
        loadComponent: () => import('./features/transactions/transactions.component').then((m) => m.TransactionsComponent),
      },
      {
        path: 'payments',
        title: 'Payments · Shopkeeper',
        data: { tx: { title: 'Payments', subtitle: 'Money received and paid out', show: ['PAYMENT_IN', 'PAYMENT_OUT'], create: ['PAYMENT_IN', 'PAYMENT_OUT'] } },
        loadComponent: () => import('./features/transactions/transactions.component').then((m) => m.TransactionsComponent),
      },
      {
        path: 'expenses',
        title: 'Expenses · Shopkeeper',
        data: { tx: { title: 'Expenses', subtitle: 'Business expenses', show: ['EXPENSE'], create: ['EXPENSE'] } },
        loadComponent: () => import('./features/transactions/transactions.component').then((m) => m.TransactionsComponent),
      },
      {
        path: 'returns',
        title: 'Returns · Shopkeeper',
        data: { tx: { title: 'Returns', subtitle: 'Sale & purchase returns', show: ['SALE_RETURN', 'PURCHASE_RETURN'], create: ['SALE_RETURN', 'PURCHASE_RETURN'] } },
        loadComponent: () => import('./features/transactions/transactions.component').then((m) => m.TransactionsComponent),
      },
      {
        path: 'reports',
        title: 'Reports · Shopkeeper',
        loadComponent: () =>
          import('./features/reports/reports.component').then((m) => m.ReportsComponent),
      },
      {
        path: 'settings',
        title: 'Settings · Shopkeeper',
        loadComponent: () =>
          import('./features/settings/settings.component').then((m) => m.SettingsComponent),
      },
      {
        path: 'admin',
        title: 'Admin · Shopkeeper',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/admin/admin.component').then((m) => m.AdminComponent),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
