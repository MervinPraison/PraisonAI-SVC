# API Contract Generator Service

A service that generates API contracts and related artifacts from simple API descriptions.

## Features

- ✅ Generate OpenAPI 3.0 specifications
- ✅ Generate Postman collections
- ✅ Generate Python client SDKs
- ✅ Generate JavaScript client SDKs
- ✅ Generate API documentation (Markdown)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment

Create `.env` file:

```bash
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
```

### 3. Start Azurite (Azure Storage Emulator)

```bash
azurite --silent
```

### 4. Run the Service

```bash
python app.py
```

## Usage Examples

### Generate OpenAPI Specification

```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "api": {
        "name": "User API",
        "version": "1.0.0",
        "base_url": "https://api.example.com",
        "endpoints": [
          {"method": "GET", "path": "/users", "summary": "List users", "returns": "list"},
          {"method": "POST", "path": "/users", "summary": "Create user", "body_example": {"name": "John"}}
        ]
      },
      "format": "openapi"
    }
  }'
```

### Generate Postman Collection

```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "api": {
        "name": "User API",
        "base_url": "https://api.example.com",
        "endpoints": [
          {"method": "GET", "path": "/users"},
          {"method": "POST", "path": "/users"}
        ]
      },
      "format": "postman"
    }
  }'
```

### Generate Python Client SDK

```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "api": {
        "name": "User API",
        "base_url": "https://api.example.com",
        "endpoints": [
          {"method": "GET", "path": "/users"},
          {"method": "POST", "path": "/users"}
        ]
      },
      "format": "python"
    }
  }'
```

### Generate JavaScript Client SDK

```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "api": {
        "name": "User API",
        "base_url": "https://api.example.com",
        "endpoints": [
          {"method": "GET", "path": "/users"},
          {"method": "POST", "path": "/users"}
        ]
      },
      "format": "javascript"
    }
  }'
```

### Generate API Documentation

```bash
curl -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "api": {
        "name": "User API",
        "description": "RESTful API for user management",
        "base_url": "https://api.example.com",
        "endpoints": [
          {"method": "GET", "path": "/users", "summary": "List all users"},
          {"method": "POST", "path": "/users", "summary": "Create a new user"}
        ]
      },
      "format": "docs"
    }
  }'
```

## Supported Formats

| Format | Output | Content Type |
|--------|--------|--------------|
| `openapi` | OpenAPI 3.0 YAML | application/yaml |
| `postman` | Postman Collection JSON | application/json |
| `python` | Python Client SDK | text/x-python |
| `javascript` | JavaScript Client SDK | application/javascript |
| `docs` | Markdown Documentation | text/markdown |

## API Description Structure

```json
{
  "api": {
    "name": "API Name",
    "version": "1.0.0",
    "base_url": "https://api.example.com",
    "description": "API description",
    "endpoints": [
      {
        "method": "GET|POST|PUT|DELETE",
        "path": "/path/to/endpoint",
        "summary": "Endpoint description",
        "returns": "list|object",
        "body_example": {},
        "response_example": {}
      }
    ]
  },
  "format": "openapi|postman|python|javascript|docs"
}
```

## Complete Workflow

```bash
# 1. Create job
JOB_ID=$(curl -s -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"api": {"name": "Test API", "endpoints": []}, "format": "openapi"}}' \
  | jq -r .job_id)

# 2. Wait for processing
sleep 3

# 3. Check status
curl http://localhost:8080/jobs/$JOB_ID

# 4. Get download URL
DOWNLOAD_URL=$(curl -s http://localhost:8080/jobs/$JOB_ID/download | jq -r .download_url)

# 5. Download result
curl "$DOWNLOAD_URL" -o result.yaml
```

## License

MIT License

