from dota2_coach.opendota.filters import FantasyFilters, match_passes_filters


def test_ranked_only_keeps_ranked_lobbies() -> None:
    ranked = FantasyFilters(ranked_only=True)
    assert match_passes_filters({"lobby_type": 7, "game_mode": 22}, ranked)
    assert match_passes_filters({"lobby_type": 5, "game_mode": 22}, ranked)
    assert not match_passes_filters({"lobby_type": 0, "game_mode": 22}, ranked)
    assert not match_passes_filters({"game_mode": 22}, ranked)


def test_hide_turbo_uses_game_mode_id() -> None:
    hide = FantasyFilters(hide_turbo=True)
    assert match_passes_filters({"lobby_type": 7, "game_mode": 22}, hide)
    assert not match_passes_filters({"lobby_type": 7, "game_mode": 23}, hide)
    assert not match_passes_filters(
        {"lobby_type": 7, "game_mode_id": 23, "game_mode": "All Pick"},
        hide,
    )
    assert match_passes_filters(
        {"lobby_type": 7, "game_mode_id": 22, "game_mode": "Turbo"},
        hide,
    )
