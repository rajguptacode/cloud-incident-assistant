from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

_TIMESTAMP_RE = re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?)")
_LEVEL_RE = re.compile(r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b")


def parse_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith(("{", "[")):
        try:
            data = json.loads(line)
            if isinstance(data, dict):
                data.setdefault("severity", data.get("level") or data.get("lvl") or "INFO")
                data.setdefault("message", data.get("msg") or data.get("log") or "")
                ts = data.get("timestamp") or data.get("time") or data.get("@timestamp")
                if isinstance(ts, str):
                    match = _TIMESTAMP_RE.search(ts)
                    if match:
                        try:
                            data["timestamp"] = datetime.fromisoformat(match.group(1))
                        except ValueError:
                            pass
                return data
        except json.JSONDecodeError:
            pass
    timestamp = None
    match = _TIMESTAMP_RE.search(line)
    if match:
        try:
            timestamp = datetime.fromisoformat(match.group(1))
        except ValueError:
            timestamp = None
    level = _LEVEL_RE.search(line)
    return {
        "timestamp": timestamp,
        "severity": level.group(1) if level else "INFO",
        "message": line,
    }