# Fantasy scoring

Points use the OpenDota published weights, plus Valve/Liquipedia **0.15 per assist**. Unparsed matches still score KDA, last hits, and GPM; ward/stun/teamfight fields count as zero until OpenDota has a parse.

```
3
+ 0.3 * kills
- 0.3 * deaths
+ 0.15 * assists
+ 0.003 * (last hits + denies)
+ 0.002 * GPM
+ 1 * tower kills
+ 1 * roshan kills
+ 3 * teamfight participation
+ 0.5 * observers placed
+ 0.5 * camps stacked
+ 0.25 * runes
+ 4 * first blood
+ 0.05 * stuns
```

Rounded to one decimal, same as OpenDota.

## Spans

| Unit | Meaning |
| --- | --- |
| `days` | Matches with `start_time` inside the last N days |
| `weeks` | Last N * 7 days |
| `months` | Last N * 30 days |
| `matches` | Most recent N games, newest first |

The overlay lets you add any number of accounts. Refresh pulls OpenDota again for the current span. Totals, averages, best, worst, and a sparkline come from the local SQLite cache.

## Filters

| Checkbox | Field | Kept when |
| --- | --- | --- |
| Ranked only | `lobby_type` | 5, 6, or 7 (ranked, including legacy) |
| Hide turbo | `game_mode` | anything except 23 |

Filters apply to cached rows for the active span. They do not change how points are calculated. Turn both on to score ranked non-turbo games only.

## Ranked field

Selecting a tracked player loads a **ranked field**: every named account that loaded into that player's ranked games in the span (cap 40 newest). Points use the same formula, but only on those shared lobbies, so a duo is compared on the same games as random pub opponents.

The overlay table keeps **regulars**: you, your duo, and anyone with 2+ shared ranked games. One-game cores still count toward "you are X of Y by average," but they are listed as a count so a single stomp does not bury the duo.

| Label | Meaning |
| --- | --- |
| You | The tracked account |
| Duo | Highest teammate-game count, at least 2 ranked games on your team |
| Stack | Other repeated teammates (2+ games) |
| Team / Enemy / Lobby | Everyone else in those ranked matches |

Unparsed ranked replays are submitted to OpenDota automatically (up to 10 per pass, 10 rate-limit calls each). Ward, stun, and teamfight points fill in after the parse. Valve replays usually expire after about 10 days.


