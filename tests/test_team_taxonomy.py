from dataclasses import FrozenInstanceError

import pytest

from polymarket_alpha_lab.team_taxonomy import (
    TEAM_IDS,
    TeamProfile,
    build_default_team_profiles,
    require_category_id,
    require_team_category_pair,
    require_team_id,
)


def test_default_team_profiles_cover_medium_taxonomy_and_are_frozen():
    profiles = build_default_team_profiles()

    assert tuple(profile.team_id for profile in profiles) == TEAM_IDS
    assert "crypto_btc" in TEAM_IDS
    assert "sports_basketball" in TEAM_IDS
    assert len(profiles) == 10
    assert all(profile.paper_only is True for profile in profiles)
    assert all(profile.report_only is True for profile in profiles)
    assert all(profile.readonly is True for profile in profiles)

    with pytest.raises(FrozenInstanceError):
        profiles[0].display_name = "changed"  # type: ignore[misc]


def test_team_profile_validates_team_category_and_agent_roles():
    profile = TeamProfile(
        team_id="crypto_btc",
        display_name="Crypto BTC",
        primary_categories=("finance.crypto.btc",),
        agent_roles=("btc_lead_forecaster", "btc_memory_postmortem"),
    )

    assert profile.team_id == "crypto_btc"
    assert profile.primary_categories == ("finance.crypto.btc",)

    with pytest.raises(ValueError, match="team_id must be a known team"):
        require_team_id("team_id", "unknown_team")

    with pytest.raises(ValueError, match="category_id must be a known category"):
        require_category_id("category_id", "unknown.category")

    with pytest.raises(ValueError, match="agent_roles must contain canonical strings"):
        TeamProfile(
            team_id="crypto_btc",
            display_name="Crypto BTC",
            primary_categories=("finance.crypto.btc",),
            agent_roles=(" bad ",),
        )


def test_team_category_pair_must_match_default_taxonomy():
    assert (
        require_team_category_pair(
            "team_id",
            "crypto_btc",
            "category_id",
            "finance.crypto.btc",
        )
        == ("crypto_btc", "finance.crypto.btc")
    )

    with pytest.raises(ValueError, match="category_id must match team_id"):
        require_team_category_pair(
            "team_id",
            "crypto_btc",
            "category_id",
            "finance.crypto.eth",
        )

    with pytest.raises(ValueError, match="team_id must be a known team"):
        require_team_category_pair(
            "team_id",
            "unknown_team",
            "category_id",
            "finance.crypto.btc",
        )
