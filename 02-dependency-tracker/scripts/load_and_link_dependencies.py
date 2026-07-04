"""
load_and_link_dependencies.py

Loads the normalized epics (from GitHub + simulated Jira) into SQLite, then
adds the cross-team dependency edges. Those edges are the actual output of
TPM judgment — cross-team blocking relationships aren't in either team's
own tool, which is exactly why this kind of tracker has to exist.

Usage:
    python load_and_link_dependencies.py
"""

import json
import sqlite3

DB_PATH = "dependency_tracker.db"
GITHUB_EPICS_PATH = "../sample_output/platform_epics_from_github.json"
JIRA_EPICS_PATH = "../sample_output/growth_and_data_epics_from_jira.json"

# Manually curated cross-team dependencies, the kind a TPM gathers by talking to
# each team's lead. Referenced by (team_name, epic_title_substring) so this stays
# readable even though titles for the GitHub source vary run to run (live data).
# For the Jira-simulated teams (Growth, Data) titles are fixed, so those pairings
# are stable and are the ones the dependency graph analysis focuses on.
DEPENDENCY_RULES = [
    # (blocked_team, blocked_title_substr, depends_on_team, depends_on_title_substr, criticality, notes)
    ("Growth", "self-serve upgrade flow", "Data", "self-serve metrics layer",
     "hard_blocker", "Upgrade flow needs usage-based pricing signals from the metrics layer"),
    ("Growth", "Sunset legacy trial-extension tool", "Data", "Deprecate legacy analytics pipeline",
     "soft_dependency", "Old tool's usage is tracked in the legacy pipeline; want clean cutover"),
    ("Growth", "pricing experimentation framework", "Data", "real-time revenue dashboard",
     "hard_blocker", "Experimentation framework needs real-time revenue data to evaluate tests"),
    ("Data", "Backfill historical activation events", "Growth", "Instrument activation funnel events",
     "hard_blocker", "Can't backfill until the new event instrumentation ships and is validated"),
    ("Data", "Build self-serve metrics layer for product teams", "Data", "Stand up unified event schema v2",
     "hard_blocker", "Metrics layer must be built on the new schema, not the old one"),
]


def build_schema(conn):
    with open("../sql/schema.sql", "r") as f:
        conn.executescript(f.read())


def load_epics(conn):
    cur = conn.cursor()
    team_ids = {}
    epic_ids = {}  # (team_name, title) -> epic_id
    next_team_id = 1
    next_epic_id = 1

    for path in [GITHUB_EPICS_PATH, JIRA_EPICS_PATH]:
        with open(path, "r") as f:
            payload = json.load(f)

        for epic in payload["epics"]:
            team_name = epic["team_name"]
            if team_name not in team_ids:
                team_ids[team_name] = next_team_id
                cur.execute("INSERT INTO teams (team_id, team_name) VALUES (?, ?)", (next_team_id, team_name))
                next_team_id += 1

            cur.execute(
                """INSERT INTO epics
                (epic_id, team_id, title, status, target_quarter, owner, source_system, external_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    next_epic_id,
                    team_ids[team_name],
                    epic["title"],
                    epic["status"],
                    "2026-Q2",
                    epic["owner"],
                    epic["source_system"],
                    epic["external_id"],
                ),
            )
            epic_ids[(team_name, epic["title"])] = next_epic_id
            next_epic_id += 1

    conn.commit()
    return epic_ids


def find_epic_id(epic_ids, team_name, title_substr):
    for (team, title), epic_id in epic_ids.items():
        if team == team_name and title_substr.lower() in title.lower():
            return epic_id
    return None


def load_dependencies(conn, epic_ids):
    cur = conn.cursor()
    dep_id = 1
    added = 0
    skipped = 0

    for blocked_team, blocked_substr, dep_team, dep_substr, criticality, notes in DEPENDENCY_RULES:
        blocked_id = find_epic_id(epic_ids, blocked_team, blocked_substr)
        dep_on_id = find_epic_id(epic_ids, dep_team, dep_substr)

        if blocked_id is None or dep_on_id is None:
            skipped += 1
            continue

        cur.execute(
            """INSERT INTO dependencies
            (dependency_id, epic_id, depends_on_epic_id, criticality, notes)
            VALUES (?, ?, ?, ?, ?)""",
            (dep_id, blocked_id, dep_on_id, criticality, notes),
        )
        dep_id += 1
        added += 1

    conn.commit()
    print(f"Loaded {added} dependency edges ({skipped} skipped — epic not found).")


def main():
    conn = sqlite3.connect(DB_PATH)
    build_schema(conn)
    epic_ids = load_epics(conn)
    print(f"Loaded {len(epic_ids)} epics across teams.")
    load_dependencies(conn, epic_ids)
    conn.close()


if __name__ == "__main__":
    main()
