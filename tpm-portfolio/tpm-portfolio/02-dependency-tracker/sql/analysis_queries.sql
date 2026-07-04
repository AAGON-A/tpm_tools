-- Cross-Team Dependency Tracker: Analysis Queries

-- 1. All cross-team dependencies (the core view a TPM needs)
SELECT
    bt.team_name AS blocked_team,
    be.title AS blocked_epic,
    be.status AS blocked_epic_status,
    dt.team_name AS depends_on_team,
    de.title AS depends_on_epic,
    de.status AS depends_on_epic_status,
    d.criticality,
    d.notes
FROM dependencies d
JOIN epics be ON d.epic_id = be.epic_id
JOIN epics de ON d.depends_on_epic_id = de.epic_id
JOIN teams bt ON be.team_id = bt.team_id
JOIN teams dt ON de.team_id = dt.team_id
WHERE bt.team_id != dt.team_id
ORDER BY d.criticality, bt.team_name;

-- 2. Hard blockers where the upstream (depended-on) epic isn't done yet
-- (i.e. real, active risk to a downstream team's timeline)
SELECT
    bt.team_name AS blocked_team,
    be.title AS blocked_epic,
    dt.team_name AS depends_on_team,
    de.title AS depends_on_epic,
    de.status AS depends_on_epic_status
FROM dependencies d
JOIN epics be ON d.epic_id = be.epic_id
JOIN epics de ON d.depends_on_epic_id = de.epic_id
JOIN teams bt ON be.team_id = bt.team_id
JOIN teams dt ON de.team_id = dt.team_id
WHERE d.criticality = 'hard_blocker'
  AND de.status != 'done'
ORDER BY bt.team_name;

-- 3. Which epics have the most downstream dependents (highest blast radius if delayed)
SELECT
    t.team_name,
    e.title,
    e.status,
    COUNT(d.dependency_id) AS num_epics_blocked_by_this
FROM epics e
LEFT JOIN dependencies d ON e.epic_id = d.depends_on_epic_id
JOIN teams t ON e.team_id = t.team_id
GROUP BY e.epic_id
HAVING num_epics_blocked_by_this > 0
ORDER BY num_epics_blocked_by_this DESC;

-- 4. Dependency count per team (who is most entangled with other teams)
SELECT
    t.team_name,
    COUNT(DISTINCT d.dependency_id) AS outgoing_dependencies
FROM epics e
JOIN teams t ON e.team_id = t.team_id
LEFT JOIN dependencies d ON e.epic_id = d.epic_id
GROUP BY t.team_name
ORDER BY outgoing_dependencies DESC;
