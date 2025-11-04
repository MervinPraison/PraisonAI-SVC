"""Azure Queue Storage integration."""

import json

from azure.storage.queue import QueueClient, QueueMessage

from praisonai_svc.models.config import ServiceConfig


class QueueManager:
    """Azure Queue Storage manager."""

    def __init__(self, config: ServiceConfig) -> None:
        """Initialize queue clients."""
        self.config = config
        self.queue_client = QueueClient.from_connection_string(
            config.queue_connection_string, queue_name=config.queue_name
        )
        self.poison_queue_client = QueueClient.from_connection_string(
            config.queue_connection_string, queue_name=config.poison_queue_name
        )
        self._ensure_queues()

    def _ensure_queues(self) -> None:
        """Ensure queues exist."""
        try:
            self.queue_client.create_queue()
        except Exception:
            pass  # Queue might already exist
        try:
            self.poison_queue_client.create_queue()
        except Exception:
            pass

    async def enqueue_job(self, job_id: str, payload: dict) -> None:
        """Add job to queue."""
        message = json.dumps({"job_id": job_id, "payload": payload})
        self.queue_client.send_message(
            message, visibility_timeout=self.config.queue_visibility_timeout
        )

    async def receive_messages(self, max_messages: int = 1) -> list[QueueMessage]:
        """Receive messages from queue."""
        messages = self.queue_client.receive_messages(
            max_messages=max_messages,
            visibility_timeout=self.config.queue_visibility_timeout,
        )
        return list(messages)

    async def delete_message(self, message: QueueMessage) -> None:
        """Delete message from queue."""
        self.queue_client.delete_message(message.id, message.pop_receipt)

    async def move_to_poison_queue(self, message: QueueMessage) -> None:
        """Move message to poison queue."""
        self.poison_queue_client.send_message(message.content)
        await self.delete_message(message)

    def get_queue_length(self) -> int:
        """Get approximate queue length."""
        properties = self.queue_client.get_queue_properties()
        return properties.approximate_message_count
