import pytest

from polymarket_alpha_lab.central_data_contracts import SourceDefinition
from polymarket_alpha_lab.central_data_registry import (
    DEFAULT_SOURCE_DEFINITIONS,
    DEFAULT_TEAM_SOURCE_REQUIREMENTS,
    SourceRegistry,
    TeamSourceRequirement,
    build_default_source_registry,
)


def source(source_id: str = "gamma", family: str = "polymarket_gamma") -> SourceDefinition:
    return SourceDefinition(
        source_id=source_id,
        source_family=family,
        url_template="https://gamma-api.polymarket.com/markets",
        content_type="application/json",
        freshness_policy_seconds=300,
        is_official=True,
    )


def test_registry_deduplicates_sources_and_lists_families_deterministically():
    registry = SourceRegistry()
    registry.register(source())
    assert registry.source_ids == ("gamma",)
    assert registry.list_current_families() == ("polymarket_gamma",)
    assert registry.has_family("polymarket_gamma")
    with pytest.raises(ValueError):
        registry.register(source())
    with pytest.raises(ValueError):
        registry.get("missing")


def test_registry_rejects_unregistered_team_sources_and_accepts_known_team():
    registry = SourceRegistry(minimum_current_source_families=1)
    registry.register(source())
    requirement = TeamSourceRequirement(
        team_id="crypto_btc",
        source_ids=("gamma",),
    )
    registry.register_requirement(requirement)
    assert registry.requirements == (requirement,)
    with pytest.raises(ValueError):
        registry.register_requirement(
            TeamSourceRequirement(team_id="crypto_btc", source_ids=("gamma",)),
        )
    with pytest.raises(ValueError):
        registry.register_requirement(
            TeamSourceRequirement(team_id="politics", source_ids=("missing",)),
        )


def test_registry_requires_positive_family_threshold_and_unique_source_ids():
    with pytest.raises(ValueError):
        SourceRegistry(minimum_current_source_families=0)
    with pytest.raises(ValueError):
        TeamSourceRequirement(team_id="crypto_btc", source_ids=("gamma", "gamma"))
    with pytest.raises(ValueError):
        TeamSourceRequirement(team_id="crypto_btc", source_ids=(" gamma",))


def test_registry_enforces_family_threshold_and_default_team_requirements():
    registry = SourceRegistry(minimum_current_source_families=2)
    registry.register(source())
    with pytest.raises(ValueError, match="family threshold"):
        registry.register_requirement(
            TeamSourceRequirement(team_id="crypto_btc", source_ids=("gamma",), minimum_current_source_families=1),
        )
    with pytest.raises(ValueError, match="source families"):
        registry.register_requirement(
            TeamSourceRequirement(team_id="crypto_btc", source_ids=("gamma",), minimum_current_source_families=2),
        )

    registry = build_default_source_registry()
    assert registry.requirements == tuple(sorted(DEFAULT_TEAM_SOURCE_REQUIREMENTS, key=lambda item: item.team_id))
    assert len(registry.requirements) == 10
    assert all(item.minimum_current_source_families == 1 for item in registry.requirements)


def test_default_registry_contains_only_official_polymarket_sources():
    registry = build_default_source_registry()
    assert registry.source_ids == tuple(sorted(item.source_id for item in DEFAULT_SOURCE_DEFINITIONS))
    assert all(item.is_official for item in DEFAULT_SOURCE_DEFINITIONS)
