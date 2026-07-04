"""
fetch_github_epics.py

Simulates how a TPM tool would pull "epics" for the Platform team from a real
API — in this case, GitHub Issues (labeled 'epic') on a real repo.

Design note: unauthenticated GitHub API calls are rate-limited (60/hr per IP,
shared across anyone on the same network/CI runner). Rather than fail loudly
when that happens, this script falls back to a cached sample response, and
tells you which one it used. This mirrors how you'd actually want a real
dependency-tracker integration to behave: don't take down the whole tool
because one team's API had a bad minute.

To use with higher rate limits, set a GITHUB_TOKEN env var (no special scopes
needed for public repo reads).

Usage:
    python fetch_github_epics.py [owner/repo]
    (defaults to a small public repo if none given)
"""

import os
import sys
import json
import urllib.request
import urllib.error

CACHE_PATH = "../sample_data/github_issues_cache.json"
DEFAULT_REPO = "github/roadmap"


def fetch_live(repo):
    url = f"https://api.github.com/repos/{repo}/issues?state=all&per_page=20"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    if isinstance(data, dict) and data.get("message"):
        # GitHub returns a dict with an error message (e.g. rate limit) instead of a list
        raise RuntimeError(data["message"])
    return data


def fetch_with_fallback(repo):
    try:
        issues = fetch_live(repo)
        print(f"✅ Fetched {len(issues)} live issues from github.com/{repo}")
        return issues, "live"
    except (urllib.error.URLError, RuntimeError, TimeoutError) as e:
        print(f"⚠️  Live GitHub API call failed ({e}). Falling back to cached sample data.")
        with open(CACHE_PATH, "r") as f:
            issues = json.load(f)
        print(f"✅ Loaded {len(issues)} issues from cache: {CACHE_PATH}")
        return issues, "cache"


def normalize(issues, team_name="Platform"):
    """Convert raw GitHub issue payloads into the epic schema our DB expects."""
    normalized = []
    for issue in issues:
        # Skip pull requests, which the GitHub issues endpoint also returns
        if "pull_request" in issue:
            continue
        normalized.append(
            {
                "title": issue["title"],
                "status": "done" if issue["state"] == "closed" else "in_progress",
                "owner": issue.get("assignee", {}).get("login") if issue.get("assignee") else "unassigned",
                "source_system": "github",
                "external_id": str(issue["number"]),
                "url": issue.get("html_url", ""),
                "team_name": team_name,
            }
        )
    return normalized


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_REPO
    issues, source = fetch_with_fallback(repo)
    normalized = normalize(issues)

    out_path = "../sample_output/platform_epics_from_github.json"
    with open(out_path, "w") as f:
        json.dump({"source": source, "epics": normalized}, f, indent=2)

    print(f"Wrote {len(normalized)} normalized epics to {out_path} (source: {source})")


if __name__ == "__main__":
    main()
