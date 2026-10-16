#!/usr/bin/env python3
"""
Scan public GitHub for real-world Agent2Agent (A2A) protocol implementations
by searching for the protocol's own discovery artifact: a `.well-known/agent-card.json`
file (the current spec name; older agents use `.well-known/agent.json`).

This does not measure private/internal production deployments -- it can't see
those. It measures the only independently falsifiable signal available from
outside any one vendor or the Linux Foundation's own membership rolls: who has
actually published an A2A-discoverable agent in the open.

Usage:
    export GITHUB_TOKEN=ghp_...   # a plain, unscoped PAT is enough (public code search)
    python3 scripts/scan.py

Requires: Python 3.9+, stdlib only (urllib). No pip install.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

API = "https://api.github.com/search/code"
QUERIES = [
    ("agent-card.json", "filename:agent-card.json path:.well-known"),
    ("agent.json", "filename:agent.json path:.well-known"),
]
PER_PAGE = 100
MAX_PAGES = 10  # GitHub code search caps at 1000 results (10 pages x 100)


def _get(url, token):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "a2a-inventory-demo",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def search_all_pages(query, token):
    items = []
    total_count = None
    for page in range(1, MAX_PAGES + 1):
        url = f"{API}?q={urllib.parse.quote(query)}&per_page={PER_PAGE}&page={page}"
        try:
            data = _get(url, token)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            print(f"  HTTP {e.code} on page {page}: {body[:300]}", file=sys.stderr)
            break
        if total_count is None:
            total_count = data.get("total_count", 0)
        batch = data.get("items", [])
        if not batch:
            break
        items.extend(batch)
        if len(batch) < PER_PAGE:
            break
        time.sleep(2.5)  # code search secondary rate limit is tight; stay well under it
    return total_count or 0, items


def account_type(owner_login, token, cache):
    if owner_login in cache:
        return cache[owner_login]
    url = f"https://api.github.com/users/{owner_login}"
    try:
        data = _get(url, token)
        t = data.get("type", "unknown")
    except urllib.error.HTTPError:
        t = "unknown"
    cache[owner_login] = t
    time.sleep(0.3)
    return t


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "GITHUB_TOKEN is not set. GitHub's code search API requires an "
            "authenticated request (even for public repos). Create a PAT with "
            "no scopes (public access only) at https://github.com/settings/tokens "
            "and export it as GITHUB_TOKEN.",
            file=sys.stderr,
        )
        sys.exit(1)

    all_repo_owner_pairs = []  # (repo_full_name, owner_login) across both queries, deduped
    seen_repo_names = set()
    report = {"queries": [], "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    for label, q in QUERIES:
        print(f"Searching: {q}")
        total, items = search_all_pages(q, token)
        fetched = len(items)
        print(f"  total_count reported by API: {total} (fetched {fetched}, capped at {MAX_PAGES * PER_PAGE})")
        report["queries"].append({"label": label, "query": q, "total_count": total, "fetched": fetched})
        for it in items:
            repo = it["repository"]["full_name"]
            owner = it["repository"]["owner"]["login"]
            if repo in seen_repo_names:
                continue
            seen_repo_names.add(repo)
            all_repo_owner_pairs.append((repo, owner))

    if not all_repo_owner_pairs:
        print("No results fetched (rate limited or token invalid). See stderr above.", file=sys.stderr)
        sys.exit(1)

    owner_counts = Counter(owner for _, owner in all_repo_owner_pairs)
    unique_repos = len(all_repo_owner_pairs)
    unique_owners = len(owner_counts)

    top_owner, top_owner_repo_count = owner_counts.most_common(1)[0]
    top_owner_share = top_owner_repo_count / unique_repos * 100

    type_cache = {}
    top_owner_type = account_type(top_owner, token, type_cache)

    print()
    print(f"Deduped repos with a published A2A discovery file: {unique_repos}")
    print(f"Distinct GitHub accounts behind them:               {unique_owners}")
    print(f"Single largest account:                             {top_owner} "
          f"({top_owner_type}) -- {top_owner_repo_count} repos ({top_owner_share:.1f}% of all hits)")
    print()
    print("Top 10 accounts by repo count:")
    for owner, count in owner_counts.most_common(10):
        print(f"  {count:4d}  {owner}")

    report.update(
        {
            "unique_repos": unique_repos,
            "unique_owners": unique_owners,
            "top_owner": top_owner,
            "top_owner_type": top_owner_type,
            "top_owner_repo_count": top_owner_repo_count,
            "top_owner_share_pct": round(top_owner_share, 1),
            "top_10_owners": owner_counts.most_common(10),
        }
    )

    out_path = os.path.join(os.path.dirname(__file__), "..", "captures", "latest-scan.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nFull report written to {out_path}")


if __name__ == "__main__":
    main()
