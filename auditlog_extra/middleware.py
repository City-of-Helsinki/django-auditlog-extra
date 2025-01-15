from auditlog.context import set_actor
from auditlog.middleware import AuditlogMiddleware as _AuditlogMiddleware
from django.utils.functional import SimpleLazyObject

from auditlog_extra.context import set_request_path


class AuditlogMiddleware(_AuditlogMiddleware):
    """
    Middleware to ensure the correct actor is logged in audit logs.

    This middleware extends the `auditlog.middleware.AuditlogMiddleware` to
    address a potential issue where the actor (user and their IP address)
    might not be available when `auditlog` attempts to access it.

    It achieves this by explicitly setting the actor in the
    audit log context before the request is processed. This ensures that
    audit logs accurately reflect the user responsible for each action.

    This fix is based on the suggestion provided in:
    https://github.com/jazzband/django-auditlog/issues/115#issuecomment-1682234986

    Additionally, this middleware sets the request path in the audit log
    context, providing more context for each logged action.
    """

    def __call__(self, request):
        """
        Processes the request and sets the actor and request path in the audit log
        context.

        This middleware sets the actor (user and remote address) and the request path
        in the audit log context before the request is processed.

        Args:
            request: The incoming HTTP request.

        Returns:
            The response from the next middleware or view.
        """
        remote_addr = self._get_remote_addr(request)
        user = SimpleLazyObject(lambda: getattr(request, "user", None))

        actor_context = set_actor(actor=user, remote_addr=remote_addr)

        request_context = set_request_path(request_path=request.path)

        with actor_context:
            with request_context:
                return self.get_response(request)  # type: ignore
