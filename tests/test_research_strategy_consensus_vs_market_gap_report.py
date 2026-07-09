from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_consensus_vs_market_gap_report import (
    DEFAULT_RESEARCH_STRATEGY_CONSENSUS_VS_MARKET_GAP_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_CONSENSUS_VS_MARKET_GAP_STATUSES,
    ResearchStrategyConsensusVsMarketGapConfig,
    ResearchStrategyConsensusVsMarketGapInput,
    ResearchStrategyConsensusVsMarketGapReasonCodeCount,
    ResearchStrategyConsensusVsMarketGapReport,
    ResearchStrategyConsensusVsMarketGapRow,
    build_research_strategy_consensus_vs_market_gap_report,
    research_strategy_consensus_vs_market_gap_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyConsensusVsMarketGapConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_CONSENSUS_VS_MARKET_GAP_REPORT_CONFIG_VERSION
        ),
        "gap_after_haircuts_pass_floor": d("0.030000"),
        "gap_after_haircuts_watch_floor": d("0.005000"),
        "confidence_score_pass_floor": d("0.800000"),
        "confidence_score_watch_floor": d("0.500000"),
        "total_cost_haircut_pass_ceiling": d("0.030000"),
        "total_cost_haircut_watch_ceiling": d("0.060000"),
        "confidence_haircut_pass_ceiling": d("0.025000"),
        "confidence_haircut_watch_ceiling": d("0.060000"),
        "consensus_band_width_pass_ceiling": d("0.120000"),
        "consensus_band_width_watch_ceiling": d("0.250000"),
    }
    values.update(overrides)
    return ResearchStrategyConsensusVsMarketGapConfig(**values)


def gap_input(**overrides: object) -> ResearchStrategyConsensusVsMarketGapInput:
    values = {
        "candidate_id": "candidate-alpha-raw",
        "market_id": "market-alpha-raw",
        "market_slug": "raw-market-alpha-slug",
        "observed_at": datetime(2026, 7, 8, 11, 45, tzinfo=UTC),
        "consensus_lower_probability": d("0.620000"),
        "consensus_upper_probability": d("0.680000"),
        "market_probability": d("0.540000"),
        "fee_probability_haircut": d("0.006000"),
        "spread_probability_haircut": d("0.004000"),
        "slippage_probability_haircut": d("0.002000"),
        "confidence_probability_haircut": d("0.008000"),
        "specialist_confidence_score": d("0.900000"),
    }
    values.update(overrides)
    return ResearchStrategyConsensusVsMarketGapInput(**values)


def report(
    *rows: ResearchStrategyConsensusVsMarketGapInput,
    cfg: ResearchStrategyConsensusVsMarketGapConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyConsensusVsMarketGapReport:
    return build_research_strategy_consensus_vs_market_gap_report(
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


def test_report_compares_consensus_bands_to_market_after_haircuts_for_manual_review() -> None:
    summary = report(
        gap_input(
            candidate_id="candidate-pass-raw",
            market_id="market-pass-raw",
            market_slug="raw-pass-market-slug",
            consensus_lower_probability=d("0.620000"),
            consensus_upper_probability=d("0.680000"),
            market_probability=d("0.540000"),
            fee_probability_haircut=d("0.006000"),
            spread_probability_haircut=d("0.004000"),
            slippage_probability_haircut=d("0.002000"),
            confidence_probability_haircut=d("0.008000"),
            specialist_confidence_score=d("0.900000"),
        ),
        gap_input(
            candidate_id="candidate-watch-raw",
            market_id="market-watch-raw",
            market_slug="raw-watch-market-slug",
            consensus_lower_probability=d("0.515000"),
            consensus_upper_probability=d("0.575000"),
            market_probability=d("0.470000"),
            fee_probability_haircut=d("0.006000"),
            spread_probability_haircut=d("0.004000"),
            slippage_probability_haircut=d("0.002000"),
            confidence_probability_haircut=d("0.008000"),
            specialist_confidence_score=d("0.700000"),
        ),
        gap_input(
            candidate_id="candidate-block-raw",
            market_id="market-block-raw",
            market_slug="raw-block-market-slug",
            consensus_lower_probability=d("0.400000"),
            consensus_upper_probability=d("0.450000"),
            market_probability=d("0.420000"),
            fee_probability_haircut=d("0.030000"),
            spread_probability_haircut=d("0.020000"),
            slippage_probability_haircut=d("0.010000"),
            confidence_probability_haircut=d("0.070000"),
            specialist_confidence_score=d("0.300000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyConsensusVsMarketGapReport
    assert summary.generated_at == GENERATED_AT
    assert summary.source_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_consensus_gap_after_haircuts == d("0.028333")
    assert summary.mean_total_cost_haircut == d("0.028000")
    assert summary.mean_confidence_haircut == d("0.028667")
    assert summary.minimum_specialist_confidence_score == d("0.300000")
    assert summary.widest_consensus_band_width == d("0.060000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "consensus_vs_market_gap_report_block",
        "confidence_haircut_review",
        "confidence_score_review",
        "gap_after_haircuts_review",
        "total_cost_haircut_review",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert len(summary.derived_validation_digest) == 64
    assert tuple(row.candidate_id for row in summary.rows) == (
        "candidate-block-raw",
        "candidate-watch-raw",
        "candidate-pass-raw",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyConsensusVsMarketGapRow)
    assert blocked.consensus_band_width == d("0.050000")
    assert blocked.total_cost_haircut == d("0.060000")
    assert blocked.market_probability_after_haircuts == d("0.420000")
    assert blocked.consensus_gap_after_haircuts == d("0.000000")
    assert blocked.gap_direction == "within_consensus_band"
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "confidence_haircut_block",
        "confidence_score_block",
        "gap_after_haircuts_block",
        "within_consensus_band_block",
    )

    watched = summary.rows[1]
    assert watched.market_probability_after_haircuts == d("0.490000")
    assert watched.consensus_gap_after_haircuts == d("0.025000")
    assert watched.gap_direction == "market_below_consensus_band"
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "confidence_score_watch",
        "gap_after_haircuts_watch",
    )

    passed = summary.rows[2]
    assert passed.market_probability_after_haircuts == d("0.560000")
    assert passed.consensus_gap_after_haircuts == d("0.060000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("consensus_vs_market_gap_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["gap_after_haircuts_watch"] == ResearchStrategyConsensusVsMarketGapReasonCodeCount(
        reason_code="gap_after_haircuts_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_payload_is_deterministic_decimal_stringed_and_digest_guarded_without_raw_ids() -> None:
    first_payload = research_strategy_consensus_vs_market_gap_report_payload(
        report(gap_input()),
    )
    second_payload = research_strategy_consensus_vs_market_gap_report_payload(
        report(gap_input()),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["market_probability_after_haircuts"] == "0.560000"
    assert first_payload["rows"][0]["consensus_gap_after_haircuts"] == "0.060000"
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
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "candidate-alpha-raw",
        "market-alpha-raw",
        "raw-market-alpha-slug",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_consensus_vs_market_gap_report_payload(
        report(gap_input()),
    )
    tampered_payload["rows"][0]["consensus_gap_after_haircuts"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_consensus_vs_market_gap_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_consensus_vs_market_gap_report_payload(
            {
                "market_slug": "raw-market-alpha-slug",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_flags_bad_times_and_duplicate_candidates() -> None:
    with pytest.raises(ValueError, match="market_probability"):
        gap_input(market_probability=0.54)
    with pytest.raises(ValueError, match="fee_probability_haircut"):
        gap_input(fee_probability_haircut=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="consensus_upper_probability"):
        gap_input(consensus_lower_probability=d("0.600000"), consensus_upper_probability=d("0.500000"))
    with pytest.raises(ValueError, match="observed_at"):
        gap_input(observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            gap_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(gap_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            gap_input(candidate_id="same-candidate", market_id="market-one"),
            gap_input(candidate_id="same-candidate", market_id="market-two"),
        )
    with pytest.raises(ValueError, match="gap_after_haircuts_pass_floor"):
        config(gap_after_haircuts_pass_floor=d("0.004000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = report(gap_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_CONSENSUS_VS_MARKET_GAP_STATUSES == (
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
            consensus_gap_after_haircuts=d("0.010000"),
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
        gap_input(),
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
                "candidate_id",
                "market_id",
                "market_slug",
                "gap_direction",
                "config_version",
                "status",
                "derived_validation_digest",
                "generated_at",
                "observed_at",
                "reason_code",
            }:
                continue
            if any(
                token in item.name
                for token in (
                    "count",
                    "floor",
                    "ceiling",
                    "gap",
                    "haircut",
                    "probability",
                    "ratio",
                    "score",
                    "width",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_consensus_vs_market_gap_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CONSENSUS_VS_MARKET_GAP_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_CONSENSUS_VS_MARKET_GAP_STATUSES",
        "ResearchStrategyConsensusVsMarketGapConfig",
        "ResearchStrategyConsensusVsMarketGapInput",
        "ResearchStrategyConsensusVsMarketGapReasonCodeCount",
        "ResearchStrategyConsensusVsMarketGapRow",
        "ResearchStrategyConsensusVsMarketGapReport",
        "build_research_strategy_consensus_vs_market_gap_report",
        "research_strategy_consensus_vs_market_gap_report_payload",
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
