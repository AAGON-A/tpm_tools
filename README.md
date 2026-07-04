# TPM Portfolio

A small set of artifacts demonstrating the technical range expected of a Technical Program Manager: data-driven program tracking, and technical architecture judgment — without pretending to be a software engineering portfolio.

## What a TPM actually needs to prove technically

Not "can you write production code." Rather:
- Can you use **SQL** to answer real questions about program health instead of asking an analyst to do it?
- Can you use **Python** to turn raw data into something a VP will actually read?
- Can you understand **API/system architecture** well enough to drive a technical decision to closure and write it down clearly?

This repo has one project for each of the first two, combined, and one for the third.

## Skills Demonstrated

| Skill | Where it shows up |
|---|---|
| **SQL** | Schema design, joins, aggregates, trend queries — [01](01-program-health-dashboard/sql/), [02](02-dependency-tracker/sql/) |
| **Python (data/analysis)** | pandas transforms, automated anomaly detection, matplotlib charting — [01](01-program-health-dashboard/scripts/) |
| **API integration** | Live GitHub REST API call with error handling + cache fallback; normalizing a second, differently-shaped (simulated Jira) API into one schema — [02](02-dependency-tracker/scripts/) |
| **Graph / algorithmic thinking** | Dependency graph construction, cycle detection, blast-radius ranking with networkx — [02](02-dependency-tracker/scripts/analyze_dependencies.py) |
| **API/systems architecture** | Event-driven vs. sync tradeoffs, service ownership boundaries, rate-limiting design — [05](05-api-architecture-adrs/adrs/) |
| **Technical writing** | ADRs with honest, non-cherry-picked consequences; auto-generated exec-ready status reports — [01](01-program-health-dashboard/sample_output/weekly_status_report.md), [05](05-api-architecture-adrs/adrs/) |
| **API specification** | OpenAPI 3.0 spec, validated — [05](05-api-architecture-adrs/openapi/notification-service.yaml) |

## Projects

### [01 — Program Health Dashboard](01-program-health-dashboard/)
**SQL + Python.** Generates a mock multi-team sprint database, runs analysis queries (velocity, blockers, bug rate, cycle time), and auto-generates a weekly status report with anomalies flagged — the artifact a TPM would actually send to leadership.

### [02 — Cross-Team Dependency Tracker](02-dependency-tracker/)
**API integration + SQL + Python (networkx).** Pulls real epics from the GitHub Issues API and simulated epics from a Jira-shaped API, normalizes both into one schema, then builds a dependency graph that detects circular blockers and ranks epics by blast radius. Solves the actual TPM problem of cross-team dependencies living in nobody's system of record.

### [05 — API Architecture Decision Records](05-api-architecture-adrs/)
**API Architecture + technical writing.** A realistic scenario (three teams need a shared notification system) worked through as three ADRs, an OpenAPI spec, and a system diagram — showing the ability to reason about tradeoffs (event-driven vs. sync, shared vs. per-team ownership, rate limiting) and document them for both engineering and non-engineering audiences.

## How to use this if you're evaluating me

Start with the ADRs (`05-api-architecture-adrs/adrs/`) if you want to see technical judgment and writing. Start with `01-program-health-dashboard/sample_output/weekly_status_report.md` or `02-dependency-tracker/sample_output/dependency_risk_report.md` if you want to see the data side.
