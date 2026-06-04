# Session Log — Stock Pipeline Project

---

## Session 1 — June 3, 2026

### What we accomplished

**Environment setup (Module 1 + 2)**
- Confirmed WSL (Ubuntu 22.04.3 LTS) was already installed
- Established that Ubuntu app is the correct way to open the terminal
  (not via `wsl` from PowerShell — login shell difference)
- Learned to read `ls -lah` output: permissions, link counts,
  file sizes, hidden files, symbolic links
- Understood the two homes: `/home/datasci` (Linux) and
  `/mnt/c/Users/swdat` (Windows C: drive viewed from Linux)
- Installed Miniconda 26.3.2, accepted conda Terms of Service,
  created `stock` environment with Python 3.11

**Project structure (Module 1)**
- Created `/home/datasci/projects/stock-pipeline/`
- Understood why projects live on the Linux side, not Windows side

**Git setup (Module 3)**
- Configured Git identity in WSL (separate from Windows Git Bash)
- Learned that WSL and Windows Git are two separate installations
  with separate configs
- Initialized repo, renamed branch master → main
- Set `init.defaultBranch = main` globally

**First commit cycle (Module 3)**
- Created README.md using `echo` and `>` redirect
- Staged with `git add`, committed with `git commit -m`
- Understood the three states: untracked → staged → committed
- Read `git log --oneline` and understood HEAD

**GitHub connection (Module 3)**
- Created public repo at github.com/spencerwidell/stock-pipeline
- Added remote with `git remote add origin <url>`
- Resolved GitHub password auth deprecation — generated PAT token
- Set up credential store so future pushes require no login

**Python environment (Module 2)**
- Installed requests, pandas, pyarrow into `stock` environment
- Understood pip installs into the *active* environment only
- Used `pip list | grep` — first real pipe command

**First working script**
- Created `fetch_stock.py` — calls Polygon.io previous-close endpoint
- Protected API key with `.env` file and `.gitignore`
- Verified `.env` is invisible to `git status`
- Fixed Unix timestamp (milliseconds) to human-readable date
- Got live AAPL price data back: Status 200, real OHLCV values

**Documentation structure**
- Created `docs/` folder with SESSION_LOG, DECISIONS, PROMPT files
- Established workflow pattern for multi-session project

### Commands used this session
```bash
pwd, ls, ls -lah, cd, mkdir         # navigation
echo "text" > file                  # create file
echo "text" >> file                 # append to file
cat file                            # read file
git init, git status                # repo setup
git add, git commit -m              # commit cycle
git remote add, git push -u         # connect to GitHub
git log --oneline                   # view history
git branch -m main                  # rename branch
git config --global ...             # set identity
conda create -n stock python=3.11   # create environment
conda activate stock                # activate environment
conda env list                      # list environments
pip install requests pandas pyarrow # install packages
pip list | grep -E "..."            # filter package list
python fetch_stock.py               # run script
```

### Key concepts learned
- Hidden files start with `.` — only visible with `ls -a` or `ls -lah`
- Silence after a command means success on Linux
- The prompt tells you two things always: where you are (`~/projects/...`)
  and which environment is active (`(stock)`)
- `>` overwrites, `>>` appends — never mix these up on important files
- Git stages changes before committing — the tray-before-photo model
- `.gitignore` makes files invisible to Git entirely — not just ignored
- API keys never go in code — `.env` + `.gitignore` is the pattern
- Unix timestamps are milliseconds since Jan 1 1970 — divide by 1000

### Mistakes made and what they taught
| Typo / mistake | Error message | Lesson |
|---|---|---|
| `ls lah` | `cannot access 'lah'` | Dash makes it a flag, not a filename |
| `git comfig` | `did you mean config?` | Git suggests corrections — read the error |
| `git log --online` | `unrecognized argument` | Double-check flag spelling |
| `wsl` from PowerShell | No `(base)` prefix | Login shell vs non-login shell difference |

---

## Session 2 — (upcoming)

### Plan
- Save API data as Parquet file (Module 5)
- Pull multiple tickers into a single DataFrame
- Inspect Parquet files from the terminal without loading into Python
- Use `find`, `du`, `wc` on real data files
- Commit the expanded script

### Starting checklist
- [ ] Open Ubuntu app (not PowerShell)
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `conda activate stock`
- [ ] `git status` — confirm clean working tree
- [ ] Read bottom of this file for where we left off

---
