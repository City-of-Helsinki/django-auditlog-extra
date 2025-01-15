import contextlib
import time
from contextvars import ContextVar
from functools import partial
from typing import Any, Optional, Type

from auditlog.context import auditlog_value
from auditlog.models import LogEntry
from django.db.models.signals import pre_save

from auditlog_extra.services import AuditLogContextService

auditlog_request_context_value = ContextVar("auditlog_value_request")


@contextlib.contextmanager
def set_request_path(request_path: Optional[str] = None):
    """
    Store the request path in the LogEntry's `additional_data` field.

    This context manager uses a ContextVar to store the request path and
    connects a signal receiver to automatically add it to LogEntry instances.
    It uses a unique signal dispatch uid to prevent duplicate signals when nested.

    NOTE: the idea for the implemenation is copied from the django-auditlog itself:
    https://github.com/jazzband/django-auditlog/blob/6e51997728c819f9a19778e84d808546013b0242/auditlog/context.py
    """
    # Initialize thread local storage
    context_data = {
        "signal_duid": ("set_request_path", time.time()),
        "request_path": request_path,
    }
    auditlog_request_context_value.set(context_data)

    # Connect signal for automatic logging
    set_request_path = partial(
        _set_request_path, signal_duid=context_data["signal_duid"]
    )
    pre_save.connect(
        set_request_path,
        sender=LogEntry,
        dispatch_uid=context_data["signal_duid"],
        weak=False,
    )

    try:
        yield
    finally:
        try:
            auditlog = auditlog_request_context_value.get()
        except LookupError:
            pass
        else:
            pre_save.disconnect(sender=LogEntry, dispatch_uid=auditlog["signal_duid"])


def _set_request_path(
    sender: Type[LogEntry], instance: LogEntry, signal_duid: Any, **kwargs
):
    """
    Signal receiver to add the request path to LogEntry.additional_data.

    This receiver retrieves the request path from the context and adds it to the
    `additional_data` field of the LogEntry instance. It ensures that only the
    correct signal (identified by `signal_duid`) is processed.

    This function becomes a valid signal receiver when it is curried with the target
    and a dispatch id.

    Args:
        sender (Type[LogEntry]): The sender of the signal (LogEntry model).
        instance (LogEntry): The LogEntry instance being saved.
        signal_duid (Any): The unique identifier for this signal.
        **kwargs: Any additional keyword arguments.
    """
    try:
        auditlog = auditlog_request_context_value.get()
    except LookupError:
        pass
    else:
        if signal_duid != auditlog["signal_duid"]:
            return
        AuditLogContextService.set_request_path_to_additional_data(
            instance, auditlog["request_path"]
        )


def get_request_path():
    return auditlog_request_context_value.get(None)


def get_actor():
    return auditlog_value.get(None)
