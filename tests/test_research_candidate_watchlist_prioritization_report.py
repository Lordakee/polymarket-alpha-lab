from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_candidate_watchlist_prioritization_report import (
    DEFAULT_RESEARCH_CANDIDATE_WATCHLIST_PRIORITIZATION_CONFIG_VERSION,
    ResearchCandidateWatchlistPrioritizationConfig,
    ResearchCandidateWatchlistPrioritizationInputRow,
    ResearchCandidateWatchlistPrioritizationReasonCodeCount,
    ResearchCandidateWatchlistPrioritizationReport,
    ResearchCandidateWatchlistPrioritizationRow,
    build_research_candidate_watchlist_prioritization_report,
    research_candidate_watchlist_prioritization_digest_payload,
    research_candidate_watchlist_prioritization_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_candidate_watchlist_prioritization_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchCandidateWatchlistPrioritizationConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_CANDIDATE_WATCHLIST_PRIORITIZATION_CONFIG_VERSION
        ),
        "information_gap_watch_threshold": d("0.350000"),
        "information_gap_block_threshold": d("0.750000"),
        "calibration_drift_watch_threshold": d("0.100000"),
        "calibration_drift_block_threshold": d("0.250000"),
        "liquidity_cost_watch_threshold": d("0.030000"),
        "liquidity_cost_block_threshold": d("0.120000"),
        "min_team_coverage_count": d("2"),
        "information_gap_weight": d("0.400000"),
        "calibration_drift_weight": d("0.250000"),
        "liquidity_cost_weight": d("0.200000"),
        "team_coverage_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchCandidateWatchlistPrioritizationConfig(**values)


def input_row(
    private_candidate_reference: str = (
        "raw-candidate-id:alpha|market_id=hidden|market_slug=hidden|"
        "question=hidden|source_url=https://private.example/ref?token=hidden"
    ),
    *,
    public_research_bucket: str = "macro_calendar",
    information_gap_score: Decimal = d("0.100000"),
    calibration_drift_score: Decimal = d("0.030000"),
    liquidity_cost_score: Decimal = d("0.010000"),
    team_coverage_count: Decimal = d("3"),
    observed_at: datetime | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchCandidateWatchlistPrioritizationInputRow:
    return ResearchCandidateWatchlistPrioritizationInputRow(
        private_candidate_reference=private_candidate_reference,
        public_research_bucket=public_research_bucket,
        information_gap_score=information_gap_score,
        calibration_drift_score=calibration_drift_score,
        liquidity_cost_score=liquidity_cost_score,
        team_coverage_count=team_coverage_count,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchCandidateWatchlistPrioritizationConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchCandidateWatchlistPrioritizationReport:
    return build_research_candidate_watchlist_prioritization_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_rank", "_score", "_threshold", "_weight")):
            assert type(item) is Decimal


def test_watchlist_prioritization_reduces_pass_watch_block_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "raw-candidate-id:ready|market_id=ready|question=ready",
                public_research_bucket="weather_alerts",
            ),
            input_row(
                "raw-candidate-id:watch|market_slug=watch|source_text=hidden",
                public_research_bucket="policy_calendar",
                information_gap_score=d("0.500000"),
                calibration_drift_score=d("0.050000"),
                liquidity_cost_score=d("0.020000"),
                team_coverage_count=d("2"),
            ),
            input_row(
                "raw-candidate-id:block|source_url=https://private.example/block",
                public_research_bucket="macro_calendar",
                information_gap_score=d("0.700000"),
                calibration_drift_score=d("0.270000"),
                liquidity_cost_score=d("0.140000"),
                team_coverage_count=d("0"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_CANDIDATE_WATCHLIST_PRIORITIZATION_CONFIG_VERSION
    )
    assert summary.status == "block"
    assert summary.next_step == (
        "block_report_only_research_candidate_watchlist_prioritization"
    )
    assert summary.candidate_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_priority_score == d("0.263833")
    assert summary.max_priority_score == d("0.525500")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.status, row.public_research_bucket) for row in summary.rows) == (
        ("block", "macro_calendar"),
        ("watch", "policy_calendar"),
        ("pass", "weather_alerts"),
    )

    blocked = summary.rows[0]
    assert blocked.priority_rank == d("1.000000")
    assert blocked.priority_score == d("0.525500")
    assert blocked.team_coverage_gap_score == d("1.000000")
    assert blocked.status == "block"
    assert blocked.public_candidate_ref.startswith("sha256:")
    assert blocked.reason_codes == (
        "research_candidate_watchlist_prioritization_calibration_drift_block",
        "research_candidate_watchlist_prioritization_liquidity_cost_block",
        "research_candidate_watchlist_prioritization_team_coverage_block",
        "research_candidate_watchlist_prioritization_information_gap_watch",
    )

    watch = summary.rows[1]
    assert watch.priority_rank == d("2.000000")
    assert watch.priority_score == d("0.216500")
    assert watch.reason_codes == (
        "research_candidate_watchlist_prioritization_information_gap_watch",
    )

    ready = summary.rows[2]
    assert ready.priority_rank == d("3.000000")
    assert ready.priority_score == d("0.049500")
    assert ready.status == "pass"
    assert ready.reason_codes == (
        "research_candidate_watchlist_prioritization_pass",
    )

    assert summary.reason_code_counts == (
        ResearchCandidateWatchlistPrioritizationReasonCodeCount(
            reason_code=(
                "research_candidate_watchlist_prioritization_calibration_drift_block"
            ),
            count=d("1.000000"),
            candidate_ratio=d("0.333333"),
        ),
        ResearchCandidateWatchlistPrioritizationReasonCodeCount(
            reason_code="research_candidate_watchlist_prioritization_liquidity_cost_block",
            count=d("1.000000"),
            candidate_ratio=d("0.333333"),
        ),
        ResearchCandidateWatchlistPrioritizationReasonCodeCount(
            reason_code="research_candidate_watchlist_prioritization_team_coverage_block",
            count=d("1.000000"),
            candidate_ratio=d("0.333333"),
        ),
        ResearchCandidateWatchlistPrioritizationReasonCodeCount(
            reason_code="research_candidate_watchlist_prioritization_information_gap_watch",
            count=d("2.000000"),
            candidate_ratio=d("0.666667"),
        ),
        ResearchCandidateWatchlistPrioritizationReasonCodeCount(
            reason_code="research_candidate_watchlist_prioritization_pass",
            count=d("1.000000"),
            candidate_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for value in (
        "raw-candidate-id",
        "market_id",
        "market_slug",
        "question=hidden",
        "source_url",
        "source_text",
        "private.example",
        "token=hidden",
    ):
        assert value not in public


def test_empty_watchlist_prioritization_is_blocked_report_only() -> None:
    summary = report(())

    assert summary.status == "block"
    assert summary.next_step == (
        "block_report_only_research_candidate_watchlist_prioritization"
    )
    assert summary.candidate_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_priority_score == ZERO
    assert summary.max_priority_score == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchCandidateWatchlistPrioritizationReasonCodeCount(
            reason_code="research_candidate_watchlist_prioritization_no_inputs",
            count=d("1.000000"),
            candidate_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "research_candidate_watchlist_prioritization_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_and_digest_are_deterministic_public_and_consistent() -> None:
    watch_input = input_row(
        "raw-candidate-id:watch|market_slug=secret|source_ref=hidden",
        public_research_bucket="policy_calendar",
        information_gap_score=d("0.500000"),
        team_coverage_count=d("2"),
    )
    block_input = input_row(
        "raw-candidate-id:block|dsn=hidden|table=private|token=secret",
        public_research_bucket="macro_calendar",
        information_gap_score=d("0.700000"),
        calibration_drift_score=d("0.270000"),
        liquidity_cost_score=d("0.140000"),
        team_coverage_count=d("0"),
    )
    summary_one = report((watch_input, block_input))
    summary_two = report((block_input, watch_input))

    payload_one = research_candidate_watchlist_prioritization_report_payload(summary_one)
    payload_two = research_candidate_watchlist_prioritization_report_payload(summary_one)
    digest_one = research_candidate_watchlist_prioritization_digest_payload(summary_one)
    digest_two = research_candidate_watchlist_prioritization_digest_payload(summary_one)

    assert payload_one == payload_two
    assert digest_one == digest_two
    assert research_candidate_watchlist_prioritization_report_payload(
        summary_two,
    ) == payload_one
    json.dumps(payload_one, sort_keys=True)
    json.dumps(digest_one, sort_keys=True)

    assert payload_one["candidate_count"] == "2.000000"
    assert payload_one["average_priority_score"] == "0.367500"
    assert payload_one["rows"][0]["priority_score"] == "0.525500"
    assert payload_one["rows"][0]["paper_only"] is True
    assert payload_one["paper_only"] is True
    assert payload_one["report_only"] is True
    assert payload_one["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload_one))

    assert digest_one["status"] == payload_one["status"]
    assert digest_one["candidate_count"] == payload_one["candidate_count"]
    assert digest_one["pass_count"] == payload_one["pass_count"]
    assert digest_one["watch_count"] == payload_one["watch_count"]
    assert digest_one["block_count"] == payload_one["block_count"]
    assert digest_one["reason_codes"] == payload_one["reason_codes"]
    assert digest_one["rows"] == [
        {
            "priority_rank": row["priority_rank"],
            "public_candidate_ref": row["public_candidate_ref"],
            "public_research_bucket": row["public_research_bucket"],
            "priority_score": row["priority_score"],
            "status": row["status"],
            "reason_codes": row["reason_codes"],
        }
        for row in payload_one["rows"]
    ]

    public = repr(payload_one).lower() + repr(digest_one).lower()
    for value in (
        "raw-candidate-id",
        "market_slug",
        "source_ref",
        "dsn",
        "table",
        "token",
        "secret",
        "private",
    ):
        assert value not in public


def test_contracts_reject_non_decimal_types_and_public_leaks() -> None:
    assert is_dataclass(ResearchCandidateWatchlistPrioritizationConfig)
    assert is_dataclass(ResearchCandidateWatchlistPrioritizationInputRow)
    assert is_dataclass(ResearchCandidateWatchlistPrioritizationRow)
    assert is_dataclass(ResearchCandidateWatchlistPrioritizationReasonCodeCount)
    assert is_dataclass(ResearchCandidateWatchlistPrioritizationReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.information_gap_score = d("0.900000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].priority_score = d("0.900000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.candidate_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("watchlist-v0"))
    with pytest.raises(ValueError, match="information_gap_watch_threshold"):
        config(information_gap_watch_threshold=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="information_gap_block_threshold"):
        config(
            information_gap_watch_threshold=d("0.800000"),
            information_gap_block_threshold=d("0.750000"),
        )
    with pytest.raises(ValueError, match="calibration_drift_score"):
        input_row(calibration_drift_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="information_gap_score"):
        input_row(information_gap_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_cost_score"):
        input_row(liquidity_cost_score=d("NaN"))
    with pytest.raises(ValueError, match="team_coverage_count"):
        input_row(team_coverage_count=d("1.5"))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="public_research_bucket"):
        input_row(public_research_bucket="contains market question")
    with pytest.raises(ValueError, match="public_research_bucket"):
        input_row(public_research_bucket="buy_sell_signal")
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_candidate_watchlist_prioritization_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_candidate_watchlist_prioritization_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_hard_flags_and_manual_drift_are_rejected() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "research_candidate_watchlist_prioritization_pass",
                "research_candidate_watchlist_prioritization_information_gap_watch",
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(ready, status="watch")
    with pytest.raises(ValueError, match="priority_score"):
        replace(ready, priority_score=d("0.999999"))
    with pytest.raises(ValueError, match="public_candidate_ref"):
        replace(ready, public_candidate_ref="raw-candidate-id:leak")
    with pytest.raises(ValueError, match="public_research_bucket"):
        replace(ready, public_research_bucket="recommendation_signal")

    summary = report(
        (
            input_row("raw-candidate-id:a", public_research_bucket="bucket_a"),
            input_row(
                "raw-candidate-id:b",
                public_research_bucket="bucket_b",
                information_gap_score=d("0.500000"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="pass_count"):
        replace(summary, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)


def test_public_numeric_fields_are_decimals() -> None:
    source_row = input_row()
    summary = report((source_row,))

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_store_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "live_trading",
        "wallet",
        "order",
        "private_key",
        "api_key",
        "dsn",
        "token",
        "market_id",
        "market_slug",
        "source_ref",
        "source_url",
        "source_text",
        "position",
        "buy",
        "sell",
        "recommendation",
        "requests",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered
