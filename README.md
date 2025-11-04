# PraisonAI Service Framework

A unified framework that turns any PraisonAI Python package into a web service on Azure using just **one file per package**.

## Features

✅ **One-file service creation** - Only a `handlers.py` file needed  
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
praisonai-svc new my-service --package praisonaippt
cd my-service
```

### Implement Your Handler

Edit `handlers.py`:

```python
import io
from praisonai_svc import ServiceApp
from praisonaippt import build_ppt

app = ServiceApp("PraisonAI PPT")

@app.job
def generate_ppt(payload: dict) -> tuple[bytes, str, str]:
    """Generate PowerPoint from YAML."""
    buf = io.BytesIO()
    build_ppt(payload, out=buf)
    return (
        buf.getvalue(),
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "slides.pptx",
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app.get_app(), host="0.0.0.0", port=8080)
```

### Configure Environment

Create `.env`:

```bash
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING=your_connection_string
PRAISONAI_API_KEY=your_secret_key
```

### Run Locally

```bash
python handlers.py
```

### Test the API

```bash
# Create a job
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "My Presentation"}}'

# Check job status
curl http://localhost:8080/jobs/{job_id}

# Download result
curl http://localhost:8080/jobs/{job_id}/download
```

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

See [deployment guide](https://github.com/praisonai/praisonai-svc/blob/main/docs/deployment.md) for full instructions.

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

We maintain defensive packages for common typos:
- `praisonaisvc` → redirects to `praisonai-svc`
- `praisonai_svc` → redirects to `praisonai-svc`
- `praisonai-service` → redirects to `praisonai-svc`

### Report Security Issues

Email: security@praisonai.com

## Development

```bash
# Clone repository
git clone https://github.com/praisonai/praisonai-svc.git
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

## Examples

See [examples/](./examples/) directory for complete service implementations:

- `examples/ppt-service/` - PowerPoint generation
- `examples/video-service/` - Video generation
- `examples/wp-service/` - WordPress content generation

## Documentation

- [Full Documentation](https://docs.praisonai.com/svc)
- [API Reference](https://docs.praisonai.com/svc/api)
- [Deployment Guide](https://docs.praisonai.com/svc/deployment)
- [PRD](./PRD.md)

## License

MIT License - see [LICENSE](./LICENSE) file

## Contributing

Contributions welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md)

## Support

- GitHub Issues: https://github.com/praisonai/praisonai-svc/issues
- Documentation: https://docs.praisonai.com/svc
- Email: support@praisonai.com
