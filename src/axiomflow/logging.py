import contextvars
import json
import logging
import uuid

request_id_var = contextvars.ContextVar("request_id", default=None)


class CorrelationIdFilter(logging.Filter):
    """Attach a correlation ID to each log record.

    The ID is retrieved from :data:`request_id_var`, falling back to a new
    UUID when unavailable so that non-request logs remain traceable.
    """

    def filter(
        self, record: logging.LogRecord
    ) -> bool:  # pragma: no cover - logging side effect
        record.correlation_id = request_id_var.get() or str(uuid.uuid4())
        return True


class JsonFormatter(logging.Formatter):
    """Render log records as JSON for container-friendly output."""

    def format(
        self, record: logging.LogRecord
    ) -> str:  # pragma: no cover - logging side effect
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", ""),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)
