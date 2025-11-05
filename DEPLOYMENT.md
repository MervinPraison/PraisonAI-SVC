# Azure Deployment Guide - Step by Step

This guide documents the **exact commands** used to successfully deploy a PraisonAI service to Azure Container Apps.

---

## Prerequisites

```bash
# 1. Install Azure CLI (one-time)
brew install azure-cli

# 2. Login to Azure
az login
# Opens browser, login with your Microsoft account
```

**That's all you need!** ✅

---

## Deployment Method 1: Using praisonai-svc CLI (Recommended)

### Step 1: Check Existing Azure Resources

```bash
# Run the check script to see what you already have
./check-azure.sh
```

**Output shows:**
- All your resource groups
- All your container registries
- All your storage accounts
- All your container apps
- **Suggested deployment command** with your actual resource names

### Step 2: Deploy Using Suggested Command

The check script will output something like:

```bash
cd your-service
praisonai-svc deploy --resource-group YOUR-RG --location YOUR-LOCATION --acr-name YOUR-ACR
```

**Example from our test:**
```bash
cd /path/to/your-service
praisonai-svc deploy --resource-group my-resource-group --location eastus --acr-name myregistry
```

### Step 3: Wait for Deployment

The deployment takes ~5-10 minutes and will:
1. ✅ Check Azure CLI authentication
2. ✅ Use existing Resource Group (or create new)
3. ✅ Use existing Container Registry (or create new)
4. ✅ Create Container Apps Environment
5. ✅ Use existing Storage Account (or create new)
6. ✅ Build Docker image using `az acr build`
7. ✅ Deploy to Azure Container Apps
8. ✅ Return your service URL

### Step 4: Test Your Deployed Service

```bash
# Get the URL from deployment output, then:

# Health check
curl https://YOUR-APP.azurecontainerapps.io/health

# Create a job
curl -X POST https://YOUR-APP.azurecontainerapps.io/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "Test Job"}}'

# Check job status (use job_id from previous response)
curl https://YOUR-APP.azurecontainerapps.io/jobs/{job_id}
```

**Example from our test:**
```bash
# Health check
curl https://my-service.randomstring.eastus.azurecontainerapps.io/health
# Output: {"status":"healthy","service":"my-service"}

# Create job
curl -X POST https://my-service.randomstring.eastus.azurecontainerapps.io/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "Test Job"}}'
# Output: {"job_id":"abc123...","status":"queued",...}

# Check status after 10 seconds
curl https://my-service.randomstring.eastus.azurecontainerapps.io/jobs/abc123...
# Output: {"job_id":"...","status":"done",...}
```

✅ **Job processed successfully in ~14 seconds!**

---

## Deployment Method 2: Using deploy.sh Script Directly

### Step 1: Set Environment Variables (Optional)

```bash
# If you want to use specific resources, set these:
export RESOURCE_GROUP="my-resource-group"
export LOCATION="eastus"
export ACR_NAME="myregistry"
export CONTAINER_ENV="my-environment"

# Otherwise, script will auto-detect or create new ones
```

### Step 2: Run Deploy Script

```bash
cd your-service
/path/to/praisonai-svc/deploy.sh
```

The script will:
- Use environment variables if set
- Otherwise, auto-detect existing resources
- Create new resources with names based on your service name

---

## Complete Command History (What We Actually Ran)

### Initial Setup

```bash
# 1. Already logged in to Azure
az login
# ✅ Logged in to Azure

# 2. Check existing resources
./check-azure.sh
# Found:
# - Resource Groups: my-rg-1, my-rg-2, etc.
# - Container Registry: myregistry (in my-rg-1)
# - Storage Accounts: mystorage1, mystorage2, etc.
# - Container Apps: None
```

### Deployment

```bash
# 3. Navigate to service directory
cd /path/to/your-service

# 4. Deploy using detected resources
praisonai-svc deploy --resource-group my-resource-group --location eastus --acr-name myregistry

# Deployment process:
# ✅ Azure CLI authenticated
# ✅ ACR already exists in resource group: my-rg-1 (reused!)
# 📦 Creating Container Apps environment... (created: env-my-service)
# 📦 Creating storage account... (created: stmyservice12345)
# 🔨 Building Docker image... (built and pushed to myregistry.azurecr.io)
# 🚀 Creating new container app... (created: my-service)
# ✅ Deployment complete!
# 🌐 Service URL: https://my-service.randomstring.eastus.azurecontainerapps.io
```

### Testing

```bash
# 5. Test health endpoint
curl https://my-service.randomstring.eastus.azurecontainerapps.io/health
# {"status":"healthy","service":"my-service"}

# 6. Create a job
curl -X POST https://my-service.randomstring.eastus.azurecontainerapps.io/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "Test Job"}}'
# {"job_id":"abc123...","status":"queued",...}

# 7. Wait 10 seconds and check status
sleep 10
curl https://my-service.randomstring.eastus.azurecontainerapps.io/jobs/abc123...
# {"job_id":"...","status":"done","download_url":"https://...",...}
```

✅ **Success! Job processed in ~14 seconds**

---

## What Gets Created

### First Deployment:

If you have **no existing resources**, the script creates:

1. **Resource Group**: `rg-{service-name}`
2. **Container Registry**: `acr{service-name}{random}`
3. **Container Apps Environment**: `env-{service-name}`
4. **Storage Account**: `st{service-name}{random}`
5. **Container App**: `{service-name}`

### Subsequent Deployments:

The script **reuses existing resources**:
- ✅ Existing Resource Groups
- ✅ Existing Container Registries
- ✅ Existing Storage Accounts
- ✅ Existing Container Apps Environments

Only creates what's missing!

---

## Resource Naming Conventions

The scripts use these patterns:

| Resource Type | Pattern | Example |
|--------------|---------|---------|
| Resource Group | `rg-{service}` | `rg-myservice` |
| Container Registry | `acr{service}{random}` | `acrmyservice12345` |
| Container Apps Environment | `env-{service}` | `env-myservice` |
| Storage Account | `st{service}{random}` | `stmyservice5018` |
| Container App | `{service}` | `myservice` |

**Note:** Storage account names have hyphens removed and are lowercase only (Azure requirement).

---

## Monitoring Your Deployment

### View Logs

```bash
# Stream live logs
az containerapp logs show \
  --name YOUR-APP-NAME \
  --resource-group YOUR-RESOURCE-GROUP \
  --follow

# Example:
az containerapp logs show \
  --name my-service \
  --resource-group my-resource-group \
  --follow
```

### Check App Status

```bash
# Get running status
az containerapp show \
  --name YOUR-APP-NAME \
  --resource-group YOUR-RESOURCE-GROUP \
  --query properties.runningStatus

# List all revisions
az containerapp revision list \
  --name YOUR-APP-NAME \
  --resource-group YOUR-RESOURCE-GROUP
```

### View in Azure Portal

1. Go to: https://portal.azure.com
2. Navigate to: Resource Groups → Your RG → Container Apps
3. Click on your app to see:
   - Metrics
   - Logs
   - Revisions
   - Configuration

---

## Cost Information

### Expected Costs (with scale-to-zero):

- **When idle**: £0 (scales to zero)
- **Light usage**: £5-10/month
- **Moderate usage**: £10-20/month

### Resources Created:

| Resource | SKU | Cost |
|----------|-----|------|
| Container Apps Environment | Consumption | ~£0.50/month base |
| Container App | 0.5 vCPU, 1GB RAM | £0 when scaled to zero |
| Container Registry | Basic | ~£4/month |
| Storage Account | Standard LRS | ~£1/month |

**Total: ~£5-15/month** with scale-to-zero enabled

### Cost Optimization Tips:

1. ✅ **Scale to zero** - Already configured (`--min-replicas 0`)
2. ✅ **Right-size resources** - Start with 0.5 CPU / 1GB RAM
3. ✅ **Monitor usage** - Check Azure Cost Management weekly
4. ✅ **Delete unused resources** - Remove test deployments

---

## Troubleshooting

### Issue: "ACR name already in use"

**Problem:** Container registry name must be globally unique.

**Solution:** The deploy script now checks if ACR exists in ANY resource group and reuses it:
```bash
# Script automatically detects and reuses existing ACR
✅ ACR already exists in resource group: my-rg-1
   Will use existing ACR
```

### Issue: "Storage account name invalid"

**Problem:** Storage account names can't have hyphens or uppercase letters.

**Solution:** Script now automatically cleans names:
```bash
# Removes hyphens and converts to lowercase
CLEAN_NAME=$(echo "$APP_NAME" | tr -d '-' | tr '[:upper:]' '[:lower:]')
STORAGE_ACCOUNT="st${CLEAN_NAME}${RANDOM}"
```

### Issue: "Container won't start"

**Check logs:**
```bash
az containerapp logs show \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --tail 100
```

**Common causes:**
- Missing environment variables
- Port mismatch (should be 8080)
- Image build failed

### Issue: "Jobs stay queued"

**Check:**
1. Storage connection string is set
2. Worker is running (check logs for "Worker started")
3. Queue visibility timeout (should be 5 seconds)

**Test locally first:**
```bash
cd your-service
cp .env.example .env
python app.py
# Test locally before deploying
```

---

## Redeployment / Updates

### Update Existing Service

```bash
# Just run deploy again - it will update the existing container app
cd your-service
praisonai-svc deploy --resource-group YOUR-RG --acr-name YOUR-ACR

# Or use the script directly
./deploy.sh
```

The script automatically:
- Builds new image with timestamp tag
- Updates the container app with new image
- Keeps the same URL

### Rollback to Previous Version

```bash
# List revisions
az containerapp revision list \
  --name YOUR-APP \
  --resource-group YOUR-RG

# Activate previous revision
az containerapp revision activate \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --revision REVISION-NAME
```

---

## GitHub Actions (CI/CD)

### Step 1: Create Service Principal

```bash
# Get your subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Create service principal
az ad sp create-for-rbac \
  --name "github-deploy-$(date +%s)" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID \
  --sdk-auth
```

Copy the JSON output.

### Step 2: Add GitHub Secrets

Go to: GitHub Repo → Settings → Secrets and variables → Actions

Add these secrets:
- `AZURE_CREDENTIALS` - The JSON from step 1
- `RESOURCE_GROUP` - Your resource group name
- `ACR_NAME` - Your container registry name
- `APP_NAME` - Your app name

### Step 3: Create Workflow File

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Azure Login
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Build and Deploy
      run: |
        # Build image
        az acr build \
          --registry ${{ secrets.ACR_NAME }} \
          --image ${{ secrets.APP_NAME }}:${{ github.sha }} \
          --image ${{ secrets.APP_NAME }}:latest \
          .
        
        # Update container app
        az containerapp update \
          --name ${{ secrets.APP_NAME }} \
          --resource-group ${{ secrets.RESOURCE_GROUP }} \
          --image ${{ secrets.ACR_NAME }}.azurecr.io/${{ secrets.APP_NAME }}:latest
    
    - name: Get URL
      run: |
        URL=$(az containerapp show \
          --name ${{ secrets.APP_NAME }} \
          --resource-group ${{ secrets.RESOURCE_GROUP }} \
          --query properties.configuration.ingress.fqdn -o tsv)
        echo "Deployed to: https://$URL"
```

### Step 4: Push and Deploy

```bash
git add .github/workflows/deploy.yml
git commit -m "Add Azure deployment workflow"
git push origin main
```

GitHub Actions will automatically deploy on every push to main!

---

## Best Practices

1. ✅ **Test locally first** - Always run `python app.py` before deploying
2. ✅ **Use check-azure.sh** - See what resources you have before deploying
3. ✅ **Reuse resources** - Don't create new ACR/Storage for every service
4. ✅ **Monitor costs** - Set up Azure budget alerts
5. ✅ **Use GitHub Actions** - Automate deployments for production
6. ✅ **Tag images** - Use git SHA or version numbers
7. ✅ **Scale to zero** - Save money when not in use
8. ✅ **Check logs** - Monitor for errors after deployment

---

## Quick Reference

### Check Resources
```bash
./check-azure.sh
```

### Deploy Service
```bash
cd your-service
praisonai-svc deploy --resource-group RG --acr-name ACR
```

### View Logs
```bash
az containerapp logs show --name APP --resource-group RG --follow
```

### Test Service
```bash
curl https://YOUR-APP.azurecontainerapps.io/health
```

### Delete Service
```bash
az containerapp delete --name APP --resource-group RG --yes
```

### Delete All Resources
```bash
az group delete --name RG --yes
```

---

## Support

- **Azure Container Apps Docs**: https://learn.microsoft.com/azure/container-apps/
- **GitHub Issues**: https://github.com/MervinPraison/PraisonAI-SVC/issues
- **Azure Support**: https://azure.microsoft.com/support/

---

## Summary

**Minimum requirement:** Just `az login` ✅

**Deployment time:** ~5-10 minutes

**Cost:** ~£5-15/month with scale-to-zero

**Commands:**
```bash
# 1. Check resources
./check-azure.sh

# 2. Deploy
cd your-service
praisonai-svc deploy --resource-group YOUR-RG --acr-name YOUR-ACR

# 3. Test
curl https://YOUR-APP.azurecontainerapps.io/health
```

**That's it!** 🚀
