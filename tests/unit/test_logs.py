from __future__ import annotations

import json
from datetime import UTC, datetime

from cloudops_sentinel.logs import patterns
from cloudops_sentinel.logs.normalizer import normalize
from cloudops_sentinel.logs.parser import parse_line
from cloudops_sentinel.models.log import LogLevel


def test_parse_json_line():
    raw = json.dumps({"timestamp": "2026-08-16T14:32:11Z", "level": "ERROR", "service": "nginx", "message": "upstream timeout"})
    data = parse_line(raw)
    assert data["severity"] == "ERROR"
    assert data["service"] == "nginx"
    assert isinstance(data["timestamp"], datetime)


def test_parse_plain_text():
    data = parse_line("2026-08-16 14:32:11 ERROR nginx upstream timeout")
    assert data["severity"] == "ERROR"
    assert data["message"].endswith("upstream timeout")
    assert data["timestamp"] is not None


def test_parse_empty():
    assert parse_line("") is None
    assert parse_line("   ") is None


def test_normalize_maps_levels():
    entry = normalize({"timestamp": datetime(2026, 8, 16, 14, 32, 11, tzinfo=UTC), "severity": "WARN", "message": "retry"}, source="test")
    assert entry.severity == LogLevel.WARNING
    assert entry.event_id
    assert entry.source == "test"


def test_normalize_default_info():
    entry = normalize({"message": "hello"})
    assert entry.severity == LogLevel.INFO
    assert entry.timestamp.tzinfo is not None


def test_patterns():
    assert "timeout" in patterns.detect_patterns("upstream timed out")
    assert "connection_refused" in patterns.detect_patterns("connection refused by peer")
    assert patterns.detect_patterns("all good here") == []


def test_restart_loop():
    msgs = ["service started", "service failed", "service started", "service crashed", "service started", "service exited"]
    assert patterns.is_restart_loop(msgs) is True
    assert patterns.is_restart_loop(["started", "started", "running"]) is False


def test_count_levels():
    from cloudops_sentinel.models.log import LogEntry

    entries = [
        LogEntry(timestamp=datetime(2026, 1, 1, tzinfo=UTC), severity=LogLevel.ERROR, message="e1"),
        LogEntry(timestamp=datetime(2026, 1, 1, tzinfo=UTC), severity=LogLevel.ERROR, message="e2"),
        LogEntry(timestamp=datetime(2026, 1, 1, tzinfo=UTC), severity=LogLevel.INFO, message="i1"),
    ]
    assert patterns.count_levels(entries) == {"ERROR": 2, "INFO": 1}