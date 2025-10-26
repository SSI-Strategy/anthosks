# Authentication & Authorization Specification

## Overview

This document specifies the integration of **Microsoft EntraID (Azure Active Directory)** authentication for the AnthosKS MOV Report application. The implementation follows OAuth 2.0 / OpenID Connect protocols using Microsoft Authentication Library (MSAL).

## Architecture

### Authentication Flow

```
User → Frontend (MSAL React) → Azure AD → Access Token → Backend API (FastAPI)
                                                              ↓
                                                    Token Validation (JWT)
                                                              ↓
                                                    Authorized Request
```

### Components

1. **Frontend (React + MSAL)**
   - MSAL React library for browser-based authentication
   - Interactive login with redirect or popup
   - Token acquisition and renewal
   - Protected route components

2. **Backend (FastAPI + MSAL Python)**
   - JWT token validation middleware
   - Azure AD token verification
   - User identity extraction
   - Role-based access control (RBAC)

3. **Azure AD Configuration**
   - App Registration in Azure Portal
   - API permissions and scopes
   - Redirect URIs
   - Token configuration

## Security Requirements

### Token Handling
- **Access Tokens**: Short-lived (1 hour), used for API authentication
- **Refresh Tokens**: Long-lived, used to acquire new access tokens
- **ID Tokens**: Contains user identity claims
- **Token Storage**: Browser session storage (MSAL handles this securely)
- **Token Transmission**: Always via Authorization header (`Bearer <token>`)

### Validation Requirements
- Validate token signature using Azure AD public keys
- Verify issuer (`iss` claim) matches Azure AD tenant
- Verify audience (`aud` claim) matches API application ID
- Check token expiration (`exp` claim)
- Validate token not used before issue time (`nbf` claim)

## Azure AD App Registration

### Required Configuration

**App Registration 1: Frontend (SPA)**
```
Name: AnthosKS-Frontend
Platform: Single-page application (SPA)
Redirect URIs:
  - http://localhost:5173 (development)
  - https://<production-domain> (production)
Authentication:
  - Allow public client flows: No
  - Supported account types: Single tenant
API Permissions:
  - User.Read (Microsoft Graph)
  - api://<backend-app-id>/access_as_user
```

**App Registration 2: Backend API**
```
Name: AnthosKS-API
Platform: Web API
Identifier URI: api://<application-id>
Expose an API:
  - Scope: access_as_user
  - Admin consent: Required
  - Description: Access MOV Report API
```

### Required Environment Variables

**Backend (.env)**
```bash
# Azure AD Configuration
AZURE_AD_TENANT_ID=<tenant-id>
AZURE_AD_CLIENT_ID=<backend-app-id>
AZURE_AD_AUTHORITY=https://login.microsoftonline.com/<tenant-id>
AZURE_AD_AUDIENCE=api://<backend-app-id>

# Optional
AZURE_AD_ALLOWED_GROUPS=<group-object-ids>  # Comma-separated for RBAC
```

**Frontend (.env or .env.local)**
```bash
VITE_AZURE_AD_CLIENT_ID=<frontend-app-id>
VITE_AZURE_AD_AUTHORITY=https://login.microsoftonline.com/<tenant-id>
VITE_AZURE_AD_REDIRECT_URI=http://localhost:5173
VITE_API_SCOPES=api://<backend-app-id>/access_as_user
```

## Implementation Details

### Backend Implementation

**Dependencies**
```bash
pip install msal fastapi-azure-auth python-jose[cryptography] pydantic-settings
```

**FastAPI Middleware Structure**
```python
# src/auth/azure_auth.py
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, jwk
import requests

class AzureADAuth:
    def __init__(self, tenant_id, client_id, audience):
        self.tenant_id = tenant_id
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.client_id = client_id
        self.audience = audience
        self.keys = self._get_signing_keys()

    def _get_signing_keys(self):
        # Fetch public keys from Azure AD
        jwks_uri = f"{self.authority}/discovery/v2.0/keys"
        response = requests.get(jwks_uri)
        return response.json()

    def verify_token(self, token: str) -> dict:
        # Validate JWT signature and claims
        # Returns decoded token with user info
        pass

    def get_current_user(self, credentials: HTTPAuthorizationCredentials):
        # Extract and validate token from Authorization header
        # Returns user identity
        pass
```

**Protected Endpoint Example**
```python
from src.auth.azure_auth import azure_auth

@app.get("/api/reports")
async def list_reports(user = Depends(azure_auth.get_current_user)):
    # user contains: oid, name, email, roles
    logger.info(f"User {user['email']} accessing reports")
    reports = db.list_reports()
    return {"reports": reports}
```

### Frontend Implementation

**Dependencies**
```bash
npm install @azure/msal-react @azure/msal-browser
```

**MSAL Configuration**
```typescript
// src/authConfig.ts
import { Configuration, PublicClientApplication } from "@azure/msal-browser";

export const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_AD_CLIENT_ID,
    authority: import.meta.env.VITE_AZURE_AD_AUTHORITY,
    redirectUri: import.meta.env.VITE_AZURE_AD_REDIRECT_URI,
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  }
};

export const msalInstance = new PublicClientApplication(msalConfig);

export const loginRequest = {
  scopes: [import.meta.env.VITE_API_SCOPES]
};
```

**App Wrapper**
```typescript
// src/main.tsx
import { MsalProvider } from "@azure/msal-react";
import { msalInstance } from "./authConfig";

ReactDOM.createRoot(document.getElementById('root')!).render(
  <MsalProvider instance={msalInstance}>
    <App />
  </MsalProvider>
);
```

**Protected Component Example**
```typescript
// src/components/ProtectedRoute.tsx
import { useMsal, useIsAuthenticated } from "@azure/msal-react";

export function ProtectedRoute({ children }) {
  const isAuthenticated = useIsAuthenticated();
  const { instance } = useMsal();

  if (!isAuthenticated) {
    instance.loginRedirect();
    return <div>Redirecting to login...</div>;
  }

  return children;
}
```

**API Client with Auth**
```typescript
// src/services/api.ts
import { msalInstance, loginRequest } from '../authConfig';

async function getAccessToken(): Promise<string> {
  const accounts = msalInstance.getAllAccounts();
  if (accounts.length === 0) throw new Error("No accounts found");

  const response = await msalInstance.acquireTokenSilent({
    ...loginRequest,
    account: accounts[0]
  });

  return response.accessToken;
}

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add token to all requests
api.interceptors.request.use(async (config) => {
  const token = await getAccessToken();
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

## Role-Based Access Control (RBAC)

### Azure AD Groups

Define security groups in Azure AD:
- `AnthosKS-Admins`: Full access (upload, delete, view all)
- `AnthosKS-Analysts`: Read-only access to reports and analytics
- `AnthosKS-Users`: Basic read access

### Backend Authorization

```python
from functools import wraps
from fastapi import HTTPException, status

def require_role(allowed_roles: list[str]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user=None, **kwargs):
            user_roles = user.get("roles", [])
            if not any(role in user_roles for role in allowed_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator

@app.delete("/api/reports/{report_id}")
@require_role(["AnthosKS-Admins"])
async def delete_report(report_id: str, user = Depends(azure_auth.get_current_user)):
    db.delete_report(report_id)
    return {"status": "deleted"}
```

## User Experience

### Login Flow
1. User navigates to application
2. If not authenticated, redirect to Azure AD login
3. User enters corporate credentials
4. MFA if required by organization
5. Consent to permissions (first time only)
6. Redirect back to application with tokens
7. Application loads with user identity displayed

### Logout Flow
1. User clicks "Sign Out"
2. Clear local tokens
3. (Optional) Redirect to Azure AD logout endpoint
4. Redirect to login page

### Token Refresh
- MSAL automatically refreshes tokens before expiration
- Silent token acquisition (no user interaction)
- Fallback to interactive login if refresh fails

## Security Best Practices

1. **Never expose tokens in URLs or logs**
2. **Use HTTPS in production**
3. **Validate all tokens server-side**
4. **Implement token revocation handling**
5. **Use scopes to limit permissions**
6. **Store tokens only in memory or session storage**
7. **Implement proper CORS policies**
8. **Rate limit authentication endpoints**
9. **Log all authentication events**
10. **Regularly rotate client secrets (if using confidential client)**

## Testing Strategy

### Unit Tests
- Token validation logic
- Claims extraction
- Permission checking

### Integration Tests
- End-to-end authentication flow
- Token refresh scenarios
- Unauthorized access attempts
- Role-based access enforcement

### Manual Testing Checklist
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Access protected endpoints with valid token
- [ ] Access protected endpoints without token
- [ ] Access protected endpoints with expired token
- [ ] Token refresh on expiration
- [ ] Logout and session cleanup
- [ ] Role-based access (admin vs. user)
- [ ] MFA flow (if enabled)

## Monitoring & Logging

### Backend Logging
```python
logger.info(f"Authentication attempt - User: {user_email}")
logger.info(f"Token validated - User: {user_email}, OID: {user_oid}")
logger.warning(f"Authentication failed - Invalid token")
logger.error(f"Token validation error: {error}")
```

### Azure AD Sign-in Logs
- Monitor sign-in activity in Azure Portal
- Track failed authentication attempts
- Review consent grants
- Analyze token usage patterns

## Migration Path

### Phase 1: Backend Authentication
1. Install dependencies
2. Configure Azure AD app registrations
3. Implement token validation middleware
4. Update API endpoints with authentication
5. Test with Postman using manual tokens

### Phase 2: Frontend Integration
1. Install MSAL React
2. Configure MSAL provider
3. Implement login/logout UI
4. Add protected routes
5. Update API client with token acquisition

### Phase 3: Authorization (RBAC)
1. Define Azure AD security groups
2. Implement role-based middleware
3. Update frontend to show/hide features based on roles
4. Test all permission scenarios

### Phase 4: Production Hardening
1. Configure production redirect URIs
2. Set up monitoring and alerts
3. Implement audit logging
4. Document runbooks
5. Train users

## Troubleshooting

### Common Issues

**Issue**: "AADSTS50011: The redirect URI specified in the request does not match"
**Solution**: Ensure redirect URI in code exactly matches Azure AD app registration

**Issue**: "AADSTS65001: The user or administrator has not consented"
**Solution**: Admin must grant consent in Azure Portal or user must consent on first login

**Issue**: "Invalid token signature"
**Solution**: Check token issuer and audience claims match configuration

**Issue**: "Token expired"
**Solution**: Implement token refresh logic or re-authenticate user

## References

- [Microsoft Identity Platform Documentation](https://learn.microsoft.com/en-us/azure/active-directory/develop/)
- [MSAL React](https://github.com/AzureAD/microsoft-authentication-library-for-js/tree/dev/lib/msal-react)
- [MSAL Python](https://github.com/AzureAD/microsoft-authentication-library-for-python)
- [FastAPI Azure Auth](https://github.com/Intility/fastapi-azure-auth)
- [JWT.io](https://jwt.io/) - Debug JWT tokens
