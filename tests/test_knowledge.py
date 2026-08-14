from dota2_coach.analysis.ability_facts import facts_for_heroes
from dota2_coach.analysis.rubrics import rubric_for


def test_facts_only_for_heroes_in_lobby() -> None:
    facts = facts_for_heroes(["Bane", "Zeus", "Techies", ""])
    assert "Bane" in facts
    assert "Zeus" in facts
    assert "Techies" not in facts
    assert any("cast range" in line for line in facts["Bane"])


def test_rubric_matches_assignment() -> None:
    mid = rubric_for("Mid")
    assert any("Rune" in line for line in mid)
    assert rubric_for("Off support")
    assert rubric_for(None) == []
    assert rubric_for("Unknown label") == []
