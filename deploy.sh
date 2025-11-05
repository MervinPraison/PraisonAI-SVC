#!/bin/bash
set -e

# Azure Deployment Script for PraisonAI Services
# Usage: ./deploy.sh [service-directory]

echo "🚀 PraisonAI Service Deployment"
echo ""

# Configuration
SERVICE_DIR="${1:-.}"
APP_NAME="${APP_NAME:-$(basename $(realpath $SERVICE_DIR))}"
TIMESTAMP=$(date +%s)

# Use environment variables or prompt for values
if [ -z "$RESOURCE_GROUP" ]; then
    RESOURCE_GROUP="rg-${APP_NAME}"
fi

if [ -z "$LOCATION" ]; then
    LOCATION="eastus"
fi

if [ -z "$ACR_NAME" ]; then
    ACR_NAME="acr${APP_NAME}${RANDOM}"
fi

if [ -z "$CONTAINER_ENV" ]; then
    CONTAINER_ENV="env-${APP_NAME}"
fi

IMAGE_TAG="$ACR_NAME.azurecr.io/$APP_NAME:$TIMESTAMP"

echo "📋 Configuration:"
echo "   Service: $APP_NAME"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   Registry: $ACR_NAME"
echo ""

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure"
    echo "   Run: az login"
    exit 1
fi

echo "✅ Azure CLI authenticated"
echo ""

# Check if service directory exists
if [ ! -d "$SERVICE_DIR" ]; then
    echo "❌ Service directory not found: $SERVICE_DIR"
    exit 1
fi

# Check if app.py exists
if [ ! -f "$SERVICE_DIR/app.py" ]; then
    echo "❌ app.py not found in $SERVICE_DIR"
    echo "   Create a service first: praisonai-svc new $APP_NAME"
    exit 1
fi

cd "$SERVICE_DIR"

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "📝 Creating Dockerfile..."
    cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy application files
COPY app.py .env* ./

# Install praisonai-svc
RUN uv pip install --system --no-cache praisonai-svc

# Expose port
EXPOSE 8080

# Run application
CMD ["python", "app.py"]
EOF
    echo "   ✓ Dockerfile created"
fi

# Check if resource group exists
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "📦 Creating resource group..."
    az group create --name $RESOURCE_GROUP --location $LOCATION --output none
    echo "   ✓ Resource group created"
fi

# Check if ACR exists (in any resource group)
ACR_EXISTS=$(az acr show --name $ACR_NAME --query id -o tsv 2>/dev/null)
if [ -z "$ACR_EXISTS" ]; then
    echo "📦 Creating Azure Container Registry..."
    az acr create \
        --resource-group $RESOURCE_GROUP \
        --name $ACR_NAME \
        --sku Basic \
        --admin-enabled true \
        --output none
    echo "   ✓ ACR created"
else
    ACR_RG=$(az acr show --name $ACR_NAME --query resourceGroup -o tsv)
    echo "✅ ACR already exists in resource group: $ACR_RG"
    echo "   Will use existing ACR"
fi

# Check if Container Apps environment exists
if ! az containerapp env show --name $CONTAINER_ENV --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo "📦 Creating Container Apps environment..."
    az containerapp env create \
        --name $CONTAINER_ENV \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --output none
    echo "   ✓ Environment created: $CONTAINER_ENV"
fi

# Check if storage account exists
STORAGE_ACCOUNT=$(az storage account list \
    --resource-group $RESOURCE_GROUP \
    --query "[0].name" -o tsv 2>/dev/null)

if [ -z "$STORAGE_ACCOUNT" ]; then
    echo "📦 Creating storage account..."
    # Remove hyphens and ensure lowercase for storage account name
    CLEAN_NAME=$(echo "$APP_NAME" | tr -d '-' | tr '[:upper:]' '[:lower:]')
    STORAGE_ACCOUNT="st${CLEAN_NAME}${RANDOM}"
    az storage account create \
        --name $STORAGE_ACCOUNT \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --output none
    echo "   ✓ Storage account created: $STORAGE_ACCOUNT"
fi

# Get storage connection string
STORAGE_CONNECTION=$(az storage account show-connection-string \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --query connectionString -o tsv)

# Build and push image using ACR
echo ""
echo "🔨 Building Docker image..."
az acr build \
    --registry $ACR_NAME \
    --image $APP_NAME:latest \
    --image $APP_NAME:$TIMESTAMP \
    --file Dockerfile \
    . \
    --output table

echo ""
echo "✅ Image built and pushed"

# Check if container app exists
if az containerapp show --name $APP_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
    echo ""
    echo "🔄 Updating existing container app..."
    az containerapp update \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --image $ACR_NAME.azurecr.io/$APP_NAME:latest \
        --output none
    echo "   ✓ Container app updated"
else
    echo ""
    echo "🚀 Creating new container app..."
    
    # Get ACR credentials
    ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
    ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
    
    az containerapp create \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --environment $CONTAINER_ENV \
        --image $ACR_NAME.azurecr.io/$APP_NAME:latest \
        --registry-server $ACR_NAME.azurecr.io \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --target-port 8080 \
        --ingress external \
        --min-replicas 0 \
        --max-replicas 3 \
        --env-vars \
            "PRAISONAI_AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION" \
        --cpu 0.5 \
        --memory 1.0Gi \
        --output none
    echo "   ✓ Container app created"
fi

# Get the app URL
APP_URL=$(az containerapp show \
    --name $APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn -o tsv)

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Service URL: https://$APP_URL"
echo ""
echo "Test your service:"
echo "  curl https://$APP_URL/health"
echo "  curl -X POST https://$APP_URL/jobs -H 'Content-Type: application/json' -d '{\"payload\": {\"title\": \"Test\"}}'"
echo ""
echo "View logs:"
echo "  az containerapp logs show --name $APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo ""
