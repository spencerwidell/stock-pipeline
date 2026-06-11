"""Exit / trim framework for held positions (Session 34 #4).

Long-term-investor framing — these are NOT hard stops, just a status on each name
you own, derived from its regression-channel position + Widell Line state:

  TRIM   — price is above the top of the channel (zone 'extended'): rich; consider
           trimming into strength.
  REVIEW — breaking down (zone 'breakdown' AND Widell state 'down'): the thesis or
           timing has turned negative; review whether to exit.
  HOLD   — everything else; nothing to do.

Thresholds match the Session 32 roadmap: trim = upper-channel *breach* (extended,
channel_pos > 1.0), exit-warning = breakdown zone + Widell down. Used by
narrative_alert.py (PORTFOLIO CHECK section) and morning_alert.py (position check).
"""


def assess_position(zone, state):
    """Return (status, reason) for a held name given its channel_zone + wl_state."""
    if zone == "extended":
        return ("TRIM", "above the channel top — consider trimming into strength")
    if zone == "breakdown" and state == "down":
        return ("REVIEW", "breaking down (breakdown zone + Widell down) — review the thesis")
    return ("HOLD", "")
