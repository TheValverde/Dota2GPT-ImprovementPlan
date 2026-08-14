from dota2_coach.opendota.lanes import (
    describe_lane_matchup,
    lane_opponents,
    lane_partners,
    opposing_lane_role,
    physical_lane_label,
)


def _lobby() -> list[dict]:
    """Dire safelane Bane/Luna vs Radiant offlane Pudge/Kunkka. Drow/WD are Radiant safe."""
    return [
        {"hero_id": 7, "personaname": "ES", "player_slot": 0, "isRadiant": True, "lane": 2, "lane_role": 2},
        {"hero_id": 30, "personaname": "WD", "player_slot": 1, "isRadiant": True, "lane": 1, "lane_role": 1},
        {"hero_id": 23, "personaname": "Kunkka", "player_slot": 2, "isRadiant": True, "lane": 3, "lane_role": 3},
        {"hero_id": 6, "personaname": "Drow", "player_slot": 3, "isRadiant": True, "lane": 1, "lane_role": 1},
        {"hero_id": 14, "personaname": "Pudge", "player_slot": 4, "isRadiant": True, "lane": 3, "lane_role": 3},
        {"hero_id": 3, "personaname": "Hugo", "player_slot": 128, "isRadiant": False, "lane": 3, "lane_role": 1},
        {"hero_id": 48, "personaname": "Luna", "player_slot": 129, "isRadiant": False, "lane": 3, "lane_role": 1},
        {"hero_id": 145, "personaname": "Kez", "player_slot": 130, "isRadiant": False, "lane": 2, "lane_role": 2},
        {"hero_id": 108, "personaname": "Abaddon", "player_slot": 131, "isRadiant": False, "lane": 1, "lane_role": 3},
        {"hero_id": 90, "personaname": "KotL", "player_slot": 132, "isRadiant": False, "lane": 1, "lane_role": 3},
    ]


def test_opposing_lane_role() -> None:
    assert opposing_lane_role(1) == 3
    assert opposing_lane_role(3) == 1
    assert opposing_lane_role(2) == 2
    assert opposing_lane_role(4) is None
    assert physical_lane_label(3) == "Top"
    assert physical_lane_label(1) == "Bottom"


def test_dire_safelane_faces_radiant_offlane_not_enemy_safe() -> None:
    lobby = _lobby()
    hugo = lobby[5]
    names = {player["personaname"] for player in lane_opponents(hugo, lobby)}
    assert names == {"Pudge", "Kunkka"}
    assert "Drow" not in names
    assert "WD" not in names
    partners = {player["personaname"] for player in lane_partners(hugo, lobby)}
    assert partners == {"Luna"}


def test_unparsed_uses_inverted_lane_role() -> None:
    lobby = []
    for player in _lobby():
        row = dict(player)
        row.pop("lane")
        lobby.append(row)
    hugo = next(player for player in lobby if player["personaname"] == "Hugo")
    names = {player["personaname"] for player in lane_opponents(hugo, lobby)}
    assert names == {"Pudge", "Kunkka"}


def test_radiant_safelane_faces_dire_offlane() -> None:
    lobby = _lobby()
    drow = next(player for player in lobby if player["personaname"] == "Drow")
    names = {player["personaname"] for player in lane_opponents(drow, lobby)}
    assert names == {"Abaddon", "KotL"}


def test_describe_lane_matchup_names_top_lane() -> None:
    lobby = _lobby()
    hugo = lobby[5]
    matchup = describe_lane_matchup(hugo, lobby, lambda hero_id: f"Hero {hero_id}")
    assert matchup["map_lane"] == "Top"
    assert {row["name"] for row in matchup["laned_against"]} == {"Pudge", "Kunkka"}
    assert matchup["laned_with"][0]["name"] == "Luna"
    assert "safelane" in matchup["lane_matchup_note"].lower()
