"""Test data models."""

from datetime import datetime

from praisonai_svc.models import JobRequest, JobResponse, JobStatus
from praisonai_svc.models.job import JobEntity


def test_job_request_hash():
    """Test JobRequest hash computation."""
    payload1 = {"key": "value", "number": 42}
    payload2 = {"number": 42, "key": "value"}  # Different order, same content

    req1 = JobRequest(payload=payload1)
    req2 = JobRequest(payload=payload2)

    # Hashes should be identical (canonical JSON)
    assert req1.compute_hash() == req2.compute_hash()


def test_job_request_different_hash():
    """Test different payloads produce different hashes."""
    req1 = JobRequest(payload={"key": "value1"})
    req2 = JobRequest(payload={"key": "value2"})

    assert req1.compute_hash() != req2.compute_hash()


def test_job_status_enum():
    """Test JobStatus enum values."""
    assert JobStatus.QUEUED.value == "queued"
    assert JobStatus.PROCESSING.value == "processing"
    assert JobStatus.DONE.value == "done"
    assert JobStatus.ERROR.value == "error"


def test_job_response_model():
    """Test JobResponse model."""
    now = datetime.utcnow()
    response = JobResponse(
        job_id="test-123",
        status=JobStatus.DONE,
        download_url="https://example.com/file.pptx",
        created_utc=now,
        updated_utc=now,
        retry_count=0,
    )

    assert response.job_id == "test-123"
    assert response.status == JobStatus.DONE
    assert response.download_url == "https://example.com/file.pptx"
    assert response.retry_count == 0


def test_job_entity_to_response():
    """Test JobEntity to JobResponse conversion."""
    now = datetime.utcnow()
    entity = JobEntity(
        RowKey="job-456",
        Status="done",
        CreatedUTC=now,
        UpdatedUTC=now,
        JobHash="abc123",
        DownloadURL="https://example.com/file.pptx",
    )

    response = entity.to_response()

    assert response.job_id == "job-456"
    assert response.status == JobStatus.DONE
    assert response.download_url == "https://example.com/file.pptx"
