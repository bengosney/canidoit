from django.tasks import task_backends

import pytest


@pytest.fixture
def queue():
    """The dummy task backend, cleared, so tests can see what was enqueued."""
    backend = task_backends["default"]
    backend.results.clear()
    return backend
