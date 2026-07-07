from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
CLOSED_AT = datetime(2026, 7, 2, 10, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_close_outcome_acknowledgement_lag_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observed(
    condition_id: str,
    *,
    closed_at: datetime = CLOSED_AT,
    outcome_confirmed_at: datetime | None = None,
    source_confirmed_at: datetime | None = None,
    team_acknowledged_at: datetime | None = None,
    outcome_value: Decimal | None = None,
    source_outcome_value: Decimal | None = None,
):
    lag_module = module()
    return lag_module.MarketCloseOutcomeAcknowledgementLagInput(
        condition_id=condition_id,
        closed_at=closed_at,
        outcome_confirmed_at=outcome_confirmed_at,
        source_confirmed_at=source_confirmed_at,
        team_acknowledged_at=team_acknowledged_at,
        outcome_value=outcome_value,
        source_outcome_value=source_outcome_value,
        source_reference="redacted-source-confirmation",
    )


def build_report(*items):
    lag_module = module()
    return lag_module.build_market_close_outcome_acknowledgement_lag_report(
        items,
        config=lag_module.MarketCloseOutcomeAcknowledgementLagConfig(
            config_version="market-close-outcome-acknowledgement-lag-test-v0",
            stale_source_after_seconds=d("600.000000"),
            late_acknowledgement_after_seconds=d("900.000000"),
            unresolved_close_after_seconds=d("1800.000000"),
        ),
        generated_at=GENERATED_AT,
    )


def test_flags_domain_lag_states_with_deterministic_sort_and_decimal_metrics() -> None:
    report = build_report(
        observed(
            "condition-pass",
            outcome_confirmed_at=datetime(2026, 7, 2, 10, 2, tzinfo=UTC),
            source_confirmed_at=datetime(2026, 7, 2, 10, 3, tzinfo=UTC),
            team_acknowledged_at=datetime(2026, 7, 2, 10, 10, tzinfo=UTC),
            outcome_value=d("1.000000"),
            source_outcome_value=d("1.000000"),
        ),
        observed(
            "condition-late-ack",
            outcome_confirmed_at=datetime(2026, 7, 2, 10, 2, tzinfo=UTC),
            source_confirmed_at=datetime(2026, 7, 2, 10, 3, tzinfo=UTC),
            team_acknowledged_at=datetime(2026, 7, 2, 10, 25, tzinfo=UTC),
            outcome_value=d("1.000000"),
            source_outcome_value=d("1.000000"),
        ),
        observed(
            "condition-stale-source",
            outcome_confirmed_at=datetime(2026, 7, 2, 10, 1, tzinfo=UTC),
            source_confirmed_at=datetime(2026, 7, 2, 10, 20, tzinfo=UTC),
            team_acknowledged_at=datetime(2026, 7, 2, 10, 25, tzinfo=UTC),
            outcome_value=d("0.000000"),
            source_outcome_value=d("0.000000"),
        ),
        observed(
            "condition-missing-outcome",
            source_confirmed_at=datetime(2026, 7, 2, 10, 20, tzinfo=UTC),
            source_outcome_value=d("1.000000"),
        ),
        observed(
            "condition-contradiction",
            outcome_confirmed_at=datetime(2026, 7, 2, 10, 4, tzinfo=UTC),
            source_confirmed_at=datetime(2026, 7, 2, 10, 5, tzinfo=UTC),
            team_acknowledged_at=datetime(2026, 7, 2, 10, 8, tzinfo=UTC),
            outcome_value=d("1.000000"),
            source_outcome_value=d("0.000000"),
        ),
    )

    assert report.lag_status == "blocked"
    assert report.total_market_count == d("5")
    assert report.blocked_market_count == d("2")
    assert report.watch_market_count == d("2")
    assert report.pass_market_count == d("1")
    assert report.acknowledged_market_count == d("4")
    assert report.acknowledgement_completion_ratio == d("0.800000")
    assert len(report.derived_validation_digest) == 64
    assert report.missing_outcome_count == d("1")
    assert report.stale_source_count == d("2")
    assert report.late_acknowledgement_count == d("2")
    assert report.contradiction_count == d("1")
    assert report.unresolved_close_age_count == d("1")
    assert report.reason_codes == (
        "market_close_outcome_acknowledgement_lag_blocked",
        "outcome_source_contradiction_present",
        "missing_outcome_confirmation_present",
        "stale_source_confirmation_present",
        "late_team_acknowledgement_present",
        "unresolved_close_age_present",
    )
    assert tuple(row.condition_id for row in report.rows) == (
        "condition-contradiction",
        "condition-missing-outcome",
        "condition-late-ack",
        "condition-stale-source",
        "condition-pass",
    )

    contradiction = report.rows[0]
    missing = report.rows[1]
    late = report.rows[2]
    stale = report.rows[3]
    passing = report.rows[4]

    assert contradiction.lag_status == "blocked"
    assert contradiction.reason_codes == ("outcome_source_contradiction",)
    assert missing.reason_codes == (
        "missing_outcome_confirmation",
        "stale_source_confirmation",
        "late_team_acknowledgement",
        "unresolved_close_age_exceeds_threshold",
    )
    assert missing.close_age_seconds == d("7200.000000")
    assert missing.close_to_outcome_seconds is None
    assert missing.close_to_source_seconds == d("1200.000000")
    assert missing.acknowledgement_lag_seconds is None
    assert missing.unresolved_close_age_seconds == d("7200.000000")
    assert late.reason_codes == ("late_team_acknowledgement",)
    assert late.acknowledgement_lag_seconds == d("1320.000000")
    assert stale.reason_codes == ("stale_source_confirmation",)
    assert stale.close_to_source_seconds == d("1200.000000")
    assert passing.lag_status == "pass"
    assert passing.reason_codes == ("market_close_outcome_acknowledgement_lag_clear",)
    assert passing.paper_only is True
    assert passing.report_only is True
    assert passing.readonly is True
    assert "secret-token" not in repr(report)


def test_no_inputs_blocks_without_float_or_division_leakage() -> None:
    report = build_report()

    assert report.lag_status == "blocked"
    assert report.total_market_count == d("0")
    assert report.acknowledgement_completion_ratio == d("0.000000")
    assert report.reason_codes == ("no_closed_markets_to_assess",)
    assert report.rows == ()


def test_dataclasses_are_frozen_and_expose_decimal_public_metrics() -> None:
    lag_module = module()

    assert lag_module.__all__ == (
        "DEFAULT_MARKET_CLOSE_OUTCOME_ACKNOWLEDGEMENT_LAG_CONFIG_VERSION",
        "MarketCloseOutcomeAcknowledgementLagConfig",
        "MarketCloseOutcomeAcknowledgementLagInput",
        "MarketCloseOutcomeAcknowledgementLagReport",
        "MarketCloseOutcomeAcknowledgementLagRow",
        "build_market_close_outcome_acknowledgement_lag_report",
        "market_close_outcome_acknowledgement_lag_report_payload",
    )
    for exported_name in lag_module.__all__:
        value = getattr(lag_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(
        observed(
            "condition-pass",
            outcome_confirmed_at=datetime(2026, 7, 2, 10, 2, tzinfo=UTC),
            source_confirmed_at=datetime(2026, 7, 2, 10, 3, tzinfo=UTC),
            team_acknowledged_at=datetime(2026, 7, 2, 10, 10, tzinfo=UTC),
            outcome_value=d("1.000000"),
            source_outcome_value=d("1.000000"),
        ),
    )

    for field in fields(report):
        if field.name.endswith("_count") or field.name.endswith("_ratio"):
            assert type(getattr(report, field.name)) is Decimal
    for row in report.rows:
        for field in fields(row):
            if field.name.endswith("_seconds"):
                value = getattr(row, field.name)
                assert value is None or type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].lag_status = "blocked"  # type: ignore[misc]


def test_report_exposes_stable_derived_validation_digest() -> None:
    lag_module = module()
    report = build_report(
        observed(
            "condition-pass",
            outcome_confirmed_at=datetime(2026, 7, 2, 10, 2, tzinfo=UTC),
            source_confirmed_at=datetime(2026, 7, 2, 10, 3, tzinfo=UTC),
            team_acknowledged_at=datetime(2026, 7, 2, 10, 10, tzinfo=UTC),
            outcome_value=d("1.000000"),
            source_outcome_value=d("1.000000"),
        ),
    )
    rebuilt = build_report(
        observed(
            "condition-pass",
            outcome_confirmed_at=datetime(2026, 7, 2, 10, 2, tzinfo=UTC),
            source_confirmed_at=datetime(2026, 7, 2, 10, 3, tzinfo=UTC),
            team_acknowledged_at=datetime(2026, 7, 2, 10, 10, tzinfo=UTC),
            outcome_value=d("1.000000"),
            source_outcome_value=d("1.000000"),
        ),
    )

    assert report.derived_validation_digest == rebuilt.derived_validation_digest
    assert report.derived_validation_digest != "0" * 64

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        lag_module.MarketCloseOutcomeAcknowledgementLagReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            total_market_count=report.total_market_count,
            blocked_market_count=report.blocked_market_count,
            watch_market_count=report.watch_market_count,
            pass_market_count=report.pass_market_count,
            acknowledged_market_count=report.acknowledged_market_count,
            missing_outcome_count=report.missing_outcome_count,
            stale_source_count=report.stale_source_count,
            late_acknowledgement_count=report.late_acknowledgement_count,
            contradiction_count=report.contradiction_count,
            unresolved_close_age_count=report.unresolved_close_age_count,
            acknowledgement_completion_ratio=report.acknowledgement_completion_ratio,
            lag_status=report.lag_status,
            reason_codes=report.reason_codes,
            rows=report.rows,
            derived_validation_digest="0" * 64,
        )


def test_utc_aware_datetimes_are_required_and_normalized() -> None:
    lag_module = module()

    report = lag_module.build_market_close_outcome_acknowledgement_lag_report(
        (
            observed(
                "condition-pass",
                closed_at=datetime(2026, 7, 2, 6, 0, tzinfo=timezone.utc),
                outcome_confirmed_at=datetime(2026, 7, 2, 6, 2, tzinfo=timezone.utc),
                source_confirmed_at=datetime(2026, 7, 2, 6, 3, tzinfo=timezone.utc),
                team_acknowledged_at=datetime(2026, 7, 2, 6, 10, tzinfo=timezone.utc),
                outcome_value=d("1.000000"),
                source_outcome_value=d("1.000000"),
            ),
        ),
        config=lag_module.MarketCloseOutcomeAcknowledgementLagConfig(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone.utc),
    )

    assert report.generated_at == datetime(2026, 7, 2, 8, 0, tzinfo=UTC)
    assert report.rows[0].closed_at == datetime(2026, 7, 2, 6, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        lag_module.build_market_close_outcome_acknowledgement_lag_report(
            (),
            config=lag_module.MarketCloseOutcomeAcknowledgementLagConfig(),
            generated_at=datetime(2026, 7, 2, 8, 0),
        )
    with pytest.raises(ValueError, match="closed_at must be timezone-aware"):
        observed("condition-naive", closed_at=datetime(2026, 7, 2, 6, 0))


def test_rejects_event_timestamps_after_report_generation() -> None:
    lag_module = module()

    with pytest.raises(ValueError, match="source_confirmed_at must not be after generated_at"):
        lag_module.build_market_close_outcome_acknowledgement_lag_report(
            (
                observed(
                    "condition-future-source",
                    outcome_confirmed_at=datetime(2026, 7, 2, 10, 2, tzinfo=UTC),
                    source_confirmed_at=datetime(2026, 7, 2, 12, 1, tzinfo=UTC),
                    outcome_value=d("1.000000"),
                    source_outcome_value=d("1.000000"),
                ),
            ),
            config=lag_module.MarketCloseOutcomeAcknowledgementLagConfig(),
            generated_at=GENERATED_AT,
        )


def test_rejects_non_decimal_values_and_false_hard_flags() -> None:
    lag_module = module()

    with pytest.raises(ValueError, match="outcome_value must be a Decimal or None"):
        observed(
            "condition-float",
            outcome_confirmed_at=datetime(2026, 7, 2, 10, 2, tzinfo=UTC),
            source_confirmed_at=datetime(2026, 7, 2, 10, 3, tzinfo=UTC),
            team_acknowledged_at=datetime(2026, 7, 2, 10, 10, tzinfo=UTC),
            outcome_value=1.0,  # type: ignore[arg-type]
            source_outcome_value=d("1.000000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        lag_module.MarketCloseOutcomeAcknowledgementLagConfig(paper_only=False)


@pytest.mark.parametrize(
    "unsafe_fragment",
    ("live", "auth", "wallet", "order", "network", "database", "persist"),
)
def test_rejects_unsafe_public_text_surfaces(unsafe_fragment: str) -> None:
    lag_module = module()

    with pytest.raises(ValueError, match="unsafe public surface"):
        lag_module.MarketCloseOutcomeAcknowledgementLagInput(
            condition_id=f"condition-{unsafe_fragment}",
            closed_at=CLOSED_AT,
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        lag_module.MarketCloseOutcomeAcknowledgementLagInput(
            condition_id="condition-safe",
            closed_at=CLOSED_AT,
            source_reference=f"redacted-{unsafe_fragment}-source",
        )


def test_rejects_uri_like_public_source_reference() -> None:
    lag_module = module()

    with pytest.raises(ValueError, match="unsafe public surface"):
        lag_module.MarketCloseOutcomeAcknowledgementLagInput(
            condition_id="condition-safe",
            closed_at=CLOSED_AT,
            source_reference="postgres://secret-token@example.invalid/source",
        )


def test_manual_rows_validate_elapsed_metrics_and_reason_code_order() -> None:
    lag_module = module()

    row_kwargs = {
        "condition_id": "condition-manual",
        "closed_at": CLOSED_AT,
        "outcome_confirmed_at": datetime(2026, 7, 2, 10, 1, tzinfo=UTC),
        "source_confirmed_at": datetime(2026, 7, 2, 10, 20, tzinfo=UTC),
        "team_acknowledged_at": datetime(2026, 7, 2, 10, 25, tzinfo=UTC),
        "outcome_value": d("1.000000"),
        "source_outcome_value": d("1.000000"),
        "source_reference": "redacted-source-confirmation",
        "close_age_seconds": d("7200.000000"),
        "close_to_outcome_seconds": d("60.000000"),
        "close_to_source_seconds": d("1200.000000"),
        "acknowledgement_lag_seconds": d("300.000000"),
        "unresolved_close_age_seconds": d("0.000000"),
        "lag_status": "watch",
        "reason_codes": (
            "late_team_acknowledgement",
            "stale_source_confirmation",
        ),
    }

    row = lag_module.MarketCloseOutcomeAcknowledgementLagRow(**row_kwargs)

    assert row.reason_codes == (
        "stale_source_confirmation",
        "late_team_acknowledgement",
    )
    assert row.source_reference == "<redacted-source-reference>"

    with pytest.raises(ValueError, match="close_to_source_seconds must match"):
        lag_module.MarketCloseOutcomeAcknowledgementLagRow(
            **(row_kwargs | {"close_to_source_seconds": d("1.000000")}),
        )

    with pytest.raises(ValueError, match="unresolved_close_age_seconds must match"):
        lag_module.MarketCloseOutcomeAcknowledgementLagRow(
            **(
                row_kwargs
                | {
                    "team_acknowledged_at": None,
                    "acknowledgement_lag_seconds": None,
                    "unresolved_close_age_seconds": d("1.000000"),
                    "lag_status": "blocked",
                    "reason_codes": ("missing_outcome_confirmation",),
                }
            ),
        )


def test_json_ready_payload_has_no_floats_and_uses_strings_for_decimals() -> None:
    lag_module = module()
    report = build_report(
        observed(
            "condition-pass",
            outcome_confirmed_at=datetime(2026, 7, 2, 10, 2, tzinfo=UTC),
            source_confirmed_at=datetime(2026, 7, 2, 10, 3, tzinfo=UTC),
            team_acknowledged_at=datetime(2026, 7, 2, 10, 10, tzinfo=UTC),
            outcome_value=d("1.000000"),
            source_outcome_value=d("1.000000"),
        ),
    )

    payload = lag_module.market_close_outcome_acknowledgement_lag_report_payload(report)

    json.dumps(payload, sort_keys=True)
    assert payload["total_market_count"] == "1.000000"
    assert payload["acknowledgement_completion_ratio"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["close_age_seconds"] == "7200.000000"
    assert_no_float(payload)


def test_public_payload_rejects_tampered_unsafe_surface_values() -> None:
    lag_module = module()
    report = build_report(
        observed(
            "condition-pass",
            outcome_confirmed_at=datetime(2026, 7, 2, 10, 2, tzinfo=UTC),
            source_confirmed_at=datetime(2026, 7, 2, 10, 3, tzinfo=UTC),
            team_acknowledged_at=datetime(2026, 7, 2, 10, 10, tzinfo=UTC),
            outcome_value=d("1.000000"),
            source_outcome_value=d("1.000000"),
        ),
    )

    object.__setattr__(report.rows[0], "condition_id", "condition-live")

    with pytest.raises(ValueError, match="unsafe public surface"):
        lag_module.market_close_outcome_acknowledgement_lag_report_payload(report)


def test_module_omits_runtime_and_financial_action_surfaces() -> None:
    source = module().__loader__.get_source(module().__name__)
    assert source is not None
    lowered = source.lower()

    for forbidden in (
        "persistence",
        "network",
        "live",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
        "database",
        "persist",
    ):
        assert forbidden not in lowered


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)
