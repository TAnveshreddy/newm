import { inject } from '@angular/core';
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

import { ToastService } from '../services/toast.service';

/**
 * Centralised HTTP error handling for any REST calls the app makes (Firebase
 * traffic goes through the SDK, not HttpClient). Surfaces a friendly toast and
 * rethrows so callers can still react. Registered in app.config via
 * withInterceptors([...]).
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const toast = inject(ToastService);
  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      const msg =
        err.status === 0
          ? 'Network error — check your connection.'
          : err.error?.message || err.message || `Request failed (${err.status}).`;
      toast.error(msg);
      return throwError(() => err);
    }),
  );
};
