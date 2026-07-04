from __future__ import annotations

import ast
import importlib
from hashlib import sha256
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 12, 30, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_probability_edge_calibration_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted_condition_id(value: str) -> str:
    return f"condition_ref_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def config(**overrides: object):
    digest = api()
    values = {
        "config_version": "strategy-probability-edge-calibration-digest-v0",
        "material_edge_threshold": d("0.050000"),
        "calibration_error_threshold": d("0.100000"),
        "stale_edge_hours": d("24.000000"),
    }
    values.update(overrides)
    return digest.StrategyProbabilityEdgeCalibrationDigestConfig(**values)


def input_row(**overrides: object):
    digest = api()
    values = {
        "strategy_id": "edge-model-v1",
        "market_slug": "politics-market",
        "condition_id": "0xabcdef1234567890secret",
        "forecast_probability": d("0.640000"),
        "market_probability": d("0.520000"),
        "realized_probability": d("1.000000"),
        "edge_probability": d("0.120000"),
        "edge_age_hours": d("6.000000"),
        "reason_codes": (
            "positive_edge_detected",
            "resolved_calibration_available",
            "calibration_error_detected",
            "edge_fresh",
        ),
    }
    values.update(overrides)
    return digest.StrategyProbabilityEdgeCalibrationInput(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    digest = api()
    return digest.build_strategy_probability_edge_calibration_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_digest_summarizes_probability_edge_calibration_and_reason_codes() -> None:
    digest_report = report(
        input_row(
            strategy_id="zeta-edge",
            market_slug="politics-market",
            condition_id="0xabcdef1234567890secret",
            forecast_probability=d("0.640000"),
            market_probability=d("0.520000"),
            realized_probability=d("1.000000"),
            edge_probability=d("0.120000"),
            edge_age_hours=d("4.000000"),
            reason_codes=(
                "positive_edge_detected",
                "resolved_calibration_available",
                "calibration_error_detected",
                "edge_fresh",
            ),
        ),
        input_row(
            strategy_id="alpha-edge",
            market_slug="crypto-market",
            condition_id="0x9999999999999999private",
            forecast_probability=d("0.430000"),
            market_probability=d("0.560000"),
            realized_probability=d("1.000000"),
            edge_probability=d("-0.130000"),
            edge_age_hours=d("30.000000"),
            reason_codes=(
                "negative_edge_detected",
                "resolved_calibration_available",
                "calibration_error_detected",
                "stale_edge",
            ),
        ),
        input_row(
            strategy_id="beta-edge",
            market_slug="macro-market",
            condition_id="0x2222222222222222hidden",
            forecast_probability=d("0.510000"),
            market_probability=d("0.500000"),
            realized_probability=None,
            edge_probability=d("0.010000"),
            edge_age_hours=d("2.000000"),
            reason_codes=("edge_within_threshold", "edge_fresh"),
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "strategy-probability-edge-calibration-digest-v0"
    )
    assert digest_report.source_row_count == d("3")
    assert digest_report.strategy_count == d("3")
    assert digest_report.market_count == d("3")
    assert digest_report.material_edge_count == d("2")
    assert digest_report.resolved_calibration_count == d("2")
    assert digest_report.calibration_error_count == d("2")
    assert digest_report.stale_edge_count == d("1")
    assert digest_report.mean_absolute_edge == d("0.086667")
    assert digest_report.mean_signed_edge == d("0.000000")
    assert digest_report.mean_calibration_error == d("0.465000")
    assert digest_report.status == "watch"
    assert digest_report.reason_codes == (
        "material_probability_edge_detected",
        "resolved_calibration_available",
        "calibration_error_detected",
        "stale_probability_edge_detected",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    first, second, third = digest_report.rows
    assert first.strategy_id == "alpha-edge"
    assert first.market_slug == "crypto-market"
    assert first.redacted_condition_id == redacted_condition_id(
        "0x9999999999999999private",
    )
    assert first.edge_probability == d("-0.130000")
    assert first.calibration_error == d("0.570000")
    assert first.status == "watch"
    assert first.reason_codes == (
        "negative_edge_detected",
        "resolved_calibration_available",
        "calibration_error_detected",
        "stale_edge",
    )

    assert second.strategy_id == "zeta-edge"
    assert second.redacted_condition_id == redacted_condition_id(
        "0xabcdef1234567890secret",
    )
    assert second.calibration_error == d("0.360000")
    assert third.strategy_id == "beta-edge"
    assert third.status == "pass"


def test_digest_normalizes_utc_and_serializes_json_without_floats_or_secrets() -> None:
    digest = api()
    digest_report = report(
        input_row(),
        generated_at=datetime(2026, 7, 3, 5, 30, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = digest.strategy_probability_edge_calibration_digest_payload(digest_report)
    payload_text = repr(payload).lower()

    assert digest_report.generated_at == GENERATED_AT
    assert payload["generated_at"] == "2026-07-03T12:30:00+00:00"
    assert payload["source_row_count"] == "1"
    assert payload["rows"][0]["edge_probability"] == "0.120000"
    assert payload["rows"][0]["redacted_condition_id"] == redacted_condition_id(
        "0xabcdef1234567890secret",
    )
    assert "1234567890secret" not in repr(payload)
    assert "Decimal(" not in repr(payload)
    assert "datetime" not in payload_text

    def assert_no_float(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float(item)
        else:
            assert type(value) is not float

    assert_no_float(payload)


def test_digest_redacts_short_condition_ids_without_source_fragments() -> None:
    secret_condition_id = "secret"
    digest_report = report(input_row(condition_id=secret_condition_id))
    payload = api().strategy_probability_edge_calibration_digest_payload(digest_report)

    assert digest_report.rows[0].redacted_condition_id == redacted_condition_id(
        secret_condition_id,
    )
    assert secret_condition_id not in repr(digest_report).lower()
    assert secret_condition_id not in repr(payload).lower()


def test_digest_payload_rejects_dict_flag_downgrades_floats_and_live_surface() -> None:
    digest = api()

    with pytest.raises(ValueError, match="payload must be readonly"):
        digest.strategy_probability_edge_calibration_digest_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        digest.strategy_probability_edge_calibration_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "mean_absolute_edge": 0.1,
            },
        )

    with pytest.raises(ValueError, match="unsafe live surface"):
        digest.strategy_probability_edge_calibration_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet": "redacted",
            },
        )


def test_digest_applies_custom_thresholds_to_rows_counts_and_reasons() -> None:
    digest_report = report(
        input_row(
            forecast_probability=d("0.940000"),
            market_probability=d("0.900000"),
            realized_probability=d("1.000000"),
            edge_probability=d("0.040000"),
            edge_age_hours=d("4.000000"),
            reason_codes=(
                "edge_within_threshold",
                "resolved_calibration_available",
                "calibration_error_within_threshold",
                "edge_fresh",
            ),
        ),
        cfg=config(
            material_edge_threshold=d("0.030000"),
            calibration_error_threshold=d("0.050000"),
            stale_edge_hours=d("3.000000"),
        ),
    )

    assert digest_report.material_edge_count == d("1")
    assert digest_report.calibration_error_count == d("1")
    assert digest_report.stale_edge_count == d("1")
    assert digest_report.reason_codes == (
        "material_probability_edge_detected",
        "resolved_calibration_available",
        "calibration_error_detected",
        "stale_probability_edge_detected",
    )
    assert digest_report.reason_code_counts == (
        ("calibration_error_detected", d("1")),
        ("positive_edge_detected", d("1")),
        ("resolved_calibration_available", d("1")),
        ("stale_edge", d("1")),
    )
    assert digest_report.rows[0].reason_codes == (
        "positive_edge_detected",
        "resolved_calibration_available",
        "calibration_error_detected",
        "stale_edge",
    )


def test_digest_uses_deterministic_sorting_and_reason_code_ties() -> None:
    digest_report = report(
        input_row(
            strategy_id="zeta",
            market_slug="z-market",
            condition_id="0xzzzzzzzzzzzzzzzzsecret",
            forecast_probability=d("0.650000"),
            market_probability=d("0.500000"),
            realized_probability=None,
            edge_probability=d("0.150000"),
            edge_age_hours=d("1.000000"),
            reason_codes=("positive_edge_detected", "edge_fresh"),
        ),
        input_row(
            strategy_id="alpha",
            market_slug="a-market",
            condition_id="0xaaaaaaaaaaaaaaaaprivate",
            forecast_probability=d("0.350000"),
            market_probability=d("0.500000"),
            realized_probability=None,
            edge_probability=d("-0.150000"),
            edge_age_hours=d("1.000000"),
            reason_codes=("negative_edge_detected", "edge_fresh"),
        ),
    )

    assert tuple(row.strategy_id for row in digest_report.rows) == ("alpha", "zeta")
    assert digest_report.reason_code_counts == (
        ("edge_fresh", d("2")),
        ("negative_edge_detected", d("1")),
        ("positive_edge_detected", d("1")),
    )


def test_digest_validates_decimal_inputs_flags_and_frozen_outputs() -> None:
    digest = api()
    digest_report = report(input_row())

    with pytest.raises(FrozenInstanceError):
        digest_report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        input_row(forecast_probability=0.64)

    with pytest.raises(ValueError, match="forecast_probability"):
        input_row(forecast_probability=_DecimalSubclass("0.640000"))

    with pytest.raises(ValueError, match="forecast_probability must be finite"):
        input_row(forecast_probability=Decimal("NaN"))

    with pytest.raises(ValueError, match="material_edge_threshold must be finite"):
        config(material_edge_threshold=Decimal("Infinity"))

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(input_row(), generated_at="bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            input_row(),
            generated_at=datetime(2026, 7, 3, 12, 30, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest.StrategyProbabilityEdgeCalibrationDigestReport(
            generated_at=_DatetimeSubclass(2026, 7, 3, 12, 30, tzinfo=UTC),
            config_version="strategy-probability-edge-calibration-digest-v0",
            source_row_count=d("0"),
            strategy_count=d("0"),
            market_count=d("0"),
            material_edge_count=d("0"),
            resolved_calibration_count=d("0"),
            calibration_error_count=d("0"),
            stale_edge_count=d("0"),
            mean_absolute_edge=d("0.000000"),
            mean_signed_edge=d("0.000000"),
            mean_calibration_error=d("0.000000"),
            status="pass",
            reason_codes=("probability_edge_calibration_digest_clear",),
            reason_code_counts=(),
            rows=(),
        )

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="input must be readonly"):
        input_row(readonly=False)

    with pytest.raises(ValueError, match="source_row_count"):
        replace(digest_report, source_row_count=d("2"))

    with pytest.raises(ValueError, match="rows"):
        replace(digest_report, rows=(digest_report.rows[0],) * 2)


def test_digest_rejects_inconsistent_inputs() -> None:
    with pytest.raises(ValueError, match="edge_probability must match"):
        input_row(edge_probability=d("0.110000"))

    with pytest.raises(ValueError, match="reason_codes must match input"):
        input_row(reason_codes=("negative_edge_detected",))

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(
            input_row(
                strategy_id="alpha",
                market_slug="same-market",
                reason_codes=(
                    "positive_edge_detected",
                    "resolved_calibration_available",
                    "calibration_error_detected",
                    "edge_fresh",
                ),
            ),
            input_row(
                strategy_id="alpha",
                market_slug="same-market",
                reason_codes=(
                    "positive_edge_detected",
                    "resolved_calibration_available",
                    "calibration_error_detected",
                    "edge_fresh",
                ),
            ),
        )

    with pytest.raises(ValueError, match="realized_probability must be 0 or 1"):
        input_row(realized_probability=d("0.500000"))

    with pytest.raises(ValueError, match="stale_edge_hours"):
        config(stale_edge_hours=d("-1.000000"))


def test_module_scope_has_no_live_forbidden_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_probability_edge_calibration_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "network",
        "database",
        "db",
        "file io",
        "open(",
        "advice",
        "order",
        "trade",
        "trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
