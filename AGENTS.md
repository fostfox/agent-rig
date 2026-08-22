# agent-rig — Agent Rules

## What this repo is

Deploys a dev VM on Vultr with pre-configured LLM agent tools. Everything is code — destroy and recreate at will.

## Layout

- `ansible/` — Playbook + roles for VM provisioning and configuration
- `.github/workflows/` — Deploy pipeline triggered by push to main

## Agent rules

- **Workspace is `~/dev/`** — clone all repos there. Short paths only.
- **Config in `agent-rig` (public)** — pull for config, SOUL, skills updates
- **Memories in `agent-rig-data` (private)** — push/pull MEMORY.md + USER.md
- **No secrets in any repo** — everything from 1Password at deploy time
- GitHub App `pipo-robot` handles repo access
- **PR → review → merge** — never push to main directly
- Run `ansible-lint` before committing playbook changes
- Test syntax: `ansible-playbook --syntax-check ansible/playbook.yml`

## How to work here

1. Edit `ansible/roles/<tool>/tasks/main.yml` to change tool setup
2. Add new tool → create a new role in `ansible/roles/`
3. Push → GH Actions deploys the updated VM
4. SSH into the VM to verify
