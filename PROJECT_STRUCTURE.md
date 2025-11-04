# PraisonAI Service Framework - Project Structure

## Directory Tree

```
praisonai-svc/
├── src/praisonai_svc/           # Main package source
│   ├── __init__.py              # Package exports
│   ├── app.py                   # ServiceApp class (FastAPI app factory)
│   ├── worker.py                # Worker with exponential backoff
│   ├── cli.py                   # CLI commands (new, run, deploy, logs)
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── job.py               # Job models (JobRequest, JobResponse, JobEntity)
│   │   └── config.py            # ServiceConfig (Pydantic settings)
│   └── azure/                   # Azure integrations
│       ├── __init__.py
│       ├── blob.py              # BlobStorage with retry logic
│       ├── queue.py             # QueueManager
│       └── table.py             # TableStorage with retry logic
├── examples/                    # Example services
│   └── ppt-service/
│       ├── handlers.py          # Example PPT handler
│       └── .env.example         # Environment configuration template
├── tests/                       # Test suite (to be created)
├── defensive-packages/          # Typosquatting protection packages
├── docker/                      # Docker configurations
├── pyproject.toml               # Project metadata and dependencies
├── Dockerfile                   # Container image definition
├── README.md                    # Main documentation
├── PRD.md                       # Product Requirements Document
└── PROJECT_STRUCTURE.md         # This file

```

## Core Modules

### 1. `app.py` - ServiceApp Class
**Purpose:** Main application factory for creating PraisonAI services

**Key Features:**
- FastAPI app initialization
- CORS middleware setup
- API endpoints (`/jobs`, `/jobs/{id}`, `/jobs/{id}/download`, `/health`)
- Job handler registration via `@app.job` decorator
- Idempotency check (JobHash)
- Azure client initialization

**Usage:**
```python
from praisonai_svc import ServiceApp

app = ServiceApp("My Service")

@app.job
def process(payload: dict) -> tuple[bytes, str, str]:
    return file_data, content_type, filename
```

### 2. `worker.py` - Job Worker
**Purpose:** Background worker for processing jobs from queue

**Key Features:**
- Exponential backoff polling (1s → 30s)
- Retry logic with poison queue
- Timeout detection (10 min default)
- Blob upload with retry
- Job status updates

**Flow:**
1. Poll queue with backoff
2. Check dequeue count (max 3 retries)
3. Update status to "processing"
4. Execute job handler
5. Upload to blob storage
6. Generate SAS URL
7. Update status to "done"

### 3. `cli.py` - Command Line Interface
**Commands:**
- `praisonai-svc new <name>` - Create new service from template
- `praisonai-svc run` - Run service locally
- `praisonai-svc deploy` - Deploy to Azure (coming soon)
- `praisonai-svc logs` - Tail logs (coming soon)

### 4. `models/` - Data Models

#### `job.py`
- `JobStatus` - Enum (queued, processing, done, error)
- `JobRequest` - API request model with `compute_hash()`
- `JobResponse` - API response model
- `JobEntity` - Table Storage entity

#### `config.py`
- `ServiceConfig` - Pydantic settings from environment variables
- Prefix: `PRAISONAI_`
- Validates and provides defaults

### 5. `azure/` - Azure Integrations

#### `blob.py` - BlobStorage
- `upload_blob()` - Upload with 3 retries (exponential backoff)
- `generate_sas_url()` - Create signed URL (1h expiry)
- `delete_blob()` - Clean up old files

#### `queue.py` - QueueManager
- `enqueue_job()` - Add job to queue
- `receive_messages()` - Poll for messages
- `delete_message()` - Remove processed message
- `move_to_poison_queue()` - Handle failed jobs
- `get_queue_length()` - Monitor queue depth

#### `table.py` - TableStorage
- `create_job()` - Create job entity with retry
- `get_job()` - Fetch job by ID with retry
- `update_job()` - Update status/URL/error with retry
- `find_job_by_hash()` - Idempotency check

## Configuration

All configuration via environment variables with `PRAISONAI_` prefix:

### Required
- `PRAISONAI_AZURE_STORAGE_CONNECTION_STRING` - Azure Storage connection string

### Optional (with defaults)
- `PRAISONAI_API_KEY` - API authentication key
- `PRAISONAI_CORS_ORIGINS` - Allowed origins (default: ["*"])
- `PRAISONAI_MAX_JOB_DURATION_MINUTES` - Job timeout (default: 10)
- `PRAISONAI_MAX_RETRY_COUNT` - Max retries before poison queue (default: 3)
- `PRAISONAI_QUEUE_VISIBILITY_TIMEOUT` - Queue message visibility (default: 60s)
- `PRAISONAI_WORKER_POLL_INTERVAL_MIN` - Min backoff (default: 1s)
- `PRAISONAI_WORKER_POLL_INTERVAL_MAX` - Max backoff (default: 30s)

## API Endpoints

| Method | Path                  | Description                                      |
|--------|-----------------------|--------------------------------------------------|
| POST   | `/jobs`               | Create job (returns job_id)                      |
| GET    | `/jobs/{id}`          | Get job status                                   |
| GET    | `/jobs/{id}/download` | Generate fresh SAS URL (on-demand)               |
| GET    | `/health`             | Health check                                     |

## Job Flow

```
1. Client → POST /jobs
   ↓
2. API validates payload (Pydantic)
   ↓
3. Check for duplicate (JobHash)
   ↓
4. Create job entity in Table Storage (status: queued)
   ↓
5. Enqueue message to Queue Storage
   ↓
6. Return job_id to client
   ↓
7. Worker polls queue (exponential backoff)
   ↓
8. Worker receives message
   ↓
9. Update status to "processing"
   ↓
10. Execute job handler
   ↓
11. Upload result to Blob Storage
   ↓
12. Generate SAS URL
   ↓
13. Update status to "done" with download_url
   ↓
14. Delete message from queue
   ↓
15. Client → GET /jobs/{id}/download
   ↓
16. Generate fresh SAS URL (1h expiry)
   ↓
17. Return download URL
```

## Error Handling

### Retry Logic
- **Blob upload**: 3 retries with exponential backoff (1s → 3s → 9s)
- **Table operations**: 3 retries with exponential backoff
- **Queue messages**: Visibility timeout 60s, max 3 dequeues

### Failure Scenarios
| Failure | Detection | Mitigation |
|---------|-----------|------------|
| Worker crash | Visibility timeout expires | Message reappears, retry |
| Job timeout | StartedUTC + 10min | Mark as error, move to poison queue |
| Duplicate job | JobHash match | Return existing result |
| Blob upload fail | Exception | Retry 3x, then error |
| Max retries | dequeue_count > 3 | Move to poison queue |

### Poison Queue
- Failed jobs after 3 retries
- Manual review required
- Alert when length > 5

## Idempotency

Jobs are idempotent via `JobHash` (SHA256 of payload):
1. Before creating job, check if JobHash exists
2. If exists and status="done", return existing result
3. If exists and status="processing", return existing job_id
4. Prevents duplicate processing on retry

## Dependencies

### Core
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `azure-storage-blob` - Blob storage
- `azure-storage-queue` - Queue storage
- `azure-data-tables` - Table storage
- `tenacity` - Retry logic
- `click` - CLI framework

### Dev
- `pytest` - Testing
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking

## Development Workflow

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/ --fix

# Type check
mypy src/

# Run locally
python examples/ppt-service/handlers.py
```

## Deployment

### Docker Build
```bash
docker build -t praisonai-svc:latest .
```

### Azure Container Apps
```bash
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

## Next Steps

1. ✅ Core framework implemented
2. ⏳ Create defensive packages
3. ⏳ Write comprehensive tests
4. ⏳ Add deployment automation
5. ⏳ Create more examples (video, wp)
6. ⏳ Add monitoring/alerting
7. ⏳ Publish to PyPI

## Security

### Package Protection
- Main package: `praisonai-svc`
- Defensive packages: `praisonaisvc`, `praisonai_svc`, `praisonai-service`
- All defensive packages redirect to main package

### API Security
- API key authentication (optional)
- CORS configuration
- Rate limiting (Table Storage-based)
- Input validation (Pydantic)
- Max payload size (1MB default)

## Support

- GitHub: https://github.com/praisonai/praisonai-svc
- Documentation: https://docs.praisonai.com/svc
- Email: support@praisonai.com
