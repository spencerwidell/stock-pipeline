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

## Session 2 — June 4, 2026

### What we accomplished

**Claude Code installation (tooling)**
- Installed Claude Code as a CLI tool to run agentic workflows
  directly in the WSL terminal
- Confirmed it runs inside the Ubuntu/WSL environment, aligning
  with the CLI-first learning goals
- Decision rationale already captured in DECISIONS.md (Claude Code
  over Copilot — included in the Max plan, no extra cost)

**Node.js setup (tooling prerequisite)**
- Installed Node.js + npm — Claude Code is distributed as an npm
  package, so Node is a prerequisite
- Verified the install with `node --version` and `npm --version`

**npm global prefix fix (troubleshooting)**
- A global `npm install -g` initially failed with a permissions
  error — npm's default global prefix pointed at a system path
  that a normal user can't write to
- Fixed it the correct way (no `sudo` for npm): pointed the global
  prefix at a user-owned directory with
  `npm config set prefix ~/.npm-global`
- Added `~/.npm-global/bin` to `PATH` in `.bashrc` so globally
  installed CLIs (like `claude`) are found on the command line
- Lesson: never `sudo npm install -g` — it scatters root-owned
  files into your home and causes more permission problems later

**sudo password reset (troubleshooting)**
- Hit a wall where the WSL user's `sudo` password was unknown
- Reset it from an elevated WSL root shell launched from Windows
  PowerShell: `wsl -d Ubuntu -u root`, then `passwd datasci`
- Lesson: the WSL user password is separate from the Windows
  account password — and root access via `-u root` is the recovery
  path when it's lost

**Expanded fetch_stock.py (Module 5)**
- Rewrote the script to pull 15 tickers in one run: AMZN, NVDA,
  MSFT, META, TSLA, ELF, CELH, PLTR, AVGO, SOFI, TSM, NOW, IBM,
  CRM, ORCL
- Switched endpoint from `/prev` (one day only) to the aggregates
  `/range/1/day` endpoint to pull the last 30 calendar days
- Looped over all tickers, reshaped Polygon's short keys
  (t/o/h/l/c/v) into clean named columns, collected into one list
- Confirmed Developer (paid) tier has unlimited API calls — removed
  the free-tier rate-limit `time.sleep()` so tickers fetch
  back-to-back
- Kept the `.env` pattern for the API key; hardened the loader to
  skip blank/comment lines

**First Parquet output (Module 5)**
- Built a single tidy DataFrame (one row per ticker-date) and wrote
  it with `df.to_parquet(..., engine="pyarrow")`
- Created the `data/` directory from Python with
  `os.makedirs("data", exist_ok=True)`
- Added `data/` to `.gitignore` — generated data shouldn't be
  committed
- Verified the result: **330 rows** (15 tickers × 22 trading days),
  date range 2026-05-05 → 2026-06-04, file only 16K on disk
- Confirmed schema: `ticker` (string), `date` (datetime64),
  OHLCV (float64) — types preserved, dates stored as real dates

### Commands used this session
```bash
node --version, npm --version       # verify Node/npm install
npm config get prefix               # see where globals install
npm config set prefix ~/.npm-global # point globals at user dir
npm install -g @anthropic-ai/claude-code  # install Claude Code
wsl -d Ubuntu -u root               # root shell (from PowerShell)
passwd datasci                      # reset WSL user password
conda activate stock                # activate environment
python fetch_stock.py               # run the expanded script
ls -lah data/                       # inspect the output file
git status                          # check working tree
```

### Key concepts learned
- Claude Code ships as an npm package — Node is a prerequisite
- npm's global prefix should live in a user-owned directory; fixing
  it removes the temptation to `sudo npm install -g`
- A CLI installed globally is only callable if its `bin` directory
  is on your `PATH`
- The WSL user password is independent of the Windows password;
  `wsl -u root` is the recovery hatch
- The Polygon `/range/1/day` endpoint returns one bar per trading
  day — weekends/holidays simply don't appear (22 days, not 30)
- Paid API tiers lift the request-rate limit — no `sleep` needed
- Parquet is columnar + compressed: 330 rows fit in 16K and types
  survive the round-trip (unlike CSV, which stores everything as text)
- "Tidy" long format (one row per ticker-date) extends to more
  tickers without changing the schema

### Mistakes made and what they taught
| Problem | What happened | Lesson |
|---|---|---|
| `npm install -g` permission error | Global prefix pointed at a system path | Set prefix to `~/.npm-global` — never `sudo` npm |
| Global CLI "command not found" | `bin` dir wasn't on `PATH` | Add the prefix `bin` to `PATH` in `.bashrc` |
| Unknown `sudo` password | WSL password forgotten | Reset via `wsl -u root` + `passwd` — it's separate from Windows |
| volume came back as `float64` | pandas inferred type from JSON | Whole-number columns can be cast to `int64` in cleanup |

---

## Session 3 — (upcoming)

### Plan
- Inspect Parquet and data files from the terminal *without* loading
  them into Python:
  - `find` — locate data files by name/pattern across the tree
  - `du` — measure file and directory sizes on disk
  - `wc` — count lines/words/bytes
- Run the fetch script as a background job with `nohup` so it keeps
  running after the terminal closes; redirect output to a log file
  and check on it later
- (Stretch) cast `volume` to `int64` during the cleanup step

### Starting checklist
- [ ] Open Ubuntu app (not PowerShell)
- [ ] `cd ~/projects/stock-pipeline`
- [ ] `conda activate stock`
- [ ] `git status` — confirm clean working tree
- [ ] Read bottom of this file for where we left off

---
