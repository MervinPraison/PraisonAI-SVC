"""Azure integration modules."""

from praisonai_svc.azure.blob import BlobStorage
from praisonai_svc.azure.queue import QueueManager
from praisonai_svc.azure.table import TableStorage

__all__ = ["BlobStorage", "QueueManager", "TableStorage"]
