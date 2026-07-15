from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import inspect
import json
from typing import Any

import pytest

import polymarket_alpha_lab.probability_edge_sensitivity_report as api
from polymarket_alpha_lab.probability_edge_sensitivity_report import (
    PROBABILITY_EDGE_SENSITIVITY_REPORT_STATUSES,
    ProbabilityEdgeSensitivityInput,
    ProbabilityEdgeSensitivityReport,
    ProbabilityEdgeSensitivityRow,
    build_probability_edge_sensitivity_report,
    probability_edge_sensitivity_report_digest,
    probability_edge_sensitivity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 11, 16, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def sensitivity_input(**overrides: object) -> ProbabilityEdgeSensitivityInput:
    values = {
        "edge_ref": "screen-alpha",
        "observed_at": datetime(2026, 7, 11, 15, 55, tzinfo=UTC),
        "forecast_probability": d("0.620000"),
        "market_probability": d("0.560000"),
        "cost_adjusted_threshold_probability": d("0.590000"),
        "forecast_error_buffer_probability": d("0.010000"),
        "liquidity_haircut_probability": d("0.005000"),
        "source_uncertainty_buffer_probability": d("0.005000"),
    }
    values.update(overrides)
    return ProbabilityEdgeSensitivityInput(**values)


def report(
    *inputs: ProbabilityEdgeSensitivityInput,
    generated_at: datetime = GENERATED_AT,
) -> ProbabilityEdgeSensitivityReport:
    return build_probability_edge_sensitivity_report(
        inputs,
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def resign_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    signed = json.loads(json.dumps(payload))
    for row in signed.get("rows", []):
        row.pop("derived_validation_digest", None)
        row["derived_validation_digest"] = hashlib.sha256(
            json.dumps(
                row,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8"),
        ).hexdigest()
    signed.pop("derived_validation_digest", None)
    signed["derived_validation_digest"] = hashlib.sha256(
        json.dumps(
            signed,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    return signed


def test_report_computes_adjusted_edge_break_even_and_sensitivity_bands() -> None:
    summary = report(
        sensitivity_input(
            edge_ref="screen-block",
            forecast_probability=d("0.595000"),
            market_probability=d("0.560000"),
            cost_adjusted_threshold_probability=d("0.590000"),
            forecast_error_buffer_probability=d("0.015000"),
            liquidity_haircut_probability=d("0.015000"),
            source_uncertainty_buffer_probability=d("0.010000"),
        ),
        sensitivity_input(
            edge_ref="screen-watch",
            forecast_probability=d("0.620000"),
            market_probability=d("0.560000"),
            cost_adjusted_threshold_probability=d("0.590000"),
            forecast_error_buffer_probability=d("0.010000"),
            liquidity_haircut_probability=d("0.005000"),
            source_uncertainty_buffer_probability=d("0.005000"),
        ),
        sensitivity_input(
            edge_ref="screen-pass",
            forecast_probability=d("0.660000"),
            market_probability=d("0.560000"),
            cost_adjusted_threshold_probability=d("0.590000"),
            forecast_error_buffer_probability=d("0.010000"),
            liquidity_haircut_probability=d("0.005000"),
            source_uncertainty_buffer_probability=d("0.005000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ProbabilityEdgeSensitivityReport
    assert summary.generated_at == GENERATED_AT
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.attention_count == d("1.000000")
    assert summary.blocker_count == d("1.000000")
    assert summary.mean_adjusted_edge_probability == d("0.038333")
    assert summary.min_safety_margin_probability == d("-0.035000")
    assert summary.status == "blocker"
    assert summary.reason_codes == (
        "adjusted_edge_blocker_review",
        "buffer_load_attention_review",
        "probability_edge_sensitivity_report_blocker",
        "threshold_margin_attention_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64

    blocked, watched, passed = summary.rows
    assert isinstance(blocked, ProbabilityEdgeSensitivityRow)
    assert blocked.edge_ref == "screen-block"
    assert blocked.gross_edge_probability == d("0.035000")
    assert blocked.total_buffer_probability == d("0.040000")
    assert blocked.adjusted_edge_probability == d("-0.005000")
    assert blocked.break_even_forecast_probability == d("0.630000")
    assert blocked.safety_margin_probability == d("-0.035000")
    assert blocked.sensitivity_band == "blocker"
    assert blocked.reason_codes == (
        "adjusted_edge_not_positive_blocker",
        "buffer_load_attention",
        "threshold_margin_negative_blocker",
    )

    assert watched.adjusted_edge_probability == d("0.040000")
    assert watched.break_even_forecast_probability == d("0.610000")
    assert watched.safety_margin_probability == d("0.010000")
    assert watched.sensitivity_band == "attention"
    assert watched.reason_codes == ("threshold_margin_thin_attention",)

    assert passed.adjusted_edge_probability == d("0.080000")
    assert passed.break_even_forecast_probability == d("0.610000")
    assert passed.safety_margin_probability == d("0.050000")
    assert passed.sensitivity_band == "pass"
    assert passed.reason_codes == ("probability_edge_sensitivity_pass",)


def test_empty_report_blocks_as_missing_readonly_inputs() -> None:
    summary = report()

    assert summary.status == "blocker"
    assert summary.input_count == d("0.000000")
    assert summary.pass_count == d("0.000000")
    assert summary.attention_count == d("0.000000")
    assert summary.blocker_count == d("0.000000")
    assert summary.mean_adjusted_edge_probability == d("0.000000")
    assert summary.min_safety_margin_probability == d("0.000000")
    assert summary.reason_codes == ("probability_edge_sensitivity_report_empty",)
    assert summary.reason_code_counts == (("probability_edge_sensitivity_report_empty", d("1.000000")),)
    assert summary.rows == ()


def test_payload_and_digest_are_public_safe_deterministic_and_guarded() -> None:
    generated_at = datetime(2026, 7, 11, 12, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = probability_edge_sensitivity_report_payload(
        report(sensitivity_input(), generated_at=generated_at),
    )
    second_payload = probability_edge_sensitivity_report_payload(
        report(sensitivity_input(), generated_at=generated_at),
    )
    digest = probability_edge_sensitivity_report_digest(
        report(sensitivity_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-11T16:00:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["adjusted_edge_probability"] == "0.040000"
    assert first_payload["rows"][0]["break_even_forecast_probability"] == "0.610000"
    assert first_payload["rows"][0]["safety_margin_probability"] == "0.010000"
    assert "edge_ref" not in first_payload["rows"][0]
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert digest == {
        "generated_at": "2026-07-11T16:00:00+00:00",
        "status": "attention",
        "input_count": "1.000000",
        "pass_count": "0.000000",
        "attention_count": "1.000000",
        "blocker_count": "0.000000",
        "mean_adjusted_edge_probability": "0.040000",
        "min_safety_margin_probability": "0.010000",
        "reason_codes": ["threshold_margin_attention_review"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "derived_validation_digest": first_payload["derived_validation_digest"],
    }
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    digest_input = dict(first_payload)
    digest_input.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_input,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert first_payload["derived_validation_digest"] == expected_digest

    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "edge_ref",
        "screen-alpha",
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "execute",
        "database",
        "network",
    ):
        assert forbidden not in payload_text

    tampered = json.loads(json.dumps(first_payload))
    tampered["rows"][0]["adjusted_edge_probability"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        probability_edge_sensitivity_report_payload(tampered)


def test_public_payload_validator_rejects_actionable_or_unsafe_surfaces_after_resigning() -> None:
    payload = probability_edge_sensitivity_report_payload(report(sensitivity_input()))

    bad_report_status = resign_public_payload({**payload, "status": "ready"})
    with pytest.raises(ValueError, match="status"):
        probability_edge_sensitivity_report_payload(bad_report_status)

    bad_row_band = json.loads(json.dumps(payload))
    bad_row_band["rows"][0]["sensitivity_band"] = "execute"
    with pytest.raises(ValueError, match="sensitivity_band"):
        probability_edge_sensitivity_report_payload(resign_public_payload(bad_row_band))

    execution_surface = resign_public_payload({**payload, "execution_mode": "paper"})
    with pytest.raises(ValueError, match="public"):
        probability_edge_sensitivity_report_payload(execution_surface)


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    summary = report(sensitivity_input())

    with pytest.raises(FrozenInstanceError):
        summary.status = "attention"  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        sensitivity_input(forecast_probability=0.62)

    with pytest.raises(ValueError, match="paper_only"):
        replace(sensitivity_input(), paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(summary.rows[0], readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary.rows[0], adjusted_edge_probability=d("0.999999"))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, attention_count=d("0.000000"))


def test_no_io_execution_or_trading_surface_is_exposed() -> None:
    assert set(PROBABILITY_EDGE_SENSITIVITY_REPORT_STATUSES) == {
        "pass",
        "attention",
        "blocker",
    }

    unsafe_terms = (
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "execute",
        "execution",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ProbabilityEdgeSensitivityInput,
        ProbabilityEdgeSensitivityRow,
        ProbabilityEdgeSensitivityReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)

    tree = ast.parse(inspect.getsource(api))
    imported_modules = {
        node.module.split(".")[0] if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(node.module or "")])
    }
    assert imported_modules.isdisjoint(
        {
            "requests",
            "httpx",
            "urllib",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "psycopg",
            "supabase",
            "web3",
            "ccxt",
            "subprocess",
            "pathlib",
        },
    )
