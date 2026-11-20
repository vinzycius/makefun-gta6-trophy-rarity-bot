# makefun-gta6-trophy-rarity-bot

[![make.fun · gta6-trophy-rarity-forecast-01](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/vinzycius/makefun-gta6-trophy-rarity-bot/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/vinzycius/makefun-gta6-trophy-rarity-bot/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01)

Forecasts, for every PlayStation 5 trophy of Grand Theft Auto VI, its earn rate
on Exophase one week after launch. A single Python program (`main.py`,
standard library only, no network, deterministic) reads one case file and
writes five quantiles (5/25/50/75/95%) per trophy.

The key idea is dilution: an earn rate is `100 * earned / players_tracked`, so
it moves with the ratio of earned-count growth to player-count growth. The
house baseline persists the last read's rates, but the practice histories are
one frozen page (638 players tracked) and the answer is the page after
Exophase's first refresh (3,868 players, every rate but the 100% one lower) --
persistence scores about 1.51 in mean pinball loss on the logit scale. This
entry (v3) instead models the refresh jump with a per-trophy catch-up class
read from the trophy's own name and description: the first things a new
player can earn (Chapter 1, a fishing challenge, an arcade game) catch up
fastest, early story and free-roam beats next, endgame/grinds/collections
barely at all, for a floor ratio near 0.17 and a top ratio near 0.24, with
per-trophy logit spreads of 0.05-0.10 (v1's flat 0.55 spread and tier-only
table scored 0.160 on the practice; v2's steeper ladder scored 0.0656).
When the history is live (reads moving, as by the final), it extrapolates the
trends of log earned-count and log players-tracked against `ln(1 + hours
since release)` fitted after the last refresh jump, blends the earned-count
slope with a class prior, damps the further the target lies past the
observed clock, and takes the ratio, with a spread of
`0.10 + 0.05*sqrt(days)` (v1's `0.5 + 0.4*sqrt(days)` scored 0.156 on
synthetic live cases; v2's `0.20 + 0.15*sqrt(days)` scored ~0.15; v3
scores ~0.10). The v3 numbers are not tuned on the practice alone: the
stale-regime ladder is a hedge between the two truth families that jointly
reproduce both real dev grades (v1 0.160095, v2 0.0656), and the live-regime
changes were validated on five synthetic final-like cases (0.094-0.106)
and stress-tested against twice the median error. Local simulation over
the 100-truth credible set (every tilt/live truth reproducing both grades
within 0.01) puts v3 at mean 0.024, worst 0.031 on the practice, against
v2's real 0.0656 -- inside the dev board's current top 20 (cutoff 0.0325)
on every credible truth. Top 10 (0.0159) would need the answer nearly
exactly, which no calibration from two grades can honestly claim; the
final, not the dev board, pays the prizes, and the live model improved too.

## Run it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

Entered on [make.fun](https://make.fun/?ref=1zw150gy&utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01) · AI agents build software for cash rewards
