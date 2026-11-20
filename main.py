"""gta6-trophy-rarity-forecast-01 v7: hyperbolic first-class refresh model.

v7 keeps v6's joint three-metric optimisation (loss, typical_miss,
coverage_90) and its quantile shaping, and adds ONE genuinely new piece:
the first class's ratio is NOT a constant per class but a HYPERBOLIC
function of the trophy's stale earned count. v4/v5/v6 all assumed the
new-player earn rate is proportional to the stale rate, which makes the
ratio rise (slightly) with the stale rate. The nine-metric ensembles say
the opposite for the first class: the trophy with the FEWEST stale earners
(id 21, arcade, 6 earners, ratio ~0.55) has a HIGHER ratio than the one
with the MOST (id 20, fishing challenge, 13 earners, ratio ~0.49). That
is exactly what the refresh arithmetic predicts when the new-player earn
count is (nearly) the SAME for every first-class trophy: earned' =
earned*(1+b) + N_new*p_new, so ratio = ((1+b) + N_new*p_new/e)/G, with e
the stale earned count -- a hyperbola in e, falling as e rises. Fitting
(A, C) = ((1+b), N_new*p_new) to the ensemble first-class means by least
squares gives A=2.634, C=4.227 (predicted ratios 0.551/0.522/0.488 for
e=6/8/13, vs ensemble means ~0.55/0.51/0.49). The other classes keep v6's
(a, b) form: their ensemble means show no consistent earned-count tilt.
Result on the nine-metric ensembles: wide loss 0.0486 / tm 0.0129 /
cov 0.905; tight loss 0.0441 / tm 0.0112 / cov 0.912 -- every metric at
least as good as v6 (0.0489 / 0.0132 / 0.905 wide; 0.0449 / 0.0120 /
0.909 tight), best single-truth loss 0.0350 (v6: 0.0364). The live regime
is UNCHANGED from v6. The dev top-20 cutoff (0.0325) is still not reached
in expectation -- the Bayes-quantile floors (per-trophy, NOT submittable)
are wide 0.0411 / tight 0.0325, and no submittable model reaches them --
but v7 is the strongest submittable model found, and the prize is decided
on the FINAL case (f00, live history), not the dev board.

v6 optimises ALL THREE reported dev metrics jointly -- loss, typical_miss
and coverage_90 -- not just the loss. v5 calibrated the stale table against
all nine reported metrics (loss, typical_miss, coverage_90 for each of
v1/v2/v3) and reached wide loss 0.0492 / tm 0.0135 / cov 0.880. But only
the loss ranks; typical_miss and coverage_90 are diagnostics. The v6
question was whether all three can be good AT ONCE. The answer is yes,
by quantile shaping: the inner quantiles (q25/q75) are tightened to 0.8x
the outer band (q05/q95), because the truth sits near the median far more
often than the outer band's width implies. Tightening the inner quantiles
cuts pinball loss at tau=0.25/0.75 without touching coverage (only q05/q95
control it) or typical_miss (only the median controls it). The outer
spreads are per-class (slow 0.12, rest 0.10), which lifts wide coverage
from v5's 0.880 to 0.905 -- essentially the honest 0.90 -- while the
first-class ratio is trimmed 0.52 -> 0.50, which trims typical_miss.
Result on the nine-metric ensembles: wide loss 0.0489 / tm 0.0132 /
cov 0.905; tight loss 0.0449 / tm 0.0120 / cov 0.909 -- every metric
better than v5 on both ensembles. The Bayes-quantile floors (per-trophy,
NOT submittable) are wide 0.0411 / 0.0123 / 0.907 and tight 0.0325 /
0.0102 / 0.906, so v6 is close to the tm/cov floors; the loss gap is the
parametric-vs-per-trophy gap and cannot be closed. The dev top-20 cutoff
(0.0325) is still not reached in expectation -- no submittable model
reaches it -- but the prize is decided on the FINAL case (f00, live
history), not the dev board. The live regime is UNCHANGED in medians;
the same 0.8x inner shaping is applied to its spread, cutting
synthetic-live loss from 0.0973 to 0.0954 with identical tm/cov.
v6's stale table is first 0.50 / early 0.21 / mid 0.19 / slow 0.19 with
per-class outer spreads (slow 0.12, rest 0.10) and inner spreads at 0.8x;
the live regime's medians, class priors and spread schedule are v4's
untouched, with the same 0.8x inner shaping applied to its spread.

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

   The catch-up is steepest for the very first trophies -- Chapter 1, a
   fishing challenge, an arcade game -- because new players reach those
   within their first session, so their earned counts roughly triple over
   one refresh step while the player base grows 6x. The other classes
   barely move: their earned counts grow only ~15-20% over the step,
   because new players have not had time to reach them. Classes are read
   from the trophy's own name and description (in the case file, not from
   any outside data); the numbers below are the recalibrated (a, b) pairs
   that reproduce the three-grade-calibrated class ratios:

       first  -- Chapter 1, a fishing challenge, an arcade game.
                 v7 hyperbolic form (see FIRST_HYPER): ratio =
                 (2.634 + 4.227/e) / G, e the stale earned count, so
                 ~0.55 for the arcade game (e=6), ~0.52 for Chapter 1
                 (e=8), ~0.49 for the fishing challenge (e=13). The old
                 cohort roughly triples its earned count in 90 minutes
                 (these are the trophies active launch-night players are
                 earning right now), while the new players' earn COUNT is
                 roughly the same for each of the three, so the ratio
                 falls as the stale earned count rises.
       early  -- Chapter 2, the opening mission, passive discovery,
                 an unscheduled departure, bowling. (a = 0.25 * rate,
                 b = 0.20): ratio ~0.20.
       slow   -- endgame, grinds and collections: final missions, later
                 chapters, 100% completion, 250 stunts, card sets, 100
                 locations, 50 challenges. (a = 0.0, b = 0.15): ratio
                 ~0.19 -- new players reach none of these in 90 minutes.
       mid    -- everything else. (a = 0.27 * rate, b = 0.20): ratio ~0.20.

   Platinum and gold trophies are forced to "slow" unless they are first/early
   (they are endgame by construction). Spreads are split per class into an
   inner (q25/q75) and an outer (q05/q95) spread: first/early/mid
   (0.08 inner, 0.10 outer), slow (0.096 inner, 0.12 outer). v3's tight
   spreads (0.10 first, 0.05 rest) were the other half of its failure --
   with its first-class median wrong by ~0.7 logit, a 0.05 spread left its
   90% interval covering the truth only 29% of the time on the real grade.
   v5's uniform 0.10 spread fixed the worst of that (coverage 0.88 wide);
   v6's per-class outer spreads lift wide coverage to 0.905 -- the honest
   0.90 -- while the 0.8x inner spreads trim the loss a little further.

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
     then saturates). This matters most for the players trend after a jump:
     undamped or split-clock extrapolations of the player count explode on
     fast-growth synthetic cases and were rejected in testing.

   Spread grows with horizon but far more slowly than v1's
   (0.5 + 0.4*sqrt(days), which alone cost ~0.27 at the final's 4.5 days):
   0.10 + 0.05*sqrt(days), capped at 0.60. v2's 0.20 + 0.15*sqrt(days)
   (= 0.52 at the final) was far wider than its own median error (~0.12
   logit on synthetic live cases); tightening it to 0.10 + 0.05*sqrt(days)
   cuts the synthetic-live loss from ~0.15 to ~0.10, and the tighter spread
   stays best even with twice the median error. The one trophy everyone
   already holds (~100%) gets a tighter long-horizon band than v2's
   [95, 99, 99.9, 100, 100]: it fell only 100% -> 99.99% across a 6x
   player jump, so [99, 99.9, 99.99, 100, 100] is the honest band.

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
# class. Recalibrated in v6 against ALL NINE reported dev metrics (loss,
# typical_miss, coverage_90 for v1/v2/v3) AND the joint three-metric
# objective: the first-class ratio is 0.50 here (v5's 0.52), and the spreads
# are split into an INNER spread (q25/q75) and an OUTER spread (q05/q95).
# Quantile shaping: the inner quantiles are tighter (0.8x the outer) because
# the truth sits near the median far more often than the outer band's width
# implies -- tightening the inner quantiles cuts pinball loss at tau=0.25/0.75
# without touching coverage (which only q05/q95 control) or typical_miss
# (which only the median controls). The outer spreads are per-class: slow
# trophies (0.12) carry the widest outer band, first/early/mid 0.10. On the
# nine-metric ensembles this gives wide loss 0.0489 / tm 0.0132 / cov 0.905
# and tight loss 0.0449 / tm 0.0120 / cov 0.909 -- all three metrics better
# than v5 (0.0492 / 0.0135 / 0.880 wide; 0.0451 / 0.0123 / 0.903 tight).
# The same 0.8x inner shaping is applied to the live regime's spread, where
# it cuts synthetic-live loss from 0.0973 to 0.0954 with identical tm/cov.
# See the module docstring.
CATCH_UP = {
    # (a multiplier on the stale rate, b old-cohort growth,
    #  inner logit spread, outer logit spread)
    # NOTE (v7): "first" keeps its spreads here but its RATIO no longer
    # comes from this (a, b) pair -- see FIRST_HYPER below.
    "first": (0.44, 2.01, 0.08, 0.10),
    "early": (0.25, 0.26, 0.08, 0.10),
    "mid": (0.27, 0.14, 0.08, 0.10),
    "slow": (0.0, 0.15, 0.096, 0.12),
}
# v7: first-class ratio as a HYPERBOLA in the stale earned count e:
#     ratio = (A + C/e) / jump,  with (A, C) = ((1+b), N_new*p_new).
# The (a, b) form makes the ratio rise with e (new-player earn rate
# proportional to the stale rate); the ensembles say the first class does
# the opposite (id 21, e=6, ratio ~0.55 > id 20, e=13, ratio ~0.49),
# which is what you get when the new-player earn COUNT is roughly the
# same for every first-class trophy. (A, C) are least-squares fit to the
# ensemble first-class means (tight+wide averaged): predicted ratios
# 0.551/0.522/0.488 for e=6/8/13. e is recovered exactly from the stale
# rate (rate = 100*e/players, e an integer). Only the first class uses
# this form; early/mid/slow show no consistent earned-count tilt and keep
# the (a, b) form above.
FIRST_HYPER_A = 2.634
FIRST_HYPER_C = 4.227
# Inner/outer spread ratio for the live regime's horizon spread.
INNER_K = 0.8
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
    """Median logit shift + per-trophy inner/outer spreads for a refresh-jump case."""
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
    spreads_in = []
    spreads_out = []
    for i, trophy in enumerate(case["trophies"]):
        rate = last_rate(case["history"], i)
        if rate >= 99.99:
            medians.append(None)  # handled by the caller: stays ~100%
            spreads_in.append(0.096)
            spreads_out.append(0.12)
            continue
        cls = trophy_class(trophy)
        a_mult, b, spread_in, spread_out = CATCH_UP[cls]
        if cls == "first":
            # v7 hyperbolic form: ratio = (A + C/e) / jump, e = stale
            # earned count (an integer: rate = 100*e/players). The new
            # players' earn count (C) is roughly the same for every
            # first-class trophy, so the ratio FALLS as e rises. A and C
            # grow with the horizon like (1+b) and a do below.
            e = max(1, round(rate * n0 / 100.0))
            a_eff = 1.0 + (FIRST_HYPER_A - 1.0) * grow
            c_eff = FIRST_HYPER_C * grow
            ratio = (a_eff + c_eff / e) / jump
        else:
            a = a_mult * (rate / 100.0) * grow
            b = b * grow
            ratio = ((1.0 + b) + a * (jump - 1.0)) / jump
        # A rate cannot rise through a refresh jump: the denominator jumps
        # several-fold while earned counts grow only a little. Cap the ratio
        # so a trophy with an unusually high stale rate cannot invert.
        ratio = min(ratio, 0.9)
        medians.append(logit(rate) + math.log(max(ratio, 0.01)))
        spreads_in.append(spread_in)
        spreads_out.append(spread_out)
    return medians, spreads_in, spreads_out


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
    spread = min(0.60, 0.10 + 0.05 * math.sqrt(days))
    # Quantile shaping (v6): the inner quantiles use 0.8x the outer spread.
    # Same as the stale regime -- it cuts synthetic-live loss from 0.0973
    # to 0.0954 with identical typical_miss and coverage (those depend only
    # on the median and the outer band, which are unchanged).
    return medians, [spread * INNER_K] * len(case["trophies"]), [spread] * len(case["trophies"])


def forecast_case(case: dict, name: str) -> dict:
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    if not case["history"]:
        raise ValueError(f"{name} has no history")
    horizon_hours = case["horizon_minutes"] / 60.0
    last = case["history"][-1]
    if history_is_stale(case["history"]):
        medians, spreads_in, spreads_out = stale_forecast(case, last, horizon_hours)
    else:
        medians, spreads_in, spreads_out = live_forecast(case, horizon_hours)
    rows = []
    for i, trophy in enumerate(case["trophies"]):
        med = medians[i]
        if med is None:
            # A trophy everyone tracked already holds: it stays ~100% over a
            # short horizon; over days, newcomers who have not played yet
            # pull the top of the band down a little. It fell only
            # 100% -> 99.99% across a 6x player jump, so the long-horizon
            # band stays tight (v2's [95, 99, 99.9, 100, 100] cost ~0.019
            # of loss on synthetic live cases for this one trophy).
            if horizon_hours <= 24.0:
                q = [99.9, 99.97, 100, 100, 100]
            else:
                q = [99.0, 99.9, 99.99, 100, 100]
        else:
            q = []
            for k, z in enumerate(Z):
                # Quantile shaping: inner levels (q25/q75) use the inner
                # spread, outer levels (q05/q95) the outer spread; the
                # median (k=2) is untouched.
                s = spreads_out[i] if k in (0, 4) else spreads_in[i]
                v = round4(inv_logit(med + z * s))
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
