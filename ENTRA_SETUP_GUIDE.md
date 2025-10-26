# Entra ID Authentication Setup Guide

## Overview

This guide walks through setting up Azure AD (Entra ID) authentication for the AnthosKS application deployed on Azure.

**Current Status:**
- Tenant ID: `c1fd05f4-5cd4-463e-b295-9ce7778cfc8d`
- Subscription: `b56571ee-60cd-4e56-a5df-d9d38ee5218d`
- Backend API URL: `https://app-anthosks-api-se-01-p.azurewebsites.net`
- Frontend UI URL: `https://app-anthosks-ui-se-01-p.azurewebsites.net`
- Local Backend: `http://localhost:8000`
- Local Frontend: `http://localhost:5173`

## Prerequisites

- Global Administrator or Application Administrator role in Azure AD
- Access to Azure Portal (https://portal.azure.com)

## Step 1: Create Backend API App Registration

### 1.1 Create the App Registration

1. Go to Azure Portal > **Azure Active Directory** > **App registrations**
2. Click **New registration**
3. Fill in the details:
   - **Name**: `AnthosKS API`
   - **Supported account types**: `Accounts in this organizational directory only (Single tenant)`
   - **Redirect URI**: Leave blank for now
4. Click **Register**

### 1.2 Configure API Identifier URI

1. In your new app registration, go to **Expose an API**
2. Click **Add** next to Application ID URI
3. Set it to: `api://anthosks-api`
4. Click **Save**

### 1.3 Define API Scope

1. Still in **Expose an API**, click **Add a scope**
2. Fill in:
   - **Scope name**: `access_as_user`
   - **Who can consent**: `Admins and users`
   - **Admin consent display name**: `Access AnthosKS API`
   - **Admin consent description**: `Allows the application to access the AnthosKS API on behalf of the signed-in user`
   - **User consent display name**: `Access AnthosKS API`
   - **User consent description**: `Allows the application to access AnthosKS on your behalf`
   - **State**: `Enabled`
3. Click **Add scope**

### 1.4 Record Backend Credentials

Go to **Overview** and record these values:
- **Application (client) ID**: `[RECORD THIS]`
- **Directory (tenant) ID**: `c1fd05f4-5cd4-463e-b295-9ce7778cfc8d` (already known)

The API audience will be: `api://anthosks-api`

## Step 2: Create Frontend SPA App Registration

### 2.1 Create the App Registration

1. Go to Azure Portal > **Azure Active Directory** > **App registrations**
2. Click **New registration**
3. Fill in the details:
   - **Name**: `AnthosKS Frontend`
   - **Supported account types**: `Accounts in this organizational directory only (Single tenant)`
   - **Redirect URI**:
     - Platform: `Single-page application (SPA)`
     - URI: `http://localhost:5173`
4. Click **Register**

### 2.2 Add Production Redirect URI

1. In your frontend app registration, go to **Authentication**
2. Under **Single-page application**, click **Add URI**
3. Add: `https://app-anthosks-ui-se-01-p.azurewebsites.net`
4. Configure the following settings:
   - **Implicit grant and hybrid flows**: ✅ Check both boxes (Access tokens, ID tokens) - Required for MSAL
   - **Allow public client flows**: No
5. Click **Save**

### 2.3 Configure API Permissions

1. Go to **API permissions**
2. Click **Add a permission**
3. Go to **My APIs** tab
4. Select **AnthosKS API** (the backend app you created)
5. Select **Delegated permissions**
6. Check `access_as_user`
7. Click **Add permissions**
8. Click **Grant admin consent for [Your Organization]** and confirm

### 2.4 Record Frontend Credentials

Go to **Overview** and record:
- **Application (client) ID**: `[RECORD THIS]`

## Step 3: Configure Environment Variables

### 3.1 Backend .env File

Add these lines to your `.env` file in the project root:

```bash
# Azure AD / EntraID Authentication
AZURE_AD_ENABLED=true
AZURE_AD_TENANT_ID=c1fd05f4-5cd4-463e-b295-9ce7778cfc8d
AZURE_AD_CLIENT_ID=[BACKEND_APP_CLIENT_ID_FROM_STEP_1.4]
AZURE_AD_AUDIENCE=api://anthosks-api
# Optional: Add group IDs for RBAC (comma-separated)
# AZURE_AD_ALLOWED_GROUPS=group-id-1,group-id-2

# CORS Configuration
CORS_ORIGINS=http://localhost:5173,https://app-anthosks-ui-se-01-p.azurewebsites.net
```

### 3.2 Frontend .env File

Create `frontend/.env` with:

```bash
# Azure AD / EntraID Authentication
VITE_AZURE_AD_ENABLED=true
VITE_AZURE_AD_CLIENT_ID=[FRONTEND_APP_CLIENT_ID_FROM_STEP_2.4]
VITE_AZURE_AD_AUTHORITY=https://login.microsoftonline.com/c1fd05f4-5cd4-463e-b295-9ce7778cfc8d
VITE_AZURE_AD_REDIRECT_URI=http://localhost:5173

# API Scopes (use the backend app client ID)
VITE_API_SCOPES=api://anthosks-api/access_as_user

# API Base URL
VITE_API_URL=http://localhost:8000
```

### 3.3 Frontend .env.production File

Create `frontend/.env.production` for production builds:

```bash
# Azure AD / EntraID Authentication
VITE_AZURE_AD_ENABLED=true
VITE_AZURE_AD_CLIENT_ID=[FRONTEND_APP_CLIENT_ID_FROM_STEP_2.4]
VITE_AZURE_AD_AUTHORITY=https://login.microsoftonline.com/c1fd05f4-5cd4-463e-b295-9ce7778cfc8d
VITE_AZURE_AD_REDIRECT_URI=https://app-anthosks-ui-se-01-p.azurewebsites.net

# API Scopes
VITE_API_SCOPES=api://anthosks-api/access_as_user

# API Base URL
VITE_API_URL=https://app-anthosks-api-se-01-p.azurewebsites.net
```

## Step 4: Configure Azure Web App Settings

### 4.1 Backend Web App Settings

Run these commands to configure the backend app settings:

```bash
az webapp config appsettings set \
  --name app-anthosks-api-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --settings \
    AZURE_AD_ENABLED=true \
    AZURE_AD_TENANT_ID=c1fd05f4-5cd4-463e-b295-9ce7778cfc8d \
    AZURE_AD_CLIENT_ID=[BACKEND_APP_CLIENT_ID] \
    AZURE_AD_AUDIENCE=api://anthosks-api \
    CORS_ORIGINS="http://localhost:5173,https://app-anthosks-ui-se-01-p.azurewebsites.net"
```

### 4.2 Frontend Web App Settings (if needed)

For Vite apps deployed to Azure, you may need to set these at build time or use a runtime configuration approach. The simplest is to build with the production environment variables.

## Step 5: Test Locally

### 5.1 Start Backend

```bash
source venv/bin/activate
python src/api/main.py
```

Check logs for:
```
INFO:     Azure AD authentication enabled
INFO:     Tenant ID: c1fd05f4-5cd4-463e-b295-9ce7778cfc8d
```

### 5.2 Start Frontend

```bash
cd frontend
npm run dev
```

### 5.3 Test Authentication Flow

1. Open http://localhost:5173
2. Click the login button
3. Sign in with your Azure AD account (`johan.stromquist@ssistrategy.com`)
4. Consent to the permissions
5. Verify you're redirected back and see your user info
6. Try uploading a report to test API authentication

## Step 6: Deploy to Azure

### 6.1 Build and Deploy Backend

```bash
# Backend should auto-deploy from the zip deployment
# Or manually:
az webapp deploy --name app-anthosks-api-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --src-path backend-deploy.zip \
  --type zip
```

### 6.2 Build and Deploy Frontend

```bash
cd frontend
npm run build  # Uses .env.production
cd ..

# Create deployment package
cd frontend/dist
zip -r ../../frontend-deploy.zip .
cd ../..

# Deploy
az webapp deploy --name app-anthosks-ui-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --src-path frontend-deploy.zip \
  --type zip
```

### 6.3 Verify Production

1. Visit https://app-anthosks-ui-se-01-p.azurewebsites.net
2. Click login
3. Authenticate with Azure AD
4. Test full functionality

## Step 7: Optional - Configure RBAC with Groups

If you want to restrict access to specific Azure AD groups:

### 7.1 Create or Identify Groups

1. Go to **Azure Active Directory** > **Groups**
2. Create a new group (e.g., "AnthosKS Users") or use existing
3. Record the **Object ID** of the group

### 7.2 Update Backend Configuration

Add to your `.env`:
```bash
AZURE_AD_ALLOWED_GROUPS=group-object-id-1,group-object-id-2
```

And update Azure Web App settings:
```bash
az webapp config appsettings set \
  --name app-anthosks-api-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --settings AZURE_AD_ALLOWED_GROUPS=group-object-id-1
```

### 7.3 Add Users to Groups

1. Go to your group > **Members**
2. Click **Add members**
3. Add authorized users

## Troubleshooting

### Invalid Redirect URI
- Ensure redirect URIs in Azure AD match exactly (including http vs https)
- Check for trailing slashes

### CORS Errors
- Verify CORS_ORIGINS environment variable includes the frontend URL
- Check browser console for specific CORS error messages

### Token Validation Failures
- Verify AZURE_AD_AUDIENCE matches the identifier URI (api://anthosks-api)
- Check that AZURE_AD_CLIENT_ID is the backend app's client ID
- Ensure frontend is requesting tokens for the correct scope

### User Not Authorized (403)
- If using AZURE_AD_ALLOWED_GROUPS, verify user is member of allowed group
- Check backend logs for authorization details

### Testing Tokens
- Visit https://jwt.ms and paste your access token to inspect claims
- Verify `aud` claim matches AZURE_AD_AUDIENCE
- Verify `iss` claim matches expected issuer

## Security Checklist

- [ ] App registrations created in Azure AD
- [ ] API scope defined and exposed
- [ ] Frontend granted API permissions with admin consent
- [ ] Redirect URIs configured for both local and production
- [ ] Environment variables set in both local .env and Azure Web Apps
- [ ] CORS origins configured properly
- [ ] Test authentication flow in local environment
- [ ] Test authentication flow in production
- [ ] (Optional) RBAC groups configured and users assigned
- [ ] Tokens validated and inspected for correct claims

## Quick Reference

**Tenant ID**: `c1fd05f4-5cd4-463e-b295-9ce7778cfc8d`

**Backend App**:
- Name: AnthosKS API
- Identifier URI: api://anthosks-api
- Scope: api://anthosks-api/access_as_user
- Client ID: `[To be filled after Step 1]`

**Frontend App**:
- Name: AnthosKS Frontend
- Platform: Single-page application
- Client ID: `[To be filled after Step 2]`
- Redirect URIs:
  - http://localhost:5173
  - https://app-anthosks-ui-se-01-p.azurewebsites.net

**URLs**:
- Local Backend: http://localhost:8000
- Local Frontend: http://localhost:5173
- Production Backend: https://app-anthosks-api-se-01-p.azurewebsites.net
- Production Frontend: https://app-anthosks-ui-se-01-p.azurewebsites.net
