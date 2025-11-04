"""CLI commands for praisonai-svc."""

import click
import uvicorn


@click.group()
@click.version_option(version="1.0.0")
def main() -> None:
    """PraisonAI Service Framework CLI."""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8080, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def run(host: str, port: int, reload: bool) -> None:
    """Run the service locally."""
    click.echo(f"Starting service on {host}:{port}")
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload,
    )


@main.command()
@click.argument("service_name")
@click.option("--package", help="PraisonAI package to integrate")
def new(service_name: str, package: str | None) -> None:
    """Create a new service from template."""
    from pathlib import Path

    service_dir = Path(service_name)
    if service_dir.exists():
        click.echo(f"Error: Directory {service_name} already exists", err=True)
        return

    # Create directory structure
    service_dir.mkdir()
    (service_dir / "handlers.py").write_text(
        f'''"""Handler for {service_name} service."""

import io
from praisonai_svc import ServiceApp

app = ServiceApp("{service_name}")


@app.job
def process_job(payload: dict) -> tuple[bytes, str, str]:
    """Process job and return file data.

    Args:
        payload: Job payload from request

    Returns:
        tuple of (file_data, content_type, filename)
    """
    # TODO: Implement your job processing logic here
    # Example:
    # from {package or "your_package"} import build_output
    # buf = io.BytesIO()
    # build_output(payload, out=buf)
    # return buf.getvalue(), "application/octet-stream", "output.bin"

    raise NotImplementedError("Job handler not implemented")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app.get_app(), host="0.0.0.0", port=8080)
'''
    )

    (service_dir / ".env.example").write_text(
        """# Azure Storage Configuration
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING=your_connection_string_here
PRAISONAI_AZURE_TABLE_CONN_STRING=  # Optional, defaults to storage connection
PRAISONAI_AZURE_QUEUE_CONN_STRING=  # Optional, defaults to storage connection

# API Configuration
PRAISONAI_API_KEY=your_secret_api_key
PRAISONAI_CORS_ORIGINS=["https://your-wordpress-site.com"]

# Job Settings
PRAISONAI_MAX_JOB_DURATION_MINUTES=10
PRAISONAI_MAX_RETRY_COUNT=3
"""
    )

    (service_dir / "README.md").write_text(
        f"""# {service_name}

PraisonAI Service built with praisonai-svc framework.

## Setup

1. Install dependencies:
```bash
uv pip install praisonai-svc{' ' + package if package else ''}
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

3. Run locally:
```bash
python handlers.py
```

4. Test the API:
```bash
curl -X POST http://localhost:8080/jobs \\
  -H "Content-Type: application/json" \\
  -d '{{"payload": {{"key": "value"}}}}'
```

## Deployment

See [deployment guide](https://docs.praisonai.com/svc/deployment) for Azure Container Apps deployment.
"""
    )

    click.echo(f"✅ Created new service: {service_name}")
    click.echo(f"📁 Directory: {service_dir.absolute()}")
    click.echo("\nNext steps:")
    click.echo(f"  cd {service_name}")
    click.echo("  # Edit handlers.py to implement your job logic")
    click.echo("  # Configure .env with Azure credentials")
    click.echo("  python handlers.py")


@main.command()
def deploy() -> None:
    """Deploy service to Azure Container Apps."""
    click.echo("🚀 Azure deployment coming soon!")
    click.echo("For now, see: https://docs.praisonai.com/svc/deployment")


@main.command()
def logs() -> None:
    """Tail logs from Azure Container App."""
    click.echo("📋 Log tailing coming soon!")


if __name__ == "__main__":
    main()
