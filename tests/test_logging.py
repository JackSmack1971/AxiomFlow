import json
import logging
import sys
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from axiomflow.logging import CorrelationIdFilter, JsonFormatter, request_id_var


def test_correlation_id_filter_injects_uuid_when_none_set():
    token = request_id_var.set(None)
    try:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname=__file__,
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        CorrelationIdFilter().filter(record)
        uuid.UUID(record.correlation_id)
    finally:
        request_id_var.reset(token)


def test_json_formatter_outputs_valid_json_with_correlation_and_exception():
    token = request_id_var.set(None)
    try:
        formatter = JsonFormatter()
        try:
            1 / 0
        except ZeroDivisionError:
            exc_info = sys.exc_info()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=0,
            msg="boom",
            args=(),
            exc_info=exc_info,
        )
        CorrelationIdFilter().filter(record)
        output = formatter.format(record)
        data = json.loads(output)
        assert data["message"] == "boom"
        assert uuid.UUID(data["correlation_id"])
        assert "ZeroDivisionError" in data.get("exc_info", "")
    finally:
        request_id_var.reset(token)
