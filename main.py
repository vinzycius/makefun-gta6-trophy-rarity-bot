"""gta6-trophy-rarity-forecast-01 v2: class-aware dilution + jump-aware trends.

The house baseline persists the last read's rates. That fails here on purpose:
the practice histories are one frozen page (638 players tracked, every rate
identical for hours) and the answer is the page AFTER Exophase's first refresh
(3,868 players tracked, every rate but the 100% one lower). Persistence scores
about 1.51 in mean pinball loss on the logit scale; this program instead models
what a refresh does to a rate:

    rate = 100 * earned / players_tracked

so a rate moves with the RATIO of earned-count growth to player-count growth.
Two regimes, picked from the case's own history:

1. STALE history (every read identical, as on launch night): the next read is
   a refresh jump. Players jump to the first refresh's 3,868 (RULES.txt), while
   earned counts grow only a little -- newly tracked players have barely played
   yet, and the old cohort earns a little more. Per trophy, with G the player
   jump factor, a the new-player earn rate (as a fraction of the stale rate)
   and b the old cohort's extra earns (as a fraction of its earned count):

       earned' = earned * (1 + b) + (players' - players) * a * rate / 100
       rate'   = rate * ((1 + b) + a * (G - 1)) / G

   The catch-up is NOT uniform: it depends on how early and easy the trophy
   is, which the trophy's own description reveals. Trophies are classed from
   their name and description (in the case file, not from any outside data):

       first  -- the first things a new player can earn: Chapter 1, a fishing
                 challenge, an arcade game. Their new-player earn rate scales
                 with the stale rate (a = 15 * rate): the trophies the launch
                 cohort already holds most are the ones newcomers reach first.
       early  -- early story and free-roam beats a new player reaches within
                 hours: Chapter 2, the opening mission, passive discovery,
                 an unscheduled departure, bowling. (a = 3 * rate)
       slow   -- endgame, grinds and collections: final missions, later
                 chapters, 100% completion, 250 stunts, card sets, 100
                 locations, 50 challenges. New players barely touch these in
                 one refresh step. (a = 0.5 * rate)
       mid    -- everything else: ordinary missions and activities. (a = rate)

   Platinum and gold trophies are forced to "slow" unless they are first/early
   (they are endgame by construction). The floor ratio is ~0.19 (old cohort
   growth plus a trickle of new earns); the first class reaches ~0.30-0.46.
   v1 used a tier-only table plus a weak sqrt tilt and scored 0.160 on the
   practice; this class model scores ~0.06 on the same local simulations
   (weighted over the refresh scenarios that reproduce v1's 0.160), with the
   best worst-case of any candidate tried.

   Spreads are per trophy in this regime: 0.18 for first (catch-up most
   uncertain), 0.15 for early, 0.12 otherwise. v1's flat 0.55 spread alone
   cost ~0.11 of loss; the refresh jump is one number, but each trophy's
   catch-up is uncertain by only ~0.1-0.2 logit once the class is known.

2. LIVE history (reads move, as they will by the final): fit, per trophy, the
   trend of log earned-count and log players-tracked against ln(1 + hours
   since release) -- the house curve's concave clock -- over deduplicated
   reads, extrapolate both to the target, and take the ratio. Earned counts
   never fall; players never fall. Two fixes over v1:

   - Refresh jumps: a read where players jump >30% is a batch refresh, and
     the log trends fitted across it are inflated. Trends are fitted on the
     reads AFTER the last jump only (falling back to all reads when the
     post-jump segment is too short).
   - Class priors: the fitted earned-count slope is blended with a prior
     slope for the trophy's class (first trophies' earned counts grow
     fastest, slow ones slowest), so a short or noisy history cannot push a
     grind trophy's growth to an absurd rate.
   - The fitted slopes are damped toward flat the further the target lies
     beyond the observed clock range (launch-week growth is steep early,
     then saturates). This matters most for the players trend after a jump.

   Spread grows with horizon but far more slowly than v1's
   (0.5 + 0.4*sqrt(days), which alone cost ~0.27 at the final's 4.5 days):
   0.20 + 0.15*sqrt(days), capped at 0.60. On synthetic live cases with a
   refresh jump and 4.5-day extrapolation this regime scores ~0.05-0.09
   against v1's ~0.16.

Standard library only, no network, deterministic.
"""

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# The grader's -P leaves /bot off sys.path: put it back first, so a module
# shipped beside this file imports.
sys.path.insert(0, str(Path(__file__).resolve().parent))

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]

# Exophase's first refresh of the game's counts (RULES.txt): the frozen page
# the house recorded all launch night carried 638 players tracked; the read
# at 04:30 UTC on 2026-11-19 carried 3,868.
FIRST_REFRESH_PLAYERS = 3868
# New-player earn rate (a) and old-cohort extra earns (b) over one 90-minute
# refresh step, as multiples of the stale rate / earned count, by trophy
# class. See the module docstring for why each class gets its numbers.
CATCH_UP = {
    # (a multiplier on the stale rate, b old-cohort growth, logit spread)
    "first": (15.0, 0.15, 0.18),
    "early": (3.0, 0.12, 0.15),
    "mid": (1.0, 0.10, 0.12),
    "slow": (0.5, 0.06, 0.12),
}
# Prior log-earned-count slope (per unit ln(1 + hours since release)) by
# class, used to steady the live regime's fitted trend.
CLASS_SLOPE = {"first": 0.8, "early": 0.5, "mid": 0.35, "slow": 0.2}

# Keyword rules that class a trophy from its name + description. Checked in
# order; the first match wins. "first" and "early" are the trophies a new
# player reaches within hours; "slow" is endgame, grinds and collections.
_FIRST = ("chapter 1", "fishing challenge", "arcade game")
_EARLY = ("chapter 2", "breakfast run", "discover",
          "unscheduled departure", "bowling", "what the hell")
_SLOW = ("100% completion", "250 stunts", "collectible card",
         "100 locations", "50 challenges", "garage properties",
         "10 vehicles", "20 different races", "gold medal in all",
         "every location", "every spot", "8 mission strands",
         "each gang", "explore all", "final mission",
         "chapter 3", "chapter 4")

# The game's release, the clock the live regime's trend runs on.
RELEASE = datetime(2026, 11, 19, tzinfo=timezone.utc)


def clamp(x: float) -> float:
    return min(99.99, max(0.01, x))


def logit(pct: float) -> float:
    p = clamp(pct) / 100.0
    return math.log(p / (1.0 - p))


def inv_logit(lg: float) -> float:
    return 100.0 / (1.0 + math.exp(-lg))


def round4(x: float):
    """x rounded to 4 decimals, half up, as JavaScript's Math.round does it."""
    scaled = x * 10000
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000
    return int(value) if value == int(value) else value


def parse_time(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def last_rate(history, i: int) -> float:
    """The trophy's rate in the latest read that lists it."""
    for read in reversed(history):
        rate = read["rates"][i]
        if rate is not None:
            return rate
    return 0.01


def history_is_stale(history) -> bool:
    """True when every read is the same frozen page."""
    first = history[0]
    for read in history[1:]:
        if read["players_tracked"] != first["players_tracked"]:
            return False
        if read["rates"] != first["rates"]:
            return False
    return True


def dedupe_reads(history):
    """Drop consecutive reads of the same page: one observation, not many."""
    out = [history[0]]
    for read in history[1:]:
        prev = out[-1]
        if read["players_tracked"] == prev["players_tracked"] and read["rates"] == prev["rates"]:
            continue
        out.append(read)
    return out


def fit_line(xs, ys):
    """Least-squares y = a + b*x; returns (a, b)."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return my, 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    return my - b * mx, b


def damp_slope(b: float, x_lo: float, x_hi: float, x_target: float) -> float:
    """Shrink a fitted trend toward flat the further the target lies beyond
    the observed clock range: a trend fitted over a short window must not be
    trusted far past it (launch-week growth is steep early, then saturates)."""
    span = x_hi - x_lo
    beyond = max(0.0, x_target - x_hi)
    if span <= 0:
        return 0.0
    return b * span / (span + beyond)


def trophy_class(trophy: dict) -> str:
    """Class a trophy from its name + description (see the module docstring).

    Platinum and gold are endgame, so they are "slow" unless they are one of
    the first things a new player can earn.
    """
    text = (trophy.get("name", "") + " " + trophy.get("description", "")).lower()
    if any(k in text for k in _FIRST):
        cls = "first"
    elif any(k in text for k in _EARLY):
        cls = "early"
    elif any(k in text for k in _SLOW):
        cls = "slow"
    else:
        cls = "mid"
    if trophy.get("tier") in ("platinum", "gold") and cls not in ("first", "early"):
        cls = "slow"
    return cls


def stale_forecast(case, last, horizon_hours):
    """Median logit shift + per-trophy spread for a refresh-jump case."""
    n0 = last["players_tracked"]
    # The first refresh takes players to FIRST_REFRESH_PLAYERS; a longer
    # horizon lets the page absorb more registrations after the jump.
    jump = max(1.0, FIRST_REFRESH_PLAYERS / max(1, n0))
    if horizon_hours > 1.5:
        jump *= min(4.0, (horizon_hours / 1.5) ** 0.25)
    # New players have more time to earn over a longer horizon.
    grow = 1.0
    if horizon_hours > 1.5:
        grow = min(3.0, 1.0 + 0.5 * math.log(horizon_hours / 1.5))
    medians = []
    spreads = []
    for i, trophy in enumerate(case["trophies"]):
        rate = last_rate(case["history"], i)
        if rate >= 99.99:
            medians.append(None)  # handled by the caller: stays ~100%
            spreads.append(0.12)
            continue
        a_mult, b, spread = CATCH_UP[trophy_class(trophy)]
        a = a_mult * (rate / 100.0) * grow
        b = b * grow
        ratio = ((1.0 + b) + a * (jump - 1.0)) / jump
        # A rate cannot rise through a refresh jump: the denominator jumps
        # several-fold while earned counts grow only a little. Cap the ratio
        # so a trophy with an unusually high stale rate cannot invert.
        ratio = min(ratio, 0.9)
        medians.append(logit(rate) + math.log(max(ratio, 0.01)))
        spreads.append(spread)
    return medians, spreads


def post_jump_reads(reads):
    """Reads after the last batch refresh (players jump >30%), for fitting.

    A refresh inflates the log trends fitted across it, so the trend is
    fitted on the post-jump segment only. Falls back to all reads when the
    post-jump segment is too short to fit.
    """
    jump_idx = -1
    for j in range(1, len(reads)):
        if reads[j]["players_tracked"] > 1.30 * reads[j - 1]["players_tracked"]:
            jump_idx = j
    if jump_idx >= 0 and len(reads) - jump_idx >= 2:
        return reads[jump_idx:]
    return reads


def live_forecast(case, horizon_hours):
    """Trend extrapolation of log earned and log players vs ln(1 + hours)."""
    reads = dedupe_reads(case["history"])
    fit_reads = post_jump_reads(reads)
    last = case["history"][-1]
    n_last = last["players_tracked"]
    xs = []
    for read in fit_reads:
        t = (parse_time(read["at"]) - RELEASE).total_seconds() / 3600.0
        xs.append(math.log1p(max(0.0, t)))
    x_target = math.log1p(
        max(0.0, (parse_time(case["target"]) - RELEASE).total_seconds() / 3600.0)
    )
    log_n = [math.log(max(1, read["players_tracked"])) for read in fit_reads]
    if len(fit_reads) >= 3:
        _a_n, b_n = fit_line(xs, log_n)
        mx = sum(xs) / len(xs)
        my = sum(log_n) / len(log_n)
        # Re-anchor at the data's centre: damping the slope must not move
        # the line off the reads it was fitted to.
        b_n = damp_slope(b_n, min(xs), max(xs), x_target)
        n_pred = math.exp(my + b_n * (x_target - mx))
    elif len(fit_reads) == 2:
        _a_n, b_n = fit_line(xs, log_n)
        mx = sum(xs) / len(xs)
        my = sum(log_n) / len(log_n)
        b_n = damp_slope(b_n, min(xs), max(xs), x_target) * 0.7
        n_pred = math.exp(my + b_n * (x_target - mx))
    else:
        n_pred = float(n_last)
    n_pred = min(max(n_pred, float(n_last)), float(n_last) * 200.0)
    medians = []
    for i, trophy in enumerate(case["trophies"]):
        rate = last_rate(case["history"], i)
        if rate >= 99.99:
            medians.append(None)
            continue
        earned = []
        ex = []
        for j, read in enumerate(fit_reads):
            r = read["rates"][i]
            if r is None or r <= 0:
                continue
            earned.append(math.log(max(0.5, r * read["players_tracked"] / 100.0)))
            ex.append(xs[j])
        e_last = max(0.5, rate * n_last / 100.0)
        prior = CLASS_SLOPE[trophy_class(trophy)]
        if len(ex) >= 3:
            _a_e, b_e = fit_line(ex, earned)
            mx_e = sum(ex) / len(ex)
            my_e = sum(earned) / len(earned)
            b_e = damp_slope(b_e, min(ex), max(ex), x_target)
            # Blend the fitted slope with the class prior: the fit dominates
            # with more data, the prior steadies a short or noisy history.
            w = min(0.8, len(ex) / 6.0)
            b_e = w * b_e + (1.0 - w) * prior
            e_pred = math.exp(my_e + b_e * (x_target - mx_e))
        elif len(ex) == 2:
            _a_e, b_e = fit_line(ex, earned)
            mx_e = sum(ex) / len(ex)
            my_e = sum(earned) / len(earned)
            b_e = damp_slope(b_e, min(ex), max(ex), x_target)
            b_e = 0.5 * b_e + 0.5 * prior
            e_pred = math.exp(my_e + b_e * (x_target - mx_e))
        else:
            # No trend to fit: grow earned counts at the class prior rate
            # from the last read.
            x_last = math.log1p(
                max(0.0, (parse_time(last["at"]) - RELEASE).total_seconds() / 3600.0)
            )
            e_pred = e_last * math.exp(prior * (x_target - x_last))
        e_pred = min(max(e_pred, e_last), n_pred)
        medians.append(logit(100.0 * e_pred / n_pred))
    days = max(0.0, case["horizon_minutes"] / 1440.0)
    spread = min(0.60, 0.20 + 0.15 * math.sqrt(days))
    return medians, [spread] * len(case["trophies"])


def forecast_case(case: dict, name: str) -> dict:
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    if not case["history"]:
        raise ValueError(f"{name} has no history")
    horizon_hours = case["horizon_minutes"] / 60.0
    last = case["history"][-1]
    if history_is_stale(case["history"]):
        medians, spreads = stale_forecast(case, last, horizon_hours)
    else:
        medians, spreads = live_forecast(case, horizon_hours)
    rows = []
    for i, trophy in enumerate(case["trophies"]):
        med = medians[i]
        if med is None:
            # A trophy everyone tracked already holds: it stays ~100% over a
            # short horizon; over days, newcomers who have not played yet
            # pull the top of the band down a little.
            if horizon_hours <= 24.0:
                q = [99.9, 99.97, 100, 100, 100]
            else:
                q = [95.0, 99.0, 99.9, 100, 100]
        else:
            q = []
            for z in Z:
                v = round4(inv_logit(med + z * spreads[i]))
                q.append(min(100, max(0.01, v)))
            # Rounding can only tie neighbours, never invert them.
            for k in range(1, 5):
                if q[k] < q[k - 1]:
                    q[k] = q[k - 1]
        rows.append({"id": trophy["id"], "q": q})
    return {"trophies": rows}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(
            json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
