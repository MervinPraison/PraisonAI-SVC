"""
PraisonAI Service Framework

A unified framework that turns any PraisonAI Python package into a web service on Azure.
"""

__version__ = "1.0.0"

from praisonai_svc.app import ServiceApp
from praisonai_svc.models import JobRequest, JobResponse, JobStatus

__all__ = ["ServiceApp", "JobRequest", "JobResponse", "JobStatus", "__version__"]
