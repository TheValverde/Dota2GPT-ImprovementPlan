from dota2_coach.opendota.benchmarks import (
    benchmarks_from_hero_curve,
    extract_match_benchmarks,
    interpolate_percentile,
)


def test_extract_match_benchmarks(sample_match: dict) -> None:
    marks = extract_match_benchmarks(sample_match["players"][0])
    assert marks["gold_per_min"] == {"raw": 720.0, "percentile": 72}
    assert marks["xp_per_min"]["percentile"] == 41


def test_interpolate_percentile() -> None:
    curve = [
        {"percentile": 0.5, "value": 600},
        {"percentile": 0.8, "value": 750},
    ]
    assert interpolate_percentile(curve, 600) == 50
    assert interpolate_percentile(curve, 750) == 80
    assert interpolate_percentile(curve, 675) == 65
    assert interpolate_percentile(curve, 100) == 50
    assert interpolate_percentile(curve, 900) == 80


def test_hero_curve_fallback() -> None:
    player = {"gold_per_min": 675, "kills": 12, "hero_damage": None}
    curve = {
        "result": {
            "gold_per_min": [
                {"percentile": 0.5, "value": 600},
                {"percentile": 0.8, "value": 750},
            ]
        }
    }
    marks = benchmarks_from_hero_curve(player, curve, duration_seconds=2460)
    assert marks["gold_per_min"]["percentile"] == 65
    assert "hero_damage_per_min" not in marks
