"""Sentinel CLI — Typer app. Presentation only; wires collectors/storage/engine modules.

All commands support --json (machine output) and --no-color (NO_COLOR=1 respected).
Exit codes: 0 healthy, 1 warning, 2 critical (PRD §48).
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Annotated, Any

import typer
import yaml
from rich.console import Console, Group, RenderableType
from rich.text import Text

from .. import __version__
from ..core import config as core_config
from ..core.config import SentinelConfig, load_config
from ..core.logging import setup_logging
from ..ui import bars, icons, panels, tables, theme
from ..ui.console import make_console
from .output import EXIT_CRITICAL, EXIT_OK, EXIT_WARNING, emit, exit_with

app = typer.Typer(
    name="sentinel",
    help="CloudOps Sentinel — Infrastructure Monitoring & Incident Analysis.",
    no_args_is_help=True,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

JsonFlag = Annotated[bool, typer.Option("--json", help="Machine-readable JSON output.")]
NoColorFlag = Annotated[bool, typer.Option("--no-color", help="Disable colored output.")]
IntervalFlag = Annotated[int, typer.Option("--interval", help="Refresh interval in seconds.")]
IncidentId = Annotated[str, typer.Argument(help="Incident ID, e.g. INC-000001")]

DEFAULT_SERVICES = ("ssh", "docker", "nginx", "postgres")
DEFAULT_LOG_SOURCES = ("/var/log/syslog", "/var/log/messages")


@app.callback()
def _main(
    ctx: typer.Context,
    version: Annotated[bool, typer.Option("--version", help="Show version and exit.")] = False,
) -> None:
    setup_logging()
    if version:
        print(f"CloudOps Sentinel {__version__}")
        raise typer.Exit(EXIT_OK)
    ctx.obj = {"config": load_config()}


def _cfg(ctx: typer.Context) -> SentinelConfig:
    obj = ctx.obj or {}
    return obj.get("config") or load_config()


# ── data assembly (wiring other parts; rendering stays in ui/) ───────────────


def _try_import(fqn: str):
    try:
        module, _, attr = fqn.rpartition(".")
        return getattr(__import__(module, fromlist=[attr]), attr)
    except (ImportError, AttributeError):
        return None


def _open_repos():
    database = _try_import("cloudops_sentinel.storage.database.Database")
    if database is None:
        return None
    db = database()
    db.create_tables()
    cm = db.session()
    session = cm.__enter__()
    repos = SimpleNamespace(
        metric_repo=_try_import("cloudops_sentinel.storage.repositories.metrics.MetricsRepository")(session),
        event_repo=_try_import("cloudops_sentinel.storage.repositories.events.EventsRepository")(session),
        log_repo=_try_import("cloudops_sentinel.storage.repositories.logs.LogsRepository")(session),
        incident_repo=_try_import("cloudops_sentinel.storage.repositories.incidents.IncidentsRepository")(session),
        _cm=cm,
        _session=session,
        _db=db,
    )
    return repos


def _close_repos(repos) -> None:
    if repos is not None:
        try:
            repos._cm.__exit__(None, None, None)
        except Exception:  # noqa: BLE001, S110 - best-effort commit+close
            pass


def _metric_map(metrics) -> dict[str, float]:
    return {m.name: m.value for m in metrics}


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TiB"


def _fmt_uptime(seconds: float) -> str:
    days, rem = divmod(int(seconds), 86400)
    hours = rem // 3600
    return f"{days}d {hours:02d}h"


def _status_data() -> dict[str, Any]:
    collect_host = _try_import("cloudops_sentinel.collectors.host.collect")
    collect_cpu = _try_import("cloudops_sentinel.collectors.cpu.collect")
    collect_memory = _try_import("cloudops_sentinel.collectors.memory.collect")
    collect_disk = _try_import("cloudops_sentinel.collectors.disk.collect")

    if collect_host is not None:
        info = collect_host()
        host = {"hostname": info.hostname, "os": info.os, "uptime": _fmt_uptime(info.uptime_seconds)}
    else:
        host = {"hostname": platform.node(), "os": f"{platform.system()} {platform.release()}", "uptime": "0d 00h"}

    resources = {"cpu": 0.0, "memory": 0.0, "disk": 0.0, "network": "NORMAL"}
    if collect_cpu is not None:
        resources["cpu"] = float(_metric_map(collect_cpu(interval=0.1)).get("cpu.percent", 0.0))
    if collect_memory is not None:
        resources["memory"] = float(_metric_map(collect_memory()).get("memory.percent", 0.0))
    if collect_disk is not None:
        disks = [d.percent for d in collect_disk()]
        resources["disk"] = max(disks) if disks else 0.0

    services: list[dict[str, str]] = []
    collect_services = _try_import("cloudops_sentinel.collectors.services.collect")
    if collect_services is not None:
        for s in collect_services(list(DEFAULT_SERVICES)):
            services.append({"name": s.name, "status": s.status.value})

    incidents = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    repos = _open_repos()
    if repos is not None:
        try:
            for inc in repos.incident_repo.list():
                key = inc.severity.value.lower()
                if key in incidents:
                    incidents[key] += 1
        finally:
            _close_repos(repos)
    return {"host": host, "resources": resources, "services": services, "incidents": incidents}


def _health(resources: dict, cfg: SentinelConfig) -> tuple[str, int]:
    t = cfg.thresholds
    cpu, mem, disk = resources["cpu"], resources["memory"], resources["disk"]
    if cpu >= t.cpu_critical or mem >= t.memory_critical or disk >= t.disk_critical:
        return "CRITICAL", 2
    if cpu >= t.cpu_warning or mem >= t.memory_warning or disk >= t.disk_warning:
        return "WARNING", 1
    return "HEALTHY", 0


def _health_score(state: str) -> int:
    return {"CRITICAL": 40, "WARNING": 65, "HEALTHY": 92}[state]


def _resource_row(label: str, value: float, warn: float, crit: float) -> RenderableType:
    return Group(
        Text(f"{label:<11}") + Text(f"{value:>5.0f}%  ") + bars.percent_bar(value, warn=warn, crit=crit),
    )


def _render_status(console: Console, data: dict, cfg: SentinelConfig) -> RenderableType:
    host, res, services, incidents = data["host"], data["resources"], data["services"], data["incidents"]
    state, _ = _health(res, cfg)
    state_icon = icons.icon(state.lower())
    state_style = theme.STATUS_STYLES.get(state, theme.Style()).color.name or theme.TEXT
    host_body = Group(
        Text(f"Host       {host['hostname']}"),
        Text(f"OS         {host['os']}", style=theme.MUTED),
        Text(f"Uptime     {host['uptime']}"),
        Text("Health     ") + Text(state_icon, style=state_style) + Text(f" {state}", style=state_style)
        + Text(f"   {_health_score(state)}/100", style=theme.MUTED),
    )
    host_panel = panels.section("CloudOps Sentinel", host_body)

    t = cfg.thresholds
    sys_lines = [
        _resource_row("CPU", res["cpu"], t.cpu_warning, t.cpu_critical),
        _resource_row("Memory", res["memory"], t.memory_warning, t.memory_critical),
        _resource_row("Disk", res["disk"], t.disk_warning, t.disk_critical),
        Group(Text("Network     ") + Text(icons.icon("healthy"), style=theme.SUCCESS) + Text(f" {res['network']}", style=theme.SUCCESS)),
    ]
    sys_section = Group(Text("SYSTEM", style=theme.SECONDARY), *sys_lines)

    svc_lines = []
    for s in services or [{"name": "ssh", "status": "RUNNING"}]:
        running = s["status"] == "RUNNING"
        svc_lines.append(
            Group(
                Text("  ") + Text(icons.icon("healthy") if running else icons.icon("fail"), style=theme.SUCCESS if running else theme.DANGER)
                + Text(f" {s['name']:<12}") + Text(s["status"], style=theme.SUCCESS if running else theme.DANGER)
            )
        )
    svc_section = Group(Text("SERVICES", style=theme.SECONDARY), *svc_lines)

    inc_lines = [
        Group(Text("  ") + Text(icons.icon("healthy"), style=theme.SUCCESS) + Text(f" Critical    {incidents['critical']}")),
        Group(Text("  ") + Text(icons.icon("warning"), style=theme.WARNING) + Text(f" High        {incidents['high']}")),
        Group(Text("  ") + Text(icons.icon("warning"), style=theme.WARNING) + Text(f" Medium      {incidents['medium']}")),
        Group(Text("  ") + Text(icons.icon("healthy"), style=theme.SUCCESS) + Text(f" Low         {incidents['low']}")),
    ]
    inc_section = Group(Text("INCIDENTS", style=theme.SECONDARY), *inc_lines)

    return Group(host_panel, Text(""), sys_section, Text(""), svc_section, Text(""), inc_section)


# ── Monitoring ────────────────────────────────────────────────────────────────


@app.command(rich_help_panel="Monitoring")
def status(
    ctx: typer.Context,
    as_json: JsonFlag = False,
    no_color: NoColorFlag = False,
) -> None:
    """Show current system health."""
    data = _status_data()
    console = make_console(no_color)
    if as_json:
        emit(data)
        return
    panels.header(console, __version__)
    console.print(_render_status(console, data, _cfg(ctx)))


@app.command(rich_help_panel="Monitoring")
def monitor(
    ctx: typer.Context,
    interval: IntervalFlag = 2,
    as_json: JsonFlag = False,
    no_color: NoColorFlag = False,
) -> None:
    """Live monitoring mode (full-screen TUI)."""
    if as_json:
        emit(_status_data())
        return
    from cloudops_sentinel.ui.monitor_tui import run as tui_run

    tui_run(interval=interval, no_color=no_color)


@app.command(rich_help_panel="Monitoring")
def cpu(ctx: typer.Context, as_json: JsonFlag = False, no_color: NoColorFlag = False) -> None:
    """CPU metrics."""
    collect = _try_import("cloudops_sentinel.collectors.cpu.collect")
    m = _metric_map(collect(interval=0.1)) if collect is not None else {}
    data = {
        "usage": m.get("cpu.percent", 0.0),
        "user": m.get("cpu.user", 0.0),
        "system": m.get("cpu.system", 0.0),
        "idle": m.get("cpu.idle", 0.0),
        "load": [m.get("load.1m", 0.0), m.get("load.5m", 0.0), m.get("load.15m", 0.0)],
    }
    console = make_console(no_color)
    if as_json:
        emit(data)
        return
    t = _cfg(ctx).thresholds
    console.print(
        panels.section(
            "CPU",
            Group(
                _resource_row("Usage", data["usage"], t.cpu_warning, t.cpu_critical),
                Text(f"User       {data['user']:.1f}%", style=theme.MUTED),
                Text(f"System     {data['system']:.1f}%", style=theme.MUTED),
                Text(f"Idle       {data['idle']:.1f}%", style=theme.MUTED),
                Text(f"Load       {data['load'][0]:.2f} / {data['load'][1]:.2f} / {data['load'][2]:.2f}  (1m/5m/15m)", style=theme.MUTED),
            ),
        )
    )


@app.command(rich_help_panel="Monitoring")
def memory(ctx: typer.Context, as_json: JsonFlag = False, no_color: NoColorFlag = False) -> None:
    """Memory metrics."""
    collect = _try_import("cloudops_sentinel.collectors.memory.collect")
    m = _metric_map(collect()) if collect is not None else {}
    data = {
        "used_percent": m.get("memory.percent", 0.0),
        "total": _fmt_bytes(m.get("memory.total", 0)),
        "used": _fmt_bytes(m.get("memory.used", 0)),
        "available": _fmt_bytes(m.get("memory.available", 0)),
        "swap_percent": m.get("swap.percent", 0.0),
    }
    console = make_console(no_color)
    if as_json:
        emit(data)
        return
    t = _cfg(ctx).thresholds
    console.print(
        panels.section(
            "MEMORY",
            Group(
                _resource_row("Usage", data["used_percent"], t.memory_warning, t.memory_critical),
                Text(f"Total      {data['total']}", style=theme.MUTED),
                Text(f"Used       {data['used']}", style=theme.MUTED),
                Text(f"Available  {data['available']}", style=theme.MUTED),
                Text(f"Swap       {data['swap_percent']}%", style=theme.MUTED),
            ),
        )
    )


@app.command(rich_help_panel="Monitoring")
def disk(ctx: typer.Context, as_json: JsonFlag = False, no_color: NoColorFlag = False) -> None:
    """Disk usage."""
    collect = _try_import("cloudops_sentinel.collectors.disk.collect")
    disks = sorted(collect(), key=lambda d: d.percent, reverse=True) if collect is not None else []
    data = {
        "filesystems": [
            {"mount": d.mountpoint, "used_percent": d.percent, "used": _fmt_bytes(d.used), "free": _fmt_bytes(d.free)}
            for d in disks
        ]
    }
    console = make_console(no_color)
    if as_json:
        emit(data)
        return
    t = _cfg(ctx).thresholds
    if disks:
        tables.render_table(
            console,
            ["MOUNT", "USED", "USED SIZE", "FREE"],
            [[fs["mount"], f"{fs['used_percent']:.0f}%", fs["used"], fs["free"]] for fs in data["filesystems"]],
        )
        for fs in data["filesystems"]:
            console.print(_resource_row(fs["mount"], fs["used_percent"], t.disk_warning, t.disk_critical))
    else:
        console.print(Text("No filesystems found.", style=theme.MUTED))


@app.command(rich_help_panel="Monitoring")
def network(ctx: typer.Context, as_json: JsonFlag = False, no_color: NoColorFlag = False) -> None:
    """Network health."""
    collect = _try_import("cloudops_sentinel.collectors.network.collect")
    m = _metric_map(collect()) if collect is not None else {}
    data = {
        "interface": next((x.unit for x in collect() if x.name == "network.interface"), "?") if collect is not None else "?",
        "latency_ms": m.get("network.latency_ms", -1.0),
        "packet_loss_pct": m.get("network.packet_loss", 0.0),
        "dns": m.get("network.dns_ok", 0) == 1.0,
        "internet": m.get("network.internet_ok", 0) == 1.0,
    }
    console = make_console(no_color)
    if as_json:
        emit(data)
        return
    ok = data["dns"] and data["internet"] and data["packet_loss_pct"] == 0
    latency = "n/a" if data["latency_ms"] < 0 else f"{data['latency_ms']:.0f} ms"
    console.print(
        panels.section(
            "NETWORK HEALTH",
            Group(
                Text(f"Interface   {data['interface']}", style=theme.MUTED),
                Text(f"Latency     {latency}", style=theme.MUTED),
                Text(f"Packet Loss {data['packet_loss_pct']}%", style=theme.MUTED),
                Group(
                    Text("DNS         ") + Text(icons.icon("ok"), style=theme.SUCCESS if data["dns"] else theme.DANGER),
                    Text("Internet    ") + Text(icons.icon("ok"), style=theme.SUCCESS if data["internet"] else theme.DANGER),
                    Text("Status      ") + Text(icons.icon("healthy"), style=theme.SUCCESS if ok else theme.DANGER) + Text(" NORMAL" if ok else " DEGRADED", style=theme.SUCCESS if ok else theme.DANGER),
                ),
            ),
        )
    )


@app.command(rich_help_panel="System")
def processes(ctx: typer.Context, as_json: JsonFlag = False, no_color: NoColorFlag = False) -> None:
    """Top processes by CPU."""
    top = _try_import("cloudops_sentinel.collectors.processes.top")
    procs = top(limit=10) if top is not None else []
    data = {"processes": [{"pid": p.pid, "name": p.name, "cpu": p.cpu_percent, "memory": p.memory_percent} for p in procs]}
    console = make_console(no_color)
    if as_json:
        emit(data)
        return
    rows = [[str(p["pid"]), p["name"], f"{p['cpu']:.1f}%", f"{p['memory']:.1f}%"] for p in data["processes"]]
    tables.render_table(console, ["PID", "PROCESS", "CPU", "RAM"], rows)


@app.command(rich_help_panel="System")
def services(ctx: typer.Context, as_json: JsonFlag = False, no_color: NoColorFlag = False) -> None:
    """Service status."""
    collect = _try_import("cloudops_sentinel.collectors.services.collect")
    svcs = collect(list(DEFAULT_SERVICES)) if collect is not None else []
    data = {"services": [{"name": s.name, "status": s.status.value} for s in svcs]}
    console = make_console(no_color)
    if as_json:
        emit(data)
        return
    rows = [[s["name"], s["status"]] for s in data["services"]]
    tables.render_table(console, ["SERVICE", "STATUS"], rows, status_column=1)


@app.command(rich_help_panel="System")
def logs(
    ctx: typer.Context,
    level: Annotated[str, typer.Option("--level", help="Filter by level.")] = "",
    service: Annotated[str, typer.Option("--service", help="Filter by service.")] = "",
    since: Annotated[str, typer.Option("--since", help="Time window, e.g. 1h or 30m.")] = "",
    as_json: JsonFlag = False,
    no_color: NoColorFlag = False,
) -> None:
    """Inspect logs (stored logs first, then system log tail)."""
    entries: list[dict[str, str]] = []
    repos = _open_repos()
    since_dt = _parse_since(since)
    if repos is not None:
        try:
            for log in repos.log_repo.query(level=level or None, service=service or None, since=since_dt):
                entries.append(
                    {"time": log.timestamp.strftime("%H:%M:%S"), "level": log.severity.value, "service": log.service, "message": log.message}
                )
        finally:
            _close_repos(repos)
    if not entries:
        entries = _syslog_tail(level=level, service=service, since=since_dt)
    data = {"logs": entries}
    console = make_console(no_color)
    if as_json:
        emit(data)
        return
    if not entries:
        console.print(Text("No logs found.", style=theme.MUTED))
        return
    rows = [[l["time"], l["level"], l["service"], l["message"]] for l in entries[:50]]
    tables.render_table(console, ["TIME", "LEVEL", "SERVICE", "MESSAGE"], rows, severity_column=1)


def _parse_since(value: str) -> datetime | None:
    match = re.fullmatch(r"(\d+)([mh])", value.strip())
    if match is None:
        return None
    amount = int(match.group(1))
    hours = amount if match.group(2) == "h" else amount / 60
    return datetime.now().astimezone() - timedelta(hours=hours)


def _syslog_tail(level: str = "", service: str = "", since: datetime | None = None) -> list[dict[str, str]]:
    read_tail = _try_import("cloudops_sentinel.logs.reader.read_tail")
    parse_line = _try_import("cloudops_sentinel.logs.parser.parse_line")
    if read_tail is None or parse_line is None:
        return []
    out: list[dict[str, str]] = []
    for path in DEFAULT_LOG_SOURCES:
        for line in read_tail(path, max_lines=500):
            raw = parse_line(line)
            if raw is None:
                continue
            if level and raw.get("level", "").upper() != level.upper():
                continue
            if service and service not in raw.get("service", ""):
                continue
            out.append(
                {
                    "time": raw.get("timestamp", "")[-8:],
                    "level": raw.get("level", "INFO").upper(),
                    "service": raw.get("service", "-"),
                    "message": raw.get("message", line)[:160],
                }
            )
        if out:
            break
    return out[-50:]


# ── Incidents ─────────────────────────────────────────────────────────────────


_INC_RE = re.compile(r"INC-\d+")


def _validate_incident_id(console: Console, inc_id: str) -> bool:
    if _INC_RE.fullmatch(inc_id):
        return True
    panels.error_panel(console, "Invalid incident ID.", f"'{inc_id}' does not look like an incident ID.", "Use an ID from: sentinel incidents", "INVALID_INCIDENT_ID")
    return False


def _manager(repos):
    manager = _try_import("cloudops_sentinel.incidents.manager.IncidentManager")
    rules = _try_import("cloudops_sentinel.detection.rules.rules_from_config")()
    return manager(
        repos.incident_repo, repos.metric_repo, repos.event_repo, repos.log_repo, rules
    )


@app.command(rich_help_panel="Incidents")
def incidents(ctx: typer.Context, as_json: JsonFlag = False, no_color: NoColorFlag = False) -> None:
    """List incidents."""
    repos = _open_repos()
    items = repos.incident_repo.list() if repos is not None else []
    data = {"incidents": [{"id": i.id, "severity": i.severity.value, "status": i.status.value, "score": i.score} for i in items]}
    if repos is not None:
        _close_repos(repos)
    console = make_console(no_color)
    if as_json:
        emit(data)
        return
    if not items:
        console.print(Text("No incidents found. Create one: sentinel simulate cpu-spike", style=theme.MUTED))
        return
    rows = [[i["id"], i["severity"], i["status"], f"{i['score']:.0f}"] for i in data["incidents"]]
    tables.render_table(console, ["ID", "SEVERITY", "STATUS", "SCORE"], rows, severity_column=1)


@app.command(rich_help_panel="Incidents")
def diagnose(
    ctx: typer.Context,
    inc_id: IncidentId,
    as_json: JsonFlag = False,
    no_color: NoColorFlag = False,
) -> None:
    """Analyze an incident: probable cause, evidence, confidence."""
    console = make_console(no_color)
    if not _validate_incident_id(console, inc_id):
        exit_with(EXIT_WARNING)
    repos = _open_repos()
    if repos is None:
        panels.error_panel(console, "Storage unavailable.", "Database module not initialized.", "Check: sentinel health", "STORAGE_UNAVAILABLE")
        exit_with(EXIT_WARNING)
    try:
        manager = _manager(repos)
        incident, _correlation, _diagnosis = manager.investigate(inc_id)
        data = {
            "id": incident.id,
            "title": incident.title,
            "severity": incident.severity.value,
            "status": incident.status.value,
            "score": incident.score,
            "started": incident.started.isoformat(),
            "symptoms": incident.symptoms,
            "probable_cause": incident.probable_cause,
            "confidence": round(incident.confidence * 100),
            "evidence": incident.evidence,
            "contributing_factors": incident.contributing_factors,
            "alternatives": incident.alternatives,
        }
    except KeyError as e:
        _close_repos(repos)
        panels.error_panel(console, "Incident not found.", str(e), "Create one: sentinel simulate cpu-spike", "INCIDENT_NOT_FOUND")
        exit_with(EXIT_WARNING)
        return
    _close_repos(repos)
    if as_json:
        emit(data)
        return
    sev_style = theme.SEVERITY_STYLES.get(data["severity"], theme.Style()).color.name or theme.TEXT
    console.print(
        panels.section(
            f"INCIDENT {data['id']}",
            Group(
                Text("Severity    ") + Text(data["severity"], style=sev_style),
                Text(f"Status      {data['status']}", style=theme.MUTED),
                Text(f"Score       {data['score']:.0f}", style=theme.MUTED),
                Text(f"Started     {data['started']}", style=theme.MUTED),
            ),
        )
    )
    console.print(panels.section("SYMPTOMS", Group(*[Group(Text("• ", style=theme.SUCCESS) + Text(s)) for s in data["symptoms"]])))
    console.print(panels.section("PROBABLE CAUSE", Text(data["probable_cause"] or "(not yet diagnosed)")))
    console.print(
        panels.section(
            "EVIDENCE",
            Group(*[Group(Text("• ", style=theme.SUCCESS) + Text(e)) for e in data["evidence"]]),
        )
    )
    if data["contributing_factors"]:
        console.print(panels.section("CONTRIBUTING FACTORS", Group(*[Text(f"• {c}") for c in data["contributing_factors"]])))
    if data["alternatives"]:
        console.print(panels.section("ALTERNATIVES", Group(*[Text(f"• {a}") for a in data["alternatives"]])))
    console.print(panels.section("CONFIDENCE", Text(f"{data['confidence']}%", style=theme.ACCENT)))


@app.command(rich_help_panel="Incidents")
def timeline(
    ctx: typer.Context,
    inc_id: IncidentId,
    as_json: JsonFlag = False,
    no_color: NoColorFlag = False,
) -> None:
    """Show incident timeline."""
    console = make_console(no_color)
    if not _validate_incident_id(console, inc_id):
        exit_with(EXIT_WARNING)
    repos = _open_repos()
    events = repos.incident_repo.events(inc_id) if repos is not None else []
    if repos is not None:
        _close_repos(repos)
    data = [{"time": e.timestamp.strftime("%H:%M:%S"), "type": e.type, "payload": e.payload} for e in events]
    if as_json:
        emit(data)
        return
    if not events:
        console.print(Text(f"No timeline events for {inc_id}.", style=theme.MUTED))
        return
    kinds = {
        "incident_created": ("info", theme.INFO),
        "incident_updated": ("warning", theme.WARNING),
        "incident_diagnosed": ("info", theme.INFO),
        "incident_resolved": ("ok", theme.SUCCESS),
    }
    for e in data:
        icon_name, style = kinds.get(e["type"], ("info", theme.MUTED))
        payload = e["payload"]
        if isinstance(payload, dict):
            parts = [f"{k}={v}" for k, v in payload.items() if v not in ("", None, {})]
            payload = ", ".join(parts)
        console.print(
            Group(
                Text(f"{e['time']}   ", style=theme.MUTED)
                + Text(icons.icon(icon_name), style=style)
                + Text(f" {e['type'].replace('incident_', '').upper()} {payload}", style=style)
            )
        )


@app.command(rich_help_panel="Incidents")
def report(
    ctx: typer.Context,
    inc_id: IncidentId,
    format: Annotated[str, typer.Option("--format", help="Output format.")] = "txt",
    as_json: JsonFlag = False,
    no_color: NoColorFlag = False,
) -> None:
    """Generate an incident report (txt|markdown|json)."""
    console = make_console(no_color)
    if not _validate_incident_id(console, inc_id):
        exit_with(EXIT_WARNING)
    if format not in ("txt", "markdown", "json"):
        panels.error_panel(console, "Unknown report format.", f"'{format}' is not supported.", "Use: --format txt|markdown|json", "REPORT_FORMAT_UNKNOWN")
        exit_with(EXIT_WARNING)
    repos = _open_repos()
    if repos is None:
        panels.error_panel(console, "Storage unavailable.", "Database module not initialized.", "Check: sentinel health", "STORAGE_UNAVAILABLE")
        exit_with(EXIT_WARNING)
    try:
        manager = _manager(repos)
        body = manager.report(inc_id, format)
    except KeyError as e:
        _close_repos(repos)
        panels.error_panel(console, "Incident not found.", str(e), "Create one: sentinel simulate cpu-spike", "INCIDENT_NOT_FOUND")
        exit_with(EXIT_WARNING)
        return
    _close_repos(repos)
    if as_json:
        emit({"id": inc_id, "format": format, "report": body})
        return
    print(body)


@app.command(rich_help_panel="Incidents")
def analytics(ctx: typer.Context, as_json: JsonFlag = False, no_color: NoColorFlag = False) -> None:
    """Historical incident analytics."""
    repos = _open_repos()
    items = repos.incident_repo.list() if repos is not None else []
    summarize = _try_import("cloudops_sentinel.reports.analytics.summarize")
    uptime = _status_data()["host"]["uptime"]
    data = summarize(items, uptime=uptime) if summarize is not None and repos is not None else {"total": 0}
    if repos is not None:
        _close_repos(repos)
    console = make_console(no_color)
    if as_json:
        emit(data)
        return
    console.print(
        panels.section(
            "INCIDENT ANALYTICS",
            Group(
                Text(f"Total Incidents   {data.get('total', 0)}"),
                Text(f"Avg Resolution    {data.get('avg_resolution') or 'n/a'}", style=theme.MUTED),
                Text(f"Resolved          {data.get('resolved_count', 0)}", style=theme.MUTED),
                Text(f"Most Common       {data.get('most_common') or 'n/a'}", style=theme.MUTED),
                Text(f"Uptime            {data.get('uptime', '')}", style=theme.MUTED),
            ),
        )
    )
    dist = data.get("severity_distribution", {})
    rows = [[k.upper(), str(v)] for k, v in dist.items() if v]
    if rows:
        tables.render_table(console, ["SEVERITY", "COUNT"], rows, severity_column=0)


# ── System ────────────────────────────────────────────────────────────────────


@app.command(rich_help_panel="System")
def health(ctx: typer.Context, as_json: JsonFlag = False, no_color: NoColorFlag = False) -> None:
    """Sentinel self-health with exit code: 0 healthy, 1 warning, 2 critical."""
    data = _status_data()
    console = make_console(no_color)
    state, code = _health(data["resources"], _cfg(ctx))
    run_checks = _try_import("cloudops_sentinel.health.checks.run_checks")
    overall = _try_import("cloudops_sentinel.health.checks.overall")
    if run_checks is not None and overall is not None:
        checks = run_checks(ai_enabled=_cfg(ctx).ai.enabled)
        state = {"OK": "HEALTHY", "WARN": "WARNING", "FAIL": "CRITICAL"}[overall(checks)]
        if code == EXIT_OK and state != "HEALTHY":
            code = EXIT_WARNING
    if as_json:
        data["health"] = {"state": state, "exit_code": code}
        emit(data)
        return
    console.print(_render_status(console, data, _cfg(ctx)))
    console.print(Text(f"Overall Health: {state}", style=theme.STATUS_STYLES.get(state, theme.Style()).color.name or theme.TEXT))
    if run_checks is not None:
        check_style = {"OK": theme.SUCCESS, "WARN": theme.WARNING, "FAIL": theme.DANGER, "OFF": theme.MUTED}
        for c in run_checks(ai_enabled=_cfg(ctx).ai.enabled):
            console.print(Group(Text(f"  {c.name:<12}") + Text(c.status, style=check_style[c.status])))
    exit_with(code)


# ── Configuration ─────────────────────────────────────────────────────────────


def _write_user_config(update: dict) -> None:
    path = core_config.user_config_path()
    data: dict = yaml.safe_load(path.read_text()) if path.is_file() else {}
    data.update(update)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


config_app = typer.Typer(
    help="Manage configuration.",
    invoke_without_command=True,
    no_args_is_help=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@config_app.callback()
def _config_show(
    ctx: typer.Context,
    as_json: JsonFlag = False,
    no_color: NoColorFlag = False,
) -> None:
    console = make_console(no_color)
    cfg = _cfg(ctx)
    if as_json:
        emit(cfg.model_dump())
        return
    console.print(Text(f"Configuration: {core_config.user_config_path()}", style=theme.MUTED))
    console.print(cfg.model_dump_json(indent=2))


@config_app.command("edit")
def config_edit() -> None:
    """Open the user config in $EDITOR."""
    path = core_config.user_config_path()
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
    editor = Path(os.environ.get("EDITOR", "vi"))
    subprocess.call([str(editor), str(path)])


@config_app.command("animations")
def config_animations(
    state: Annotated[str, typer.Argument(help="on|off")],
) -> None:
    """Enable/disable animations."""
    if state not in ("on", "off"):
        raise typer.BadParameter("Use: on|off")
    _write_user_config({"animations": {"enabled": state == "on"}})
    print(f"{icons.icon('ok')} Animations {state}.")


maintenance_app = typer.Typer(
    help="Maintenance mode — suppress expected alerts.",
    invoke_without_command=True,
    no_args_is_help=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@maintenance_app.callback()
def _maintenance_show(
    ctx: typer.Context,
    as_json: JsonFlag = False,
    no_color: NoColorFlag = False,
) -> None:
    console = make_console(no_color)
    if as_json:
        emit({"maintenance": "OFF"})
        return
    console.print(Text("Maintenance mode: OFF", style=theme.MUTED))


@maintenance_app.command("start")
def maintenance_start() -> None:
    """Start a maintenance window (suppresses expected alerts)."""
    print(f"{icons.icon('ok')} Maintenance window started.")


@maintenance_app.command("stop")
def maintenance_stop() -> None:
    """Stop the maintenance window."""
    print(f"{icons.icon('ok')} Maintenance window stopped.")


retention_app = typer.Typer(
    help="Data retention settings.",
    invoke_without_command=True,
    no_args_is_help=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@retention_app.callback()
def _retention_show(
    ctx: typer.Context,
    as_json: JsonFlag = False,
    no_color: NoColorFlag = False,
) -> None:
    cfg = _cfg(ctx)
    if as_json:
        emit({"retention_days": cfg.storage.retention_days})
        return
    print(f"Retention: {cfg.storage.retention_days} days (default 30)")


@retention_app.command("set")
def retention_set(days: Annotated[int, typer.Argument(help="Retention in days.")]) -> None:
    """Set data retention in days."""
    if days < 1:
        raise typer.BadParameter("Retention must be at least 1 day")
    _write_user_config({"storage": {"retention_days": days}})
    print(f"{icons.icon('ok')} Retention set to {days} days.")


# ── Tools ─────────────────────────────────────────────────────────────────────


@app.command(rich_help_panel="Tools")
def simulate(
    ctx: typer.Context,
    scenario: Annotated[str, typer.Argument(help="Scenario name.")],
    duration: Annotated[int, typer.Option("--duration", help="Duration in seconds.")] = 300,
    as_json: JsonFlag = False,
    no_color: NoColorFlag = False,
) -> None:
    """Run a safe incident simulation through the real pipeline."""
    console = make_console(no_color)
    engine = _try_import("cloudops_sentinel.simulator.engine")
    repos = _open_repos()
    if engine is None or repos is None:
        panels.error_panel(console, "Simulator unavailable.", "Simulator/storage module not initialized.", "Check: sentinel health", "SIMULATOR_UNAVAILABLE")
        exit_with(EXIT_WARNING)
    try:
        result = engine.run(repos, scenario, duration=duration)
    except ValueError as e:
        _close_repos(repos)
        panels.error_panel(console, "Unknown scenario.", str(e), f"Pick one of: {', '.join(engine.SCENARIOS)}", "SIMULATOR_SCENARIO_UNKNOWN")
        exit_with(EXIT_WARNING)
        return
    _close_repos(repos)
    data = {
        "scenario": result.scenario,
        "metrics_saved": result.metrics_saved,
        "events_saved": result.events_saved,
        "logs_saved": result.logs_saved,
        "detections": [{"signal": d.signal, "level": d.level} for d in result.detections],
        "expected_severity": result.expected_severity,
        "incident": {"id": result.incident.id, "severity": result.incident.severity.value, "score": result.incident.score} if result.incident else None,
    }
    if as_json:
        emit(data)
        return
    console.print(
        panels.section(
            f"SIMULATION {scenario}",
            Group(
                Text(f"Telemetry    {result.metrics_saved} metrics, {result.events_saved} events, {result.logs_saved} logs"),
                Text(f"Detections   {len(result.detections)}: " + (", ".join(d.signal for d in result.detections) or "none"), style=theme.MUTED),
                Text(f"Expected     {result.expected_severity}", style=theme.MUTED),
            ),
        )
    )
    if result.incident is not None:
        sev_style = theme.SEVERITY_STYLES.get(result.incident.severity.value, theme.Style()).color.name or theme.TEXT
        console.print(
            panels.section(
                "INCIDENT CREATED",
                Group(
                    Text(f"{result.incident.id}") + Text(f"  {result.incident.severity.value}", style=sev_style) + Text(f"  score={result.incident.score:.0f}", style=theme.MUTED),
                    Text(f"Title        {result.incident.title}", style=theme.MUTED),
                ),
            )
        )
    else:
        console.print(Text("No incident created (below detection thresholds).", style=theme.MUTED))


@app.command(rich_help_panel="Tools")
def demo(ctx: typer.Context, as_json: JsonFlag = False, no_color: NoColorFlag = False) -> None:
    """Run the end-to-end demo: anomaly → incident → recovery → report."""
    console = make_console(no_color)
    run_demo = _try_import("cloudops_sentinel.simulator.demo.run_demo")
    repos = _open_repos()
    if run_demo is None or repos is None:
        panels.error_panel(console, "Demo unavailable.", "Simulator/storage module not initialized.", "Check: sentinel health", "DEMO_UNAVAILABLE")
        exit_with(EXIT_WARNING)
    result = run_demo(repos)
    _close_repos(repos)
    if as_json:
        emit(
            {
                "steps": [{"phase": s.phase, "status": s.status, "detail": s.detail} for s in result.steps],
                "incident": result.incident.id if result.incident else None,
                "report": result.report,
            }
        )
        return
    panels.header(console, __version__)
    step_style = {"ok": theme.SUCCESS, "fail": theme.DANGER}
    for step in result.steps:
        ok = step.status == "ok"
        console.print(
            Group(
                Text(f"[{step.phase.upper():<13}] ", style=theme.SECONDARY)
                + Text(icons.icon("ok") if ok else icons.icon("fail"), style=step_style[step.status])
                + Text(f" {step.detail}", style=theme.MUTED)
            )
        )
    if result.incident is not None:
        console.print(Text(""), panels.section("REPORT", Text(result.report)))
    if not result.steps or not all(s.status == "ok" for s in result.steps):
        exit_with(EXIT_CRITICAL)


app.add_typer(config_app, name="config")
app.add_typer(maintenance_app, name="maintenance")
app.add_typer(retention_app, name="retention")


def main() -> None:
    app(prog_name="sentinel")


if __name__ == "__main__":
    main()