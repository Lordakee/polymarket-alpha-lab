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

from polymarket_alpha_lab.research_market_cost_depth_probability_quorum_report import (
    DEFAULT_RESEARCH_MARKET_COST_DEPTH_PROBABILITY_QUORUM_CONFIG_VERSION,
    MarketCostDepthProbabilityQuorumConfig,
    MarketCostDepthProbabilityQuorumInput,
    MarketCostDepthProbabilityQuorumReasonCodeCount,
    MarketCostDepthProbabilityQuorumReport,
    build_research_market_cost_depth_probability_quorum_report,
    research_market_cost_depth_probability_quorum_report_payload,
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


def config(**overrides: object) -> MarketCostDepthProbabilityQuorumConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_COST_DEPTH_PROBABILITY_QUORUM_CONFIG_VERSION
        ),
        "max_pass_cost_rate": d("0.030000"),
        "max_watch_cost_rate": d("0.060000"),
        "min_pass_depth_score": d("0.700000"),
        "min_watch_depth_score": d("0.450000"),
        "min_pass_probability_quorum_score": d("0.800000"),
        "min_watch_probability_quorum_score": d("0.550000"),
        "max_pass_probability_dispersion_rate": d("0.080000"),
        "max_watch_probability_dispersion_rate": d("0.150000"),
        "pass_min_readiness_score": d("0.850000"),
    }
    values.update(overrides)
    return MarketCostDepthProbabilityQuorumConfig(**values)


def input_row(
    *,
    cost_rate: Decimal = d("0.020000"),
    depth_score: Decimal = d("0.900000"),
    probability_quorum_score: Decimal = d("0.900000"),
    probability_dispersion_rate: Decimal = d("0.040000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("manual_quorum_review",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketCostDepthProbabilityQuorumInput:
    return MarketCostDepthProbabilityQuorumInput(
        cost_rate=cost_rate,
        depth_score=depth_score,
        probability_quorum_score=probability_quorum_score,
        probability_dispersion_rate=probability_dispersion_rate,
        observed_at=observed_at,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: MarketCostDepthProbabilityQuorumInput,
    cfg: MarketCostDepthProbabilityQuorumConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketCostDepthProbabilityQuorumReport:
    return build_research_market_cost_depth_probability_quorum_report(
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


def test_builds_pass_watch_and_block_report_only_rows() -> None:
    quorum_report = report(
        input_row(
            cost_rate=d("0.080000"),
            depth_score=d("0.300000"),
            probability_quorum_score=d("0.400000"),
            probability_dispersion_rate=d("0.200000"),
            reason_codes=("manual_quorum_review", "desk_escalation"),
        ),
        input_row(
            cost_rate=d("0.040000"),
            depth_score=d("0.600000"),
            probability_quorum_score=d("0.700000"),
            probability_dispersion_rate=d("0.100000"),
        ),
        input_row(reason_codes=("quorum_complete",)),
    )

    assert is_dataclass(quorum_report)
    assert type(quorum_report) is MarketCostDepthProbabilityQuorumReport
    assert quorum_report.generated_at == GENERATED_AT
    assert quorum_report.config_version == (
        "research-market-cost-depth-probability-quorum-report-v0"
    )
    assert quorum_report.input_count == d("3.000000")
    assert quorum_report.pass_count == d("1.000000")
    assert quorum_report.watch_count == d("1.000000")
    assert quorum_report.block_count == d("1.000000")
    assert quorum_report.max_cost_rate == d("0.080000")
    assert quorum_report.min_depth_score == d("0.300000")
    assert quorum_report.min_probability_quorum_score == d("0.400000")
    assert quorum_report.max_probability_dispersion_rate == d("0.200000")
    assert quorum_report.min_readiness_score == d("0.350000")
    assert quorum_report.status == "block"
    assert quorum_report.summary_explanation == (
        "block: cost/depth/probability quorum inputs are not sufficient "
        "for paper review"
    )
    assert quorum_report.reason_codes == (
        "market_cost_depth_probability_quorum_report_block",
        "market_cost_depth_probability_quorum_cost_block",
        "market_cost_depth_probability_quorum_depth_block",
        "market_cost_depth_probability_quorum_quorum_block",
        "market_cost_depth_probability_quorum_dispersion_block",
        "market_cost_depth_probability_quorum_readiness_block",
        "market_cost_depth_probability_quorum_cost_watch",
        "market_cost_depth_probability_quorum_depth_watch",
        "market_cost_depth_probability_quorum_quorum_watch",
        "market_cost_depth_probability_quorum_dispersion_watch",
        "market_cost_depth_probability_quorum_readiness_watch",
    )
    assert quorum_report.paper_only is True
    assert quorum_report.report_only is True
    assert quorum_report.readonly is True
    assert len(quorum_report.derived_validation_digest) == 64

    block_row, watch_row, pass_row = quorum_report.rows
    assert tuple(row.status for row in quorum_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert block_row.row_index == d("1.000000")
    assert block_row.readiness_score == d("0.350000")
    assert block_row.status_explanation == (
        "block: cost/depth/probability quorum inputs are not sufficient "
        "for paper review"
    )
    assert block_row.reason_codes == (
        "desk_escalation",
        "manual_quorum_review",
        "market_cost_depth_probability_quorum_cost_block",
        "market_cost_depth_probability_quorum_depth_block",
        "market_cost_depth_probability_quorum_quorum_block",
        "market_cost_depth_probability_quorum_dispersion_block",
        "market_cost_depth_probability_quorum_readiness_block",
    )
    assert watch_row.row_index == d("2.000000")
    assert watch_row.readiness_score == d("0.650000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "manual_quorum_review",
        "market_cost_depth_probability_quorum_cost_watch",
        "market_cost_depth_probability_quorum_depth_watch",
        "market_cost_depth_probability_quorum_quorum_watch",
        "market_cost_depth_probability_quorum_dispersion_watch",
        "market_cost_depth_probability_quorum_readiness_watch",
    )
    assert pass_row.row_index == d("3.000000")
    assert pass_row.readiness_score == d("0.900000")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "quorum_complete",
        "market_cost_depth_probability_quorum_ready",
    )

    assert quorum_report.reason_code_counts[0] == (
        MarketCostDepthProbabilityQuorumReasonCodeCount(
            reason_code="manual_quorum_review",
            count=d("2.000000"),
            input_ratio=d("0.666667"),
        )
    )


def test_empty_report_blocks_without_review_inputs_and_keeps_hard_flags() -> None:
    quorum_report = report()

    assert quorum_report.input_count == ZERO
    assert quorum_report.pass_count == ZERO
    assert quorum_report.watch_count == ZERO
    assert quorum_report.block_count == ZERO
    assert quorum_report.max_cost_rate == ZERO
    assert quorum_report.min_depth_score == ZERO
    assert quorum_report.min_probability_quorum_score == ZERO
    assert quorum_report.max_probability_dispersion_rate == ZERO
    assert quorum_report.min_readiness_score == ZERO
    assert quorum_report.status == "block"
    assert quorum_report.summary_explanation == (
        "block: no market cost/depth/probability quorum inputs supplied "
        "for paper review"
    )
    assert quorum_report.reason_codes == (
        "market_cost_depth_probability_quorum_report_empty",
    )
    assert quorum_report.reason_code_counts == ()
    assert quorum_report.rows == ()

    populated = report(input_row())
    for value in (
        quorum_report,
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


def test_payload_is_deterministic_json_safe_and_does_not_leak_raw_surfaces() -> None:
    quorum_report = report(
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

    payload = research_market_cost_depth_probability_quorum_report_payload(quorum_report)
    repeated_payload = research_market_cost_depth_probability_quorum_report_payload(
        quorum_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == repeated_payload
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["observed_at"] == "2026-07-09T11:45:00+00:00"
    assert payload["rows"][0]["cost_rate"] == "0.020000"
    assert payload["rows"][0]["readiness_score"] == "0.900000"
    for blocked_fragment in (
        "market_id",
        "candidate_id",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
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
    assert quorum_report.derived_validation_digest == digest


def test_validation_rejects_non_decimal_types_bad_thresholds_terms_and_flags() -> None:
    with pytest.raises(ValueError, match="cost_rate"):
        input_row(cost_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_rate"):
        input_row(cost_rate=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="depth_score"):
        input_row(depth_score=d("1.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            input_row(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(reason_codes=("source_url_seen",))
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


def test_report_rejects_non_generated_row_indices_before_payload() -> None:
    quorum_report = report(input_row())
    bad_row = replace(quorum_report.rows[0], row_index=d("99.000000"))

    with pytest.raises(ValueError, match="row_index"):
        replace(quorum_report, rows=(bad_row,), derived_validation_digest="")


def test_report_rejects_impure_inputs_and_does_not_expose_execution_surfaces() -> None:
    impure_input = input_row()
    object.__setattr__(impure_input, "readonly", False)
    with pytest.raises(ValueError, match="inputs"):
        build_research_market_cost_depth_probability_quorum_report(
            (impure_input,),
            config=config(),
            generated_at=GENERATED_AT,
        )

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_cost_depth_probability_quorum_report.py"
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
        "wallet",
        "auth",
        "order",
        "trade",
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
