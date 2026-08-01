import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, withComponentInputBinding, withInMemoryScrolling } from '@angular/router';
import { provideHttpClient, withInterceptors, withFetch } from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';

import { initializeApp, provideFirebaseApp, getApp } from '@angular/fire/app';
import { provideAuth, getAuth } from '@angular/fire/auth';
import {
  provideFirestore,
  initializeFirestore,
  persistentLocalCache,
  persistentMultipleTabManager,
} from '@angular/fire/firestore';

import { routes } from './app.routes';
import { environment } from '../environments/environment';
import { errorInterceptor } from './core/interceptors/error.interceptor';

/**
 * Application-wide providers. Standalone bootstrap (no root NgModule) — the
 * modern Angular composition model. Firebase is provided once here and injected
 * via DI everywhere; Firestore uses an offline persistent cache so the app keeps
 * working without a connection and syncs automatically on reconnect.
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(
      routes,
      withComponentInputBinding(),
      withInMemoryScrolling({ scrollPositionRestoration: 'top' }),
    ),
    provideHttpClient(withFetch(), withInterceptors([errorInterceptor])),
    provideAnimations(),

    provideFirebaseApp(() => initializeApp(environment.firebase)),
    provideAuth(() => getAuth()),
    provideFirestore(() =>
      initializeFirestore(getApp(), {
        localCache: persistentLocalCache({
          tabManager: persistentMultipleTabManager(),
        }),
        // Firestore rejects any field whose value is `undefined` (e.g. an item's
        // optional hsn/brand/description, or an unpaid party on a cash sale).
        // Ignore them instead of throwing so saving a bill never fails; the
        // field is simply omitted from the stored document.
        ignoreUndefinedProperties: true,
      }),
    ),
  ],
};
