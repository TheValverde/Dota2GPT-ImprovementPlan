from dota2_coach.opendota.roles import infer_assignment


def test_safe_core_vs_support_from_farm(sample_match: dict) -> None:
    players = sample_match["players"]
    carry = players[0]
    support = players[1]
    teammates = [carry, support]
    assert infer_assignment(carry, teammates)["label"] == "Safe core"
    assert infer_assignment(support, teammates)["label"] == "Safe support"


def test_mid_jungle_roam_and_unknown() -> None:
    assert infer_assignment({"lane_role": 2})["label"] == "Mid"
    assert infer_assignment({"lane_role": 4})["label"] == "Jungle"
    assert infer_assignment({"is_roaming": True, "lane_role": 1})["label"] == "Roam"
    assert infer_assignment({})["label"] == "Unknown"


def test_offlane_split_by_farm() -> None:
    offlane = {"lane_role": 3, "gold_per_min": 520, "last_hits": 180}
    support = {"lane_role": 3, "gold_per_min": 250, "last_hits": 40, "obs_placed": 12}
    assert infer_assignment(offlane, [offlane, support])["label"] == "Offlane"
    assert infer_assignment(support, [offlane, support])["label"] == "Off support"


def test_solo_safe_lane_uses_wards() -> None:
    support = {
        "lane_role": 1,
        "gold_per_min": 260,
        "last_hits": 40,
        "observer_wards_placed": 10,
    }
    assert infer_assignment(support)["label"] == "Safe support"
