# GitHub Actions CI/CD Setup

This document explains how to complete the GitHub Actions setup for automated deployments to Azure.

## Overview

The repository is configured with two GitHub Actions workflows:
- **Deploy Backend API** (`.github/workflows/deploy-backend.yml`) - Deploys FastAPI backend
- **Deploy Frontend UI** (`.github/workflows/deploy-frontend.yml`) - Deploys React frontend

Both workflows use Azure CLI for deployment, which requires a service principal with contributor access.

## Current Status

✅ **Completed:**
- Repository created: https://github.com/SSI-Strategy/anthosks
- Workflows configured with proper build steps
- Environment variables configured for production builds
- Publish profiles downloaded (but not usable due to validation issues)

⚠️ **Requires Admin Action:**
- Service principal creation (requires Azure AD admin permissions)
- GitHub secret configuration with service principal credentials

## Step 1: Create Azure Service Principal

You need Azure AD admin permissions to create a service principal. Run this command:

```bash
az ad sp create-for-rbac \
  --name "github-actions-anthosks" \
  --role contributor \
  --scopes /subscriptions/b56571ee-60cd-4e56-a5df-d9d38ee5218d/resourceGroups/rg-sandbox-se-01-p \
  --sdk-auth
```

This will output JSON credentials like:

```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "b56571ee-60cd-4e56-a5df-d9d38ee5218d",
  "tenantId": "c1fd05f4-5cd4-463e-b295-9ce7778cfc8d",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

**Alternative if you don't have permissions:**

Ask your Azure administrator to create the service principal with these specifications:
- Name: `github-actions-anthosks`
- Role: `Contributor`
- Scope: `/subscriptions/b56571ee-60cd-4e56-a5df-d9d38ee5218d/resourceGroups/rg-sandbox-se-01-p`

## Step 2: Add GitHub Secret

Once you have the service principal credentials, add them to GitHub:

### Option A: Using GitHub CLI (Recommended)
```bash
# Copy the ENTIRE JSON output from Step 1 to a file
cat > /tmp/azure-creds.json <<'EOF'
{
  "clientId": "...",
  "clientSecret": "...",
  ...
}
EOF

# Set the GitHub secret
gh secret set AZURE_CREDENTIALS --repo SSI-Strategy/anthosks < /tmp/azure-creds.json

# Clean up
rm /tmp/azure-creds.json
```

### Option B: Using GitHub Web UI
1. Go to https://github.com/SSI-Strategy/anthosks/settings/secrets/actions
2. Click "New repository secret"
3. Name: `AZURE_CREDENTIALS`
4. Value: Paste the entire JSON output from Step 1
5. Click "Add secret"

## Step 3: Verify Setup

After adding the secret, test the deployment:

```bash
# Make a small change and push
echo "# Deployment test" >> README.md
git add README.md
git commit -m "Test: Verify GitHub Actions deployment"
git push
```

Watch the workflow runs:
```bash
gh run watch --repo SSI-Strategy/anthosks
```

Or view in browser:
https://github.com/SSI-Strategy/anthosks/actions

## Workflow Triggers

Both workflows are configured to trigger on:
- **Push to main branch** with changes to relevant paths:
  - Backend: Changes to `src/**`, `requirements.txt`, `startup.sh`, or workflow file
  - Frontend: Changes to `frontend/**` or workflow file

## Deployment Process

### Backend Deployment
1. Checkout code
2. Setup Python 3.11
3. Install dependencies
4. Run tests (if any)
5. Create zip package (excluding git, tests, etc.)
6. Deploy to `app-anthosks-api-se-01-p` via Azure CLI

### Frontend Deployment
1. Checkout code
2. Setup Node.js 20
3. Install dependencies (`npm ci`)
4. Build with production environment variables:
   - Azure AD auth enabled
   - Production API URL
   - All auth configuration
5. Create zip package from dist folder
6. Deploy to `app-anthosks-ui-se-01-p` via Azure CLI

## Troubleshooting

### "Insufficient privileges" Error
You don't have Azure AD admin permissions. Ask your administrator to create the service principal and provide you with the credentials.

### "Invalid publish profile" Error
We switched from publish profiles to service principal authentication because the webapps-deploy action was validating app names incorrectly.

### Deployment Succeeds but Site Doesn't Update
- Check Azure Web App logs: `az webapp log tail --name <app-name> --resource-group rg-sandbox-se-01-p`
- Restart the app: `az webapp restart --name <app-name> --resource-group rg-sandbox-se-01-p`

### Build Fails
- Check workflow logs: `gh run view --repo SSI-Strategy/anthosks --log`
- Common issues:
  - Missing environment variables (check `.github/workflows/` files)
  - TypeScript errors in frontend
  - Missing Python dependencies in backend

## Manual Deployment (Fallback)

If GitHub Actions isn't working, you can deploy manually:

### Backend
```bash
cd /Users/johanstromquist/Dropbox/Coding/AnthosKS
zip -r deploy.zip . -x ".git/*" ".github/*" "*.pyc" "__pycache__/*" "tests/*" ".env" "venv/*" "*.md" "frontend/*" "*.zip"
az webapp deploy --resource-group rg-sandbox-se-01-p --name app-anthosks-api-se-01-p --src-path deploy.zip --type zip
```

### Frontend
```bash
cd /Users/johanstromquist/Dropbox/Coding/AnthosKS/frontend
npm run build
cd dist
zip -r ../deploy.zip .
cd ..
az webapp deploy --resource-group rg-sandbox-se-01-p --name app-anthosks-ui-se-01-p --src-path deploy.zip --type zip
```

## Repository Information

- **GitHub Repository**: https://github.com/SSI-Strategy/anthosks
- **Organization**: SSI-Strategy
- **Backend App**: app-anthosks-api-se-01-p
- **Frontend App**: app-anthosks-ui-se-01-p
- **Resource Group**: rg-sandbox-se-01-p
- **Subscription ID**: b56571ee-60cd-4e56-a5df-d9d38ee5218d
- **Tenant ID**: c1fd05f4-5cd4-463e-b295-9ce7778cfc8d

## Next Steps

1. Create service principal (requires admin)
2. Add AZURE_CREDENTIALS secret to GitHub
3. Push a change to test automated deployment
4. Monitor workflow runs and verify successful deployments
