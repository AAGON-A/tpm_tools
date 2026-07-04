"""
generate_mock_data.py

Creates a SQLite database (program_health.db) with realistic mock data
across 3 teams, 6 sprints, and ~300 tickets, including intentional
patterns a TPM would want to catch: a team with rising blocked tickets,
a bug spike, and declining velocity in one sprint.

Usage:
    python generate_mock_data.py
"""

import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "program_health.db"
random.seed(42)

TEAMS = ["Checkout", "Notifications", "Identity"]
SPRINT_LENGTH_DAYS = 14
NUM_SPRINTS = 6
START_DATE = datetime(2025, 10, 1)

PRIORITIES = ["P0", "P1", "P2", "P3"]
PRIORITY_WEIGHTS = [0.05, 0.20, 0.45, 0.30]


def build_schema(conn):
    with open("../sql/schema.sql", "r") as f:
        conn.executescript(f.read())


def seed_teams(conn):
    cur = conn.cursor()
    for i, name in enumerate(TEAMS, start=1):
        cur.execute("INSERT INTO teams (team_id, team_name) VALUES (?, ?)", (i, name))
    conn.commit()


def seed_sprints(conn):
    cur = conn.cursor()
    sprint_id = 1
    sprints = []
    for team_id in range(1, len(TEAMS) + 1):
        current_start = START_DATE
        for s in range(1, NUM_SPRINTS + 1):
            end = current_start + timedelta(days=SPRINT_LENGTH_DAYS - 1)
            cur.execute(
                "INSERT INTO sprints (sprint_id, team_id, sprint_name, start_date, end_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (sprint_id, team_id, f"Sprint {s}", current_start.date().isoformat(), end.date().isoformat()),
            )
            sprints.append((sprint_id, team_id, s, current_start, end))
            sprint_id += 1
            current_start = end + timedelta(days=1)
    conn.commit()
    return sprints


def seed_tickets(conn, sprints):
    cur = conn.cursor()
    ticket_id = 1

    for sprint_id, team_id, sprint_num, start, end in sprints:
        # Base ticket volume per sprint
        num_tickets = random.randint(12, 20)

        # Injected story patterns for the dashboard to surface:
        # - Notifications team (team_id=2) has a bug spike in sprint 4
        # - Identity team (team_id=3) has rising blocked tickets from sprint 3 onward
        bug_spike = team_id == 2 and sprint_num == 4
        rising_blockers = team_id == 3 and sprint_num >= 3

        for _ in range(num_tickets):
            if bug_spike:
                ticket_type = random.choices(
                    ["bug", "feature", "chore"], weights=[0.55, 0.30, 0.15]
                )[0]
            else:
                ticket_type = random.choices(
                    ["feature", "bug", "chore"], weights=[0.55, 0.30, 0.15]
                )[0]

            story_points = random.choice([1, 2, 3, 5, 8])
            priority = random.choices(PRIORITIES, weights=PRIORITY_WEIGHTS)[0]
            created_at = start + timedelta(days=random.randint(0, 3))

            if rising_blockers:
                status_weights = [0.10, 0.20, 0.35, 0.35]  # more blocked/in_progress
            else:
                status_weights = [0.10, 0.15, 0.10, 0.65]  # mostly done

            status = random.choices(
                ["todo", "in_progress", "blocked", "done"], weights=status_weights
            )[0]

            resolved_at = None
            blocked_reason = None
            if status == "done":
                resolved_at = (created_at + timedelta(days=random.randint(1, 12))).date().isoformat()
            if status == "blocked":
                blocked_reason = random.choice(
                    [
                        "waiting on Identity API contract",
                        "waiting on design review",
                        "blocked by third-party vendor",
                        "waiting on security sign-off",
                        "dependency on Checkout release",
                    ]
                )

            title = f"{ticket_type.title()}-{ticket_id}: {random.choice(['update flow', 'fix regression', 'add validation', 'refactor module', 'improve latency', 'add logging'])}"

            cur.execute(
                """INSERT INTO tickets
                (ticket_id, team_id, sprint_id, title, ticket_type, story_points,
                 status, priority, created_at, resolved_at, blocked_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    ticket_id,
                    team_id,
                    sprint_id,
                    title,
                    ticket_type,
                    story_points,
                    status,
                    priority,
                    created_at.date().isoformat(),
                    resolved_at,
                    blocked_reason,
                ),
            )
            ticket_id += 1

    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    build_schema(conn)
    seed_teams(conn)
    sprints = seed_sprints(conn)
    seed_tickets(conn, sprints)
    conn.close()
    print(f"Created {DB_PATH} with {len(TEAMS)} teams, {len(sprints)} sprints, and mock tickets.")


if __name__ == "__main__":
    main()
