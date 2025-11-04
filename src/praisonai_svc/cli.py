"""CLI commands for PraisonAI Service Framework."""

import click


@click.group()
@click.version_option(version="1.1.0")
def main() -> None:
    """PraisonAI Service Framework CLI."""
    pass


@main.command()
@click.option("--host", default="0.0.0.0", help="Host to bind to")
@click.option("--port", default=8080, help="Port to bind to")
def run(host: str, port: int) -> None:
    """Run the service locally (loads handlers.py)."""
    import sys
    from pathlib import Path
    
    # Check if handlers.py exists
    handlers_file = Path("handlers.py")
    if not handlers_file.exists():
        click.echo("❌ Error: handlers.py not found in current directory")
        click.echo("Run this command from your service directory")
        sys.exit(1)
    
    # Load handlers.py and run the app
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("handlers", handlers_file)
        if spec and spec.loader:
            handlers = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(handlers)
            
            # Get the app from handlers and run it
            if hasattr(handlers, 'app'):
                handlers.app.run(host=host, port=port)
            else:
                click.echo("❌ Error: No 'app' found in handlers.py")
                sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error loading handlers.py: {e}")
        sys.exit(1)


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
from dotenv import load_dotenv
from praisonai_svc import ServiceApp

# Load environment variables from .env file
load_dotenv()

app = ServiceApp("{service_name}")


@app.job
def process_job(payload: dict) -> tuple[bytes, str, str]:
    """Process job and return file data.

    Args:
        payload: Job payload from request

    Returns:
        tuple of (file_data, content_type, filename)
    """
    # Simple example - replace with your actual processing logic
    title = payload.get('title', 'Untitled')
    content = f"Processed: {{title}}\\n\\nFull payload:\\n{{payload}}"
    
    return (
        content.encode(),  # File content as bytes
        "text/plain",      # Content type
        "result.txt"       # Filename
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
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
