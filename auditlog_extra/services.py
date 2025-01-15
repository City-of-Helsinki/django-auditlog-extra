from typing import Optional

from auditlog.models import LogEntry


class AuditLogContextService:
    """Service class for managing audit log context data."""

    @staticmethod
    def set_request_path_to_additional_data(
        log_entry: LogEntry, request_path: Optional[str]
    ):
        """
        Add the request path to the `additional_data` field of a LogEntry.

        Args:
            log_entry (LogEntry): The LogEntry instance to modify.
            request_path (Optional[str]): The request path to store,
                                            None if not available.
        """
        if not log_entry.additional_data:
            log_entry.additional_data = {}
        log_entry.additional_data["request_path"] = request_path
