from auditlog.models import LogEntry
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=LogEntry)
def update_log_entry_additional_data_with_is_sent(sender, instance, **kwargs):
    """
    Sets the `is_sent` key in the `additional_data` dictionary of a new LogEntry
    instance to False.

    This function is intended to be used as a signal receiver for the `pre_save` signal
    of the `LogEntry` model. It is designed to modify the `additional_data` field
    of newly created LogEntry instances before they are saved to the database.

    This is a requirement of https://github.com/City-of-Helsinki/structured-log-transfer.
    When the structured log transfer tool finishes handling the data,
    it will then mark the LogEntry as sent (by updating
    `additional_data["is_sent"]=True`).

    Parameters:
        sender (LogEntry): The model class of the LogEntry instance being saved.
        instance (LogEntry): The LogEntry instance being saved.
        kwargs (dict): Additional keyword arguments passed to the signal handler.

    Returns:
        None
    """
    if not instance.pk:  # Check if the instance is new
        if not instance.additional_data:
            instance.additional_data = {}
        instance.additional_data["is_sent"] = False
