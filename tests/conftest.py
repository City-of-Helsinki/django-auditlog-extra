import pytest
from auditlog.models import LogEntry


@pytest.fixture
def log_entry():
    return LogEntry()
