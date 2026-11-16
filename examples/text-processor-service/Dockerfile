FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY app.py .
COPY .env* ./

# Install dependencies
RUN pip install --no-cache-dir \
    praisonai-svc \
    python-dotenv

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

# Run application
CMD ["python", "app.py"]

