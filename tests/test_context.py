import time

import pytest
from auditlog.models import LogEntry
from django.db.models.signals import pre_save

from auditlog_extra.context import (
    AuditLogContextService,
    _set_request_path,
    auditlog_request_context_value,
    set_request_path,
)


@pytest.mark.django_db
def test_set_request_path_to_additional_data(log_entry):
    """Test adding request path to LogEntry.additional_data."""

    request_path = "/test-path/"
    AuditLogContextService.set_request_path_to_additional_data(log_entry, request_path)

    assert log_entry.additional_data["request_path"] == request_path


@pytest.mark.django_db
def test_set_request_path_context_manager(log_entry):
    """Test the set_request_path context manager."""

    request_path = "/test-path/"
    with set_request_path(request_path):
        pre_save.send(sender=LogEntry, instance=log_entry)

    assert log_entry.additional_data["request_path"] == request_path


@pytest.mark.django_db
def test_set_request_path_context_manager_no_request_path(log_entry):
    """Test the context manager without providing a request path."""

    with set_request_path():
        pre_save.send(sender=LogEntry, instance=log_entry)

    assert log_entry.additional_data["request_path"] is None


@pytest.mark.django_db
def test_set_request_path_signal_receiver(log_entry):
    """Test the _set_request_path signal receiver."""

    request_path = "/test-path/"
    signal_duid = ("set_request_path", time.time())

    # Set the context variable directly
    auditlog_request_context_value.set(
        {
            "signal_duid": signal_duid,
            "request_path": request_path,
        }
    )

    # Simulate the context variable being set
    _set_request_path(
        sender=LogEntry,
        instance=log_entry,
        signal_duid=signal_duid,
        request_path=request_path,
    )

    assert log_entry.additional_data["request_path"] == request_path


@pytest.mark.django_db
def test_set_request_path_signal_receiver_wrong_signal_duid(log_entry):
    """Test the signal receiver with an incorrect signal_duid."""

    request_path = "/test-path/"
    wrong_signal_duid = ("wrong_signal", time.time())

    # Simulate the context variable being set
    _set_request_path(
        sender=LogEntry,
        instance=log_entry,
        signal_duid=wrong_signal_duid,
        request_path=request_path,
    )

    # Assert that additional_data is not modified
    assert log_entry.additional_data is None


def test_set_request_path_nested_context_managers(log_entry):
    """Test nested context managers to ensure no duplicate signals."""

    request_path1 = "/test-path1/"
    request_path2 = "/test-path2/"

    with set_request_path(request_path1):
        with set_request_path(request_path2):
            pre_save.send(sender=LogEntry, instance=log_entry)

        assert log_entry.additional_data["request_path"] == request_path2

    # After the inner context manager exits, the outer one should still work
    with set_request_path(request_path1):
        pre_save.send(sender=LogEntry, instance=log_entry, created=False)

    assert log_entry.additional_data["request_path"] == request_path1
