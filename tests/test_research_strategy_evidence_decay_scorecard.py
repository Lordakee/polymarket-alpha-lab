from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_evidence_decay_scorecard import (
    DEFAULT_RESEARCH_STRATEGY_EVIDENCE_DECAY_SCORECARD_CONFIG_VERSION,
    ResearchStrategyEvidenceDecayInputRow,
    ResearchStrategyEvidenceDecayReasonCodeCount,
    ResearchStrategyEvidenceDecayScoreRow,
    ResearchStrategyEvidenceDecayScorecardConfig,
    ResearchStrategyEvidenceDecayScorecardReport,
    build_research_strategy_evidence_decay_scorecard,
    research_strategy_evidence_decay_scorecard_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path("src/polymarket_alpha_lab/research_strategy_evidence_decay_scorecard.py")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyEvidenceDecayScorecardConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_STRATEGY_EVIDENCE_DECAY_SCORECARD_CONFIG_VERSION,
        "fresh_evidence_max_age_seconds": d("3600.000000"),
        "stale_evidence_max_age_seconds": d("86400.000000"),
        "target_refresh_interval_seconds": d("21600.000000"),
        "stale_refresh_interval_seconds": d("86400.000000"),
        "conflict_growth_watch_threshold": d("0.100000"),
        "conflict_growth_block_threshold": d("0.500000"),
        "settlement_watch_window_seconds": d("172800.000000"),
        "settlement_block_window_seconds": d("21600.000000"),
        "pass_decay_score": d("0.700000"),
        "watch_decay_score": d("0.400000"),
        "evidence_age_weight": d("0.300000"),
        "refresh_frequency_weight": d("0.250000"),
        "conflict_growth_weight": d("0.250000"),
        "settlement_risk_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchStrategyEvidenceDecayScorecardConfig(**values)


def input_row(
    strategy_ref: str = "strategy-alpha",
    *,
    evidence_observed_at: datetime | None = None,
    last_refreshed_at: datetime | None = None,
    previous_refreshed_at: datetime | None = None,
    conflict_count_previous: Decimal = d("0.000000"),
    conflict_count_current: Decimal = d("0.000000"),
    settlement_at: datetime | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyEvidenceDecayInputRow:
    return ResearchStrategyEvidenceDecayInputRow(
        strategy_ref=strategy_ref,
        evidence_observed_at=evidence_observed_at
        or GENERATED_AT - timedelta(minutes=30),
        last_refreshed_at=last_refreshed_at or GENERATED_AT - timedelta(minutes=30),
        previous_refreshed_at=previous_refreshed_at or GENERATED_AT - timedelta(hours=4),
        conflict_count_previous=conflict_count_previous,
        conflict_count_current=conflict_count_current,
        settlement_at=settlement_at or GENERATED_AT + timedelta(days=7),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategyEvidenceDecayScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyEvidenceDecayScorecardReport:
    return build_research_strategy_evidence_decay_scorecard(
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
        if field.name.endswith(("_count", "_ratio", "_score", "_seconds")):
            assert type(item) is Decimal


def test_scorecard_reduces_pass_watch_and_block_rows_deterministically() -> None:
    summary = report(
        (
            input_row("strategy-pass"),
            input_row(
                "strategy-watch",
                evidence_observed_at=GENERATED_AT - timedelta(hours=6),
                last_refreshed_at=GENERATED_AT - timedelta(hours=6),
                previous_refreshed_at=GENERATED_AT - timedelta(hours=18),
                conflict_count_previous=d("10.000000"),
                conflict_count_current=d("12.000000"),
                settlement_at=GENERATED_AT + timedelta(hours=24),
            ),
            input_row(
                "strategy-block",
                evidence_observed_at=GENERATED_AT - timedelta(hours=30),
                last_refreshed_at=GENERATED_AT - timedelta(hours=30),
                previous_refreshed_at=GENERATED_AT - timedelta(hours=48),
                conflict_count_previous=d("2.000000"),
                conflict_count_current=d("4.000000"),
                settlement_at=GENERATED_AT + timedelta(hours=3),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == DEFAULT_RESEARCH_STRATEGY_EVIDENCE_DECAY_SCORECARD_CONFIG_VERSION
    assert summary.scorecard_status == "block"
    assert summary.row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_decay_score == d("0.533333")
    assert summary.max_evidence_age_seconds == d("108000.000000")
    assert summary.max_refresh_lag_seconds == d("108000.000000")
    assert summary.max_conflict_growth_ratio == d("1.000000")
    assert summary.min_settlement_seconds_remaining == d("10800.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked = summary.rows[0]
    assert type(blocked) is ResearchStrategyEvidenceDecayScoreRow
    assert blocked.evidence_age_seconds == d("108000.000000")
    assert blocked.refresh_interval_seconds == d("64800.000000")
    assert blocked.refresh_lag_seconds == d("108000.000000")
    assert blocked.effective_refresh_seconds == d("108000.000000")
    assert blocked.conflict_delta_count == d("2.000000")
    assert blocked.conflict_growth_ratio == d("1.000000")
    assert blocked.settlement_seconds_remaining == d("10800.000000")
    assert blocked.decay_score == d("0.000000")
    assert blocked.reason_codes == (
        "research_strategy_evidence_decay_scorecard_stale_evidence",
        "research_strategy_evidence_decay_scorecard_stale_refresh",
        "research_strategy_evidence_decay_scorecard_conflict_growth_block",
        "research_strategy_evidence_decay_scorecard_settlement_block_window",
        "research_strategy_evidence_decay_scorecard_score_block",
    )

    watched = summary.rows[1]
    assert watched.evidence_age_seconds == d("21600.000000")
    assert watched.refresh_interval_seconds == d("43200.000000")
    assert watched.refresh_lag_seconds == d("21600.000000")
    assert watched.effective_refresh_seconds == d("43200.000000")
    assert watched.conflict_delta_count == d("2.000000")
    assert watched.conflict_growth_ratio == d("0.200000")
    assert watched.settlement_seconds_remaining == d("86400.000000")
    assert watched.evidence_age_score == d("0.750000")
    assert watched.refresh_frequency_score == d("0.500000")
    assert watched.conflict_growth_score == d("0.600000")
    assert watched.settlement_risk_score == d("0.500000")
    assert watched.decay_score == d("0.600000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "research_strategy_evidence_decay_scorecard_aging_evidence",
        "research_strategy_evidence_decay_scorecard_slow_refresh",
        "research_strategy_evidence_decay_scorecard_conflict_growth_watch",
        "research_strategy_evidence_decay_scorecard_settlement_watch_window",
        "research_strategy_evidence_decay_scorecard_score_watch",
    )

    passed = summary.rows[2]
    assert passed.decay_score == d("1.000000")
    assert passed.status == "pass"
    assert passed.reason_codes == (
        "research_strategy_evidence_decay_scorecard_pass",
    )


def test_empty_scorecard_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.scorecard_status == "block"
    assert summary.row_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_decay_score == ZERO
    assert summary.max_evidence_age_seconds == ZERO
    assert summary.max_refresh_lag_seconds == ZERO
    assert summary.max_conflict_growth_ratio == ZERO
    assert summary.min_settlement_seconds_remaining == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchStrategyEvidenceDecayReasonCodeCount(
            reason_code="research_strategy_evidence_decay_scorecard_no_inputs",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "research_strategy_evidence_decay_scorecard_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_scorecard_payload_uses_decimal_strings_and_redacts_private_refs() -> None:
    summary = report(
        (
            input_row("raw-market-alpha?token=hidden&source=private_table"),
        ),
    )
    payload = research_strategy_evidence_decay_scorecard_payload(summary)
    encoded = json.dumps(payload, sort_keys=True)
    public_text = repr(payload).lower()
    dataclass_text = repr(asdict(summary)).lower()

    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["decay_score"] == "1.000000"
    assert payload["rows"][0]["redacted_strategy_ref"].startswith("sha256:")
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in ("raw-market-alpha", "hidden", "source", "market", "table", "token"):
        assert leaked not in public_text
        assert leaked not in dataclass_text


def test_scorecard_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(ResearchStrategyEvidenceDecayScorecardConfig)
    assert is_dataclass(ResearchStrategyEvidenceDecayInputRow)
    assert is_dataclass(ResearchStrategyEvidenceDecayScoreRow)
    assert is_dataclass(ResearchStrategyEvidenceDecayReasonCodeCount)
    assert is_dataclass(ResearchStrategyEvidenceDecayScorecardReport)

    cfg = config()
    row = input_row()
    summary = report((row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.conflict_count_current = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].decay_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.scorecard_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("research-strategy-evidence-decay-scorecard-v0"))
    with pytest.raises(ValueError, match="fresh_evidence_max_age_seconds"):
        config(fresh_evidence_max_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_evidence_max_age_seconds"):
        config(
            fresh_evidence_max_age_seconds=d("86400.000000"),
            stale_evidence_max_age_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="conflict_growth_watch_threshold"):
        config(conflict_growth_watch_threshold=d("0.600000"))
    with pytest.raises(ValueError, match="settlement_block_window_seconds"):
        config(settlement_block_window_seconds=d("172801.000000"))
    with pytest.raises(ValueError, match="pass_decay_score"):
        config(pass_decay_score=d("0.300000"))
    with pytest.raises(ValueError, match="evidence_age_weight"):
        config(evidence_age_weight=d("0.100000"))
    with pytest.raises(ValueError, match="refresh_frequency_weight"):
        config(refresh_frequency_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="strategy_ref"):
        input_row(_StringSubclass("strategy-alpha"))
    with pytest.raises(ValueError, match="strategy_ref"):
        input_row(" strategy-alpha")
    with pytest.raises(ValueError, match="evidence_observed_at"):
        input_row(evidence_observed_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="last_refreshed_at"):
        input_row(last_refreshed_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="conflict_count_current"):
        input_row(conflict_count_current=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="conflict_count_previous"):
        input_row(conflict_count_previous=Decimal("NaN"))
    with pytest.raises(ValueError, match="conflict_count_current"):
        input_row(conflict_count_previous=d("2.000000"), conflict_count_current=d("1.000000"))
    with pytest.raises(ValueError, match="previous_refreshed_at"):
        input_row(
            previous_refreshed_at=GENERATED_AT - timedelta(hours=1),
            last_refreshed_at=GENERATED_AT - timedelta(hours=2),
        )
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_research_strategy_evidence_decay_scorecard(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_strategy_evidence_decay_scorecard(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        report((input_row(evidence_observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="last_refreshed_at"):
        report((input_row(last_refreshed_at=GENERATED_AT + timedelta(seconds=1)),))


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    ready_summary = report((input_row(),))
    ready = ready_summary.rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "research_strategy_evidence_decay_scorecard_pass",
                "research_strategy_evidence_decay_scorecard_score_watch",
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(ready, status="block")
    with pytest.raises(ValueError, match="decay_score"):
        replace(ready, decay_score=d("0.000000"))
    with pytest.raises(ValueError, match="redacted_strategy_ref"):
        replace(ready, redacted_strategy_ref="raw-market-alpha?token=hidden")

    with pytest.raises(ValueError, match="pass_count"):
        replace(ready_summary, pass_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(ready_summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(ready_summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(ready_summary, readonly=False)
    with pytest.raises(ValueError, match="rows"):
        unordered = report((input_row("strategy-z"), input_row("strategy-a")))
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    source_row = input_row()
    summary = report((source_row,))

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_store_execution_or_recommendation_surfaces() -> None:
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
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "advice",
        "source",
        "market",
        "dsn",
        "table",
        "token",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "network",
        "database",
        "durable",
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
