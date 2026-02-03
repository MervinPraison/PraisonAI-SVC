# CLI Commands

Command-line tools for service creation, running, and deployment.

## Overview

PraisonAI-SVC provides CLI commands for the complete service lifecycle.

## praisonai-svc new

**Purpose:** Create a new service from template

```bash
praisonai-svc new my-service
# or with package integration
praisonai-svc new my-service --package praisonaippt
```

**What it creates:**

```
my-service/
├── app.py          # ServiceApp boilerplate
├── .env.example    # Required configuration
├── README.md       # Setup instructions
└── pyproject.toml  # Dependencies
```

**Next steps:**
```bash
cd my-service
cp .env.example .env
# Edit .env with your Azure credentials
# Edit app.py to implement your logic
```

## praisonai-svc run

**Purpose:** Run the service locally for development

```bash
cd my-service
praisonai-svc run
```

**What it does:**
1. Loads environment variables from `.env`
2. Starts FastAPI server on `http://localhost:8080`
3. Starts worker process for job processing
4. Enables hot-reload for development

**Test it:**
```bash
# Health check
curl http://localhost:8080/health

# Create a job
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "Test"}}'
```

## praisonai-svc deploy

**Purpose:** Deploy service to Azure Container Apps

```bash
cd my-service
praisonai-svc deploy
```

**What it does:**
1. Validates Azure CLI is installed and authenticated
2. Builds Docker image from your service
3. Pushes image to Azure Container Registry
4. Creates/updates Azure Container App
5. Configures environment variables
6. Sets up scaling rules (min 0, max 3 replicas)

**Prerequisites:**
- Azure CLI: `brew install azure-cli`
- Logged in: `az login`
- Resource group and container registry created

## praisonai-svc logs

**Purpose:** View real-time logs from deployed service

```bash
cd my-service
praisonai-svc logs

# Follow logs (like tail -f)
praisonai-svc logs --follow

# Show last 100 lines
praisonai-svc logs --tail 100
```

**Useful for:**
- Debugging production issues
- Monitoring job processing
- Tracking API requests
- Identifying errors
