import sys
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from axiomflow.logging import request_id_var
from axiomflow.middleware import CorrelationIdMiddleware


class DummyRequest:
    def __init__(self, headers):
        self.headers = headers


def test_middleware_uses_header_when_present():
    token = request_id_var.set(None)
    try:
        request_id = "abc123"
        request = DummyRequest(headers={"X-Request-ID": request_id})

        def get_response(_):
            return {}

        middleware = CorrelationIdMiddleware(get_response)
        response = middleware(request)
        assert response["X-Request-ID"] == request_id
        assert request_id_var.get() == request_id
    finally:
        request_id_var.reset(token)


def test_middleware_generates_and_stores_uuid_when_missing():
    token = request_id_var.set(None)
    try:
        request = DummyRequest(headers={})

        def get_response(_):
            return {}

        middleware = CorrelationIdMiddleware(get_response)
        response = middleware(request)
        header_request_id = response["X-Request-ID"]
        assert uuid.UUID(header_request_id)
        assert request_id_var.get() == header_request_id
    finally:
        request_id_var.reset(token)
