---
name: dev-workflow
description: >
  Workflow for developing and deploying the agent-rig VM itself.
  Use when working on the provisioning, tools, or config of the rig.
---

# agent-rig Dev Workflow

## Structure

- `ansible/` — VM provisioning and tool configuration
- `config/` — Hermes config.yaml + SOUL.md (my identity)
- `skills/` — Custom skills installed on the VM
- `.github/workflows/` — CI/CD pipeline

## How to work

1. **Config changes** → edit `config/hermes.yaml`, push, PR
2. **Tool changes** → edit `ansible/roles/<tool>/tasks/main.yml`
3. **New tools** → create new role under `ansible/roles/`
4. **My identity** → edit `config/SOUL.md`
5. **Deploy** → merge PR, GH Actions runs the workflow

## Rules

- All secrets come from 1Password vault `agent-rig`
- GitHub App `pipo-robot` handles repo access
- `evn` file is NEVER in the repo
- `hermes doctor` to verify after changes

## Common commands

```bash
# Syntax check playbook
ansible-playbook --syntax-check ansible/playbook.yml

# List installed Hermes skills
hermes skills list
```
