"""Email Template Renderer Service Application.

This service renders email templates with dynamic data:
- HTML email templates
- Plain text email templates
- Support for Jinja2 templating syntax
- Variable substitution
- Template inheritance
"""

import io
from datetime import datetime
from dotenv import load_dotenv

try:
    from jinja2 import Template, Environment, BaseLoader
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

from praisonai_svc import ServiceApp

# Load environment variables from .env file
load_dotenv()

# Initialize the service with custom config for separate queue
from praisonai_svc.models.config import ServiceConfig
config = ServiceConfig()
config.queue_name = "email-template-jobs"
config.poison_queue_name = "email-template-jobs-poison"

app = ServiceApp("Email Template Renderer Service", config=config)


@app.job
def render_email_template(payload: dict) -> tuple[bytes, str, str]:
    """Render email template with provided data.

    Args:
        payload: Job payload containing:
            - template (str): Email template content (HTML or text)
            - template_type (str): Type of template (html, text) - default: html
            - data (dict): Variables to substitute in template
            - subject (str, optional): Email subject line
            - output_format (str): Output format (html, text, json) - default: html
    
    Returns:
        tuple of (file_data, content_type, filename)
    
    Example payload:
        {
            "template": "<h1>Hello {{ name }}!</h1><p>Welcome to {{ company }}.</p>",
            "template_type": "html",
            "data": {"name": "John Doe", "company": "Acme Corp"},
            "subject": "Welcome Email",
            "output_format": "html"
        }
    """
    if not JINJA2_AVAILABLE:
        raise ValueError("Jinja2 library is required. Install with: pip install Jinja2")
    
    # Extract parameters
    template_content = payload.get("template", "")
    template_type = payload.get("template_type", "html").lower()
    data = payload.get("data", {})
    subject = payload.get("subject", "")
    output_format = payload.get("output_format", template_type).lower()
    
    # Validate this is an email template job, not a chart job
    if "chart_type" in payload or ("data" in payload and "labels" in payload.get("data", {}) and "values" in payload.get("data", {})):
        raise ValueError("This is a Chart Generator job. Please use the Chart Generator service (port 8083) instead of Email Template Renderer (port 8082).")
    
    if not template_content:
        raise ValueError("template is required in payload")
    
    # Create Jinja2 environment
    env = Environment(loader=BaseLoader())
    
    # Render template
    try:
        template = env.from_string(template_content)
        rendered_content = template.render(**data)
    except Exception as e:
        raise ValueError(f"Template rendering error: {str(e)}")
    
    # Prepare output based on format
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    if output_format == "json":
        # Return as JSON with metadata
        import json
        output_data = {
            "subject": subject,
            "body": rendered_content,
            "type": template_type,
            "rendered_at": datetime.utcnow().isoformat()
        }
        file_data = json.dumps(output_data, indent=2).encode('utf-8')
        content_type = "application/json"
        filename = f"email_template_{timestamp}.json"
    
    elif output_format == "text" or template_type == "text":
        # Plain text email
        if subject:
            full_content = f"Subject: {subject}\n\n{rendered_content}"
        else:
            full_content = rendered_content
        file_data = full_content.encode('utf-8')
        content_type = "text/plain"
        filename = f"email_template_{timestamp}.txt"
    
    else:
        # HTML email (default)
        if subject:
            # Create a complete HTML email structure
            html_wrapper = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body>
{rendered_content}
</body>
</html>"""
            full_content = html_wrapper
        else:
            full_content = rendered_content
        
        file_data = full_content.encode('utf-8')
        content_type = "text/html"
        filename = f"email_template_{timestamp}.html"
    
    return file_data, content_type, filename


# Add direct download endpoint for local testing
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
    if job.BlobName.endswith('.html'):
        media_type = "text/html"
    elif job.BlobName.endswith('.txt'):
        media_type = "text/plain"
    elif job.BlobName.endswith('.json'):
        media_type = "application/json"
    else:
        media_type = "application/octet-stream"
    
    return Response(content=content, media_type=media_type)


if __name__ == "__main__":
    print("Starting Email Template Renderer Service...")
    print("Service URL: http://localhost:8082")
    print("Use POST /jobs to create jobs")
    print("Use GET /health for health check")
    print("Use GET /jobs/{job_id}/content to download directly (for local testing)")
    app.run(host="0.0.0.0", port=8082)

