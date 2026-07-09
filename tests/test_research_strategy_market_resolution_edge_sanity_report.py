from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_market_resolution_edge_sanity_report import (
    DEFAULT_RESEARCH_STRATEGY_MARKET_RESOLUTION_EDGE_SANITY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_MARKET_RESOLUTION_EDGE_SANITY_REPORT_STATUSES,
    ResearchStrategyMarketResolutionEdgeSanityConfig,
    ResearchStrategyMarketResolutionEdgeSanityInput,
    ResearchStrategyMarketResolutionEdgeSanityReasonCodeCount,
    ResearchStrategyMarketResolutionEdgeSanityReport,
    ResearchStrategyMarketResolutionEdgeSanityRow,
    build_research_strategy_market_resolution_edge_sanity_report,
    research_strategy_market_resolution_edge_sanity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyMarketResolutionEdgeSanityConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_MARKET_RESOLUTION_EDGE_SANITY_REPORT_CONFIG_VERSION
        ),
        "sanity_adjusted_edge_pass_floor": d("0.030000"),
        "sanity_adjusted_edge_watch_floor": d("0.000000"),
        "resolution_confidence_pass_floor": d("0.800000"),
        "resolution_confidence_watch_floor": d("0.500000"),
        "resolution_ambiguity_pass_ceiling": d("0.250000"),
        "resolution_ambiguity_watch_ceiling": d("0.600000"),
        "evidence_freshness_pass_floor": d("0.800000"),
        "evidence_freshness_watch_floor": d("0.500000"),
        "market_reaction_gap_pass_ceiling": d("0.250000"),
        "market_reaction_gap_watch_ceiling": d("0.600000"),
        "observation_age_pass_ceiling_seconds": d("3600.000000"),
        "observation_age_watch_ceiling_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return ResearchStrategyMarketResolutionEdgeSanityConfig(**values)


def sanity_input(**overrides: object) -> ResearchStrategyMarketResolutionEdgeSanityInput:
    values = {
        "candidate_ref": "candidate-alpha-secret-123",
        "market_ref": "market-id-alpha",
        "market_slug": "will-fed-cut-rates-alpha",
        "market_question": "Will the Fed cut rates before September?",
        "source_url": "https://example.test/source-alpha?token=hidden",
        "source_text": "raw evidence text should never leave the public payload",
        "observed_at": datetime(2026, 7, 8, 11, 30, tzinfo=UTC),
        "research_probability": d("0.640000"),
        "market_probability": d("0.560000"),
        "resolution_confidence_score": d("0.900000"),
        "resolution_ambiguity_score": d("0.100000"),
        "evidence_freshness_score": d("0.900000"),
        "market_reaction_gap_score": d("0.050000"),
    }
    values.update(overrides)
    return ResearchStrategyMarketResolutionEdgeSanityInput(**values)


def report(
    *rows: ResearchStrategyMarketResolutionEdgeSanityInput,
    cfg: ResearchStrategyMarketResolutionEdgeSanityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyMarketResolutionEdgeSanityReport:
    return build_research_strategy_market_resolution_edge_sanity_report(
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


def test_report_scores_market_resolution_edge_sanity() -> None:
    summary = report(
        sanity_input(
            candidate_ref="candidate-alpha-secret-123",
            market_ref="market-id-alpha",
            market_slug="will-fed-cut-rates-alpha",
            research_probability=d("0.640000"),
            market_probability=d("0.560000"),
            resolution_confidence_score=d("0.900000"),
            resolution_ambiguity_score=d("0.100000"),
            evidence_freshness_score=d("0.900000"),
            market_reaction_gap_score=d("0.050000"),
        ),
        sanity_input(
            candidate_ref="candidate-beta-secret-456",
            market_ref="market-id-beta",
            market_slug="will-fed-cut-rates-beta",
            research_probability=d("0.600000"),
            market_probability=d("0.560000"),
            resolution_confidence_score=d("0.700000"),
            resolution_ambiguity_score=d("0.200000"),
            evidence_freshness_score=d("0.800000"),
            market_reaction_gap_score=d("0.100000"),
        ),
        sanity_input(
            candidate_ref="candidate-gamma-secret-789",
            market_ref="market-id-gamma",
            market_slug="will-fed-cut-rates-gamma",
            observed_at=datetime(2026, 7, 8, 9, 0, tzinfo=UTC),
            research_probability=d("0.590000"),
            market_probability=d("0.560000"),
            resolution_confidence_score=d("0.300000"),
            resolution_ambiguity_score=d("0.700000"),
            evidence_freshness_score=d("0.400000"),
            market_reaction_gap_score=d("0.700000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyMarketResolutionEdgeSanityReport
    assert summary.generated_at == GENERATED_AT
    assert summary.source_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_raw_probability_edge == d("0.050000")
    assert summary.mean_sanity_adjusted_edge == d("0.003000")
    assert summary.mean_resolution_confidence_score == d("0.633333")
    assert summary.max_resolution_ambiguity_score == d("0.700000")
    assert summary.max_market_reaction_gap_score == d("0.700000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "edge_sanity_adjusted_edge_review",
        "evidence_freshness_review",
        "market_reaction_gap_review",
        "market_resolution_edge_sanity_report_block",
        "observation_age_review",
        "resolution_ambiguity_review",
        "resolution_confidence_review",
    )
    assert len(summary.derived_validation_digest) == 64
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True
    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyMarketResolutionEdgeSanityRow)
    assert blocked.raw_probability_edge == d("0.030000")
    assert blocked.resolution_confidence_haircut == d("0.021000")
    assert blocked.resolution_ambiguity_haircut == d("0.021000")
    assert blocked.evidence_freshness_haircut == d("0.018000")
    assert blocked.market_reaction_gap_haircut == d("0.021000")
    assert blocked.sanity_adjusted_edge == d("-0.051000")
    assert blocked.observation_age_seconds == d("10800.000000")
    assert blocked.reason_codes == (
        "edge_sanity_adjusted_edge_block",
        "evidence_freshness_block",
        "market_reaction_gap_block",
        "observation_age_block",
        "resolution_ambiguity_block",
        "resolution_confidence_block",
    )

    watched = summary.rows[1]
    assert watched.raw_probability_edge == d("0.040000")
    assert watched.sanity_adjusted_edge == d("0.008000")
    assert watched.reason_codes == (
        "edge_sanity_adjusted_edge_watch",
        "resolution_confidence_watch",
    )

    passed = summary.rows[2]
    assert passed.raw_probability_edge == d("0.080000")
    assert passed.sanity_adjusted_edge == d("0.052000")
    assert passed.reason_codes == ("market_resolution_edge_sanity_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["resolution_confidence_block"] == (
        ResearchStrategyMarketResolutionEdgeSanityReasonCodeCount(
            reason_code="resolution_confidence_block",
            count=d("1.000000"),
            input_ratio=d("0.333333"),
        )
    )


def test_payload_is_public_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_market_resolution_edge_sanity_report_payload(
        report(sanity_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_market_resolution_edge_sanity_report_payload(
        report(sanity_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["sanity_adjusted_edge"] == "0.052000"
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
        "token=hidden",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_market_resolution_edge_sanity_report_payload(
        report(sanity_input()),
    )
    tampered_payload["rows"][0]["sanity_adjusted_edge"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_market_resolution_edge_sanity_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_market_resolution_edge_sanity_report_payload(
            {
                "source_url": "https://example.test/secret",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_bad_flags_times_and_duplicate_candidates() -> None:
    with pytest.raises(ValueError, match="research_probability"):
        sanity_input(research_probability=0.64)
    with pytest.raises(ValueError, match="market_probability"):
        sanity_input(market_probability=_DecimalSubclass("0.560000"))
    with pytest.raises(ValueError, match="resolution_confidence_score"):
        sanity_input(resolution_confidence_score=d("1.200000"))
    with pytest.raises(ValueError, match="observed_at"):
        sanity_input(observed_at=datetime(2026, 7, 8, 11, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            sanity_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(sanity_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            sanity_input(candidate_ref="same_candidate"),
            sanity_input(candidate_ref="same_candidate", market_ref="market-id-beta"),
        )
    with pytest.raises(ValueError, match="sanity_adjusted_edge_pass_floor"):
        config(sanity_adjusted_edge_pass_floor=d("-0.010000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = report(sanity_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_MARKET_RESOLUTION_EDGE_SANITY_REPORT_STATUSES == (
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
            sanity_adjusted_edge=d("0.010000"),
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
        sanity_input(),
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
                    "seconds",
                    "probability",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_market_resolution_edge_sanity_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_MARKET_RESOLUTION_EDGE_SANITY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_MARKET_RESOLUTION_EDGE_SANITY_REPORT_STATUSES",
        "ResearchStrategyMarketResolutionEdgeSanityConfig",
        "ResearchStrategyMarketResolutionEdgeSanityInput",
        "ResearchStrategyMarketResolutionEdgeSanityReasonCodeCount",
        "ResearchStrategyMarketResolutionEdgeSanityRow",
        "ResearchStrategyMarketResolutionEdgeSanityReport",
        "build_research_strategy_market_resolution_edge_sanity_report",
        "research_strategy_market_resolution_edge_sanity_report_payload",
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
