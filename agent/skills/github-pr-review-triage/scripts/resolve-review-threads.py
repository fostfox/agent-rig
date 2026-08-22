#!/usr/bin/env python3
"""
Resolve fixed PR review threads via GitHub GraphQL API.

Usage:
  python3 resolve-review-threads.py --owner <owner> --repo <repo> --pr <N> [--comment-ids ID1,ID2,...]

If --comment-ids is omitted, lists all unresolved threads for manual review.

Requires: gh CLI authenticated with the repo.
"""

import subprocess, json, sys, argparse

def gh_graphql(query):
    r = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:300])
    return json.loads(r.stdout)

def list_threads(owner, repo, pr_num):
    """Return all review threads with their comment databaseIds."""
    q = f"""
    {{
      repository(owner: "{owner}", name: "{repo}") {{
        pullRequest(number: {pr_num}) {{
          reviewThreads(first: 100) {{
            nodes {{
              id
              isResolved
              comments(first: 50) {{
                nodes {{ databaseId path body }}
              }}
            }}
          }}
        }}
      }}
    }}
    """
    data = gh_graphql(q)
    return data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]

def resolve_thread(thread_id):
    q = f"""
    mutation {{
      resolveReviewThread(input: {{threadId: "{thread_id}"}}) {{
        thread {{ id isResolved }}
      }}
    }}
    """
    res = gh_graphql(q)
    return res["data"]["resolveReviewThread"]["thread"]["isResolved"]

def main():
    parser = argparse.ArgumentParser(description="Resolve PR review threads")
    parser.add_argument("--owner", default="fostfox")
    parser.add_argument("--repo", default="prompt-to-print")
    parser.add_argument("--pr", type=int, default=11)
    parser.add_argument("--comment-ids", help="Comma-separated REST comment IDs to resolve")
    args = parser.parse_args()

    threads = list_threads(args.owner, args.repo, args.pr)

    if args.comment_ids:
        target_ids = set(int(x) for x in args.comment_ids.split(","))
        resolved = 0
        for t in threads:
            if t["isResolved"]:
                continue
            for c in t["comments"]["nodes"]:
                if c["databaseId"] in target_ids:
                    ok = resolve_thread(t["id"])
                    print(f"{'OK' if ok else 'FAIL'} {c['databaseId']} ({c['path']})")
                    resolved += 1
                    break
        print(f"\nResolved {resolved}/{len(target_ids)} threads.")
    else:
        # List all unresolved threads
        print(f"Unresolved threads: {sum(1 for t in threads if not t['isResolved'])}")
        for t in threads:
            if t["isResolved"]:
                continue
            c = t["comments"]["nodes"][0]
            print(f"  [{c['databaseId']}] {c['path']} | {c['body'][:80]}")

if __name__ == "__main__":
    main()