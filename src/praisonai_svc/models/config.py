"""Configuration models."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceConfig(BaseSettings):
    """Service configuration from environment variables."""

    model_config = SettingsConfigDict(env_prefix="PRAISONAI_", case_sensitive=False)

    # Azure Storage
    azure_storage_connection_string: str
    azure_table_conn_string: str | None = None
    azure_queue_conn_string: str | None = None

    # Storage names
    blob_container_name: str = "praison-output"
    queue_name: str = "praison-jobs"
    poison_queue_name: str = "praison-jobs-poison"
    table_name: str = "jobs"

    # Job settings
    max_job_duration_minutes: int = 10
    max_retry_count: int = 3
    queue_visibility_timeout: int = 60

    # API settings
    api_key: str | None = None
    cors_origins: list[str] = ["*"]
    max_payload_size_mb: int = 1

    # Worker settings
    worker_poll_interval_min: int = 1
    worker_poll_interval_max: int = 30

    @property
    def table_connection_string(self) -> str:
        """Get table connection string (fallback to storage connection string)."""
        return self.azure_table_conn_string or self.azure_storage_connection_string

    @property
    def queue_connection_string(self) -> str:
        """Get queue connection string (fallback to storage connection string)."""
        return self.azure_queue_conn_string or self.azure_storage_connection_string
