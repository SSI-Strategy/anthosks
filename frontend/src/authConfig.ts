/**
 * Azure AD / EntraID authentication configuration for MSAL React
 */

import type { Configuration, PopupRequest } from "@azure/msal-browser";

// Azure AD configuration from environment variables
export const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_AD_CLIENT_ID || "dev-client-id",
    authority: import.meta.env.VITE_AZURE_AD_AUTHORITY || "https://login.microsoftonline.com/common",
    redirectUri: import.meta.env.VITE_AZURE_AD_REDIRECT_URI || window.location.origin,
  },
  cache: {
    cacheLocation: "sessionStorage", // Use sessionStorage for better security
    storeAuthStateInCookie: false, // Set to true for IE11 or Edge compatibility
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        switch (level) {
          case 0: // Error
            console.error(message);
            break;
          case 1: // Warning
            console.warn(message);
            break;
          case 2: // Info
            console.info(message);
            break;
          case 3: // Verbose
            console.debug(message);
            break;
        }
      },
    },
  },
};

// Scopes for API access
const apiScopes = import.meta.env.VITE_API_SCOPES || "api://dev/access_as_user";

export const loginRequest: PopupRequest = {
  scopes: [apiScopes],
};

// Silent token request configuration
export const tokenRequest = {
  scopes: [apiScopes],
  forceRefresh: false, // Set to true to skip cache
};

// Check if authentication is enabled
export const isAuthEnabled = () => {
  return import.meta.env.VITE_AZURE_AD_ENABLED === "true";
};
