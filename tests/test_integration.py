"""Integration tests with mock Azure services."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from praisonai_svc import ServiceApp
from praisonai_svc.models.config import ServiceConfig
from praisonai_svc.models.job import JobEntity


@pytest.fixture
def mock_azure_services():
    """Mock all Azure services."""
    with (
        patch("praisonai_svc.app.BlobStorage") as mock_blob,
        patch("praisonai_svc.app.QueueManager") as mock_queue,
        patch("praisonai_svc.app.TableStorage") as mock_table,
    ):

        # Setup mock instances
        mock_blob_instance = MagicMock()
        mock_queue_instance = MagicMock()
        mock_table_instance = MagicMock()

        mock_blob.return_value = mock_blob_instance
        mock_queue.return_value = mock_queue_instance
        mock_table.return_value = mock_table_instance

        # Mock async methods
        mock_queue_instance.enqueue_job = AsyncMock()
        mock_table_instance.create_job = AsyncMock()
        mock_table_instance.get_job = AsyncMock()
        mock_table_instance.find_job_by_hash = AsyncMock(return_value=None)

        yield {
            "blob": mock_blob_instance,
            "queue": mock_queue_instance,
            "table": mock_table_instance,
        }


@pytest.fixture
def test_app(mock_azure_services):
    """Create test app with mocked services."""
    config = MagicMock(spec=ServiceConfig)
    config.azure_storage_connection_string = "mock"
    config.cors_origins = ["*"]
    config.table_connection_string = "mock"
    config.queue_connection_string = "mock"

    app = ServiceApp("Test Service", config=config)

    @app.job
    def test_handler(payload: dict) -> tuple[bytes, str, str]:
        return b"test content", "text/plain", "test.txt"

    return app, mock_azure_services


def test_create_job_endpoint(test_app):
    """Test POST /jobs endpoint."""
    app, mocks = test_app
    client = TestClient(app.app)

    response = client.post("/jobs", json={"payload": {"key": "value"}})

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "queued"

    # Verify Azure services were called
    mocks["table"].create_job.assert_called_once()
    mocks["queue"].enqueue_job.assert_called_once()


def test_get_job_endpoint(test_app):
    """Test GET /jobs/{id} endpoint."""
    app, mocks = test_app
    client = TestClient(app.app)

    # Mock job entity
    from datetime import datetime

    mock_job = JobEntity(
        RowKey="test-job-123",
        Status="done",
        CreatedUTC=datetime.utcnow(),
        UpdatedUTC=datetime.utcnow(),
        JobHash="abc123",
        DownloadURL="https://example.com/file.txt",
    )
    mocks["table"].get_job.return_value = mock_job

    response = client.get("/jobs/test-job-123")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "test-job-123"
    assert data["status"] == "done"
    assert data["download_url"] == "https://example.com/file.txt"


def test_get_job_not_found(test_app):
    """Test GET /jobs/{id} with non-existent job."""
    app, mocks = test_app
    client = TestClient(app.app)

    mocks["table"].get_job.return_value = None

    response = client.get("/jobs/nonexistent")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_download_endpoint(test_app):
    """Test GET /jobs/{id}/download endpoint."""
    app, mocks = test_app
    client = TestClient(app.app)

    # Mock job entity
    from datetime import datetime

    mock_job = JobEntity(
        RowKey="test-job-456",
        Status="done",
        CreatedUTC=datetime.utcnow(),
        UpdatedUTC=datetime.utcnow(),
        JobHash="def456",
        BlobName="test-job-456/file.txt",
    )
    mocks["table"].get_job.return_value = mock_job
    mocks["blob"].generate_sas_url.return_value = "https://blob.example.com/file.txt?sas=token"

    response = client.get("/jobs/test-job-456/download")

    assert response.status_code == 200
    data = response.json()
    assert "download_url" in data
    assert "sas=token" in data["download_url"]


def test_download_job_not_ready(test_app):
    """Test download endpoint with job not ready."""
    app, mocks = test_app
    client = TestClient(app.app)

    # Mock job entity in processing state
    from datetime import datetime

    mock_job = JobEntity(
        RowKey="test-job-789",
        Status="processing",
        CreatedUTC=datetime.utcnow(),
        UpdatedUTC=datetime.utcnow(),
        JobHash="ghi789",
    )
    mocks["table"].get_job.return_value = mock_job

    response = client.get("/jobs/test-job-789/download")

    assert response.status_code == 400
    assert "not ready" in response.json()["detail"].lower()


def test_idempotency_check(test_app):
    """Test that duplicate jobs return existing result."""
    app, mocks = test_app
    client = TestClient(app.app)

    # Mock existing job
    from datetime import datetime

    existing_job = JobEntity(
        RowKey="existing-job",
        Status="done",
        CreatedUTC=datetime.utcnow(),
        UpdatedUTC=datetime.utcnow(),
        JobHash="same-hash",
        DownloadURL="https://example.com/existing.txt",
    )
    mocks["table"].find_job_by_hash.return_value = existing_job

    response = client.post("/jobs", json={"payload": {"key": "value"}})

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "existing-job"
    assert data["status"] == "done"

    # Should not create new job
    mocks["table"].create_job.assert_not_called()
