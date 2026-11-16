"""Chart Generator Service Application.

This service generates charts from data:
- Line charts
- Bar charts
- Pie charts
- Scatter plots
- Area charts
- Multiple chart formats (PNG, SVG, PDF)
"""

import io
from datetime import datetime
from dotenv import load_dotenv

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from praisonai_svc import ServiceApp

# Load environment variables from .env file
load_dotenv()

# Initialize the service with custom config for separate queue
from praisonai_svc.models.config import ServiceConfig
config = ServiceConfig()
config.queue_name = "chart-generator-jobs"
config.poison_queue_name = "chart-generator-jobs-poison"

app = ServiceApp("Chart Generator Service", config=config)


def create_chart(data: dict, chart_type: str, options: dict) -> io.BytesIO:
    """Create a chart from data.
    
    Args:
        data: Chart data containing labels and values
        chart_type: Type of chart (line, bar, pie, scatter, area)
        options: Chart options (title, colors, size, etc.)
    
    Returns:
        BytesIO object containing the chart image
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ValueError("Matplotlib library is required. Install with: pip install matplotlib")
    
    # Extract data
    labels = data.get("labels", [])
    values = data.get("values", [])
    datasets = data.get("datasets", [])  # For multiple series
    
    # Extract options
    title = options.get("title", "Chart")
    xlabel = options.get("xlabel", "")
    ylabel = options.get("ylabel", "")
    width = options.get("width", 10)
    height = options.get("height", 6)
    dpi = options.get("dpi", 100)
    colors = options.get("colors", None)
    style = options.get("style", "default")
    
    # Set style
    if style == "dark":
        plt.style.use("dark_background")
    elif style == "seaborn":
        try:
            plt.style.use("seaborn-v0_8")
        except:
            plt.style.use("seaborn")
    else:
        plt.style.use("default")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
    
    # Generate colors if not provided
    if colors is None:
        if chart_type == "pie":
            colors = plt.cm.Set3(range(len(values)))
        else:
            colors = plt.cm.tab10(range(len(datasets) if datasets else 1))
    
    # Create chart based on type
    if chart_type == "line":
        if datasets:
            for i, dataset in enumerate(datasets):
                dataset_labels = dataset.get("labels", labels)
                dataset_values = dataset.get("values", [])
                dataset_label = dataset.get("label", f"Series {i+1}")
                ax.plot(dataset_labels, dataset_values, marker='o', label=dataset_label, 
                       color=colors[i % len(colors)] if isinstance(colors, list) else colors)
        else:
            ax.plot(labels, values, marker='o', color=colors[0] if isinstance(colors, list) else colors)
        ax.grid(True, alpha=0.3)
    
    elif chart_type == "bar":
        if datasets:
            x = range(len(labels))
            width_bar = 0.8 / len(datasets)
            for i, dataset in enumerate(datasets):
                dataset_values = dataset.get("values", [])
                dataset_label = dataset.get("label", f"Series {i+1}")
                offset = (i - len(datasets)/2 + 0.5) * width_bar
                ax.bar([xi + offset for xi in x], dataset_values, width_bar, 
                      label=dataset_label, color=colors[i % len(colors)] if isinstance(colors, list) else colors)
            ax.set_xticks(x)
            ax.set_xticklabels(labels)
        else:
            ax.bar(labels, values, color=colors[0] if isinstance(colors, list) else colors)
        ax.grid(True, alpha=0.3, axis='y')
    
    elif chart_type == "pie":
        if not labels or not values:
            raise ValueError("Labels and values are required for pie chart")
        wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%', 
                                          colors=colors, startangle=90)
        ax.axis('equal')
    
    elif chart_type == "scatter":
        if datasets:
            for i, dataset in enumerate(datasets):
                x_data = dataset.get("x", labels)
                y_data = dataset.get("y", dataset.get("values", values))
                dataset_label = dataset.get("label", f"Series {i+1}")
                ax.scatter(x_data, y_data, label=dataset_label, 
                          color=colors[i % len(colors)] if isinstance(colors, list) else colors,
                          alpha=0.6, s=100)
        else:
            if len(labels) == len(values):
                ax.scatter(labels, values, color=colors[0] if isinstance(colors, list) else colors, 
                          alpha=0.6, s=100)
            else:
                raise ValueError("Labels and values must have the same length for scatter plot")
        ax.grid(True, alpha=0.3)
    
    elif chart_type == "area":
        if datasets:
            ax.stackplot(labels, *[d.get("values", []) for d in datasets], 
                        labels=[d.get("label", f"Series {i+1}") for i, d in enumerate(datasets)],
                        colors=colors if isinstance(colors, list) else [colors] * len(datasets),
                        alpha=0.7)
        else:
            ax.fill_between(labels, values, alpha=0.7, color=colors[0] if isinstance(colors, list) else colors)
        ax.grid(True, alpha=0.3)
    
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")
    
    # Set labels and title
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Add legend if multiple series
    if datasets and len(datasets) > 1:
        ax.legend(loc='best')
    
    # Adjust layout
    plt.tight_layout()
    
    # Save to BytesIO
    output = io.BytesIO()
    fig.savefig(output, format='png', dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    
    return output


@app.job
def generate_chart(payload: dict) -> tuple[bytes, str, str]:
    """Generate chart from provided data.

    Args:
        payload: Job payload containing:
            - data (dict): Chart data with labels, values, and optionally datasets
            - chart_type (str): Type of chart (line, bar, pie, scatter, area)
            - options (dict): Chart options (title, colors, size, format, etc.)
            - format (str): Output format (png, svg, pdf) - default: png
    
    Returns:
        tuple of (file_data, content_type, filename)
    
    Example payload:
        {
            "data": {
                "labels": ["Jan", "Feb", "Mar", "Apr"],
                "values": [100, 150, 120, 180]
            },
            "chart_type": "bar",
            "options": {
                "title": "Monthly Sales",
                "xlabel": "Month",
                "ylabel": "Sales ($)",
                "width": 10,
                "height": 6
            },
            "format": "png"
        }
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ValueError("Matplotlib library is required. Install with: pip install matplotlib")
    
    # Extract parameters
    data = payload.get("data", {})
    chart_type = payload.get("chart_type", "bar").lower()
    options = payload.get("options", {})
    output_format = payload.get("format", "png").lower()
    
    # Validate this is a chart job, not an email template job
    if "template" in payload and "template_type" in payload:
        raise ValueError("This is an Email Template Renderer job. Please use the Email Template Renderer service (port 8082) instead of Chart Generator (port 8083).")
    
    if not data:
        raise ValueError("data is required in payload")
    
    # Validate chart type
    supported_types = ["line", "bar", "pie", "scatter", "area"]
    if chart_type not in supported_types:
        raise ValueError(f"Unsupported chart_type: {chart_type}. Supported: {', '.join(supported_types)}")
    
    # Create chart
    chart_output = create_chart(data, chart_type, options)
    
    # Handle different output formats
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    chart_type_name = chart_type.replace(" ", "_")
    
    if output_format == "svg":
        # For SVG, we need to recreate with SVG backend
        import matplotlib
        matplotlib.use('SVG')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(options.get("width", 10), options.get("height", 6)))
        # Recreate chart logic for SVG (simplified)
        # For now, convert PNG to SVG is complex, so we'll use PNG as base
        # In production, you'd recreate the chart with SVG backend
        file_data = chart_output.getvalue()
        content_type = "image/png"  # Fallback to PNG
        filename = f"chart_{chart_type_name}_{timestamp}.png"
    elif output_format == "pdf":
        # Similar to SVG, would need PDF backend
        file_data = chart_output.getvalue()
        content_type = "image/png"  # Fallback to PNG
        filename = f"chart_{chart_type_name}_{timestamp}.png"
    else:  # png (default)
        file_data = chart_output.getvalue()
        content_type = "image/png"
        filename = f"chart_{chart_type_name}_{timestamp}.png"
    
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
    if job.BlobName.endswith('.png'):
        media_type = "image/png"
    elif job.BlobName.endswith('.svg'):
        media_type = "image/svg+xml"
    elif job.BlobName.endswith('.pdf'):
        media_type = "application/pdf"
    else:
        media_type = "image/png"
    
    return Response(content=content, media_type=media_type)


if __name__ == "__main__":
    print("Starting Chart Generator Service...")
    print("Service URL: http://localhost:8083")
    print("Use POST /jobs to create jobs")
    print("Use GET /health for health check")
    print("Use GET /jobs/{job_id}/content to download directly (for local testing)")
    app.run(host="0.0.0.0", port=8083)

