# Cross-Team Dependency Tracker

**Pulls epics from two different real-world-shaped APIs (GitHub Issues + a simulated Jira feed), normalizes them into one schema, and surfaces cross-team blocking risk — including circular dependencies — that neither team's own tool would show them.**

## The problem

The most common program-level failure isn't that any one team executes badly — it's that Team A doesn't know they're blocked on Team B until two weeks before a deadline, because that dependency lived in someone's head or a stale spreadsheet. Worse: sometimes A is blocked on B, and B (unknowingly) is blocked on A.

## What this does

1. **`fetch_github_epics.py`** pulls real, live epics from the GitHub Issues API for one team (Platform) — with a graceful fallback to a cached sample if the API is rate-limited, which it will be on a shared/unauthenticated connection. This mirrors a real integration concern: one flaky API shouldn't take down the whole tool.
2. **`generate_jira_epics.py`** simulates a Jira-shaped API response for two other teams (Growth, Data), since not every team lives in the same tool. This is the actual point of the exercise — a dependency tracker's job is to normalize across tools teams didn't agree on.
3. **`load_and_link_dependencies.py`** loads both normalized sources into a shared SQLite schema and adds the cross-team dependency edges — the relationships a TPM gathers by actually talking to team leads, since no API exposes them.
4. **`analyze_dependencies.py`** builds a directed graph with `networkx`, detects **circular dependencies** (A blocked on B blocked on A — a real planning failure mode), ranks epics by **blast radius** (how many other epics depend on them), and generates a visual graph plus a markdown risk report.

## Why this matters for a TPM role

This demonstrates the two things a dependency tracker actually needs to be useful: **normalizing messy, multi-tool reality into one model**, and **surfacing the specific failure mode that manual tracking misses** — a chain of dependencies with no visible cycle until you actually build the graph. The blast-radius ranking is the same logic a TPM uses to decide which slipping epic deserves an escalation and which doesn't.

## Sample output

See [`sample_output/dependency_risk_report.md`](sample_output/dependency_risk_report.md) for the full generated report.

![Dependency Graph](sample_output/dependency_graph.png)

## Run it yourself

```bash
cd scripts
pip install pandas matplotlib networkx tabulate
python fetch_github_epics.py                 # pulls real GitHub issues (falls back to cache if rate-limited)
python generate_jira_epics.py                # simulates Jira API responses for 2 more teams
python load_and_link_dependencies.py         # loads everything into SQLite + adds dependency edges
python analyze_dependencies.py               # builds graph, detects cycles, generates report + PNG
```

Optional: set a `GITHUB_TOKEN` environment variable before running `fetch_github_epics.py` for a higher (5,000/hr) rate limit instead of the unauthenticated 60/hr.

## Stack

- **API integration** — real GitHub REST API call with error handling and cache fallback; simulated Jira REST API shape for a second source
- **SQL** (SQLite) — normalized schema across two source systems, cross-team join queries
- **Python** — `networkx` for graph construction and cycle detection, `matplotlib` for the dependency visualization, `pandas` for the tabular views

## Possible extensions

- Add a real Jira integration alongside the GitHub one (swap the simulated response for a real `GET /rest/api/3/search` call)
- Add Slack alerting when a new hard blocker is added upstream of an epic that's already "in progress"
- Track dependency *age* (how long has this blocker existed) to flag dependencies that are stale, not just present
