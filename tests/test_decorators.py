from unittest.mock import MagicMock, patch

import pytest

from auditlog_extra.graphene_decorators import (
    logger as auditlog_decorators_logger,
)
from tests.models import DummyTestModel
from tests.schema import LoggedTestModelType, TestModelType


@pytest.mark.parametrize("is_decorated", [True, False])
@pytest.mark.django_db
def test_auditlog_access_decorator(is_decorated):
    # Mock the info object
    info = MagicMock()
    info.context.user = "testuser"

    model_type = LoggedTestModelType if is_decorated else TestModelType

    # Call the get_node method with the decorated class
    with patch("auditlog.signals.accessed.send") as mock_send:
        test_model = model_type.get_node(info, 999)

    if is_decorated:
        # Assert that accessed.send was called with the correct arguments
        mock_send.assert_called_once_with(
            sender=DummyTestModel, instance=test_model, actor="testuser"
        )
    else:
        mock_send.assert_not_called()


@pytest.mark.django_db
def test_auditlog_access_decorator_exception_handling():
    # Mock the info object
    info = MagicMock()
    info.context.user = "testuser"

    # Patch accessed.send to raise an exception
    with patch("auditlog.signals.accessed.send") as mock_send:
        mock_send.side_effect = Exception("Test exception")

        # Call the get_node method with the decorated class
        with patch.object(auditlog_decorators_logger, "exception") as mock_log:
            LoggedTestModelType.get_node(info, 999)

    # Assert that the exception was logged
    mock_log.assert_called_once()
