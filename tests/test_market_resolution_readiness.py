from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def module():
    return importlib.import_module("polymarket_alpha_lab.market_resolution_readiness")


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    condition_id: str,
    *,
    closed: bool,
    active: bool,
    pending: bool,
    outcome_observed: bool,
    outcome_value: Decimal | None = None,
):
    readiness_module = module()
    return readiness_module.MarketResolutionObservation(
        condition_id=condition_id,
        closed=closed,
        active=active,
        pending=pending,
        outcome_observed=outcome_observed,
        outcome_value=outcome_value,
    )


def build_report(*observations):
    readiness_module = module()
    return readiness_module.build_market_resolution_readiness_report(
        observations,
        config=readiness_module.MarketResolutionReadinessConfig(
            config_version="market-resolution-readiness-test-v0",
            min_ready_resolution_share=d("0.750000"),
        ),
        generated_at=GENERATED_AT,
    )


def test_builds_readonly_resolution_readiness_summary_without_market_identity() -> None:
    report = build_report(
        observation(
            "condition-c",
            closed=True,
            active=False,
            pending=False,
            outcome_observed=True,
            outcome_value=d("1.000000"),
        ),
        observation(
            "condition-a",
            closed=True,
            active=False,
            pending=False,
            outcome_observed=True,
            outcome_value=d("0.000000"),
        ),
        observation(
            "condition-b",
            closed=True,
            active=False,
            pending=False,
            outcome_observed=False,
        ),
        observation(
            "condition-d",
            closed=False,
            active=True,
            pending=True,
            outcome_observed=False,
        ),
    )

    assert report.resolution_status == "watch"
    assert report.total_market_count == 4
    assert report.closed_market_count == 3
    assert report.active_market_count == 1
    assert report.pending_market_count == 1
    assert report.outcome_observed_count == 2
    assert report.ready_resolution_count == 2
    assert report.ready_resolution_share == d("0.500000")
    assert report.reason_codes == ("resolution_observation_below_ready_threshold",)
    assert tuple(row.condition_id for row in report.rows) == (
        "condition-d",
        "condition-b",
        "condition-a",
        "condition-c",
    )
    assert report.rows[0].resolution_status == "blocked"
    assert report.rows[0].reason_codes == ("market_resolution_still_pending",)
    assert report.rows[1].resolution_status == "watch"
    assert report.rows[1].reason_codes == ("closed_market_missing_outcome_observation",)
    assert report.rows[2].outcome_value == d("0.000000")
    assert report.rows[3].outcome_value == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert "slug" not in repr(report).lower()
    assert "question" not in repr(report).lower()


def test_all_closed_observed_markets_pass_readiness() -> None:
    report = build_report(
        observation(
            "condition-a",
            closed=True,
            active=False,
            pending=False,
            outcome_observed=True,
            outcome_value=d("1.000000"),
        ),
        observation(
            "condition-b",
            closed=True,
            active=False,
            pending=False,
            outcome_observed=True,
            outcome_value=d("0.000000"),
        ),
    )

    assert report.resolution_status == "pass"
    assert report.ready_resolution_share == d("1.000000")
    assert report.reason_codes == ("market_resolution_ready",)
    assert tuple(row.resolution_status for row in report.rows) == ("pass", "pass")


def test_no_observations_blocks_without_dividing_by_zero() -> None:
    report = build_report()

    assert report.resolution_status == "blocked"
    assert report.total_market_count == 0
    assert report.ready_resolution_share == d("0.000000")
    assert report.reason_codes == ("no_markets_to_assess",)
    assert report.rows == ()


def test_dataclasses_are_frozen_decimal_only_and_public_api_is_local() -> None:
    readiness_module = module()

    assert readiness_module.__all__ == (
        "DEFAULT_MARKET_RESOLUTION_READINESS_CONFIG_VERSION",
        "MarketResolutionObservation",
        "MarketResolutionReadinessConfig",
        "MarketResolutionReadinessReport",
        "MarketResolutionReadinessRow",
        "build_market_resolution_readiness_report",
    )
    for exported_name in readiness_module.__all__:
        value = getattr(readiness_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    cfg = readiness_module.MarketResolutionReadinessConfig()
    obs = observation(
        "condition-b",
        closed=True,
        active=False,
        pending=False,
        outcome_observed=True,
        outcome_value=d("0.000000"),
    )
    report = build_report(
        observation(
            "condition-a",
            closed=True,
            active=False,
            pending=False,
            outcome_observed=True,
            outcome_value=d("1.000000"),
        ),
    )
    for value in (cfg, obs, report.rows[0], report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    with pytest.raises(FrozenInstanceError):
        report.rows[0].resolution_status = "blocked"  # type: ignore[misc]
    for value in (cfg, obs, report.rows[0], report):
        with pytest.raises(ValueError, match="paper_only"):
            replace(value, paper_only=False)
        with pytest.raises(ValueError, match="report_only"):
            replace(value, report_only=False)
        with pytest.raises(ValueError, match="readonly"):
            replace(value, readonly=False)


def test_generated_at_is_normalized_to_utc() -> None:
    readiness_module = module()

    report = readiness_module.build_market_resolution_readiness_report(
        (
            observation(
                "condition-a",
                closed=True,
                active=False,
                pending=False,
                outcome_observed=True,
                outcome_value=d("1.000000"),
            ),
        ),
        config=readiness_module.MarketResolutionReadinessConfig(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone.utc),
    )

    assert report.generated_at == datetime(2026, 7, 2, 8, 0, tzinfo=UTC)


@pytest.mark.parametrize("bad_value", [Decimal("NaN"), Decimal("Infinity")])
def test_rejects_non_finite_decimal_outcome_values(bad_value: Decimal) -> None:
    readiness_module = module()

    with pytest.raises(ValueError, match="outcome_value must be finite"):
        readiness_module.MarketResolutionObservation(
            condition_id="condition-a",
            closed=True,
            active=False,
            pending=False,
            outcome_observed=True,
            outcome_value=bad_value,
        )


def test_rejects_float_outcome_values_to_keep_decimal_only() -> None:
    readiness_module = module()

    with pytest.raises(ValueError, match="outcome_value must be a Decimal or None"):
        readiness_module.MarketResolutionObservation(
            condition_id="condition-a",
            closed=True,
            active=False,
            pending=False,
            outcome_observed=True,
            outcome_value=1.0,
        )


def test_rejects_market_identity_fields_and_inconsistent_states() -> None:
    readiness_module = module()

    with pytest.raises(TypeError):
        readiness_module.MarketResolutionObservation(
            condition_id="condition-a",
            market_slug="secret-market-slug",
            closed=True,
            active=False,
            pending=False,
            outcome_observed=True,
            outcome_value=d("1.000000"),
        )
    with pytest.raises(TypeError):
        readiness_module.MarketResolutionObservation(
            condition_id="condition-a",
            question="Will this leak?",
            closed=True,
            active=False,
            pending=False,
            outcome_observed=True,
            outcome_value=d("1.000000"),
        )
    with pytest.raises(ValueError, match="pending markets must not have outcome observations"):
        readiness_module.MarketResolutionObservation(
            condition_id="condition-a",
            closed=False,
            active=True,
            pending=True,
            outcome_observed=True,
            outcome_value=d("1.000000"),
        )
    with pytest.raises(ValueError, match="closed markets must not be active"):
        readiness_module.MarketResolutionObservation(
            condition_id="condition-a",
            closed=True,
            active=True,
            pending=False,
            outcome_observed=False,
        )


def test_module_omits_live_auth_wallet_order_account_and_advice_language() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in ("live", "auth", "wallet", "order", "account", "advice"):
        assert forbidden not in lowered
