from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

SpanUnit = Literal["matches", "days", "weeks", "months"]
VALID_UNITS: tuple[SpanUnit, ...] = ("matches", "days", "weeks", "months")


@dataclass(frozen=True)
class Span:
    amount: int
    unit: SpanUnit

    def __post_init__(self) -> None:
        if self.amount < 1:
            raise ValueError("Span amount must be at least 1.")
        if self.unit not in VALID_UNITS:
            raise ValueError(f"Unknown span unit '{self.unit}'.")

    def as_days(self) -> int | None:
        if self.unit == "days":
            return self.amount
        if self.unit == "weeks":
            return self.amount * 7
        if self.unit == "months":
            return self.amount * 30
        return None

    def match_limit(self) -> int | None:
        if self.unit == "matches":
            return min(self.amount, 200)
        return None

    def fetch_limit(self) -> int:
        if self.unit == "matches":
            return min(self.amount, 200)
        return 200

    def label(self) -> str:
        name = self.unit if self.amount != 1 else self.unit.rstrip("s")
        if self.unit == "matches" and self.amount == 1:
            name = "match"
        return f"{self.amount} {name}"


def parse_span(amount: int, unit: str) -> Span:
    if unit not in VALID_UNITS:
        raise ValueError(f"Span unit must be one of: {', '.join(VALID_UNITS)}.")
    return Span(amount=amount, unit=unit)  # type: ignore[arg-type]


def _num(*values: Any) -> float:
    for value in values:
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return 0.0


# OpenDota core weights, plus Valve/Liquipedia assist value.
WEIGHTS = {
    "base": 3.0,
    "kills": 0.3,
    "deaths": -0.3,
    "assists": 0.15,
    "last_hits": 0.003,
    "gold_per_min": 0.002,
    "tower_kills": 1.0,
    "roshan_kills": 1.0,
    "teamfight_participation": 3.0,
    "obs_placed": 0.5,
    "camps_stacked": 0.5,
    "rune_pickups": 0.25,
    "firstblood_claimed": 4.0,
    "stuns": 0.05,
}


@dataclass(frozen=True)
class FantasyScore:
    total: float
    breakdown: dict[str, float]
    parsed: bool


def score_match(stats: dict[str, Any]) -> FantasyScore:
    last_hits = _num(stats.get("last_hits")) + _num(stats.get("denies"))
    breakdown = {
        "base": WEIGHTS["base"],
        "kills": round(WEIGHTS["kills"] * _num(stats.get("kills")), 4),
        "deaths": round(WEIGHTS["deaths"] * _num(stats.get("deaths")), 4),
        "assists": round(WEIGHTS["assists"] * _num(stats.get("assists")), 4),
        "last_hits": round(WEIGHTS["last_hits"] * last_hits, 4),
        "gold_per_min": round(WEIGHTS["gold_per_min"] * _num(stats.get("gold_per_min")), 4),
        "tower_kills": round(
            WEIGHTS["tower_kills"] * _num(stats.get("tower_kills"), stats.get("towers_killed")),
            4,
        ),
        "roshan_kills": round(
            WEIGHTS["roshan_kills"] * _num(stats.get("roshan_kills"), stats.get("roshans_killed")),
            4,
        ),
        "teamfight_participation": round(
            WEIGHTS["teamfight_participation"]
            * _num(stats.get("teamfight_participation")),
            4,
        ),
        "obs_placed": round(
            WEIGHTS["obs_placed"] * _num(stats.get("obs_placed"), stats.get("observers_placed")),
            4,
        ),
        "camps_stacked": round(WEIGHTS["camps_stacked"] * _num(stats.get("camps_stacked")), 4),
        "rune_pickups": round(
            WEIGHTS["rune_pickups"] * _num(stats.get("rune_pickups"), stats.get("runes_grabbed")),
            4,
        ),
        "firstblood_claimed": round(
            WEIGHTS["firstblood_claimed"]
            * _num(stats.get("firstblood_claimed"), stats.get("first_blood")),
            4,
        ),
        "stuns": round(WEIGHTS["stuns"] * _num(stats.get("stuns")), 4),
    }
    parsed = any(
        stats.get(key) is not None
        for key in (
            "stuns",
            "teamfight_participation",
            "obs_placed",
            "camps_stacked",
            "rune_pickups",
        )
    )
    total = round(sum(breakdown.values()), 1)
    return FantasyScore(total=total, breakdown=breakdown, parsed=parsed)
