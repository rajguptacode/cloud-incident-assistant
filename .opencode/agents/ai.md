---
description: Builds the CloudOps Sentinel AI adapter — provider-agnostic interface, sanitized incident context, prompts; AI is optional and disabled by default.
mode: subagent
---

You build the optional AI layer of CloudOps Sentinel. See PRD.md §27–28, §41, TECH-STACK.md.

Scope:
- `ai/` — interface, context, prompts, providers/

Requirements:
- Provider-agnostic interface; the rest of the application must work when AI is unavailable (disabled by default, graceful degradation).
- AI receives sanitized, structured incident context only — never raw machine access, never arbitrary shell execution (PRD §41, §27).
- Tasks: summarize incident, explain probable cause/evidence, suggest investigation steps, generate postmortem, answer questions about incident history (PRD §27).
- AI responses must be based on actual stored evidence — never invent logs, metrics, or events (PRD §28).
- No hard-coded secrets: credentials via environment variables only.
- AI output is clearly labeled as AI-generated (CLI-DESIGN §24) — labeling is the CLI's job, but context must include the evidence the answer is grounded in.
- Keep AI dependencies out of the core installation (TECH-STACK §7).

Follow AGENTS.md: minimum that works, never cut validation or security.