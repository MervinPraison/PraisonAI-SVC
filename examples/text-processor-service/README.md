# Text Processor Service

A complete example application demonstrating the PraisonAI Service Framework. This service processes text input with various operations and returns formatted results.

## Features

- ✅ Multiple text operations (uppercase, lowercase, reverse, statistics)
- ✅ Multiple output formats (TXT, JSON, Markdown)
- ✅ Complete job workflow (create → process → download)
- ✅ Error handling and validation
- ✅ Production-ready configuration

## Quick Start

### 1. Install Dependencies

```bash
# Install praisonai-svc
pip install praisonai-svc

# Install python-dotenv for environment management
pip install python-dotenv
```

### 2. Setup Azure Storage

**Option A: Local Testing (Recommended for development)**

```bash
# Install Azurite (Azure Storage Emulator)
npm install -g azurite

# Start Azurite in a separate terminal
azurite --silent
```

**Option B: Use Real Azure Storage**

1. Create a Storage Account in Azure Portal
2. Get the connection string from Access Keys section

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env if needed (defaults work with Azurite)
```

### 4. Run the Service

```bash
python app.py
```

You should see:
```
🚀 Starting Text Processor Service...
📝 Service URL: http://localhost:8080
💡 Use POST /jobs to create jobs
❤️  Use GET /health for health check
✅ Worker started for Text Processor Service
✅ API server starting on http://0.0.0.0:8080
```

## API Usage

### Health Check

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "service": "Text Processor Service"
}
```

### Create a Job

**Example 1: Get Text Statistics (TXT format)**

```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "text": "Hello World! This is a test of the text processor service.",
      "operation": "stats",
      "format": "txt"
    }
  }'
```

**Example 2: All Operations (JSON format)**

```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "text": "The Quick Brown Fox Jumps Over The Lazy Dog",
      "operation": "all",
      "format": "json"
    }
  }'
```

**Example 3: Uppercase Transformation (Markdown format)**

```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "text": "convert this text to uppercase",
      "operation": "uppercase",
      "format": "md"
    }
  }'
```

Response:
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "queued",
  "created_at": "2025-11-18T12:00:00Z",
  "updated_at": "2025-11-18T12:00:00Z"
}
```

### Check Job Status

```bash
# Replace {job_id} with actual job ID from create response
curl http://localhost:8080/jobs/{job_id}
```

Response:
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "done",
  "created_at": "2025-11-18T12:00:00Z",
  "updated_at": "2025-11-18T12:00:05Z",
  "blob_name": "results/abc123-def456-ghi789.txt",
  "download_url": null
}
```

Status values:
- `queued` - Job created, waiting to be processed
- `processing` - Job is currently being processed
- `done` - Job completed successfully
- `failed` - Job failed with error

### Get Download URL

```bash
curl http://localhost:8080/jobs/{job_id}/download
```

Response:
```json
{
  "download_url": "https://127.0.0.1:10000/devstoreaccount1/results/abc123-def456-ghi789.txt?sig=..."
}
```

### Download Result File

```bash
# Get the download URL and download the file
DOWNLOAD_URL=$(curl -s http://localhost:8080/jobs/{job_id}/download | jq -r .download_url)
curl "$DOWNLOAD_URL" -o result.txt

# View the result
cat result.txt
```

## Supported Operations

| Operation | Description | Example Output |
|-----------|-------------|----------------|
| `uppercase` | Convert text to uppercase | `HELLO WORLD` |
| `lowercase` | Convert text to lowercase | `hello world` |
| `reverse` | Reverse the text | `dlroW olleH` |
| `title` | Convert to title case | `Hello World` |
| `stats` | Calculate text statistics | Word count, character count, etc. |
| `count_vowels` | Count vowels in text | Number of vowels |
| `all` | All operations combined | All transformations |

## Supported Output Formats

| Format | Content Type | Description |
|--------|--------------|-------------|
| `txt` | text/plain | Plain text with formatted sections |
| `json` | application/json | Structured JSON output |
| `md` | text/markdown | Markdown formatted with headers |

## Testing with Different Inputs

### Test 1: Long Text Processing

```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "text": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.",
      "operation": "stats",
      "format": "json"
    }
  }'
```

### Test 2: Special Characters

```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "text": "Hello! @User123 #Testing $100 50% complete...",
      "operation": "all",
      "format": "md"
    }
  }'
```

### Test 3: Multi-line Text

```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "text": "Line 1: First line\nLine 2: Second line\nLine 3: Third line",
      "operation": "stats",
      "format": "txt"
    }
  }'
```

## Complete Workflow Example

```bash
#!/bin/bash

# 1. Health check
echo "1. Checking service health..."
curl http://localhost:8080/health
echo -e "\n"

# 2. Create job
echo "2. Creating job..."
RESPONSE=$(curl -s -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "text": "Testing the PraisonAI Service Framework!",
      "operation": "all",
      "format": "json"
    }
  }')
echo $RESPONSE | jq .
JOB_ID=$(echo $RESPONSE | jq -r .job_id)
echo "Job ID: $JOB_ID"
echo -e "\n"

# 3. Wait for processing
echo "3. Waiting for job to complete..."
sleep 3

# 4. Check status
echo "4. Checking job status..."
curl -s http://localhost:8080/jobs/$JOB_ID | jq .
echo -e "\n"

# 5. Get download URL
echo "5. Getting download URL..."
DOWNLOAD_RESPONSE=$(curl -s http://localhost:8080/jobs/$JOB_ID/download)
echo $DOWNLOAD_RESPONSE | jq .
DOWNLOAD_URL=$(echo $DOWNLOAD_RESPONSE | jq -r .download_url)
echo -e "\n"

# 6. Download result
echo "6. Downloading result..."
curl -s "$DOWNLOAD_URL" -o result.json
echo "Result saved to result.json"
cat result.json | jq .
```

## Architecture

This service uses the PraisonAI Service Framework which provides:

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /jobs
       ▼
┌─────────────────────────────────────┐
│   FastAPI Application (app.py)      │
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

## Error Handling

The service validates input and returns appropriate errors:

```bash
# Missing text
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"operation": "uppercase"}}'
# Returns: ValueError: Text is required in payload

# Invalid job ID
curl http://localhost:8080/jobs/invalid-id
# Returns: 404 Job not found

# Download before completion
curl http://localhost:8080/jobs/{queued_job_id}/download
# Returns: 400 Job not ready for download
```

## Configuration

All configuration is done through environment variables in `.env`:

- `PRAISONAI_AZURE_STORAGE_CONNECTION_STRING` - Azure Storage connection string (required)
- `PRAISONAI_API_KEY` - API key for authentication (optional)
- `PRAISONAI_CORS_ORIGINS` - Allowed CORS origins (optional)
- `PRAISONAI_MAX_JOB_DURATION_MINUTES` - Job timeout (default: 10)
- `PRAISONAI_MAX_RETRY_COUNT` - Retry attempts (default: 3)

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY app.py .
RUN pip install praisonai-svc python-dotenv

CMD ["python", "app.py"]
```

Build and run:

```bash
docker build -t text-processor-service .
docker run -p 8080:8080 --env-file .env text-processor-service
```

### Azure Container Apps

```bash
# Build and push
docker build -t myregistry.azurecr.io/text-processor:latest .
docker push myregistry.azurecr.io/text-processor:latest

# Deploy
az containerapp create \
  --name text-processor \
  --resource-group my-rg \
  --environment my-env \
  --image myregistry.azurecr.io/text-processor:latest \
  --target-port 8080 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  --env-vars PRAISONAI_AZURE_STORAGE_CONNECTION_STRING=secretref:storage-connection
```

## Troubleshooting

### Azurite not running

```
Error: Connection refused on port 10000
Solution: Start Azurite with: azurite --silent
```

### Worker not processing jobs

```
Check: Is the worker started?
Look for: "✅ Worker started for Text Processor Service"
```

### Jobs stuck in "queued" state

```
1. Check worker logs for errors
2. Verify Azure storage connection
3. Check job timeout settings
```

## Next Steps

- Add authentication with API keys
- Implement more text operations
- Add support for file uploads
- Create a web UI for the service
- Add metrics and monitoring

## Resources

- [PraisonAI-SVC Documentation](https://github.com/MervinPraison/PraisonAI-SVC)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Storage Documentation](https://docs.microsoft.com/azure/storage/)

## License

MIT License - See parent project for details

