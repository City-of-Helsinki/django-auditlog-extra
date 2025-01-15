from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuditLogExtraConfig(AppConfig):
    name = "auditlog_extra"
    verbose_name = _("auditlog extra")
