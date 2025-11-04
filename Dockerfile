FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies
RUN uv pip install --system --no-cache .

# Expose port
EXPOSE 8080

# Run application
CMD ["uvicorn", "praisonai_svc.app:app", "--host", "0.0.0.0", "--port", "8080"]
