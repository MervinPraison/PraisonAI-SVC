"""Image Processor Service Application.

This service processes images with various operations:
- Resize images
- Convert formats (PNG, JPEG, WebP, etc.)
- Apply filters (grayscale, blur, brightness, contrast)
- Generate thumbnails
- Crop and rotate images
"""

import io
from datetime import datetime
from dotenv import load_dotenv

try:
    from PIL import Image, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from praisonai_svc import ServiceApp

# Load environment variables from .env file
load_dotenv()

# Initialize the service
app = ServiceApp("Image Processor Service")


@app.job
def process_image(payload: dict) -> tuple[bytes, str, str]:
    """Process image based on the requested operation.

    Args:
        payload: Job payload containing:
            - image_data (str): Base64 encoded image data or image URL
            - operation (str): Type of operation (resize, convert, filter, thumbnail, crop, rotate)
            - format (str): Output format (png, jpeg, webp) - default: png
            - width (int): Target width for resize/crop
            - height (int): Target height for resize/crop
            - filter_type (str): Filter to apply (grayscale, blur, brightness, contrast)
            - quality (int): JPEG quality (1-100, default: 85)
    
    Returns:
        tuple of (file_data, content_type, filename)
    
    Example payload:
        {
            "image_data": "base64_encoded_image_or_url",
            "operation": "resize",
            "width": 800,
            "height": 600,
            "format": "jpeg"
        }
    """
    if not PIL_AVAILABLE:
        raise ValueError("Pillow library is required. Install with: pip install Pillow")
    
    import base64
    
    # Extract parameters
    image_data = payload.get("image_data", "")
    operation = payload.get("operation", "resize").lower()
    output_format = payload.get("format", "png").lower()
    width = payload.get("width")
    height = payload.get("height")
    filter_type = payload.get("filter_type", "grayscale").lower()
    quality = payload.get("quality", 85)
    
    if not image_data:
        raise ValueError("image_data is required in payload")
    
    # Load image
    try:
        # Try to decode as base64
        if image_data.startswith("data:image"):
            # Remove data URL prefix
            image_data = image_data.split(",")[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
    except Exception:
        # If base64 fails, assume it's a URL (mock implementation)
        # In production, you'd fetch the image from URL
        raise ValueError("Invalid image data. Provide base64 encoded image.")
    
    # Process image based on operation
    if operation == "resize":
        if not width or not height:
            raise ValueError("width and height are required for resize operation")
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    
    elif operation == "convert":
        # Format conversion handled at save time
        pass
    
    elif operation == "filter":
        if filter_type == "grayscale":
            image = image.convert("L")
        elif filter_type == "blur":
            image = image.filter(ImageFilter.BLUR)
        elif filter_type == "brightness":
            factor = payload.get("factor", 1.2)
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(factor)
        elif filter_type == "contrast":
            factor = payload.get("factor", 1.2)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(factor)
        elif filter_type == "sharpness":
            factor = payload.get("factor", 1.2)
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(factor)
    
    elif operation == "thumbnail":
        if not width or not height:
            raise ValueError("width and height are required for thumbnail operation")
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
    
    elif operation == "crop":
        if not all([width, height]):
            raise ValueError("width and height are required for crop operation")
        # Center crop
        left = (image.width - width) // 2
        top = (image.height - height) // 2
        right = left + width
        bottom = top + height
        image = image.crop((left, top, right, bottom))
    
    elif operation == "rotate":
        angle = payload.get("angle", 90)
        image = image.rotate(angle, expand=True)
    
    else:
        raise ValueError(f"Unsupported operation: {operation}. Supported: resize, convert, filter, thumbnail, crop, rotate")
    
    # Convert to RGB if needed for JPEG
    if output_format == "jpeg" and image.mode != "RGB":
        image = image.convert("RGB")
    
    # Save to bytes
    output = io.BytesIO()
    
    if output_format == "jpeg" or output_format == "jpg":
        image.save(output, format="JPEG", quality=quality)
        content_type = "image/jpeg"
        extension = "jpg"
    elif output_format == "webp":
        image.save(output, format="WebP", quality=quality)
        content_type = "image/webp"
        extension = "webp"
    else:  # png
        image.save(output, format="PNG")
        content_type = "image/png"
        extension = "png"
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"processed_image_{timestamp}.{extension}"
    
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
    if job.BlobName.endswith('.jpg') or job.BlobName.endswith('.jpeg'):
        media_type = "image/jpeg"
    elif job.BlobName.endswith('.png'):
        media_type = "image/png"
    elif job.BlobName.endswith('.webp'):
        media_type = "image/webp"
    else:
        media_type = "application/octet-stream"
    
    return Response(content=content, media_type=media_type)


if __name__ == "__main__":
    print("Starting Image Processor Service...")
    print("Service URL: http://localhost:8081")
    print("Use POST /jobs to create jobs")
    print("Use GET /health for health check")
    print("Use GET /jobs/{job_id}/content to download directly (for local testing)")
    app.run(host="0.0.0.0", port=8081)

