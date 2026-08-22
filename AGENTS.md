# agent-rig — Agent Rules

## What this repo is

Public repo for agent-rig — a provisioned Vultr dev VM with pre-configured agent tools.

## Layout

- `agent/` — Hermes config that syncs to `~/.hermes/` on the VM
- `ansible/` — VM provisioning and tool configuration

## Agent rules

- **Workspace is `~/dev/`** — clone all repos there. Short paths only.
- **Config in `agent/`** — pull from public repo, heartbeat PR back changes
- **Memories in `agent-rig-data` (private)** — push/pull MEMORY.md + USER.md
- **No secrets in any repo** — everything from 1Password at deploy time
- GitHub App `pipo-robot` handles repo access
- **PR → review → merge** — never push to main directly
- Run `ansible-lint` before committing playbook changes
- Test syntax: `ansible-playbook --syntax-check ansible/playbook.yml`

## How to work here

1. Edit `agent/hermes.yaml` to change agent config
2. Edit `agent/SOUL.md` to change agent identity
3. Edit `agent/skills/` to change skills
4. Edit `ansible/` to change infra
5. Push → PR → merge → VM updates via sync
