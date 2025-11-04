"""Test ServiceApp functionality."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from praisonai_svc import ServiceApp
from praisonai_svc.models.config import ServiceConfig


@pytest.fixture
def mock_config():
    """Mock ServiceConfig."""
    config = MagicMock(spec=ServiceConfig)
    config.azure_storage_connection_string = "mock_connection"
    config.cors_origins = ["*"]
    config.blob_container_name = "test-container"
    config.queue_name = "test-queue"
    config.poison_queue_name = "test-poison"
    config.table_name = "test-table"
    config.max_job_duration_minutes = 10
    config.max_retry_count = 3
    config.queue_visibility_timeout = 60
    config.worker_poll_interval_min = 1
    config.worker_poll_interval_max = 30
    config.table_connection_string = "mock_connection"
    config.queue_connection_string = "mock_connection"
    return config


@pytest.fixture
def app_with_mocks(mock_config):
    """Create ServiceApp with mocked Azure clients."""
    with (
        patch("praisonai_svc.app.BlobStorage"),
        patch("praisonai_svc.app.QueueManager"),
        patch("praisonai_svc.app.TableStorage"),
    ):
        app = ServiceApp("Test Service", config=mock_config)
        return app


def test_service_app_creation(app_with_mocks):
    """Test ServiceApp can be created."""
    assert app_with_mocks.service_name == "Test Service"
    assert app_with_mocks.app is not None


def test_health_endpoint(app_with_mocks):
    """Test health endpoint."""
    client = TestClient(app_with_mocks.app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Test Service"


def test_job_decorator(app_with_mocks):
    """Test @app.job decorator."""

    @app_with_mocks.job
    def test_handler(payload: dict) -> tuple[bytes, str, str]:
        return b"test", "text/plain", "test.txt"

    assert app_with_mocks.job_handler is not None
    assert app_with_mocks.job_handler == test_handler


def test_get_app(app_with_mocks):
    """Test get_app returns FastAPI instance."""
    fastapi_app = app_with_mocks.get_app()
    assert fastapi_app is not None
    assert hasattr(fastapi_app, "routes")
