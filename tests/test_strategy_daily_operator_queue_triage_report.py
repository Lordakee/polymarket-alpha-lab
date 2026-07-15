from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.strategy_daily_operator_queue_triage_report import (
    DEFAULT_STRATEGY_DAILY_OPERATOR_QUEUE_TRIAGE_REPORT_CONFIG_VERSION,
    StrategyDailyOperatorQueueTriageConfig,
    StrategyDailyOperatorQueueTriageInput,
    StrategyDailyOperatorQueueTriageReasonCodeCount,
    StrategyDailyOperatorQueueTriageReport,
    StrategyDailyOperatorQueueTriageRow,
    build_strategy_daily_operator_queue_triage_report,
    strategy_daily_operator_queue_triage_report_digest,
    strategy_daily_operator_queue_triage_report_payload,
)


GENERATED_AT = datetime(2026, 7, 12, 9, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/strategy_daily_operator_queue_triage_report.py",
)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyDailyOperatorQueueTriageConfig:
    values = {
        "config_version": (
            DEFAULT_STRATEGY_DAILY_OPERATOR_QUEUE_TRIAGE_REPORT_CONFIG_VERSION
        ),
        "watch_urgency": d("0.500000"),
        "block_urgency": d("0.850000"),
        "watch_research_gap_count": d("1.000000"),
        "block_research_gap_count": d("3.000000"),
        "watch_manual_review_age_hours": d("12.000000"),
        "block_manual_review_age_hours": d("36.000000"),
    }
    values.update(overrides)
    return StrategyDailyOperatorQueueTriageConfig(**values)


def item(
    operator_queue_key: str = "operator-alpha",
    *,
    status: str = "pass",
    urgency: Decimal = d("0.100000"),
    research_gap_count: Decimal = ZERO,
    manual_review_age_hours: Decimal = d("1.000000"),
    source_refresh_due: bool = False,
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> StrategyDailyOperatorQueueTriageInput:
    return StrategyDailyOperatorQueueTriageInput(
        operator_queue_key=operator_queue_key,
        status=status,
        urgency=urgency,
        research_gap_count=research_gap_count,
        manual_review_age_hours=manual_review_age_hours,
        source_refresh_due=source_refresh_due,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: StrategyDailyOperatorQueueTriageInput,
    cfg: StrategyDailyOperatorQueueTriageConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyDailyOperatorQueueTriageReport:
    return build_strategy_daily_operator_queue_triage_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_float(item_value)
    if isinstance(value, list):
        for item_value in value:
            assert_no_float(item_value)


def test_pass_report_uses_decimal_payload_strings_and_digest() -> None:
    triage = report(item("operator-pass"))

    assert is_dataclass(triage)
    assert triage.generated_at == GENERATED_AT
    assert triage.config_version == (
        DEFAULT_STRATEGY_DAILY_OPERATOR_QUEUE_TRIAGE_REPORT_CONFIG_VERSION
    )
    assert triage.queue_count == d("1.000000")
    assert triage.pass_count == d("1.000000")
    assert triage.watch_count == ZERO
    assert triage.blocked_count == ZERO
    assert triage.status == "pass"
    assert triage.reason_codes == ("strategy_daily_operator_queue_triage_clear",)
    assert triage.paper_only is True
    assert triage.report_only is True
    assert triage.readonly is True

    row = triage.rows[0]
    assert row.triage_rank == d("1.000000")
    assert row.operator_queue_key == "operator-pass"
    assert row.status == "pass"
    assert row.triage_bucket == "pass"
    assert row.triage_score == d("0.130000")
    assert row.manual_next_step == "continue_daily_monitoring"
    assert row.reason_codes == ("triage_clear",)

    payload = strategy_daily_operator_queue_triage_report_payload(triage)
    assert payload["queue_count"] == "1.000000"
    assert payload["rows"][0]["triage_score"] == "0.130000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["public_digest"] == (
        strategy_daily_operator_queue_triage_report_digest(triage)
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)
    json.dumps(payload, sort_keys=True)


def test_rows_sort_by_blocked_watch_pass_then_operational_urgency() -> None:
    triage = report(
        item(
            "watch-low",
            status="watch",
            urgency=d("0.600000"),
            research_gap_count=d("1.000000"),
        ),
        item("pass-high", urgency=d("0.950000")),
        item(
            "blocked-lower-gap",
            status="blocked",
            urgency=d("0.700000"),
            research_gap_count=d("2.000000"),
            manual_review_age_hours=d("50.000000"),
        ),
        item(
            "blocked-top",
            status="blocked",
            urgency=d("0.900000"),
            research_gap_count=d("4.000000"),
            manual_review_age_hours=d("48.000000"),
            source_refresh_due=True,
        ),
        item(
            "watch-refresh",
            status="watch",
            urgency=d("0.600000"),
            research_gap_count=d("1.000000"),
            manual_review_age_hours=d("24.000000"),
            source_refresh_due=True,
        ),
    )

    assert triage.status == "blocked"
    assert triage.pass_count == d("1.000000")
    assert triage.watch_count == d("2.000000")
    assert triage.blocked_count == d("2.000000")
    assert triage.source_refresh_due_count == d("2.000000")
    assert triage.research_gap_queue_count == d("4.000000")
    assert tuple(row.operator_queue_key for row in triage.rows) == (
        "blocked-top",
        "blocked-lower-gap",
        "watch-refresh",
        "watch-low",
        "pass-high",
    )
    assert tuple(row.triage_rank for row in triage.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
        d("4.000000"),
        d("5.000000"),
    )
    assert triage.rows[0].triage_bucket == "blocked"
    assert triage.rows[0].manual_next_step == "assign_research_owner_before_review"
    assert triage.rows[0].reason_codes == (
        "input_status_blocked",
        "manual_review_age_blocked",
        "research_gap_count_blocked",
        "source_refresh_due",
        "urgency_blocked",
    )
    assert triage.rows[2].triage_bucket == "watch"
    assert triage.rows[2].manual_next_step == "refresh_sources_then_recheck"
    assert triage.rows[2].reason_codes == (
        "input_status_watch",
        "manual_review_age_watch",
        "research_gap_count_watch",
        "source_refresh_due",
        "urgency_watch",
    )


def test_manual_next_step_prioritizes_research_gaps_then_source_age_then_review_age() -> None:
    triage = report(
        item(
            "gap-first",
            status="blocked",
            urgency=d("0.900000"),
            research_gap_count=d("3.000000"),
            source_refresh_due=True,
            manual_review_age_hours=d("40.000000"),
        ),
        item(
            "refresh-first",
            status="watch",
            urgency=d("0.550000"),
            research_gap_count=ZERO,
            source_refresh_due=True,
            manual_review_age_hours=d("18.000000"),
        ),
        item(
            "age-first",
            status="watch",
            urgency=d("0.550000"),
            manual_review_age_hours=d("20.000000"),
        ),
    )

    steps = {row.operator_queue_key: row.manual_next_step for row in triage.rows}

    assert steps == {
        "gap-first": "assign_research_owner_before_review",
        "refresh-first": "refresh_sources_then_recheck",
        "age-first": "complete_manual_review_today",
    }


def test_empty_inputs_blocked_with_no_inputs_reason_count() -> None:
    triage = report()

    assert triage.status == "blocked"
    assert triage.queue_count == ZERO
    assert triage.pass_count == ZERO
    assert triage.watch_count == ZERO
    assert triage.blocked_count == ZERO
    assert triage.mean_triage_score == ZERO
    assert triage.max_triage_score == ZERO
    assert triage.reason_codes == (
        "strategy_daily_operator_queue_triage_no_inputs",
    )
    assert triage.reason_code_counts == (
        StrategyDailyOperatorQueueTriageReasonCodeCount(
            reason_code="strategy_daily_operator_queue_triage_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert triage.rows == ()


def test_decimal_type_rejection_and_public_numerics_are_decimal_only() -> None:
    triage = report(item("operator-decimal"))

    with pytest.raises(ValueError, match="watch_urgency"):
        config(watch_urgency=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="urgency"):
        item(urgency=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="manual_review_age_hours"):
        item(manual_review_age_hours=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="research_gap_count"):
        item(research_gap_count=d("-1.000000"))
    with pytest.raises(ValueError, match="source_refresh_due"):
        item(source_refresh_due=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="status"):
        item(status="block")
    with pytest.raises(ValueError, match="reason_codes"):
        item(reason_codes=["manual_review"])  # type: ignore[arg-type]

    for public_value in (triage, *triage.rows, *triage.reason_code_counts):
        for field in fields(public_value):
            value = getattr(public_value, field.name)
            if field.name in {"paper_only", "report_only", "readonly", "source_refresh_due"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name
    for field_name in (
        "queue_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "mean_triage_score",
        "max_triage_score",
    ):
        assert type(getattr(triage, field_name)) is Decimal


def test_public_leak_rejection_and_hard_flags_revalidated() -> None:
    for unsafe_value in (
        "market:123",
        "source_url:https://example.invalid",
        "token=secret",
        "wallet-address",
        "order-ticket",
        "buy-now",
        "sell-now",
        "position-entry",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            item(operator_queue_key=unsafe_value)

    triage = report(item("operator-safe"))
    with pytest.raises(FrozenInstanceError):
        triage.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        triage.rows[0].triage_score = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        item(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(triage, readonly=False)

    object.__setattr__(triage.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        strategy_daily_operator_queue_triage_report_payload(triage)


def test_deterministic_payload_reason_counts_and_public_exports() -> None:
    first = report(
        item(
            "zeta-watch",
            status="watch",
            urgency=d("0.600000"),
            reason_codes=("operator_note_pending",),
        ),
        item(
            "beta-blocked",
            status="blocked",
            research_gap_count=d("3.000000"),
        ),
        item("alpha-pass"),
    )
    second = report(
        item("alpha-pass"),
        item(
            "beta-blocked",
            status="blocked",
            research_gap_count=d("3.000000"),
        ),
        item(
            "zeta-watch",
            status="watch",
            urgency=d("0.600000"),
            reason_codes=("operator_note_pending",),
        ),
    )

    assert strategy_daily_operator_queue_triage_report_payload(first) == (
        strategy_daily_operator_queue_triage_report_payload(second)
    )
    assert strategy_daily_operator_queue_triage_report_digest(first) == (
        strategy_daily_operator_queue_triage_report_digest(second)
    )
    assert first.reason_code_counts == (
        StrategyDailyOperatorQueueTriageReasonCodeCount(
            reason_code="input_status_blocked",
            count=d("1.000000"),
        ),
        StrategyDailyOperatorQueueTriageReasonCodeCount(
            reason_code="input_status_watch",
            count=d("1.000000"),
        ),
        StrategyDailyOperatorQueueTriageReasonCodeCount(
            reason_code="operator_note_pending",
            count=d("1.000000"),
        ),
        StrategyDailyOperatorQueueTriageReasonCodeCount(
            reason_code="research_gap_count_blocked",
            count=d("1.000000"),
        ),
        StrategyDailyOperatorQueueTriageReasonCodeCount(
            reason_code="triage_clear",
            count=d("1.000000"),
        ),
        StrategyDailyOperatorQueueTriageReasonCodeCount(
            reason_code="urgency_watch",
            count=d("1.000000"),
        ),
    )

    import polymarket_alpha_lab.strategy_daily_operator_queue_triage_report as triage_module

    assert triage_module.__all__ == (
        "DEFAULT_STRATEGY_DAILY_OPERATOR_QUEUE_TRIAGE_REPORT_CONFIG_VERSION",
        "StrategyDailyOperatorQueueTriageConfig",
        "StrategyDailyOperatorQueueTriageInput",
        "StrategyDailyOperatorQueueTriageReasonCodeCount",
        "StrategyDailyOperatorQueueTriageReport",
        "StrategyDailyOperatorQueueTriageRow",
        "build_strategy_daily_operator_queue_triage_report",
        "strategy_daily_operator_queue_triage_report_digest",
        "strategy_daily_operator_queue_triage_report_payload",
    )


def test_report_digest_consistency_validation() -> None:
    triage = report(item("operator-consistent"))

    assert triage.public_digest == strategy_daily_operator_queue_triage_report_digest(
        triage,
    )
    assert (
        strategy_daily_operator_queue_triage_report_payload(triage)["public_digest"]
        == triage.public_digest
    )
    with pytest.raises(ValueError, match="public_digest"):
        replace(triage, public_digest="0" * 64)
    with pytest.raises(ValueError, match="queue_count"):
        replace(triage, queue_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(triage, status="blocked")
    with pytest.raises(ValueError, match="mean_triage_score"):
        replace(triage, mean_triage_score=d("9.000000"))


def test_static_forbidden_public_terms_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower().replace("source_refresh_due", "")
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "market",
        "slug",
        "question",
        "source",
        "ref",
        "url",
        "dsn",
        "table",
        "token",
        "position",
        "buy",
        "sell",
        "recommend",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
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
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", "asdict"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Name):
            if node.id == "source_refresh_due":
                continue
            assert node.id.lower() not in forbidden
        elif isinstance(node, ast.Attribute):
            if node.attr == "source_refresh_due":
                continue
            assert node.attr.lower() not in forbidden
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(alias.name != "asdict" for alias in node.names)
