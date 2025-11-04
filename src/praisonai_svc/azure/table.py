"""Azure Table Storage integration."""

from datetime import datetime

from azure.data.tables import TableClient
from tenacity import retry, stop_after_attempt, wait_exponential

from praisonai_svc.models.config import ServiceConfig
from praisonai_svc.models.job import JobEntity, JobStatus


class TableStorage:
    """Azure Table Storage manager."""

    def __init__(self, config: ServiceConfig) -> None:
        """Initialize table client."""
        self.config = config
        self.client = TableClient.from_connection_string(
            config.table_connection_string, table_name=config.table_name
        )
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Ensure table exists."""
        try:
            self.client.create_table()
        except Exception:
            pass  # Table might already exist

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_job(self, job_entity: JobEntity) -> None:
        """Create job entity."""
        entity = {
            "PartitionKey": job_entity.PartitionKey,
            "RowKey": job_entity.RowKey,
            "Status": job_entity.Status,
            "CreatedUTC": job_entity.CreatedUTC,
            "UpdatedUTC": job_entity.UpdatedUTC,
            "JobHash": job_entity.JobHash,
            "RetryCount": job_entity.RetryCount,
        }
        self.client.create_entity(entity)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def get_job(self, job_id: str) -> JobEntity | None:
        """Get job entity by ID."""
        try:
            entity = self.client.get_entity(partition_key="praison", row_key=job_id)
            return JobEntity(
                RowKey=entity["RowKey"],
                Status=entity["Status"],
                CreatedUTC=entity["CreatedUTC"],
                UpdatedUTC=entity["UpdatedUTC"],
                JobHash=entity["JobHash"],
                RetryCount=entity.get("RetryCount", 0),
                DownloadURL=entity.get("DownloadURL"),
                StartedUTC=entity.get("StartedUTC"),
                ErrorMsg=entity.get("ErrorMsg"),
                BlobName=entity.get("BlobName"),
            )
        except Exception:
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def update_job(
        self,
        job_id: str,
        status: JobStatus | None = None,
        download_url: str | None = None,
        error_msg: str | None = None,
        started_utc: datetime | None = None,
        blob_name: str | None = None,
        increment_retry: bool = False,
    ) -> None:
        """Update job entity."""
        entity = self.client.get_entity(partition_key="praison", row_key=job_id)

        if status:
            entity["Status"] = status.value
        if download_url:
            entity["DownloadURL"] = download_url
        if error_msg:
            entity["ErrorMsg"] = error_msg[:10000]  # Truncate to 10KB
        if started_utc:
            entity["StartedUTC"] = started_utc
        if blob_name:
            entity["BlobName"] = blob_name
        if increment_retry:
            entity["RetryCount"] = entity.get("RetryCount", 0) + 1

        entity["UpdatedUTC"] = datetime.utcnow()
        self.client.update_entity(entity, mode="merge")

    async def find_job_by_hash(self, job_hash: str) -> JobEntity | None:
        """Find job by hash for idempotency check."""
        try:
            query = f"JobHash eq '{job_hash}'"
            entities = self.client.query_entities(query)
            for entity in entities:
                return JobEntity(
                    RowKey=entity["RowKey"],
                    Status=entity["Status"],
                    CreatedUTC=entity["CreatedUTC"],
                    UpdatedUTC=entity["UpdatedUTC"],
                    JobHash=entity["JobHash"],
                    RetryCount=entity.get("RetryCount", 0),
                    DownloadURL=entity.get("DownloadURL"),
                    StartedUTC=entity.get("StartedUTC"),
                    ErrorMsg=entity.get("ErrorMsg"),
                    BlobName=entity.get("BlobName"),
                )
        except Exception:
            pass
        return None
