import React from 'react';
import ReactDOM from 'react-dom/client';
import { MsalProvider } from '@azure/msal-react';
import App from './App';
import { msalInstance, mockAuth } from './auth/authConfig';
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root')!);

/**
 * In mock-auth mode there is no MSAL instance and no MsalProvider — the mock
 * auth hook supplies a static token. Otherwise the app is wrapped in
 * MsalProvider so MSAL hooks work.
 */
if (mockAuth || !msalInstance) {
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
} else {
  root.render(
    <React.StrictMode>
      <MsalProvider instance={msalInstance}>
        <App />
      </MsalProvider>
    </React.StrictMode>,
  );
}
