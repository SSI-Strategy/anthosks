# Quick Start: Enable Entra ID Authentication

## Current Status
- ✅ All code is ready and production-quality
- ✅ Environment files created with placeholders
- ✅ CORS configured
- ✅ Enhanced audit logging added
- ❌ Azure AD app registrations need to be created (manual step)
- ❌ Client IDs need to be filled in

## What You Need to Do Manually

### Step 1: Create Azure AD App Registrations

You need **Global Administrator** or **Application Administrator** role to do this.

#### 1A. Create Backend API App

1. Go to https://portal.azure.com
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in:
   - Name: `AnthosKS API`
   - Supported account types: `Accounts in this organizational directory only`
   - Redirect URI: Leave blank
5. Click **Register**
6. **RECORD THE APPLICATION (CLIENT) ID** - you'll need this

#### 1B. Configure Backend API

1. In your new app, go to **Expose an API**
2. Click **Add** next to Application ID URI
3. Change it to: `api://anthosks-api`
4. Click **Save**
5. Click **Add a scope**:
   - Scope name: `access_as_user`
   - Who can consent: `Admins and users`
   - Admin consent display name: `Access AnthosKS API`
   - Admin consent description: `Allows the application to access the AnthosKS API on behalf of the signed-in user`
   - User consent display name: `Access AnthosKS API`
   - User consent description: `Allows the application to access AnthosKS on your behalf`
   - State: `Enabled`
6. Click **Add scope**

#### 1C. Create Frontend SPA App

1. Go to **Azure Active Directory** > **App registrations**
2. Click **New registration**
3. Fill in:
   - Name: `AnthosKS Frontend`
   - Supported account types: `Accounts in this organizational directory only`
   - Redirect URI:
     - Platform: `Single-page application (SPA)`
     - URI: `http://localhost:5173`
4. Click **Register**
5. **RECORD THE APPLICATION (CLIENT) ID** - you'll need this

#### 1D. Configure Frontend App

1. In your frontend app, go to **Authentication**
2. Under **Single-page application**, click **Add URI**
3. Add: `https://app-anthosks-ui-se-01-p.azurewebsites.net`
4. Under **Implicit grant and hybrid flows**:
   - ✅ Check **Access tokens**
   - ✅ Check **ID tokens**
5. Click **Save**

#### 1E. Grant API Permissions

1. Still in the frontend app, go to **API permissions**
2. Click **Add a permission**
3. Go to **My APIs** tab
4. Select **AnthosKS API**
5. Select **Delegated permissions**
6. Check `access_as_user`
7. Click **Add permissions**
8. Click **Grant admin consent for [Your Organization]**
9. Click **Yes** to confirm

### Step 2: Update Environment Files

Now update the placeholder values with the Client IDs you recorded:

#### 2A. Backend (.env)

Open `.env` and replace:
```bash
AZURE_AD_ENABLED=true  # Change from false to true
AZURE_AD_CLIENT_ID=REPLACE_WITH_BACKEND_APP_CLIENT_ID  # Replace with backend app's client ID
```

#### 2B. Frontend (frontend/.env)

Open `frontend/.env` and replace:
```bash
VITE_AZURE_AD_ENABLED=true  # Change from false to true
VITE_AZURE_AD_CLIENT_ID=REPLACE_WITH_FRONTEND_APP_CLIENT_ID  # Replace with frontend app's client ID
```

#### 2C. Frontend Production (frontend/.env.production)

Open `frontend/.env.production` and replace:
```bash
VITE_AZURE_AD_CLIENT_ID=REPLACE_WITH_FRONTEND_APP_CLIENT_ID  # Replace with frontend app's client ID
```

### Step 3: Test Locally

```bash
# Terminal 1 - Start backend
source venv/bin/activate
python src/api/main.py

# Terminal 2 - Start frontend
cd frontend
npm run dev
```

Open http://localhost:5173 and click the login button. You should be redirected to Azure AD login.

### Step 4: Deploy to Azure

#### 4A. Configure Backend App Settings

Run this command (replace `YOUR_BACKEND_CLIENT_ID` with the actual ID):

```bash
az webapp config appsettings set \
  --name app-anthosks-api-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --settings \
    AZURE_AD_ENABLED=true \
    AZURE_AD_TENANT_ID=c1fd05f4-5cd4-463e-b295-9ce7778cfc8d \
    AZURE_AD_CLIENT_ID=YOUR_BACKEND_CLIENT_ID \
    AZURE_AD_AUDIENCE=api://anthosks-api \
    CORS_ORIGINS="http://localhost:5173,http://localhost:5174,http://localhost:3000,https://app-anthosks-ui-se-01-p.azurewebsites.net"
```

#### 4B. Build and Deploy Frontend

The frontend will use `.env.production` when you run:

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

#### 4C. Deploy Backend

If you've made changes to backend code:

```bash
# From project root
cd src
zip -r ../backend-deploy.zip . -x "*.pyc" -x "__pycache__/*" -x "*.pytest_cache/*"
cd ..

az webapp deploy \
  --name app-anthosks-api-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --src-path backend-deploy.zip \
  --type zip
```

### Step 5: Verify Production

1. Visit https://app-anthosks-ui-se-01-p.azurewebsites.net
2. Click the login button
3. Sign in with your Azure AD account (`johan.stromquist@ssistrategy.com`)
4. Grant consent when prompted
5. You should be logged in and see your name displayed

## Troubleshooting

### "Invalid redirect URI"
- Make sure you added both redirect URIs in the frontend app registration:
  - `http://localhost:5173` (for local)
  - `https://app-anthosks-ui-se-01-p.azurewebsites.net` (for production)

### CORS errors
- Verify the backend has the CORS_ORIGINS setting configured in Azure Web App settings

### "Invalid audience"
- Make sure the backend app's identifier URI is exactly `api://anthosks-api`
- Verify AZURE_AD_AUDIENCE in backend settings matches this

### Token validation failures
- Check that AZURE_AD_CLIENT_ID on backend is the **backend app's** client ID (not frontend)
- Check that VITE_AZURE_AD_CLIENT_ID on frontend is the **frontend app's** client ID (not backend)

### View token claims
- Go to https://jwt.ms
- Copy your access token from browser developer tools
- Paste it to see the claims
- Verify `aud` claim is `api://anthosks-api`

## Quick Reference

**Tenant ID**: `c1fd05f4-5cd4-463e-b295-9ce7778cfc8d`

**Backend App**:
- Name: AnthosKS API
- Identifier URI: `api://anthosks-api`
- Scope: `api://anthosks-api/access_as_user`

**Frontend App**:
- Name: AnthosKS Frontend
- Platform: Single-page application
- Redirect URIs:
  - `http://localhost:5173`
  - `https://app-anthosks-ui-se-01-p.azurewebsites.net`

**URLs**:
- Production Backend: https://app-anthosks-api-se-01-p.azurewebsites.net
- Production Frontend: https://app-anthosks-ui-se-01-p.azurewebsites.net

## Optional: Enable Role-Based Access Control (RBAC)

If you want to restrict access to specific Azure AD groups:

1. Create or identify an Azure AD group
2. Get the group's Object ID from Azure Portal
3. Add to backend .env:
   ```bash
   AZURE_AD_ALLOWED_GROUPS=your-group-object-id
   ```
4. Add the same setting to Azure Web App settings
5. Add users to the group in Azure AD

Users not in the allowed group will get a 403 Forbidden error with detailed audit logging.
