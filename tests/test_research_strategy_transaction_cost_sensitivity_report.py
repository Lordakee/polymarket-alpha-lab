from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_transaction_cost_sensitivity_report import (
    DEFAULT_RESEARCH_STRATEGY_TRANSACTION_COST_SENSITIVITY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_TRANSACTION_COST_SENSITIVITY_STATUSES,
    ResearchStrategyTransactionCostSensitivityConfig,
    ResearchStrategyTransactionCostSensitivityInput,
    ResearchStrategyTransactionCostSensitivityReasonCodeCount,
    ResearchStrategyTransactionCostSensitivityReport,
    ResearchStrategyTransactionCostSensitivityRow,
    build_research_strategy_transaction_cost_sensitivity_report,
    research_strategy_transaction_cost_sensitivity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyTransactionCostSensitivityConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_TRANSACTION_COST_SENSITIVITY_REPORT_CONFIG_VERSION
        ),
        "required_cost_profile_count": d("3.000000"),
        "profile_coverage_pass_floor": d("1.000000"),
        "profile_coverage_watch_floor": d("0.650000"),
        "max_pass_input_age_seconds": d("3600.000000"),
        "max_watch_input_age_seconds": d("14400.000000"),
        "completeness_pass_floor": d("0.900000"),
        "completeness_watch_floor": d("0.650000"),
    }
    values.update(overrides)
    return ResearchStrategyTransactionCostSensitivityConfig(**values)


def cost_input(**overrides: object) -> ResearchStrategyTransactionCostSensitivityInput:
    values = {
        "cost_case_ref": "case_alpha",
        "cost_profile_ref": "baseline",
        "observed_at": datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
        "fee_bps": d("10.000000"),
        "spread_bps": d("20.000000"),
        "slippage_bps": d("5.000000"),
        "settlement_bps": d("5.000000"),
        "completeness_score": d("0.950000"),
    }
    values.update(overrides)
    return ResearchStrategyTransactionCostSensitivityInput(**values)


def report(
    *rows: ResearchStrategyTransactionCostSensitivityInput,
    cfg: ResearchStrategyTransactionCostSensitivityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyTransactionCostSensitivityReport:
    return build_research_strategy_transaction_cost_sensitivity_report(
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


def build_mixed_report() -> ResearchStrategyTransactionCostSensitivityReport:
    return report(
        cost_input(
            cost_case_ref="case_alpha",
            cost_profile_ref="baseline",
            observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
            fee_bps=d("10.000000"),
            spread_bps=d("20.000000"),
            slippage_bps=d("5.000000"),
            settlement_bps=d("5.000000"),
            completeness_score=d("0.950000"),
        ),
        cost_input(
            cost_case_ref="case_alpha",
            cost_profile_ref="elevated",
            observed_at=datetime(2026, 7, 8, 11, 20, tzinfo=UTC),
            fee_bps=d("15.000000"),
            spread_bps=d("25.000000"),
            slippage_bps=d("7.500000"),
            settlement_bps=d("7.500000"),
            completeness_score=d("0.970000"),
        ),
        cost_input(
            cost_case_ref="case_alpha",
            cost_profile_ref="stress",
            observed_at=datetime(2026, 7, 8, 11, 10, tzinfo=UTC),
            fee_bps=d("20.000000"),
            spread_bps=d("30.000000"),
            slippage_bps=d("10.000000"),
            settlement_bps=d("10.000000"),
            completeness_score=d("0.960000"),
        ),
        cost_input(
            cost_case_ref="case_beta",
            cost_profile_ref="baseline",
            observed_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
            fee_bps=d("20.000000"),
            spread_bps=d("35.000000"),
            slippage_bps=d("15.000000"),
            settlement_bps=d("10.000000"),
            completeness_score=d("0.800000"),
        ),
        cost_input(
            cost_case_ref="case_beta",
            cost_profile_ref="stress",
            observed_at=datetime(2026, 7, 8, 10, 0, tzinfo=UTC),
            fee_bps=d("25.000000"),
            spread_bps=d("40.000000"),
            slippage_bps=d("20.000000"),
            settlement_bps=d("10.000000"),
            completeness_score=d("0.820000"),
        ),
        cost_input(
            cost_case_ref="case_gamma",
            cost_profile_ref="baseline",
            observed_at=datetime(2026, 7, 8, 7, 0, tzinfo=UTC),
            fee_bps=d("30.000000"),
            spread_bps=d("25.000000"),
            slippage_bps=d("10.000000"),
            settlement_bps=d("5.000000"),
            completeness_score=d("0.400000"),
        ),
    )


def test_report_flags_freshness_and_completeness_without_strategy_decisions() -> None:
    summary = build_mixed_report()

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyTransactionCostSensitivityReport
    assert summary.generated_at == GENERATED_AT
    assert summary.input_profile_count == d("6.000000")
    assert summary.cost_case_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_profile_coverage_score == d("0.666667")
    assert summary.mean_min_completeness_score == d("0.716667")
    assert summary.mean_max_input_age_seconds == d("9400.000000")
    assert summary.mean_readiness_score == d("0.430556")
    assert summary.mean_cost_sensitivity_span_bps == d("15.000000")
    assert summary.max_cost_sensitivity_span_bps == d("30.000000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "transaction_cost_sensitivity_report_block",
        "cost_input_age_review",
        "cost_input_completeness_review",
        "cost_profile_coverage_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert tuple(row.cost_case_ref for row in summary.rows) == (
        "case_gamma",
        "case_beta",
        "case_alpha",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyTransactionCostSensitivityRow)
    assert blocked.profile_count == d("1.000000")
    assert blocked.missing_profile_count == d("2.000000")
    assert blocked.profile_coverage_score == d("0.333333")
    assert blocked.max_input_age_seconds == d("18000.000000")
    assert blocked.min_completeness_score == d("0.400000")
    assert blocked.average_total_cost_bps == d("70.000000")
    assert blocked.cost_sensitivity_span_bps == d("0.000000")
    assert blocked.readiness_score == d("0.000000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "cost_input_age_block",
        "cost_input_completeness_block",
        "cost_profile_coverage_block",
    )

    watched = summary.rows[1]
    assert watched.profile_count == d("2.000000")
    assert watched.missing_profile_count == d("1.000000")
    assert watched.profile_coverage_score == d("0.666667")
    assert watched.max_input_age_seconds == d("7200.000000")
    assert watched.min_completeness_score == d("0.800000")
    assert watched.average_total_cost_bps == d("87.500000")
    assert watched.cost_sensitivity_span_bps == d("15.000000")
    assert watched.readiness_score == d("0.500000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "cost_input_age_watch",
        "cost_input_completeness_watch",
        "cost_profile_coverage_watch",
    )

    passed = summary.rows[2]
    assert passed.profile_count == d("3.000000")
    assert passed.missing_profile_count == d("0.000000")
    assert passed.profile_coverage_score == d("1.000000")
    assert passed.max_input_age_seconds == d("3000.000000")
    assert passed.min_completeness_score == d("0.950000")
    assert passed.average_total_cost_bps == d("55.000000")
    assert passed.cost_sensitivity_span_bps == d("30.000000")
    assert passed.readiness_score == d("0.791667")
    assert passed.status == "pass"
    assert passed.reason_codes == ("transaction_cost_sensitivity_ready",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts[
        "cost_input_age_watch"
    ] == ResearchStrategyTransactionCostSensitivityReasonCodeCount(
        reason_code="cost_input_age_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_payload_is_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_transaction_cost_sensitivity_report_payload(
        report(cost_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_transaction_cost_sensitivity_report_payload(
        report(cost_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_profile_count"] == "1.000000"
    assert first_payload["rows"][0]["average_total_cost_bps"] == "40.000000"
    assert first_payload["rows"][0]["readiness_score"] == "0.333333"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    forbidden_payload_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source",
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
    )
    payload_text = repr(first_payload).lower()
    assert all(fragment not in payload_text for fragment in forbidden_payload_fragments)

    tampered_payload = research_strategy_transaction_cost_sensitivity_report_payload(
        report(cost_input()),
    )
    tampered_payload["rows"][0]["min_completeness_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_transaction_cost_sensitivity_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_transaction_cost_sensitivity_report_payload(
            {
                "mar" + "ket_id": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_flags_bad_times_and_duplicate_profiles() -> None:
    with pytest.raises(ValueError, match="fee_bps"):
        cost_input(fee_bps=10)
    with pytest.raises(ValueError, match="spread_bps"):
        cost_input(spread_bps=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="slippage_bps"):
        cost_input(slippage_bps=d("-0.000001"))
    with pytest.raises(ValueError, match="completeness_score"):
        cost_input(completeness_score=d("1.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        cost_input(observed_at=datetime(2026, 7, 8, 11, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            cost_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(cost_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            cost_input(cost_case_ref="case_same", cost_profile_ref="baseline"),
            cost_input(cost_case_ref="case_same", cost_profile_ref="baseline"),
        )
    with pytest.raises(ValueError, match="profile_coverage_pass_floor"):
        config(profile_coverage_pass_floor=d("0.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = build_mixed_report()
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_TRANSACTION_COST_SENSITIVITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            average_total_cost_bps=d("1.000000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_profile_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )

    for value in (
        config(),
        cost_input(),
        row,
        summary,
        *summary.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item_value is None or item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "reason_codes",
                "reason_code_counts",
                "rows",
                "cost_case_ref",
                "cost_profile_ref",
            }:
                continue
            if any(
                token in item.name
                for token in ("count", "score", "seconds", "bps", "ratio")
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_transaction_cost_sensitivity_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TRANSACTION_COST_SENSITIVITY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_TRANSACTION_COST_SENSITIVITY_STATUSES",
        "ResearchStrategyTransactionCostSensitivityConfig",
        "ResearchStrategyTransactionCostSensitivityInput",
        "ResearchStrategyTransactionCostSensitivityReasonCodeCount",
        "ResearchStrategyTransactionCostSensitivityRow",
        "ResearchStrategyTransactionCostSensitivityReport",
        "build_research_strategy_transaction_cost_sensitivity_report",
        "research_strategy_transaction_cost_sensitivity_report_payload",
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

    forbidden_terms = (
        "reco" + "mmend",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "wal" + "let",
        "or" + "der",
        "trad" + "e",
        "trad" + "ing",
        "data" + "base",
        "net" + "work",
        "au" + "th",
        "tok" + "en",
        "request",
        "socket",
        "subprocess",
        "open(",
        "candidate_id",
        "mar" + "ket_id",
        "mar" + "ket_slug",
        "question",
        "sou" + "rce_text",
        "sou" + "rce_url",
        "d" + "sn",
        "tab" + "le_name",
    )
    assert all(term not in source.lower() for term in forbidden_terms)

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
