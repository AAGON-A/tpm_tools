-- Program Health Dashboard: Analysis Queries
-- These are the queries the Python report generator runs.
-- Included standalone so reviewers can read/run pure SQL without Python.

-- 1. Sprint velocity per team (completed story points per sprint)
SELECT
    t.team_name,
    s.sprint_name,
    s.start_date,
    SUM(CASE WHEN tk.status = 'done' THEN tk.story_points ELSE 0 END) AS completed_points,
    SUM(tk.story_points) AS committed_points,
    ROUND(
        100.0 * SUM(CASE WHEN tk.status = 'done' THEN tk.story_points ELSE 0 END)
        / NULLIF(SUM(tk.story_points), 0), 1
    ) AS completion_rate_pct
FROM tickets tk
JOIN sprints s ON tk.sprint_id = s.sprint_id
JOIN teams t ON tk.team_id = t.team_id
GROUP BY t.team_name, s.sprint_id
ORDER BY t.team_name, s.start_date;

-- 2. Blocked ticket trend per team per sprint (surfaces rising-blocker teams)
SELECT
    t.team_name,
    s.sprint_name,
    s.start_date,
    COUNT(*) AS blocked_count,
    GROUP_CONCAT(DISTINCT tk.blocked_reason) AS blocked_reasons
FROM tickets tk
JOIN sprints s ON tk.sprint_id = s.sprint_id
JOIN teams t ON tk.team_id = t.team_id
WHERE tk.status = 'blocked'
GROUP BY t.team_name, s.sprint_id
ORDER BY t.team_name, s.start_date;

-- 3. Bug rate per team per sprint (surfaces quality regressions/spikes)
SELECT
    t.team_name,
    s.sprint_name,
    s.start_date,
    SUM(CASE WHEN tk.ticket_type = 'bug' THEN 1 ELSE 0 END) AS bug_count,
    COUNT(*) AS total_tickets,
    ROUND(100.0 * SUM(CASE WHEN tk.ticket_type = 'bug' THEN 1 ELSE 0 END) / COUNT(*), 1) AS bug_rate_pct
FROM tickets tk
JOIN sprints s ON tk.sprint_id = s.sprint_id
JOIN teams t ON tk.team_id = t.team_id
GROUP BY t.team_name, s.sprint_id
ORDER BY t.team_name, s.start_date;

-- 4. Open P0/P1 tickets right now (cross-team risk snapshot)
SELECT
    t.team_name,
    tk.priority,
    tk.title,
    tk.status,
    tk.created_at,
    tk.blocked_reason
FROM tickets tk
JOIN teams t ON tk.team_id = t.team_id
WHERE tk.priority IN ('P0', 'P1')
  AND tk.status != 'done'
ORDER BY tk.priority, t.team_name;

-- 5. Average cycle time (days from created to resolved) per team
SELECT
    t.team_name,
    ROUND(AVG(julianday(tk.resolved_at) - julianday(tk.created_at)), 1) AS avg_cycle_time_days,
    COUNT(*) AS tickets_resolved
FROM tickets tk
JOIN teams t ON tk.team_id = t.team_id
WHERE tk.status = 'done'
GROUP BY t.team_name
ORDER BY avg_cycle_time_days DESC;
