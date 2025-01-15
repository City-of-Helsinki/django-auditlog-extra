from typing import List, Set

from auditlog.registry import auditlog
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase


class AuditLogConfigurationHelper:
    """
    A helper class for managing audit log configuration in your Django project.

    This class provides methods to:

    - Retrieve all models in your project.
    - Identify models that are not explicitly configured for audit logging.
    - Raise an error if any models are not configured when
        `AUDITLOG_INCLUDE_ALL_MODELS` is enabled.

    This helps ensure that all models are either explicitly included or excluded
    from audit logging, preventing accidental omissions.
    """

    @staticmethod
    def get_app_models() -> List[ModelBase]:
        """
        Fetch all models in your Django project, including those automatically
        created by Django (like those for user accounts or sessions).
        """
        return apps.get_models(include_auto_created=True)

    @staticmethod
    def get_app_model_key(model: ModelBase) -> str:
        """
        Returns a string representation of the model,
        like 'app_label.model_name'.
        """
        return f"{model._meta.app_label}.{model._meta.model_name}"

    @staticmethod
    def get_model_classes(app_model: str) -> List[ModelBase]:
        return auditlog._get_model_classes(app_model)

    @classmethod
    def print_app_models(cls) -> None:
        """Prints all models in the project to the console."""
        for model in cls.get_app_models():
            print(cls.get_app_model_key(model))

    @classmethod
    def get_excluded_by_default(cls):
        return set(
            cls.get_model_classes(app_model)[0]
            for app_model in auditlog.DEFAULT_EXCLUDE_MODELS
        )

    @classmethod
    def get_excluded_models(cls) -> Set[ModelBase]:
        """
        Returns a set of models that are explicitly excluded from audit logging.
        """
        excluded_models: Set[ModelBase] = set()
        if (
            hasattr(settings, "AUDITLOG_INCLUDE_ALL_MODELS")
            and settings.AUDITLOG_INCLUDE_ALL_MODELS
        ):
            excluded_models = set(
                auditlog._get_exclude_models(
                    getattr(settings, "AUDITLOG_EXCLUDE_TRACKING_MODELS", [])
                )
            )

        return excluded_models | cls.get_excluded_by_default()

    @classmethod
    def get_included_models(cls) -> Set[ModelBase]:
        """Returns a set of models in included mapping for audit logging."""
        included_models = []
        models = getattr(settings, "AUDITLOG_INCLUDE_TRACKING_MODELS", [])
        for model in models:
            if isinstance(model, str):
                for model_class in cls.get_model_classes(model):
                    included_models.append(model_class)
            elif isinstance(model, dict):
                appmodel = cls.get_model_classes(model["model"])
                included_models.append(appmodel[0])
        return set(included_models)

    @classmethod
    def get_unconfigured_models(cls) -> Set[ModelBase]:
        """
        Returns a set of models that are neither registered nor excluded
        from audit logging.
        """
        excluded_models = cls.get_excluded_models()
        included_models = cls.get_included_models()
        all_models = set(cls.get_app_models())
        return all_models - excluded_models - included_models

    @classmethod
    def raise_error_if_unconfigured_models(cls) -> None:
        """
        Raises an ImproperlyConfigured exception if there are any models
        that are not explicitly configured for audit logging.
        """
        unconfigured_models = cls.get_unconfigured_models()
        if unconfigured_models:
            unconfigured_keys = [
                cls.get_app_model_key(model) for model in unconfigured_models
            ]
            raise ImproperlyConfigured(
                "AUDITLOG_INCLUDE_ALL_MODELS is enabled, requiring "
                "explicit configuration of all models. "
                "The following models ({count}) are not configured: {entries}. "
                "Please register them with `auditlog.register` "
                "or add them to `AUDITLOG_EXCLUDE_TRACKING_MODELS` "
                "in your Django settings.".format(
                    count=len(unconfigured_keys),
                    entries=", ".join(f"`{key}`" for key in unconfigured_keys),
                )
            )
