from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_edge_decay_monitor_report import (
    DEFAULT_RESEARCH_STRATEGY_EDGE_DECAY_MONITOR_REPORT_CONFIG_VERSION,
    ResearchStrategyEdgeDecayMonitorConfig,
    ResearchStrategyEdgeDecayMonitorInput,
    ResearchStrategyEdgeDecayMonitorReasonCodeCount,
    ResearchStrategyEdgeDecayMonitorReport,
    ResearchStrategyEdgeDecayMonitorRow,
    build_research_strategy_edge_decay_monitor_report,
    research_strategy_edge_decay_monitor_report_digest,
    research_strategy_edge_decay_monitor_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_edge_decay_monitor_report.py"
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyEdgeDecayMonitorConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_STRATEGY_EDGE_DECAY_MONITOR_REPORT_CONFIG_VERSION,
        "fresh_evidence_max_age_seconds": d("3600.000000"),
        "stale_evidence_max_age_seconds": d("86400.000000"),
        "repricing_watch_delta": d("0.050000"),
        "repricing_block_delta": d("0.120000"),
        "cost_pressure_watch_delta": d("0.020000"),
        "cost_pressure_block_delta": d("0.060000"),
        "review_watch_lag_seconds": d("21600.000000"),
        "review_block_lag_seconds": d("86400.000000"),
        "pass_edge_health_score": d("0.750000"),
        "watch_edge_health_score": d("0.500000"),
        "evidence_age_weight": d("0.250000"),
        "market_repricing_weight": d("0.250000"),
        "cost_pressure_weight": d("0.250000"),
        "team_review_lag_weight": d("0.250000"),
    }
    values.update(overrides)
    return ResearchStrategyEdgeDecayMonitorConfig(**values)


def input_row(
    research_case_ref: str = "case-alpha",
    *,
    evidence_observed_at: datetime | None = None,
    last_market_priced_at: datetime | None = None,
    last_team_reviewed_at: datetime | None = None,
    apparent_edge: Decimal = d("0.100000"),
    current_edge: Decimal = d("0.100000"),
    evidence_market_probability: Decimal = d("0.420000"),
    current_market_probability: Decimal = d("0.430000"),
    baseline_cost_rate: Decimal = d("0.010000"),
    current_cost_rate: Decimal = d("0.012000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyEdgeDecayMonitorInput:
    return ResearchStrategyEdgeDecayMonitorInput(
        research_case_ref=research_case_ref,
        evidence_observed_at=evidence_observed_at
        or GENERATED_AT - timedelta(minutes=30),
        last_market_priced_at=last_market_priced_at
        or GENERATED_AT - timedelta(minutes=15),
        last_team_reviewed_at=last_team_reviewed_at
        or GENERATED_AT - timedelta(hours=2),
        apparent_edge=apparent_edge,
        current_edge=current_edge,
        evidence_market_probability=evidence_market_probability,
        current_market_probability=current_market_probability,
        baseline_cost_rate=baseline_cost_rate,
        current_cost_rate=current_cost_rate,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategyEdgeDecayMonitorConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyEdgeDecayMonitorReport:
    return build_research_strategy_edge_decay_monitor_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_monitor_reports_pass_watch_and_block_decay_causes() -> None:
    monitor = report(
        (
            input_row("case-pass"),
            input_row(
                "case-watch",
                evidence_observed_at=GENERATED_AT - timedelta(hours=8),
                last_market_priced_at=GENERATED_AT - timedelta(minutes=20),
                last_team_reviewed_at=GENERATED_AT - timedelta(hours=8),
                apparent_edge=d("0.100000"),
                current_edge=d("0.070000"),
                evidence_market_probability=d("0.420000"),
                current_market_probability=d("0.480000"),
                baseline_cost_rate=d("0.010000"),
                current_cost_rate=d("0.040000"),
                reason_codes=("research_packet_reviewed",),
            ),
            input_row(
                "case-block",
                evidence_observed_at=GENERATED_AT - timedelta(hours=30),
                last_market_priced_at=GENERATED_AT - timedelta(hours=1),
                last_team_reviewed_at=GENERATED_AT - timedelta(hours=30),
                apparent_edge=d("0.120000"),
                current_edge=d("0.010000"),
                evidence_market_probability=d("0.390000"),
                current_market_probability=d("0.560000"),
                baseline_cost_rate=d("0.010000"),
                current_cost_rate=d("0.080000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert type(monitor) is ResearchStrategyEdgeDecayMonitorReport
    assert is_dataclass(monitor)
    assert monitor.__dataclass_params__.frozen
    assert monitor.generated_at == GENERATED_AT
    assert monitor.generated_at.tzinfo is UTC
    assert monitor.config_version == (
        "research-strategy-edge-decay-monitor-report-v0"
    )
    assert monitor.status == "block"
    assert monitor.input_count == d("3.000000")
    assert monitor.pass_count == d("1.000000")
    assert monitor.watch_count == d("1.000000")
    assert monitor.block_count == d("1.000000")
    assert monitor.average_edge_health_score == d("0.519515")
    assert monitor.max_edge_decay_ratio == d("0.916667")
    assert monitor.max_evidence_age_seconds == d("108000.000000")
    assert monitor.max_market_repricing_delta == d("0.170000")
    assert monitor.max_cost_pressure == d("0.070000")
    assert monitor.max_team_review_lag_seconds == d("108000.000000")
    assert monitor.paper_only is True
    assert monitor.report_only is True
    assert monitor.readonly is True

    assert tuple(row.status for row in monitor.rows) == ("block", "watch", "pass")
    blocked, watched, passed = monitor.rows

    assert type(blocked) is ResearchStrategyEdgeDecayMonitorRow
    assert blocked.evidence_age_seconds == d("108000.000000")
    assert blocked.market_repricing_delta == d("0.170000")
    assert blocked.cost_pressure == d("0.070000")
    assert blocked.team_review_lag_seconds == d("108000.000000")
    assert blocked.edge_decay_ratio == d("0.916667")
    assert blocked.edge_retention_ratio == d("0.083333")
    assert blocked.edge_health_score == ZERO
    assert blocked.reason_codes == (
        "research_strategy_edge_decay_monitor_stale_evidence",
        "research_strategy_edge_decay_monitor_market_repricing_block",
        "research_strategy_edge_decay_monitor_cost_pressure_block",
        "research_strategy_edge_decay_monitor_team_review_lag_block",
        "research_strategy_edge_decay_monitor_score_block",
    )

    assert watched.evidence_age_seconds == d("28800.000000")
    assert watched.market_repricing_delta == d("0.060000")
    assert watched.cost_pressure == d("0.030000")
    assert watched.team_review_lag_seconds == d("28800.000000")
    assert watched.edge_decay_ratio == d("0.300000")
    assert watched.edge_retention_ratio == d("0.700000")
    assert watched.edge_health_score == d("0.558545")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "research_strategy_edge_decay_monitor_aging_evidence",
        "research_strategy_edge_decay_monitor_market_repricing_watch",
        "research_strategy_edge_decay_monitor_cost_pressure_watch",
        "research_strategy_edge_decay_monitor_team_review_lag_watch",
        "research_strategy_edge_decay_monitor_score_watch",
        "input_research_packet_reviewed",
    )

    assert passed.edge_health_score == d("1.000000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("research_strategy_edge_decay_monitor_pass",)


def test_empty_monitor_is_blocked_report_only_decimal_summary() -> None:
    monitor = report(())

    assert monitor.status == "block"
    assert monitor.input_count == ZERO
    assert monitor.pass_count == ZERO
    assert monitor.watch_count == ZERO
    assert monitor.block_count == ZERO
    assert monitor.average_edge_health_score == ZERO
    assert monitor.max_edge_decay_ratio == ZERO
    assert monitor.max_evidence_age_seconds == ZERO
    assert monitor.max_market_repricing_delta == ZERO
    assert monitor.max_cost_pressure == ZERO
    assert monitor.max_team_review_lag_seconds == ZERO
    assert monitor.rows == ()
    assert monitor.reason_codes == ("research_strategy_edge_decay_monitor_no_inputs",)
    assert monitor.reason_code_counts == (
        ResearchStrategyEdgeDecayMonitorReasonCodeCount(
            reason_code="research_strategy_edge_decay_monitor_no_inputs",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert monitor.paper_only is True
    assert monitor.report_only is True
    assert monitor.readonly is True


def test_payload_and_digest_are_deterministic_public_and_decimal_only() -> None:
    first = report(
        (
            input_row("private-case?token=hidden", reason_codes=("zeta", "alpha")),
            input_row("case-a"),
        ),
    )
    second = report(
        (
            input_row("case-a"),
            input_row("private-case?token=hidden", reason_codes=("alpha", "zeta")),
        ),
    )

    first_payload = research_strategy_edge_decay_monitor_report_payload(first)
    second_payload = research_strategy_edge_decay_monitor_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)
    public_text = repr(first_payload).lower()

    assert first == second
    assert first_payload == second_payload
    assert research_strategy_edge_decay_monitor_report_digest(first) == (
        research_strategy_edge_decay_monitor_report_digest(second)
    )
    assert len(research_strategy_edge_decay_monitor_report_digest(first)) == 64
    assert first_payload["input_count"] == "2.000000"
    assert first_payload["rows"][0]["edge_health_score"] == "1.000000"
    assert all(not isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 1.0" not in encoded
    assert "hidden" not in public_text
    assert "private-case" not in public_text
    assert not any(
        key
        in {
            "research_case_ref",
            "condition_id",
            "token_id",
            "source_url",
            "source_reference",
        }
        for key in _walk_payload_keys(first_payload)
    )


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_rows() -> None:
    with pytest.raises(ValueError, match="repricing_watch_delta"):
        config(repricing_watch_delta=d("0.130000"))
    with pytest.raises(ValueError, match="pass_edge_health_score"):
        config(pass_edge_health_score=d("0.300000"))
    with pytest.raises(ValueError, match="evidence_age_weight"):
        config(evidence_age_weight=d("0.100000"))
    with pytest.raises(ValueError, match="market_repricing_weight"):
        config(market_repricing_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="research_case_ref"):
        input_row(_StringSubclass("case-alpha"))
    with pytest.raises(ValueError, match="research_case_ref"):
        input_row(" case-alpha")
    with pytest.raises(ValueError, match="evidence_observed_at"):
        input_row(evidence_observed_at=datetime(2026, 7, 7, 15, 0))
    with pytest.raises(ValueError, match="last_team_reviewed_at"):
        input_row(
            last_team_reviewed_at=_DateTimeSubclass(2026, 7, 7, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="apparent_edge"):
        input_row(apparent_edge=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="current_cost_rate"):
        input_row(current_cost_rate=Decimal("NaN"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        report((input_row(),), generated_at=datetime(2026, 7, 7, 15, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (input_row(),),
            generated_at=_DateTimeSubclass(2026, 7, 7, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="inputs"):
        report((object(),))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        report((input_row(evidence_observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="last_market_priced_at"):
        report((input_row(last_market_priced_at=GENERATED_AT + timedelta(seconds=1)),))

    ready_report = report((input_row(),))
    ready = ready_report.rows[0]
    with pytest.raises(ValueError, match="edge_decay_ratio"):
        replace(ready, edge_decay_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "research_strategy_edge_decay_monitor_pass",
                "research_strategy_edge_decay_monitor_score_watch",
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(ready, status="block")
    with pytest.raises(ValueError, match="pass_count"):
        replace(ready_report, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report((input_row("case-z"), input_row("case-a")))
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_dataclasses_are_frozen_and_numeric_fields_are_decimals() -> None:
    cfg = config()
    source_row = input_row()
    monitor = report((source_row,), cfg=cfg)

    for value in (
        cfg,
        source_row,
        monitor,
        monitor.rows[0],
        monitor.reason_code_counts[0],
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        _assert_decimal_numeric_fields(value)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.current_edge = d("0.010000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        monitor.rows[0].edge_health_score = ZERO  # type: ignore[misc]


def test_owned_module_has_no_io_execution_or_action_language() -> None:
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
        "live trading",
        "wallet",
        "order",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "requests",
        "http",
        "socket",
        "subprocess",
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
    for value in forbidden_fragments:
        assert value not in source.lower()


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(
            (
                "_count",
                "_ratio",
                "_score",
                "_seconds",
                "_delta",
                "_pressure",
                "_edge",
                "_rate",
            ),
        ):
            assert type(item) is Decimal
