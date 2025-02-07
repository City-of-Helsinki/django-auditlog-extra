import pytest
from auditlog.models import LogEntry
from auditlog.registry import auditlog
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_additional_data_is_sent_is_set_to_false_on_log_entry_creation():
    """Whenever a new LogEntry instance is created (and is preparing to be saved to db),
    it should have the `additional_data` field populated with `is_sent` boolean (set to False).
    This is a requirement of https://github.com/City-of-Helsinki/structured-log-transfer.
    When the structured log transfer tool finishes handling the data,
    it will then mark the LogEntry as sent (by updating `additional_data["is_sent"]=True`).
    """
    # register User model to auditlog registry.
    auditlog.register(User)
    # By creating a new User instance, we will also create a LogEntry for it.
    user = User.objects.create(username="testuser")
    log_entry = LogEntry.objects.get_for_object(user).first()
    assert log_entry.additional_data["is_sent"] is False
