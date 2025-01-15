from typing import List, Optional
from unittest import mock

import pytest
from auditlog.context import set_actor
from auditlog.models import LogEntry
from auditlog.registry import auditlog
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory

from auditlog_extra.mixins import AuditlogAdminViewAccessLogMixin
from auditlog_extra.tests.models import DummyTestModel

User = get_user_model()

REMOTE_ADDR = "127.0.0.1"


@pytest.fixture(autouse=True)
def register_auditlog():
    auditlog.register(DummyTestModel)
    yield
    ContentType.objects.clear_cache()


@pytest.fixture
def user():
    return User.objects.create_user(
        username="testuser",
        password="testpassword",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def obj1():
    return DummyTestModel(id=1, text_field="text1", number_field=1, boolean_field=True)


@pytest.fixture
def obj2():
    return DummyTestModel(id=2, text_field="text2", number_field=2, boolean_field=False)


@pytest.fixture
def all_objects(obj1, obj2):
    return (obj1, obj2)


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def model_admin(all_objects):
    (obj1, obj2) = all_objects

    def get_model_admin(result_list: Optional[List] = None, **kwargs):
        class MockedChangeList(ChangeList):
            show_full_result_count = False

            def has_change_permission(self, request, obj=None):
                return True

            def has_delete_permission(self, request, obj=None):
                return True

            def get_queryset(self, request):
                return list(result_list or [])

            def get_results(self, request):
                """
                A mocked get_result is needed to bypass QuerySet functions usage,
                since we are dealing with a static list of unmanaged DummyTestModel
                instances.
                """
                paginator = self.model_admin.get_paginator(
                    request, self.queryset, self.list_per_page
                )
                # Get the number of objects, with admin filters applied.
                result_count = paginator.count
                can_show_all = result_count <= self.list_max_show_all
                multi_page = result_count > self.list_per_page
                self.result_count = result_count
                self.show_full_result_count = self.model_admin.show_full_result_count
                self.show_admin_actions = False
                self.full_result_count = None
                self.can_show_all = can_show_all
                self.multi_page = multi_page
                self.paginator = paginator
                # Mock the result_list of objects.
                self.result_list = self.get_queryset(request)

        class DummyTestModelAdmin(AuditlogAdminViewAccessLogMixin, admin.ModelAdmin):
            """
            Register DummyTestModel with DummyTestModelAdmin to test
            Django admin views.
            """

            enable_list_view_audit_logging = False

            def get_changelist(self, request, **kwargs):
                return MockedChangeList

            def to_field_allowed(self, request, to_field):
                return True

            def get_deleted_objects(self, objs, request):
                return [
                    self.get_object(request, obj1.pk),
                    {},
                    False,
                    True,
                ]

        return DummyTestModelAdmin(DummyTestModel, admin.site)

    return get_model_admin(result_list=list(all_objects))


def assert_access_log(log: LogEntry, obj, user):
    assert log.actor == user
    assert log.remote_addr == REMOTE_ADDR
    assert log.content_type.model == obj._meta.model_name
    assert log.object_id == obj.id


@pytest.mark.django_db
@pytest.mark.parametrize("is_write_accessed_enabled", (True, False))
def test_changelist_view_logging(
    factory, user, model_admin, is_write_accessed_enabled, all_objects
):
    auditlog_count_on_start = LogEntry.objects.count()
    model_admin.enable_list_view_audit_logging = is_write_accessed_enabled
    request = factory.get("/admin/auditlog_extra/dummytestmodel/")
    request.user = user
    with set_actor(request.user, remote_addr=REMOTE_ADDR):
        response = model_admin.changelist_view(request)
        assert response.status_code == 200
        if is_write_accessed_enabled:
            assert LogEntry.objects.count() == auditlog_count_on_start + len(
                all_objects
            )
            log = LogEntry.objects.first()
            assert_access_log(log, all_objects[1], user)
        else:
            assert LogEntry.objects.count() == auditlog_count_on_start


@pytest.mark.django_db
def test_change_view(factory, user, model_admin, obj1):
    with mock.patch(
        "django.contrib.admin.options.ModelAdmin.get_object", return_value=obj1
    ):
        request = factory.get(f"/admin/auditlog_extra/dummytestmodel/{obj1.pk}/change/")
        request.user = user
        auditlog_count_on_start = LogEntry.objects.count()
        with set_actor(request.user, remote_addr=REMOTE_ADDR):
            response = model_admin.change_view(request, str(obj1.pk))
            assert response.status_code == 200
            assert LogEntry.objects.count() == auditlog_count_on_start + 1

            log = LogEntry.objects.first()
            assert_access_log(log, obj1, user)


@pytest.mark.django_db
def test_history_view(factory, user, model_admin, obj1):
    with mock.patch(
        "django.contrib.admin.options.ModelAdmin.get_object", return_value=obj1
    ):
        request = factory.get(
            f"/admin/auditlog_extra/dummytestmodel/{obj1.pk}/history/"
        )
        request.user = user
        auditlog_count_on_start = LogEntry.objects.count()
        with set_actor(request.user, remote_addr=REMOTE_ADDR):
            response = model_admin.history_view(request, str(obj1.pk))
            assert response.status_code == 200
            assert LogEntry.objects.count() == auditlog_count_on_start + 1

            log = LogEntry.objects.first()
            assert_access_log(log, obj1, user)


@pytest.mark.django_db
def test_delete_view(factory, user, model_admin, obj1):
    with mock.patch(
        "django.contrib.admin.options.ModelAdmin.get_object", return_value=obj1
    ):
        request = factory.get(f"/admin/auditlog_extra/dummytestmodel/{obj1.pk}/delete/")
        request.user = user
        auditlog_count_on_start = LogEntry.objects.count()
        with set_actor(request.user, remote_addr=REMOTE_ADDR):
            response = model_admin.delete_view(request, str(obj1.pk))
            assert response.status_code == 200
            assert LogEntry.objects.count() == auditlog_count_on_start + 1
            log = LogEntry.objects.first()
            assert_access_log(log, obj1, user)
