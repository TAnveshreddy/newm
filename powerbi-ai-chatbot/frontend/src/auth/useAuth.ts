import { useCallback } from 'react';
import { useMsal, useIsAuthenticated } from '@azure/msal-react';
import { InteractionRequiredAuthError } from '@azure/msal-browser';
import { loginRequest, mockAuth } from './authConfig';
import { TokenProvider } from '../services/api';

export interface AuthState {
  isAuthenticated: boolean;
  username?: string;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  getToken: TokenProvider;
}

const MOCK_TOKEN = 'mock:' + JSON.stringify({ userId: 'dev-user', username: 'dev-user@example.com', roles: [] });

/** Mock auth: static bearer token, no MSAL context required. */
function useMockAuth(): AuthState {
  const getToken = useCallback<TokenProvider>(async () => MOCK_TOKEN, []);
  const noop = useCallback(async () => {}, []);
  return {
    isAuthenticated: true,
    username: 'dev-user@example.com',
    login: noop,
    logout: noop,
    getToken,
  };
}

/** MSAL auth: silent token acquisition with an interactive fallback. */
function useMsalAuth(): AuthState {
  const { instance, accounts } = useMsal();
  const msalAuthenticated = useIsAuthenticated();

  const getToken = useCallback<TokenProvider>(async () => {
    const account = accounts[0];
    if (!account) throw new Error('Not signed in.');
    try {
      const result = await instance.acquireTokenSilent({ ...loginRequest, account });
      return result.accessToken;
    } catch (err) {
      if (err instanceof InteractionRequiredAuthError) {
        const result = await instance.acquireTokenPopup(loginRequest);
        return result.accessToken;
      }
      throw err;
    }
  }, [instance, accounts]);

  const login = useCallback(async () => {
    await instance.loginPopup(loginRequest);
  }, [instance]);

  const logout = useCallback(async () => {
    await instance.logoutPopup();
  }, [instance]);

  return {
    isAuthenticated: msalAuthenticated,
    username: accounts[0]?.username,
    login,
    logout,
    getToken,
  };
}

/**
 * Selected once at module load. `mockAuth` is a build-time flag, so the choice
 * is stable for the app's lifetime and never violates the rules of hooks.
 */
export const useAuth: () => AuthState = mockAuth ? useMockAuth : useMsalAuth;
