/**
 * Authentication service to manage Azure AD tokens for API calls
 */

import { PublicClientApplication } from "@azure/msal-browser";
import type { AccountInfo } from "@azure/msal-browser";
import { msalConfig, tokenRequest, isAuthEnabled } from "../authConfig";

let msalInstance: PublicClientApplication | null = null;

export const initializeMsal = () => {
  if (!isAuthEnabled()) {
    console.log("Azure AD authentication is disabled - running in development mode");
    return null;
  }

  if (!msalInstance) {
    msalInstance = new PublicClientApplication(msalConfig);
  }
  return msalInstance;
};

export const getMsalInstance = (): PublicClientApplication | null => {
  return msalInstance;
};

/**
 * Get access token for API requests
 * Returns null if auth is disabled (development mode)
 */
export const getAccessToken = async (): Promise<string | null> => {
  if (!isAuthEnabled() || !msalInstance) {
    return null; // No auth in development mode
  }

  try {
    const accounts = msalInstance.getAllAccounts();

    if (accounts.length === 0) {
      throw new Error("No authenticated accounts found");
    }

    const account = accounts[0];

    // Try to acquire token silently
    const response = await msalInstance.acquireTokenSilent({
      ...tokenRequest,
      account: account,
    });

    return response.accessToken;
  } catch (error) {
    console.error("Failed to acquire token silently:", error);

    // If silent acquisition fails, try interactive
    try {
      const response = await msalInstance.acquireTokenPopup(tokenRequest);
      return response.accessToken;
    } catch (popupError) {
      console.error("Failed to acquire token with popup:", popupError);
      throw popupError;
    }
  }
};

/**
 * Get current user information
 */
export const getCurrentUser = (): AccountInfo | null => {
  if (!isAuthEnabled() || !msalInstance) {
    // Return mock user for development
    return {
      homeAccountId: "dev-user",
      environment: "dev",
      tenantId: "dev",
      username: "dev@localhost",
      localAccountId: "dev-user",
      name: "Development User",
    };
  }

  const accounts = msalInstance.getAllAccounts();
  return accounts.length > 0 ? accounts[0] : null;
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  if (!isAuthEnabled()) {
    return true; // Always authenticated in dev mode
  }

  if (!msalInstance) {
    return false;
  }

  const accounts = msalInstance.getAllAccounts();
  return accounts.length > 0;
};

/**
 * Sign out the current user
 */
export const signOut = async (): Promise<void> => {
  if (!isAuthEnabled() || !msalInstance) {
    return;
  }

  const accounts = msalInstance.getAllAccounts();
  if (accounts.length > 0) {
    await msalInstance.logoutPopup({
      account: accounts[0],
    });
  }
};
