from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_cost_depth_memory_scorecard_report import (
    DEFAULT_RESEARCH_MARKET_COST_DEPTH_MEMORY_SCORECARD_CONFIG_VERSION,
    MarketCostDepthMemoryScorecardConfig,
    MarketCostDepthMemoryScorecardInput,
    MarketCostDepthMemoryScorecardReasonCodeCount,
    MarketCostDepthMemoryScorecardReport,
    build_research_market_cost_depth_memory_scorecard_report,
    research_market_cost_depth_memory_scorecard_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketCostDepthMemoryScorecardConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_COST_DEPTH_MEMORY_SCORECARD_CONFIG_VERSION
        ),
        "max_pass_cost_rate": d("0.025000"),
        "max_watch_cost_rate": d("0.060000"),
        "min_pass_depth_score": d("0.700000"),
        "min_watch_depth_score": d("0.450000"),
        "min_pass_memory_confidence_score": d("0.750000"),
        "min_watch_memory_confidence_score": d("0.500000"),
        "min_pass_memory_recency_score": d("0.700000"),
        "min_watch_memory_recency_score": d("0.450000"),
        "pass_min_scorecard_score": d("0.850000"),
    }
    values.update(overrides)
    return MarketCostDepthMemoryScorecardConfig(**values)


def input_row(
    *,
    cost_rate: Decimal = d("0.020000"),
    depth_score: Decimal = d("0.900000"),
    memory_confidence_score: Decimal = d("0.900000"),
    memory_recency_score: Decimal = d("0.900000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("manual_memory_review",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketCostDepthMemoryScorecardInput:
    return MarketCostDepthMemoryScorecardInput(
        cost_rate=cost_rate,
        depth_score=depth_score,
        memory_confidence_score=memory_confidence_score,
        memory_recency_score=memory_recency_score,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: MarketCostDepthMemoryScorecardInput,
    cfg: MarketCostDepthMemoryScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketCostDepthMemoryScorecardReport:
    return build_research_market_cost_depth_memory_scorecard_report(
        items,
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


def term(*parts: str) -> str:
    return "".join(parts)


def test_builds_pass_watch_and_block_report_only_rows() -> None:
    scorecard_report = report(
        input_row(
            cost_rate=d("0.080000"),
            depth_score=d("0.300000"),
            memory_confidence_score=d("0.400000"),
            memory_recency_score=d("0.300000"),
            reason_codes=("manual_memory_review", "desk_escalation"),
        ),
        input_row(
            cost_rate=d("0.040000"),
            depth_score=d("0.600000"),
            memory_confidence_score=d("0.650000"),
            memory_recency_score=d("0.600000"),
        ),
        input_row(reason_codes=("memory_coverage_complete",)),
    )

    assert is_dataclass(scorecard_report)
    assert type(scorecard_report) is MarketCostDepthMemoryScorecardReport
    assert scorecard_report.generated_at == GENERATED_AT
    assert scorecard_report.config_version == (
        "research-market-cost-depth-memory-scorecard-report-v0"
    )
    assert scorecard_report.input_count == d("3.000000")
    assert scorecard_report.pass_count == d("1.000000")
    assert scorecard_report.watch_count == d("1.000000")
    assert scorecard_report.block_count == d("1.000000")
    assert scorecard_report.max_cost_rate == d("0.080000")
    assert scorecard_report.min_depth_score == d("0.300000")
    assert scorecard_report.min_memory_confidence_score == d("0.400000")
    assert scorecard_report.min_memory_recency_score == d("0.300000")
    assert scorecard_report.min_scorecard_score == d("0.350000")
    assert scorecard_report.status == "block"
    assert scorecard_report.summary_explanation == (
        "block: cost/depth/memory scorecard inputs are not sufficient for paper review"
    )
    assert scorecard_report.reason_codes == (
        "market_cost_depth_memory_scorecard_report_block",
        "market_cost_depth_memory_scorecard_cost_block",
        "market_cost_depth_memory_scorecard_depth_block",
        "market_cost_depth_memory_scorecard_confidence_block",
        "market_cost_depth_memory_scorecard_recency_block",
        "market_cost_depth_memory_scorecard_readiness_block",
        "market_cost_depth_memory_scorecard_cost_watch",
        "market_cost_depth_memory_scorecard_depth_watch",
        "market_cost_depth_memory_scorecard_confidence_watch",
        "market_cost_depth_memory_scorecard_recency_watch",
        "market_cost_depth_memory_scorecard_readiness_watch",
    )
    assert scorecard_report.paper_only is True
    assert scorecard_report.report_only is True
    assert scorecard_report.readonly is True
    assert len(scorecard_report.derived_validation_digest) == 64

    block_row, watch_row, pass_row = scorecard_report.rows
    assert tuple(row.status for row in scorecard_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert block_row.row_index == d("1.000000")
    assert block_row.scorecard_score == d("0.350000")
    assert block_row.status_explanation == (
        "block: cost/depth/memory scorecard inputs are not sufficient for paper review"
    )
    assert block_row.reason_codes == (
        "desk_escalation",
        "manual_memory_review",
        "market_cost_depth_memory_scorecard_cost_block",
        "market_cost_depth_memory_scorecard_depth_block",
        "market_cost_depth_memory_scorecard_confidence_block",
        "market_cost_depth_memory_scorecard_recency_block",
        "market_cost_depth_memory_scorecard_readiness_block",
    )
    assert watch_row.row_index == d("2.000000")
    assert watch_row.scorecard_score == d("0.650000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "manual_memory_review",
        "market_cost_depth_memory_scorecard_cost_watch",
        "market_cost_depth_memory_scorecard_depth_watch",
        "market_cost_depth_memory_scorecard_confidence_watch",
        "market_cost_depth_memory_scorecard_recency_watch",
        "market_cost_depth_memory_scorecard_readiness_watch",
    )
    assert pass_row.row_index == d("3.000000")
    assert pass_row.scorecard_score == d("0.900000")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "memory_coverage_complete",
        "market_cost_depth_memory_scorecard_ready",
    )

    assert scorecard_report.reason_code_counts[0] == (
        MarketCostDepthMemoryScorecardReasonCodeCount(
            reason_code="manual_memory_review",
            count=d("2.000000"),
            input_ratio=d("0.666667"),
        )
    )


def test_empty_report_blocks_without_review_inputs_and_keeps_hard_flags() -> None:
    scorecard_report = report()

    assert scorecard_report.input_count == ZERO
    assert scorecard_report.pass_count == ZERO
    assert scorecard_report.watch_count == ZERO
    assert scorecard_report.block_count == ZERO
    assert scorecard_report.max_cost_rate == ZERO
    assert scorecard_report.min_depth_score == ZERO
    assert scorecard_report.min_memory_confidence_score == ZERO
    assert scorecard_report.min_memory_recency_score == ZERO
    assert scorecard_report.min_scorecard_score == ZERO
    assert scorecard_report.status == "block"
    assert scorecard_report.summary_explanation == (
        "block: no cost/depth/memory scorecard inputs supplied for paper review"
    )
    assert scorecard_report.reason_codes == (
        "market_cost_depth_memory_scorecard_report_empty",
    )
    assert scorecard_report.reason_code_counts == ()
    assert scorecard_report.rows == ()

    populated = report(input_row())
    for value in (
        config(),
        input_row(),
        scorecard_report,
        populated,
        *populated.rows,
        *populated.reason_code_counts,
    ):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(
                (
                    "_count",
                    "_rate",
                    "_score",
                    "_ratio",
                ),
            ) or item.name == "row_index":
                assert type(item_value) is Decimal

    frozen = input_row()
    with pytest.raises(FrozenInstanceError):
        frozen.cost_rate = d("0.100000")  # type: ignore[misc]


def test_payload_is_deterministic_json_safe_and_validates_sha256_digest() -> None:
    scorecard_report = report(
        input_row(
            observed_at=datetime(
                2026,
                7,
                9,
                4,
                45,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            9,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    payload = research_market_cost_depth_memory_scorecard_report_payload(
        scorecard_report,
    )
    repeated_payload = research_market_cost_depth_memory_scorecard_report_payload(
        scorecard_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == repeated_payload
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["observed_at"] == "2026-07-09T11:45:00+00:00"
    assert payload["rows"][0]["cost_rate"] == "0.020000"
    assert payload["rows"][0]["scorecard_score"] == "0.900000"
    for blocked_fragment in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_url",
        "source_url",
        "raw_text",
        "dsn",
        "table",
        "token",
    ):
        assert blocked_fragment not in encoded.lower()
    assert not any(
        type(value) in (int, float, Decimal) for value in walk_payload_values(payload)
    )

    payload_without_digest = dict(payload)
    digest = payload_without_digest.pop("derived_validation_digest")
    assert digest == sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert scorecard_report.derived_validation_digest == digest


def test_validation_rejects_non_decimal_types_bad_thresholds_terms_and_flags() -> None:
    with pytest.raises(ValueError, match="cost_rate"):
        input_row(cost_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_rate"):
        input_row(cost_rate=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="memory_confidence_score"):
        input_row(memory_confidence_score=d("1.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            input_row(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("source_url_seen",))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("candidate_seen",))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("event_slug_seen",))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("market_question_seen",))
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("http_reference_seen",))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="min_pass_depth_score"):
        config(min_pass_depth_score=d("0.400000"))
    with pytest.raises(ValueError, match="max_watch_cost_rate"):
        config(max_watch_cost_rate=d("0.020000"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="custom")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report(input_row()), derived_validation_digest="0" * 64)


def test_report_rejects_impure_inputs_and_has_no_execution_surfaces() -> None:
    impure_input = input_row()
    object.__setattr__(impure_input, "readonly", False)
    with pytest.raises(ValueError, match="inputs"):
        build_research_market_cost_depth_memory_scorecard_report(
            (impure_input,),
            config=config(),
            generated_at=GENERATED_AT,
        )

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_cost_depth_memory_scorecard_report.py"
    )
    tree = ast.parse(module_path.read_text())
    banned_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "post",
        "put",
        "delete",
        term("w", "a", "l", "l", "e", "t"),
        term("a", "u", "t", "h"),
        term("o", "r", "d", "e", "r"),
        term("t", "r", "a", "d", "e"),
        "sign",
    }
    banned_import_roots = {
        "os",
        "socket",
        "sqlite3",
        "subprocess",
        "requests",
        "urllib",
        "httpx",
        "web3",
        "psycopg",
        "supabase",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            assert name.lower() not in banned_calls
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_import_roots
