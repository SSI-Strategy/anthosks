# Simple Single-App Authentication Setup

## Overview

This is a simplified setup using **one Azure AD app registration** for both frontend and backend. Perfect for internal/sandbox applications.

## Step 1: Create Single Azure AD App Registration

1. Go to https://portal.azure.com
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in:
   - **Name**: `AnthosKS`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**:
     - Platform: `Single-page application (SPA)`
     - URI: `http://localhost:5173`
5. Click **Register**
6. **COPY THE APPLICATION (CLIENT) ID** - you'll need this

## Step 2: Configure the App Registration

### 2A. Add Production Redirect URI

1. In your app, go to **Authentication**
2. Under **Single-page application**, click **Add URI**
3. Add: `https://app-anthosks-ui-se-01-p.azurewebsites.net`
4. Under **Implicit grant and hybrid flows**:
   - ✅ Check **Access tokens**
   - ✅ Check **ID tokens**
5. Click **Save**

### 2B. Expose API Scope

1. Go to **Expose an API**
2. Click **Add** next to Application ID URI
3. Accept the default `api://[your-client-id]` or change to `api://anthosks`
4. Click **Save**
5. Click **Add a scope**:
   - Scope name: `access_as_user`
   - Who can consent: `Admins and users`
   - Admin consent display name: `Access AnthosKS`
   - Admin consent description: `Allows access to AnthosKS application`
   - User consent display name: `Access AnthosKS`
   - User consent description: `Allows access to AnthosKS on your behalf`
   - State: `Enabled`
6. Click **Add scope**

### 2C. Grant API Permissions to Itself

1. Go to **API permissions**
2. Click **Add a permission**
3. Go to **My APIs** tab
4. Select **AnthosKS** (your own app)
5. Select **Delegated permissions**
6. Check `access_as_user`
7. Click **Add permissions**
8. Click **Grant admin consent for [Your Organization]**

## Step 3: Update Environment Variables

You'll use the **same Client ID** for both frontend and backend.

### 3A. Backend (.env)

```bash
# Change these lines:
AZURE_AD_ENABLED=true
AZURE_AD_CLIENT_ID=YOUR_CLIENT_ID_FROM_STEP_1
AZURE_AD_AUDIENCE=api://YOUR_CLIENT_ID_FROM_STEP_1
```

Or if you used custom URI `api://anthosks`:
```bash
AZURE_AD_ENABLED=true
AZURE_AD_CLIENT_ID=YOUR_CLIENT_ID_FROM_STEP_1
AZURE_AD_AUDIENCE=api://anthosks
```

### 3B. Frontend (frontend/.env)

```bash
# Change these lines:
VITE_AZURE_AD_ENABLED=true
VITE_AZURE_AD_CLIENT_ID=YOUR_CLIENT_ID_FROM_STEP_1
VITE_API_SCOPES=api://YOUR_CLIENT_ID_FROM_STEP_1/access_as_user
```

Or if you used custom URI:
```bash
VITE_AZURE_AD_ENABLED=true
VITE_AZURE_AD_CLIENT_ID=YOUR_CLIENT_ID_FROM_STEP_1
VITE_API_SCOPES=api://anthosks/access_as_user
```

### 3C. Frontend Production (frontend/.env.production)

```bash
# Change this line:
VITE_AZURE_AD_CLIENT_ID=YOUR_CLIENT_ID_FROM_STEP_1
VITE_API_SCOPES=api://YOUR_CLIENT_ID_FROM_STEP_1/access_as_user
```

## Step 4: Test Locally

```bash
# Terminal 1 - Backend
source venv/bin/activate
python src/api/main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Open http://localhost:5173 and test login.

## Step 5: Deploy to Azure

### 5A. Configure Backend Web App

```bash
# Replace YOUR_CLIENT_ID with the actual client ID from Step 1
az webapp config appsettings set \
  --name app-anthosks-api-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --settings \
    AZURE_AD_ENABLED=true \
    AZURE_AD_TENANT_ID=c1fd05f4-5cd4-463e-b295-9ce7778cfc8d \
    AZURE_AD_CLIENT_ID=YOUR_CLIENT_ID \
    AZURE_AD_AUDIENCE=api://YOUR_CLIENT_ID \
    CORS_ORIGINS="http://localhost:5173,http://localhost:5174,http://localhost:3000,https://app-anthosks-ui-se-01-p.azurewebsites.net"
```

### 5B. Build and Deploy Frontend

```bash
cd frontend
npm run build
cd dist
zip -r ../../frontend-deploy.zip .
cd ../..

az webapp deploy \
  --name app-anthosks-ui-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --src-path frontend-deploy.zip \
  --type zip
```

### 5C. Deploy Backend (if needed)

```bash
cd src
zip -r ../backend-deploy.zip . -x "*.pyc" -x "__pycache__/*" -x "*.pytest_cache/*"
cd ..

az webapp deploy \
  --name app-anthosks-api-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --src-path backend-deploy.zip \
  --type zip
```

## Step 6: Verify Production

Visit https://app-anthosks-ui-se-01-p.azurewebsites.net and test login.

## Summary

**One App Registration: "AnthosKS"**
- Client ID: [YOUR_CLIENT_ID]
- Tenant ID: c1fd05f4-5cd4-463e-b295-9ce7778cfc8d
- Application ID URI: `api://[YOUR_CLIENT_ID]` or `api://anthosks`
- Scope: `access_as_user`
- Redirect URIs:
  - `http://localhost:5173`
  - `https://app-anthosks-ui-se-01-p.azurewebsites.net`

**Used by:**
- Frontend: Uses this Client ID to get tokens
- Backend: Validates tokens for this same Client ID

This is simpler than the two-app approach and perfectly fine for internal/sandbox applications.

## Troubleshooting

Same troubleshooting steps as QUICK_START_AUTH.md apply. The main difference is you use the same Client ID everywhere.
