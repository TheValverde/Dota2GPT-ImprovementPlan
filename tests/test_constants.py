from dota2_coach.opendota.constants import constants_from_payloads


def test_constants_from_payloads() -> None:
    constants = constants_from_payloads(
        heroes={"1": {"id": 1, "localized_name": "Anti-Mage"}},
        items={"blink": {"id": 1, "dname": "Blink Dagger"}},
        game_modes={"22": {"id": 22, "name": "game_mode_all_pick"}},
        lobby_types={"7": {"id": 7, "name": "lobby_type_ranked"}},
    )
    assert constants.hero_name(1) == "Anti-Mage"
    assert constants.item_name(1) == "Blink Dagger"
    assert constants.game_mode_name(22) == "All Pick"
    assert constants.lobby_name(7) == "Ranked"
