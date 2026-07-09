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

import polymarket_alpha_lab.research_strategy_probability_edge_sensitivity_report as api
from polymarket_alpha_lab.research_strategy_probability_edge_sensitivity_report import (
    DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_SENSITIVITY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_PROBABILITY_EDGE_SENSITIVITY_STATUSES,
    ResearchStrategyProbabilityEdgeSensitivityConfig,
    ResearchStrategyProbabilityEdgeSensitivityInput,
    ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount,
    ResearchStrategyProbabilityEdgeSensitivityReport,
    ResearchStrategyProbabilityEdgeSensitivityRow,
    build_research_strategy_probability_edge_sensitivity_report,
    research_strategy_probability_edge_sensitivity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyProbabilityEdgeSensitivityConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_SENSITIVITY_REPORT_CONFIG_VERSION
        ),
        "pass_conservative_edge_floor": d("0.030000"),
        "watch_conservative_edge_floor": d("0.010000"),
        "pass_fragility_ceiling": d("0.500000"),
        "watch_fragility_ceiling": d("0.850000"),
        "freshness_drift_per_hour": d("0.001000"),
        "max_freshness_drift_haircut": d("0.100000"),
        "component_watch_haircut": d("0.020000"),
        "component_block_haircut": d("0.050000"),
    }
    values.update(overrides)
    return ResearchStrategyProbabilityEdgeSensitivityConfig(**values)


def sensitivity_input(
    **overrides: object,
) -> ResearchStrategyProbabilityEdgeSensitivityInput:
    values = {
        "edge_ref": "raw-" + "candidate-alpha-" + "market-slug",
        "observed_at": datetime(2026, 7, 8, 11, 45, tzinfo=UTC),
        "model_probability": d("0.620000"),
        "quoted_probability": d("0.560000"),
        "model_uncertainty_bound": d("0.010000"),
        "fee_haircut": d("0.005000"),
        "spread_haircut": d("0.005000"),
        "freshness_age_hours": d("2.000000"),
        "resolution_risk_haircut": d("0.005000"),
    }
    values.update(overrides)
    return ResearchStrategyProbabilityEdgeSensitivityInput(**values)


def report(
    *rows: ResearchStrategyProbabilityEdgeSensitivityInput,
    cfg: ResearchStrategyProbabilityEdgeSensitivityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyProbabilityEdgeSensitivityReport:
    return build_research_strategy_probability_edge_sensitivity_report(
        rows,
        config=cfg or config(),
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


def test_report_evaluates_probability_edge_fragility_under_haircuts() -> None:
    summary = report(
        sensitivity_input(
            edge_ref="raw-" + "candidate-block-" + "market-slug",
            model_probability=d("0.600000"),
            quoted_probability=d("0.560000"),
            model_uncertainty_bound=d("0.020000"),
            fee_haircut=d("0.010000"),
            spread_haircut=d("0.010000"),
            freshness_age_hours=d("20.000000"),
            resolution_risk_haircut=d("0.010000"),
        ),
        sensitivity_input(
            edge_ref="raw-" + "candidate-watch-" + "market-slug",
            model_probability=d("0.610000"),
            quoted_probability=d("0.560000"),
            model_uncertainty_bound=d("0.010000"),
            fee_haircut=d("0.005000"),
            spread_haircut=d("0.005000"),
            freshness_age_hours=d("10.000000"),
            resolution_risk_haircut=d("0.005000"),
        ),
        sensitivity_input(
            edge_ref="raw-" + "candidate-pass-" + "market-slug",
            model_probability=d("0.620000"),
            quoted_probability=d("0.560000"),
            model_uncertainty_bound=d("0.010000"),
            fee_haircut=d("0.005000"),
            spread_haircut=d("0.005000"),
            freshness_age_hours=d("2.000000"),
            resolution_risk_haircut=d("0.005000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyProbabilityEdgeSensitivityReport
    assert summary.generated_at == GENERATED_AT
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_gross_probability_edge == d("0.050000")
    assert summary.mean_total_haircut == d("0.044000")
    assert summary.mean_conservative_probability_edge == d("0.006000")
    assert summary.max_fragility_score == d("1.000000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "conservative_edge_review",
        "fragility_review",
        "freshness_drift_review",
        "probability_edge_sensitivity_report_block",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert tuple(row.edge_ref for row in summary.rows) == (
        "raw-" + "candidate-block-" + "market-slug",
        "raw-" + "candidate-watch-" + "market-slug",
        "raw-" + "candidate-pass-" + "market-slug",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyProbabilityEdgeSensitivityRow)
    assert blocked.gross_probability_edge == d("0.040000")
    assert blocked.freshness_drift_haircut == d("0.020000")
    assert blocked.fee_spread_haircut == d("0.020000")
    assert blocked.total_haircut == d("0.070000")
    assert blocked.conservative_probability_edge == d("-0.030000")
    assert blocked.fragility_score == d("1.000000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "conservative_edge_block",
        "fragility_block",
        "freshness_drift_watch",
    )

    watched = summary.rows[1]
    assert watched.total_haircut == d("0.035000")
    assert watched.conservative_probability_edge == d("0.015000")
    assert watched.fragility_score == d("0.700000")
    assert watched.status == "watch"
    assert watched.reason_codes == ("conservative_edge_watch", "fragility_watch")

    passed = summary.rows[2]
    assert passed.total_haircut == d("0.027000")
    assert passed.conservative_probability_edge == d("0.033000")
    assert passed.fragility_score == d("0.450000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("probability_edge_sensitivity_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["fragility_watch"] == ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount(
        reason_code="fragility_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_empty_report_blocks_for_missing_sensitivity_inputs() -> None:
    summary = report()

    assert summary.status == "block"
    assert summary.input_count == d("0.000000")
    assert summary.reason_codes == ("probability_edge_sensitivity_report_empty",)
    assert summary.reason_code_counts == (
        ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount(
            reason_code="probability_edge_sensitivity_report_empty",
            count=d("1.000000"),
            input_ratio=d("0.000000"),
        ),
    )
    assert summary.rows == ()


def test_payload_is_deterministic_public_safe_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_probability_edge_sensitivity_report_payload(
        report(sensitivity_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_probability_edge_sensitivity_report_payload(
        report(sensitivity_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["conservative_probability_edge"] == "0.033000"
    assert "edge_ref" not in first_payload["rows"][0]
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    digest_input = dict(first_payload)
    digest_input.pop("derived_validation_digest")
    expected_digest = __import__("hashlib").sha256(
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
        "raw-" + "candidate-alpha",
        "market-slug",
        "market_id",
        "market_slug",
        "question",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wal" + "let",
        "or" + "der",
        "trad" + "e",
        "b" + "uy",
        "se" + "ll",
    ):
        assert forbidden not in payload_text

    tampered = json.loads(json.dumps(first_payload))
    tampered["rows"][0]["conservative_probability_edge"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_probability_edge_sensitivity_report_payload(tampered)


def test_public_payload_validator_rejects_non_diagnostic_surfaces_after_resigning() -> None:
    payload = research_strategy_probability_edge_sensitivity_report_payload(
        report(sensitivity_input()),
    )

    bad_report_status = resign_public_payload({**payload, "status": "allow"})
    with pytest.raises(ValueError, match="status"):
        research_strategy_probability_edge_sensitivity_report_payload(bad_report_status)

    bad_row_status = json.loads(json.dumps(payload))
    bad_row_status["rows"][0]["status"] = "allow"
    with pytest.raises(ValueError, match="status"):
        research_strategy_probability_edge_sensitivity_report_payload(
            resign_public_payload(bad_row_status),
        )

    execution_surface = resign_public_payload({**payload, "execution_mode": "paper"})
    with pytest.raises(ValueError, match="public"):
        research_strategy_probability_edge_sensitivity_report_payload(execution_surface)


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    summary = report(sensitivity_input())

    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="Decimal"):
        sensitivity_input(model_probability=0.62)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(summary.rows[0], readonly=False)


def test_derived_validation_digest_rejects_internal_tampering() -> None:
    summary = report(sensitivity_input())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary.rows[0], conservative_probability_edge=d("0.010000"))


def test_no_unsafe_public_or_automation_surfaces_are_exposed() -> None:
    assert set(RESEARCH_STRATEGY_PROBABILITY_EDGE_SENSITIVITY_STATUSES) == {
        "pass",
        "watch",
        "block",
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
        "wal" + "let",
        "or" + "der",
        "trad" + "e",
        "b" + "uy",
        "se" + "ll",
        "reco" + "mmend",
        "siz" + "ing",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)

    for cls in (
        ResearchStrategyProbabilityEdgeSensitivityConfig,
        ResearchStrategyProbabilityEdgeSensitivityInput,
        ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount,
        ResearchStrategyProbabilityEdgeSensitivityRow,
        ResearchStrategyProbabilityEdgeSensitivityReport,
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
            "web3",
            "ccxt",
        },
    )
