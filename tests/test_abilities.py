from dota2_coach.opendota.abilities import kill_key_matches, named_ability_targets, npc_hero_label
from dota2_coach.opendota.constants import GameConstants


def test_npc_hero_label() -> None:
    assert npc_hero_label("npc_dota_hero_drow_ranger") == "Drow Ranger"
    assert npc_hero_label("npc_dota_hero_shadow_shaman") == "Shadow Shaman"


def test_kill_key_matches_npc_alias() -> None:
    constants = GameConstants(
        heroes={11: "Shadow Fiend"},
        hero_npcs={11: "npc_dota_hero_nevermore"},
    )
    sf = {"hero_id": 11}
    assert kill_key_matches("npc_dota_hero_nevermore", sf, constants)
    assert not kill_key_matches("npc_dota_hero_zuus", sf, constants)


def test_named_ability_targets_skips_empty() -> None:
    raw = {
        "bane_fiends_grip": {"npc_dota_hero_drow_ranger": 2, "npc_dota_hero_muerta": 3},
        "bane_enfeeble": {"npc_dota_hero_crystal_maiden": 2},
        "bane_brain_sap": {},
    }
    named = named_ability_targets(raw)
    assert named["bane_fiends_grip"] == {"Drow Ranger": 2, "Muerta": 3}
    assert named["bane_enfeeble"] == {"Crystal Maiden": 2}
    assert "bane_brain_sap" not in named
