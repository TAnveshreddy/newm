import { Configuration, PublicClientApplication } from '@azure/msal-browser';

/**
 * MSAL configuration (Phase 3). Only public SPA values are used — tenant ID and
 * client ID. There is NO client secret in the browser (NFR §3).
 *
 * The backend API scope is requested so the SPA receives an access token whose
 * audience is the backend API; that token is what protected endpoints validate.
 */

const tenantId = import.meta.env.VITE_ENTRA_TENANT_ID ?? '';
const clientId = import.meta.env.VITE_ENTRA_CLIENT_ID ?? '';

export const apiScope = import.meta.env.VITE_ENTRA_API_SCOPE ?? '';

export const mockAuth = (import.meta.env.VITE_MOCK_AUTH ?? 'false') === 'true';

export const msalConfig: Configuration = {
  auth: {
    clientId,
    authority: tenantId ? `https://login.microsoftonline.com/${tenantId}` : undefined,
    redirectUri: import.meta.env.VITE_ENTRA_REDIRECT_URI || window.location.origin,
    postLogoutRedirectUri: window.location.origin,
  },
  cache: {
    // Store tokens in memory only; never in localStorage (NFR §11).
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
};

/** Scopes requested at login / token acquisition. */
export const loginRequest = {
  scopes: apiScope ? [apiScope] : ['openid', 'profile'],
};

/** Shared MSAL instance (only created when not in mock-auth mode). */
export const msalInstance = mockAuth ? undefined : new PublicClientApplication(msalConfig);
