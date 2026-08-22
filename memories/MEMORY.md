Chat: match user's language per-message (RU ok when he writes RU). Look up official docs before guessing CLI flags. Banter/jokes in group chat — don't be stiff.
§
Tilt is the single entry point for local dev (tilt up/ci) — no ad-hoc pytest/compose. Integration tests must update with handler changes.
§
GitHub `project` scope needed for Projects v2 management. `gh auth refresh -h github.com -s project` uses device code flow (browser required) — not available in non-interactive agent context.
§
Sandbox VM: YC, ubuntu@93.77.189.250:18483. yc+cloud-init; --ssh-key conflicts with user-data. Worktree from origin/main; rsync one-way.
§
Amphetamine v5.3.2 keeps Mac awake for Hermes uptime; full AppleScript control via osascript — see amphetamine skill.
§
Repository uses `agent` label (#a371f7) for AI-created issues — not actionable until human removes label and assigns category. New agent issues go to Roadmap project with priority.
§
All research deliverables must be formatted as PDF with mobile-friendly page sizes (readable on phones).
§
Code hygiene: lower-level code never mentions higher-level infra; one runtime path; no dead config. Verify full-stack on sandbox VM.
§
YC NAT quirk: new VMs sometimes get external IPs that drop internet TCP (VM fine internally). Fix: recreate VM; verify with external TCP connect.
§
prompt-to-print CI vars: MAX_PR_VMS=5, YC_FOLDER_ID, YC_SUBNET, YC_SG, YC_ZONE — ansible playbook requires all (no defaults by design).
§
Click — предпочтительный CLI-фреймворк для Python-скриптов. Разрешены внешние зависимости.
§
GitHub App for agent-rig VM named mr-mechanic
§
Bogdan is pragmatic & security-conscious: prefers HTTP adapter over direct DB access for bot, rejects over-engineered infra (sealed-secrets, Postgres TLS) for POC. Test-only endpoints (reset-db, consume-link) must be DEV_MODE-gated. Prefers clean prefix structure (/api/internal/bot vs /api/internal/tests). Strong opinions on what belongs in prod vs dev-only.
§
plan-execution skill has `references/pr-review-feedback-handling.md` — pattern for reading all 3 GitHub feedback channels, fixing, replying to threads, multi-round review. Pointer in SKILL.md still needs foreground patch.