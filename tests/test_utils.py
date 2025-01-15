import pytest
from auditlog.models import LogEntry
from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from auditlog_extra.tests.models import DummyTestModel
from auditlog_extra.utils import AuditLogConfigurationHelper


@pytest.mark.parametrize(
    "model, expected_key",
    [
        (LogEntry, "auditlog.logentry"),
        (DummyTestModel, "auditlog_extra.dummytestmodel"),
    ],
)
def test_get_app_model_key(model, expected_key):
    """Test that get_app_model_key returns the correct key."""
    key = AuditLogConfigurationHelper.get_app_model_key(model)
    assert key == expected_key


@pytest.mark.parametrize(
    "excluded_model_apps",
    [
        [
            "sessions.session",
        ],
        ["sessions.session", "contenttypes.contenttype"],
    ],
)
def test_get_excluded_models(excluded_model_apps, settings):
    settings.AUDITLOG_INCLUDE_ALL_MODELS = True
    settings.AUDITLOG_EXCLUDE_TRACKING_MODELS = excluded_model_apps
    excluded_models = AuditLogConfigurationHelper.get_excluded_models()
    assert (
        excluded_models - AuditLogConfigurationHelper.get_excluded_by_default()
    ) == set(
        AuditLogConfigurationHelper.get_model_classes(model_app)[0]
        for model_app in excluded_model_apps
    )


@pytest.mark.parametrize(
    "included_model_apps",
    [
        [
            "sessions.session",
        ],
        ["sessions.session", "contenttypes.contenttype"],
    ],
)
def test_get_included_models(included_model_apps, settings):
    settings.AUDITLOG_INCLUDE_ALL_MODELS = True
    settings.AUDITLOG_INCLUDE_TRACKING_MODELS = included_model_apps
    included_models = AuditLogConfigurationHelper.get_included_models()
    assert included_models == set(
        AuditLogConfigurationHelper.get_model_classes(model_app)[0]
        for model_app in included_model_apps
    )


def test_get_unconfigured_models(settings):
    settings.AUDITLOG_INCLUDE_ALL_MODELS = True
    settings.AUDITLOG_EXCLUDE_TRACKING_MODELS = []
    settings.AUDITLOG_INCLUDE_TRACKING_MODELS = []
    defaulty_excluded = AuditLogConfigurationHelper.get_excluded_by_default()
    unconfigured_models = AuditLogConfigurationHelper.get_unconfigured_models()
    all_models = set(apps.get_models(include_auto_created=True))
    assert len(all_models) > 0
    assert (
        unconfigured_models | defaulty_excluded
    ) == all_models  # Initially, all should be unconfigured
    settings.AUDITLOG_INCLUDE_TRACKING_MODELS = ["contenttypes.contenttype"]
    assert (
        len(unconfigured_models - AuditLogConfigurationHelper.get_unconfigured_models())
        == 1
    )
    settings.AUDITLOG_EXCLUDE_TRACKING_MODELS = ["sessions.session"]
    assert (
        len(unconfigured_models - AuditLogConfigurationHelper.get_unconfigured_models())
        == 2
    )


def test_raise_error_if_unconfigured_models_no_error(settings):
    """Test that raise_error_if_unconfigured_models does not raise an error
    when all models are configured.
    """
    settings.AUDITLOG_INCLUDE_ALL_MODELS = True
    all_models = AuditLogConfigurationHelper.get_app_models()
    app_model_keys = [
        AuditLogConfigurationHelper.get_app_model_key(model) for model in all_models
    ]
    settings.AUDITLOG_EXCLUDE_TRACKING_MODELS = app_model_keys[::2]
    settings.AUDITLOG_INCLUDE_TRACKING_MODELS = app_model_keys[1::2]
    try:
        AuditLogConfigurationHelper.raise_error_if_unconfigured_models()
    except ImproperlyConfigured:
        raise AssertionError("Should not raise ImproperlyConfigured")


def test_raise_error_if_unconfigured_models(settings):
    """Test that raise_error_if_unconfigured_models raises an error when
    there are unconfigured models.
    """
    all_models = AuditLogConfigurationHelper.get_app_models()
    assert len(all_models) > 0

    with pytest.raises(ImproperlyConfigured):
        AuditLogConfigurationHelper.raise_error_if_unconfigured_models()
