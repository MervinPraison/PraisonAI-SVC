"""QR Code Generator Service Application.

This service generates QR codes from text, URLs, or contact information:
- Generate QR codes in multiple formats (PNG, SVG, PDF)
- Customizable size and error correction
- Support for different data types (URL, text, contact, WiFi)
"""

import io
from datetime import datetime
from dotenv import load_dotenv

try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

from praisonai_svc import ServiceApp

# Load environment variables from .env file
load_dotenv()

# Initialize the service
app = ServiceApp("QR Code Generator Service")


@app.job
def generate_qrcode(payload: dict) -> tuple[bytes, str, str]:
    """Generate QR code from data.

    Args:
        payload: Job payload containing:
            - data (str): Data to encode (URL, text, contact info, etc.)
            - format (str): Output format (png, svg, pdf) - default: png
            - size (int): QR code size in pixels (default: 300)
            - error_correction (str): Error correction level (L, M, Q, H) - default: M
            - border (int): Border size in boxes (default: 4)
            - fill_color (str): Fill color hex code (default: "#000000")
            - back_color (str): Background color hex code (default: "#FFFFFF")
    
    Returns:
        tuple of (file_data, content_type, filename)
    
    Example payload:
        {
            "data": "https://example.com",
            "format": "png",
            "size": 400,
            "error_correction": "H"
        }
    """
    if not QRCODE_AVAILABLE:
        raise ValueError("qrcode library is required. Install with: pip install qrcode[pil]")
    
    # Extract parameters
    data = payload.get("data", "")
    output_format = payload.get("format", "png").lower()
    size = payload.get("size", 300)
    error_correction = payload.get("error_correction", "M").upper()
    border = payload.get("border", 4)
    fill_color = payload.get("fill_color", "#000000")
    back_color = payload.get("back_color", "#FFFFFF")
    
    if not data:
        raise ValueError("data is required in payload")
    
    # Map error correction levels
    error_map = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }
    
    error_level = error_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M)
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=error_level,
        box_size=10,
        border=border,
    )
    
    # Add data
    qr.add_data(data)
    qr.make(fit=True)
    
    # Generate image
    output = io.BytesIO()
    
    if output_format == "svg":
        # SVG format
        try:
            from qrcode.image.svg import SvgImage
            img = qr.make_image(image_factory=SvgImage, fill_color=fill_color, back_color=back_color)
            img.save(output)
            content_type = "image/svg+xml"
            extension = "svg"
        except ImportError:
            raise ValueError("SVG support requires qrcode[svg]. Install with: pip install qrcode[svg]")
    
    elif output_format == "pdf":
        # PDF format (generate as PNG first, then convert)
        from PIL import Image
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        # Resize if needed
        if size != 300:
            img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # For PDF, we'll return PNG for now (PDF conversion requires reportlab)
        # In production, you could add PDF support
        img.save(output, format="PNG")
        content_type = "image/png"
        extension = "png"
    
    else:  # png
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        # Resize if needed
        if size != 300:
            from PIL import Image
            img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        img.save(output, format="PNG")
        content_type = "image/png"
        extension = "png"
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"qrcode_{timestamp}.{extension}"
    
    return output.getvalue(), content_type, filename


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
        media_type = "application/octet-stream"
    
    return Response(content=content, media_type=media_type)


if __name__ == "__main__":
    print("Starting QR Code Generator Service...")
    print("Service URL: http://localhost:8080")
    print("Use POST /jobs to create jobs")
    print("Use GET /health for health check")
    print("Use GET /jobs/{job_id}/content to download directly (for local testing)")
    app.run(host="0.0.0.0", port=8080)

