from auditlog.signals import accessed


class AuditlogAdminViewAccessLogMixin:
    """
    A mixin for Django Admin views to log access events using `django-auditlog`.

    This mixin automatically logs accesses to the `change_view`, `history_view`,
    and `delete_view` in the Django Admin. It also provides an option to log
    accesses to the `changelist_view` (list view).

    By default, only access to individual object views (change, history, delete)
    is logged. To enable logging for the list view, set the
    `enable_list_view_audit_logging` attribute to `True` in your `ModelAdmin`.
    Please note that this will trigger a very intensive logging and a lots of
    access log data will be created and stored!

    Attributes:
        enable_list_view_audit_logging (bool):
            A flag to enable/disable logging access from the list view.
            Defaults to `False`.

    Example:

        ```python
        from django.contrib import admin
        from .models import MyModel


        @admin.register(MyModel)
        class MyModelAdmin(AuditlogAdminViewAccessLogMixin, admin.ModelAdmin):
            enable_list_view_audit_logging = True  # Enable list view logging
            # ... other admin configurations ...
        ```
    """

    _request_obj_accessed_sent_key = "_auditlog_accessed_sent"

    # To write access log to audit log of each instance in the admin list view
    enable_list_view_audit_logging = False

    def changelist_view(self, request, extra_context=None):
        """
        Handles the changelist view (list view) and logs access events for
        objects on the current page if `enable_list_view_audit_logging` is `True`.

        Args:
            request: The HTTP request object.
            extra_context: Optional extra context to pass to the template.

        Returns:
            The response from the superclass's `changelist_view` method.
        """
        response = super().changelist_view(request, extra_context)
        if self.enable_list_view_audit_logging and request.method == "GET":
            changelist = super().get_changelist_instance(request)
            for obj in changelist.result_list:
                accessed.send(sender=obj.__class__, instance=obj, actor=request.user)
        return response

    def get_object(self, request, object_id, from_field=None):
        """
        Retrieves the object for the admin view and sends the `accessed` signal.

        This method overrides the default `get_object` to include sending the
        `accessed` signal from `django-auditlog`. It uses a flag in the request
        object to ensure the signal is sent only once per request, even if
        `get_object` is called multiple times.

        Args:
            request: The HTTP request object.
            object_id: The ID of the object to retrieve.
            from_field: The field to use to retrieve the object.

        Returns:
            The retrieved object, or None if the object does not exist.
        """
        if not hasattr(request, self._request_obj_accessed_sent_key):
            setattr(request, self._request_obj_accessed_sent_key, False)

        obj = super().get_object(request, object_id, from_field)
        if obj is not None and not getattr(
            request, self._request_obj_accessed_sent_key
        ):
            accessed.send(sender=obj.__class__, instance=obj, actor=request.user)
            # get_object can be called multiple times,
            # so prevent signalling the accessed,
            # if it has already been signalled.
            setattr(request, self._request_obj_accessed_sent_key, True)
        return obj
