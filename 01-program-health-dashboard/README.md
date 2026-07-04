# Program Health Dashboard

**A weekly status report a TPM would actually send — generated automatically from sprint data instead of copy-pasted into slides.**

## The problem

Every TPM spends hours every week pulling numbers from Jira/Linear, building charts, and writing a status update. It's repetitive, error-prone, and the insights (which team is slipping, which risk is growing) often get buried instead of surfaced.

## What this does

1. **`generate_mock_data.py`** creates a SQLite database modeling 3 teams across 6 sprints (~300 tickets), with a few realistic patterns baked in: a bug spike, a team with worsening blockers, and normal sprint noise.
2. **`analysis_queries.sql`** contains the five core SQL queries a TPM needs: velocity/completion rate, blocked-ticket trend, bug rate trend, open P0/P1 risk snapshot, and average cycle time.
3. **`generate_report.py`** runs those queries with pandas, renders trend charts with matplotlib, **automatically flags anomalies** (e.g., "completion rate dropped 35pts," "3 consecutive sprints of rising blockers"), and writes a ready-to-share `weekly_status_report.md`.

## Why this matters for a TPM role

This is the core loop of program management: **data → insight → communication**. The valuable part isn't the code — it's the automated anomaly-flagging logic, which mirrors how a TPM should triage: don't just report numbers, tell leadership what changed and why it matters.

## Sample output

See [`sample_output/weekly_status_report.md`](sample_output/weekly_status_report.md) for a full generated report, including:

![Velocity Trend](sample_output/velocity_trend.png)

## Run it yourself

```bash
cd scripts
pip install pandas matplotlib tabulate
python generate_mock_data.py     # creates program_health.db
python generate_report.py        # generates charts + markdown report in sample_output/
```

## Stack

- **SQL** (SQLite) — schema design, aggregate queries, trend analysis
- **Python** — pandas for transformation, matplotlib for visualization
- **Output** — versioned markdown report + PNG charts, ready to paste into Slack/Confluence

## Possible extensions

- Swap SQLite for a live Jira/Linear API connection
- Add Slack API integration to auto-post the weekly report to a channel
- Add a `--team` flag to generate single-team deep-dive reports
