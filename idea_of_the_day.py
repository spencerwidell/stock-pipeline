"""Idea of the Day — the single most important thing today, in one line.

The antidote to "too many choices." Every other surface lists everything; this one
picks ONE thing and says why. It's a deterministic synthesis (no API cost) over the
engines already built — the Destination Book, the Tide, and the stop/thesis context —
chosen by a priority ladder, most urgent first:

  1. 🛑 A speculative stop was hit            → protect capital, exit.
  2. ⚠️ A core name's thesis is eroding        → reassess before adding.
  3. 🌊 The tide turned vs the prior day       → shift posture (deploy / defend).
  4. 🎯 The top step toward the Destination    → the everyday idea (sell→complete).
  5. 💵 Nothing at entry                       → hold the powder, patience is the edge.

The idea is framed by today's tide (a rising tide says deploy; a falling tide says
wait), and a SELL idea names the winner its proceeds should complete. Shown atop the
Briefing and pushable to phone in the morning.
"""

import json
import os
from datetime import date

import cash_deployment
import destination

TIDE_HIST = "data/tide_history.json"


# ---------------------------------------------------------------------------
# Tide-turn memory — record today's tide, recall the prior day's (data/ is
# gitignored, so this builds up per-machine via the daily push).
# ---------------------------------------------------------------------------
def _load_hist():
    if not os.path.exists(TIDE_HIST):
        return {}
    try:
        with open(TIDE_HIST) as f:
            return json.load(f)
    except Exception:
        return {}


def _prev_level(on):
    """The tide level on the most recent recorded date BEFORE `on` (or None)."""
    hist = _load_hist()
    prev = None
    for d in sorted(hist):
        if d < on:
            prev = hist[d]
    return prev


def record_tide(level, on=None):
    """Persist today's tide level (once per day). Called by the daily push, not by
    dashboard loads, so 'previous' always means a real prior day."""
    on = on or date.today().isoformat()
    hist = _load_hist()
    if on in hist:
        return
    hist[on] = level
    try:
        os.makedirs("data", exist_ok=True)
        with open(TIDE_HIST, "w") as f:
            json.dump(hist, f)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Build the idea
# ---------------------------------------------------------------------------
def _first_add(actions):
    for a in actions:
        if a["type"] == "ADD":
            return a
    return None


def build_idea(on=None):
    """Return the one idea: {tag, icon, headline, body, ticker, frame, tide_level}."""
    on = on or date.today().isoformat()
    dest = destination.compute_destination()
    tide = dest.get("tide") or {}
    level = tide.get("level", "NEUTRAL")
    cd = cash_deployment.deployment()

    frame = (f"{tide.get('icon', '🌊')} {level} tide · {dest['reserve']:.0f}% reserve · "
             f"{dest['cash']:.0f}% cash · {dest['pool']:.0f}% to deploy")

    def idea(tag, icon, headline, body, ticker=None):
        return {"tag": tag, "icon": icon, "headline": headline, "body": body,
                "ticker": ticker, "frame": frame, "tide_level": level, "date": on}

    # 1) Stop hit — most urgent (capital protection).
    hit = [s for s in cd.get("stops", []) if s.get("status") == "triggered"]
    if hit:
        s = hit[0]
        return idea("STOP", "🛑",
                    f"Sell {s['ticker']} — it hit its −7% stop (${s['current']} vs ${s['stop']}).",
                    "A speculative position triggered its stop. The discipline says exit, no "
                    "exception — then redeploy the proceeds toward an underweight winner.",
                    s["ticker"])

    # 2) Thesis erosion on a core name.
    if cd.get("thesis_alerts"):
        a = cd["thesis_alerts"][0]
        return idea("THESIS", "⚠️",
                    f"Reassess {a['ticker']} — {a['detail']}",
                    "Core is held through volatility, but a broken thesis is the one reason to "
                    "exit. Check the story before you add another dollar.",
                    a["ticker"])

    # 3) Tide turn vs the prior recorded day.
    prev = _prev_level(on)
    if prev and prev != level:
        if level == "FALLING":
            return idea("TIDE", "🌊",
                        f"The tide turned {prev}→FALLING — shift to defense.",
                        f"Benchmarks and breadth rolled over, so the book now holds a "
                        f"{dest['reserve']:.0f}% reserve. Stop chasing adds into the downtrend; "
                        "let exits and reduces raise cash, and wait for the turn.")
        if level == "RISING":
            return idea("TIDE", "🌊",
                        f"The tide turned {prev}→RISING — time to deploy.",
                        f"Breadth and the benchmarks turned up; the reserve drops to "
                        f"{dest['reserve']:.0f}%. Complete your underweight winners while the "
                        "tide is with you.")

    # 4) The top step toward the Destination Book.
    if dest.get("actions"):
        top = dest["actions"][0]
        tk = top["ticker"]
        if top["type"] in ("SELL", "REDUCE"):
            verb = "Sell" if top["type"] == "SELL" else "Trim"
            add = _first_add(dest["actions"])
            tail = (f" and put it toward {add['ticker']} (+{add['trade_pct']:g}% → "
                    f"{add['new_weight']:g}%, {add.get('detail', '').split('—')[0].strip()})"
                    if add else " and hold the proceeds as powder until a winner sets up")
            return idea("STEP", "🔴" if top["type"] == "SELL" else "🟡",
                        f"{verb} {tk}{tail}.",
                        f"Today's top step: {top['detail']} " +
                        (f"A {level.lower()} tide says deploy the cash now." if level == "RISING"
                         else f"A {level.lower()} tide — redeploy patiently."), tk)
        # an ADD
        return idea("STEP", "🟢",
                    f"Complete {tk} to {top['new_weight']:g}% (+{top['trade_pct']:g}%).",
                    f"Your highest-priority step: {top['detail']} " +
                    (f"The {level.lower()} tide is with you — deploy." if level == "RISING"
                     else f"Sized for a {level.lower()} tide."), tk)

    # 5) Something setting up but waiting (cash/tide/macro-gated).
    if dest.get("waitlist"):
        w = dest["waitlist"][0]
        return idea("WAIT", "👀",
                    f"{w['ticker']} is setting up (+{w['trade_pct']:g}% → {w['target']:g}%) — "
                    f"but waiting: {w.get('wait_reason')}.",
                    "The setup is there; the timing isn't. Keep it on the radar and let the "
                    "trigger come to you.", w["ticker"])

    # 6) Patience.
    return idea("HOLD", "💵",
                f"Hold your {dest['cash']:.0f}% powder — nothing at entry today.",
                f"A {level.lower()} tide and no compelling step. Patience is the edge; "
                "the watchlist is forming.")


def to_text(idea):
    """Plain-text render for Telegram."""
    return (f"💡 IDEA OF THE DAY · {idea['date']}\n"
            f"{idea['frame']}\n\n"
            f"{idea['icon']} {idea['headline']}\n\n"
            f"{idea['body']}")


def send_idea():
    """Build the idea, record today's tide, and push it to Telegram (cron path)."""
    from narrative_alert import send_telegram
    idea = build_idea()
    record_tide(idea["tide_level"])
    send_telegram(to_text(idea))
    return idea


if __name__ == "__main__":
    print(to_text(build_idea()))
