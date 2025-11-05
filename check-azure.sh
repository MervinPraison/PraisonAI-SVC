#!/bin/bash
# Check existing Azure resources for PraisonAI deployment

echo "🔍 Checking Azure Resources..."
echo ""

# Check if logged in
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure"
    echo "   Run: az login"
    exit 1
fi

SUBSCRIPTION=$(az account show --query name -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

echo "✅ Logged in to Azure"
echo "   Subscription: $SUBSCRIPTION"
echo "   ID: $SUBSCRIPTION_ID"
echo ""

echo "📋 Searching for existing resources in your subscription..."
echo ""

# Find ALL Resource Groups
echo "1️⃣  Resource Groups"
ALL_RGS=$(az group list --query "[].{name:name, location:location}" -o tsv)
if [ -n "$ALL_RGS" ]; then
    echo "   ✅ FOUND:"
    while IFS=$'\t' read -r rg_name rg_location; do
        echo "      - $rg_name (Location: $rg_location)"
    done <<< "$ALL_RGS"
    
    # Ask user to select or use first one
    RESOURCE_GROUP=$(echo "$ALL_RGS" | head -1 | cut -f1)
    LOCATION=$(echo "$ALL_RGS" | head -1 | cut -f2)
    echo "   📝 Will use: $RESOURCE_GROUP (Location: $LOCATION)"
    export RESOURCE_GROUP=$RESOURCE_GROUP
    export LOCATION=$LOCATION
else
    echo "   ❌ NOT FOUND"
    echo "   No resource groups exist in your subscription"
    echo "   Deployment will create a new one"
    RESOURCE_GROUP=""
    LOCATION=""
fi
echo ""

# Find ALL Container Registries
echo "2️⃣  Azure Container Registries"
ALL_ACRS=$(az acr list --query "[].{name:name, loginServer:loginServer, sku:sku.name, rg:resourceGroup}" -o tsv)
if [ -n "$ALL_ACRS" ]; then
    echo "   ✅ FOUND:"
    while IFS=$'\t' read -r acr_name acr_server acr_sku acr_rg; do
        echo "      - $acr_name"
        echo "        Server: $acr_server"
        echo "        SKU: $acr_sku"
        echo "        Resource Group: $acr_rg"
    done <<< "$ALL_ACRS"
    
    # Use first ACR
    ACR_NAME=$(echo "$ALL_ACRS" | head -1 | cut -f1)
    ACR_LOGIN_SERVER=$(echo "$ALL_ACRS" | head -1 | cut -f2)
    echo "   📝 Will use: $ACR_NAME"
    export ACR_NAME=$ACR_NAME
    export ACR_LOGIN_SERVER=$ACR_LOGIN_SERVER
else
    echo "   ❌ NOT FOUND"
    echo "   No container registries exist in your subscription"
    echo "   Deployment will create a new one"
    ACR_NAME=""
fi
echo ""

# Find ALL Container Apps Environments
echo "3️⃣  Container Apps Environments"
ALL_ENVS=$(az containerapp env list --query "[].{name:name, location:location, rg:resourceGroup}" -o tsv 2>/dev/null)
if [ -n "$ALL_ENVS" ]; then
    echo "   ✅ FOUND:"
    while IFS=$'\t' read -r env_name env_location env_rg; do
        echo "      - $env_name"
        echo "        Location: $env_location"
        echo "        Resource Group: $env_rg"
    done <<< "$ALL_ENVS"
    
    # Use first environment
    CONTAINER_ENV=$(echo "$ALL_ENVS" | head -1 | cut -f1)
    echo "   📝 Will use: $CONTAINER_ENV"
    export CONTAINER_ENV=$CONTAINER_ENV
else
    echo "   ❌ NOT FOUND"
    echo "   No container app environments exist"
    echo "   Deployment will create a new one"
    CONTAINER_ENV=""
fi
echo ""

# Find ALL Storage Accounts
echo "4️⃣  Storage Accounts"
ALL_STORAGE=$(az storage account list --query "[].{name:name, location:location, sku:sku.name, rg:resourceGroup}" -o tsv)
if [ -n "$ALL_STORAGE" ]; then
    echo "   ✅ FOUND:"
    while IFS=$'\t' read -r storage_name storage_location storage_sku storage_rg; do
        echo "      - $storage_name"
        echo "        Location: $storage_location"
        echo "        SKU: $storage_sku"
        echo "        Resource Group: $storage_rg"
    done <<< "$ALL_STORAGE"
    
    # Use first storage account
    STORAGE_ACCOUNT=$(echo "$ALL_STORAGE" | head -1 | cut -f1)
    STORAGE_RG=$(echo "$ALL_STORAGE" | head -1 | cut -f4)
    STORAGE_CONNECTION=$(az storage account show-connection-string \
        --name $STORAGE_ACCOUNT \
        --resource-group $STORAGE_RG \
        --query connectionString -o tsv)
    echo "   📝 Will use: $STORAGE_ACCOUNT"
    export STORAGE_ACCOUNT=$STORAGE_ACCOUNT
    export STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION
else
    echo "   ❌ NOT FOUND"
    echo "   Will create new storage account"
fi
echo ""

# Find ALL Container Apps
echo "5️⃣  Deployed Container Apps"
ALL_APPS=$(az containerapp list --query "[].{name:name, rg:resourceGroup}" -o tsv 2>/dev/null)
if [ -n "$ALL_APPS" ]; then
    echo "   ✅ FOUND:"
    while IFS=$'\t' read -r app_name app_rg; do
        APP_URL=$(az containerapp show --name $app_name --resource-group $app_rg --query properties.configuration.ingress.fqdn -o tsv 2>/dev/null)
        APP_STATUS=$(az containerapp show --name $app_name --resource-group $app_rg --query properties.runningStatus -o tsv 2>/dev/null)
        echo "      - $app_name (Resource Group: $app_rg)"
        if [ -n "$APP_URL" ]; then
            echo "        URL: https://$APP_URL"
            echo "        Status: $APP_STATUS"
        else
            echo "        Status: $APP_STATUS"
        fi
    done <<< "$ALL_APPS"
else
    echo "   ❌ NOT FOUND"
    echo "   No container apps deployed yet"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Count what exists
EXISTS_COUNT=0
MISSING_COUNT=0

if az group show --name $RESOURCE_GROUP &> /dev/null; then
    EXISTS_COUNT=$((EXISTS_COUNT + 1))
else
    MISSING_COUNT=$((MISSING_COUNT + 1))
fi

if az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP &> /dev/null 2>&1; then
    EXISTS_COUNT=$((EXISTS_COUNT + 1))
else
    MISSING_COUNT=$((MISSING_COUNT + 1))
fi

if [ -n "$CONTAINER_ENV" ]; then
    EXISTS_COUNT=$((EXISTS_COUNT + 1))
else
    MISSING_COUNT=$((MISSING_COUNT + 1))
fi

if [ -n "$STORAGE_ACCOUNTS" ]; then
    EXISTS_COUNT=$((EXISTS_COUNT + 1))
else
    MISSING_COUNT=$((MISSING_COUNT + 1))
fi

echo "✅ Existing resources: $EXISTS_COUNT"
echo "❌ Missing resources: $MISSING_COUNT"
echo ""

if [ $EXISTS_COUNT -eq 4 ]; then
    echo "🎉 All core resources exist! Ready for deployment."
elif [ $EXISTS_COUNT -gt 0 ]; then
    echo "⚠️  Some resources exist. Deployment will create missing ones."
else
    echo "🆕 No resources found. First deployment will create everything."
fi
echo ""

# Generate deployment command
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Suggested Deployment Command"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -n "$RESOURCE_GROUP" ] || [ -n "$ACR_NAME" ] || [ -n "$LOCATION" ]; then
    DEPLOY_CMD="praisonai-svc deploy"
    
    # Add resource group if exists
    if [ -n "$RESOURCE_GROUP" ]; then
        DEPLOY_CMD="$DEPLOY_CMD --resource-group $RESOURCE_GROUP"
    fi
    
    # Add location if exists
    if [ -n "$LOCATION" ]; then
        DEPLOY_CMD="$DEPLOY_CMD --location $LOCATION"
    fi
    
    # Add ACR name if exists
    if [ -n "$ACR_NAME" ]; then
        DEPLOY_CMD="$DEPLOY_CMD --acr-name $ACR_NAME"
    fi
    
    echo "cd your-service"
    echo "$DEPLOY_CMD"
else
    echo "cd your-service"
    echo "praisonai-svc deploy"
    echo ""
    echo "Note: No existing resources found. Deployment will use defaults."
fi
echo ""

# Show what will be used/created
echo "This will:"
if [ -n "$RESOURCE_GROUP" ] && az group show --name $RESOURCE_GROUP &> /dev/null 2>&1; then
    echo "  ✅ Use existing Resource Group: $RESOURCE_GROUP"
else
    echo "  🆕 Create new Resource Group"
fi

if [ -n "$ACR_LOGIN_SERVER" ]; then
    echo "  ✅ Use existing Container Registry: $ACR_NAME ($ACR_LOGIN_SERVER)"
else
    echo "  🆕 Create new Container Registry"
fi

if [ -n "$CONTAINER_ENV" ]; then
    echo "  ✅ Use existing Container Apps Environment: $CONTAINER_ENV"
else
    echo "  🆕 Create new Container Apps Environment"
fi

if [ -n "$STORAGE_ACCOUNT" ]; then
    echo "  ✅ Use existing Storage Account: $STORAGE_ACCOUNT"
else
    echo "  🆕 Create new Storage Account"
fi
echo ""

# Export configuration
echo "💾 Environment Variables (copy if needed):"
echo ""
echo "export RESOURCE_GROUP=\"$RESOURCE_GROUP\""
echo "export LOCATION=\"$LOCATION\""
echo "export ACR_NAME=\"$ACR_NAME\""
if [ -n "$STORAGE_ACCOUNT" ]; then
    echo "export STORAGE_ACCOUNT=\"$STORAGE_ACCOUNT\""
fi
echo ""

# Save to file
CONFIG_FILE=".azure-config"
cat > $CONFIG_FILE << EOF
# Azure Configuration for PraisonAI
# Generated: $(date)

RESOURCE_GROUP="$RESOURCE_GROUP"
LOCATION="$LOCATION"
ACR_NAME="$ACR_NAME"
EOF

if [ -n "$STORAGE_ACCOUNT" ]; then
    echo "STORAGE_ACCOUNT=\"$STORAGE_ACCOUNT\"" >> $CONFIG_FILE
fi

if [ -n "$STORAGE_CONNECTION_STRING" ]; then
    echo "STORAGE_CONNECTION_STRING=\"$STORAGE_CONNECTION_STRING\"" >> $CONFIG_FILE
fi

echo "📝 Configuration saved to: $CONFIG_FILE"
echo "   Load with: source $CONFIG_FILE"
echo ""
