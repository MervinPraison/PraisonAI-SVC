"""Test that all imports work correctly."""



def test_main_imports():
    """Test main package imports."""
    from praisonai_svc import JobRequest, JobResponse, JobStatus, ServiceApp, __version__

    assert ServiceApp is not None
    assert JobRequest is not None
    assert JobResponse is not None
    assert JobStatus is not None
    assert __version__ == "1.0.0"


def test_model_imports():
    """Test model imports."""
    from praisonai_svc.models import JobRequest, JobResponse, JobStatus, ServiceConfig
    from praisonai_svc.models.job import JobEntity

    assert JobRequest is not None
    assert JobResponse is not None
    assert JobStatus is not None
    assert ServiceConfig is not None
    assert JobEntity is not None


def test_azure_imports():
    """Test Azure integration imports."""
    from praisonai_svc.azure import BlobStorage, QueueManager, TableStorage

    assert BlobStorage is not None
    assert QueueManager is not None
    assert TableStorage is not None


def test_worker_import():
    """Test worker import."""
    from praisonai_svc.worker import Worker, run_worker

    assert Worker is not None
    assert run_worker is not None


def test_cli_import():
    """Test CLI import."""
    from praisonai_svc.cli import main

    assert main is not None
