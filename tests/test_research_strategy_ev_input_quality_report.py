from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_strategy_ev_input_quality_report import (
    DEFAULT_RESEARCH_STRATEGY_EV_INPUT_QUALITY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_EV_INPUT_QUALITY_STATUSES,
    ResearchStrategyEvInputQualityConfig,
    ResearchStrategyEvInputQualityInput,
    ResearchStrategyEvInputQualityReport,
    ResearchStrategyEvInputQualityRow,
    build_research_strategy_ev_input_quality_report,
    research_strategy_ev_input_quality_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyEvInputQualityConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_STRATEGY_EV_INPUT_QUALITY_REPORT_CONFIG_VERSION,
        "calibration_watch_error_threshold": d("0.075000"),
        "calibration_block_error_threshold": d("0.200000"),
        "cost_watch_probability_threshold": d("0.030000"),
        "cost_block_probability_threshold": d("0.070000"),
        "liquidity_watch_score_floor": d("0.600000"),
        "liquidity_block_score_floor": d("0.300000"),
        "source_confidence_watch_score_floor": d("0.750000"),
        "source_confidence_block_score_floor": d("0.450000"),
        "resolution_rule_watch_score_floor": d("0.900000"),
        "resolution_rule_block_score_floor": d("0.650000"),
    }
    values.update(overrides)
    return ResearchStrategyEvInputQualityConfig(**values)


def ev_input(**overrides: object) -> ResearchStrategyEvInputQualityInput:
    values = {
        "ev_case_ref": "case_alpha",
        "strategy_ref": "strategy_alpha",
        "market_slug": "market-alpha",
        "observed_at": datetime(2026, 7, 8, 11, 50, tzinfo=UTC),
        "forecast_probability": d("0.980000"),
        "market_probability": d("0.930000"),
        "resolved_probability": d("1.000000"),
        "fee_probability_cost": d("0.008000"),
        "spread_probability_cost": d("0.006000"),
        "slippage_probability_cost": d("0.003000"),
        "liquidity_score": d("0.820000"),
        "source_confidence_score": d("0.910000"),
        "resolution_rule_completeness_score": d("0.950000"),
    }
    values.update(overrides)
    return ResearchStrategyEvInputQualityInput(**values)


def report(
    *rows: ResearchStrategyEvInputQualityInput,
    cfg: ResearchStrategyEvInputQualityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyEvInputQualityReport:
    return build_research_strategy_ev_input_quality_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_scores_aggregate_ev_input_quality_for_manual_review() -> None:
    summary = report(
        ev_input(),
        ev_input(
            ev_case_ref="case_beta",
            strategy_ref="strategy_beta",
            market_slug="market-beta",
            resolved_probability=None,
            fee_probability_cost=d("0.020000"),
            spread_probability_cost=d("0.015000"),
            slippage_probability_cost=d("0.005000"),
            liquidity_score=d("0.450000"),
            source_confidence_score=d("0.650000"),
            resolution_rule_completeness_score=d("0.800000"),
        ),
        ev_input(
            ev_case_ref="case_gamma",
            strategy_ref="strategy_gamma",
            market_slug="market-gamma",
            forecast_probability=d("0.700000"),
            market_probability=d("0.520000"),
            resolved_probability=d("0.000000"),
            fee_probability_cost=d("0.040000"),
            spread_probability_cost=d("0.030000"),
            slippage_probability_cost=d("0.020000"),
            liquidity_score=d("0.200000"),
            source_confidence_score=d("0.350000"),
            resolution_rule_completeness_score=d("0.500000"),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == DEFAULT_RESEARCH_STRATEGY_EV_INPUT_QUALITY_REPORT_CONFIG_VERSION
    assert summary.source_row_count == d("3")
    assert summary.pass_count == d("1")
    assert summary.watch_count == d("1")
    assert summary.block_count == d("1")
    assert summary.mean_probability_calibration_error == d("0.360000")
    assert summary.mean_total_cost_probability == d("0.049000")
    assert summary.mean_liquidity_score == d("0.490000")
    assert summary.mean_source_confidence_score == d("0.636667")
    assert summary.mean_resolution_rule_completeness_score == d("0.750000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "cost_input_review",
        "input_quality_block",
        "liquidity_review",
        "probability_calibration_review",
        "resolution_rule_review",
        "source_confidence_review",
    )
    assert tuple(row.ev_case_ref for row in summary.rows) == (
        "case_gamma",
        "case_beta",
        "case_alpha",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyEvInputQualityRow)
    assert blocked.forecast_market_gap_probability == d("0.180000")
    assert blocked.probability_calibration_error == d("0.700000")
    assert blocked.total_cost_probability == d("0.090000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "cost_inputs_block",
        "liquidity_block",
        "probability_calibration_block",
        "resolution_rule_block",
        "source_confidence_block",
    )

    watched = summary.rows[1]
    assert watched.probability_calibration_error == d("0.000000")
    assert watched.total_cost_probability == d("0.040000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "cost_inputs_watch",
        "liquidity_watch",
        "probability_calibration_missing_resolution",
        "resolution_rule_watch",
        "source_confidence_watch",
    )

    passed = summary.rows[2]
    assert passed.status == "pass"
    assert passed.reason_codes == ("ev_input_quality_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True
    assert len(passed.derived_validation_digest) == 64


def test_payload_is_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_ev_input_quality_report_payload(
        report(ev_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_ev_input_quality_report_payload(
        report(ev_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["rows"][0]["forecast_market_gap_probability"] == "0.050000"
    assert first_payload["rows"][0]["total_cost_probability"] == "0.017000"
    assert "market_group_ref" in first_payload["rows"][0]
    payload_text = repr(first_payload)
    assert "market_slug" not in payload_text
    assert "market-alpha" not in payload_text
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64

    tampered_payload = research_strategy_ev_input_quality_report_payload(report(ev_input()))
    tampered_payload["rows"][0]["total_cost_probability"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_ev_input_quality_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_ev_input_quality_report_payload(
            {
                "credential_ref": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_ev_input_quality_report_payload(
            {
                "note": "secret phrase",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_ev_input_quality_report_payload(
            {
                "market_slug": "will-event-resolve",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_missing_resolution_only_is_valid_watch_sentinel_reason() -> None:
    summary = report(ev_input(resolved_probability=None))

    assert summary.status == "watch"
    assert summary.watch_count == d("1")
    assert summary.block_count == d("0")
    assert summary.rows[0].status == "watch"
    assert summary.rows[0].reason_codes == (
        "probability_calibration_missing_resolution",
    )


def test_validation_rejects_non_decimal_flags_bad_times_and_duplicate_cases() -> None:
    with pytest.raises(ValueError, match="forecast_probability"):
        ev_input(forecast_probability=0.62)
    with pytest.raises(ValueError, match="forecast_probability"):
        ev_input(forecast_probability=d("1.200000"))
    with pytest.raises(ValueError, match="resolved_probability"):
        ev_input(resolved_probability=d("0.500000"))
    with pytest.raises(ValueError, match="observed_at"):
        ev_input(observed_at=datetime(2026, 7, 8, 11, 50))
    with pytest.raises(ValueError, match="generated_at"):
        report(ev_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(ev_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            ev_input(ev_case_ref="same_case"),
            ev_input(ev_case_ref="same_case", strategy_ref="strategy_beta"),
        )
    with pytest.raises(ValueError, match="threshold"):
        config(calibration_watch_error_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_reject_tampering() -> None:
    summary = report(ev_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_EV_INPUT_QUALITY_STATUSES == ("pass", "watch", "block")
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            total_cost_probability=d("0.010000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            source_row_count=d("0"),
            derived_validation_digest=summary.derived_validation_digest,
        )


def test_module_scope_is_pure_report_reducer_with_local_exports_only() -> None:
    import polymarket_alpha_lab.research_strategy_ev_input_quality_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_EV_INPUT_QUALITY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_EV_INPUT_QUALITY_STATUSES",
        "ResearchStrategyEvInputQualityConfig",
        "ResearchStrategyEvInputQualityInput",
        "ResearchStrategyEvInputQualityRow",
        "ResearchStrategyEvInputQualityReport",
        "build_research_strategy_ev_input_quality_report",
        "research_strategy_ev_input_quality_report_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_source_terms = (
        "reco" + "mmendation",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "wal" + "let",
        "or" + "der",
        "li" + "ve",
        "trad" + "ing",
        "data" + "base",
        "net" + "work",
        "request",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names
