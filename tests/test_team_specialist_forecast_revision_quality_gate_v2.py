from __future__ import annotations

import ast
import importlib
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
    / "team_specialist_forecast_revision_quality_gate_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_forecast_revision_quality_gate_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def revision(**overrides: object):
    module = api()
    values = {
        "team_id": "alpha_specialists",
        "specialist_id": "rates_specialist",
        "forecast_id": "forecast_alpha",
        "category_id": "macro_rates",
        "revised_at": GENERATED_AT,
        "prior_probability": d("0.400000"),
        "revised_probability": d("0.520000"),
        "evidence_support_score": d("0.900000"),
        "rationale_quality_score": d("0.800000"),
        "calibration_improvement_score": d("0.850000"),
        "timeliness_score": d("0.750000"),
        "revision_supported": True,
        "learning_feedback_available": False,
        "learning_feedback_score": d("0.000000"),
    }
    values.update(overrides)
    return module.TeamSpecialistForecastRevisionQualityGateV2Input(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    config = overrides.pop("config", None)
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            revision(),
            revision(
                team_id="beta_specialists",
                specialist_id="policy_specialist",
                forecast_id="forecast_beta",
                evidence_support_score=d("0.900000"),
                rationale_quality_score=d("0.900000"),
                calibration_improvement_score=d("0.900000"),
                timeliness_score=d("0.900000"),
                revision_supported=False,
            ),
            revision(
                team_id="gamma_specialists",
                specialist_id="energy_specialist",
                forecast_id="forecast_gamma",
                evidence_support_score=d("0.800000"),
                rationale_quality_score=d("0.800000"),
                calibration_improvement_score=d("0.750000"),
                timeliness_score=d("0.800000"),
                learning_feedback_available=True,
                learning_feedback_score=d("1.000000"),
            ),
        )
    return module.build_team_specialist_forecast_revision_quality_gate_v2(
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


def test_revision_quality_scoring_penalties_and_learning_feedback_boosts() -> None:
    report = build_report()

    assert report.gate_status == "watch"
    assert report.revision_count == d("3")
    assert report.pass_revision_count == d("2")
    assert report.watch_revision_count == d("1")
    assert report.blocked_revision_count == d("0")
    assert report.unsupported_revision_count == d("1")
    assert report.learning_feedback_revision_count == d("1")
    assert report.average_revision_quality_score == d("0.759167")
    assert report.top_revision_quality_score == d("0.840000")
    assert report.bottom_revision_quality_score == d("0.600000")
    assert report.reason_codes == (
        "team_specialist_forecast_revision_quality_gate_watch_rows",
        "team_specialist_forecast_revision_quality_gate_unsupported_revision_penalty_rows",
        "team_specialist_forecast_revision_quality_gate_learning_feedback_boost_rows",
    )

    rows = report.rows
    assert tuple(row.forecast_id for row in rows) == (
        "forecast_alpha",
        "forecast_gamma",
        "forecast_beta",
    )
    assert tuple(row.revision_quality_score for row in rows) == (
        d("0.840000"),
        d("0.837500"),
        d("0.600000"),
    )
    assert tuple(row.gate_status for row in rows) == ("pass", "pass", "watch")
    assert rows[1].learning_feedback_boost_applied == d("0.050000")
    assert "learning_feedback_boost_applied" in rows[1].reason_codes
    assert rows[2].unsupported_revision_penalty_applied == d("0.300000")
    assert "unsupported_revision_penalty_applied" in rows[2].reason_codes
    assert "revision_quality_score_below_pass_floor" in rows[2].reason_codes


def test_blocked_revision_quality_and_empty_report() -> None:
    blocked = build_report(
        revision(
            evidence_support_score=d("0.250000"),
            rationale_quality_score=d("0.300000"),
            calibration_improvement_score=d("0.200000"),
            timeliness_score=d("0.300000"),
        ),
    )

    assert blocked.gate_status == "blocked"
    assert blocked.blocked_revision_count == d("1")
    assert blocked.rows[0].revision_quality_score == d("0.257500")
    assert blocked.rows[0].reason_codes == (
        "team_specialist_forecast_revision_quality_blocked",
        "revision_quality_score_below_watch_floor",
    )

    empty = build_report(use_default_items=False)
    assert empty.gate_status == "blocked"
    assert empty.revision_count == d("0")
    assert empty.average_revision_quality_score == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "team_specialist_forecast_revision_quality_gate_empty",
    )


def test_payload_serializes_decimal_values_as_strings_and_keeps_hard_flags() -> None:
    module = api()
    report = build_report()
    payload = module.team_specialist_forecast_revision_quality_gate_v2_payload(report)

    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["revision_count"] == "3"
    assert payload["average_revision_quality_score"] == "0.759167"
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["revision_quality_score"] == "0.840000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert_no_float_values(payload)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistForecastRevisionQualityGateV2Config()
    sample = revision()
    report = build_report(sample)
    row = report.rows[0]

    for item in (config, sample, row, report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {
                "evidence_support_weight",
                "rationale_quality_weight",
                "calibration_improvement_weight",
                "timeliness_weight",
                "unsupported_revision_penalty",
                "max_learning_feedback_boost",
                "pass_score_floor",
                "watch_score_floor",
                "prior_probability",
                "revised_probability",
                "evidence_support_score",
                "rationale_quality_score",
                "calibration_improvement_score",
                "timeliness_score",
                "learning_feedback_score",
                "rank",
                "probability_delta_abs",
                "unsupported_revision_penalty_applied",
                "learning_feedback_boost_applied",
                "revision_quality_score",
                "revision_count",
                "pass_revision_count",
                "watch_revision_count",
                "blocked_revision_count",
                "unsupported_revision_count",
                "learning_feedback_revision_count",
                "average_revision_quality_score",
                "top_revision_quality_score",
                "bottom_revision_quality_score",
            }:
                assert type(value) is Decimal


def test_rejects_bad_numeric_types_hard_flag_overrides_and_digest_tampering() -> None:
    module = api()

    with pytest.raises(ValueError, match="evidence_support_score must be exactly Decimal"):
        revision(evidence_support_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="prior_probability must be exactly Decimal"):
        revision(prior_probability="0.400000")
    with pytest.raises(ValueError, match="paper_only must be True"):
        revision(paper_only=False)

    report = build_report()
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            generated_at=datetime(2026, 7, 6, 12, 1, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    object.__setattr__(report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        _ = report.payload

    report = build_report()
    with pytest.raises(ValueError, match="report must be exactly"):
        module.team_specialist_forecast_revision_quality_gate_v2_payload(report.payload)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("team_id", "live_specialists"),
        ("specialist_id", "auth_specialist"),
        ("forecast_id", "wallet_case"),
        ("category_id", "order_flow"),
        ("team_id", "network_panel"),
        ("specialist_id", "database_panel"),
        ("forecast_id", "persist_case"),
        ("category_id", "signing_case"),
        ("team_id", "mutation_panel"),
        ("specialist_id", "buy_case"),
        ("forecast_id", "sell_case"),
        ("category_id", "trade_case"),
    ),
)
def test_rejects_unsafe_public_values(field_name: str, bad_value: str) -> None:
    with pytest.raises(ValueError, match="unsafe public value"):
        revision(**{field_name: bad_value})


@pytest.mark.parametrize(
    "bad_key",
    (
        "live_key",
        "auth_key",
        "wallet_key",
        "order_key",
        "network_key",
        "database_key",
        "persist_key",
        "signing_key",
        "mutation_key",
        "buy_key",
        "sell_key",
        "trade_key",
    ),
)
def test_rejects_unsafe_public_payload_keys(bad_key: str) -> None:
    module = api()

    with pytest.raises(ValueError, match="unsafe public key"):
        module._reject_unsafe_public_payload("payload", {bad_key: "safe_value"})


def test_module_exposes_no_unsafe_execution_surfaces() -> None:
    module = api()
    unsafe_public_fragments = module.UNSAFE_PUBLIC_TEXT_FRAGMENTS

    for public_name in module.__all__:
        assert not any(fragment in public_name.lower() for fragment in unsafe_public_fragments)

    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "os",
        "socket",
        "subprocess",
        "requests",
        "urllib",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }
    forbidden_calls = {
        "open",
        "exec",
        "eval",
        "compile",
        "connect",
        "request",
        "urlopen",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls
