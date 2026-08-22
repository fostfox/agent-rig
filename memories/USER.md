Docs/PRs/comments EN only; chat matches user's language (RU ok when he writes RU).
§
GitHub: public IDs → Variables, secrets → Secrets. Push via existing PR branch.
§
Expects full devloop verify on sandbox VM before PR finalization. Fast-only not sufficient.
§
PR review: fix→test→reply short→🚀 or issue→👀. Never bulk-resolve. Git worktree when main dirty.
§
Bogdan — prompt-to-print architect. Prefers single-file config. #feature=stakeholder, #enabler=technical.
§
Code: Click not argparse/typer for Python CLIs. No lower-level code ref higher-level infra.
§
1Password: vault `agent-rig`, lowercase_underscore item/field names (no spaces). Prefers GitHub App over PAT for automation.
§
Wants step-by-step guidance: 'what I do vs what you do'. Likes iteration + discussion before decisions.
§
Prefers Russian for architecture discussions, English for code and actions.
§
For multi-task issues (5+ tasks), prefers subagent delegation with parallel git worktrees. Each subagent gets `git worktree add -b feature/issue-N-slug ~/Worktrees/issue-N-slug origin/main`, implements TDD, commits, pushes, opens PR. Orchestrator manages dependency graph: parallel independent tasks first, then sequential dependent ones, final verify on sandbox VM.