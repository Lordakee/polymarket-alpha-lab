from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_source_confidence_cost_alignment_report import (
    DEFAULT_RESEARCH_STRATEGY_SOURCE_CONFIDENCE_COST_ALIGNMENT_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_SOURCE_CONFIDENCE_COST_ALIGNMENT_REPORT_STATUSES,
    ResearchStrategySourceConfidenceCostAlignmentConfig,
    ResearchStrategySourceConfidenceCostAlignmentInput,
    ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount,
    ResearchStrategySourceConfidenceCostAlignmentReport,
    ResearchStrategySourceConfidenceCostAlignmentRow,
    build_research_strategy_source_confidence_cost_alignment_report,
    research_strategy_source_confidence_cost_alignment_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategySourceConfidenceCostAlignmentConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SOURCE_CONFIDENCE_COST_ALIGNMENT_REPORT_CONFIG_VERSION
        ),
        "source_confidence_pass_floor": d("0.800000"),
        "source_confidence_watch_floor": d("0.550000"),
        "probability_edge_pass_floor": d("0.050000"),
        "probability_edge_watch_floor": d("0.015000"),
        "fee_cost_pressure_pass_ceiling": d("0.010000"),
        "fee_cost_pressure_watch_ceiling": d("0.020000"),
        "spread_cost_pressure_pass_ceiling": d("0.015000"),
        "spread_cost_pressure_watch_ceiling": d("0.030000"),
        "liquidity_cost_pressure_pass_ceiling": d("0.008000"),
        "liquidity_cost_pressure_watch_ceiling": d("0.020000"),
        "total_cost_pressure_pass_ceiling": d("0.030000"),
        "total_cost_pressure_watch_ceiling": d("0.060000"),
    }
    values.update(overrides)
    return ResearchStrategySourceConfidenceCostAlignmentConfig(**values)


def alignment_input(**overrides: object) -> ResearchStrategySourceConfidenceCostAlignmentInput:
    values = {
        "candidate_id": "candidate_alpha_raw_id",
        "market_id": "market_alpha_raw_id",
        "market_slug": "market-alpha-slug",
        "market_question": "Will alpha resolve yes?",
        "observed_at": datetime(2026, 7, 8, 11, 40, tzinfo=UTC),
        "sanitized_source_confidence_score": d("0.920000"),
        "forecast_probability": d("0.620000"),
        "market_probability": d("0.560000"),
        "fee_cost_pressure_score": d("0.006000"),
        "spread_cost_pressure_score": d("0.010000"),
        "liquidity_cost_pressure_score": d("0.004000"),
    }
    values.update(overrides)
    return ResearchStrategySourceConfidenceCostAlignmentInput(**values)


def report(
    *inputs: ResearchStrategySourceConfidenceCostAlignmentInput,
    cfg: ResearchStrategySourceConfidenceCostAlignmentConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySourceConfidenceCostAlignmentReport:
    return build_research_strategy_source_confidence_cost_alignment_report(
        inputs,
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


def public_payload_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def resign_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = public_payload_digest(payload)
    return payload


def test_alignment_scoring_combines_source_edge_and_cost_pressure() -> None:
    summary = report(
        alignment_input(
            candidate_id="candidate_alpha_raw_id",
            market_id="market_alpha_raw_id",
            market_slug="market-alpha-slug",
            sanitized_source_confidence_score=d("0.920000"),
            forecast_probability=d("0.620000"),
            market_probability=d("0.560000"),
            fee_cost_pressure_score=d("0.006000"),
            spread_cost_pressure_score=d("0.010000"),
            liquidity_cost_pressure_score=d("0.004000"),
        ),
        alignment_input(
            candidate_id="candidate_beta_raw_id",
            market_id="market_beta_raw_id",
            market_slug="market-beta-slug",
            sanitized_source_confidence_score=d("0.700000"),
            forecast_probability=d("0.570000"),
            market_probability=d("0.530000"),
            fee_cost_pressure_score=d("0.010000"),
            spread_cost_pressure_score=d("0.015000"),
            liquidity_cost_pressure_score=d("0.010000"),
        ),
        alignment_input(
            candidate_id="candidate_gamma_raw_id",
            market_id="market_gamma_raw_id",
            market_slug="market-gamma-slug",
            sanitized_source_confidence_score=d("0.400000"),
            forecast_probability=d("0.520000"),
            market_probability=d("0.510000"),
            fee_cost_pressure_score=d("0.030000"),
            spread_cost_pressure_score=d("0.035000"),
            liquidity_cost_pressure_score=d("0.025000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategySourceConfidenceCostAlignmentReport
    assert summary.generated_at == GENERATED_AT
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_sanitized_source_confidence_score == d("0.673333")
    assert summary.mean_absolute_probability_edge == d("0.036667")
    assert summary.mean_total_cost_pressure_score == d("0.048333")
    assert summary.mean_alignment_score == d("0.618624")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "source_confidence_cost_alignment_report_block",
        "source_confidence_review",
        "probability_edge_review",
        "cost_pressure_review",
    )
    assert tuple(row.candidate_id for row in summary.rows) == (
        "candidate_gamma_raw_id",
        "candidate_beta_raw_id",
        "candidate_alpha_raw_id",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategySourceConfidenceCostAlignmentRow)
    assert blocked.raw_probability_edge == d("0.010000")
    assert blocked.absolute_probability_edge == d("0.010000")
    assert blocked.total_cost_pressure_score == d("0.090000")
    assert blocked.probability_edge_strength_score == d("0.000000")
    assert blocked.cost_pressure_safety_score == d("0.000000")
    assert blocked.alignment_score == d("0.133333")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "source_confidence_cost_alignment_block",
        "source_confidence_block",
        "probability_edge_block",
        "cost_pressure_block",
    )

    watched = summary.rows[1]
    assert watched.total_cost_pressure_score == d("0.035000")
    assert watched.probability_edge_strength_score == d("0.714286")
    assert watched.cost_pressure_safety_score == d("0.833333")
    assert watched.alignment_score == d("0.749206")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "source_confidence_cost_alignment_watch",
        "source_confidence_watch",
        "probability_edge_watch",
        "cost_pressure_watch",
    )

    passed = summary.rows[2]
    assert passed.status == "pass"
    assert passed.alignment_score == d("0.973333")
    assert passed.reason_codes == (
        "source_confidence_cost_alignment_pass",
        "source_confidence_pass",
        "probability_edge_pass",
        "cost_pressure_pass",
    )
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts[
        "source_confidence_cost_alignment_watch"
    ] == ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount(
        reason_code="source_confidence_cost_alignment_watch",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_cost_pressure_boundaries_are_inclusive_for_pass_and_watch() -> None:
    summary = report(
        alignment_input(
            candidate_id="candidate_pass_boundary",
            fee_cost_pressure_score=d("0.010000"),
            spread_cost_pressure_score=d("0.012000"),
            liquidity_cost_pressure_score=d("0.008000"),
        ),
        alignment_input(
            candidate_id="candidate_watch_boundary",
            fee_cost_pressure_score=d("0.020000"),
            spread_cost_pressure_score=d("0.020000"),
            liquidity_cost_pressure_score=d("0.020000"),
        ),
        alignment_input(
            candidate_id="candidate_block_boundary",
            fee_cost_pressure_score=d("0.020001"),
            spread_cost_pressure_score=d("0.020000"),
            liquidity_cost_pressure_score=d("0.020000"),
        ),
    )

    rows = {row.candidate_id: row for row in summary.rows}
    assert rows["candidate_pass_boundary"].total_cost_pressure_score == d("0.030000")
    assert rows["candidate_pass_boundary"].status == "pass"
    assert "cost_pressure_pass" in rows["candidate_pass_boundary"].reason_codes
    assert rows["candidate_watch_boundary"].total_cost_pressure_score == d("0.060000")
    assert rows["candidate_watch_boundary"].status == "watch"
    assert "cost_pressure_watch" in rows["candidate_watch_boundary"].reason_codes
    assert rows["candidate_block_boundary"].total_cost_pressure_score == d("0.060001")
    assert rows["candidate_block_boundary"].status == "block"
    assert "cost_pressure_block" in rows["candidate_block_boundary"].reason_codes


def test_public_payload_is_deterministic_sanitized_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    first_payload = research_strategy_source_confidence_cost_alignment_report_payload(
        report(alignment_input(), generated_at=generated_at),
    )
    second_payload = research_strategy_source_confidence_cost_alignment_report_payload(
        report(alignment_input(), generated_at=generated_at),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["alignment_score"] == "0.973333"
    assert first_payload["rows"][0]["total_cost_pressure_score"] == "0.020000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert len(first_payload["rows"][0]["derived_validation_digest"]) == 64
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
        "source_url",
        "source_text",
        "candidate_alpha_raw_id",
        "market_alpha_raw_id",
        "market-alpha-slug",
        "will alpha resolve yes",
        "https://example.invalid/private-alpha",
        "private alpha source text",
        "dsn=",
        "access_token",
        "wallet",
        "order",
        "trade",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in payload_text

    tampered_payload = research_strategy_source_confidence_cost_alignment_report_payload(
        report(alignment_input()),
    )
    tampered_payload["rows"][0]["alignment_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_source_confidence_cost_alignment_report_payload(tampered_payload)

    extra_report_field_payload = research_strategy_source_confidence_cost_alignment_report_payload(
        report(alignment_input()),
    )
    extra_report_field_payload["research_note"] = "clean"
    resign_public_payload(extra_report_field_payload)
    with pytest.raises(ValueError, match="unexpected"):
        research_strategy_source_confidence_cost_alignment_report_payload(
            extra_report_field_payload,
        )

    extra_row_field_payload = research_strategy_source_confidence_cost_alignment_report_payload(
        report(alignment_input()),
    )
    extra_row_field_payload["rows"][0]["row_note"] = "clean"
    resign_public_payload(extra_row_field_payload["rows"][0])
    resign_public_payload(extra_row_field_payload)
    with pytest.raises(ValueError, match="unexpected"):
        research_strategy_source_confidence_cost_alignment_report_payload(
            extra_row_field_payload,
        )

    raw_numeric_payload = research_strategy_source_confidence_cost_alignment_report_payload(
        report(alignment_input()),
    )
    raw_numeric_payload["input_count"] = 1
    resign_public_payload(raw_numeric_payload)
    with pytest.raises(ValueError, match="input_count"):
        research_strategy_source_confidence_cost_alignment_report_payload(raw_numeric_payload)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_source_confidence_cost_alignment_report_payload(
            {
                "access_" + "token": "redacted",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_custom_config_validation_and_empty_report() -> None:
    custom = config(
        source_confidence_pass_floor=d("0.900000"),
        source_confidence_watch_floor=d("0.700000"),
        probability_edge_pass_floor=d("0.080000"),
        probability_edge_watch_floor=d("0.030000"),
        total_cost_pressure_pass_ceiling=d("0.020000"),
        total_cost_pressure_watch_ceiling=d("0.040000"),
    )
    summary = report(alignment_input(), cfg=custom)
    empty = report(cfg=custom)

    assert summary.status == "watch"
    assert summary.rows[0].status == "watch"
    assert "probability_edge_watch" in summary.rows[0].reason_codes
    assert empty.input_count == d("0.000000")
    assert empty.pass_count == d("0.000000")
    assert empty.watch_count == d("0.000000")
    assert empty.block_count == d("0.000000")
    assert empty.mean_alignment_score == d("0.000000")
    assert empty.status == "block"
    assert empty.reason_codes == ("source_confidence_cost_alignment_report_empty",)
    assert empty.reason_code_counts == (
        ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount(
            reason_code="source_confidence_cost_alignment_report_empty",
            count=d("1.000000"),
            input_ratio=d("1.000000"),
        ),
    )

    with pytest.raises(ValueError, match="source_confidence_pass_floor"):
        config(
            source_confidence_pass_floor=d("0.500000"),
            source_confidence_watch_floor=d("0.500000"),
        )
    with pytest.raises(ValueError, match="fee_cost_pressure_pass_ceiling"):
        config(
            fee_cost_pressure_pass_ceiling=d("0.030000"),
            fee_cost_pressure_watch_ceiling=d("0.020000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)


def test_validation_rejects_non_decimal_flags_bad_times_and_duplicate_candidates() -> None:
    with pytest.raises(ValueError, match="sanitized_source_confidence_score"):
        alignment_input(sanitized_source_confidence_score=0.92)
    with pytest.raises(ValueError, match="fee_cost_pressure_score"):
        alignment_input(fee_cost_pressure_score=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="market_probability"):
        alignment_input(market_probability=d("1.200000"))
    with pytest.raises(ValueError, match="observed_at"):
        alignment_input(observed_at=datetime(2026, 7, 8, 11, 40))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            alignment_input(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(alignment_input(observed_at=datetime(2026, 7, 8, 12, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(
            alignment_input(candidate_id="same_candidate", market_id="market_a"),
            alignment_input(candidate_id="same_candidate", market_id="market_b"),
        )
    with pytest.raises(ValueError, match="input must be report_only"):
        report(alignment_input(report_only=False))


def test_dataclasses_are_frozen_decimal_only_and_module_has_no_external_surfaces() -> None:
    summary = report(alignment_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_SOURCE_CONFIDENCE_COST_ALIGNMENT_REPORT_STATUSES == (
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
            total_cost_pressure_score=d("0.010000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )

    for value in (
        config(),
        alignment_input(),
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
                "market_question",
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
                    "ceiling",
                    "confidence",
                    "cost",
                    "count",
                    "edge",
                    "floor",
                    "probability",
                    "ratio",
                    "score",
                )
            ):
                assert type(item_value) is Decimal

    import polymarket_alpha_lab.research_strategy_source_confidence_cost_alignment_report as module

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_SOURCE_CONFIDENCE_COST_ALIGNMENT_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_SOURCE_CONFIDENCE_COST_ALIGNMENT_REPORT_STATUSES",
        "ResearchStrategySourceConfidenceCostAlignmentConfig",
        "ResearchStrategySourceConfidenceCostAlignmentInput",
        "ResearchStrategySourceConfidenceCostAlignmentReasonCodeCount",
        "ResearchStrategySourceConfidenceCostAlignmentRow",
        "ResearchStrategySourceConfidenceCostAlignmentReport",
        "build_research_strategy_source_confidence_cost_alignment_report",
        "research_strategy_source_confidence_cost_alignment_report_payload",
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

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_source_confidence_cost_alignment_report.py"
    )
    module_source = module_path.read_text(encoding="utf-8").lower()
    forbidden_source_terms = (
        "request",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "connect(",
        "open(",
        "create_" + "order",
        "cancel_" + "order",
        "post(",
        "wal" + "let",
        "reco" + "mmendation",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "trad" + "e",
    )
    assert all(term not in module_source for term in forbidden_source_terms)

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
