import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { ToastService } from '../../core/services/toast.service';

/** Global toast host — renders the ToastService signal. */
@Component({
  selector: 'app-toast',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="toast-stack">
      @for (t of toasts.toasts(); track t.id) {
        <div class="toast" [class]="t.kind" (click)="toasts.dismiss(t.id)">{{ t.message }}</div>
      }
    </div>
  `,
  styles: [`
    .toast-stack { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%);
      display: flex; flex-direction: column; gap: 8px; z-index: 1000; }
    .toast { background: #16232a; color: #fff; padding: 10px 18px; border-radius: 10px;
      font-size: 13.5px; box-shadow: 0 8px 24px rgba(0,0,0,.25); cursor: pointer; max-width: 90vw; }
    .toast.success { background: #0a9d54; }
    .toast.error { background: #d64545; }
  `],
})
export class ToastComponent {
  readonly toasts = inject(ToastService);
}
