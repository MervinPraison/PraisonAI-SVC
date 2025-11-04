"""Worker module for processing jobs from queue."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

from praisonai_svc.azure import BlobStorage, QueueManager, TableStorage
from praisonai_svc.models import JobStatus
from praisonai_svc.models.config import ServiceConfig

logger = logging.getLogger(__name__)


class Worker:
    """Job worker with exponential backoff polling."""

    def __init__(
        self,
        config: ServiceConfig,
        job_handler: Any,
    ) -> None:
        """Initialize worker."""
        self.config = config
        self.job_handler = job_handler
        self.blob_storage = BlobStorage(config)
        self.queue_manager = QueueManager(config)
        self.table_storage = TableStorage(config)
        self.running = False

    async def poll_queue_with_backoff(self) -> None:
        """Poll queue with exponential backoff."""
        backoff = self.config.worker_poll_interval_min
        max_backoff = self.config.worker_poll_interval_max

        logger.info("Worker started")
        self.running = True

        while self.running:
            try:
                messages = await self.queue_manager.receive_messages(max_messages=1)

                if messages:
                    backoff = self.config.worker_poll_interval_min  # Reset on success
                    for message in messages:
                        await self._process_message(message)
                else:
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, max_backoff)  # Exponential increase
                    logger.debug(f"Queue empty, backing off to {backoff}s")

            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(backoff)

    async def _process_message(self, message: Any) -> None:
        """Process a single queue message."""
        try:
            data = json.loads(message.content)
            job_id = data["job_id"]
            payload = data["payload"]

            logger.info(f"Processing job {job_id}")

            # Check dequeue count for poison queue
            if message.dequeue_count > self.config.max_retry_count:
                logger.warning(f"Job {job_id} exceeded retry limit, moving to poison queue")
                await self.queue_manager.move_to_poison_queue(message)
                await self.table_storage.update_job(
                    job_id,
                    status=JobStatus.ERROR,
                    error_msg="Exceeded maximum retry attempts",
                )
                return

            # Update job status to processing
            await self.table_storage.update_job(
                job_id,
                status=JobStatus.PROCESSING,
                started_utc=datetime.utcnow(),
                increment_retry=True,
            )

            # Check for timeout
            job = await self.table_storage.get_job(job_id)
            if job and job.StartedUTC:
                elapsed = datetime.utcnow() - job.StartedUTC
                max_duration = timedelta(minutes=self.config.max_job_duration_minutes)
                if elapsed > max_duration:
                    logger.warning(f"Job {job_id} timed out")
                    await self.table_storage.update_job(
                        job_id,
                        status=JobStatus.ERROR,
                        error_msg=f"Job exceeded {self.config.max_job_duration_minutes} minute timeout",
                    )
                    await self.queue_manager.delete_message(message)
                    return

            # Execute job handler
            try:
                file_data, content_type, filename = self.job_handler(payload)

                # Upload to blob storage
                blob_name = f"{job_id}/{filename}"
                await self.blob_storage.upload_blob(file_data, blob_name)

                # Generate SAS URL
                download_url = self.blob_storage.generate_sas_url(blob_name)

                # Update job status to done
                await self.table_storage.update_job(
                    job_id,
                    status=JobStatus.DONE,
                    download_url=download_url,
                    blob_name=blob_name,
                )

                logger.info(f"Job {job_id} completed successfully")

            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
                await self.table_storage.update_job(
                    job_id, status=JobStatus.ERROR, error_msg=str(e)
                )

            # Delete message from queue
            await self.queue_manager.delete_message(message)

        except Exception as e:
            logger.error(f"Failed to process message: {e}")

    def stop(self) -> None:
        """Stop the worker."""
        self.running = False
        logger.info("Worker stopped")


async def run_worker(config: ServiceConfig, job_handler: Any) -> None:
    """Run worker process."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    worker = Worker(config, job_handler)
    await worker.poll_queue_with_backoff()
