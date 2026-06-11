# Session Start Prompt

Paste this at the start of each new conversation:

---
I'm continuing my stock-pipeline project — a **personal investing intelligence
system** that turns a validated signal stack into clear, plain-English decisions for
a concentrated, conviction-driven long-term investor (wide moats, secular trends
toward the future, cash-flowing now, ~10 best-in-class names).

**Repo:** github.com/spencerwidell/stock-pipeline
**Env:** WSL Ubuntu 22.04, conda `stock`, Python 3.11
**Deploy:** git push → SSH to AWS EC2 (18.188.180.99) → git pull → regenerate
data (data/ is gitignored) → `sudo systemctl restart streamlit`

**Mission & guardrails:** see docs/KEY_OBJECTIVES.md (what it does / does not do)
and docs/MODEL_RISK.md (known risks + controls). Roadmap in docs/PRODUCT_ROADMAP.md.

**System today:** daily pipeline (Widell Line, composite + conviction scores,
fundamentals, moat, valuation), intelligence layer (LLM narrative briefing, secular
theme engine, macro/TLT regime, exit/trim), six-tab Streamlit dashboard, three daily
Telegram alerts. universe.yaml / holdings.yaml / themes.yaml / macro_calendar.yaml
are the hand-maintained single sources of truth.

**Last session:** [FILL IN — or see docs/SESSION_LOG.md]

**This session:** [FILL IN]
---
