"""Job-related data models."""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job status enumeration."""

    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class JobRequest(BaseModel):
    """Request model for creating a new job."""

    payload: dict[str, Any] = Field(..., description="Job payload (YAML/JSON data)")
    service_name: str | None = Field(None, description="Service name override")

    def compute_hash(self) -> str:
        """Generate deterministic hash for idempotent processing."""
        canonical = json.dumps(self.payload, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()


class JobResponse(BaseModel):
    """Response model for job status."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    download_url: str | None = Field(None, description="Download URL when status is done")
    error_msg: str | None = Field(None, description="Error message if status is error")
    created_utc: datetime = Field(..., description="Job creation timestamp")
    updated_utc: datetime = Field(..., description="Last update timestamp")
    started_utc: datetime | None = Field(None, description="Processing start timestamp")
    retry_count: int = Field(0, description="Number of retry attempts")


class JobEntity(BaseModel):
    """Table Storage entity model for jobs."""

    PartitionKey: str = "praison"
    RowKey: str  # job_id
    Status: str
    DownloadURL: str | None = None
    CreatedUTC: datetime
    UpdatedUTC: datetime
    StartedUTC: datetime | None = None
    RetryCount: int = 0
    JobHash: str
    ErrorMsg: str | None = None
    BlobName: str | None = None

    def to_response(self) -> JobResponse:
        """Convert to JobResponse model."""
        return JobResponse(
            job_id=self.RowKey,
            status=JobStatus(self.Status),
            download_url=self.DownloadURL,
            error_msg=self.ErrorMsg,
            created_utc=self.CreatedUTC,
            updated_utc=self.UpdatedUTC,
            started_utc=self.StartedUTC,
            retry_count=self.RetryCount,
        )
