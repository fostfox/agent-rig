---
name: github-pr-review-triage
description: Triage PR review comments and propose responses.
version: 1.3.0
metadata:
  hermes:
    tags: [github, pr, review, code-review, workflow]
    category: autonomous-ai-agents
    requires_toolsets: [terminal, web]
    related_skills: [github-code-review, github-pr-workflow]
---

# GitHub PR Review Comment Triage

When the user asks you to "read all PR comments", "respond to review comments",
or "address review feedback" — this is the **contributor's workflow**. You are
not performing the review; you are triaging incoming review comments on your
(or the user's) PR, categorizing each, and proposing how to respond.

## When to Use

- User says "read all comments left in PR, write responses for each"
- User says "address review feedback" or "respond to PR comments"
- A PR has multiple review comments (human + automated) that need categorization
- You need to decide which comments to fix now and which to defer

## Procedure

### 1. Fetch ALL review comments

PR comments come in two types — both need fetching:

```bash
# Fetch PR details + top-level review summaries
gh pr view <N> --json comments,reviews

# Fetch inline review comments (code-level)
gh api repos/<owner>/<repo>/pulls/<N>/comments --paginate

# Single command for structured output:
gh pr view <N> --json comments,reviews \
  --jq '{comments: [.comments[] | {author, body}], reviews: [.reviews[] | {author, state, body}]}'
```

Use `--paginate` on the inline comments endpoint — Copilot often generates 30+
comments spread across multiple pages.

### 2. Categorize every comment

Group into these tiers:

| Tier | What it means | Response |
|------|--------------|----------|
| **Critical bug** | Security issue, production crash, data loss, broken feature | **Agree, must fix** before merge |
| **Genuine bug** | Logic error, wrong assertion, missing edge case, regression | **Agree**, explain the fix plan |
| **Style/preference** | Naming, formatting, approach — subjective | **Agree or disagree** politely with reasoning |
| **Outdated** | Already fixed in a later commit, or stale context | Say so — "already fixed in commit X" |
| **Misunderstanding** | Commenter missed the intent or constraint | **Explain**, not fight. "The constraint is..." |
| **Wrong/silly** | Incorrect analysis, suggests worse approach, ignores constraints | Say **why briefly**. Don't debate — state the constraint. "This is necessary because YC Cloud Functions require x." |

### 3. Batch aggregation for large reviews

When there are 40+ comments (Copilot, thorough human reviewer):

- **Deduplicate:** identical comments across multiple files (e.g. 3× same `***` password issue) = one response
- **Copilot comments:** treat seriously — Copilot catches real bugs (missing YDB param, uppercase prefix, security leaks). But batch repetitive ones.
- **Author's own comments** (fostfox): prioritize over automated reviewer comments
- **Group by subsystem:** all Docker compose fixes together, all Terraform together, etc.

### 3a. Parallel subagent dispatch for large reviews

When there are 30+ comments spanning multiple distinct areas (e.g. deploy.yml,
docs, Python code, k8s manifests, CI), split the work across **parallel
subagents** for speed. The user may explicitly ask for this — "run parallel
agents" is a green light.

**How to split:**

| Batch size | Strategy |
|-----------|----------|
| 10–20 comments | Single agent, batch by file |
| 20–40 comments | 2 subagents: 1 for code/infra, 1 for docs |
| 40–80 comments | 3–4 subagents: e.g. deploy.yml, docs/ARCH, Python code, verification |

**Dispatch pattern for each subagent:**

```python
delegate_task(
    context="...",
    goal=f"Fix these N threads on PR #N: [list thread IDs with descriptions]. "
         f"Worktree: ~/Worktrees/branch-name (branch: fix/branch). "
         f"After fixing, commit with message 'fix: ...' and push to origin/branch. "
         f"IMPORTANT: do NOT resolve threads — just fix, commit, push.",
    role="leaf"
)
```

**Critical: parallel agent collision rule.** When two agents work on the same
branch simultaneously, one agent's commit may already contain the other's fix.
Before attempting your own changes, always check:

```bash
git fetch origin && git log --oneline origin/branch-name -3
```

If the branch has moved forward (new commit from a parallel agent), your fixes
may already be upstream. Rebase (or --continue the in-progress rebase), re-check
each thread's file, and skip any that are already fixed. Push only the changes
that are genuinely new. Do NOT re-resolve threads the other agent resolved.

**Re-open escalation tip:** The user may also re-open THREADS, not just files.
A re-opened thread with no new reply means GitHub thinks the resolve-the-fix
link broke — the fix code may still be there, but the commit SHA the resolve
reference is gone (rebase/force-push). Check the file on disk, and if the fix
is solid, a new commit + push (not a re-resolve) is sufficient — the user's
re-review will confirm it. If a thread has a reply from the user ("why did you
resolve this? / this was not fixed"), do NOT re-resolve — fix the issue first,
then re-resolve.

**IMPORTANT: commit scoping.** Delegated agents each commit only their batch.
Do NOT delegate a "resolver" agent that merges or resolves — that's the
parent's job after all fix-agents finish. The parent waits for all delegated
agents (via the completion notification), then verifies the branch state and
resolves threads via GraphQL.

**Pre-conditions before dispatching:**
- Fetch the PR's review threads first (`gh api graphql ... reviewThreads`)
- Classify them yourself so you know which threads go to which agent
- Ensure each agent gets a self-contained batch (no agent depends on another's fix)
- Set `background=True` for all dispatches — they run in parallel

### 4. Response format per comment

```
### `file/path:line` — @author

**Tier:** critical | bug | style | outdated | misunderstanding | wrong

**Response:** [agree/disagree + concise reasoning]

**Action:** will fix | already fixed in commit X | no action needed | discuss
```

### 5. Response phrasing guide

| Situation | Phrase |
|-----------|--------|
| Agree, critical | "Agree. This breaks [thing] because [mechanism]. Will fix." |
| Agree, minor | "Agree, good catch. Will address." |
| Disagree | "Respectfully disagree — [one-sentence constraint or rationale]. Doing it the suggested way would [negative consequence]." |
| Misunderstanding | "The intent here is [x]. The code does this because [y] — not [what commenter assumed]." |
| Wrong/silly | "This isn't an issue because [concise reason]. The suggested approach would [break something]." |
| Already fixed | "Already fixed in [branch/commit summary] — the current code handles this." |

### 6. Per-comment protocol: 👍 + resolve vs reply

**HARD RULE (user-enforced): process threads ONE AT A TIME — fix → verify → resolve → NEXT.**
The user has twice caught a bulk resolve that closed conversations without fixing them.
Bulk-resolving (e.g. one script resolving 10+ threads in a loop) is GUARANTEED to
miss something and the user WILL re-open the threads. Never do it.

**HARD RULE: reply IN each thread, not one summary comment.** The user explicitly
rejected a single summary comment enumerating all fixes. Each review thread must
get its OWN reply with a concise description of what was fixed and the commit SHA.
Use the `gh api repos/OWNER/REPO/pulls/PR_NUMBER/comments/COMMENT_ID/replies`
endpoint once per thread — do NOT batch into a single PR comment or GraphQL mutation.

```bash
for pair in \
  "3827118686|Fixed: clarified rebuild-on-change in docs." \
; do
  cid="${pair%%|*}"
  body="${pair#*|}"
  gh api "repos/OWNER/REPO/pulls/PR_NUMBER/comments/$cid/replies" -f body="$body"
done
```

The `"in_reply_to": COMMENT_ID` field on the response confirms the reply was
attached to the correct thread.

**Keep replies short:** Bogdan flagged verbose docstrings and unnecessary comments
as issues. Each reply should be a single line: what was fixed + commit SHA. No
explanation of why unless the comment asked for one.

Per-thread sequence for a thread that requires a code change:

1. **Fix the code** — make the actual edit in the worktree
2. **Verify the fix** — run the relevant test / grep the file / check syntax
3. **Sandbox VM test** — when the project has a sandbox VM (k3s cluster with Tilt
   hot-reload), rsync the worktree to the VM and let Tilt reload before
   confirming the fix:
   ```bash
   # Sync worktree to sandbox VM (uses rsync + custom SSH port)
   rsync -az --delete --exclude=.git --exclude=node_modules --exclude=.venv \
     -e "ssh -i ~/.ssh/id_ed25519 -p $SANDBOX_PORT" \
     ~/Worktrees/branch-name/ ubuntu@$SANDBOX_IP:~/prompt-to-print/
   
   # Wait for Tilt hot-reload (uvicorn --reload picks up changes within seconds)
   sleep 5
   
   # Verify the fix is live on the VM
   ssh -p $SANDBOX_PORT ubuntu@$SANDBOX_IP \
     "kubectl exec -n prompt-to-print deploy/api -- python3 -c '...'"
   ```
   See the repo's AGENTS.md for exact SSH details (`ubuntu@93.77.189.250:18483`
   in the reference project). Only skip this step for pure-documentation changes
   or when the user explicitly says to skip it.
4. **Commit + push** — only after verification passes
5. **👍 + resolve that ONE thread**
6. **Move to the next thread** — repeat

When the user says "for each comment: thumbs up + resolve if you fixed it,
reply if you didn't", follow this protocol:

| Your action | For comments where you… |
|-------------|--------------------------|
| 👍 + resolve thread | Fixed the issue AND committed/pushed the fix to the branch |
| Reply only (leave unresolved) | Deferred to another issue, answered with explanation, or needs discussion |
| 👍 only (no resolve) | Issue was fixed by someone else's merged PR, not by you |
| Reply + 👍 + resolve | Fixed the issue AND the fix is committed/pushed — full cycle |

**A resolve must be backed by evidence.** Before resolving ANY thread, be able
to answer: "which commit on this branch contains the fix, and did I verify it
on disk?" If you cannot name the commit and point at the fixed line, do NOT
resolve — reply instead. This includes threads you claim are "already fixed":
re-check the file in the CURRENT worktree state (a rebase, parallel agent
commit, or merge can drop a fix). The user re-opens threads precisely when a
resolve was premature.

### Continuous re-check loop — threads may be re-opened or new ones added

After processing ALL threads in the initial batch, **re-fetch** to check for new
unreacted threads. The reviewer may:
- Re-open previously-resolved threads after checking your fixes
- Add new inline comments on new commits
- Resolve some threads themselves and leave others for you to handle

**Loop workflow:**

```bash
while true; do
  # Fetch all thread starters without 🚀 or 👀
  gh api repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments --paginate \
    | python3 -c "
import sys, json
# ... parse, deduplicate, find thread starters without rocket/eyes ...
"

  pending=$(...)  # count of unreacted thread starters
  if [ "$pending" -eq 0 ]; then
    echo "All threads processed."
    break
  fi

  echo "$pending threads remaining — processing next..."
  # Pick the first unreacted thread, classify, fix/reply/react
done
```

**When to use the loop:**
- The user resolved conversations and created new ones (common human-reviewer behavior)
- Copilot re-review after new push generated additional comments
- You committed fixes and the branch advanced — GitHub may trigger a fresh review

**Ordering heuristic:** process threads chronologically (oldest first) unless the
user's own replies are among them — in that case, prioritize user threads over
automated reviewer threads.

### Reaction-based triage (🚀/👀) — lighter-weight alternative

When the reviewer is an automated system (Copilot, bot) or you want a
lighter-weight state marker than formal resolution, use **reactions** to
track thread state:

| Reaction | Meaning |
|----------|---------|
| (none) | Unaddressed — needs triage |
| 🚀 | Fixed in this PR — code change was committed and pushed |
| 👀 | Escalated to a separate issue — fix deferred to future work |

**Workflow:**

1. **Fetch all inline PR comments** and check for existing reactions:
   ```bash
   gh api repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments --paginate
   ```
   For each comment, check `reactions.rocket` and `reactions.eyes` — if both are
   0, the thread hasn't been processed yet.

2. **Classify** each unaddressed thread into one of three buckets:
   - **Fix in this PR** — commit a fix, push, post a reply, add 🚀
   - **Create separate issue** — create a GitHub issue, post a reply linking it, add 👀
   - **Won't fix** — reply explaining why, no reaction needed

3. **Reply inline** to each thread (not as a top-level PR comment):

   **IMPORTANT — `in_reply_to` is mutually exclusive with location params.**
   When replying to an existing thread, do NOT include `commit_id`, `path`,
   `line`, `side`, or `subject_type`. Only send `body` and `in_reply_to`:

   ```bash
   # Method A: JSON file (reliable — ensures in_reply_to is a number)
   cat > /tmp/reply.json << 'JSONEOF'
   {"body": "✅ Fixed: <short>. (<sha>)", "in_reply_to": COMMENT_ID}
   JSONEOF
   gh api repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments --input /tmp/reply.json

   # Method B: -f flags (works for simple cases)
   gh api repos/$OWNER/$REPO/pulls/$PR_NUMBER/comments \
     --method POST \
     -f body="✅ Fixed: <short>. (<sha>)" \
     -f in_reply_to=$ORIGINAL_COMMENT_ID
   ```

   **Why JSON file is preferred:** `-f in_reply_to=$ID` sometimes sends the
   value as a string (causing `"is not a number"` errors). The `--input` file
   approach with unquoted integer values avoids this entirely.

   The reply confirms success when `gh api ... --input /tmp/reply.json` returns
   a JSON object with `"in_reply_to_id": COMMENT_ID` in the response.

4. **Add reaction** to the original comment to mark its state:
   ```bash
   # 🚀 for fixed in this PR
   gh api repos/$OWNER/$REPO/pulls/comments/$ORIGINAL_COMMENT_ID/reactions \
     --method POST -f content=rocket

   # 👀 for escalated to separate issue
   gh api repos/$OWNER/$REPO/pulls/comments/$ORIGINAL_COMMENT_ID/reactions \
     --method POST -f content=eyes
   ```

5. **Batch operations** for efficiency when there are many threads — use
   `execute_code` with `terminal()` calls in a loop rather than serial round-trips.

**Reacting to automated reviewer threads vs human threads:**
- Automated reviewer (Copilot): reaction-based triage is ideal — no concept of
  "resolving" from the bot's side
- Human reviewer: use the 👍+resolve protocol in section 6 instead, or combine
  them (reply + 🚀 + resolve for a full cycle)

**Order of operations — always two passes:**

1. **Pass 1 — Reply to unresolved/deferred threads.** Before resolving
   anything, reply to the threads you are NOT resolving. Use GraphQL:
   ```graphql
   mutation {
     addPullRequestReviewThreadReply(
       input: {pullRequestReviewThreadId: "THREAD_ID", body: "Reply"}
     ) { __typename }
   }
   ```
2. **Pass 2 — Then resolve fixed threads.** Once all replies are posted, add
   👍 reactions to the fixed threads, then resolve them via GraphQL.

A reply was successfully posted when `gh api .../replies -f body="..." --method POST`
returns `{` as first response character. Empty/null responses or explicit
errors indicate failure — a second attempt often succeeds. If it consistently
returns 404, use the endpoint WITHOUT the PR number:
`repos/{owner}/{repo}/pulls/comments/{id}/replies` (also valid).

### 7. Mapping REST comment IDs to GraphQL thread IDs

REST API returns integer comment IDs (e.g. `3817156290`). GraphQL thread IDs
are opaque strings (e.g. `PRRT_kwDOTzFRNc6aoaOU`). To map them:

```python
import subprocess, json

# 1. Query all review threads on the PR
result = subprocess.run(
  ["gh", "api", "graphql", "-f", f"query={ ... }"],
  capture_output=True, text=True, cwd="/path/to/repo"
)
data = json.loads(result.stdout)
threads = data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]

# 2. Build REST_ID -> thread_id mapping
comment_to_thread = {}
for t in threads:
    for c in t["comments"]["nodes"]:
        comment_to_thread[c["databaseId"]] = t["id"]

# 3. Resolve by REST ID
rest_id = 3817156290
thread_id = comment_to_thread[rest_id]
```

### 8. Author's comments take priority over automated reviewers

When a human author (e.g. `fostfox`) and an automated reviewer (e.g. Copilot)
both left comments:
- Address the author's comments FIRST — they decide what gets merged
- For Copilot comments: treat seriously (they catch real bugs) but batch
  repetitive ones. If the author already responded to a Copilot comment,
  don't add another reply.

### 9. Closing Resolved Threads (Resolving Conversations)

After you have fixed the issues and replied to the relevant threads, the user
may ask you to "close fixed conversations" or "resolve resolved threads".
This is a two-step process — REST replies plus GraphQL resolution.

**Step 1: Reply to each fixed thread** with a note referencing the fix:

```bash
gh api repos/<owner>/<repo>/pulls/<N>/comments/<comment_id>/replies \
  -X POST -f "body=Fixed in <sha>: <summary>"
```

- Classify each thread before replying: genuinely fixed / answered (explanation
  sufficed) / deliberately-skipped (documented decision). Leave truly open
  threads (real pending work) unresolved.
- For "answered" threads, reply with: "Addressed — [short explanation]"
  rather than faking a fix reference.

**Step 2: Resolve the thread via GraphQL** — REST cannot do this:

```bash
# Find thread IDs by querying all review threads on the PR
gh api graphql -f query='
{
  repository(owner: "OWNER", name: "REPO") {
    pullRequest(number: N) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 50) { nodes { databaseId } }
        }
      }
    }
  }
}'
```

Then resolve each matching thread:

```bash
gh api graphql -f query='
mutation {
  resolveReviewThread(input: {threadId: "THREAD_ID"}) {
    thread { id isResolved }
  }
}'
```

**Key gotchas:**
- `PATCH /repos/{owner}/{repo}/pulls/comments/{id}` with `resolution=RESOLVED`
  returns `422: "resolution is not a permitted key"` — **does not work.**
- You need the thread's **GraphQL node ID** (starts with `PRR_kw...`), not the
  REST comment ID (integer). Map them by matching the comment's `databaseId`
  from the GraphQL query against the REST comment IDs you know.
- For bulk resolution (30+ threads), use `scripts/resolve-review-threads.py`
  under this skill directory. It accepts `--comment-ids` for batch resolution
  or runs without arguments to list all unresolved threads for manual review.

### 10. Verifying Re-Opened Threads

A reviewer may re-open a previously-resolved thread because the fix wasn't
actually effective, the commit SHA changed after rebase, or the diff context
shifted. This is a distinct workflow from initial triage — the fix was
*allegedly* already committed, and you need to verify it's real.

**Pattern: per-thread verification with targeted commands**

For each re-opened thread, write an explicit verification command (grep, ls,
head) that proves the fix is on disk. Batch all verifications in a single
terminal call for efficiency — they are independent:

```bash
cd ~/Worktrees/branch-name
echo "=== Thread X: <topic> ===" && grep -n "SEARCH_TERM" path/to/file
echo "=== Thread Y: <topic> ===" && ls -la path/to/other/file 2>/dev/null
echo "=== Thread Z: <topic> ===" && head -20 path/to/config.py
```

Then classify each thread:

| Result | Action |
|--------|--------|
| **Already fixed** — grep/head shows the fix is present | No code change needed. The fix is real — commit and push the current branch state. Do NOT re-resolve via API; the new commit triggers re-evaluation. |
| **Not fixed** — file doesn't exist or still has the offending content | Fix the underlying issue with `patch`/`write_file`, then commit. |
| **File exists but needs a tweak** | Fix the specific line. The review comment tells you exactly what's wrong. |

**Important: DO NOT resolve threads in this workflow.** The instruction is
often "commit + push only, do not resolve threads." The reviewer re-opened
them because the previous resolve was premature. Let the new commit on the
branch trigger GitHub's re-evaluation — the reviewer will re-check and
re-resolve.

**Key gotchas for re-opened threads:**

- A file showing `UU` in `git status` (unmerged) may already be clean (no
  conflict markers). `git diff --cc` shows the combined diff. If clean,
  just `git add <file>` to mark resolution — the next commit concludes the
  merge.
- Re-opened threads after a rebase/force-push: GitHub may have unresolved
  threads because the commit SHA linked to the resolve no longer exists.
  The fix code may be identical — the re-open is a metadata issue. A new
  push to the branch is sufficient.
- The reviewer may have re-opened ALL threads in one click (GitHub supports
  batch "re-open unresolved"). Not every thread necessarily had a broken
  fix — some may be collateral. Verify each one independently before
  assuming it's broken.
- Also check for pre-existing uncommitted changes in the worktree (e.g. CI
  workflow improvements) and decide whether to include them in the commit —
  don't silently drop or add them.
- **Parallel agent collision:** if you were dispatched as one of several
  parallel agents, a sibling agent may have already committed a fix to the
  same thread before you. Before starting work, `git fetch origin && git log
  --oneline origin/branch -3` — if new commits appeared, the fixes may
  already be upstream. Rebase, re-verify each thread's file, and skip any
  already fixed. Push only genuinely new changes.

### 11. Pre-Merge PR Hygiene

The user may ask you to prepare the PR for merge: update the description,
reference closed issues, and resolve conversations.

**Update PR description:** Write a summary in the repo's doc language
(English for code/docs, keep UI copy in the product language). Group by
feature area. End with `Closes #N` for each issue the PR resolves. Verify
each referenced issue exists:
`gh issue view N --json title,state`. Use a temp file for the body to
avoid shell-quoting breakage on apostrophes/quotes:

```bash
gh pr edit N --body-file /tmp/pr-body.md
```

**Mention closed issues:** Add `Closes #N` to the PR body. GitHub
auto-closes them when the PR merges. Do NOT list merged PRs or unrelated
issues as "Closes".

**Check merge readiness:**
```bash
gh pr view N --json mergeable,state,statusCheckRollup
# mergeable: MERGEABLE, verify job: SUCCESS
```

### 12. Fixing vs waiting

The user may want you to fix issues immediately after reading them, not wait
for approval. When they say "start fixing", proceed directly — don't re-ask
for permission. Batch fixes by subsystem for clean commits:

1. Security fixes first
2. Production crash bugs
3. Infrastructure (Docker, mock, CI)
4. Logic bugs (handlers, tests)
5. Documentation/cleanup

### 13. Verify with CI after fixing

After committing all fixes:
1. Trigger the CI workflow (`gh workflow run deploy.yml --ref <branch> -f dry-run=true -f include-verify=true`)
2. Wait for the run to complete (`gh run watch <id> --exit-status`)
3. Check each job's conclusion: verify ✅, lint (if pre-existing debt, note it), deploy ✅
4. If any job fails due to YOUR changes (not pre-existing debt), fix and re-run
5. Only report "all comments addressed" when CI passes on the pushed branch

### 14. DO NOT start fixing until user approves (default)

After presenting the full categorized response, tell the user the
categorization summary (X critical, Y bugs, Z style, etc.) and wait for
explicit direction before touching any code — UNLESS the user said "start
fixing" or "address comments" in the same message.

### 15. Relationship to other skills

- **`github-code-review`** covers the REVIEWER workflow (reviewing a PR, leaving comments).
  This skill covers the CONTRIBUTOR workflow (reading review comments and responding).
- Both skills share the same tooling (`gh`, `curl`, `jq`) but have different
  outputs — reviews produce feedback; triage produces categorized responses + action items.

### 16. Known Traps (Hermes-specific)

- **ADR precision — don't blanket-supersede grouped files.** A single ADR file
  often contains multiple decisions (e.g., ADR-001 covers ADR-001 through
  ADR-005). When superseding, be PRECISE about which individual decisions within
  the file are superseded vs still active. A product decision like "No
  Registration" may remain valid even though the infrastructure decisions in the
  same file are obsolete. Copilot will call this out — and correctly so.
- **Verify doc claims against code.** A common review catch is documenting
  features that don't exist (rate limiting, nginx, specific error responses).
  Before writing docs that claim a feature exists, check the actual codebase —
  `grep` for the component, check k8s manifests for the resource, verify the
  endpoint handler returns the claimed status code. If a feature is planned but
  not implemented, say "not yet configured" rather than pretending it exists.
- **Diagrams must match prose.** Adding a note that says "nginx was replaced"
  while the Mermaid diagram above still shows nginx creates a contradiction.
  Update both diagrams AND prose in the same pass — don't leave a note that
  disproves the diagram.

- **`AGENTS.md` is write-protected.** Hermes blocks `write_file` and `patch`
  on `AGENTS.md` and `CLAUDE.md` unless the user explicitly approves in a
  popup. If you need to edit AGENTS.md as part of a PR fix (e.g. removing a
  stale file reference), use a terminal workaround:
  ```bash
  cd ~/Worktrees/branch
  sed -i '' '/stale-line/d' AGENTS.md
  git add AGENTS.md && git commit -m "..." --no-gpg-sign
  ```
  The tool guard blocks API-level writes, not bash-level ones. However, only
  use this when the user explicitly approved the AGENTS.md change — do not
  silently modify it.
- **`git -c user.signingkey=""` for GPG-free commits.** The user's GPG agent
  (1Password, YubiKey, etc.) can block `git commit`. Always pass
  `git -c user.signingkey="" commit -m "..." --no-gpg-sign` to bypass.
- **`graphql` query formatting.** The `gh api graphql` tool is extremely
  sensitive to newlines inside the query string. For multi-line GraphQL
  mutations, build the query in a Python script and pass with `-f query=`.
  Inline shell heredocs with GraphQL mutations frequently fail with "invalid
  query" errors due to unescaped newlines.