"""Main ServiceApp class for creating PraisonAI services."""

import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from praisonai_svc.azure import BlobStorage, QueueManager, TableStorage
from praisonai_svc.models import JobRequest, JobResponse, JobStatus
from praisonai_svc.models.config import ServiceConfig
from praisonai_svc.models.job import JobEntity


class ServiceApp:
    """Main application class for PraisonAI services."""

    def __init__(self, service_name: str, config: ServiceConfig | None = None) -> None:
        """Initialize service application."""
        self.service_name = service_name
        self.config = config or ServiceConfig()
        self.app = FastAPI(title=f"{service_name} API", version="1.0.0")
        self.job_handler: Callable[[dict[str, Any]], tuple[bytes, str, str]] | None = None

        # Initialize Azure clients
        self.blob_storage = BlobStorage(self.config)
        self.queue_manager = QueueManager(self.config)
        self.table_storage = TableStorage(self.config)

        # Setup middleware
        self._setup_middleware()

        # Setup routes
        self._setup_routes()

    def _setup_middleware(self) -> None:
        """Setup CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )

    def _setup_routes(self) -> None:
        """Setup API routes."""

        @self.app.get("/health")
        async def health() -> dict[str, str]:
            """Health check endpoint."""
            return {"status": "healthy", "service": self.service_name}

        @self.app.post("/jobs", response_model=JobResponse)
        async def create_job(request: JobRequest) -> JobResponse:
            """Create a new job."""
            # Check for duplicate job by hash
            job_hash = request.compute_hash()
            existing_job = await self.table_storage.find_job_by_hash(job_hash)

            if existing_job:
                # Return existing job if done
                if existing_job.Status == JobStatus.DONE.value:
                    return existing_job.to_response()
                # Return existing job if still processing
                if existing_job.Status == JobStatus.PROCESSING.value:
                    return existing_job.to_response()

            # Create new job
            job_id = str(uuid.uuid4())
            now = datetime.utcnow()

            job_entity = JobEntity(
                RowKey=job_id,
                Status=JobStatus.QUEUED.value,
                CreatedUTC=now,
                UpdatedUTC=now,
                JobHash=job_hash,
            )

            await self.table_storage.create_job(job_entity)
            await self.queue_manager.enqueue_job(job_id, request.payload)

            return job_entity.to_response()

        @self.app.get("/jobs/{job_id}", response_model=JobResponse)
        async def get_job(job_id: str) -> JobResponse:
            """Get job status."""
            job = await self.table_storage.get_job(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            return job.to_response()

        @self.app.get("/jobs/{job_id}/download")
        async def download_job(job_id: str) -> dict[str, str]:
            """Generate fresh download URL."""
            job = await self.table_storage.get_job(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")

            if job.Status != JobStatus.DONE.value:
                raise HTTPException(status_code=400, detail="Job not ready for download")

            if not job.BlobName:
                raise HTTPException(status_code=500, detail="Blob name not found")

            # Generate fresh SAS URL
            download_url = self.blob_storage.generate_sas_url(job.BlobName)
            return {"download_url": download_url}

    def job(
        self, func: Callable[[dict[str, Any]], tuple[bytes, str, str]]
    ) -> Callable[[dict[str, Any]], tuple[bytes, str, str]]:
        """Decorator to register job handler.

        Handler should return: (file_data, content_type, filename)
        """
        self.job_handler = func
        return func

    def get_app(self) -> FastAPI:
        """Get FastAPI application instance."""
        return self.app
