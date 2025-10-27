#!/bin/bash
# Script to configure GitHub Actions secret for Azure deployment
# This script requires Azure AD admin permissions

set -e

echo "=== GitHub Actions Azure Credentials Setup ==="
echo ""

# Service principal details
APP_ID="4801c432-e001-4060-83a3-f8dfb0d73af0"
SP_NAME="github-actions-anthosks"

echo "Service Principal: $SP_NAME"
echo "App ID: $APP_ID"
echo ""

# Check if service principal exists
echo "Checking service principal..."
SP_EXISTS=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[].appId" -o tsv)

if [ -z "$SP_EXISTS" ]; then
    echo "ERROR: Service principal does not exist!"
    echo "Please create it first with:"
    echo "  az ad sp create --id $APP_ID"
    exit 1
fi

echo "✓ Service principal found"
echo ""

# Reset credentials to get a new client secret
echo "Resetting credentials to generate new client secret..."
CREDENTIALS=$(az ad sp credential reset --id $APP_ID --output json)

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to reset credentials. You may need admin permissions."
    exit 1
fi

echo "✓ Credentials reset successfully"
echo ""

# Extract values
CLIENT_ID=$(echo $CREDENTIALS | jq -r '.appId')
CLIENT_SECRET=$(echo $CREDENTIALS | jq -r '.password')
TENANT_ID=$(echo $CREDENTIALS | jq -r '.tenant')
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create the GitHub secret JSON
cat > /tmp/azure-credentials.json <<EOF
{
  "clientId": "$CLIENT_ID",
  "clientSecret": "$CLIENT_SECRET",
  "subscriptionId": "$SUBSCRIPTION_ID",
  "tenantId": "$TENANT_ID",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
EOF

echo "Credentials created:"
echo "  Client ID: $CLIENT_ID"
echo "  Tenant ID: $TENANT_ID"
echo "  Subscription ID: $SUBSCRIPTION_ID"
echo "  Client Secret: [HIDDEN]"
echo ""

# Check role assignments
echo "Checking role assignments..."
ROLES=$(az role assignment list --assignee $APP_ID --query "[].{role:roleDefinitionName, scope:scope}" -o table)

if [ -z "$ROLES" ]; then
    echo "⚠ WARNING: No role assignments found!"
    echo "Adding Contributor role to resource group..."

    az role assignment create \
        --assignee $APP_ID \
        --role "Contributor" \
        --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/rg-sandbox-se-01-p"

    echo "✓ Contributor role assigned"
else
    echo "✓ Role assignments:"
    echo "$ROLES"
fi
echo ""

# Set GitHub secret
echo "Setting GitHub secret..."
if ! command -v gh &> /dev/null; then
    echo "⚠ WARNING: GitHub CLI (gh) not found"
    echo ""
    echo "Please install GitHub CLI or manually add the secret:"
    echo "1. Go to: https://github.com/SSI-Strategy/anthosks/settings/secrets/actions"
    echo "2. Click 'New repository secret'"
    echo "3. Name: AZURE_CREDENTIALS"
    echo "4. Value: Copy from /tmp/azure-credentials.json"
    echo ""
    echo "Credentials saved to: /tmp/azure-credentials.json"
else
    gh secret set AZURE_CREDENTIALS --repo SSI-Strategy/anthosks < /tmp/azure-credentials.json
    echo "✓ GitHub secret 'AZURE_CREDENTIALS' configured"

    # Clean up
    rm /tmp/azure-credentials.json
    echo "✓ Temporary credentials file removed"
fi

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Test the deployment with:"
echo "  cd /Users/johanstromquist/Dropbox/Coding/AnthosKS"
echo "  echo 'test' >> README.md"
echo "  git add README.md && git commit -m 'Test deployment' && git push"
echo "  gh run watch --repo SSI-Strategy/anthosks"
echo ""
