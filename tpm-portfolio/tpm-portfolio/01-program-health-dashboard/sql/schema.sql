-- Program Health Dashboard: Schema
-- Models a simplified multi-team sprint tracker (Jira/Linear-like)

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sprints (
    sprint_id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL,
    sprint_name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL,
    sprint_id INTEGER,
    title TEXT NOT NULL,
    ticket_type TEXT NOT NULL CHECK (ticket_type IN ('feature', 'bug', 'chore')),
    story_points INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('todo', 'in_progress', 'blocked', 'done')),
    priority TEXT NOT NULL CHECK (priority IN ('P0', 'P1', 'P2', 'P3')),
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    blocked_reason TEXT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (sprint_id) REFERENCES sprints(sprint_id)
);
