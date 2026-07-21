import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { toSignal } from '@angular/core/rxjs-interop';

import { AdminService } from '../../core/services/admin.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { UserProfile, Role, Plan, ROLES, PLANS } from '../../core/models';

@Component({
  selector: 'app-admin',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule],
  template: `
    <div class="page-head"><div><h2>Admin — Users</h2><div class="sub">Manage accounts, roles and subscriptions</div></div></div>

    <div class="card" style="margin-bottom:14px">
      <div class="head-actions" style="gap:14px;flex-wrap:wrap;align-items:center">
        <span class="badge info">Total: {{ users().length }}</span>
        <span class="badge ok">Active: {{ activeCount() }}</span>
        <span class="badge bad">Inactive: {{ users().length - activeCount() }}</span>
        <span class="badge warn">Admins: {{ adminCount() }}</span>
        <input class="search" style="flex:1;min-width:200px" placeholder="Search name / phone / email / plan" [(ngModel)]="queryText" />
      </div>
    </div>

    <div class="card">
      <div class="table-wrap"><table>
        <thead><tr><th>User</th><th>Login</th><th>Role</th><th>Plan</th><th>Status</th><th>Registered</th><th>Activated</th><th>Last login</th><th class="r">Actions</th></tr></thead>
        <tbody>
          @for (u of filtered(); track u.uid) {
            <tr>
              <td><strong>{{ u.displayName || (u.phone ? '+91 ' + u.phone : u.email) }}</strong>
                @if (u.uid === myUid()) { <span class="badge info">you</span> }
                <div class="sub">{{ provider(u) }}</div></td>
              <td>{{ u.phone ? '+91 ' + u.phone : '' }}<br class="soft" />{{ u.email }}</td>
              <td><select [value]="u.role" (change)="setRole(u, $any($event.target).value)" [disabled]="u.uid === myUid()">
                @for (r of roles; track r) { <option [value]="r">{{ r }}</option> }</select></td>
              <td><select [value]="u.plan" (change)="setPlan(u, $any($event.target).value)">
                @for (p of plans; track p) { <option [value]="p">{{ p }}</option> }</select></td>
              <td>@if (u.active !== false) { <span class="badge ok">Active</span> } @else { <span class="badge bad">Inactive</span> }</td>
              <td class="sub">{{ ts(u.createdAt) }}</td>
              <td class="sub">{{ ts(u.activatedAt) }}</td>
              <td class="sub">{{ ts(u.lastLogin) }}</td>
              <td class="r">
                @if (u.uid === myUid()) { <span class="sub">You</span> }
                @else {
                  @if (u.active !== false) { <button class="btn tiny ghost" (click)="setActive(u, false)">Deactivate</button> }
                  @else { <button class="btn tiny primary" (click)="setActive(u, true)">Activate</button> }
                  <button class="btn tiny danger" (click)="remove(u)">Delete</button>
                }
              </td>
            </tr>
          } @empty { <tr><td colspan="9" class="empty">No users found.</td></tr> }
        </tbody>
      </table></div>
    </div>
  `,
})
export class AdminComponent {
  private readonly admin = inject(AdminService);
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);

  readonly roles = ROLES;
  readonly plans = PLANS;

  readonly users = toSignal(this.admin.users$(), { initialValue: [] as UserProfile[] });
  readonly queryText = signal('');
  readonly myUid = computed(() => this.auth.user()?.uid ?? '');

  readonly activeCount = computed(() => this.users().filter((u) => u.active !== false).length);
  readonly adminCount = computed(() => this.users().filter((u) => u.role === 'admin').length);

  readonly filtered = computed(() => {
    const q = this.queryText().trim().toLowerCase();
    if (!q) return this.users();
    return this.users().filter((u) =>
      [u.displayName, u.phone, u.email, u.plan, u.role].some((v) => (v ?? '').toString().toLowerCase().includes(q)),
    );
  });

  provider(u: UserProfile): string {
    return (u.provider ?? '').includes('google') ? 'Google' : (u.provider ?? '').includes('phone') ? 'Mobile OTP' : u.email ? 'Google' : 'Mobile OTP';
  }

  async setActive(u: UserProfile, active: boolean): Promise<void> {
    if (u.uid === this.myUid()) return;
    await this.admin.setActive(u.uid, active);
    this.toast.success(active ? 'Account activated' : 'Account deactivated');
  }
  async setRole(u: UserProfile, role: Role): Promise<void> {
    if (u.uid === this.myUid()) return;
    await this.admin.setRole(u.uid, role);
    this.toast.success('Role set to ' + role);
  }
  async setPlan(u: UserProfile, plan: Plan): Promise<void> {
    await this.admin.setPlan(u.uid, plan);
    this.toast.success('Plan changed to ' + plan);
  }
  async remove(u: UserProfile): Promise<void> {
    if (u.uid === this.myUid()) return;
    if (!confirm(`Delete ${u.displayName || u.phone || u.email}? This removes their profile and all their data.`)) return;
    try {
      await this.admin.deleteUser(u.uid);
      this.toast.success('User deleted');
    } catch (e) {
      this.toast.error('Delete failed: ' + (e as Error).message);
    }
  }

  ts(v: unknown): string {
    if (!v) return '—';
    const anyV = v as { toDate?: () => Date; seconds?: number };
    let d: Date;
    if (typeof anyV.toDate === 'function') d = anyV.toDate();
    else if (anyV.seconds != null) d = new Date(anyV.seconds * 1000);
    else d = new Date(v as string | number);
    if (isNaN(d.getTime())) return '—';
    return `${d.getDate()}/${d.getMonth() + 1}/${d.getFullYear()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  }
}
