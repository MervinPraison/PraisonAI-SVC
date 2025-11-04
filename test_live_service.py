#!/usr/bin/env python
"""Live service test - creates a working service and tests it with mock Azure."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path
sys.path.insert(0, "src")

from praisonai_svc import ServiceApp
from praisonai_svc.models.config import ServiceConfig


def test_live_service():
    """Test a complete service with mocked Azure."""
    print("=" * 60)
    print("LIVE SERVICE TEST")
    print("=" * 60)

    # Mock Azure services
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

        # Create mock config
        config = MagicMock(spec=ServiceConfig)
        config.azure_storage_connection_string = "mock_connection"
        config.cors_origins = ["*"]
        config.table_connection_string = "mock_connection"
        config.queue_connection_string = "mock_connection"

        print("\n1. Creating ServiceApp...")
        app = ServiceApp("Test PPT Service", config=config)
        print("   ✓ ServiceApp created")

        print("\n2. Registering job handler...")

        @app.job
        def generate_ppt(payload: dict) -> tuple[bytes, str, str]:
            """Generate a mock PPT file."""
            title = payload.get("title", "Untitled")
            content = f"Mock PPT: {title}".encode()
            return (
                content,
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                f"{title}.pptx",
            )

        print("   ✓ Job handler registered")

        print("\n3. Testing FastAPI app...")
        fastapi_app = app.get_app()
        assert fastapi_app is not None
        print("   ✓ FastAPI app accessible")

        print("\n4. Testing routes...")
        routes = [route.path for route in fastapi_app.routes]
        expected_routes = ["/health", "/jobs", "/jobs/{job_id}", "/jobs/{job_id}/download"]
        for route in expected_routes:
            assert any(route in r for r in routes), f"Missing route: {route}"
        print(f"   ✓ All routes present: {expected_routes}")

        print("\n5. Testing health endpoint...")
        from fastapi.testclient import TestClient

        client = TestClient(fastapi_app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"   ✓ Health check: {data}")

        print("\n6. Testing job creation...")
        response = client.post("/jobs", json={"payload": {"title": "My Presentation"}})
        assert response.status_code == 200
        job_data = response.json()
        assert "job_id" in job_data
        assert job_data["status"] == "queued"
        print(f"   ✓ Job created: {job_data['job_id']}")

        print("\n7. Verifying Azure calls...")
        assert mock_table_instance.create_job.called
        assert mock_queue_instance.enqueue_job.called
        print("   ✓ Azure services called correctly")

        print("\n8. Testing job handler execution...")
        result = generate_ppt({"title": "Test"})
        assert len(result) == 3
        assert result[0] == b"Mock PPT: Test"
        assert "presentationml" in result[1] or "pptx" in result[1]
        assert result[2] == "Test.pptx"
        print(f"   ✓ Handler works: {result[2]}, content-type: {result[1]}")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True


if __name__ == "__main__":
    try:
        success = test_live_service()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
