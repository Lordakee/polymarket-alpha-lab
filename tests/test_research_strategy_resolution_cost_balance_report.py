from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_resolution_cost_balance_report import (
    DEFAULT_RESEARCH_STRATEGY_RESOLUTION_COST_BALANCE_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_RESOLUTION_COST_BALANCE_REPORT_STATUSES,
    ResearchStrategyResolutionCostBalanceConfig,
    ResearchStrategyResolutionCostBalanceInput,
    ResearchStrategyResolutionCostBalanceReasonCodeCount,
    ResearchStrategyResolutionCostBalanceReport,
    ResearchStrategyResolutionCostBalanceRow,
    build_research_strategy_resolution_cost_balance_report,
    research_strategy_resolution_cost_balance_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyResolutionCostBalanceConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_RESOLUTION_COST_BALANCE_REPORT_CONFIG_VERSION
        ),
        "credible_edge_pass_floor": d("0.030000"),
        "credible_edge_watch_floor": d("0.000000"),
        "resolution_ambiguity_pass_ceiling": d("0.250000"),
        "resolution_ambiguity_watch_ceiling": d("0.600000"),
        "review_latency_pass_ceiling": d("0.250000"),
        "review_latency_watch_ceiling": d("0.600000"),
        "fee_spread_haircut_pass_ceiling": d("0.025000"),
        "fee_spread_haircut_watch_ceiling": d("0.070000"),
        "evidence_confidence_pass_floor": d("0.800000"),
        "evidence_confidence_watch_floor": d("0.500000"),
    }
    values.update(overrides)
    return ResearchStrategyResolutionCostBalanceConfig(**values)


def balance_input(**overrides: object) -> ResearchStrategyResolutionCostBalanceInput:
    values = {
        "candidate_ref": "candidate-alpha-secret-123",
        "market_ref": "market-id-alpha",
        "market_slug": "will-fed-cut-rates-alpha",
        "market_question": "Will the Fed cut rates before September?",
        "source_url": "https://example.test/source-alpha?token=hidden",
        "source_text": "raw evidence text should never leave the public payload",
        "observed_at": datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
        "expected_edge": d("0.080000"),
        "resolution_ambiguity_score": d("0.100000"),
        "review_latency_score": d("0.050000"),
        "fee_haircut": d("0.006000"),
        "spread_haircut": d("0.004000"),
        "evidence_confidence_score": d("0.900000"),
    }
    values.update(overrides)
    return ResearchStrategyResolutionCostBalanceInput(**values)


def report(
    *rows: ResearchStrategyResolutionCostBalanceInput,
    cfg: ResearchStrategyResolutionCostBalanceConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyResolutionCostBalanceReport:
    return build_research_strategy_resolution_cost_balance_report(
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


def test_report_balances_resolution_cost_latency_and_confidence() -> None:
    summary = report(
        balance_input(
            candidate_ref="candidate-alpha-secret-123",
            market_ref="market-id-alpha",
            market_slug="will-fed-cut-rates-alpha",
            expected_edge=d("0.080000"),
            resolution_ambiguity_score=d("0.100000"),
            review_latency_score=d("0.050000"),
            fee_haircut=d("0.006000"),
            spread_haircut=d("0.004000"),
            evidence_confidence_score=d("0.900000"),
        ),
        balance_input(
            candidate_ref="candidate-beta-secret-456",
            market_ref="market-id-beta",
            market_slug="will-fed-cut-rates-beta",
            expected_edge=d("0.070000"),
            resolution_ambiguity_score=d("0.200000"),
            review_latency_score=d("0.200000"),
            fee_haircut=d("0.012000"),
            spread_haircut=d("0.018000"),
            evidence_confidence_score=d("0.700000"),
        ),
        balance_input(
            candidate_ref="candidate-gamma-secret-789",
            market_ref="market-id-gamma",
            market_slug="will-fed-cut-rates-gamma",
            expected_edge=d("0.050000"),
            resolution_ambiguity_score=d("0.700000"),
            review_latency_score=d("0.650000"),
            fee_haircut=d("0.030000"),
            spread_haircut=d("0.035000"),
            evidence_confidence_score=d("0.300000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyResolutionCostBalanceReport
    assert summary.generated_at == GENERATED_AT
    assert summary.source_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_expected_edge == d("0.066667")
    assert summary.mean_fee_spread_haircut == d("0.035000")
    assert summary.mean_confidence_adjusted_edge == d("0.011950")
    assert summary.mean_evidence_confidence_score == d("0.633333")
    assert summary.max_resolution_ambiguity_score == d("0.700000")
    assert summary.max_review_latency_score == d("0.650000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "credible_edge_review",
        "evidence_confidence_review",
        "fee_spread_haircut_review",
        "resolution_ambiguity_review",
        "resolution_cost_balance_report_block",
        "review_latency_review",
    )
    assert len(summary.derived_validation_digest) == 64
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyResolutionCostBalanceRow)
    assert blocked.resolution_ambiguity_haircut == d("0.035000")
    assert blocked.review_latency_haircut == d("0.032500")
    assert blocked.fee_spread_haircut == d("0.065000")
    assert blocked.pre_confidence_edge == d("-0.082500")
    assert blocked.confidence_adjusted_edge == d("-0.024750")
    assert blocked.reason_codes == (
        "credible_edge_block",
        "evidence_confidence_block",
        "fee_spread_haircut_watch",
        "resolution_ambiguity_block",
        "review_latency_block",
    )

    watched = summary.rows[1]
    assert watched.pre_confidence_edge == d("0.012000")
    assert watched.confidence_adjusted_edge == d("0.008400")
    assert watched.reason_codes == (
        "credible_edge_watch",
        "evidence_confidence_watch",
        "fee_spread_haircut_watch",
    )

    passed = summary.rows[2]
    assert passed.confidence_adjusted_edge == d("0.052200")
    assert passed.reason_codes == ("resolution_cost_balance_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["fee_spread_haircut_watch"] == (
        ResearchStrategyResolutionCostBalanceReasonCodeCount(
            reason_code="fee_spread_haircut_watch",
            count=d("2.000000"),
            input_ratio=d("0.666667"),
        )
    )


def test_payload_is_public_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_resolution_cost_balance_report_payload(
        report(balance_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_resolution_cost_balance_report_payload(
        report(balance_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["confidence_adjusted_edge"] == "0.052200"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )
    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_ref",
        "market_ref",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "candidate-alpha-secret-123",
        "market-id-alpha",
        "will-fed-cut-rates-alpha",
        "will the fed cut rates",
        "https://example.test",
        "raw evidence text",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_resolution_cost_balance_report_payload(
        report(balance_input()),
    )
    tampered_payload["rows"][0]["confidence_adjusted_edge"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_resolution_cost_balance_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_resolution_cost_balance_report_payload(
            {
                "source_url": "https://example.test/secret",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_resolution_cost_balance_report_payload(
            {
                "api_key": "hidden",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_resolution_cost_balance_report_payload(
            {
                "status": "pass",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_bad_flags_times_and_duplicate_candidates() -> None:
    with pytest.raises(ValueError, match="expected_edge"):
        balance_input(expected_edge=0.08)
    with pytest.raises(ValueError, match="fee_haircut"):
        balance_input(fee_haircut=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="resolution_ambiguity_score"):
        balance_input(resolution_ambiguity_score=d("1.200000"))
    with pytest.raises(ValueError, match="observed_at"):
        balance_input(observed_at=datetime(2026, 7, 8, 11, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            balance_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(balance_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            balance_input(candidate_ref="same_candidate"),
            balance_input(candidate_ref="same_candidate", market_ref="market-id-beta"),
        )
    with pytest.raises(ValueError, match="credible_edge_pass_floor"):
        config(credible_edge_pass_floor=d("-0.010000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = report(balance_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_RESOLUTION_COST_BALANCE_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            confidence_adjusted_edge=d("0.010000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            source_row_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )

    for value in (
        config(),
        balance_input(),
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
                "candidate_ref",
                "market_ref",
                "market_slug",
                "market_question",
                "source_url",
                "source_text",
                "config_version",
                "status",
                "derived_validation_digest",
                "observed_at",
                "generated_at",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "count",
                    "edge",
                    "haircut",
                    "floor",
                    "ceiling",
                    "score",
                    "ratio",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_resolution_cost_balance_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_RESOLUTION_COST_BALANCE_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_RESOLUTION_COST_BALANCE_REPORT_STATUSES",
        "ResearchStrategyResolutionCostBalanceConfig",
        "ResearchStrategyResolutionCostBalanceInput",
        "ResearchStrategyResolutionCostBalanceReasonCodeCount",
        "ResearchStrategyResolutionCostBalanceRow",
        "ResearchStrategyResolutionCostBalanceReport",
        "build_research_strategy_resolution_cost_balance_report",
        "research_strategy_resolution_cost_balance_report_payload",
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
