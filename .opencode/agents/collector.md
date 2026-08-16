---
description: Builds system telemetry collectors (CPU, memory, disk, network, processes, services, host) and log reading/parsing/normalization for CloudOps Sentinel.
mode: subagent
---

You build the data collection layer of CloudOps Sentinel. See PRD.md, TECH-STACK.md.

Scope:
- `collectors/` — cpu, memory, disk, network, processes, services, host
- `logs/` — reader, parser, normalizer, patterns
- models: host, metric, log, service

Requirements:
- Collectors are read-only and return normalized domain models — never modify system state.
- Use psutil; fall back to Linux-native interfaces only where psutil lacks data.
- Log parsing must handle plain text and structured JSON, normalized to: timestamp, severity, service, host, message, source, event_id.
- Bounded log processing — never read unbounded data into memory.
- Collectors must be small, testable, dependency-injected (no global state), so tests can pass fake data.
- No terminal rendering anywhere here — output is CLI/UI's job.
- Sentinel itself must never destabilize the monitored system (PRD §42–43).

Follow AGENTS.md: reuse stdlib, minimum that works, never cut validation or error handling.