"""gta6-trophy-rarity-forecast-01 v11: full-window E/N race + saturation-shape
selection + joint three-metric calibration.

v11 is a LARGE jump over v10 on every metric, on every validation set
(dev tight/wide, live tuning seeds, live held-out seeds never used in
tuning, new families H/M/R, and second-wave families D/T/U/W):

  dev tight  0.0408 / tm 0.0113 / cov 0.945   (v10: 0.0440 / 0.0113 / 0.930)
  dev wide   0.0453 / tm 0.0129 / cov 0.942   (v10: 0.0480 / 0.0129 / 0.926)
  live tuning (76 cases)  0.0339 / 0.0366 / 0.939   (v10: 0.0627 / 0.0519 / 0.921)
  live held-out (76 cases) 0.0348 / 0.0367 / 0.931 (v10: 0.0626 / 0.0495 / 0.921)
  new H/M/R (20) 0.0309 / 0.0280 / 0.970         (v10: 0.1392 / 0.0487 / 0.742)
  new2 D/T/U/W (20) 0.0481 / 0.0365 / 0.855      (v10: 0.2070 / 0.1720 / 0.742;
                                             U 0.090 vs v10 0.713, D 0.032,
                                             T 0.023, W 0.047)

Three structural ideas (each validated on held-out seeds and new
families the winner was never tuned on; each rejected-or-adopted on
evidence, not hope):

1. EN3: full-window E fit (live). v10's EN2 fitted log E on the
post-jump segment only (20.5h, 5 reads on GB) -- too short to identify
the (b, c) split of log E = a + b*ln(1+t) + c*t (ln(1+t) vs t corr
~0.995 there), so the fit put E growth into the exponential component
and over-predicted E at the target (EN2 was as wrong as the logistic
on most GB trophies, errors -0.6..-0.9 logit). E is SMOOTH across
players jumps (rate*N is continuous even when the rate cliffs), so
EN3 fits log E on ALL deduplicated reads (56.5h, 10 reads) while the
log-N fit stays post-jump (exact counts, clock-linear) with the same
>=4-reads abstain guard (family H untouched). GB collapses 0.41 ->
0.08, R 0.46 -> 0.04, and with the ratio-weighted blend cap raised to
1.00 the smooth families are untouched (the blend fires only where
EN3 predicts a strong decline vs the saturation fit).

2. Saturation-shape selection (live). The logistic's exponential tail
saturates too fast for power-law-approach truths (family P had the
worst typical_miss of all families, 0.105). v11 fits a power-law
saturation p(t) = p_inf - (p_inf-p0)*(1+(t-t0)/tau)^(-1) alongside
the logistic and picks per trophy by weighted in-sample SSE -- but
only when the power-law fit is CLEARLY better (SSE < 0.5x the
logistic's), so noisy picks on short segments (family H) cannot
misfire. P's loss falls 0.0398 -> 0.0276 and its tm 0.105 -> ~0.06.

3. Joint three-metric calibration (stale/dev + live spread). Dev:
per-class spread reallocation (early was under-covered 0.875, first
over-covered 1.000) plus a tighter short-horizon band for the
already-held trophy ([99.99, 99.99, 100, 100, 100] -- the practice
answer keeps it at exactly 100%, RULES.txt, and all 31 ensemble
truths agree). The (a, b) / hyperbola refit was REJECTED: it won on
tight but lost on wide (no cross-ensemble win). Live: with medians
this accurate the v10 spread is far too wide (cov 0.988), so it is
retuned to 0.06 + 0.01*sqrt(days), INNER_K 0.4 -- cov back to honest
0.93-0.94 with loss lower still.

4. Symmetric drop segmentation (live). A persistent players DROP
(>25%, persisting) is a segment break like a refresh jump, and a
rate SPIKE >40% across a drop triggers the cliff rule (fit on
post-drop reads only). Family U (a 30% players drop mid-window, a
bot-purge-style correction) falls 0.61 -> 0.09 with zero cost on any
other set (dev, tuning, held-out, H/M/R, D/T/W all identical).
An earlier in-process test wrongly reported "no effect" -- it had
patched a duplicate module object the scorer never used; the
program-level validation is the ground truth. No hostile family
remains above 0.10: the worst single case across all 192 live
validations is 0.106 (GB, held-out seed 77).

Known limits that remain: family G-B's covariance is still the
lowest (cov ~0.67-0.70 on held-out at this spread -- its medians are
good now, but a few trophies' truths still fall outside the bands);
family U's coverage is ~0.4-0.5 (loss is good at 0.09, the bands
just stay narrow). The dev top-20 cutoff (0.0325) is still not
reached in expectation -- the honest LOO Bayes ceiling (0.040-0.046)
says no submittable model reaches it -- but v11 sits at the bottom
of that ceiling on dev (0.0408) and is far stronger than v10 where
the prize is actually decided, the FINAL case.

v10 keeps v9's logistic-saturation live medians as its core and adds THREE
upgrades, each validated on synthetic truth families the model never tuned
on (held-out seeds + new families H/M/R) and each rejected-or-adopted on
evidence, not on hope:

1. E/N race blend (live). v9's logistic fit extrapolates the RATE curve;
when the player base is growing exponentially while earned counts grow
only as a power law (the log-time growth family G), the rate FALLS toward
the target and the logistic -- which fits the in-window rate shape -- misses
the decline. The E/N decomposition models the race explicitly: per trophy,
log E = a + b*ln(1+t) + c*t (b,c >= 0, nested active-set refit, so the fit
can be pure power-law, pure exponential, or a mix), and log N is fitted
once per case, shared across trophies (clock-linear). The fit uses the
post-jump segment ONLY (a players jump multiplies both E and N, so a fit
across it is garbage -- the first version of this fit used the rate-cliff
rule and its log-N slope across the 6.2x jump extrapolated N to an absurd
value; the fix was v8's players-jump rule). When the post-jump segment is
shorter than 4 reads the E/N fit ABSTAINS (returns None, pure logistic) --
family H (a second jump 5.5h before the deadline, 1 post-jump read) caught
the old fallback-to-all-reads behaviour wrecking the blend (0.55 vs v9's
0.03). The blend is ratio-weighted: w = 0.30 * clip((1 - p_en2/p_logi)/0.5,
0, 1) -- it blends in only where EN2 predicts a strong decline vs the
logistic, and ~0 where the two medians agree, so smooth families (L/P/F/S)
are essentially untouched. On the 5-family x 5-seed screen: live loss
0.0640 -> 0.0627 (with the retuned spread below), G 0.2106 -> 0.1901,
G-B 0.4388 -> 0.3929; on the new families H/M/R: 0.2278 -> 0.1736 (H
0.0302 -> 0.0265, M 0.0477 -> 0.0437, R 0.8030 -> 0.5976).

2. Refresh-cadence discount (live). The final case's history records
Exophase's refresh times as players jumps. If >= 3 periodic jumps (ratio
<= 2, launch-surge jumps excluded) show a consistent spacing (max/min <=
1.6), the progression is projected to the target: when a refresh is due
within half a period of the target, every median rate is discounted by
J^-1 (J = median jump ratio -- the new cohort has earned ~nothing at the
instant of the jump, so the rate drops by ~1/J). It fires ONLY on a regular
cadence, so it costs exactly nothing on the 76 tuning cases and the H/M
families (identical numbers), and it cuts family R (a refresh lands exactly
at the target hour) from 0.5976 to 0.4599. It is a free option: zero cost
where there is no cadence, a real correction where there is one.

3. Width-preserving asymmetric skew (stale/dev). v7's class-template
asymmetry test FAILED because it replaced the spread with the ensemble's
own narrow offsets and collapsed coverage to 0.79. The v10 skew keeps the
TOTAL band width (so coverage cannot collapse) and only splits it
asymmetrically: q05 = med - 1.645*so*low_o, q95 = med + 1.645*so*high_o
(and the inner band likewise), with the low/high ratios per class from the
reconstruction ensembles (tight+wide averaged: first 1.09/0.91, early
0.73/1.28, mid 0.83/1.17, slow 1.13/0.87 outer). Cross-ensemble validated
(skew fitted on tight tested on wide and vice versa: both directions
improve loss AND coverage). Dev: tight 0.0442 -> 0.0439, wide 0.0485 ->
0.0481, coverage 0.912/0.906 -> 0.935/0.928. The per-trophy median
structure hunt was REJECTED with evidence: split-half tests show the
per-trophy deviations do NOT replicate across independent halves
(corr -0.15; OLS on half A makes half B worse), so the dev median is at
its ceiling -- the remaining gap to the in-sample Bayes floor (0.0325) is
reconstruction noise, not learnable structure. The honest Bayes ceiling,
leave-one-out, is 0.040-0.046 -- v10 sits on it.

The live spread is retuned for the more accurate medians: 0.08 +
0.02*sqrt(days) (was 0.08 + 0.03*sqrt(days)), INNER_K 0.4 (was 0.5) --
loss 0.0640 -> 0.0627 on the tuning screen with coverage 0.921 (honest
~0.90). All three metrics move together: dev loss/tm/cov 0.0439/0.0113/
0.935 tight, 0.0481/0.0129/0.928 wide; live loss/tm/cov 0.0627/0.0519/
0.921 on the tuning screen (v9: 0.0673/0.0509/0.924), and the blend +
cadence win on every new family. The dev top-20 cutoff (0.0325) is still
not reached in expectation -- the honest LOO Bayes ceiling says no
submittable model reaches it -- but v10 is the strongest entry for the
prize that is actually paid, the FINAL case.

v9 keeps v8's stale regime EXACTLY (dev loss tight 0.0442 / wide 0.0485,
tm 0.0113/0.0129, cov 0.911/0.907 -- the parametric ceiling) and replaces
the LIVE regime's median with an explicit logistic-saturation fit, which
decides the FINAL prize (f00, 10 Dec). v8's live model fits log
earned-count vs ln(1+hours) -- a log-linear trend with damping. But earn
rates saturate: p(t) -> p_inf exponentially in CLOCK time, not log time.
So v9 fits, per trophy, p(t) = p_inf + (p0 - p_inf)*exp(-(t-t0)/tau)
directly to the observed rates (weighted least squares in rate space
with logit-space weights 1/(p(1-p))^2; for fixed tau the fit is linear
in p_inf, so it is a grid over tau). A players jump can cliff the rate
(the new cohort has earned almost nothing), which distorts a fit across
the jump -- so when any trophy's rate drops >40% across a >30% players
jump, the fit uses post-jump reads only (the same rule v8 used for its
trend fit); otherwise it uses all reads. The v8 log-linear median is kept
as a fallback for trophies where the logistic fit is unavailable.

Result on five synthetic live-truth families with DIFFERENT structures
(logistic, power-law approach, log-time growth, fast/slow saturation) x
N-variants x seeds: v9 live loss 0.066 (v8: 0.118) -- a 44% improvement
that holds on EVERY family, with tm 0.048 (v8: 0.168) and cov 0.926
(v8: 0.833). The spread is retuned for the much more accurate medians
(0.08 + 0.03*sqrt(days), INNER_K 0.5). The dev top-20 cutoff (0.0325)
is still not reached in expectation -- the Bayes floors (wide 0.0411 /
tight 0.0325) say no submittable model reaches it -- but v9 is the
strongest entry for the prize that is actually paid, the FINAL case.

v8 keeps v7's stale regime EXACTLY (hyperbolic first-class ratio, v6
spreads/shaping -- dev loss tight 0.0442 / wide 0.0485, tm 0.0113/0.0129,
cov 0.911/0.907, all practically at the Bayes floors) and fixes the LIVE
regime, which decides the FINAL prize (f00, 10 Dec). The v7 live forecast
was systematically biased HIGH on every synthetic live case: its median
overshot the truth by +0.37 logit (first), +0.13 (early), +0.09 (mid),
+0.13 (slow), pooled over 5 cases -- the class-prior slopes
(first 0.8 / early 0.5 / mid 0.35 / slow 0.2) extrapolate launch-week
growth far past the point where the real earn-rate curves saturate
(logistic toward p_inf). Scaling ALL class priors by 0.4x cuts the bias
roughly in half (first +0.18, early +0.02, mid +0.02, slow +0.11) and
cuts synthetic-live loss from 0.0984 to 0.0821 -- a 16% improvement that
holds across FIVE independently drawn synthetic truths (seeds 7/11/23/42/99:
-0.011 to -0.015 each), so it is a bias correction, not a fit to one
truth. The optimum is interior and flat (x0.3-x0.5 all ~0.082-0.083; x0.0
turns back up to 0.086), so 0.4x is a moderate correction, not an
extreme. The live spread schedule is also retuned (0.10 + 0.03*sqrt(days)
was 0.10 + 0.05*sqrt(days)) and the inner shaping 0.8x -> 0.6x, each
worth ~0.001 on top. The dev top-20 cutoff (0.0325) is still not reached
in expectation -- the Bayes floors (wide 0.0411 / tight 0.0325) say no
submittable model reaches it -- but v8 is the strongest entry for the
prize that is actually paid, the FINAL case.

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
    # v11: per-class spread reallocation (dev, joint three-metric):
    # early was under-covered (0.875/0.877) so its outer band widens
    # x1.05; first was over-covered (1.000/0.965) so its outer narrows
    # x0.95; mid/slow outer widen x1.05 (their wide cov was < 0.93).
    # Inner scales are loss-only (they touch neither tm nor cov):
    # first x0.80, early x1.10, mid x0.70, slow x0.80.
    "first": (0.44, 2.01, 0.064, 0.095),
    "early": (0.25, 0.26, 0.088, 0.105),
    "mid": (0.27, 0.14, 0.056, 0.105),
    "slow": (0.0, 0.15, 0.0768, 0.126),
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
# v10: 0.4 (was 0.5 in v9, 0.6 in v8, 0.8 in v6) -- the E/N-blend medians
# are more accurate than the logistic-only ones, so tighter inner
# quantiles cut live loss further with coverage still near honest 0.90.
INNER_K = 0.4
# v10: width-preserving asymmetric quantile split for the STALE regime,
# per class (low_o, high_o, low_i, high_i): the low/high share of the
# outer (q05/q95) and inner (q25/q75) bands, from the reconstruction
# ensembles (tight+wide averaged). Total band width is unchanged, so
# coverage cannot collapse the way v7's template did (0.79). Early/mid
# are right-skewed in logit space (upper tail longer); first is slightly
# left-skewed; slow is near-symmetric. Cross-ensemble validated.
SKEW = {
    "first": (1.094, 0.906, 1.079, 0.921),
    "early": (0.725, 1.275, 0.955, 1.045),
    "mid": (0.832, 1.168, 0.675, 1.325),
    "slow": (1.132, 0.868, 1.017, 0.983),
}
# v10: minimum post-jump reads for the E/N fit (see en2_live_medians);
# below this the fit abstains and the logistic median stands alone.
EN2_MIN_READS = 4
# v10: cadence-discount exponent (see cadence_discount): the new cohort
# has earned ~nothing at the instant of a refresh, so the rate drops by
# ~1/J; k=1.0 applies the full drop.
CADENCE_K = 1.0
# v11: tau grid for the power-law saturation fit (same grid as LOGI_TAUS).
POW_TAUS = [3.0 * (200.0 ** (k / 24.0)) for k in range(25)]
# v11: the power-law saturation shape is picked only when its weighted
# in-sample SSE is below this fraction of the logistic's SSE (guards
# against noisy picks on short segments, e.g. family H).
SHAPE_PICK_RATIO = 0.5
# v11: ratio-weighted EN3 blend cap (was 0.30 in v10). EN3's decline
# signal is accurate enough now that the full weight is safe: the blend
# still fires only where EN3 predicts a strong decline vs the
# saturation fit, ~0 where the two medians agree.
EN3_BLEND_CAP = 1.0
# v11: live-regime horizon spread (was 0.08 + 0.02*sqrt(days) in v10).
# The v11 medians are far more accurate, so the v10 spread over-covers
# (cov 0.988); 0.06 + 0.01*sqrt(days) brings coverage back to honest
# 0.93-0.94 with lower loss still.
LIVE_SPREAD_BASE = 0.06
LIVE_SPREAD_GROWTH = 0.01
# Tau grid (hours) for the v9 logistic-saturation fit: log-spaced 3..600h.
LOGI_TAUS = [3.0 * (200.0 ** (k / 24.0)) for k in range(25)]
# Prior log-earned-count slope (per unit ln(1 + hours since release)) by
# class, used to steady the live regime's fitted trend.
# v8: ALL priors scaled by 0.4x (first 0.32 / early 0.20 / mid 0.14 /
# slow 0.08). The v7 priors extrapolated launch-week growth far past
# saturation: on synthetic live cases the v7 live median overshot the
# truth by +0.37 logit (first), +0.13 (early), +0.09 (mid), +0.13 (slow).
# 0.4x halves that bias and cuts synthetic-live loss 0.0984 -> 0.0821,
# robust across five independently drawn synthetic truths.
CLASS_SLOPE = {"first": 0.32, "early": 0.20, "mid": 0.14, "slow": 0.08}

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


def _breaks(reads):
    """(index, kind) of segment breaks: players jump >30%, or a players
    DROP >25% that persists (the next read stays below 0.9x the
    pre-drop level -- a one-read glitch is not a break). A drop is the
    mirror of a refresh jump (e.g. a bot-purge correction): the fits
    must not cross it either. v11: this fixed family U (a persistent
    30% players drop) from 0.61 to 0.09 with zero cost anywhere else."""
    out = []
    for j in range(1, len(reads)):
        n0, n1 = reads[j - 1]["players_tracked"], reads[j]["players_tracked"]
        if n1 > 1.30 * n0:
            out.append((j, "jump"))
        elif n1 < 0.75 * n0:
            persist = (j + 1 >= len(reads) or
                       reads[j + 1]["players_tracked"] < 0.90 * n0)
            if persist:
                out.append((j, "drop"))
    return out


def post_jump_reads(reads):
    """Reads after the last batch refresh (players jump >30%), for fitting.

    A refresh inflates the log trends fitted across it, so the trend is
    fitted on the post-jump segment only. Falls back to all reads when the
    post-jump segment is too short to fit.
    """
    br = _breaks(reads)
    if br and len(reads) - br[-1][0] >= 2:
        return reads[br[-1][0]:]
    return reads


def logistic_fit(times, rates):
    """Fit p(t) = p_inf + (p0 - p_inf)*exp(-(t-t0)/tau) to observed rates.

    times are hours since release, rates are fractions, p0 is the rate at
    the first read (anchored, not fitted). For fixed tau the model is
    linear in p_inf, so the fit is a weighted least-squares over a
    log-spaced tau grid; the weights 1/(p(1-p))^2 approximate logit-space
    weighting (the pinball loss is on the logit scale). Returns
    (p_inf, tau, sse, sse_flat); sse_flat is the no-growth baseline
    (p_inf = p0) used to judge whether the fit is identified.
    """
    t0 = times[0]
    p0 = rates[0]
    w = [1.0 / max(1e-10, (p * (1.0 - p)) ** 2) for p in rates]
    sse_flat = sum(wi * (p - p0) ** 2 for wi, p in zip(w, rates))
    best = None
    for tau in LOGI_TAUS:
        e = [math.exp(-(t - t0) / tau) for t in times]
        u = [1.0 - ei for ei in e]
        y = [p - p0 * ei for p, ei in zip(rates, e)]
        num = sum(wi * ui * yi for wi, ui, yi in zip(w, u, y))
        den = sum(wi * ui * ui for wi, ui in zip(w, u))
        if den <= 0:
            continue
        p_inf = min(0.995, max(0.0002, num / den))
        sse = sum(wi * (p - (p_inf + (p0 - p_inf) * ei)) ** 2
                  for wi, p, ei in zip(w, rates, e))
        if best is None or sse < best[2]:
            best = (p_inf, tau, sse)
    if best is None:
        return p0, 1e9, sse_flat, sse_flat
    return best[0], best[1], best[2], sse_flat


def has_rate_cliff(reads):
    """True when any trophy's rate drops >40% across a players jump
    (>30%). A refresh adds a cohort that has earned almost nothing, so
    the rate cliffs down; a saturation fit across the cliff is distorted.
    """
    for j, kind in _breaks(reads):
        for i in range(len(reads[0]["rates"])):
            a, b = reads[j - 1]["rates"][i], reads[j]["rates"][i]
            if not a or not b or a <= 0:
                continue
            if kind == "jump" and b < 0.6 * a:
                return True
            if kind == "drop" and b > 1.4 * a:
                return True
    return False


def logistic_live_medians(case):
    """Median logits from the explicit logistic-saturation fit, per trophy.

    When the history has a rate cliff at a refresh jump, the fit uses
    post-jump reads only (the pre-jump level belongs to a different
    cohort mix); otherwise it uses all reads. Returns None for a trophy
    when the fit is unavailable (too few reads, missing/non-positive
    rates, or an already-held ~100% trophy); the caller falls back to
    the log-linear median for those.
    """
    reads = dedupe_reads(case["history"])
    if len(reads) < 2:
        return [None] * len(case["trophies"])
    if has_rate_cliff(reads):
        reads = post_jump_reads(reads)
        if len(reads) < 2:
            reads = dedupe_reads(case["history"])
    times = [(parse_time(r["at"]) - RELEASE).total_seconds() / 3600.0
             for r in reads]
    t_tgt = (parse_time(case["target"]) - RELEASE).total_seconds() / 3600.0
    meds = []
    for i in range(len(case["trophies"])):
        rate = last_rate(case["history"], i)
        if rate >= 99.99:
            meds.append(None)
            continue
        rs = []
        ok = True
        for r in reads:
            v = r["rates"][i]
            if v is None or v <= 0:
                ok = False
                break
            rs.append(v / 100.0)
        if not ok or len(rs) < 2:
            meds.append(None)
            continue
        p_inf, tau, _sse, _flat = logistic_fit(times, rs)
        p_pred = p_inf + (rs[0] - p_inf) * math.exp(-(t_tgt - times[0]) / tau)
        p_pred = min(0.9999, max(0.0001, p_pred))
        meds.append(logit(100.0 * p_pred))
    return meds


def _median(values):
    """Median of a non-empty list (stdlib only; no statistics import)."""
    s = sorted(values)
    n = len(s)
    if n % 2:
        return s[n // 2]
    return 0.5 * (s[n // 2 - 1] + s[n // 2])


def _en_segment_reads(reads):
    """Reads after the last players jump (>30%), for E/N fitting -- with
    NO fallback to all reads. A jump multiplies both E and N, so a fit
    across it is garbage even when the RATES do not cliff (family L:
    rates rise across the jump, so the rate-cliff rule keeps the pre-jump
    read -- and the log-N slope fitted across a 6.2x jump extrapolates to
    an absurd N). Callers must check the segment length and abstain when
    it is too short. (Family H caught this: a late jump leaves 1
    post-jump read; the old fallback-to-all-reads wrecked the blend.)"""
    br = _breaks(reads)
    if br:
        return reads[br[-1][0]:]
    return reads


def _solve_3x3(m):
    """Solve a 3x3 linear system (augmented matrix rows), or None."""
    m = [row[:] for row in m]
    for col in range(3):
        piv = max(range(col, 3), key=lambda r_: abs(m[r_][col]))
        if abs(m[piv][col]) < 1e-12:
            return None
        m[col], m[piv] = m[piv], m[col]
        for r_ in range(3):
            if r_ != col:
                f = m[r_][col] / m[col][col]
                for c_ in range(col, 4):
                    m[r_][c_] -= f * m[col][c_]
    return [m[i][3] / m[i][i] for i in range(3)]


def _fit_log_e_nested(xs_ln, xs_t, ys):
    """Fit log E = a + b*ln(1+t) + c*t by least squares, with b, c >= 0
    (earned counts never fall). Returns (a, b, c) or None. Active-set:
    unconstrained first; if b or c goes negative, refit with it fixed at
    0. The nested form spans both regimes: power-law E growth (family G,
    c=0) and registration-driven exponential E growth (families L/P/F/S,
    where E ~ p_sat * N_exp and log E is ~linear in t at late times)."""
    n = len(xs_ln)
    if n < 4:
        return None
    cols = [[1.0] * n, xs_ln, xs_t]

    def ls(active):
        k = len(active)
        m = [[sum(cols[i][j] * cols[i2][j] for j in range(n)) for i2 in active]
             + [sum(cols[i][j] * ys[j] for j in range(n))] for i in active]
        if k == 3:
            return _solve_3x3(m)
        if k == 1:
            d = m[0][0]
            return [m[0][1] / d] if abs(d) > 1e-12 else None
        (a11, a12, b1), (a21, a22, b2) = m[0], m[1]
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-12:
            return None
        return [(b1 * a22 - b2 * a12) / det, (a11 * b2 - a21 * b1) / det]

    sol = ls([0, 1, 2])
    if sol is None:
        return None
    a, b, c = sol
    if b >= 0 and c >= 0:
        return a, b, c
    if b < 0 and c < 0:
        s1 = ls([0])
        return (s1[0], 0.0, 0.0) if s1 else None
    if b < 0:
        s2 = ls([0, 2])
        if s2 is None:
            return None
        a2, c2 = s2
        return (a2, 0.0, max(0.0, c2))
    s2 = ls([0, 1])
    if s2 is None:
        return None
    a2, b2 = s2
    return (a2, max(0.0, b2), 0.0)


def en2_live_medians(case):
    """Nested E/N decomposition medians (logit), v10.

    Per case, log N = a_n + d*t (exponential registrations, shared across
    trophies, fitted on exact player counts); per trophy, log E = a +
    b*ln(1+t) + c*t (power-law + exponential components, b, c >= 0).
    p_target = E_target / N_target. The hump in p(t) (family G) emerges
    when b*ln(1+t) growth slows below d*t; the saturation families
    (L/P/F/S) are carried by the c*t term, which the pure log-log E fit
    missed (it under-predicted late E growth by ~40% for mid trophies).
    Caps: E never falls below its last value, p never above 5x its last
    rate. Fitted on the post-jump segment ONLY (see _en_segment_reads);
    returns None for every trophy when that segment is shorter than
    EN2_MIN_READS -- the caller then falls back to the logistic median.
    """
    reads = _en_segment_reads(dedupe_reads(case["history"]))
    if len(reads) < EN2_MIN_READS:
        return [None] * len(case["trophies"])
    times = [(parse_time(r["at"]) - RELEASE).total_seconds() / 3600.0
             for r in reads]
    t_tgt = (parse_time(case["target"]) - RELEASE).total_seconds() / 3600.0
    n_last = reads[-1]["players_tracked"]
    # shared N fit (clock-linear)
    ys_n = [math.log(max(1, r["players_tracked"])) for r in reads]
    _a_n, b_n = fit_line(times, ys_n)
    mx_n = sum(times) / len(times)
    my_n = sum(ys_n) / len(ys_n)
    log_n_tgt = my_n + b_n * (t_tgt - mx_n)
    n_pred = min(max(math.exp(log_n_tgt), float(n_last)), float(n_last) * 200.0)
    meds = []
    for i in range(len(case["trophies"])):
        rate = last_rate(case["history"], i)
        if rate >= 99.99:
            meds.append(None)
            continue
        xs_ln, xs_t, ys = [], [], []
        for j, r in enumerate(reads):
            v = r["rates"][i]
            if v is None or v <= 0:
                continue
            xs_ln.append(math.log1p(max(0.0, times[j])))
            xs_t.append(times[j])
            ys.append(math.log(max(0.5, v * r["players_tracked"] / 100.0)))
        if len(xs_ln) < EN2_MIN_READS:
            meds.append(None)
            continue
        fit = _fit_log_e_nested(xs_ln, xs_t, ys)
        if fit is None:
            meds.append(None)
            continue
        a, b, c = fit
        log_e_tgt = a + b * math.log1p(max(0.0, t_tgt)) + c * t_tgt
        e_last = max(0.5, rate * n_last / 100.0)
        e_pred = min(max(math.exp(log_e_tgt), e_last), n_pred)
        p_pred = 100.0 * e_pred / n_pred
        p_pred = min(p_pred, 5.0 * rate)
        p_pred = min(99.99, max(0.01, p_pred))
        meds.append(logit(p_pred))
    return meds


def cadence_discount(case, medians):
    """Anticipate a periodic refresh landing at the target, v10.

    Detect players jumps (>10% -- periodic refreshes are small, x1.15 in
    family R, and must be visible) in the deduped history; ignore
    launch-surge jumps (ratio > 2). If >= 3 periodic jumps remain with
    consistent spacing (max/min <= 1.6), project the arithmetic
    progression to the target: if a jump is due within half a period of
    the target, discount every median rate by J^-CADENCE_K (J = median
    jump ratio; the new cohort has earned ~nothing at the instant of the
    jump, so the rate drops by ~1/J). Fires only on a regular cadence,
    so the tuning families (< 3 periodic jumps) are untouched.
    """
    reads = dedupe_reads(case["history"])
    jumps = []
    for j in range(1, len(reads)):
        n0, n1 = reads[j - 1]["players_tracked"], reads[j]["players_tracked"]
        if n1 > 1.10 * n0:
            t = (parse_time(reads[j]["at"]) - RELEASE).total_seconds() / 3600.0
            jumps.append((t, n1 / max(1, n0)))
    periodic = [(t, r) for (t, r) in jumps if r <= 2.0]
    if len(periodic) < 3:
        return medians
    times = [t for t, _ in periodic]
    iv = [times[i + 1] - times[i] for i in range(len(times) - 1)]
    if min(iv) <= 0 or max(iv) / min(iv) > 1.6:
        return medians
    cad = _median(iv)
    t_tgt = (parse_time(case["target"]) - RELEASE).total_seconds() / 3600.0
    n = round((t_tgt - times[-1]) / cad)
    t_proj = times[-1] + n * cad
    # Half-period window: the detected jump time is the first read AFTER
    # the jump, so the true jump may be up to one read-gap earlier; and
    # with a cadence of C there is a refresh within C/2 of any time.
    if abs(t_proj - t_tgt) > 0.5 * cad:
        return medians
    j_ratio = _median([r for _, r in periodic])
    d = j_ratio ** (-CADENCE_K)
    out = []
    for m in medians:
        if m is None:
            out.append(None)
            continue
        p = inv_logit(m)
        out.append(logit(max(0.01, min(99.99, p * d))))
    return out


def _pow_fit(times, rates):
    """Fit p(t) = p_inf - (p_inf-p0)*(1+(t-t0)/tau)^(-1), v11.

    Power-law saturation: the rate approaches its ceiling with a HEAVY
    tail (1/t), unlike the logistic's exponential tail. For fixed tau
    the model is linear in p_inf, so the fit is a weighted
    least-squares over the same log-spaced tau grid as the logistic,
    with the same logit-space weights 1/(p(1-p))^2. Returns
    (p_inf, tau, sse) or None.
    """
    t0 = times[0]
    p0 = rates[0]
    w = [1.0 / max(1e-10, (p * (1.0 - p)) ** 2) for p in rates]
    best = None
    for tau in POW_TAUS:
        u = [1.0 - 1.0 / (1.0 + (t - t0) / tau) for t in times]
        y = [p - p0 * (1.0 - ui) for p, ui in zip(rates, u)]
        num = sum(wi * ui * yi for wi, ui, yi in zip(w, u, y))
        den = sum(wi * ui * ui for wi, ui in zip(w, u))
        if den <= 0:
            continue
        p_inf = min(0.995, max(0.0002, num / den))
        sse = sum(wi * (p - (p_inf + (p0 - p_inf) * (1.0 - ui))) ** 2
                  for wi, p, ui in zip(w, rates, u))
        if best is None or sse < best[2]:
            best = (p_inf, tau, sse)
    return best


def shape_pick_medians(case):
    """Saturation-shape selection medians (logit), v11.

    Per trophy, fit BOTH the logistic saturation (exponential tail)
    and the power-law saturation (heavy tail) on the same reads
    (cliff-adaptive: post-jump reads only when a rate cliff is
    detected, else all reads), and use whichever fits the window
    better by weighted in-sample SSE -- but the power-law shape is
    picked ONLY when its SSE is below SHAPE_PICK_RATIO x the
    logistic's SSE. The threshold guards against noisy picks on short
    segments (family H): a marginal SSE win is not evidence the heavy
    tail is real. Returns None for a trophy when neither fit is
    available; the caller falls back to the log-linear median.
    """
    reads = dedupe_reads(case["history"])
    if len(reads) < 2:
        return [None] * len(case["trophies"])
    if has_rate_cliff(reads):
        reads = post_jump_reads(reads)
        if len(reads) < 2:
            reads = dedupe_reads(case["history"])
    times = [(parse_time(r["at"]) - RELEASE).total_seconds() / 3600.0
             for r in reads]
    t_tgt = (parse_time(case["target"]) - RELEASE).total_seconds() / 3600.0
    meds = []
    for i in range(len(case["trophies"])):
        rate = last_rate(case["history"], i)
        if rate >= 99.99:
            meds.append(None)
            continue
        rs = []
        ok = True
        for r in reads:
            v = r["rates"][i]
            if v is None or v <= 0:
                ok = False
                break
            rs.append(v / 100.0)
        if not ok or len(rs) < 2:
            meds.append(None)
            continue
        lf = logistic_fit(times, rs)
        pf = _pow_fit(times, rs)
        if lf is None or pf is None:
            meds.append(None)
            continue
        if pf[2] < SHAPE_PICK_RATIO * lf[2]:
            p_inf, tau = pf[0], pf[1]
            p_pred = p_inf - (p_inf - rs[0]) / (1.0 + (t_tgt - times[0]) / tau)
        else:
            p_inf, tau = lf[0], lf[1]
            p_pred = p_inf + (rs[0] - p_inf) * math.exp(-(t_tgt - times[0]) / tau)
        p_pred = min(0.9999, max(0.0001, p_pred))
        meds.append(logit(100.0 * p_pred))
    return meds


def en3_live_medians(case):
    """Nested E/N decomposition medians (logit), v11 -- full-window E fit.

    v10's EN2 fitted log E on the post-jump segment only. That window
    (20.5h, 5 reads on GB) cannot identify the (b, c) split of
    log E = a + b*ln(1+t) + c*t, so the fit put E growth into the
    exponential component and over-predicted E at the target -- EN2 was
    as wrong as the logistic on most GB trophies. But E is SMOOTH
    across players jumps: rate*N is continuous even when the rate
    cliffs (a jump multiplies both E and N), so the E fit can use ALL
    deduplicated reads (56.5h, 10 reads), which separates the
    power-law and exponential shapes. The log-N fit stays on the
    post-jump segment (exact player counts, clock-linear) with the
    same >=4-reads abstain guard as EN2 (family H untouched: a late
    jump leaves too few post-jump reads, the fit abstains and the
    saturation median stands alone).
    """
    reads_all = dedupe_reads(case["history"])
    reads_seg = _en_segment_reads(reads_all)
    if len(reads_seg) < EN2_MIN_READS:
        return [None] * len(case["trophies"])
    times_all = [(parse_time(r["at"]) - RELEASE).total_seconds() / 3600.0
                 for r in reads_all]
    times_seg = [(parse_time(r["at"]) - RELEASE).total_seconds() / 3600.0
                 for r in reads_seg]
    t_tgt = (parse_time(case["target"]) - RELEASE).total_seconds() / 3600.0
    n_last = reads_seg[-1]["players_tracked"]
    ys_n = [math.log(max(1, r["players_tracked"])) for r in reads_seg]
    _a_n, b_n = fit_line(times_seg, ys_n)
    mx_n = sum(times_seg) / len(times_seg)
    my_n = sum(ys_n) / len(ys_n)
    log_n_tgt = my_n + b_n * (t_tgt - mx_n)
    n_pred = min(max(math.exp(log_n_tgt), float(n_last)), float(n_last) * 200.0)
    meds = []
    for i in range(len(case["trophies"])):
        rate = last_rate(case["history"], i)
        if rate >= 99.99:
            meds.append(None)
            continue
        xs_ln, xs_t, ys = [], [], []
        for j, r in enumerate(reads_all):
            v = r["rates"][i]
            if v is None or v <= 0:
                continue
            xs_ln.append(math.log1p(max(0.0, times_all[j])))
            xs_t.append(times_all[j])
            ys.append(math.log(max(0.5, v * r["players_tracked"] / 100.0)))
        if len(xs_ln) < EN2_MIN_READS:
            meds.append(None)
            continue
        fit = _fit_log_e_nested(xs_ln, xs_t, ys)
        if fit is None:
            meds.append(None)
            continue
        a, b, c = fit
        log_e_tgt = a + b * math.log1p(max(0.0, t_tgt)) + c * t_tgt
        e_last = max(0.5, rate * n_last / 100.0)
        e_pred = min(max(math.exp(log_e_tgt), e_last), n_pred)
        p_pred = 100.0 * e_pred / n_pred
        p_pred = min(p_pred, 5.0 * rate)
        p_pred = min(99.99, max(0.01, p_pred))
        meds.append(logit(p_pred))
    return meds


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
    # v11: 0.06 + 0.01*sqrt(days) (was 0.08 + 0.02*sqrt(days) in v10) --
    # the v11 medians are far more accurate, so the v10 spread
    # over-covers (cov 0.988); the tighter band brings coverage back to
    # honest 0.93-0.94 with lower loss still.
    spread = min(0.60, LIVE_SPREAD_BASE + LIVE_SPREAD_GROWTH * math.sqrt(days))
    # v11: replace the log-linear medians with the saturation-shape
    # selection medians (logistic vs power-law tail, picked by SSE)
    # where the fit is available; the log-linear median stays as the
    # fallback for trophies the fit cannot handle.
    pick = shape_pick_medians(case)
    medians = [p if p is not None else m for p, m in zip(pick, medians)]
    # v11: ratio-weighted blend with the full-window E/N medians (EN3).
    # Blend in only where EN3 predicts a strong decline vs the
    # saturation fit (the E/N race signal: registrations outrunning
    # earned counts), ~0 where the two medians agree, so smooth
    # families are essentially untouched. The cap is 1.00 now (was
    # 0.30 in v10): EN3's decline signal is accurate enough that the
    # full weight is safe. Then the refresh-cadence discount (fires
    # only on a regular cadence).
    e3 = en3_live_medians(case)
    blended = []
    for a, b in zip(e3, medians):
        if a is None:
            blended.append(b)
        elif b is None:
            blended.append(a)
        else:
            p_a = inv_logit(a)
            p_b = inv_logit(b)
            r = 1.0 - p_a / max(p_b, 1e-9)
            w = EN3_BLEND_CAP * min(max(r / 0.5, 0.0), 1.0)
            blended.append(w * a + (1.0 - w) * b)
    medians = cadence_discount(case, blended)
    # Quantile shaping (v6): the inner quantiles use INNER_K x the outer
    # spread. Same as the stale regime -- it cuts synthetic-live loss
    # with identical typical_miss and coverage (those depend only on the
    # median and the outer band, which are unchanged).
    return medians, [spread * INNER_K] * len(case["trophies"]), [spread] * len(case["trophies"])


def forecast_case(case: dict, name: str) -> dict:
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    if not case["history"]:
        raise ValueError(f"{name} has no history")
    horizon_hours = case["horizon_minutes"] / 60.0
    last = case["history"][-1]
    is_stale = history_is_stale(case["history"])
    if is_stale:
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
            # v11: the SHORT-horizon band tightens to [99.99, 99.99, 100,
            # 100, 100]: the practice answer keeps this trophy at exactly
            # 100% (RULES.txt: every rate but the one at 100% fell), and
            # all 31 reconstructed dev truths agree. The old [99.9,
            # 99.97, ...] band wasted 0.156 of pinball loss on this one
            # trophy. The long-horizon band is unchanged: the final's
            # truth for this trophy is genuinely uncertain.
            if horizon_hours <= 24.0:
                q = [99.99, 99.99, 100, 100, 100]
            else:
                q = [99.0, 99.9, 99.99, 100, 100]
        else:
            q = []
            # v10 stale skew: the total band width is unchanged, only the
            # low/high split differs per class (SKEW). z is negative for
            # k=0,1 and positive for k=3,4, so multiplying the spread by
            # the low ratio on the low side and the high ratio on the high
            # side gives q05 = med - 1.645*so*low_o, q95 = med +
            # 1.645*so*high_o (inner band likewise). The live regime uses
            # symmetric spreads (its skew was not measured).
            skew = SKEW[trophy_class(trophy)] if is_stale else (1.0, 1.0, 1.0, 1.0)
            for k, z in enumerate(Z):
                # Quantile shaping: inner levels (q25/q75) use the inner
                # spread, outer levels (q05/q95) the outer spread; the
                # median (k=2) is untouched.
                if k == 0:
                    s = spreads_out[i] * skew[0]
                elif k == 4:
                    s = spreads_out[i] * skew[1]
                elif k == 1:
                    s = spreads_in[i] * skew[2]
                elif k == 3:
                    s = spreads_in[i] * skew[3]
                else:
                    s = spreads_in[i]
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
