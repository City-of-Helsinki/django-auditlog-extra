# Django Auditlog Extra

A module that fixes some issues and provides some reusable tools for Django application using `django-auditlog` in the context of **City of Helsinki**, that uses **Django Auditlog with Django Graphene** or Django Rest Framework.

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Context](#context)
  - [Django Auditlog](#django-auditlog)
  - [Django Graphene](#django-graphene)
  - [Django Rest Framework](#django-rest-framework)
- [FAQ](#faq)
- [Installation](#installation)
- [Features](#features)
  - [Signals](#signals)
    - [`update_log_entry_additional_data_with_is_sent`](#update_log_entry_additional_data_with_is_sent)
  - [Context manager](#context-manager)
    - [`set_request_path`](#set_request_path)
  - [Middleware](#middleware)
    - [`AuditlogMiddleware`](#auditlogmiddleware)
  - [Graphene Decorators](#graphene-decorators)
    - [`auditlog_access`](#auditlog_access)
  - [Mixins](#mixins)
    - [`AuditlogAdminViewAccessLogMixin`](#auditlogadminviewaccesslogmixin)
  - [Utilities](#utilities)
    - [`AuditLogConfigurationHelper`](#auditlogconfigurationhelper)
      - [Initialization examples for `AuditLogConfigurationHelper`:](#initialization-examples-for-auditlogconfigurationhelper)
- [Development](#development)
  - [Development tools installation](#development-tools-installation)
  - [Code linting & formatting](#code-linting--formatting)
  - [Pre-commit hooks](#pre-commit-hooks)
  - [Testing](#testing)
    - [pytest](#pytest)
    - [tox](#tox)
- [Releases](#releases)
  - [Build tool](#build-tool)
  - [Conventional Commits](#conventional-commits)
  - [Releasable units](#releasable-units)
  - [Configuration](#configuration)
  - [Troubleshoting release-please](#troubleshoting-release-please)
    - [Fix merge conflicts by running release-please -action manually](#fix-merge-conflicts-by-running-release-please--action-manually)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Context

### Django Auditlog

> PyPi: https://pypi.org/project/django-auditlog/.
>
> Github: https://github.com/jazzband/django-auditlog.
>
> Docs: https://django-auditlog.readthedocs.io/en/latest/index.html.

The `django-auditlog` is a reusable app for Django that makes logging changes to your models a breeze. It provides a simple and efficient way to track who made changes to your data and when. This is crucial for accountability, debugging, and compliance with regulations like GDPR.

> NOTE: The `django-auditlog` is supported by the **Platta structured log transfer utility** (https://github.com/City-of-Helsinki/structured-log-transfer).

Here's a breakdown of what it offers:

- **Automatic Change Logging**: It automatically logs changes to your Django models, including creation, updates, and deletion. You can easily track who made the changes and what those changes were.

- **Customization**: You can customize which fields to track, the logging level (e.g., only log changes without access log to specific fields), and even use signals to trigger actions based on logged events.

- **Integration with Existing Models**: It seamlessly integrates with your existing Django models. You can easily add audit logging to new or existing models with minimal code changes.

- **Simple Setup**: It's easy to install and configure. You can get started quickly with just a few lines of code.

- **Performance** : Django-auditlog is designed to be fast and efficient, minimizing the performance impact on your application.

Here's why you might use `django-auditlog`:

- **Debugging**: Easily identify the cause of data inconsistencies by reviewing the history of changes.

- **Security and Compliance**: Track user actions to meet regulatory requirements and identify potentially malicious activity.

- **Data Analysis**: Gain insights into how your data is being used and modified over time.

- **Accountability**: Ensure that users are held accountable for their actions within your application.

If you're building a Django application where tracking data changes is important, django-auditlog is a valuable tool to consider.

### Django Graphene

> PyPi: https://pypi.org/project/graphene-django/.
>
> Github: https://github.com/graphql-python/graphene-django.
>
> Docs: https://docs.graphene-python.org/projects/django/en/latest/.

Django Graphene is a library that integrates the Django web framework with Graphene, a Python library for building GraphQL APIs. It allows you to easily create GraphQL APIs in your Django projects, leveraging the power and flexibility of GraphQL while maintaining the simplicity and structure of Django.

### Django Rest Framework

> PyPi: https://pypi.org/project/djangorestframework/.
>
> Github: https://github.com/encode/django-rest-framework.
>
> Docs: https://www.django-rest-framework.org/.

Django REST framework is a powerful and flexible toolkit that makes it easier to build Web REST APIs using the Django framework.

## FAQ

There have been some incompatibility issues with `django-auditlog` and `django-graphene`. Some solutions to them and answers to common questions and issues, see the [FAQ.md](./docs/FAQ.md).

## Installation

**Dependencies:**
For actor handling, django-auditlog and test usage:

- **`django.contrib.auth`**: Django built-in
- **`django.contrib.contenttypes`**: Django built-in
- **`auditlog`**: django-auditlog

**`settings.py`:**

```python
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "auditlog",
    # ...
    "auditlog_extra.apps.AuditLogExtraConfig",
```

**Configuration:**

The base configuration comes from the Django Auditlog. See the installation and usage of `django-auditlog` from https://django-auditlog.readthedocs.io/en/latest/installation.html.

The most important configurations for the audit log itself are:

```python
# Register all models by default
AUDITLOG_INCLUDE_ALL_MODELS = True

# Exclude the IP address from logging.
# When using “AuditlogMiddleware”, the IP address is logged by default
AUDITLOG_DISABLE_REMOTE_ADDR = False

# Disables logging during raw save. (I.e. for instance using loaddata)
# M2M operations will still be logged, since they’re never considered raw.
AUDITLOG_DISABLE_ON_RAW_SAVE = True

# Exclude models in registration process.
# It will be considered when AUDITLOG_INCLUDE_ALL_MODELS is True.
AUDITLOG_EXCLUDE_TRACKING_MODELS = [
    # Some examples:
    "contenttypes.contenttype",
    "sessions.session",
]

# Configure models registration and other behaviours.
AUDITLOG_INCLUDE_TRACKING_MODELS = [
    # Some examples:
    "auth.permission",
    {
      "model": "users.user",
      "exclude_fields": [
          "last_login",
      ],
      "mask_fields": [
          "first_name",
          "last_name",
          "email",
      ],
      "serialize_data": True,
      "serialize_auditlog_fields_only": False,
    },
]
```

Set the middleware in use to log the actor of the audit event:

```python
MIDDLEWARE = [
    # ...other middlewares that manipulates request context...
    "auditlog_extra.middleware.AuditlogMiddleware",
]
```

Optionally, you can also use a configuration utility that helps you configure all the models: [How to initialize the Auditlog Configuration helper](#initialization-examples-for-auditlogconfigurationhelper).

## Features

### Signals

Code reference: [signals.py](./auditlog_extra/signals.py).

#### `update_log_entry_additional_data_with_is_sent`

    Sets the `is_sent` key in the `additional_data` dictionary of a new LogEntry
    instance to False.

    This function is intended to be used as a signal receiver for the `pre_save` signal
    of the `LogEntry` model. It is designed to modify the `additional_data` field
    of newly created LogEntry instances before they are saved to the database.

    This is a requirement of https://github.com/City-of-Helsinki/structured-log-transfer.
    When the structured log transfer tool finishes handling the data,
    it will then mark the LogEntry as sent (by updating
    `additional_data["is_sent"]=True`).

### Context manager

Code reference: [context.py](./auditlog_extra/context.py).

#### `set_request_path`

    Store the request path in the LogEntry's `additional_data` field.

    This context manager uses a ContextVar to store the request path and
    connects a signal receiver to automatically add it to LogEntry instances.
    It uses a unique signal dispatch uid to prevent duplicate signals when nested.

    See the existing django-auditlog implementation to set the actor from: https://github.com/jazzband/django-auditlog/blob/6e51997728c819f9a19778e84d808546013b0242/auditlog/context.py.

NOTE: This is used by the [`AuditlogMiddleware`](#middleware).

### Middleware

Code reference: [middleware.py](./auditlog_extra/middleware.py).

#### `AuditlogMiddleware`

    Extends the `auditlog.middleware.AuditlogMiddleware` to fix an issue
    with setting the actor in the audit log context.

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

To use, add `"auditlog_extra.middleware.AuditlogMiddleware"` to the list of the middlewares in `settings.py`, (instead of the one that `django-auditlog` offers):

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # ...other middlewares that manipulates request context...
    "auditlog_extra.middleware.AuditlogMiddleware",
]
```

### Graphene Decorators

Code reference: [graphene_decorators.py](./auditlog_extra/graphene_decorators.py).

#### `auditlog_access`

    Decorator to add audit logging to a Graphene DjangoObjectType's get_node method.

    Uses the `accessed` signal to log the access of the node.

To use this decorator for a GraphQL Node, add it to the Node-class that is implementing a `DjangoObjectType`. The decorator will then wrap the `get_node` -function, that is inherited from the `DjangoObjectType`.

```python
@auditlog_access
class ChildNode(DjangoObjectType):

    # fields...

    class Meta:
        model = Child
        # meta...

    # methods...
    @classmethod
    @login_required
    def get_node(cls, info, id):
        try:
            return cls._meta.model.objects.user_can_view(info.context.user).get(id=id)
        except cls._meta.model.DoesNotExist:
            return None
```

### Mixins

Code reference: [mixins.py](./auditlog_extra/mixins.py).

#### `AuditlogAdminViewAccessLogMixin`

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

### Utilities

Code reference: [utils.py](./auditlog_extra/utils.py).

#### `AuditLogConfigurationHelper`

    A helper class for managing audit log configuration in your Django project.

    This class provides methods to:

    - Retrieve all models in your project.
    - Identify models that are not explicitly configured for audit logging.
    - Raise an error if any models are not configured when
    `AUDITLOG_INCLUDE_ALL_MODELS` is enabled.

    This helps ensure that all models are either explicitly included or excluded
    from audit logging, preventing accidental omissions.

NOTE: The `AuditLogConfigurationHelper` can be used only after all the apps are ready.

Example usage: Use when the audit log registry is already configured...

```python
AuditLogConfigurationHelper.raise_error_if_unconfigured_models()
```

##### Initialization examples for `AuditLogConfigurationHelper`:

- One place to call this helper function would be in the ready-function of the last app's configuration, when all the models are already registered. You can even add an `apps.py` file into your main Django project folder and then add the project app to the list of the `INSTALLED_APPS` in project's `settings.py`. The important thing is that it should be the last one with models.

  **`apps.py`**:

  ```python
  from django.apps import AppConfig

  class MainProjectConfig(AppConfig):
      name = "mainproject"

      def ready(self):
          from auditlog_extra.utils import AuditLogConfigurationHelper

          AuditLogConfigurationHelper.raise_error_if_unconfigured_models()
  ```

  **`settings.py`**:

  ```python
  INSTALLED_APPS = [
      "django.contrib.auth",
      "django.contrib.contenttypes",
      "django.contrib.sessions",
      "django.contrib.messages",
      "django.contrib.staticfiles",
      "auditlog",
      # local apps
      "events",
      "auditlog_extra.apps.AuditLogExtraConfig",
      "mainproject",
      "django_cleanup.apps.CleanupConfig",  # This must be included last
  ]
  ```

- Another way to achieve this would be using a `post_migrate` signal receiver, which is called after the migration process (`python manage.py migrate`) is done:

  **`signals.py`**:

  ```python
  from django.apps import apps
  from django.db.models.signals import post_migrate
  from django.dispatch import receiver

  from auditlog_extra.utils import AuditLogConfigurationHelper


  @receiver(post_migrate)
  def check_audit_log_configuration(sender, **kwargs):
      """
      Signal receiver to check audit log configuration after all apps are migrated.
      """
      if apps.ready:
          AuditLogConfigurationHelper.raise_error_if_unconfigured_models()
  ```

  Remember that signals (and receivers) needs to be registered to Django after all the models are registered (for example in `apps.py`):

  ```python
  from django.apps import AppConfig

  class MyAppConfig(AppConfig):
      ...

      def ready(self):
            # Implicitly connect signal handlers decorated with @receiver.
            from . import signals

            # OR
            # Explicitly connect a signal handler.
            # from django.core.signals import post_migrate
            # post_migrate.connect(signals.check_audit_log_configuration)
  ```

  Reference: https://docs.djangoproject.com/en/5.1/topics/signals/#listening-to-signals.

## Development

### Development tools installation

To install development tools, run

```bash
pip install .[test]
```

### Code linting & formatting

This project uses [ruff](https://github.com/astral-sh/ruff) for Python code linting and formatting.
Ruff is configured through [pyproject.toml](./pyproject.toml).
Basic `ruff` commands:

- Check linting: `ruff check`
- Check & auto-fix linting: `ruff check --fix`
- Format: `ruff format`

Integrations for `ruff` are available for many editors:

- https://docs.astral.sh/ruff/integrations/

### Pre-commit hooks

You can use [`pre-commit`](https://pre-commit.com/) to lint and format your code before committing:

1. Install `pre-commit` (there are many ways to do that, but let's use pip as an example):
   - `pip install pre-commit`
2. Set up git hooks from `.pre-commit-config.yaml` by running these commands from project root:
   - `pre-commit install` to enable pre-commit code formatting & linting
   - `pre-commit install --hook-type commit-msg` to enable pre-commit commit message linting

After that, linting and formatting hooks will run against all changed files before committing.

Git commit message linting is configured in [.gitlint](./.gitlint)

### Testing

This project uses pytest for unit testing and tox for managing different testing environments.

#### pytest

To run the tests using pytest, execute the following command in your terminal:

```bash
pytest
```

This will run all the tests in the `tests` directory. You can specify individual test files or directories using command-line arguments. For example, to run tests in a specific directory:

```bash
pytest tests/test_utils.py
```

#### tox

Tox is used to manage different testing environments. It allows you to run your tests in various Python versions and with different dependencies. The `tox.ini` file defines the different environments. To run tests using tox, execute:

```bash
tox
```

This will run the tests defined in the `tox.ini` file. Each environment will be created and the tests will be run within that environment. This ensures that your code works correctly across different Python versions and dependency configurations. You can specify individual environments using command-line arguments. For example, to run tests in the `py39` environment (Python v3.9):

```bash
tox -e py39
```

For more information on pytest and tox, refer to their respective documentations:

- pytest: [https://docs.pytest.org/en/7.4.x/](https://docs.pytest.org/en/7.4.x/)
- tox: [https://tox.wiki/en/latest/](https://tox.wiki/en/latest/)

## Releases

The application follows semantic versioning and is released using [Release Please](https://github.com/googleapis/release-please) GitHub Action.

A new release is created by merging a release PR, which is automatically generated by the Release Please action. Once the PR is merged, Release Please automatically creates a new release with release notes and a corresponding tag. The release PR is updated automatically whenever new code is merged into the main branch. Release Please maintains the changelog based on conventional commits.

### Build tool

This project uses [Hatchling](https://hatch.pypa.io/latest/) for building and packaging.

To build the package, run:

```bash
hatch build
```

This will create a distribution package (wheel and sdist) in the `dist` directory. The wheel package is optimized for faster installation.

To build only a wheel:

```bash
hatch build --wheel
```

To build only an sdist:

```bash
hatch build --sdist
```

> For more information on Hatchling build options, refer to the Hatchling documentation: [https://hatch.pypa.io/latest/build/](https://hatch.pypa.io/latest/build/)

To publish to Pypi:

```bash
hatch publish
```

> For more information on Hatchling build options, refer to the Hatchling documentation: [https://hatch.pypa.io/latest/publish/](https://hatch.pypa.io/latest/publish/)

### Conventional Commits

Use [Conventional Commits](https://www.conventionalcommits.org/) to ensure that the changelogs are generated correctly.

### Releasable units

Release please goes through commits and tries to find "releasable units" using commit messages as guidance - it will then add these units to their respective release PR's and figures out the version number from the types: `fix` for patch, `feat` for minor, `feat!` for major. None of the other types will be included in the changelog. So, you can use for example `chore` or `refactor` to do work that does not need to be included in the changelog and won't bump the version.

### Configuration

The release-please workflow is located in the [release-please.yml](./.github/workflows/release-please.yml) file.

The configuration for release-please is located in the [release-please-config.json](./release-please-config.json) file.
See all the options here: [release-please docs](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md).

The manifest file is located in the [release-please-manifest.json](./.release-please-manifest.json) file.

When adding a new app, add it to both the [release-please-config.json](./release-please-config.json) and [release-please-manifest.json](./.release-please-manifest.json) file with the current version of the app. After this, release-please will keep track of versions with [release-please-manifest.json](./.release-please-manifest.json).

### Troubleshoting release-please

If you were expecting a new release PR to be created or old one to be updated, but nothing happened, there's probably one of the older release PR's in pending state or action didn't run.

1. Check if the release action ran for the last merge to main. If it didn't, run the action manually with a label.
2. Check if there's any open release PR. If there is, the work is now included on this one (this is the normal scenario).
3. If you do not see any open release PR related to the work, check if any of the closed PR's are labeled with `autorelease: pending` - ie. someone might have closed a release PR manually. Change the closed PR's label to `autorelease: tagged`. Then go and re-run the last merge workflow to trigger the release action - a new release PR should now appear.
4. Finally check the output of the release action. Sometimes the bot can't parse the commit message and there is a notification about this in the action log. If this happens, it won't include the work in the commit either. You can fix this by changing the commit message to follow the [Conventional Commits](https://www.conventionalcommits.org/) format and rerun the action.

**Important!** If you have closed a release PR manually, you need to change the label of closed release PR to `autorelease: tagged`. Otherwise, the release action will not create a new release PR.

**Important!** Extra label will force release-please to re-generate PR's. This is done when action is run manually with prlabel -option

Sometimes there might be a merge conflict in release PR - this should resolve itself on the next push to main. It is possible run release-please action manually with label, it should recreate the PR's. You can also resolve it manually, by updating the [release-please-manifest.json](./.release-please-manifest.json) file.

#### Fix merge conflicts by running release-please -action manually

1. Open [release-please github action](https://github.com/City-of-Helsinki/django-auditlog-extra/actions/workflows/release-please.yml)
2. Click **Run workflow**
3. Check Branch is **main**
4. Leave label field empty. New label is not needed to fix merge issues
5. Click **Run workflow** -button

There's also a CLI for debugging and manually running releases available for release-please: [release-please-cli](https://github.com/googleapis/release-please/blob/main/docs/cli.md)

## License

See [LICENSE](./LICENSE).
