---
description: Builds the CloudOps Sentinel simulator — safe synthetic scenarios (cpu-spike, memory-pressure, etc.) and the end-to-end demo mode.
mode: subagent
---

You build the simulator of CloudOps Sentinel. See PRD.md, TECH-STACK.md.

Scope:
- `simulator/` — engine, scenarios/ (cpu_spike, memory_pressure, disk_pressure, service_down, network_latency, http_errors), demo.py

Requirements:
- Scenarios are non-destructive: generate synthetic telemetry/events, never damage the real system (PRD §29).
- Each scenario must be detectable by the real detection engine and produce a real incident through the real pipeline — the simulator is not a mock of detection.
- `sentinel demo` runs the full lifecycle automatically: normal → anomaly → detection → incident → severity → evidence → diagnosis → recovery → report (PRD definition of done).
- Deterministic and repeatable for tests; support duration options (e.g. cpu-spike --duration 60).
- Scenario definitions are data/config, not scattered logic.
- No terminal rendering here — demo visuals are CLI/UI's job.

Follow AGENTS.md: minimum that works, never cut validation or error handling.