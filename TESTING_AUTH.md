# Testing Azure AD Authentication

This guide explains how to test the Azure AD authentication implementation.

## Quick Setup for Testing

### Option 1: Use Azure AD Test Tenant (Recommended)

Microsoft provides free Azure AD test tenants for development:

1. **Create a Microsoft 365 Developer Account** (Free)
   - Visit: https://developer.microsoft.com/en-us/microsoft-365/dev-program
   - Sign up for a free developer subscription
   - You'll get a test tenant with admin access

2. **Create App Registrations**

   **Backend API App:**
   ```
   Azure Portal → App Registrations → New Registration
   Name: AnthosKS-API-Dev
   Supported account types: Single tenant
   → Register

   → Expose an API
   → Add a scope:
     - Scope name: access_as_user
     - Who can consent: Admins and users
     - Admin consent display name: Access MOV API
     - Admin consent description: Allows the app to access the MOV API

   → Copy:
     - Application (client) ID
     - Directory (tenant) ID
   ```

   **Frontend SPA App:**
   ```
   Azure Portal → App Registrations → New Registration
   Name: AnthosKS-Frontend-Dev
   Supported account types: Single tenant
   Redirect URI: Single-page application → http://localhost:5173
   → Register

   → Authentication
   → Add platform: Single-page application
   → Redirect URIs: http://localhost:5173
   → Implicit grant: UNCHECK both boxes (not needed for SPA)
   → Allow public client flows: No

   → API Permissions
   → Add a permission → My APIs → AnthosKS-API-Dev
   → Select: access_as_user
   → Grant admin consent

   → Copy:
     - Application (client) ID
   ```

3. **Update Environment Variables**

   **Backend (.env):**
   ```bash
   AZURE_AD_ENABLED=true
   AZURE_AD_TENANT_ID=<your-tenant-id>
   AZURE_AD_CLIENT_ID=<backend-app-client-id>
   AZURE_AD_AUDIENCE=api://<backend-app-client-id>
   ```

   **Frontend (.env):**
   ```bash
   VITE_AZURE_AD_ENABLED=true
   VITE_AZURE_AD_CLIENT_ID=<frontend-app-client-id>
   VITE_AZURE_AD_AUTHORITY=https://login.microsoftonline.com/<your-tenant-id>
   VITE_AZURE_AD_REDIRECT_URI=http://localhost:5173
   VITE_API_SCOPES=api://<backend-app-client-id>/access_as_user
   ```

4. **Restart Services**
   ```bash
   # Backend
   lsof -ti:8000 | xargs kill -9
   source venv/bin/activate && python src/api/main.py

   # Frontend
   cd frontend
   npm run dev
   ```

5. **Test Login**
   - Navigate to http://localhost:5173
   - Click "Sign In" button
   - Login with your test tenant credentials
   - You should see your name in the header
   - Try accessing different pages - they should all work with your token

### Option 2: Disable Auth Temporarily for Development

If you're not ready to set up Azure AD yet:

**Backend (.env):**
```bash
AZURE_AD_ENABLED=false
```

**Frontend (.env):**
```bash
VITE_AZURE_AD_ENABLED=false
```

This will:
- Show "DEV MODE" badge in the header
- Allow all API requests without authentication
- Use a mock "Development User" account

## Testing Checklist

### Basic Authentication Flow
- [ ] User can click "Sign In" button
- [ ] Azure AD login popup appears
- [ ] User can enter credentials
- [ ] Consent screen appears (first time only)
- [ ] User is redirected back to app after login
- [ ] User's name appears in header
- [ ] Token is automatically attached to API requests

### Protected Endpoints
- [ ] Upload report (POST /api/reports/upload)
- [ ] List reports (GET /api/reports)
- [ ] View report details (GET /api/reports/{id})
- [ ] Delete report (DELETE /api/reports/{id})
- [ ] View analytics (GET /api/analytics/*)

### Token Management
- [ ] Token is automatically refreshed when expired
- [ ] Silent token renewal works (no popup)
- [ ] Interactive renewal works if silent fails
- [ ] Logout clears tokens
- [ ] Re-login after logout works

### Error Handling
- [ ] 401 Unauthorized shows appropriate message
- [ ] Invalid token triggers re-authentication
- [ ] Network errors are handled gracefully

## Debugging Authentication Issues

### Check Backend Logs
```bash
# Backend should show:
INFO:src.auth.azure_auth:Azure AD authentication ENABLED for tenant: <tenant-id>
INFO:src.api.main:Received file: test.pdf from user: user@domain.com
```

### Check Frontend Console
```javascript
// Open browser console (F12)
// Look for MSAL logs:
[MSAL] Acquiring token silently...
[MSAL] Token acquired successfully
```

### Test Token Manually

**Get Token:**
```bash
# In browser console after login:
const accounts = msalInstance.getAllAccounts();
const result = await msalInstance.acquireTokenSilent({
  scopes: ["api://<backend-app-id>/access_as_user"],
  account: accounts[0]
});
console.log(result.accessToken);
```

**Test API with Token:**
```bash
# Copy token from above
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/reports
```

**Decode Token:**
Visit https://jwt.ms and paste your token to see claims:
- `aud`: Should match your backend client ID
- `iss`: Should be your Azure AD tenant
- `exp`: Token expiration time
- `oid`: User's unique identifier
- `preferred_username`: User's email

### Common Issues

**Issue**: "Invalid token signature"
**Solution**: Check that `AZURE_AD_AUDIENCE` matches the backend `Application (client) ID`

**Issue**: "AADSTS50011: Redirect URI mismatch"
**Solution**: Ensure redirect URI in code exactly matches Azure Portal configuration

**Issue**: "AADSTS65001: User has not consented"
**Solution**: Grant admin consent in Azure Portal → API Permissions

**Issue**: "No accounts found"
**Solution**: User needs to login first - click "Sign In" button

**Issue**: Token works but API returns 401
**Solution**: Check backend logs - may be incorrect `AZURE_AD_CLIENT_ID` or `AZURE_AD_AUDIENCE`

## Production Deployment

Before deploying to production:

1. **Update Redirect URIs** in Azure Portal with production domain
2. **Update Frontend .env** with production redirect URI
3. **Configure HTTPS** (required for production)
4. **Set up proper logging** and monitoring
5. **Configure CORS** to allow only your production domain
6. **Review security** settings in Azure Portal
7. **Test MFA** if required by your organization
8. **Create Azure AD Groups** for role-based access control
9. **Update `AZURE_AD_ALLOWED_GROUPS`** to restrict access

## Additional Resources

- [Microsoft Identity Platform Documentation](https://learn.microsoft.com/en-us/azure/active-directory/develop/)
- [MSAL.js Browser Documentation](https://github.com/AzureAD/microsoft-authentication-library-for-js/tree/dev/lib/msal-browser)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io Token Debugger](https://jwt.io/)
