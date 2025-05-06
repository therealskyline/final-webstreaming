import pytest

from .data import episode_data, season_data

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_episodes():
    assert episode_data.one_piece_season1 == await season_data.one_piece[0].episodes()
    assert episode_data.gumball_season1 == await season_data.gumball[0].episodes()
    assert episode_data.mha_season1 == await season_data.mha[0].episodes()
