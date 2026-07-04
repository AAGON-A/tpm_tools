-- Cross-Team Dependency Tracker: Schema
-- Models epics across teams and explicit "blocks/blocked-by" relationships between them.
-- This is the normalized version of what a TPM tracks manually in a spreadsheet.

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY,
    team_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS epics (
    epic_id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('not_started', 'in_progress', 'blocked', 'done')),
    target_quarter TEXT NOT NULL,
    owner TEXT NOT NULL,
    source_system TEXT NOT NULL,  -- e.g. 'github', 'jira' -- shows data came from multiple APIs
    external_id TEXT NOT NULL,    -- the ID in that external system
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

-- A dependency means: epic_id is BLOCKED BY depends_on_epic_id
CREATE TABLE IF NOT EXISTS dependencies (
    dependency_id INTEGER PRIMARY KEY,
    epic_id INTEGER NOT NULL,
    depends_on_epic_id INTEGER NOT NULL,
    criticality TEXT NOT NULL CHECK (criticality IN ('hard_blocker', 'soft_dependency')),
    notes TEXT,
    FOREIGN KEY (epic_id) REFERENCES epics(epic_id),
    FOREIGN KEY (depends_on_epic_id) REFERENCES epics(epic_id)
);
