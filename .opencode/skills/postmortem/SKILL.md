---
name: postmortem
description: Use when writing an incident postmortem, RCA document, or after-incident review for CloudOps Sentinel. Trigger words: postmortem, blameless, timeline, rca, root cause analysis, lessons learned, incident report.
---

# Postmortem

Draft blameless postmortems with this structure:

1. **Summary** — one paragraph: what happened, impact, duration.
2. **Timeline** — UTC entries: detection, key actions, mitigation, resolution.
3. **Root cause** — evidence-backed; mark gaps as UNKNOWN, do not guess.
4. **Impact** — users, services, data, cost if known.
5. **Resolution** — what was done to restore service.
6. **Prevention** — concrete, tracked follow-ups; no vague "monitor better".

## RCA requirements

Produce all five parts:

- probable cause
- supporting evidence
- contributing factors
- confidence
- alternative possibilities

## Rules

- Blameless language only.
- No fabricated evidence — evidence comes from the stored telemetry, not from guesses.
- Do not claim certainty unless evidence supports it.
- Label the severity: INFO / LOW / MEDIUM / HIGH / CRITICAL.
- Reports can be generated via `sentinel report INC-xxxx` (markdown/text/JSON) — use that data as the source.