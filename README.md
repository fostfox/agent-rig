# agent-rig 🚀

**Provisioned dev VM with pre-configured LLM agent tools.**

A Vultr VM, fully automated via Ansible + GitHub Actions. Spin up a ready-to-use development environment with Hermes CLI, GitHub CLI, Yandex Cloud CLI, Docker, and more — everything configured and authenticated.

## Quick start

```bash
# 1. Push to main → triggers provision
git push origin main

# 2. Wait ~5 min → VM is ready

# 3. SSH in
ssh dev@<vm-ip>
```

## What's inside

| Tool | Status |
|------|--------|
| **Hermes CLI** | Pre-configured with OpenRouter |
| **gh CLI** | Authenticated as GitHub App (`pipo-robot`) |
| **yc CLI** | Authenticated with SA key |
| **Docker** | Installed |
| **git, curl, jq, make** | Base packages |
| **Workspace** | `~/dev/` — short clean paths |

## Credentials

All secrets live in **1Password** (vault: `GHA`). The only thing in GitHub is a single `OP_SERVICE_ACCOUNT_TOKEN` secret.

## Repo structure

```
├── AGENTS.md              ← portable agent rules
├── ansible/
│   ├── playbook.yml       ← provision + configure
│   ├── requirements.yml   ← Ansible collections
│   └── roles/
│       ├── base/          ← system packages, dev user, workspace
│       ├── gh-cli/        ← install gh, GitHub App auth
│       ├── yc-cli/        ← install yc, SA key auth
│       ├── docker/        ← install docker
│       └── hermes-cli/    ← install hermes, OpenRouter config
└── .github/workflows/
    └── deploy-vm.yml      ← 1Password → Ansible → Vultr
```
