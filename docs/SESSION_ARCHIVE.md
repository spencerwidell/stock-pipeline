# Session Archive

Full history for sessions 1-24 — preserved for portfolio reference.
See SESSION_LOG.md for recent sessions (25 onward).

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

## Session 3 — June 5, 2026

### What we accomplished

**Terminal inspection of Parquet files (Module 6)**
- Learned to inspect binary data files *without* loading them into Python
- `ls -lah data/` — see file sizes in human-readable format (16K)
- `find data/ -name "*.parquet"` — locate files by pattern across
  the directory tree
- `du -h data/` — measure directory size on disk (20K including overhead)
- `wc -l fetch_stock.py` — count lines in script files
- `df -h .` — check available disk space on the filesystem
- Used pyarrow to read Parquet schema and metadata *without* loading
  the full dataset — `pq.read_schema()` and `pq.ParquetFile().metadata`
  show row count (330), column types, compression codec, all without
  materializing the data

**Background job pattern with nohup (Module 7)**
- Learned to run long scripts in the background with `nohup` so they
  survive terminal closure
- Pattern: `nohup python script.py > logfile.log 2>&1 &`
- The `LOGFILE` variable trick: define once at the top, use throughout
  the script — makes log redirection cleaner
- `tail -f logs/fetch.log` — monitor a growing log file in real time
- Understood that live scrolling with `tail -f` will be experienced
  organically on a future long-running job (not forced today)

**The find -exec pattern (Module 6)**
- `find data/ -name "*.parquet" -exec ls -lh {} \;` — run a command
  on each found file
- The `{}` placeholder represents the matched filename
- The `\;` terminates the `-exec` action
- Combines search and action in one command

### Commands used this session
```bash
ls -lah data/                        # human-readable file sizes
find data/ -name "*.parquet"         # locate files by pattern
du -h data/                          # directory size on disk
wc -l fetch_stock.py                 # count lines in a file
df -h .                              # filesystem disk usage
find ... -exec ls -lh {} \;          # find + execute on matches
nohup python script.py > log 2>&1 &  # background job with logging
tail -f logs/fetch.log               # live log monitoring
```

### Key concepts learned
- Binary files like Parquet can't be inspected with `cat` — use
  dedicated tools like pyarrow to read metadata/schema
- `find` is the search tool for locating files by name, type, or age
- `du` measures actual disk usage (includes overhead), `ls -lah` shows
  file size only
- `wc -l` counts newlines — useful for quick script size checks
- `nohup` keeps a process running after logout; `&` backgrounds it
- `> logfile.log 2>&1` redirects both stdout and stderr to one log
- `tail -f` follows a growing file — perfect for watching logs live
- The `LOGFILE` variable pattern centralizes the log path in scripts
- `find -exec` combines search and action — no need for a separate loop

### Mistakes made and what they taught
| Problem | What happened | Lesson |
|---|---|---|
| Tried `cat` on Parquet file | Binary garbage printed to screen | Binary files need format-aware readers |
| Forgot `\;` on `-exec` | Syntax error from `find` | `-exec` needs explicit terminator |
| Ran long script in foreground | Terminal stuck waiting | Use `nohup ... &` for long jobs |

---

## Session 4 — June 5, 2026 (afternoon)

### What we accomplished

**Created RESEARCH_ROADMAP.md (documentation)**
- Documented the full research vision: production-grade research
  platform built from first principles
- Captured the five-layer analytical stack:
  1. Deterministic/Rule-Based (VSA bar classification)
  2. Statistical/Probabilistic (correlation, hypothesis testing)
  3. Machine Learning (sequence models, phase detection)
  4. LLM Augmentation (contextual analysis)
  5. Production Infrastructure (backtesting, monitoring)
- Explained the VSA → Wyckoff progression and why we start with
  bar-by-bar features before phase detection
- Listed the open research questions we plan to answer empirically
- Documented the session arc (Sessions 4-16+) with corrected tooling:
  DuckDB instead of PostgreSQL

**Updated DECISIONS.md (documentation)**
- Added the DuckDB choice: embedded, no server, queries Parquet
  directly, perfect for single-user research
- Documented the VSA-before-Wyckoff decision and linked to the
  RESEARCH_ROADMAP for the full rationale
- Clarified that Parquet + DuckDB means no ETL step — query files
  directly with SQL

**Updated SESSION_LOG.md (this file)**
- Recorded Session 4 accomplishments
- Updated Session 5+ plan to align with the corrected roadmap

### Key concepts learned
- Research documentation serves two purposes: align on vision at the
  start, and provide context for future sessions when the project
  spans weeks/months
- The analytical stack is a ladder: each rung must hold weight before
  you step to the next. Deterministic → statistical → ML → LLM is
  not arbitrary; it's the empirical testing sequence.
- DuckDB eliminates the server/client model — it's SQLite for analytics
- Tool choices should match the environment: embedded database for
  single-user research, client-server for multi-user production

---
---

## Session 5 — June 6, 2026

### What we accomplished

**Shell scripting (Module 6)**
- Created `scripts/` directory to house operational scripts
- Built `morning_startup.sh`:
  - Sources conda explicitly for non-interactive shells
  - Activates the `stock` environment
  - Guards against missing `data/` directory with loud error + exit 1
  - Pulls latest from GitHub with --rebase
  - Reports disk space with df -h
- Built `run_pipeline.sh`:
  - Uses `cd "$(dirname "$0")/.."` to always run from project root
  - Creates timestamped log file so runs never overwrite each other
  - Launches fetch_stock.py with nohup in the background
  - Reports PID and tail command for live monitoring
- Made both scripts executable with `chmod +x` (stored in Git as mode 100755)
- Added `logs/` to `.gitignore` — generated output, not source

### Commands used this session
mkdir, touch, nano                        # create and edit files
chmod +x script.sh                        # make executable
ls -lah script.sh                         # verify permissions
./script.sh                               # run a script
cat script.sh                             # verify file contents
conda info --base                         # find conda install path
echo "logs/" >> .gitignore               # append to gitignore
git add, git commit, git push             # commit cycle

### Key concepts learned
- Non-interactive shells don't source .bashrc — conda needs
  `source /path/to/conda.sh` explicitly inside scripts
- `set -euo pipefail` stops a script immediately on any error
  instead of blundering forward — caught the conda failure cleanly
- Working directory follows the caller, not the script —
  `cd "$(dirname "$0")/.."` fixes this robustly
- `chmod +x` is a one-time operation stored in file metadata;
  Git records it as mode 100755
- Timestamped log filenames (`date +%Y%m%d_%H%M`) prevent
  consecutive runs from overwriting each other's logs
- `$!` captures the PID of the last backgrounded process

### Mistakes made and what they taught
| Problem | What happened | Lesson |
|---|---|---|
| `conda activate` failed in script | Non-interactive shell, no .bashrc | Source conda.sh explicitly |
| Log file not found after cd fix | Paths still used `../` after cd to root | After cd, all paths are relative to new location |

---

---

## Session 6 — June 6, 2026

### What we accomplished

**DuckDB installation and first queries (research stack)**
- Installed DuckDB 1.5.3 into the `stock` conda environment
- Learned that DuckDB has no CLI entry point via `python -m` —
  used Python interactive shell instead
- Queried `data/stock_ohlcv.parquet` directly with SQL — no pandas
  load, no ETL step, file stays on disk
- Ran three analytical queries:
  - Top 5 single-day closes (META dominated)
  - Average close by ticker over the period (META → SOFI range)
  - Top 10 daily returns by (close - open) / open
- Noticed May 28-29 appeared across multiple tickers in the daily
  returns — correlated market move, worth investigating in VSA work
- Built `analyze.py` — reusable script wrapping all three queries
  with a helper function to print clean output without row index

### Commands used this session
```bash
pip install duckdb                   # install DuckDB
python                               # open Python interactive shell
git add, git commit, git push        # commit cycle
nano docs/SESSION_LOG.md             # update session log
```

### Key concepts learned
- DuckDB queries Parquet files directly with SQL — the file path
  goes in the FROM clause as a string literal
- No ETL step needed: DuckDB + Parquet is the full analytics stack
  for single-user research
- Calculated columns (daily return %) are computed in the query,
  not in Python — keeps the script clean
- `Alt+U` is undo in nano (M = Meta = Alt key)
- `to_string(index=False)` removes pandas row numbers from printed output

### Mistakes made and what they taught
| Problem | What happened | Lesson |
|---|---|---|
| `python -m duckdb` failed | No __main__ module in duckdb package | Use `python` shell and import duckdb directly |
| `print(results)` NameError | Typo — variable was named `result` | Read the error message — Python told you exactly what was wrong |

---

cat >> docs/SESSION_ARCHIVE.md << 'EOF'

---

## Session 7 — June 6, 2026

**Built:** `vsa_features.py` — first analytical layer
- `direction` (up/down), `spread` (high-low), `rel_volume` (vol/10d ma)
- Saved to `data/stock_vsa.parquet`

**Key findings:** IBM May 21 3.18x volume up bar, May 29 cluster
across multiple tickers, SOFI effort with no result.

**Concepts:** groupby().transform(), wide spread + high volume =
significant bar, high volume + narrow spread = supply absorbing demand
EOF

---

## Session 12 — June 7, 2026

**Combined signal test:** inconclusive + buying_climax + mixed = +11.53%
**Stress test revealed 2022 artifact** — signal negative in all other years
**Key lesson:** Always stress test headline results by year/regime

---

---

## Session 13 — June 7, 2026

**Expanded universe:** 15 → 21 tickers (added SPY, QQQ, JPM, PG, XOM, GLD)

**buying_climax by segment (5-day return):**
- tech/growth: +3.11% (501 bars)
- value/defensive: +0.73% (86 bars)
- market ETFs: -0.01% (30 bars)

**buying_climax by segment and year:**
- 2022 outlier (+17.20%) is entirely in tech/growth — rate-hike snapbacks
- Value/defensive is MORE CONSISTENT: positive in 5 of 7 years,
  clustering +1.25% to +1.79%, no massive outlier
- Market ETFs: no signal, useful as benchmark

**Key findings:**
- VSA buying_climax is a stock-selection signal, not market-timing
- Tech/growth: high magnitude, regime-dependent, 2022-driven
- Value/defensive: lower magnitude, more consistent across regimes
- Market ETFs confirm: signal doesn't work on broad indices

**Research insight:** Consistency often more valuable than magnitude
in a trading system. Value/defensive buying_climax may be more
practically useful than tech despite lower average return.

---

---

## Session 14 — June 7, 2026

**Widell Line validation across segments:**

| Segment | Up | Inconclusive | Down | Spread |
|---|---|---|---|---|
| Tech/Growth | +2.38% | +0.95% | -0.83% | 3.21% |
| Value/Defensive | +1.17% | +0.23% | -0.44% | 1.61% |
| Market ETFs | +0.65% | +0.34% | -0.33% | 0.98% |

**Key finding:** Widell Line is a universal framework — up > inconclusive
> down ordering holds across all three segments. Signal strength scales
with volatility. Tech produces the widest spread, market ETFs the narrowest.

**Implication:** Framework is valid as a general tool. Threshold
calibration may need to be segment-specific. A composite score could
weight signals by segment volatility.

---

---

## Session 15 — June 7, 2026

**Built:** `composite_score.py` — additive signal scoring
- score_wl: wl_state mapped to +2/0/-2
- score_flip: flip direction +1/-1/0
- score_vsa: vsa_label mapped to +2 to -2
- score_regime: bull/mixed/bear mapped to +1/0/-1
- composite: sum of all four, range -6 to +6

**Score vs 5-day return:**
- Score 2+: consistently +1.47% to +2.15%
- Score -3 and below: negative to flat
- Middle zone (-1 to +1): noisy, no clear edge

**Score by segment:**
| Segment | High (2+) | Neutral | Low (-3) | Spread |
|---|---|---|---|---|
| Tech/Growth | +2.16% | +0.85% | -0.63% | 2.79% |
| Value/Defensive | +0.99% | +0.20% | -0.18% | 1.17% |
| Market ETFs | +0.49% | +0.33% | +0.21% | 0.28% |

**Key finding:** Composite score is universal — high beats neutral
beats low in every segment. Spread scales with volatility.
Market ETFs insufficient spread to be actionable.

**Layer 2 complete:** Features built in Layer 1 have measurable,
consistent predictive power across segments and regimes.
Green light to begin ML layer.

---

---

## Session 16 — June 7, 2026

**Built:** `ml_classifier.py` and `ml_feature_test.py`
- RandomForest with TimeSeriesSplit (5 folds)
- MLflow experiment tracking (widell_vsa_classifier, widell_feature_isolation)
- Feature isolation test: MA only, VSA only, Widell only, all features

**Baselines established:**
- Always predict "up": 0.443 (most common class = 44.3% of bars)
- Random baseline: 0.363

**Feature isolation results:**
- All features:  0.362 — at random baseline
- MA only:       0.332 — below random
- Widell only:   0.331 — below random
- VSA only:      0.317 — worst of all

**The VSA chapter is closed.**
No feature set beats naive baseline. VSA labels are the weakest
feature set tested. Adding all features together barely reaches random.

**The gap between DuckDB and ML findings:**
DuckDB showed real average differences (Widell up = +2.38%).
ML cannot classify individual bars reliably because variance is too
high. These signals work as filters that shift average outcomes,
not as classifiers for individual bar prediction. This is a
meaningful distinction for practical use.

**Research pivot confirmed:**
Signals are useful as overlays and filters in a rules-based system.
ML classification of individual bars is not the right application.
The Widell Line + regime framework is the original contribution.
VSA labels are background context, not primary signal.

**Next focus — what IS working:**
- Widell Line state separation is real and consistent
- Regime-conditional signals shift averages meaningfully
- Composite scoring as a filter (score 2+ vs score -3 and below)
- These work as portfolio filters, not trade-by-trade classifiers

---

---

## Session 17 — June 8, 2026

**VSA sequence test — consecutive labels:**
- buying_climax 2 consecutive: -0.48% (59 bars) — signal reverses
- no_supply 2 consecutive: +0.89% — marginal improvement
- 3-consecutive samples too small to trust (6 bars max)
- Conclusion: consecutive labels don't strengthen VSA signal

**VSA weekly bar test — 4 week forward returns:**
- All labels positive (1.17% to 3.13%)
- No theoretical ordering — effort_down nearly matches effort_up
- Market upward drift swamps all label differences
- Conclusion: weekly VSA shows drift, not signal

**VSA chapter fully closed.**
Tested across: daily next-day, daily 5-10 day, daily consecutive
sequence, weekly 4-week. No consistent standalone predictive signal
found across timeframes or methods.

**The pivot:**
VSA served as scaffolding that led to the Widell Line — which shows
consistent, theoretically ordered signal separation. The original
contribution of this project is the Widell Line framework, not VSA.

---

---

## Session 18 — June 8, 2026

**Built:** New features in vsa_features.py, ml_alpha_test.py

**New features added:**
- close_pos: where in the bar did price close (0=low, 1=high)
- upper_wick, lower_wick: rejection ratios
- effort: rel_spread * rel_volume combined
- roc_20: 20-day rate of change (momentum)
- dist_52w_high, dist_52w_low: distance from 52-week extremes

**Widell Line parameter optimization (widell_optimize.py):**
- Tested N=2,3,5,7,10 swing window
- N=3 confirmed as optimal — spread collapses at N=5
- Original parameter choice empirically validated

**ML alpha target test (SPY-relative outperformance):**
- Switching from raw return to alpha removed market drift
- Naive baseline dropped from 0.443 to 0.368
- Results:
  - widell_only:    0.352 (below naive)
  - new_features:   0.400 (beats naive by +0.032)
  - widell_plus_new: 0.412 (beats naive by +0.044)
  - all_features:   0.410

**First time beating naive baseline.**

**Feature importances:**
- dist_52w_high: 24.9% — dominant predictor
- dist_52w_low:  21.4%
- ma200_slope:   13.2%
- dist_ma200:    12.4%
- roc_20:         8.1%
- vsa_encoded:    0.08% — confirmed irrelevant
- score_vsa:      0.11% — confirmed irrelevant

**Key finding:** 52-week distance features dominate. Stocks near
52-week lows recovering outperform; stocks near highs consolidate.
The Widell Line adds 3-4% importance — modest but real contribution.
VSA labels confirmed irrelevant in ML context.

---

---

## Session 19 — June 8, 2026

**Built:** ml_xgboost.py, ml_tune.py, ml_optuna.py, tests/test_pipeline.py

**XGBoost vs Random Forest (GPU, alpha target):**
- RandomForest: 0.408
- XGBoost GPU:  0.413 — marginal improvement
- XGBoost feature importances shifted: wl_encoded now #1 at 11.3%
  vs buried in Random Forest. Gradient boosting finds Widell Line
  interactions that Random Forest misses.

**Hyperparameter tuning:**
- Manual grid search: best 0.413 (depth=4, lr=0.05)
- Optuna 50 trials: best 0.417 (depth=4, lr=0.046, n_est=337)
- Marginal gain — likely near ceiling for this feature set/dataset

**GPU enabled:** RTX 4090 confirmed working with XGBoost device=cuda
Each Optuna trial ~7 seconds vs minutes on CPU.

**MLflow UI:** Running at localhost:5000, 5 experiments tracked.
All runs logged with parameters, metrics, and model artifacts.

**Test suite:** 20 pytest tests, all passing in 0.31 seconds.
Covers: data integrity, feature ranges, regime values, VSA labels,
Widell Line state separation, pipeline consistency.

**Key insight:** We are near the ceiling at 0.417 with this feature
set. To improve meaningfully need either:
1. More training data (expand universe further)
2. New feature types (options flow, sentiment, fundamentals)
3. Different model architecture (sequence model for temporal patterns)

---

---

## Session 20 — June 8, 2026

**Built:** ml_lstm.py, sequence features, updated README and DECISIONS

**Sequence features added to composite_score.py:**
- rsi_trend: RSI change over 5 bars
- composite_trend: composite score change over 5 bars
- momentum_5: 5-bar price return
- wl_duration: consecutive bars in current Widell state

**LSTM results:**
- Accuracy: 0.412 — identical to XGBoost
- Sequence model does not outperform gradient boosting
- Daily OHLCV patterns not complex enough to justify LSTM overhead
- XGBoost + engineered sequence features captures same information

**ML ceiling confirmed at ~0.417**
All models cluster 0.408-0.417. Further gains require new data types.

**Documentation updated:**
- README.md: full project overview with all findings
- DECISIONS.md: complete record of all architectural choices

---

---

## Session 21 — June 8, 2026

**Built:** run_checks.sh, daily_signals.py, updated RESEARCH_ROADMAP

**run_checks.sh:**
- Runs full pytest suite (20 tests)
- Reports data freshness (latest date, ticker count, row count)
- Run after conda activate stock each morning

**daily_signals.py:**
- Shows current Widell Line state for all 21 tickers
- Includes regime, composite score, RSI, 52w distance, VSA label
- Highlights flips with lightning bolt
- Summary: universe state counts, high/low score counts
- Today's reading: 8 flips, 1 up, 12 inconclusive, 8 down
  QQQ and SPY selling climax — broad market move confirmed

**RESEARCH_ROADMAP.md fully updated:**
- All 8 empirical findings documented
- Widell Line contribution formalized
- Session arc updated through Session 21
- Upcoming sessions: backtesting, universe expansion, LLM

---

---

## Session 22 — June 8, 2026

**Built:** backtest.py, backtest_v2.py, backtest_v3.py, sector_map.py
Fixed META data corruption (FB/META ticker stitch)

**META data fix:**
Polygon's META ticker contained wrong historical prices (~$15 vs ~$340).
Root cause: different company previously traded as META.
Fix: fetch FB (pre Oct 2021) + META (post Oct 2021), stitch together.
First close now correctly $236.73 in June 2020.

**Backtest V3 — apples to apples (same 15 names):**
System avg: 241.4% vs Buy-and-hold avg: 222.2%
System wins by +19.2% including NVDA/AVGO generational outliers.

**Excluding NVDA and AVGO (generational AI plays):**
System avg: 202.3% vs Buy-and-hold avg: 107.9%
System edge: +94.4 percentage points
System beats BAH: 9/13 names

**Key insight — system value varies by stock type:**
- Volatile growth (PLTR, ELF, CELH, META): system adds significant value
- Steady compounders (MSFT, ORCL, IBM, TSM): BAH wins, system times poorly
- Losers/turnarounds (SOFI, CRM): system protects by reducing exposure
- Generational trends (NVDA, AVGO): just hold, don't time

**Portfolio framework:**
- High conviction secular trends: hold, use system only for breakdown alerts
- Volatile growth names: use Widell Line for entry timing and sizing
- Value/turnaround plays: system entry signals add real value

**Top-down filter added:** sector_map.py maps each stock to its
parent sector ETF and broad market ETF for top-down confirmation.

---

---

## Session 23 — June 8, 2026

**Universe expansion:** 32 → 88 tickers
Added full watchlist: AXON, PANW, SNOW, MU, ASML, GOOG, NFLX,
BKNG, AMD, AAPL, FCX, COST, CAT, CMI, CVX, MELI, ZS, CRWD,
ALAB, BIDU, ANET, CDNS, APP, ISRG, VRT, NXE, SMR, CRDO, CEG,
DVN, RTX, NBIS, LITE, GEV, ARM, GLW, PWR, LRCX, AMAT, ONDS,
RKLB, ASTS, RGTI, QBTS, IONQ, SERV, UEC, CCJ, URG, LEU, CRWV,
ZETA, HOOD, MSTR, FANG, MELI, BE, and others.
ALOY, XE, SLVR, RNRK, USAR not found on Polygon.

**Gap features added to vsa_features.py:**
- gap_pct: overnight gap as % of prior close
- gap_volume: gap_pct * rel_volume (conviction gap)
- day_of_week, is_friday: for Friday close signal testing

**Data quality fix:**
- Filter bars with volume < 1000 (NXE bad data row removed)
- Test updated to reflect improved data quality

**Daily signals with full universe — key observations:**
- ASML, CAT: 🟢 up, score +4, flipped today — strong entries
- AMAT: 🟢 up, score +3 — established semiconductor equipment strength
- AAPL: 🔴 down, score -3, flip today — largest company breaking down
- BKNG: 🔴 down, score -4, flip today — consumer discretionary warning
- Uranium basket mixed: CCJ/URG holding, LEU/UEC breaking down
- SPY/QQQ inconclusive bull +1 — market in holding pattern

**Watchlist philosophy confirmed:**
System most valuable for screening opportunities before buying.
Prevents falling knife purchases by requiring confirmed entry signal.
PLTR example: bear/inconclusive/negative composite = wait, not buy.

---

---

## Session 24 — June 8, 2026

**Built:** run_daily.sh, dashboard.py, requirements.txt, environment.yml

**run_daily.sh — full pipeline automation:**
- Fetches data, runs all feature scripts, tests, generates signals
- Runs end to end in ~52 seconds
- Logs to logs/daily_YYYYMMDD_HHMM.log

**Cron job scheduled:**
- 30 13 * * 1-5 (1:30 PM Phoenix / 4:30 PM Eastern, weekdays)
- Cron already running since June 6
- WSL limitation: laptop must be on for cron to fire
- Cloud VM is the production solution (upcoming)

**Environment captured:**
- requirements.txt: 131 packages, exact versions
- environment.yml: full conda environment snapshot

**Streamlit dashboard — dashboard.py:**
- Tab 1: Signals — live signal table with color coding
  - Summary metrics (up/inconclusive/down/flips/high score)
  - Flips today section with action items
  - Filterable full universe table
  - Score distribution chart
  - Ticker history with price and composite charts
- Tab 2: Guide — complete reference documentation
  - What is the Widell Line
  - Three states explained with returns
  - Composite score breakdown
  - Regime definitions
  - Flip signal types
  - Entry and exit checklists
  - Column reference

**Cloud deployment plan (Session 25):**
- AWS/GCP free tier VM
- Deploy pipeline + dashboard
- Always-on cron at market close
- Accessible from phone/browser anywhere
- Telegram bot for flip alerts

---

---
