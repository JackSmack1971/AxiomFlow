import uuid
from typing import Callable

from .logging import request_id_var


class CorrelationIdMiddleware:
    """Store a correlation ID for each request.

    The middleware extracts an ``X-Request-ID`` header when present or
    generates a new UUID. The ID is stored in :data:`request_id_var` so log
    records can include it, and the same value is echoed back in the response
    headers.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request):  # pragma: no cover - integration behavior
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(request_id)
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response
