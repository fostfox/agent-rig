---
name: github-self-review
description: "Self-review your own PR: fix, push, no formal review."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Pull-Requests, Code-Review, Self-Review, Git]
    related_skills: [github-code-review, github-pr-workflow]
---

# GitHub Self-Review Workflow

When the user asks you to review **your own PR** (self-review), the workflow is different from reviewing someone else's. You are both author and reviewer — there's no human in the review loop to respond to. Fix findings immediately, push, and move on.

## Core Rule

**Do NOT submit a formal GitHub review (`gh pr review --request-changes` or `--comment`) on your own PR.** This creates a formal review record that blocks auto-merge and requires dismissal. Just fix and push.

## Self-Review Sequence

### 1. Gather the diff

```bash
# From the PR branch:
git fetch origin main
git diff main...HEAD --stat       # scope at a glance
git diff main...HEAD              # full diff

# Or via gh:
gh pr diff 123
gh pr diff 123 --name-only
```

### 2. Run the checklist

Same criteria as a normal code review (correctness, security, code quality, testing, docs), but focus on:

- **Docs cross-references** — if you changed docs, do ADR cross-refs still match? Does the index (ADRS.md, plan.md) need updating?
- **Commit message quality** — backticks in commit bodies get consumed by bash. Verify with `git log -1 --format="%B"`.
- **Stale references** — the PR may fix some references but miss others (diagrams vs prose contradictions). Sweep for contradictions.

### 3. Fix findings → commit → push

```bash
# Fix issues with patch/write_file
git add -A
git commit -m "fix: address self-review findings

- Item one fixed
- Item two fixed"
git push
```

No force-push needed — adding a new commit to the PR branch is fine.

### 4. Reply to the PR thread

If you already posted a comment review, reply with what was fixed:

```bash
gh pr comment 123 --body "All findings fixed in <commit-sha>:

- Item one
- Item two"
```

## Pitfalls

- **Submitting a formal review on your own PR blocks the merge.** Skip the `gh pr review` call entirely. Just fix and push.
- **Backticks in commit messages get consumed by bash.** Use single-quoted heredocs or `--cleanup=whitespace` to avoid shell interpolation. If the message looks mangled, amend.
- **Patch tool can produce pipe artifacts.** When using `patch()` on table-heavy markdown (pipe tables), extra `|` may appear in adjacent cells. Re-read affected lines after each patch to verify table structure.
- **Do not call `gh pr review --approve` either.** Your own PR doesn't need your approval — if CI is green, the user will merge.

## Relationship to github-code-review

The bundled `github-code-review` skill covers reviewing *other people's* PRs and submitting formal reviews. This skill covers reviewing *your own* PRs, where the fix-then-push pattern replaces the formal-review pattern. Use both in sequence: first this skill to fix issues, then the bundled skill's checklist for thoroughness.