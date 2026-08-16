import pytest

from cloudops_sentinel.ui import theme
from cloudops_sentinel.ui.bars import percent_bar, sparkline
from cloudops_sentinel.ui.console import make_console, severity_style
from cloudops_sentinel.ui.icons import icon


@pytest.mark.parametrize("token", ["PRIMARY", "SECONDARY", "SUCCESS", "WARNING", "DANGER", "CRITICAL", "MUTED", "INFO", "ACCENT"])
def test_theme_tokens_defined(token):
    assert isinstance(getattr(theme, token), str)
    assert getattr(theme, token)


def test_severity_styles():
    assert severity_style("CRITICAL") != severity_style("INFO")
    assert severity_style("high") == theme.DANGER


def test_icon_unicode(monkeypatch):
    monkeypatch.setenv("SENTINEL_ASCII", "0")
    monkeypatch.setattr("cloudops_sentinel.ui.icons.sys.stdout.isatty", lambda: True)
    assert icon("ok") == "✓"
    assert icon("critical") == "◆"


def test_icon_ascii(monkeypatch):
    monkeypatch.setenv("SENTINEL_ASCII", "1")
    assert icon("ok") == "[PASS]"
    assert icon("critical") == "[CRIT]"


def test_no_color_console():
    assert make_console(no_color=True).color_system is None


def test_percent_bar_clamps():
    text = percent_bar(150)
    assert str(text)
    text = percent_bar(0)
    assert str(text)


def test_sparkline_empty():
    assert str(sparkline([])) == ""