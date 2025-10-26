/**
 * Authentication Provider component
 * Wraps the app with MSAL authentication context
 */

import { useEffect } from 'react';
import { MsalProvider } from '@azure/msal-react';
import { EventType } from '@azure/msal-browser';
import { isAuthEnabled } from '../authConfig';
import { initializeMsal } from '../services/authService';

interface AuthProviderProps {
  children: React.ReactNode;
}

// Initialize MSAL instance
const msalInstance = initializeMsal();

export function AuthProvider({ children }: AuthProviderProps) {
  useEffect(() => {
    if (!msalInstance) {
      console.log('Running without Azure AD authentication');
      return;
    }

    // Initialize MSAL
    msalInstance.initialize().then(() => {
      // Account selection logic
      const accounts = msalInstance.getAllAccounts();
      if (accounts.length > 0) {
        msalInstance.setActiveAccount(accounts[0]);
      }

      // Listen for sign-in event and set active account
      msalInstance.addEventCallback((event) => {
        if (event.eventType === EventType.LOGIN_SUCCESS && event.payload) {
          const payload = event.payload as any;
          const account = payload.account;
          msalInstance.setActiveAccount(account);
        }
      });
    });
  }, []);

  // If auth is disabled, just render children without MSAL provider
  if (!isAuthEnabled() || !msalInstance) {
    return <>{children}</>;
  }

  return <MsalProvider instance={msalInstance}>{children}</MsalProvider>;
}
