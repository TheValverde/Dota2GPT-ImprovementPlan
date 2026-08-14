from __future__ import annotations

RUBRICS: dict[str, list[str]] = {
    "Mid": [
        "Rune control: power runes are a mid resource. Check rune pickups against the fight timings.",
        "Tower trades: winning the lane must convert into the mid T1 or a covered rotation. A rotation that costs the T1 is a trade; say whether it paid.",
        "Rotation tax: every side-lane play has a price in CS and tower damage. Name the price, not just the kills.",
        "Item pace: bottle, boots, and the first damage item against the lane state. A winning mid with a late key item usually means deaths or wasted moves; find them.",
    ],
    "Safe core": [
        "Farm-to-objective conversion: net worth leads must show up as towers, Roshan, or map control within a few minutes.",
        "Death cost: each death delays an item timing. Name the item and the delay.",
        "Fight selection: a carry who joins every skirmish trades farm for kills; check whether the trades paid.",
    ],
    "Offlane": [
        "Space creation: the offlaner's job is making the enemy carry's lane and jungle unsafe. Check pressure against the enemy carry's farm curve.",
        "Engage timing: initiations should line up with teammate cooldowns and item spikes.",
        "Survivability: dying first in every fight is only right if the follow-up lands.",
    ],
    "Safe support": [
        "Vision timing: wards should land before fights and objectives, not after. Compare ward times with fight times.",
        "Lane protection: the carry's early CS and deaths are partly the support's scoreboard.",
        "Courier and pull plays: small resource denials early are this role's kills.",
    ],
    "Off support": [
        "Sacrificial spacing: dying to buy the offlaner XP can be right; dying without a trade is not.",
        "Stacking and pulls: check camps stacked against the timer.",
        "Rotations: an off support who never leaves the lane after minute 8 is idle; check mid and rune presence.",
    ],
    "Roam": [
        "Every roam has a cost somewhere; check what the lanes lost while roaming and what the roam bought.",
    ],
    "Jungle": [
        "Jungle farm must beat lane farm to justify itself; compare GPM against the lanes.",
    ],
}


def rubric_for(assignment: str | None) -> list[str]:
    if not assignment:
        return []
    return RUBRICS.get(str(assignment), [])
