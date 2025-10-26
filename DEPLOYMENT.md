# AnthosKS Azure Deployment Guide

This document describes the Azure infrastructure and deployment process for the AnthosKS compliance extraction system.

## Architecture Overview

### Resource Organization
- **Sandbox Resource Group**: `rg-sandbox-se-01-p` - Hosts app-specific resources
- **Shared Resources**: Uses shared OpenAI and PostgreSQL from `rg-shared_resources-se-01-p`

### Deployed Resources

| Resource | Name | Purpose |
|----------|------|---------|
| Storage Account | `stsandboxse01pfbfe41` | PDF/DOCX uploads & Excel reports |
| App Service Plan | `asp-sandbox-se-01-p` | Shared hosting (B1 Linux) |
| Backend API | `app-anthosks-api-se-01-p` | FastAPI application |
| Frontend UI | `app-anthosks-ui-se-01-p` | React (Vite) application |
| App Insights | `appi-anthosks-se-01-p` | Monitoring & logging |
| Blob Containers | `anthosks-uploads`, `anthosks-reports` | File storage |

### Shared Resources (from rg-shared_resources-se-01-p)
- **Azure OpenAI**: `oai-shared-se-01-p` with deployment `gpt-5-chat-deployment`
- **PostgreSQL**: Cloud database with `anthosks` schema

---

## URLs

- **Backend API**: https://app-anthosks-api-se-01-p.azurewebsites.net
- **Frontend UI**: https://app-anthosks-ui-se-01-p.azurewebsites.net
- **API Health**: https://app-anthosks-api-se-01-p.azurewebsites.net/

---

## Initial Setup (Already Completed)

The infrastructure has been created using Azure CLI. To recreate from scratch:

```bash
chmod +x scripts/setup_infrastructure.sh
./scripts/setup_infrastructure.sh
```

---

## Environment Variables

### Backend (app-anthosks-api-se-01-p)

| Variable | Value | Status |
|----------|-------|--------|
| `AZURE_OPENAI_ENDPOINT` | `https://oai-shared-se-01-p.openai.azure.com/` | ✅ Set |
| `AZURE_OPENAI_DEPLOYMENT` | `gpt-5-chat-deployment` | ✅ Set |
| `AZURE_OPENAI_API_VERSION` | `2024-08-01-preview` | ✅ Set |
| `AZURE_OPENAI_API_KEY` | (from shared resource) | ✅ Set |
| `DATABASE_URL` | `postgresql://...` | ⚠️ **NEEDS TO BE SET** |
| `AZURE_STORAGE_CONNECTION_STRING` | (from storage account) | ✅ Set |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | (from App Insights) | ✅ Set |
| `LOG_LEVEL` | `INFO` | ✅ Set |
| `ENABLE_CACHE` | `true` | ✅ Set |
| `LLM_TEMPERATURE` | `0.0` | ✅ Set |
| `LLM_MAX_TOKENS` | `16000` | ✅ Set |
| `CONFIDENCE_THRESHOLD` | `0.7` | ✅ Set |

### Frontend (app-anthosks-ui-se-01-p)

| Variable | Value | Status |
|----------|-------|--------|
| `VITE_API_URL` | `https://app-anthosks-api-se-01-p.azurewebsites.net` | ✅ Set |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | (from App Insights) | ✅ Set |

---

## Required Manual Steps

### 1. Add PostgreSQL Connection String

You need to add the cloud PostgreSQL `DATABASE_URL` to the backend:

```bash
az webapp config appsettings set \
  --name app-anthosks-api-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --settings DATABASE_URL="postgresql://user:password@host:port/database"
```

The schema `anthosks` will be created automatically on first connection.

### 2. Migrate Data from Dev Database

Export data from local dev database:

```bash
# From local machine
pg_dump -h localhost -U johanstromquist -d sandbox_db -n anthosks --data-only > anthosks_data.sql
```

Import to cloud database:

```bash
psql <CLOUD_POSTGRES_CONNECTION_STRING> -f anthosks_data.sql
```

### 3. Configure GitHub Secrets

For CI/CD to work, add these secrets to your GitHub repository:

1. **AZURE_CREDENTIALS**: Service Principal JSON
   ```bash
   az ad sp create-for-rbac --name "github-anthosks-deploy" \
     --role contributor \
     --scopes /subscriptions/<subscription-id>/resourceGroups/rg-sandbox-se-01-p \
     --sdk-auth
   ```
   Copy the entire JSON output to GitHub Secrets.

2. Navigate to: GitHub Repository → Settings → Secrets and variables → Actions
3. Add secret: `AZURE_CREDENTIALS` with the JSON from above

---

## Deployment Methods

### Method 1: GitHub Actions (Automatic on push to main)

Once GitHub secrets are configured:

1. Push to `main` branch
2. GitHub Actions automatically deploy:
   - Backend API when `src/**` or `requirements.txt` changes
   - Frontend UI when `frontend/**` changes

### Method 2: Manual Deployment via Azure CLI

#### Deploy Backend

```bash
# Create deployment zip (exclude unnecessary files)
zip -r backend.zip . \
  -x "frontend/*" \
  -x "*.git*" \
  -x "venv/*" \
  -x "*.pyc" \
  -x "data/*" \
  -x "references/*"

# Deploy
az webapp deploy \
  --name app-anthosks-api-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --src-path backend.zip \
  --type zip
```

#### Deploy Frontend

```bash
cd frontend
npm install
npm run build

# Create deployment zip from dist folder
cd dist
zip -r ../../frontend-dist.zip .
cd ../..

# Deploy
az webapp deploy \
  --name app-anthosks-ui-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --src-path frontend-dist.zip \
  --type zip
```

### Method 3: VS Code Azure Extension

1. Install Azure App Service extension for VS Code
2. Sign in to Azure
3. Right-click on `app-anthosks-api-se-01-p` or `app-anthosks-ui-se-01-p`
4. Select "Deploy to Web App"

---

## Monitoring & Logs

### View Application Logs

```bash
# Backend logs
az webapp log tail --name app-anthosks-api-se-01-p --resource-group rg-sandbox-se-01-p

# Frontend logs
az webapp log tail --name app-anthosks-ui-se-01-p --resource-group rg-sandbox-se-01-p
```

### Application Insights

View metrics, traces, and logs in Azure Portal:
- Navigate to: `appi-anthosks-se-01-p` → Logs/Metrics

---

## Troubleshooting

### Backend not starting

1. Check logs: `az webapp log tail --name app-anthosks-api-se-01-p --resource-group rg-sandbox-se-01-p`
2. Verify `DATABASE_URL` is set
3. Check startup script permissions: `chmod +x startup.sh`
4. Verify all environment variables are set

### Database connection issues

1. Verify PostgreSQL connection string is correct
2. Check firewall rules allow Azure services
3. Verify `anthosks` schema exists (created automatically)

### Frontend can't reach backend

1. Verify `VITE_API_URL` points to correct backend URL
2. Check CORS settings in `src/api/main.py` include frontend URL
3. Verify backend is running and accessible

---

## Cost Optimization

Current SKU: **B1 Basic**
- Estimated cost: ~$13/month for App Service Plan
- Storage: Pay-as-you-go (minimal for this app)
- App Insights: Free tier (first 5GB/month)
- PostgreSQL: Shared (cost in shared_resources RG)
- OpenAI: Pay-per-use (shared with other apps)

### To scale up:

```bash
az appservice plan update \
  --name asp-sandbox-se-01-p \
  --resource-group rg-sandbox-se-01-p \
  --sku S1  # or P1V2, P2V2, etc.
```

---

## Security

- **HTTPS Only**: Enabled by default on App Services
- **Managed Identity**: Can be enabled for passwordless Azure resource access
- **Secrets Management**: Consider Azure Key Vault for production
- **Network Security**: Currently public (consider VNet integration for production)

---

## Backup & Recovery

### Database
- Use PostgreSQL automated backups
- Export schema/data regularly:
  ```bash
  pg_dump <CONNECTION_STRING> -n anthosks > backup.sql
  ```

### Storage Account
- Enable soft delete for blob containers
- Consider geo-replication for production

---

## Next Steps

1. ✅ Infrastructure created
2. ✅ Environment variables configured (except DATABASE_URL)
3. ⚠️ Add PostgreSQL connection string to backend
4. ⚠️ Migrate data from dev database to cloud
5. ⚠️ Configure GitHub secrets for CI/CD
6. ⚠️ Test first deployment
7. ⚠️ Configure custom domain (optional)
8. ⚠️ Set up Azure AD authentication (code already prepared)
