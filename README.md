# PraisonAI Service Framework

A unified framework that turns any PraisonAI Python package into a web service on Azure using just **one file per package**.

## Features

✅ **One-file service creation** - Only an `app.py` file needed  
✅ **Azure-native** - Uses Container Apps, Blob Storage, Queue, Table Storage  
✅ **Cost-predictable** - Scale-to-zero, hard-capped replicas (£15-25/month)  
✅ **Production-ready** - Retry logic, idempotency, monitoring  
✅ **Secure** - API keys, rate limiting, CORS  
✅ **Fast** - Built with FastAPI and async/await  

## Quick Start

### Installation

```bash
# Using uv (recommended)
uv pip install praisonai-svc

# Using pip
pip install praisonai-svc
```

### Create a New Service

```bash
praisonai-svc new my-service
cd my-service
```

### Implement Your Application

Edit `app.py` - customize the job processing logic:

```python
from dotenv import load_dotenv
from praisonai_svc import ServiceApp

# Load environment variables from .env file
load_dotenv()

app = ServiceApp("My Service")

@app.job
def process_job(payload: dict) -> tuple[bytes, str, str]:
    """Process job and return file data."""
    # Your processing logic here
    title = payload.get('title', 'Untitled')
    content = f"Processed: {title}\n\nFull payload:\n{payload}"
    
    return (
        content.encode(),  # File content as bytes
        "text/plain",      # Content type
        "result.txt"       # Filename
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### Configure Environment

Create `.env`:

```bash
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING=your_connection_string
PRAISONAI_API_KEY=your_secret_key
```

### Run the Service

```bash
python app.py
```

### Test the API

```bash
# Create a job
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "My First Job", "data": "test"}}'

# Check job status (replace {job_id} with actual ID from response)
curl http://localhost:8080/jobs/{job_id}

# Get download URL
curl http://localhost:8080/jobs/{job_id}/download

# Download the result file
curl "$(curl -s http://localhost:8080/jobs/{job_id}/download | jq -r .download_url)"
```

## Local Testing

Test locally in 4 simple steps:

### 1. Install

```bash
pip install praisonai-svc
```

### 2. Create Service

```bash
praisonai-svc new my-service
cd my-service
```

### 3. Set Up Azure (Choose One)

**Option A: Local Testing (No Azure Account)**
```bash
# Install and start Azurite
npm install -g azurite
azurite --silent

# Use this in .env:
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
```

**Option B: Real Azure**
```bash
# Get from Azure Portal → Storage Account → Access Keys
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;..."
```

### 4. Run & Test

```bash
# Start service
python app.py

# Test (in another terminal)
curl http://localhost:8080/health
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "Test"}}'
```

That's it! ✅

## Architecture

```
┌─────────────┐
│  WordPress  │
│   Chatbot   │
└──────┬──────┘
       │ POST /jobs
       ▼
┌─────────────────────────────────────┐
│   Azure Container App (FastAPI)     │
│  ┌──────────┐      ┌──────────┐    │
│  │   API    │      │  Worker  │    │
│  └────┬─────┘      └─────┬────┘    │
└───────┼──────────────────┼──────────┘
        │                  │
        ▼                  ▼
   ┌─────────┐        ┌─────────┐
   │  Table  │        │  Queue  │
   │ Storage │        │ Storage │
   └─────────┘        └─────────┘
                           │
                           ▼
                      ┌─────────┐
                      │  Blob   │
                      │ Storage │
                      └─────────┘
```

## API Endpoints

| Method | Path                  | Description                    |
|--------|-----------------------|--------------------------------|
| POST   | `/jobs`               | Create new job                 |
| GET    | `/jobs/{id}`          | Get job status                 |
| GET    | `/jobs/{id}/download` | Get fresh download URL         |
| GET    | `/health`             | Health check                   |

## Configuration

All configuration via environment variables with `PRAISONAI_` prefix:

```bash
# Required
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING=...

# Optional
PRAISONAI_API_KEY=secret
PRAISONAI_CORS_ORIGINS=["https://example.com"]
PRAISONAI_MAX_JOB_DURATION_MINUTES=10
PRAISONAI_MAX_RETRY_COUNT=3
```

## Deployment

### Azure Container Apps

Quick deploy:

```bash
# Build and push image
docker build -t myregistry.azurecr.io/my-service:latest .
docker push myregistry.azurecr.io/my-service:latest

# Deploy to Azure Container Apps
az containerapp create \
  --name my-service \
  --resource-group my-rg \
  --environment my-env \
  --image myregistry.azurecr.io/my-service:latest \
  --target-port 8080 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3
```

## Security

### Official Package

⚠️ The only official package is: **praisonai-svc**

Install via:
```bash
pip install praisonai-svc
```

### Typosquatting Protection

We maintain a defensive package for common typo:
- `praisonai-svcs` (plural) → redirects to `praisonai-svc`

PyPI's built-in name similarity protection prevents other typosquatting attempts.

### Report Security Issues

GitHub Issues: https://github.com/MervinPraison/PraisonAI-SVC/issues

## Development

```bash
# Clone repository
git clone https://github.com/MervinPraison/PraisonAI-SVC.git
cd praisonai-svc

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/ --fix

# Type check
mypy src/
```

### Version Management

When incrementing the version, update these files:

1. **`pyproject.toml`** - Line 3: `version = "X.Y.Z"`
2. **`src/praisonai_svc/cli.py`** - Line 7: `@click.version_option(version="X.Y.Z")`
3. **`tests/AUTOTESTING.md`** - Lines 445-447: Update version references

**Version numbering (Semantic Versioning):**
- **Patch (X.Y.Z)** - Bug fixes only: `1.2.0` → `1.2.1`
- **Minor (X.Y.0)** - New features, backward compatible: `1.2.0` → `1.3.0`
- **Major (X.0.0)** - Breaking changes: `1.2.0` → `2.0.0`

**Example:**
```bash
# For a new feature (minor version bump)
# 1. Update pyproject.toml: version = "1.3.0"
# 2. Update cli.py: @click.version_option(version="1.3.0")
# 3. Update AUTOTESTING.md: Framework Version: 1.3.0
# 4. Commit and tag
git commit -am "Bump version to 1.3.0"
git tag v1.3.0
```

## Project Structure

```
praisonai-svc/
├── src/praisonai_svc/          # Main package
│   ├── __init__.py             # Package exports
│   ├── app.py                  # ServiceApp class
│   ├── worker.py               # Worker with exponential backoff
│   ├── cli.py                  # CLI commands
│   ├── models/                 # Data models
│   └── azure/                  # Azure integrations
├── tests/                      # Test suite (20 tests)
├── examples/                   # Example services
├── pyproject.toml              # Package configuration
├── Dockerfile                  # Container image
└── LICENSE                     # MIT License
```

## Key Features

### Core Framework
- **ServiceApp class** - FastAPI app factory
- **@app.job decorator** - Simple handler registration
- **Automatic API generation** - 4 endpoints created automatically
- **CORS middleware** - Configurable cross-origin support
- **Idempotency** - SHA256 JobHash prevents duplicate processing

### Azure Integration
- **Blob Storage** - File storage with retry logic (3 attempts)
- **Queue Storage** - Job queue with poison queue for failures
- **Table Storage** - Job state tracking with retry logic
- **SAS URLs** - On-demand secure download links (1h expiry)

### Reliability
- **Exponential backoff** - Worker polling (1s → 30s)
- **Retry logic** - Max 3 attempts before poison queue
- **Timeout detection** - 10 minute job timeout
- **Error handling** - Comprehensive error messages

### CLI Commands

#### `praisonai-svc new <name>`

**Purpose:** Create a new service from template

**Usage:**
```bash
praisonai-svc new my-service
# or with package integration
praisonai-svc new my-service --package praisonaippt
```

**What it does:**
1. Creates a new directory with your service name
2. Generates `app.py` with ServiceApp boilerplate
3. Creates `.env.example` with required configuration
4. Creates `README.md` with setup instructions
5. Generates `pyproject.toml` with dependencies

**Output:**
```
✅ Service created: my-service/
   ├── app.py
   ├── .env.example
   ├── README.md
   └── pyproject.toml
```

**Next steps after creation:**
```bash
cd my-service
cp .env.example .env
# Edit .env with your Azure credentials
# Edit app.py to implement your logic
```

---

#### `praisonai-svc run`

**Purpose:** Run the service locally for development

**Usage:**
```bash
cd my-service
praisonai-svc run
```

**What it does:**
1. Loads environment variables from `.env`
2. Starts FastAPI server on `http://localhost:8080`
3. Starts worker process for job processing
4. Enables hot-reload for development

**Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**Test it:**
```bash
# Health check
curl http://localhost:8080/health

# Create a job
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "Test"}}'
```

---

#### `praisonai-svc deploy`

**Purpose:** Deploy service to Azure Container Apps

**Usage:**
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
- Azure CLI installed: `brew install azure-cli`
- Logged in: `az login`
- Resource group and container registry created

**Output:**
```
🔨 Building Docker image...
✅ Image built: myregistry.azurecr.io/my-service:latest

📤 Pushing to Azure Container Registry...
✅ Image pushed

🚀 Deploying to Azure Container Apps...
✅ Deployed: https://my-service.azurecontainerapps.io

📊 Service URL: https://my-service.azurecontainerapps.io
```

**What happens:**
- Service is deployed with scale-to-zero (no cost when idle)
- Auto-scales based on HTTP requests (0-3 replicas)
- Environment variables from `.env` are configured
- HTTPS endpoint is automatically provisioned

---

#### `praisonai-svc logs`

**Purpose:** View real-time logs from deployed service

**Usage:**
```bash
cd my-service
praisonai-svc logs

# Follow logs (like tail -f)
praisonai-svc logs --follow

# Show last 100 lines
praisonai-svc logs --tail 100
```

**What it does:**
1. Connects to Azure Container Apps
2. Streams application logs in real-time
3. Shows both API and worker logs
4. Displays timestamps and log levels

**Output:**
```
2025-11-04 21:00:15 INFO  [API] Started server
2025-11-04 21:00:20 INFO  [API] POST /jobs - 201 Created
2025-11-04 21:00:21 INFO  [Worker] Processing job abc123
2025-11-04 21:00:25 INFO  [Worker] Job abc123 completed
2025-11-04 21:00:26 INFO  [API] GET /jobs/abc123 - 200 OK
```

**Useful for:**
- Debugging production issues
- Monitoring job processing
- Tracking API requests
- Identifying errors

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=praisonai_svc

# Run specific test file
pytest tests/test_integration.py -v
```

**Test Results:** 20/20 tests passing ✅

## Examples

See [examples/](./examples/) directory:
- `examples/ppt-service/` - PowerPoint generation example

## Documentation

- [PRD](./PRD.md) - Complete product requirements
- GitHub: https://github.com/MervinPraison/PraisonAI-SVC
- Issues: https://github.com/MervinPraison/PraisonAI-SVC/issues

## License

MIT License - see [LICENSE](./LICENSE) file

## Contributing

Contributions welcome! Please open an issue or pull request on GitHub.

## Support

- GitHub Issues: https://github.com/MervinPraison/PraisonAI-SVC/issues
- Documentation: https://mervinpraison.github.io/PraisonAI-SVC
- Website: https://praison.ai
