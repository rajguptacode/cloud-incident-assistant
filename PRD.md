# PRD v2 — CloudOps Sentinel

## Product

CloudOps Sentinel

## Tagline

CLI-First Intelligent Infrastructure Monitoring & Incident Analysis

## Primary Interface

CLI

## Future Interface

Web Dashboard — later phase

---

## 1. Product Vision

CloudOps Sentinel ek local-first, CLI-based infrastructure monitoring and incident-analysis platform hoga.

Ye Linux machine/server ko continuously monitor karega, metrics/logs/events collect karega, abnormal behavior detect karega, related signals ko correlate karega, incident create karega aur probable root cause + recommended investigation steps provide karega.

### Core pipeline

```
SYSTEM
  ↓
COLLECT
  ↓
NORMALIZE
  ↓
STORE
  ↓
DETECT
  ↓
CORRELATE
  ↓
ANALYZE
  ↓
INCIDENT
  ↓
RECOMMEND
  ↓
REPORT
```

> AI optional intelligence layer hoga — not the foundation.

---

## 2. Main Design Principle

### Local-first

**Abhi:**

```
Ubuntu/Linux PC
      ↓
CloudOps Sentinel
```

Cloud account ki zarurat nahi.

**Future:**

```
Cloud VM
   ↓
Sentinel Agent
   ↓
Sentinel Backend
```

### Offline-first

Basic monitoring, detection, storage aur CLI internet ke bina bhi kaam karenge.

AI/cloud integrations optional honge.

---

## 3. CLI-First Philosophy

Project ka primary interface CLI hoga.

Example:

```
sentinel status
sentinel monitor
sentinel incidents
sentinel logs
sentinel services
sentinel diagnose INC-0001
sentinel report INC-0001
sentinel simulate cpu-spike
sentinel config
```

Future web UI isi backend/data layer ko consume karega.

---

## 4. CLI Command Architecture

### Main command

```
sentinel
```

### Help

```
sentinel --help
```

### Version

```
sentinel --version
```

### sentinel status

Current machine health.

```
CLOUDOPS SENTINEL
────────────────────────────

HOST
Hostname       ubuntu-pc
OS             Ubuntu Linux
Uptime         3d 04h

RESOURCES
CPU            42%     ✓
Memory         61%     ✓
Disk           73%     ✓
Network        NORMAL  ✓

SERVICES
SSH            RUNNING ✓
Docker         RUNNING ✓

INCIDENTS
Critical       0
High           0
Medium         1

Overall Health: HEALTHY
```

---

## 5. sentinel monitor

Live monitoring mode.

```
sentinel monitor
```

Refresh:

```
CPU   ███████░░░  68%
RAM   ██████░░░░  61%
DISK  ███████░░░  73%

NETWORK
RX  2.4 MB/s
TX  0.8 MB/s

ACTIVE INCIDENTS
1
```

Optional:

```
sentinel monitor --interval 2
```

---

## 6. sentinel cpu

CPU-specific information.

```
sentinel cpu
```

Output:

```
CPU
──────────────────
Usage       78%
User        52%
System      21%
Idle        22%

Load Average
1m          2.31
5m          1.84
15m         1.22
```

Future:

```
sentinel cpu --history 1h
```

---

## 7. sentinel memory

Show:

- total
- used
- available
- swap
- percentage

Also detect abnormal growth.

---

## 8. sentinel disk

```
sentinel disk
```

Example:

```
FILESYSTEM       USED       FREE
/dev/sda1        73%        27%
```

Advanced:

```
sentinel disk --forecast
```

Possible output:

```
Disk Usage Forecast
────────────────────────

Current:        73%
Growth rate:    +1.4% / day

90% threshold:
Estimated in ~12 days

Confidence: Medium
```

> Forecast will clearly be labelled as an estimate, not a guarantee.

---

## 9. sentinel network

Show:

- interface
- IP
- RX/TX
- packet errors
- latency
- packet loss
- DNS
- HTTP connectivity

Example:

```
NETWORK HEALTH

Interface    eth0
IP           192.168.x.x

Latency      24 ms
Packet Loss  0%
DNS          ✓
Internet     ✓
```

---

## 10. sentinel processes

Top processes:

```
PID     PROCESS        CPU     RAM
1821    python         71%     12%
923     nginx          12%      4%
711     postgres        8%       9%
```

Filters:

```
sentinel processes --cpu
sentinel processes --memory
```

---

## 11. Service Monitoring

```
sentinel services
```

Example:

```
SERVICE        STATUS
nginx          RUNNING ✓
ssh            RUNNING ✓
docker         RUNNING ✓
postgres       STOPPED ✗
```

**Important:**

- V1 read-only monitoring.
- Sentinel won't automatically restart or kill processes.
- Later optional remediation can be added with explicit user approval.

---

## 12. Log Intelligence

```
sentinel logs
```

Filters:

```
sentinel logs --level error
sentinel logs --service nginx
sentinel logs --since 1h
```

Output:

```
14:32:11 ERROR nginx upstream timeout
14:32:15 ERROR nginx connection refused
14:32:19 WARNING nginx retry
```

---

## 13. Structured Log Normalization

Different log formats ko common schema me convert karenge:

- timestamp
- severity
- service
- host
- message
- source
- event_id

This makes correlation possible.

---

## 14. Detection Engine

Detection ke multiple levels honge.

| Level | Type | Example |
|-------|------|---------|
| Level 1 | Static threshold | CPU > 90% |
| Level 2 | Duration | CPU > 90% continuously for 5 minutes |
| Level 3 | Rate of change | CPU: 30% → 91% in 2 minutes |
| Level 4 | Baseline anomaly | System historical normal behavior ke against compare karega |

Level 4 example:

```
Normal:
20–40%

Current:
91%

→ Anomaly
```

---

## 15. Detection Rule Engine

Rules configurable honge.

Example config:

```yaml
cpu:
  warning: 70
  critical: 90
  duration: 300

memory:
  warning: 75
  critical: 90

disk:
  warning: 80
  critical: 90
```

User rules modify kar sakega:

```
sentinel config edit
```

---

## 16. Incident Engine

Detection ke baad Incident Candidate create hoga.

Example:

```
CPU > 95%
+
HTTP latency increased
+
nginx errors

→ Incident
```

---

## 17. Incident Lifecycle

Har incident ka lifecycle:

```
DETECTED
   ↓
TRIAGED
   ↓
INVESTIGATING
   ↓
MITIGATED
   ↓
RESOLVED
   ↓
CLOSED
```

Agar false alarm ho:

```
DETECTED
   ↓
FALSE POSITIVE
```

---

## 18. Incident IDs

Har incident unique ID:

```
INC-000001
INC-000002
INC-000003
```

CLI:

```
sentinel incidents
```

---

## 19. Incident Details

```
sentinel diagnose INC-000001
```

Output:

```
INCIDENT INC-000001
────────────────────────────

Severity       HIGH
Status         INVESTIGATING
Started        14:32
Duration       08m

SYMPTOMS
CPU           96%
HTTP latency  2.8s
502 errors    43

PROBABLE CAUSE
High CPU utilization by
python-worker

CONFIDENCE
82%

EVIDENCE
• CPU crossed 90%
• python-worker consumed 81%
• latency increased afterward
• nginx timeout errors detected
```

---

## 20. Incident Correlation Engine

Ye project ka core advanced feature hoga.

Different signals:

- Metrics
- Logs
- Processes
- Services
- Network
- Events

ko timeline me correlate karega.

Example:

```
14:29 Deployment/event
       ↓
14:30 CPU ↑
       ↓
14:31 Memory ↑
       ↓
14:31 Latency ↑
       ↓
14:32 HTTP 502 ↑
       ↓
14:32 Incident
```

System automatically related events ko same incident window me group karega.

---

## 21. Root Cause Analysis

RCA output me:

- Probable Cause
- Supporting Evidence
- Contributing Factors
- Confidence
- Alternative Possibilities

Example:

```
PROBABLE CAUSE
Application process overload

CONFIDENCE
82%

CONTRIBUTING FACTOR
High memory pressure

ALTERNATIVE
Upstream dependency degradation
```

> Isse system overconfident conclusions nahi dega.

---

## 22. Incident Scoring

Scoring model:

| Signal | Score |
|--------|-------|
| CPU anomaly | +20 |
| Memory anomaly | +15 |
| Disk critical | +20 |
| Service down | +30 |
| HTTP errors | +25 |
| Log error spike | +15 |

Final score:

| Score | Severity |
|-------|----------|
| 0–20 | INFO |
| 21–40 | LOW |
| 41–60 | MEDIUM |
| 61–80 | HIGH |
| 81–100 | CRITICAL |

Weights configuration se change ho sakenge.

---

## 23. Alert Deduplication

Suppose CPU 95% par 50 readings aayi.

System:

- ❌ 50 incidents create nahi karega.

Instead:

```
INC-000123

Repeated CPU anomaly
Occurrences: 50
Duration: 8m
```

This prevents alert flooding.

---

## 24. Incident Suppression

Maintenance mode:

```
sentinel maintenance start
```

During maintenance expected alerts suppress kiye ja sakte hain.

```
sentinel maintenance stop
```

---

## 25. Recovery Detection

System sirf problem detect nahi karega — recovery bhi detect karega.

Example:

```
14:32 CPU 96%
14:35 CPU 93%
14:38 CPU 64%
14:40 CPU 42%
```

Output:

```
INC-000123
Status: RESOLVED ✓

Recovery detected after 8m 12s.
```

---

## 26. Incident Timeline

```
sentinel timeline INC-000123
```

Output:

```
14:29:10  Process started
14:30:12  CPU anomaly
14:31:04  HTTP latency ↑
14:31:20  Error spike
14:32:01  Incident created
14:35:20  CPU normalized
14:37:42  Service healthy
```

---

## 27. AI Assistant

AI optional module:

```
sentinel ai diagnose INC-000123
```

AI ko raw machine access nahi milega — it receives sanitized structured context.

AI tasks:

- summarize incident
- explain probable cause
- explain evidence
- suggest investigation steps
- generate postmortem
- answer questions about incident history

---

## 28. Natural Language CLI

Future advanced feature:

```
sentinel ask "Why did my server become slow at 2:30?"
```

System:

```
Analyzing telemetry...

Likely reason:
CPU utilization increased from 38% to 94%.

Supporting evidence:
python-worker consumed ~81% CPU.

Related event:
A process restart occurred 2 minutes earlier.
```

> AI response must be based on actual stored evidence.

---

## 29. Incident Simulator

Kyuki tumhare paas abhi cloud account nahi hai, simulator mandatory feature rakhenge.

Commands:

```
sentinel simulate cpu-spike
sentinel simulate memory-pressure
sentinel simulate disk-pressure
sentinel simulate service-down
sentinel simulate network-latency
sentinel simulate http-errors
```

Simulator ideally real system ko damage nahi karega — it will generate synthetic telemetry/events.

Example:

```
sentinel simulate cpu-spike --duration 60
```

Then Sentinel should detect:

```
🚨 INCIDENT DETECTED
INC-000021
CPU anomaly
Severity: HIGH
```

---

## 30. Demo Mode

One command:

```
sentinel demo
```

It runs a complete controlled scenario:

```
Normal
 ↓
Anomaly
 ↓
Incident
 ↓
Investigation
 ↓
Recovery
 ↓
Report
```

> Portfolio demo ke liye extremely useful.

---

## 31. Reports

```
sentinel report INC-000021
```

Generate:

- Incident Summary
- Impact
- Timeline
- Metrics
- Logs
- Probable Cause
- Evidence
- Resolution
- Recommendations

Formats:

```
--format json
--format markdown
--format txt
```

Future:

```
--format pdf
```

---

## 32. Historical Analytics

```
sentinel analytics
```

Show:

- incident count
- severity distribution
- most frequent incident type
- average resolution time
- most common error
- uptime
- resource trends

Example:

```
INCIDENT ANALYTICS

Total Incidents       24
Critical               1
High                   5
Medium                11
Low                    7

Avg Resolution        8m 21s

Most Common:
CPU anomalies
```

---

## 33. Health Score

System overall score:

```
SYSTEM HEALTH

████████████████░░░░ 82/100

CPU              ✓
Memory           ✓
Disk             ⚠
Network          ✓
Services         ✓
Recent Incidents ⚠
```

Health score explainable hona chahiye — user ko sirf 82 nahi, 82 kyun hai bhi dikhna chahiye.

---

## 34. Configuration System

Config:

```
~/.config/cloudops-sentinel/config.yaml
```

Possible settings:

```yaml
monitoring:
  interval: 5

thresholds:
  cpu_warning: 70
  cpu_critical: 90

storage:
  retention_days: 30

alerts:
  enabled: true

ai:
  enabled: false
```

---

## 35. Data Retention

Local machine par unlimited data store nahi karenge.

Default: **30 days**

User:

```
sentinel retention set 60
```

Old telemetry automatically purge ho sakta hai.

---

## 36. Database

**V1: SQLite**

Tables:

- hosts
- metrics
- logs
- events
- services
- incidents
- incident_events
- rules
- reports

Later: PostgreSQL for multi-server/cloud version.

---

## 37. Multi-Host Architecture

Abhi single machine. Future:

```
Server A ─┐
Server B ─┼→ Sentinel Backend
Server C ─┘
```

CLI:

```
sentinel hosts
HOST             STATUS
ubuntu-local     HEALTHY
server-01        HIGH
server-02        HEALTHY
```

---

## 38. Plugin Architecture

Future me monitoring modules plugins ki tarah add honge:

```
plugins/
├── linux
├── docker
├── nginx
├── postgres
├── redis
└── cloud
```

Example:

```
sentinel plugin list
```

> This avoids making the core code monolithic.

---

## 39. Docker Monitoring

Future feature:

```
sentinel docker
```

Show:

```
CONTAINER       STATUS     CPU
nginx           RUNNING    4%
api             RUNNING    31%
postgres        RUNNING    12%
```

Detect:

- container stopped
- restart loop
- high CPU
- high memory

---

## 40. HTTP/Application Monitoring

Later:

```
sentinel endpoint check
```

Monitor:

```
https://example.com
```

Read-only health check:

- response time
- status code
- availability
- TLS expiry warning later

---

## 41. Security Architecture

Very important:

- **No hard-coded secrets** — use environment variables.
- **No automatic destructive actions** — AI cannot execute `rm`, `kill`, `shutdown` without explicit controlled mechanisms — and V1 won't have autonomous remediation.
- **Read-only by default** — monitoring agent should collect information, not modify system state.

---

## 42. Performance Requirements

Sentinel itself shouldn't become the problem.

Target:

- low CPU overhead
- low memory usage
- configurable collection interval
- asynchronous collection where appropriate
- bounded log processing
- database retention

Example:

> Monitoring agent should normally consume only a small fraction of system resources.

Exact benchmark later testing se decide hoga, arbitrary hard limit initially nahi rakhenge.

---

## 43. Reliability

If Sentinel crashes — system continues normally. Monitoring failure must not crash the monitored server.

On restart:

```
Sentinel restarting...
Loading configuration...
Recovering database...
Monitoring resumed.
```

---

## 44. Testing Strategy

**Unit tests** — test:

- CPU parser
- memory calculation
- severity calculation
- incident scoring
- log parser

**Integration tests**:

```
metric
 ↓
detection
 ↓
incident
```

**Simulation tests**:

```
simulate cpu-spike
Expected:
HIGH incident

Result:
PASS
```

**Regression tests** — new feature old detection ko break na kare.

---

## 45. Observability of Sentinel itself

Important missing feature in many monitoring projects — Sentinel ko khud monitor karna hoga.

```
Sentinel Agent Health

Collector status     ✓
Database             ✓
Detection engine     ✓
Storage              ✓
AI module            OFF
```

> Otherwise monitoring system itself fail ho gaya to tumhe pata nahi chalega.

---

## 46. Logging

Sentinel ke apne logs:

```
~/.local/share/cloudops-sentinel/logs/
```

Levels:

- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

---

## 47. JSON Output

CLI human-readable output ke saath machine-readable output bhi dega.

```
sentinel status --json
```

Output:

```json
{
  "cpu": 42,
  "memory": 61,
  "disk": 73,
  "health": 82
}
```

> Ye future automation/API integration ke liye important hai.

---

## 48. Exit Codes

DevOps-friendly behavior:

```
sentinel health
```

Exit codes:

- `0` = healthy
- `1` = warning
- `2` = critical

Isse scripts aur CI/CD pipelines Sentinel ko consume kar sakenge.

---

## 49. Documentation

GitHub README me:

- What is CloudOps Sentinel?
- Why does it exist?
- Architecture
- Installation
- CLI commands
- Configuration
- Detection engine
- Incident lifecycle
- AI
- Simulator
- Testing
- Roadmap
- Screenshots/GIF

Plus:

```
docs/
├── architecture.md
├── detection.md
├── incidents.md
├── configuration.md
├── development.md
└── security.md
```

---

## 50. Final Architecture

```
                 CLOUDOPS SENTINEL
                       │
                ┌──────▼──────┐
                │     CLI     │
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │ Core Engine │
                └──────┬──────┘
                       │
       ┌───────────────┼────────────────┐
       │               │                │
   Collectors       Storage          Config
       │               │
       ├──── Metrics   │
       ├──── Logs      │
       ├──── Events    │
       └──── Services  │
                       │
                ┌──────▼──────┐
                │  Detection  │
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │ Correlation │
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │  Incidents  │
                └──────┬──────┘
                       │
              ┌────────┴────────┐
              │                 │
        RCA / Analysis      AI Assistant
              │                 │
              └────────┬────────┘
                       │
                ┌──────▼──────┐
                │   Reports   │
                └─────────────┘
```

**Future:** Web UI / Docker / Cloud / Multi-host

---

## 🛣️ Actual Build Plan

Don't try to build this entire PRD at once.

| Version | Scope |
|---------|-------|
| **V0.1** | Foundation — Python project + CLI + config + logging |
| **V0.2** | Monitoring — CPU/RAM/Disk/Network |
| **V0.3** | Linux — Processes + services + system logs |
| **V0.4** | Storage — SQLite + historical metrics |
| **V0.5** | Detection — Threshold + duration + anomaly basics |
| **V0.6** | Incidents — Severity + scoring + lifecycle + deduplication |
| **V0.7** | Correlation — Metrics + logs + events + timeline |
| **V0.8** | Diagnosis — RCA + evidence + confidence |
| **V0.9** | Simulator — Controlled incidents + demo mode |
| **V1.0** | Stable CLI — Testing + documentation + JSON output + reports |
| **V1.1** | AI — AI explanation + natural-language investigation |
| **V1.2** | Docker — Container monitoring + Docker deployment |
| **V2.0** | Web UI — Dashboard |
| **V3.0** | Cloud — Cloud VM + multi-host + cloud adapters |
| **V4.0** | Advanced Observability — OpenTelemetry + traces + more sophisticated anomaly detection |

---

## 🎯 V1 ka definition of "DONE"

Tumhara first serious release tab complete maana jayega jab ye command:

```
sentinel demo
```

run karke system:

```
Normal system
     ↓
Simulated anomaly
     ↓
Detection
     ↓
Incident creation
     ↓
Severity
     ↓
Evidence collection
     ↓
Probable diagnosis
     ↓
Recovery detection
     ↓
Incident report
```

end-to-end automatically demonstrate kar sake.