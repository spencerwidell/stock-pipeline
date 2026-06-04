# Project Decisions

A record of choices made and why — so future sessions don't
relitigate settled questions.

---

## Environment

**WSL over plain Windows terminal**
Chose WSL because all DS tooling, cloud servers, Docker, and
interview expectations assume Unix/Linux bash. PowerShell commands
don't transfer. One-time setup cost, permanent payoff.

**Ubuntu app to open terminal, not `wsl` from PowerShell**
The `wsl` command starts a non-login shell that doesn't fully
load `.bashrc`, so conda doesn't activate. Ubuntu app starts
a login shell — consistent, correct every time.

**Miniconda over Anaconda**
Anaconda bundles ~3GB of packages, most of which we don't need.
Miniconda is ~150MB and installs only what you explicitly ask for.
Keeps the environment clean and intentional.

## Project structure

**Projects live on the Linux side (`/home/datasci/projects/`)**
Not on the Windows side (`/mnt/c/...`). Linux filesystem
performance in WSL is significantly faster for file-heavy
operations like reading Parquet. Keep all active project
work here.

**One conda environment per project (`stock`)**
Never install project packages into `base`. Isolated environments
prevent dependency conflicts and make projects reproducible.
`environment.yml` (to be added) will let anyone recreate it.

## Git / GitHub

**HTTPS over SSH for GitHub remote**
Simpler setup for a learning environment. SSH would require
key generation and GitHub configuration. HTTPS with credential
store achieves the same result with less setup friction.
Can migrate to SSH later if needed.

**Credential store for authentication**
`git config --global credential.helper store` saves the PAT
token to disk after first use. Fine for a personal machine.
On a shared or production machine, use a more secure helper.

**Public repository**
Project is a learning portfolio piece targeting a lead DS role.
Public visibility is intentional — it's the point.

## Security

**API keys in `.env`, never in code**
`.env` file holds `POLYGON_API_KEY=...` and is listed in
`.gitignore` so Git never sees it. Script reads key into memory
at runtime. This pattern applies to all secrets: API keys,
tokens, passwords, connection strings.

**Personal Access Token for GitHub**
GitHub deprecated password auth for Git operations in 2021.
PAT generated with `repo` scope only — minimum permissions
needed. Stored via credential helper after first use.

---
## AI Tooling

**Claude Code over GitHub Copilot (for now)**
Already included in Max $200/month plan — no additional cost.
Runs in WSL terminal, aligns with CLI learning goals, supports
agentic workflows. VS Code extension also included. Will
reassess Copilot if inline autocomplete becomes a felt need
after several sessions with Claude Code.

---

*Add new decisions here as the project evolves.*
