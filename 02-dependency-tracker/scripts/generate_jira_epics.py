"""
generate_jira_epics.py

Simulates fetching epics from a Jira-style REST API for two teams (Growth,
Data) that don't live on GitHub. In a real environment this would call
Jira's REST API (e.g. GET /rest/api/3/search?jql=project=GROWTH); here it
generates a realistic-shaped payload so the rest of the pipeline (loading,
normalization, dependency graph) works identically regardless of source
system — which is the actual point: a dependency tracker has to normalize
across tools teams didn't agree on.

Usage:
    python generate_jira_epics.py
"""

import json
import random

random.seed(7)

TEAMS = {
    "Growth": [
        ("Launch referral program v2", "in_progress", "a-chen"),
        ("Migrate onboarding flow to new activation model", "in_progress", "s-ibrahim"),
        ("Add self-serve upgrade flow", "not_started", "a-chen"),
        ("Sunset legacy trial-extension tool", "blocked", "s-ibrahim"),
        ("Instrument activation funnel events", "done", "r-kowalski"),
        ("Build pricing experimentation framework", "not_started", "a-chen"),
    ],
    "Data": [
        ("Stand up unified event schema v2", "in_progress", "t-nakamura"),
        ("Backfill historical activation events", "blocked", "l-fontaine"),
        ("Deprecate legacy analytics pipeline", "not_started", "t-nakamura"),
        ("Ship real-time revenue dashboard", "in_progress", "l-fontaine"),
        ("Add data quality monitoring for event pipeline", "done", "t-nakamura"),
        ("Build self-serve metrics layer for product teams", "not_started", "l-fontaine"),
    ],
}


def fake_jira_response(team, epics):
    """Shape the output like a real Jira search API response."""
    issues = []
    for i, (title, status, owner) in enumerate(epics, start=1):
        jira_status_map = {
            "not_started": "To Do",
            "in_progress": "In Progress",
            "blocked": "Blocked",
            "done": "Done",
        }
        issues.append(
            {
                "key": f"{team[:2].upper()}-{100 + i}",
                "fields": {
                    "summary": title,
                    "status": {"name": jira_status_map[status]},
                    "assignee": {"displayName": owner},
                    "issuetype": {"name": "Epic"},
                },
            }
        )
    return {"issues": issues}


def normalize(jira_response, team_name):
    status_map = {"To Do": "not_started", "In Progress": "in_progress", "Blocked": "blocked", "Done": "done"}
    normalized = []
    for issue in jira_response["issues"]:
        fields = issue["fields"]
        normalized.append(
            {
                "title": fields["summary"],
                "status": status_map[fields["status"]["name"]],
                "owner": fields["assignee"]["displayName"],
                "source_system": "jira",
                "external_id": issue["key"],
                "url": f"https://example.atlassian.net/browse/{issue['key']}",
                "team_name": team_name,
            }
        )
    return normalized


def main():
    all_epics = []
    for team_name, epics in TEAMS.items():
        jira_response = fake_jira_response(team_name, epics)
        normalized = normalize(jira_response, team_name)
        all_epics.extend(normalized)
        print(f"Simulated Jira fetch for {team_name}: {len(normalized)} epics")

    out_path = "../sample_output/growth_and_data_epics_from_jira.json"
    with open(out_path, "w") as f:
        json.dump({"source": "jira_simulated", "epics": all_epics}, f, indent=2)

    print(f"Wrote {len(all_epics)} normalized epics to {out_path}")


if __name__ == "__main__":
    main()
