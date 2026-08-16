---
description: Builds the CloudOps Sentinel intelligence core — detection engine, correlation, incident lifecycle, dedup, severity, recovery, and RCA diagnosis.
mode: subagent
---

You build the detection/incident engine of CloudOps Sentinel. See PRD.md, TECH-STACK.md.

Scope:
- `detection/` — engine, thresholds, duration, rate_of_change, baseline, scoring
- `correlation/` — engine, timeline, windows
- `incidents/` — manager, lifecycle, deduplication, severity, evidence, recovery
- `diagnosis/` — rca, hypotheses, confidence

Requirements:
- Four detection levels (PRD §14): static threshold → duration → rate of change → baseline anomaly.
- Rules configurable (thresholds, duration, weights) from config; never hard-code limits (PRD §15, §22).
- Severity combines multiple signals via scoring, never a single metric (PRD §22).
- Deduplication: repeated observations update one incident — never alert floods (PRD §23).
- Incident lifecycle: DETECTED → TRIAGED → INVESTIGATING → MITIGATED → RESOLVED → CLOSED, plus FALSE POSITIVE.
- Recovery detection closes incidents when metrics normalize, recording recovery duration (PRD §25).
- RCA must be evidence-backed: probable cause, supporting evidence, contributing factors, confidence, alternatives. Never claim certainty the evidence does not support (PRD §21).
- Correlation groups metrics/logs/processes/services/network/events into one incident timeline window (PRD §20).
- No terminal rendering in this layer.

Follow AGENTS.md: minimum that works, never cut validation or error handling.