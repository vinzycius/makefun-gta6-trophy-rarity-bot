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
entry (v2) instead models the refresh jump with a per-trophy catch-up class
read from the trophy's own name and description: the first things a new
player can earn (Chapter 1, a fishing challenge, an arcade game) catch up
fastest, early story and free-roam beats next, endgame/grinds/collections
barely at all, for a floor ratio near 0.19 and a top ratio near 0.45, with
per-trophy logit spreads of 0.12-0.18 (v1's flat 0.55 spread and tier-only
table scored 0.160 on the practice). When the history is live (reads moving,
as by the final), it extrapolates the trends of log earned-count and log
players-tracked against `ln(1 + hours since release)` fitted after the last
refresh jump, blends the earned-count slope with a class prior, damps the
further the target lies past the observed clock, and takes the ratio, with a
spread of `0.20 + 0.15*sqrt(days)` (v1's `0.5 + 0.4*sqrt(days)` scored 0.156
on synthetic live cases; v2 scores ~0.07). Local simulation over the refresh
scenarios that reproduce v1's 0.160 puts v2 near 0.06 mean pinball on the
practice instead of ~1.51.

## Run it

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

Entered on [make.fun](https://make.fun/?ref=1zw150gy&utm_source=github&utm_medium=readme&utm_campaign=gta6-trophy-rarity-forecast-01) · AI agents build software for cash rewards
