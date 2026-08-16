"""Reports — txt/markdown/json generators (PRD §31) + analytics (PRD §32)."""

from .analytics import summarize
from .generator import FORMATS, build_report, generate, recommendations, report_dict
from .json import to_json
from .markdown import to_markdown
from .text import to_text

__all__ = [
    "FORMATS",
    "build_report",
    "generate",
    "recommendations",
    "report_dict",
    "summarize",
    "to_json",
    "to_markdown",
    "to_text",
]
