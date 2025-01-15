# FAQ

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Audit Logging Principles](#audit-logging-principles)
- [Django-auditlog incompatibility issues with Django-graphene](#django-auditlog-incompatibility-issues-with-django-graphene)
  - [Graphene's Error Handling and its Impact on Authentication](#graphenes-error-handling-and-its-impact-on-authentication)
  - [Graphene's Unique Authentication Challenges](#graphenes-unique-authentication-challenges)
  - [A custom Django authentication middleware implemenation for GraphQL vs the initial one](#a-custom-django-authentication-middleware-implemenation-for-graphql-vs-the-initial-one)
  - [Automatic logging doesn't log the Actor](#automatic-logging-doesnt-log-the-actor)
- [Users can't remove their own account because of actor field](#users-cant-remove-their-own-account-because-of-actor-field)
- [How does Django use SimpleLazyObject during the authentication?](#how-does-django-use-simplelazyobject-during-the-authentication)
- [Why are login attempts not logged with auditlog?](#why-are-login-attempts-not-logged-with-auditlog)
- [Does django-auditlog track failed actions (e.g., failed saves, deletes)?](#does-django-auditlog-track-failed-actions-eg-failed-saves-deletes)
  - [Should I log failed actions with django-auditlog?](#should-i-log-failed-actions-with-django-auditlog)
  - [How can I log failed actions with django-auditlog?](#how-can-i-log-failed-actions-with-django-auditlog)
  - [How can I create a separate model for logging specific errors?](#how-can-i-create-a-separate-model-for-logging-specific-errors)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Audit Logging Principles

This project prioritizes reliable and efficient audit logging within Django applications. Focus is on capturing essential data changes while ensuring developer convenience and security.

**Core Principles:**

- **Automatic Tracking:** `django-auditlog` automatically records changes to your Django models, providing a comprehensive history of create, update, and delete actions. This ensures that crucial data modifications are never missed, even without explicit developer configuration.

- **Object-Level Logging:** We emphasize object-level logging over request or view-level logging. This approach provides a more granular and trustworthy audit trail, directly linked to the affected data objects. It also facilitates seamless integration with Django's ORM signals for effortless automation.

- **Focused Data Collection:** While prioritizing comprehensive logging, we recognize the sensitivity of audit data. `django-auditlog` allows for customization to avoid unnecessary data collection and protect confidential information.

- **Developer Trust and Convenience:** We aim to provide a solution that developers can rely on. `django-auditlog` strives to be intuitive and easy to use, enabling developers to focus on their core tasks while ensuring their applications maintain robust audit trails.

**Priorities:**

To achieve these principles, we prioritize the following:

1. **Automatic Change Logging:** Seamlessly record modifications (create, update, delete) to model instances.
2. **Easy Access Logging:** Provide a simple and reliable mechanism for logging data access at the object level.
3. **Flexibility:** Allow for customization and extensibility to meet diverse audit logging needs.

By adhering to these principles, we aim to deliver a powerful and reliable audit logging solution that balances comprehensive data capture with developer ease of use and data security.

## Django-auditlog incompatibility issues with Django-graphene

The Django-auditlog does not provide any automatic support for writing access logs to the audit logs. It only provides an automated way to handle object write logs. By access logs, we mean logs that record when a user accesses or interacts with a particular view or resource, as opposed to modifying an object in the database.

While it is a widely used Django app, `django-auditlog` does not support writing access logs for GraphQL views very well. It is quite simple to call the `accessed` signal of the `auditlog` module to write access logs where needed. However, the problem is specifically with the **actor field**, which does not get populated properly. The `set_actor` function, which associates a user with an audit log entry, is called in Django middleware before the user is authenticated by Graphene. It does not get reset with a new value because of the optimization feature of `auditlog`, which prevents the actor from being updated once it's initially set.

For example, if a user accesses a GraphQL view to fetch data, the audit log entry created by `django-auditlog` might show the actor as `system` (which is used for `AnonymousUser` or `None`), even though the user was authenticated by Graphene's middleware. This is because `set_actor` was called in Django's middleware before Graphene had a chance to authenticate the user.

### Graphene's Error Handling and its Impact on Authentication

> Why does the Django Graphene have it's own `GRAPHENE.MIDDLEWARE` configuration?

Django and Graphene have distinct middleware systems that serve different purposes. Django middlewares operate at the broader application level, handling tasks like authentication, session management, and security. Graphene middlewares, on the other hand, are specific to your GraphQL API.

Graphene typically exposes a single endpoint (e.g., `/graphql`) for all GraphQL operations. This means Django's middleware processes the initial request first, regardless of the specific GraphQL query or mutation.

Once the request reaches Graphene's view, Graphene's middleware steps in. This allows you to perform actions specific to your GraphQL API, such as:

- **Authorization:** Check if a user has permission to execute a particular query or mutation.
- **Logging:** Log GraphQL queries for debugging or analytics.
- **Data Transformation:** Modify the request or response data before or after resolving the query.

Diagram of the flow and the execution order in Django and Graphene is like the following:

```diagram
Django middleware -> Routing to a GraphQL view -> Graphene middleware -> Graphene Query handler
```

> The Django middlewares are executed before the Graphene middlewares. They actually wraps the whole Graphene system inside them. The Graphene endpoint is like every GraphQL endpoint generally are -- a single (JSON) endpoint. The request handling first goes through all the Django middlewares and then the request is forwarded to the Graphene views from the Django routers / URL mapping. From there on, the request is in Graphene's (and in its GraphQL view's) scope, so then the request first goes through the Graphene middlewares before it's handled by the GraphQL view and it's query/mutation/subsription handlers.

In essence, Graphene's middleware provides a way to add a layer of processing and customization specifically tailored to your GraphQL API, separate from the broader Django application middleware.

### Graphene's Unique Authentication Challenges

The Graphene can provide public and private query fields. The queries like `introspection query` are generally public. Because the Django middlewares are executed before the GraphQL view is, and because the Django generally handles the authentication with Django middlewares (in city of Helsinki context usually with `django-helusers` auth middlewares), **the authentication errors are raised before the request handling gets to the Graphene**.

Generally, the Graphene handles the GraphQL errors in it's own scope. Instead of responding with HTTP500, if a GraphQL error is raised, the Graphene responds with HTTP200, but adds the errors message in the response's JSON data. So, if an authentication error is raised and it is not handled as GraphQL error, the Graphene view gets rejected before it's execution.

> Question: Should we somehow set (or mark) the GraphQL endpoint public in the Django routing?

### A custom Django authentication middleware implemenation for GraphQL vs the initial one

> Installation instructions of the django-graphql-jwt: https://django-graphql-jwt.domake.io/quickstart.html#installation.

The installation instructions of the Django-GraphQL-JWT uses a combination of Django authentication backends and Graphene middleware. In some of the city of Helsinki Django services, the suggested authentication implementation is replaced with a custom middleware implementation, where all the authentication errors are handled by the Graphene's GraphQL view. That custom implementation is a combination of a custom Django middleware and a custom Graphene middleware.

The advantage of the custom middleware implementation is that then the authentication is handled already in the Django middleware's (and not is not postponed to Django authentication backends). Then also the Django-auditlogging, that sets the actor of the audit log event in a middleware, would get the info about the authenticated user in right time.

A con of the custom middleware implementation was a critical one: **The public query fields were rejected, because the Django middleware set the `auth_error` field to the `request` object**. When the suggested configuration for the Django-Graphene is used, the `django-auditlog` sets the actor too soon, because the Graphene middlewares and therefore also the GraphQL JWT authentication are executed after the Django middlewares.

An example of JWT authentication implemented with Django middleware (references: https://github.com/City-of-Helsinki/open-city-profile/blob/4f46f9f9f195c4254f79f5dfbd97d03b7fa87a5b/open_city_profile/middleware.py and https://github.com/City-of-Helsinki/kukkuu/blob/623d553b1701bb35968c687ecd287d2d257d122c/kukkuu/middleware.py):

```python
from helusers.oidc import RequestJWTAuthentication

from services.utils import set_service_to_request


class JWTAuthentication:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            try:
                authenticator = RequestJWTAuthentication()
                user_auth = authenticator.authenticate(request)
                if user_auth is not None:
                    request.user_auth = user_auth
                    request.user = user_auth.user
                    set_service_to_request(request)
            except Exception as e:
                request.auth_error = e

        return self.get_response(request)
```

The authentication error is not raised directly, but got written in the request object, so it can be handled later (by the Graphene middleware).

An example of JWT authentication full filled with Graphene middleware (references: https://github.com/City-of-Helsinki/open-city-profile/blob/4f46f9f9f195c4254f79f5dfbd97d03b7fa87a5b/open_city_profile/graphene.py#L18 and
https://github.com/City-of-Helsinki/kukkuu/blob/623d553b1701bb35968c687ecd287d2d257d122c/kukkuu/graphene.py):

```python
class JWTMiddleware:
    def resolve(self, next, root, info, **kwargs):
        request = info.context

        auth_error = getattr(request, "auth_error", None)
        if isinstance(auth_error, Exception):
            raise auth_error

        return next(root, info, **kwargs)
```

Since the JWTMiddleware is a Graphene middleware (not Django middleware), the `auth_error` is raised as a GraphQL error (HTTP200 with an `error` field populated in the response).

### Automatic logging doesn't log the Actor

"Automatic Logging doesn't log the Actor": This is an issue tracked in: https://github.com/jazzband/django-auditlog/issues/115.

An originally provided fix for the issue:

```python
from auditlog.context import set_actor
from auditlog.middleware import AuditlogMiddleware as _AuditlogMiddleware
from django.utils.functional import SimpleLazyObject


class AuditlogMiddleware(_AuditlogMiddleware):
    def __call__(self, request):
        remote_addr = self._get_remote_addr(request)

        user = SimpleLazyObject(lambda: getattr(request, "user", None))

        context = set_actor(actor=user, remote_addr=remote_addr)

        with context:
            return self.get_response(request)
```

This is the fix that is applied in [AuditlogMiddleware](../middleware.py).

Eventhough the `auditlog.middleware.AuditlogMiddleware` is applied after the `django.contrib.auth.middleware.AuthenticationMiddleware`, the `__call__` funtion of the `auditlog.middleware.AuditlogMiddleware` will be handled before the `process_request` -function of the `auditlog.middleware.AuditlogMiddleware`. That is the reason why the `actor` is set as `AnonymousUser` and the audit log entries are showing that `system` was the actor of the audit log event.

In this provided fix, the user is set as a `SimpleLazyObject`, which means that the actor won't be set immediately, but will be resolved later, when the authentication is (hopefully) already done.

## Users can't remove their own account because of actor field

"Users can't remove their own account because of actor field": This is an issue tracked in https://github.com/jazzband/django-auditlog/issues/245.

```python
# make a log entry for the deletion
LogEntry.objects.log_create(user, force_log=True, action=LogEntry.Action.DELETE).save()
with disable_auditlog():
    user.delete()
```

## How does Django use SimpleLazyObject during the authentication?

Django uses `SimpleLazyObject` during authentication to optimize database access and improve performance. Here's how it works:

1. Delayed User Loading:

- When a request comes in, Django's authentication middleware adds a user attribute to the request object. This attribute is an instance of `SimpleLazyObject`.

- `SimpleLazyObject` acts as a proxy for the actual user object. It doesn't actually retrieve the user from the database until it's needed.

2. On-Demand User Retrieval:

- The first time you access an attribute of `request.user` (e.g., `request.user.username`), the `SimpleLazyObject` "wakes up" and calls a function (`get_user`) to fetch the actual user object.

- `get_user` retrieves the user ID from the session, loads the appropriate authentication backend, and uses it to get the user from the database.

- The retrieved user object is then cached in the `SimpleLazyObject`, so subsequent accesses don't hit the database again.

3. Anonymous User Handling:

- If the user isn't authenticated (no user ID in the session), get_user returns an instance of AnonymousUser.
- This allows Django to handle both authenticated and unauthenticated users seamlessly, without requiring conditional checks throughout the code.

Benefits of using `SimpleLazyObject`:

- **Performance**: Avoids unnecessary database queries if the user object isn't actually used in the request.
- **Flexibility**: Allows the `request.user` object to represent both authenticated and anonymous users dynamically.
- **Clean Code**: Simplifies code by hiding the complexities of user loading and caching.

Example:

```python
def my_view(request):
  if request.user.is_authenticated:  # No database query yet
    username = request.user.username  # User is fetched from the database here
    # ... do something with the username ...
```

In this example, the database query to fetch the user happens only when `request.user.username` is accessed. If the user isn't authenticated, the database is never queried.

## Why are login attempts not logged with auditlog?

The city of Helsinki's audit logs do not typically record individual login attempts. This is because most of our services rely on external authorization instead of local logins.

Here's why:

- **External Authorization**: Users log in using services like Helsinki Profile or with Entra IDs through a Keycloak service.

- **Continuous Authorization**: Because of this, permissions are checked with every request made to our APIs, not just during the initial login.

- **Reducing Log Volume**: Logging every API request would create an overwhelming amount of data, making it difficult to find relevant information.

## Does django-auditlog track failed actions (e.g., failed saves, deletes)?

No, django-auditlog primarily focuses on logging successful changes to your models. It doesn't automatically record failed actions like validation errors or database exceptions.

### Should I log failed actions with django-auditlog?

Logging every failed action can lead to very verbose logs, consume significant storage, and potentially impact performance. However, there are cases where it's beneficial:

- **Security Auditing:** Track failed login attempts to detect malicious activity.
- **Debugging:** Log critical errors (e.g., database issues) to help diagnose problems.
- **Business Logic:** Monitor failed actions related to core processes (e.g., payments, orders).
- **Compliance:** Adhere to industry regulations that require logging specific failed actions.

By default, the `django-auditlog` does not log the failed actions. It would be better to do that with some other logger. Solution could be on web server's access log level and also some tools like `django-axe` could be used to prevent brute-forcing and attacking.

### How can I log failed actions with django-auditlog?

While you _could_ use `auditlog.LogEntry` for this, it's generally better to create a separate model (e.g., `ErrorLogEntry`) or use a different logging mechanism altogether. This provides clearer separation, more flexibility, and better performance.

### How can I create a separate model for logging specific errors?

Define a new model to store the relevant information about the errors you want to track:

```python
from django.db import models

class ErrorLogEntry(models.Model):
    is_sent = models.BooleanField(default=False, verbose_name=_("is sent"))
    message = models.JSONField(verbose_name=_("message"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("created at"))
    # Add other relevant fields like user, affected object, etc.
```

Then, in your signal handlers, middleware, or decorators, catch the specific errors and create instances of this model to log them.

**Example** (using signals and a separate model):

```python
from django.db.models.signals import pre_save
from django.dispatch import receiver
from myapp.models import MyModel, ErrorLogEntry

@receiver(pre_save, sender=MyModel)
def log_validation_error(sender, instance, **kwargs):
    try:
        instance.full_clean()
    except ValidationError as e:
        ErrorLogEntry.objects.create(
            message={
                "status": "ValidationError"
                # ... other relevant fields
            },
        )
```
