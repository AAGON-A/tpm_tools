"""
generate_report.py

Reads program_health.db, runs the analysis queries, produces:
  - velocity_trend.png
  - blocked_tickets_trend.png
  - bug_rate_trend.png
  - weekly_status_report.md   <- the artifact a TPM would actually send out

Usage:
    python generate_report.py
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DB_PATH = "program_health.db"
OUTPUT_DIR = Path("../sample_output")
OUTPUT_DIR.mkdir(exist_ok=True)


def run_query(conn, query):
    return pd.read_sql_query(query, conn)


VELOCITY_QUERY = """
SELECT
    t.team_name,
    s.sprint_name,
    s.start_date,
    SUM(CASE WHEN tk.status = 'done' THEN tk.story_points ELSE 0 END) AS completed_points,
    SUM(tk.story_points) AS committed_points,
    ROUND(100.0 * SUM(CASE WHEN tk.status = 'done' THEN tk.story_points ELSE 0 END)
        / NULLIF(SUM(tk.story_points), 0), 1) AS completion_rate_pct
FROM tickets tk
JOIN sprints s ON tk.sprint_id = s.sprint_id
JOIN teams t ON tk.team_id = t.team_id
GROUP BY t.team_name, s.sprint_id
ORDER BY t.team_name, s.start_date;
"""

BLOCKED_QUERY = """
SELECT
    t.team_name,
    s.sprint_name,
    s.start_date,
    COUNT(*) AS blocked_count
FROM tickets tk
JOIN sprints s ON tk.sprint_id = s.sprint_id
JOIN teams t ON tk.team_id = t.team_id
WHERE tk.status = 'blocked'
GROUP BY t.team_name, s.sprint_id
ORDER BY t.team_name, s.start_date;
"""

BUG_RATE_QUERY = """
SELECT
    t.team_name,
    s.sprint_name,
    s.start_date,
    ROUND(100.0 * SUM(CASE WHEN tk.ticket_type = 'bug' THEN 1 ELSE 0 END) / COUNT(*), 1) AS bug_rate_pct
FROM tickets tk
JOIN sprints s ON tk.sprint_id = s.sprint_id
JOIN teams t ON tk.team_id = t.team_id
GROUP BY t.team_name, s.sprint_id
ORDER BY t.team_name, s.start_date;
"""

OPEN_RISK_QUERY = """
SELECT
    t.team_name,
    tk.priority,
    tk.title,
    tk.status,
    tk.blocked_reason
FROM tickets tk
JOIN teams t ON tk.team_id = t.team_id
WHERE tk.priority IN ('P0', 'P1')
  AND tk.status != 'done'
ORDER BY tk.priority, t.team_name;
"""

CYCLE_TIME_QUERY = """
SELECT
    t.team_name,
    ROUND(AVG(julianday(tk.resolved_at) - julianday(tk.created_at)), 1) AS avg_cycle_time_days,
    COUNT(*) AS tickets_resolved
FROM tickets tk
JOIN teams t ON tk.team_id = t.team_id
WHERE tk.status = 'done'
GROUP BY t.team_name
ORDER BY avg_cycle_time_days DESC;
"""


def plot_trend(df, value_col, title, ylabel, filename):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for team, group in df.groupby("team_name"):
        ax.plot(group["sprint_name"], group[value_col], marker="o", label=team)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Sprint")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.close(fig)


def flag_insights(velocity_df, blocked_df, bug_df):
    insights = []

    # Flag teams whose completion rate dropped >15pts sprint over sprint
    for team, group in velocity_df.groupby("team_name"):
        group = group.sort_values("start_date").reset_index(drop=True)
        for i in range(1, len(group)):
            drop = group.loc[i - 1, "completion_rate_pct"] - group.loc[i, "completion_rate_pct"]
            if drop and drop > 15:
                insights.append(
                    f"⚠️ **{team}** completion rate dropped {drop:.0f} pts "
                    f"({group.loc[i-1, 'sprint_name']} → {group.loc[i, 'sprint_name']})."
                )

    # Flag teams with rising blocked tickets for 2+ consecutive sprints
    for team, group in blocked_df.groupby("team_name"):
        group = group.sort_values("start_date").reset_index(drop=True)
        rising_streak = 0
        for i in range(1, len(group)):
            if group.loc[i, "blocked_count"] > group.loc[i - 1, "blocked_count"]:
                rising_streak += 1
            else:
                rising_streak = 0
            if rising_streak >= 2:
                insights.append(
                    f"🚧 **{team}** has had rising blocked-ticket counts for "
                    f"{rising_streak + 1} consecutive sprints — worth a dependency review."
                )
                break

    # Flag any sprint with bug rate > 40%
    spike = bug_df[bug_df["bug_rate_pct"] > 40]
    for _, row in spike.iterrows():
        insights.append(
            f"🐛 **{row['team_name']}** had a bug-rate spike of {row['bug_rate_pct']}% "
            f"in {row['sprint_name']} — likely worth a root-cause discussion."
        )

    return insights


def build_markdown_report(velocity_df, blocked_df, bug_df, open_risk_df, cycle_df, insights):
    lines = []
    lines.append("# Weekly Program Health Report\n")
    lines.append(f"_Generated from `{DB_PATH}` — data covers {velocity_df['start_date'].min()} "
                  f"to {velocity_df['start_date'].max()}._\n")

    lines.append("## 🔑 Key Insights\n")
    if insights:
        for i in insights:
            lines.append(f"- {i}")
    else:
        lines.append("- No major anomalies detected this period.")
    lines.append("")

    lines.append("## 📈 Velocity & Completion Rate\n")
    lines.append("![Velocity Trend](velocity_trend.png)\n")
    lines.append(velocity_df.pivot(index="sprint_name", columns="team_name", values="completion_rate_pct")
                 .to_markdown())
    lines.append("")

    lines.append("## 🚧 Blocked Tickets by Sprint\n")
    lines.append("![Blocked Trend](blocked_tickets_trend.png)\n")

    lines.append("## 🐛 Bug Rate by Sprint\n")
    lines.append("![Bug Rate Trend](bug_rate_trend.png)\n")

    lines.append("## ⏱️ Average Cycle Time (days, resolved tickets)\n")
    lines.append(cycle_df.to_markdown(index=False))
    lines.append("")

    lines.append("## 🔴 Open P0/P1 Tickets (Cross-Team Risk Snapshot)\n")
    if open_risk_df.empty:
        lines.append("_No open P0/P1 tickets. ✅_")
    else:
        lines.append(open_risk_df.to_markdown(index=False))
    lines.append("")

    return "\n".join(lines)


def main():
    conn = sqlite3.connect(DB_PATH)

    velocity_df = run_query(conn, VELOCITY_QUERY)
    blocked_df = run_query(conn, BLOCKED_QUERY)
    bug_df = run_query(conn, BUG_RATE_QUERY)
    open_risk_df = run_query(conn, OPEN_RISK_QUERY)
    open_risk_df["blocked_reason"] = open_risk_df["blocked_reason"].fillna("—")
    cycle_df = run_query(conn, CYCLE_TIME_QUERY)

    plot_trend(velocity_df, "completion_rate_pct", "Sprint Completion Rate by Team", "% Completed", "velocity_trend.png")
    plot_trend(blocked_df, "blocked_count", "Blocked Tickets by Sprint", "# Blocked", "blocked_tickets_trend.png")
    plot_trend(bug_df, "bug_rate_pct", "Bug Rate by Sprint", "% Bugs of Total Tickets", "bug_rate_trend.png")

    insights = flag_insights(velocity_df, blocked_df, bug_df)
    report_md = build_markdown_report(velocity_df, blocked_df, bug_df, open_risk_df, cycle_df, insights)

    report_path = OUTPUT_DIR / "weekly_status_report.md"
    report_path.write_text(report_md)

    conn.close()
    print(f"Report written to {report_path}")
    print(f"Charts written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
