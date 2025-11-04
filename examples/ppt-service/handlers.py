"""Example PPT service handler."""


from praisonai_svc import ServiceApp

app = ServiceApp("PraisonAI PPT Example")


@app.job
def generate_ppt(payload: dict) -> tuple[bytes, str, str]:
    """Generate PowerPoint from YAML payload.

    Args:
        payload: Job payload containing presentation data

    Returns:
        tuple of (file_data, content_type, filename)
    """
    # TODO: Replace with actual praisonaippt integration
    # from praisonaippt import build_ppt
    # buf = io.BytesIO()
    # build_ppt(payload, out=buf)
    # return buf.getvalue(), "application/vnd.openxmlformats-officedocument.presentationml.presentation", "slides.pptx"

    # Mock implementation for demonstration
    mock_pptx_data = b"Mock PPTX file content"
    return (
        mock_pptx_data,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "presentation.pptx",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app.get_app(), host="0.0.0.0", port=8080)
