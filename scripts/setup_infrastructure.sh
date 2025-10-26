#!/bin/bash
# Infrastructure setup script for AnthosKS Azure deployment
# This script creates all required Azure resources from scratch

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="rg-sandbox-se-01-p"
LOCATION="swedencentral"
STORAGE_NAME="stsandboxse01p$(openssl rand -hex 3)"
APP_PLAN="asp-sandbox-se-01-p"
BACKEND_APP="app-anthosks-api-se-01-p"
FRONTEND_APP="app-anthosks-ui-se-01-p"
APP_INSIGHTS="appi-anthosks-se-01-p"
SHARED_OPENAI_RG="rg-shared_resources-se-01-p"
SHARED_OPENAI_NAME="oai-shared-se-01-p"

echo "========================================="
echo "AnthosKS Infrastructure Setup"
echo "========================================="

# Step 1: Create Storage Account
echo ""
echo "[1/7] Creating storage account: $STORAGE_NAME"
az storage account create \
  --name "$STORAGE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false

# Create blob containers
echo "Creating blob containers..."
az storage container create --name anthosks-uploads --account-name "$STORAGE_NAME"
az storage container create --name anthosks-reports --account-name "$STORAGE_NAME"

# Step 2: Create App Service Plan
echo ""
echo "[2/7] Creating App Service Plan: $APP_PLAN"
az appservice plan create \
  --name "$APP_PLAN" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --is-linux \
  --sku B1

# Step 3: Create Backend App Service
echo ""
echo "[3/7] Creating Backend App Service: $BACKEND_APP"
az webapp create \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_PLAN" \
  --runtime "PYTHON:3.11"

# Step 4: Create Frontend App Service
echo ""
echo "[4/7] Creating Frontend App Service: $FRONTEND_APP"
az webapp create \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_PLAN" \
  --runtime "NODE:20-lts"

# Step 5: Create Application Insights
echo ""
echo "[5/7] Creating Application Insights: $APP_INSIGHTS"
az monitor app-insights component create \
  --app "$APP_INSIGHTS" \
  --location "$LOCATION" \
  --resource-group "$RESOURCE_GROUP" \
  --application-type web

# Step 6: Configure Backend Environment Variables
echo ""
echo "[6/7] Configuring Backend Environment Variables"
OPENAI_KEY=$(az cognitiveservices account keys list \
  --resource-group "$SHARED_OPENAI_RG" \
  --name "$SHARED_OPENAI_NAME" \
  --query "key1" -o tsv)

STORAGE_CONN=$(az storage account show-connection-string \
  --name "$STORAGE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query connectionString -o tsv)

APPINSIGHTS_CONN=$(az monitor app-insights component show \
  --app "$APP_INSIGHTS" \
  --resource-group "$RESOURCE_GROUP" \
  --query connectionString -o tsv)

az webapp config appsettings set \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://oai-shared-se-01-p.openai.azure.com/" \
    AZURE_OPENAI_DEPLOYMENT="gpt-5-chat-deployment" \
    AZURE_OPENAI_API_VERSION="2024-08-01-preview" \
    AZURE_OPENAI_API_KEY="$OPENAI_KEY" \
    AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONN" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="$APPINSIGHTS_CONN" \
    LOG_LEVEL="INFO" \
    ENABLE_CACHE="true" \
    LLM_TEMPERATURE="0.0" \
    LLM_MAX_TOKENS="16000" \
    CONFIDENCE_THRESHOLD="0.7" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"

# Step 7: Configure Frontend Environment Variables
echo ""
echo "[7/7] Configuring Frontend Environment Variables"
az webapp config appsettings set \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --settings \
    VITE_API_URL="https://$BACKEND_APP.azurewebsites.net" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="$APPINSIGHTS_CONN"

echo ""
echo "========================================="
echo "Infrastructure Setup Complete!"
echo "========================================="
echo ""
echo "Resources Created:"
echo "  Storage Account: $STORAGE_NAME"
echo "  App Service Plan: $APP_PLAN"
echo "  Backend App: https://$BACKEND_APP.azurewebsites.net"
echo "  Frontend App: https://$FRONTEND_APP.azurewebsites.net"
echo "  App Insights: $APP_INSIGHTS"
echo ""
echo "Next Steps:"
echo "  1. Add DATABASE_URL to backend app settings"
echo "  2. Deploy backend code"
echo "  3. Deploy frontend code"
echo ""
