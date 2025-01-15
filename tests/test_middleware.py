from unittest import mock

import pytest
from auditlog.middleware import AuditlogMiddleware as _AuditlogMiddleware
from django.test import RequestFactory

from auditlog_extra.context import get_actor, get_request_path
from auditlog_extra.middleware import AuditlogMiddleware


@pytest.mark.django_db()
def test_middleware_sets_actor_and_request_pathname():
    # Create a request factory for creating mock requests
    factory = RequestFactory()
    request = factory.get("/test/")
    request.user = mock.Mock(username="testuser")
    request.META["REMOTE_ADDR"] = "127.0.0.1"

    # Create an instance of the middleware
    middleware = AuditlogMiddleware(get_response=lambda req: req)

    # Process the request through the middleware
    middleware(request)

    # Assert that the actor and request pathname are set correctly
    assert get_actor()["remote_addr"] == "127.0.0.1"
    assert get_actor()["signal_duid"][0] == "set_actor"
    assert get_request_path()["request_path"] == "/test/"
    assert get_request_path()["signal_duid"][0] == "set_request_path"


@pytest.mark.django_db()
def test_middleware_calls_get_response():
    # Create a mock request
    request = mock.Mock()
    current_ip = "127.0.0.1"
    request.headers.get.return_value = current_ip

    # Create a mock response
    response = mock.Mock()

    # Create a mock get_response function
    get_response = mock.Mock(return_value=response)

    # Create an instance of the middleware
    middleware = AuditlogMiddleware(get_response=get_response)

    # Process the request through the middleware
    result = middleware(request)

    # Assert that get_response was called with the request
    get_response.assert_called_once_with(request)

    # Assert that the middleware returns the response from get_response
    assert result == response


@pytest.mark.django_db()
def test_middleware_inherits_from_auditlogmiddleware():
    # Assert that the middleware inherits from AuditlogMiddleware
    assert issubclass(AuditlogMiddleware, _AuditlogMiddleware)


@pytest.mark.django_db()
def test_get_remote_addr_with_x_forwarded_for():
    # Create a mock request with X-Forwarded-For header
    forwarded_for = "192.168.1.1, 10.0.0.1"
    request = mock.Mock()
    request.headers.get.return_value = forwarded_for
    request.META = {"HTTP_X_FORWARDED_FOR": forwarded_for}

    # Create an instance of the middleware
    middleware = AuditlogMiddleware(get_response=lambda req: req)

    # Get the remote address
    remote_addr = middleware._get_remote_addr(request)

    # Assert that the remote address is the first IP in X-Forwarded-For
    assert remote_addr == forwarded_for.split(", ")[0]


@pytest.mark.django_db()
def test_get_remote_addr_without_x_forwarded_for():
    # Create a mock request without X-Forwarded-For header
    request = mock.Mock()
    current_ip = "127.0.0.1"
    request.META = {"REMOTE_ADDR": current_ip}
    request.headers.get.return_value = current_ip

    # Create an instance of the middleware
    middleware = AuditlogMiddleware(get_response=lambda req: req)

    # Get the remote address
    remote_addr = middleware._get_remote_addr(request)

    # Assert that the remote address is from REMOTE_ADDR
    assert remote_addr == current_ip
