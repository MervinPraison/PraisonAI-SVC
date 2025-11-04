"""Azure Blob Storage integration with retry logic."""

from datetime import datetime, timedelta

from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas
from tenacity import retry, stop_after_attempt, wait_exponential

from praisonai_svc.models.config import ServiceConfig


class BlobStorage:
    """Azure Blob Storage manager with retry logic."""

    def __init__(self, config: ServiceConfig) -> None:
        """Initialize blob storage client."""
        self.config = config
        self.client = BlobServiceClient.from_connection_string(
            config.azure_storage_connection_string
        )
        self.container_name = config.blob_container_name
        self._ensure_container()

    def _ensure_container(self) -> None:
        """Ensure container exists."""
        try:
            container_client = self.client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
        except Exception:
            pass  # Container might already exist

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def upload_blob(self, data: bytes, filename: str) -> str:
        """Upload blob with retry logic."""
        blob_client = self.client.get_blob_client(container=self.container_name, blob=filename)
        blob_client.upload_blob(data, overwrite=True)
        return filename

    def generate_sas_url(self, blob_name: str, expiry_hours: int = 1) -> str:
        """Generate SAS URL for blob download."""
        sas_token = generate_blob_sas(
            account_name=self.client.account_name,
            container_name=self.container_name,
            blob_name=blob_name,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=expiry_hours),
            account_key=self.client.credential.account_key,
        )
        return (
            f"https://{self.client.account_name}.blob.core.windows.net/"
            f"{self.container_name}/{blob_name}?{sas_token}"
        )

    async def delete_blob(self, blob_name: str) -> None:
        """Delete a blob."""
        blob_client = self.client.get_blob_client(container=self.container_name, blob=blob_name)
        blob_client.delete_blob()
