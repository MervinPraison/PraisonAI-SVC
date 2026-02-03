# ServiceApp

The core class for creating web services from any PraisonAI Python package.

## Overview

ServiceApp is a FastAPI-based application factory that automatically creates REST endpoints for job processing.

## Quick Start

```python
from dotenv import load_dotenv
from praisonai_svc import ServiceApp

# Load environment variables from .env file
load_dotenv()

app = ServiceApp("My Service")

@app.job
def process_job(payload: dict) -> tuple[bytes, str, str]:
    """Process job and return file data."""
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

## @app.job Decorator

The `@app.job` decorator registers your job processing function:

```python
@app.job
def process_job(payload: dict) -> tuple[bytes, str, str]:
    # Your processing logic
    return (file_bytes, content_type, filename)
```

**Return Values:**
- `file_bytes` - The file content as bytes
- `content_type` - MIME type (e.g., "application/pdf", "image/png")
- `filename` - Name for the output file

## Generated Endpoints

ServiceApp automatically creates these endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/jobs` | Create new job |
| GET | `/jobs/{id}` | Get job status |
| GET | `/jobs/{id}/download` | Get fresh download URL |
| GET | `/health` | Health check |

## Configuration

```python
app = ServiceApp(
    name="My Service",
    version="1.0.0",
    cors_origins=["https://example.com"]
)
```

## Running the Service

```python
# Development
app.run(host="0.0.0.0", port=8080, reload=True)

# Production (via CLI)
praisonai-svc run
```
