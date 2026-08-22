# agent-rig 🚀

**Provisioned dev VM with pre-configured LLM agent tools.**

A Vultr VM, fully automated via Ansible + GitHub Actions. Spin up a ready-to-use development environment with Hermes CLI, GitHub CLI (pipo-robot), Yandex Cloud CLI, Docker + bidirectional config sync.

> This is a **private repo** — it's both the infrastructure-as-code AND the Hermes profile distribution that the agent syncs against.

## Quick start

```bash
# Push to main → triggers VM provision
git push origin main

# Wait ~5 min → VM is ready
# SSH in:
ssh -i <key> dev@<vm-ip>
```

## What's inside

| Tool | Config |
|------|--------|
| **Hermes CLI** | Pre-configured OpenRouter, deepseek/deepseek-v4-flash |
| **gh CLI** | Authenticated as `pipo-robot` (GitHub App) |
| **yc CLI** | Authenticated with SA key |
| **Docker** | Installed |
| **Workspace** | `~/dev/` — short clean paths |

## Bidirectional sync

The agent on the VM syncs with this repo every 10 minutes:

```
repo push  →  agent pulls: config.yaml, SOUL.md, skills/
agent push →  repo pulls: MEMORY.md, USER.md
```

No secrets in repo — all API keys come from 1Password at deploy time.

## Repo structure

```
├── distribution.yaml      ← Hermes profile distribution manifest
├── hermes.yaml             ← agent config (no secrets)
├── SOUL.md                 ← agent identity (me!)
├── memories/
│   ├── MEMORY.md          ← what agent remembers about environment
│   └── USER.md            ← what agent knows about you
├── skills/                 ← custom skills installed on the VM
│   ├── github-pr-review-triage/
│   ├── github-self-review/
│   └── http-repository-adapter/
├── ansible/                ← VM provisioning & tool config
│   ├── playbook.yml
│   ├── requirements.yml
│   └── roles/
│       ├── base/           ← dev user, packages, workspace
│       ├── gh-cli/         ← gh + GitHub App (pipo-robot)
│       ├── yc-cli/         ← yc + SA key auth
│       ├── docker/         ← Docker install
│       └── hermes-cli/     ← hermes install + config from repo + sync cron
├── .github/workflows/
│   └── deploy-vm.yml      ← 1Password → Ansible → Vultr
└── AGENTS.md               ← agent rules for working in this repo
```