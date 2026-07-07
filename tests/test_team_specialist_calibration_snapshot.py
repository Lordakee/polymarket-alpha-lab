from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_calibration_snapshot.py"
)
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_calibration_snapshot",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def snapshot(**overrides: object) -> Any:
    module = api()
    values = {
        "team_id": "alpha_team",
        "specialist_id": "rates_specialist",
        "resolved_prediction_count": d("120"),
        "brier_score": d("0.120000"),
        "calibration_error_score": d("0.050000"),
        "recent_hit_rate": d("0.680000"),
        "confidence_bias_score": d("0.040000"),
        "stale_sample_days": d("5"),
    }
    values.update(overrides)
    return module.TeamSpecialistCalibrationSnapshotInput(**values)


def build_report(*items: object, **overrides: object) -> Any:
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (snapshot(),)
    return module.build_team_specialist_calibration_snapshot_report(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def payload_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def test_calibrated_snapshot_passes_with_safe_public_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.report_status == "pass"
    assert report.snapshot_count == d("1")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.average_calibration_snapshot_score == d("0.881944")
    assert report.top_calibration_snapshot_score == d("0.881944")
    assert report.bottom_calibration_snapshot_score == d("0.881944")
    assert report.max_routing_priority_score == d("0.118056")
    assert report.reason_codes == ("calibration_snapshot_report_pass",)

    row = report.rows[0]
    assert row.rank == d("1")
    assert row.team_id == "alpha_team"
    assert row.specialist_id == "rates_specialist"
    assert row.status == "pass"
    assert row.routing_priority_score == d("0.118056")
    assert row.reason_codes == (
        "snapshot_pass",
        "sample_size_strong",
        "sample_fresh",
        "brier_score_strong",
        "calibration_error_low",
        "hit_rate_strong",
        "confidence_bias_low",
    )

    payload = report.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["snapshot_count"] == "1"
    assert payload["rows"][0]["calibration_snapshot_score"] == "0.881944"
    assert payload["rows"][0]["status"] == "pass"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)

    forbidden_statuses = ("ready", "blocked", "matched", "supported")
    rendered = payload_text(payload).lower()
    assert not any(status in rendered for status in forbidden_statuses)


def test_stale_low_sample_snapshot_blocks_routing() -> None:
    report = build_report(
        snapshot(
            resolved_prediction_count=d("8"),
            stale_sample_days=d("60"),
        ),
    )

    row = report.rows[0]
    assert report.report_status == "block"
    assert report.block_count == d("1")
    assert row.status == "block"
    assert row.routing_priority_score == d("0.900000")
    assert "sample_size_low" in row.reason_codes
    assert "sample_stale_block" in row.reason_codes
    assert report.reason_codes == ("calibration_snapshot_report_block_rows",)


def test_biased_snapshot_watches_without_blocking() -> None:
    report = build_report(
        snapshot(confidence_bias_score=d("0.150000")),
    )

    row = report.rows[0]
    assert report.report_status == "watch"
    assert report.watch_count == d("1")
    assert report.block_count == d("0")
    assert row.status == "watch"
    assert row.routing_priority_score == d("0.500000")
    assert "confidence_bias_watch" in row.reason_codes


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "brier_score",
            _DecimalSubclass("0.120000"),
            "brier_score must be exactly Decimal",
        ),
        (
            "calibration_error_score",
            d("0.0500001"),
            "calibration_error_score must use six decimal places or fewer",
        ),
        (
            "recent_hit_rate",
            d("1.000001"),
            "recent_hit_rate must be <= 1.000000",
        ),
        (
            "confidence_bias_score",
            Decimal("NaN"),
            "confidence_bias_score must be finite",
        ),
        (
            "resolved_prediction_count",
            d("12.5"),
            "resolved_prediction_count must be an integral Decimal",
        ),
        (
            "stale_sample_days",
            5,
            "stale_sample_days must be exactly Decimal",
        ),
    ),
)
def test_decimal_fields_reject_non_exact_or_invalid_decimal_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        snapshot(**{field_name: bad_value})


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("team_id", "market_123"),
        ("specialist_id", "candidate_42"),
        ("team_id", "https://example.invalid/path"),
        ("specialist_id", "wallet_check"),
    ),
)
def test_public_payload_rejects_leaky_identifiers(
    field_name: str,
    bad_value: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe public payload"):
        snapshot(**{field_name: bad_value})


def test_hard_flags_are_required_and_dataclasses_are_frozen() -> None:
    module = api()
    config = module.TeamSpecialistCalibrationSnapshotConfig()
    item = snapshot()
    report = build_report(item)
    row = report.rows[0]

    for value in (config, item, row, report):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name.endswith("_score") or field.name in {
                "resolved_prediction_count",
                "stale_sample_days",
                "min_resolved_prediction_count",
                "watch_resolved_prediction_count",
                "watch_stale_sample_days",
                "max_stale_sample_days",
                "rank",
                "snapshot_count",
                "pass_count",
                "watch_count",
                "block_count",
            }:
                assert type(field_value) is Decimal

    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistCalibrationSnapshotConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        module.TeamSpecialistCalibrationSnapshotInput(
            team_id="alpha_team",
            specialist_id="rates_specialist",
            resolved_prediction_count=d("120"),
            brier_score=d("0.120000"),
            calibration_error_score=d("0.050000"),
            recent_hit_rate=d("0.680000"),
            confidence_bias_score=d("0.040000"),
            stale_sample_days=d("5"),
            report_only=False,
        )


def test_deterministic_ordering_uses_priority_then_team_and_specialist() -> None:
    first = snapshot(team_id="beta_team", specialist_id="zeta_specialist")
    second = snapshot(team_id="alpha_team", specialist_id="alpha_specialist")
    urgent = snapshot(
        team_id="gamma_team",
        specialist_id="gamma_specialist",
        resolved_prediction_count=d("5"),
    )

    report_a = build_report(first, second, urgent)
    report_b = build_report(urgent, second, first)

    expected = (
        ("gamma_team", "gamma_specialist", "block", d("1")),
        ("alpha_team", "alpha_specialist", "pass", d("2")),
        ("beta_team", "zeta_specialist", "pass", d("3")),
    )
    assert tuple(
        (row.team_id, row.specialist_id, row.status, row.rank) for row in report_a.rows
    ) == expected
    assert tuple(
        (row.team_id, row.specialist_id, row.status, row.rank) for row in report_b.rows
    ) == expected


def test_payload_and_report_consistency_are_enforced() -> None:
    report = build_report(
        snapshot(team_id="beta_team", specialist_id="beta_specialist"),
        snapshot(
            team_id="alpha_team",
            specialist_id="alpha_specialist",
            confidence_bias_score=d("0.150000"),
        ),
    )

    payload = report.payload
    assert payload["report_status"] == report.report_status
    assert payload["snapshot_count"] == str(report.snapshot_count)
    assert payload["watch_count"] == str(report.watch_count)
    assert payload["max_routing_priority_score"] == str(report.max_routing_priority_score)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["team_id"] == report.rows[0].team_id
    assert payload["rows"][0]["routing_priority_score"] == str(
        report.rows[0].routing_priority_score,
    )

    with pytest.raises(ValueError, match="snapshot_count must match rows"):
        replace(report, snapshot_count=d("99"))
    with pytest.raises(ValueError, match="rows must be sorted by routing priority"):
        replace(report, rows=tuple(reversed(report.rows)))


def test_empty_report_is_readonly_and_uses_public_block_status() -> None:
    report = build_report(use_default_items=False)

    assert report.report_status == "block"
    assert report.snapshot_count == d("0")
    assert report.rows == ()
    assert report.average_calibration_snapshot_score == d("0.000000")
    assert report.max_routing_priority_score == d("0.000000")
    assert report.reason_codes == ("calibration_snapshot_report_empty",)
    assert report.payload["report_status"] == "block"
