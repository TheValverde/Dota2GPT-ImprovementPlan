from dota2_coach.opendota.abilities import named_ability_targets, npc_hero_label


def test_npc_hero_label() -> None:
    assert npc_hero_label("npc_dota_hero_drow_ranger") == "Drow Ranger"
    assert npc_hero_label("npc_dota_hero_shadow_shaman") == "Shadow Shaman"


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
