---
name: incident-triage
description: Use when triaging a CloudOps Sentinel incident — severity levels, triage questions, incident lifecycle. Trigger words: incident, sev, severity, triage, sev1, sev2, sev3, outage, pager, on-call, INC-.
---

# Incident Triage

## 1. Classify severity

| Severity | Score range | Response |
|----------|-------------|----------|
| INFO | 0–20 | Informational, no action needed |
| LOW | 21–40 | Monitor, normal queue |
| MEDIUM | 41–60 | Workaround ASAP, investigate |
| HIGH | 61–80 | Urgent, page on-call |
| CRITICAL | 81–100 | Immediate, all hands |

Severity must combine multiple signals — never rely on a single metric.

## 2. Ask before diving in

- Affected service and subsystem?
- Started when? Detected by what (alert, metric, log)?
- Recent deploys/config changes in the window?

## 3. Timeline capture

Record every action with UTC timestamps. Never fabricate entries — mark gaps as UNKNOWN.

## 4. Incident lifecycle

```
DETECTED → TRIAGED → INVESTIGATING → MITIGATED → RESOLVED → CLOSED
```

False alarm path: `DETECTED → FALSE POSITIVE`.

## 5. Minimum fix

Propose the smallest change that restores service. V1 is read-only: never restart or kill processes without explicit user approval.