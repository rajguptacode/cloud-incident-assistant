"""JSON incident report renderer."""

from __future__ import annotations

import json


def to_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
