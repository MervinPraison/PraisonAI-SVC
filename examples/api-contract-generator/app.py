"""API Contract Generator Service Application.

This service generates API contracts and related artifacts from simple API descriptions:
- OpenAPI/Swagger specifications
- Postman collections
- Client SDKs (Python, JavaScript, TypeScript)
- API documentation
"""

import json
import yaml
from datetime import datetime
from dotenv import load_dotenv

from praisonai_svc import ServiceApp

# Load environment variables from .env file
load_dotenv()

# Initialize the service
app = ServiceApp("API Contract Generator Service")


def generate_openapi(api_desc: dict) -> str:
    """Generate OpenAPI 3.0 specification."""
    api_name = api_desc.get("name", "API")
    version = api_desc.get("version", "1.0.0")
    base_url = api_desc.get("base_url", "https://api.example.com")
    endpoints = api_desc.get("endpoints", [])
    
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": api_name,
            "version": version,
            "description": api_desc.get("description", f"{api_name} API specification")
        },
        "servers": [{"url": base_url}],
        "paths": {}
    }
    
    for endpoint in endpoints:
        method = endpoint.get("method", "GET").lower()
        path = endpoint.get("path", "/")
        summary = endpoint.get("summary", f"{method.upper()} {path}")
        returns = endpoint.get("returns", "object")
        
        if path not in openapi_spec["paths"]:
            openapi_spec["paths"][path] = {}
        
        operation = {
            "summary": summary,
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array" if returns == "list" else "object"
                            }
                        }
                    }
                }
            }
        }
        
        if method == "post" or method == "put":
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": endpoint.get("body_schema", {})
                        }
                    }
                }
            }
        
        openapi_spec["paths"][path][method] = operation
    
    return yaml.dump(openapi_spec, default_flow_style=False)


def generate_postman_collection(api_desc: dict) -> dict:
    """Generate Postman collection."""
    api_name = api_desc.get("name", "API")
    endpoints = api_desc.get("endpoints", [])
    
    collection = {
        "info": {
            "name": api_name,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }
    
    for endpoint in endpoints:
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "/")
        base_url = api_desc.get("base_url", "https://api.example.com")
        
        item = {
            "name": f"{method} {path}",
            "request": {
                "method": method,
                "header": [],
                "url": {
                    "raw": f"{base_url}{path}",
                    "host": [base_url.split("//")[1].split("/")[0]],
                    "path": path.strip("/").split("/")
                }
            }
        }
        
        if method in ["POST", "PUT", "PATCH"]:
            item["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(endpoint.get("body_example", {}), indent=2),
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            }
        
        collection["item"].append(item)
    
    return collection


def generate_python_client(api_desc: dict) -> str:
    """Generate Python client SDK."""
    api_name = api_desc.get("name", "API").replace(" ", "")
    base_url = api_desc.get("base_url", "https://api.example.com")
    endpoints = api_desc.get("endpoints", [])
    
    code = f'''"""Generated Python client for {api_desc.get("name", "API")}."""

import requests

class {api_name}Client:
    """Client for {api_desc.get("name", "API")} API."""
    
    def __init__(self, base_url: str = "{base_url}"):
        self.base_url = base_url
        self.session = requests.Session()
    
'''
    
    for endpoint in endpoints:
        method = endpoint.get("method", "GET").lower()
        path = endpoint.get("path", "/")
        func_name = path.strip("/").replace("/", "_").replace("-", "_") or "root"
        
        if method == "get":
            code += f'''    def get_{func_name}(self):
        """{endpoint.get("summary", f"GET {path}")}"""
        response = self.session.get(f"{{self.base_url}}{path}")
        response.raise_for_status()
        return response.json()
    
'''
        elif method == "post":
            code += f'''    def create_{func_name}(self, data: dict):
        """{endpoint.get("summary", f"POST {path}")}"""
        response = self.session.post(f"{{self.base_url}}{path}", json=data)
        response.raise_for_status()
        return response.json()
    
'''
        elif method == "put":
            code += f'''    def update_{func_name}(self, data: dict):
        """{endpoint.get("summary", f"PUT {path}")}"""
        response = self.session.put(f"{{self.base_url}}{path}", json=data)
        response.raise_for_status()
        return response.json()
    
'''
        elif method == "delete":
            code += f'''    def delete_{func_name}(self):
        """{endpoint.get("summary", f"DELETE {path}")}"""
        response = self.session.delete(f"{{self.base_url}}{path}")
        response.raise_for_status()
        return response.json()
    
'''
    
    return code


def generate_javascript_client(api_desc: dict) -> str:
    """Generate JavaScript client SDK."""
    api_name = api_desc.get("name", "API").replace(" ", "")
    base_url = api_desc.get("base_url", "https://api.example.com")
    endpoints = api_desc.get("endpoints", [])
    
    code = f'''// Generated JavaScript client for {api_desc.get("name", "API")}

class {api_name}Client {{
    constructor(baseUrl = "{base_url}") {{
        this.baseUrl = baseUrl;
    }}
    
    async request(method, path, data = null) {{
        const options = {{
            method,
            headers: {{ "Content-Type": "application/json" }}
        }};
        
        if (data) {{
            options.body = JSON.stringify(data);
        }}
        
        const response = await fetch(`${{this.baseUrl}}${{path}}`, options);
        if (!response.ok) {{
            throw new Error(`HTTP error! status: ${{response.status}}`);
        }}
        return await response.json();
    }}
    
'''
    
    for endpoint in endpoints:
        method = endpoint.get("method", "GET").lower()
        path = endpoint.get("path", "/")
        func_name = path.strip("/").replace("/", "_").replace("-", "_") or "root"
        func_name_camel = "".join(word.capitalize() for word in func_name.split("_")) if func_name != "root" else "Root"
        
        if method == "get":
            code += f'''    async get{func_name_camel}() {{
        return this.request("GET", "{path}");
    }}
    
'''
        elif method == "post":
            code += f'''    async create{func_name_camel}(data) {{
        return this.request("POST", "{path}", data);
    }}
    
'''
    
    code += "}\n\nexport default " + api_name + "Client;"
    return code


def generate_api_docs(api_desc: dict) -> str:
    """Generate Markdown API documentation."""
    api_name = api_desc.get("name", "API")
    description = api_desc.get("description", f"{api_name} API documentation")
    base_url = api_desc.get("base_url", "https://api.example.com")
    endpoints = api_desc.get("endpoints", [])
    
    docs = f"""# {api_name} API Documentation

{description}

## Base URL

```
{base_url}
```

## Endpoints

"""
    
    for endpoint in endpoints:
        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "/")
        summary = endpoint.get("summary", f"{method} {path}")
        
        docs += f"""### {method} {path}

{summary}

**Request:**
```http
{method} {base_url}{path}
```

"""
        
        if method in ["POST", "PUT", "PATCH"]:
            body_example = endpoint.get("body_example", {})
            docs += f"""**Request Body:**
```json
{json.dumps(body_example, indent=2)}
```

"""
        
        response_example = endpoint.get("response_example", {"status": "success"})
        docs += f"""**Response:**
```json
{json.dumps(response_example, indent=2)}
```

---
"""
    
    return docs


@app.job
def generate_contract(payload: dict) -> tuple[bytes, str, str]:
    """Generate API contract artifacts from API description.

    Args:
        payload: Job payload containing:
            - api (dict): API description with name, version, base_url, endpoints
            - format (str): Output format (openapi, postman, python, javascript, docs)
    
    Returns:
        tuple of (file_data, content_type, filename)
    
    Example payload:
        {
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
    """
    api_desc = payload.get("api", {})
    format_type = payload.get("format", "openapi").lower()
    
    if not api_desc:
        raise ValueError("API description is required in payload")
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    api_name = api_desc.get("name", "API").replace(" ", "_")
    
    if format_type == "openapi":
        content = generate_openapi(api_desc)
        file_data = content.encode('utf-8')
        content_type = "application/yaml"
        filename = f"{api_name}_openapi_{timestamp}.yaml"
    
    elif format_type == "postman":
        collection = generate_postman_collection(api_desc)
        file_data = json.dumps(collection, indent=2).encode('utf-8')
        content_type = "application/json"
        filename = f"{api_name}_postman_{timestamp}.json"
    
    elif format_type == "python":
        content = generate_python_client(api_desc)
        file_data = content.encode('utf-8')
        content_type = "text/x-python"
        filename = f"{api_name}_client_{timestamp}.py"
    
    elif format_type == "javascript":
        content = generate_javascript_client(api_desc)
        file_data = content.encode('utf-8')
        content_type = "application/javascript"
        filename = f"{api_name}_client_{timestamp}.js"
    
    elif format_type == "docs":
        content = generate_api_docs(api_desc)
        file_data = content.encode('utf-8')
        content_type = "text/markdown"
        filename = f"{api_name}_docs_{timestamp}.md"
    
    else:
        raise ValueError(f"Unsupported format: {format_type}. Supported: openapi, postman, python, javascript, docs")
    
    return file_data, content_type, filename


# Add direct download endpoint for local testing (bypasses SAS URL issues with Azurite)
fastapi_app = app.get_app()

@fastapi_app.get("/jobs/{job_id}/content")
async def get_job_content(job_id: str):
    """Get job result content directly (for local testing with Azurite)."""
    from fastapi import HTTPException
    from fastapi.responses import Response
    from praisonai_svc.models import JobStatus
    
    job = await app.table_storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.Status != JobStatus.DONE.value:
        raise HTTPException(status_code=400, detail="Job not ready for download")
    
    if not job.BlobName:
        raise HTTPException(status_code=500, detail="Blob name not found")
    
    # Download blob content directly
    blob_client = app.blob_storage.client.get_blob_client(
        container=app.blob_storage.container_name,
        blob=job.BlobName
    )
    content = blob_client.download_blob().readall()
    
    # Determine content type from filename
    if job.BlobName.endswith('.yaml') or job.BlobName.endswith('.yml'):
        media_type = "application/yaml"
    elif job.BlobName.endswith('.json'):
        media_type = "application/json"
    elif job.BlobName.endswith('.py'):
        media_type = "text/x-python"
    elif job.BlobName.endswith('.js'):
        media_type = "application/javascript"
    elif job.BlobName.endswith('.md'):
        media_type = "text/markdown"
    else:
        media_type = "application/octet-stream"
    
    return Response(content=content, media_type=media_type)


if __name__ == "__main__":
    print("Starting API Contract Generator Service...")
    print("Service URL: http://localhost:8080")
    print("Use POST /jobs to create jobs")
    print("Use GET /health for health check")
    print("Use GET /jobs/{job_id}/content to download directly (for local testing)")
    app.run(host="0.0.0.0", port=8080)

