"""Full-screen monitor TUI (Antigravity-style): alt-screen, minimal borders,
keyboard-driven tabs, bottom status bar, background sampler (never blocks UI).

Tabs: 1 Overview · 2 CPU · 3 Memory · 4 Disk · 5 Network · 6 Processes
      7 Incidents · 8 Logs · 9 Analytics
Keys: 1-9/arrows switch tabs, +/- interval, h help, q quit.
Non-tty (CI/pipe): falls back to a plain non-alt-screen loop, no keys.
"""

from __future__ import annotations

import select
import sys
import termios
import threading
import time
import tty
from collections import deque
from datetime import UTC, datetime
from typing import Any

import psutil
from pyfiglet import figlet_format
from rich.console import Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from cloudops_sentinel.collectors import cpu as cpu_collector
from cloudops_sentinel.collectors import disk as disk_collector
from cloudops_sentinel.collectors import host as host_collector
from cloudops_sentinel.collectors import memory as mem_collector
from cloudops_sentinel.collectors import network as net_collector
from cloudops_sentinel.collectors import processes as proc_collector
from cloudops_sentinel.collectors import services as svc_collector
from cloudops_sentinel.core.config import load_config
from cloudops_sentinel.models.incident import Incident
from cloudops_sentinel.models.log import LogEntry

from . import bars, theme
from .console import make_console

TABS = ["Overview", "CPU", "Memory", "Disk", "Network", "Processes", "Incidents", "Logs", "Analytics"]
ARROWS = {"\x1b[A": -1, "\x1b[B": 1, "\x1b[C": 1, "\x1b[D": -1}
SPINNER = ["◐", "◓", "◑", "◒"]
DEFAULT_SERVICES = ["ssh", "docker", "nginx", "postgres"]
WORDMARK = [line.rstrip() for line in figlet_format("CLOUD INCIDENT", font="standard").splitlines()]


def _metric_map(metrics) -> dict[str, float]:
    return {m.name: m.value for m in metrics}


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TiB"


def _gradient(text: str, start: str, end: str) -> Text:
    def rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]

    s, e = rgb(start), rgb(end)
    out = Text()
    n = max(1, len(text) - 1)
    for i, ch in enumerate(text):
        r = tuple(s[j] + (e[j] - s[j]) * i / n for j in range(3))
        out.append(ch, style=f"#{int(r[0]):02x}{int(r[1]):02x}{int(r[2]):02x}")
    out.stylize("bold")
    return out


def _fmt_speed(n: float) -> str:
    return _fmt_bytes(n) + "/s"


def _speed_line(label: str, hist: deque, width: int) -> RenderableType:
    cur = hist[-1] if hist else 0.0
    return Group(
        Text(f"{label:<9}") + Text(f"{_fmt_speed(cur):>11}", style=theme.MUTED)
        + Text("  ") + bars.sparkline(list(hist)[-30:], width=width - 34),
    )


def _uptime(seconds: float) -> str:
    days, rem = divmod(int(seconds), 86400)
    return f"{days}d {rem // 3600:02d}h {rem % 3600 // 60:02d}m"


def _bar_row(label: str, value: float, warn: float, crit: float, width: int) -> RenderableType:
    return Group(
        Text(f"{label:<10}") + Text(f"{value:>5.0f}% ", style=theme.MUTED)
        + bars.percent_bar(value, width=width, warn=warn, crit=crit),
    )


def _severity_style(sev: str) -> str:
    style = theme.SEVERITY_STYLES.get(sev.upper())
    return style.color.name if style and style.color else theme.MUTED


# ── Background sampler: collects everything without blocking the UI ──────────


class _Sampler(threading.Thread):
    """Refreshes system + storage state every interval in the background."""

    def __init__(self, state: dict, interval_holder: list[float], stop: threading.Event) -> None:
        super().__init__(daemon=True)
        self.state = state
        self.interval_holder = interval_holder
        self.stop = stop
        self.cfg = load_config()
        self.db = None
        self._prev_rx = self._prev_tx = self._prev_t = None

    def _load_db(self):
        if self.db is None:
            from cloudops_sentinel.storage.database import Database

            self.db = Database()
            self.db.create_tables()
        return self.db

    def _system(self, cycle: int) -> None:
        t = self.cfg.thresholds
        st = self.state
        st["host"] = host_collector.collect()
        st["cpu"] = _metric_map(cpu_collector.collect(interval=0.1))
        st["mem"] = _metric_map(mem_collector.collect())
        stats = psutil.net_io_counters()
        st["net"].update(
            {
                "network.rx_bytes": float(stats.bytes_recv),
                "network.tx_bytes": float(stats.bytes_sent),
                "network.rx_errors": float(stats.errin),
                "network.tx_errors": float(stats.errout),
            }
        )
        if cycle % 5 == 0:  # latency/DNS probes are slow; refresh every 5th cycle
            st["net"].update(_metric_map(net_collector.collect()))
        st["disk"] = disk_collector.collect()
        st["procs"] = proc_collector.top(limit=10, by="cpu")
        st["services"] = svc_collector.collect(DEFAULT_SERVICES)
        st["thresholds"] = t
        now = time.monotonic()
        rx, tx = st["net"].get("network.rx_bytes", 0.0), st["net"].get("network.tx_bytes", 0.0)
        if self._prev_rx is not None:
            dt = max(now - self._prev_t, 0.1)
            st["net_hist"]["rx"].append((rx - self._prev_rx) / dt)
            st["net_hist"]["tx"].append((tx - self._prev_tx) / dt)
        self._prev_rx, self._prev_tx, self._prev_t = rx, tx, now
        for key, value in (
            ("cpu", st["cpu"].get("cpu.percent", 0.0)),
            ("mem", st["mem"].get("memory.percent", 0.0)),
        ):
            st["history"][key].append(value)

    def _storage(self) -> None:
        st = self.state
        try:
            db = self._load_db()
            with db.session() as s:
                from cloudops_sentinel.storage.repositories.incidents import IncidentsRepository
                from cloudops_sentinel.storage.repositories.logs import LogsRepository

                incidents = IncidentsRepository(s).list()
                st["incidents"] = incidents
                st["logs"] = LogsRepository(s).query()[-12:]
            from cloudops_sentinel.reports.analytics import summarize

            st["analytics"] = summarize(st["incidents"] or [], uptime=_uptime(st["host"].uptime_seconds))
        except Exception as e:  # noqa: BLE001 — storage is best-effort in the TUI
            st["storage_error"] = str(e)

    def run(self) -> None:
        cycle = 0
        while not self.stop.is_set():
            try:
                self._system(cycle)
                cycle += 1
                if cycle % 5 == 0:
                    self._storage()
            except Exception as e:  # noqa: BLE001 — collector failures must not kill the TUI
                self.state["error"] = str(e)
            self.stop.wait(self.interval_holder[0])


# ── Tabs ──────────────────────────────────────────────────────────────────────


def _overview(st: dict, width: int) -> RenderableType:
    t = st.get("thresholds")
    net = st.get("net", {})
    services = st.get("services") or []
    running = [s for s in services if s.status.value == "RUNNING"]
    latency = net.get("network.latency_ms", -1)
    bar = st["bar"]
    rows = [
        _bar_row("CPU", bar["cpu"], t.cpu_warning, t.cpu_critical, width - 28),
        _bar_row("Memory", bar["mem"], t.memory_warning, t.memory_critical, width - 28),
        _bar_row("Disk", bar["disk"], t.disk_warning, t.disk_critical, width - 28),
        Group(
            Text("Network   ") + Text(f"{latency:.0f}ms" if latency >= 0 else "n/a", style=theme.MUTED)
            + Text(f"  rx {_fmt_bytes(net.get('network.rx_bytes', 0))}", style=theme.MUTED)
            + Text(f"  tx {_fmt_bytes(net.get('network.tx_bytes', 0))}", style=theme.MUTED),
        ),
        Group(
            Text("Services  ")
            + Text(f"{len(running)}/{len(services)} running", style=theme.SUCCESS if running else theme.DANGER),
        ),
        Text(""),
        Group(
            Text("CPU HIST ") + bars.sparkline(list(st["history"]["cpu"])[-30:], width=width - 28),
            Text("MEM HIST ") + bars.sparkline(list(st["history"]["mem"])[-30:], width=width - 28),
            _speed_line("NET RX", st["net_hist"]["rx"], width),
        ),
    ]
    return Panel(Group(*rows), title=Text("OVERVIEW", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))


def _cpu_tab(st: dict, width: int) -> RenderableType:
    t = st.get("thresholds")
    cpu = st.get("cpu", {})
    load = cpu.get("load.1m", 0.0), cpu.get("load.5m", 0.0), cpu.get("load.15m", 0.0)
    cores = sorted((name, value) for name, value in cpu.items() if name.startswith("cpu.core."))
    half = (len(cores) + 1) // 2
    core_rows = []
    for i in range(half):
        left = cores[i] if i < len(cores) else None
        right = cores[i + half] if i + half < len(cores) else None
        if left and right:
            core_rows.append(
                Group(
                    _bar_row(left[0].split(".")[-1], left[1], t.cpu_warning, t.cpu_critical, (width - 40) // 2),
                    Text("  "),
                    _bar_row(right[0].split(".")[-1], right[1], t.cpu_warning, t.cpu_critical, (width - 40) // 2),
                )
            )
        elif left:
            core_rows.append(_bar_row(left[0].split(".")[-1], left[1], t.cpu_warning, t.cpu_critical, (width - 40) // 2))
    rows = [
        _bar_row("Usage", st["bar"]["cpu"], t.cpu_warning, t.cpu_critical, width - 28),
        Group(
            Text("User      ") + Text(f"{cpu.get('cpu.user', 0.0):.1f}%", style=theme.MUTED),
            Text(f"  System {cpu.get('cpu.system', 0.0):.1f}%", style=theme.MUTED),
            Text(f"  Idle {cpu.get('cpu.idle', 0.0):.1f}%", style=theme.MUTED),
        ),
        Group(Text("Load      ") + Text(f"{load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f} (1m/5m/15m)", style=theme.MUTED)),
        Text(""),
        Text("PER-CORE", style=theme.SECONDARY),
        *core_rows,
    ]
    return Panel(Group(*rows), title=Text("CPU", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))


def _mem_tab(st: dict, width: int) -> RenderableType:
    t = st.get("thresholds")
    mem = st.get("mem", {})
    rows = [
        _bar_row("Memory", st["bar"]["mem"], t.memory_warning, t.memory_critical, width - 28),
        Group(
            Text("Total     ") + Text(_fmt_bytes(mem.get("memory.total", 0)), style=theme.MUTED),
            Text(f"  Used {_fmt_bytes(mem.get('memory.used', 0))}", style=theme.MUTED),
            Text(f"  Free {_fmt_bytes(mem.get('memory.available', 0))}", style=theme.MUTED),
        ),
        Text(""),
        _bar_row("Swap", st["bar"]["swap"], t.memory_warning, t.memory_critical, width - 28),
        Group(Text("Swap used ") + Text(_fmt_bytes(mem.get("swap.used", 0)), style=theme.MUTED)),
        Text(""),
        Text("HISTORY (30s)", style=theme.SECONDARY),
        Group(
            Text("CPU ") + bars.sparkline(list(st["history"]["cpu"])[-30:], width=width - 28),
            Text("Mem ") + bars.sparkline(list(st["history"]["mem"])[-30:], width=width - 28),
        ),
    ]
    return Panel(Group(*rows), title=Text("MEMORY", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))


def _disk_tab(st: dict, width: int) -> RenderableType:
    t = st.get("thresholds")
    mounts = [d for d in (st.get("disk") or []) if d.mountpoint != "/boot/efi"]
    rows = [
        Group(
            _bar_row(m.mountpoint, m.percent, t.disk_warning, t.disk_critical, width - 34),
            Text(f"  {_fmt_bytes(m.free)} free", style=theme.MUTED),
        )
        for m in mounts
    ]
    return Panel(Group(*rows), title=Text("DISK", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))


def _net_tab(st: dict, width: int) -> RenderableType:
    net = st.get("net", {})
    latency = net.get("network.latency_ms", -1)
    rows = [
        Group(
            Text("RX        ") + Text(_fmt_bytes(net.get("network.rx_bytes", 0)), style=theme.MUTED),
            Text(f"  TX {_fmt_bytes(net.get('network.tx_bytes', 0))}", style=theme.MUTED),
        ),
        Group(
            Text("Errors    ") + Text(f"rx {net.get('network.rx_errors', 0):.0f}", style=theme.MUTED),
            Text(f"  tx {net.get('network.tx_errors', 0):.0f}", style=theme.MUTED),
        ),
        Group(
            Text("Latency   ")
            + Text(f"{latency:.0f}ms" if latency >= 0 else "unreachable", style=theme.SUCCESS if latency >= 0 else theme.DANGER),
            Text(f"  DNS {'ok' if net.get('network.dns_ok', 0) else 'fail'}", style=theme.SUCCESS if net.get('network.dns_ok') else theme.DANGER),
            Text(f"  Internet {'ok' if net.get('network.internet_ok', 0) else 'fail'}", style=theme.SUCCESS if net.get('network.internet_ok') else theme.DANGER),
        ),
        Text(""),
        Text("SPEED (30s)", style=theme.SECONDARY),
        _speed_line("RX rate", st["net_hist"]["rx"], width),
        _speed_line("TX rate", st["net_hist"]["tx"], width),
    ]
    return Panel(Group(*rows), title=Text("NETWORK", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))


def _proc_tab(st: dict, width: int) -> RenderableType:
    table = Table(show_header=True, header_style=theme.SECONDARY, box=None, padding=(0, 1))
    table.add_column("PID", justify="right")
    table.add_column("NAME")
    table.add_column("CPU%", justify="right")
    table.add_column("MEM%", justify="right")
    for p in st.get("procs") or []:
        table.add_row(str(p.pid), p.name[:24], f"{p.cpu_percent:.1f}", f"{p.memory_percent:.1f}")
    return Panel(table, title=Text("PROCESSES", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))


def _incidents_tab(st: dict, width: int) -> RenderableType:
    incidents: list[Incident] = st.get("incidents")
    if incidents is None:
        body = Text("No incident data (storage empty or unavailable).", style=theme.MUTED)
        return Panel(body, title=Text("INCIDENTS", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))
    table = Table(show_header=True, header_style=theme.SECONDARY, box=None, padding=(0, 1))
    table.add_column("ID")
    table.add_column("SEV")
    table.add_column("STATUS")
    table.add_column("STARTED", justify="right")
    table.add_column("TITLE")
    for inc in reversed(incidents[-8:]):
        table.add_row(
            inc.id,
            Text(inc.severity.value, style=_severity_style(inc.severity.value)),
            Text(inc.status.value, style=theme.SUCCESS if inc.status.value in ("RESOLVED", "CLOSED") else theme.WARNING),
            inc.started.strftime("%m-%d %H:%M"),
            (inc.title or "")[:22],
        )
    return Panel(table, title=Text("INCIDENTS", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))


def _logs_tab(st: dict, width: int) -> RenderableType:
    logs: list[LogEntry] = st.get("logs")
    if not logs:
        body = Text("No stored logs yet — run `sentinel demo` or `sentinel logs` first.", style=theme.MUTED)
        return Panel(body, title=Text("LOGS", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))
    rows = [
        Group(
            Text(log.timestamp.strftime("%H:%M:%S"), style=theme.MUTED),
            Text(f" {log.severity.value:<8}", style=_severity_style(log.severity.value)),
            Text(f"{log.service[:12]:<12}", style=theme.SECONDARY),
            Text(log.message[: max(10, width - 46)], style=theme.TEXT),
        )
        for log in logs[-10:]
    ]
    return Panel(Group(*rows), title=Text("LOGS", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))


def _analytics_tab(st: dict, width: int) -> RenderableType:
    a = st.get("analytics")
    if not a:
        body = Text("No analytics yet — run `sentinel demo` first.", style=theme.MUTED)
        return Panel(body, title=Text("ANALYTICS", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))
    dist = a["severity_distribution"]
    total = max(a["total"], 1)
    rows = [
        Group(
            *[
                Text(f"{sev:<8}") + Text(f"{dist[sev]:>3} ", style=theme.MUTED)
                + bars.percent_bar(dist[sev] / total * 100, width=width - 34)
                for sev in ("critical", "high", "medium", "low", "info")
            ]
        )
    ]
    lines = [
        Text(""),
        Group(
            Text(f"Total incidents  {a['total']}", style=theme.PRIMARY),
            Text(f"  Resolved {a['resolved_count']}", style=theme.MUTED),
            Text(f"  Avg resolution {a['avg_resolution']}", style=theme.MUTED),
        ),
        Group(
            Text(f"Most common      {a['most_common'] or 'n/a'}", style=theme.MUTED),
            Text(f"  Uptime {a['uptime']}", style=theme.MUTED),
        ),
    ]
    return Panel(Group(*rows, *lines), title=Text("ANALYTICS", style=theme.SECONDARY), border_style=theme.BORDER, padding=(0, 1))


_TABS = [_overview, _cpu_tab, _mem_tab, _disk_tab, _net_tab, _proc_tab, _incidents_tab, _logs_tab, _analytics_tab]


class _KeyReader(threading.Thread):
    """Background single-char reader; puts decoded keys on a queue."""

    def __init__(self, keys: deque) -> None:
        super().__init__(daemon=True)
        self.keys = keys
        self.fd = sys.stdin.fileno()
        self._old = None

    def run(self) -> None:
        self._old = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        try:
            while True:
                if not select.select([sys.stdin], [], [], 0.3)[0]:
                    continue
                ch = sys.stdin.read(1)
                if not ch:
                    continue
                if ch == "\x1b":
                    seq = ch + sys.stdin.read(1) + sys.stdin.read(1)
                    self.keys.append(ARROWS.get(seq, "?"))
                else:
                    self.keys.append(ch)
        finally:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self._old)


def run(interval: float = 2.0, no_color: bool = False) -> None:
    console = make_console(no_color)
    interactive = sys.stdin.isatty() and sys.stdout.isatty()
    tab = 0
    frame = 0
    help_line = False
    keys: deque = deque(maxlen=8)
    reader = _KeyReader(keys) if interactive else None
    if reader:
        reader.start()

    state: dict[str, Any] = {
        "host": host_collector.collect(),
        "cpu": {}, "mem": {}, "net": {}, "disk": [], "procs": [], "services": [],
        "history": {"cpu": deque(maxlen=40), "mem": deque(maxlen=40)},
        "net_hist": {"rx": deque(maxlen=60), "tx": deque(maxlen=60)},
        "bar": {"cpu": 0.0, "mem": 0.0, "disk": 0.0, "swap": 0.0},
        "incidents": None, "logs": None, "analytics": None, "error": None, "storage_error": None,
        "thresholds": load_config().thresholds,
    }
    interval_holder = [interval]
    stop = threading.Event()
    _Sampler(state, interval_holder, stop).start()

    def render() -> RenderableType:
        nonlocal frame
        frame += 1
        width = console.size.width - 2
        host = state["host"]
        error = state.get("error") or state.get("storage_error")
        targets = {
            "cpu": state["cpu"].get("cpu.percent", 0.0),
            "mem": state["mem"].get("memory.percent", 0.0),
            "disk": max((d.percent for d in state["disk"]), default=0.0),
            "swap": state["mem"].get("swap.percent", 0.0),
        }
        for key, target in targets.items():
            state["bar"][key] += (target - state["bar"][key]) * 0.2
        art_width = max(len(line) for line in WORDMARK)
        if width >= art_width:
            wordmark = Group(*[_gradient(line, theme.PRIMARY, theme.SECONDARY) for line in WORDMARK])
        else:  # narrow terminal: spaced fallback
            wordmark = _gradient("C L O U D   I N C I D E N T", theme.PRIMARY, theme.SECONDARY)
        header = Group(
            wordmark,
            _gradient("━" * max(0, width), theme.PRIMARY, theme.SECONDARY),
            Text(f"{host.hostname} · {host.os} · up {_uptime(host.uptime_seconds)}", style=theme.MUTED),
        )
        tabs_row = Group(
            *[
                Text(f" {'●' if i == tab else '○'} {name} ", style=f"bold {theme.PRIMARY}" if i == tab else theme.MUTED)
                for i, name in enumerate(TABS)
            ]
        )
        hint = "↑/↓ tabs · +/- speed · 1-9 jump · h help · q quit" if not help_line else (
            "1 Overview  2 CPU  3 Memory  4 Disk  5 Network  6 Processes  7 Incidents  8 Logs  9 Analytics"
        )
        status = Group(
            Text(hint, style=theme.MUTED),
            Text(f"  every {interval_holder[0]:.0f}s  ", style=theme.MUTED),
            Text(SPINNER[frame % len(SPINNER)], style=theme.PRIMARY),
            Text(f"  {datetime.now(UTC).strftime('%H:%M:%S')}", style=theme.MUTED),
            Text(f"  {error[:40]}" if error else "", style=theme.DANGER),
        )
        return Group(header, tabs_row, Text(""), _TABS[tab](state, width), Text(""), status)

    console.print("[dim]Sentinel monitor starting…[/dim]")
    with Live(
        render(),
        console=console,
        refresh_per_second=8,
        screen=interactive,
        auto_refresh=False,
    ) as live:
        while True:
            live.update(render(), refresh=True)
            deadline = time.monotonic() + interval_holder[0]
            while time.monotonic() < deadline:
                if not keys:
                    time.sleep(0.05)
                    continue
                key = keys.popleft()
                if key == "q":
                    return
                if key == "h":
                    help_line = not help_line
                if key in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
                    tab = int(key) - 1
                if key in (1, -1):
                    tab = (tab + key) % len(TABS)
                if key in ("+", "="):
                    interval_holder[0] = min(30.0, interval_holder[0] + 1)
                if key == "-":
                    interval_holder[0] = max(0.5, interval_holder[0] - 1)


def _demo() -> None:
    """Self-check: every tab renderer produces output without exceptions."""
    state: dict[str, Any] = {
        "host": host_collector.collect(),
        "cpu": _metric_map(cpu_collector.collect(interval=0.1)),
        "mem": _metric_map(mem_collector.collect()),
        "net": _metric_map(net_collector.collect()),
        "disk": disk_collector.collect(),
        "procs": proc_collector.top(limit=10, by="cpu"),
        "services": svc_collector.collect(DEFAULT_SERVICES),
        "history": {"cpu": deque(maxlen=40), "mem": deque(maxlen=40)},
        "net_hist": {"rx": deque(maxlen=60), "tx": deque(maxlen=60)},
        "bar": {"cpu": 0.0, "mem": 0.0, "disk": 0.0, "swap": 0.0},
        "incidents": None, "logs": None, "analytics": None, "error": None, "storage_error": None,
        "thresholds": load_config().thresholds,
    }
    for fn in _TABS:
        assert fn(state, 100) is not None
    assert len(_gradient("CI", theme.PRIMARY, theme.SECONDARY)) == 2
    print("monitor_tui self-check OK")


if __name__ == "__main__":
    _demo()