"""
analyze_dependencies.py

Builds a directed graph of cross-team epic dependencies using networkx,
detects circular dependencies (a real and common planning failure mode —
Team A blocked on Team B blocked on Team A), ranks epics by "blast radius"
(how many other epics depend on them), and renders both a visual graph and
a markdown risk report.

Usage:
    python analyze_dependencies.py
"""

import sqlite3
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path

DB_PATH = "dependency_tracker.db"
OUTPUT_DIR = Path("../sample_output")
OUTPUT_DIR.mkdir(exist_ok=True)

STATUS_COLORS = {
    "not_started": "#9aa0a6",
    "in_progress": "#4285f4",
    "blocked": "#ea4335",
    "done": "#34a853",
}


def load_data(conn):
    epics_df = pd.read_sql_query(
        """
        SELECT e.epic_id, e.title, e.status, e.owner, t.team_name
        FROM epics e JOIN teams t ON e.team_id = t.team_id
        """,
        conn,
    )
    deps_df = pd.read_sql_query(
        """
        SELECT d.epic_id, d.depends_on_epic_id, d.criticality, d.notes,
               be.title AS blocked_title, be.team_id AS blocked_team_id,
               de.title AS depends_on_title, de.team_id AS depends_on_team_id
        FROM dependencies d
        JOIN epics be ON d.epic_id = be.epic_id
        JOIN epics de ON d.depends_on_epic_id = de.epic_id
        """,
        conn,
    )
    return epics_df, deps_df


def build_graph(epics_df, deps_df):
    G = nx.DiGraph()
    for _, row in epics_df.iterrows():
        G.add_node(row["epic_id"], title=row["title"], status=row["status"], team=row["team_name"])
    for _, row in deps_df.iterrows():
        # Edge direction: depends_on -> blocked (i.e. "must finish before")
        G.add_edge(
            row["depends_on_epic_id"],
            row["epic_id"],
            criticality=row["criticality"],
            notes=row["notes"],
        )
    return G


def find_cycles(G):
    return list(nx.simple_cycles(G))


def rank_by_blast_radius(G, epics_df):
    epics_lookup = epics_df.set_index("epic_id")
    rows = []
    for node in G.nodes:
        downstream_count = len(list(nx.descendants(G, node)))
        if downstream_count > 0:
            rows.append(
                {
                    "epic": epics_lookup.loc[node, "title"],
                    "team": epics_lookup.loc[node, "team_name"],
                    "status": epics_lookup.loc[node, "status"],
                    "epics_downstream_if_delayed": downstream_count,
                }
            )
    return pd.DataFrame(rows).sort_values("epics_downstream_if_delayed", ascending=False)


def draw_graph(G, epics_df, filename="dependency_graph.png"):
    fig, ax = plt.subplots(figsize=(11, 8))
    pos = nx.spring_layout(G, seed=42, k=1.1)

    node_colors = [STATUS_COLORS.get(G.nodes[n]["status"], "#cccccc") for n in G.nodes]
    node_labels = {n: f"{G.nodes[n]['team']}:\n{G.nodes[n]['title'][:28]}" for n in G.nodes}

    hard_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("criticality") == "hard_blocker"]
    soft_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("criticality") != "hard_blocker"]

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1400, ax=ax, edgecolors="#333", linewidths=0.8)
    nx.draw_networkx_edges(G, pos, edgelist=hard_edges, edge_color="#ea4335", width=2, arrowsize=18, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=soft_edges, edge_color="#9aa0a6", width=1.2,
                            style="dashed", arrowsize=14, ax=ax)
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=7.5, ax=ax)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="#ea4335", lw=2, label="hard blocker"),
        Line2D([0], [0], color="#9aa0a6", lw=1.5, linestyle="dashed", label="soft dependency"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#9aa0a6", markersize=10, label="not started"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#4285f4", markersize=10, label="in progress"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#ea4335", markersize=10, label="blocked"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#34a853", markersize=10, label="done"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=8, framealpha=0.9)

    ax.set_title("Cross-Team Epic Dependency Graph\n(arrow points from prerequisite → blocked epic)", fontsize=12)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.close(fig)


def build_markdown_report(deps_df, cycles, blast_radius_df, hard_blocker_risk_df):
    lines = []
    lines.append("# Cross-Team Dependency Risk Report\n")

    lines.append("## 🔑 Key Findings\n")
    if cycles:
        for cycle in cycles:
            lines.append(f"- 🔴 **Circular dependency detected** involving epic IDs: {cycle}. "
                          f"This must be resolved before planning can proceed — by definition, "
                          f"neither epic can start first.")
    else:
        lines.append("- ✅ No circular dependencies detected in the current graph.")

    if not blast_radius_df.empty:
        top = blast_radius_df.iloc[0]
        lines.append(
            f"- 🎯 Highest blast-radius epic: **{top['epic']}** ({top['team']}, status: {top['status']}) "
            f"— {top['epics_downstream_if_delayed']} other epic(s) are downstream of it. "
            f"If this slips, treat it as a program-level risk, not just a {top['team']} risk."
        )

    lines.append("")
    lines.append("## 🎯 Blast Radius Ranking (epics other work depends on)\n")
    lines.append(blast_radius_df.to_markdown(index=False) if not blast_radius_df.empty else "_None found._")
    lines.append("")

    lines.append("## 🚫 Active Hard Blockers (upstream work not yet done)\n")
    if hard_blocker_risk_df.empty:
        lines.append("_No active hard blockers. ✅_")
    else:
        lines.append(hard_blocker_risk_df.to_markdown(index=False))
    lines.append("")

    lines.append("## 🔗 All Cross-Team Dependencies\n")
    display_df = deps_df[["blocked_title", "depends_on_title", "criticality", "notes"]].rename(
        columns={"blocked_title": "Blocked Epic", "depends_on_title": "Depends On", "notes": "Notes"}
    )
    lines.append(display_df.to_markdown(index=False))
    lines.append("")

    lines.append("![Dependency Graph](dependency_graph.png)\n")

    return "\n".join(lines)


def main():
    conn = sqlite3.connect(DB_PATH)
    epics_df, deps_df = load_data(conn)

    G = build_graph(epics_df, deps_df)
    cycles = find_cycles(G)
    blast_radius_df = rank_by_blast_radius(G, epics_df)

    hard_blocker_risk_df = pd.read_sql_query(
        """
        SELECT bt.team_name AS blocked_team, be.title AS blocked_epic,
               dt.team_name AS depends_on_team, de.title AS depends_on_epic,
               de.status AS depends_on_epic_status
        FROM dependencies d
        JOIN epics be ON d.epic_id = be.epic_id
        JOIN epics de ON d.depends_on_epic_id = de.epic_id
        JOIN teams bt ON be.team_id = bt.team_id
        JOIN teams dt ON de.team_id = dt.team_id
        WHERE d.criticality = 'hard_blocker' AND de.status != 'done'
        """,
        conn,
    )

    draw_graph(G, epics_df)
    report_md = build_markdown_report(deps_df, cycles, blast_radius_df, hard_blocker_risk_df)

    report_path = OUTPUT_DIR / "dependency_risk_report.md"
    report_path.write_text(report_md)

    conn.close()
    print(f"Report written to {report_path}")
    print(f"Graph written to {OUTPUT_DIR}/dependency_graph.png")
    if cycles:
        print(f"⚠️  {len(cycles)} circular dependency chain(s) detected!")


if __name__ == "__main__":
    main()
