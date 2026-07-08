from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_signal_decay_dashboard_report import (
    DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_DASHBOARD_CONFIG_VERSION,
    ResearchStrategySignalDecayDashboardConfig,
    ResearchStrategySignalDecayDashboardReasonCodeCount,
    ResearchStrategySignalDecayDashboardReport,
    ResearchStrategySignalDecayDashboardRow,
    ResearchStrategySignalDecayInputRow,
    build_research_strategy_signal_decay_dashboard_report,
    research_strategy_signal_decay_dashboard_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_signal_decay_dashboard_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategySignalDecayDashboardConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_DASHBOARD_CONFIG_VERSION
        ),
        "fresh_signal_max_age_seconds": d("3600.000000"),
        "stale_signal_max_age_seconds": d("86400.000000"),
        "refresh_failure_watch_threshold": d("0.100000"),
        "refresh_failure_block_threshold": d("0.300000"),
        "domain_difference_watch_threshold": d("0.250000"),
        "domain_difference_block_threshold": d("0.500000"),
        "settlement_watch_window_seconds": d("172800.000000"),
        "settlement_block_window_seconds": d("21600.000000"),
        "model_disagreement_watch_threshold": d("0.150000"),
        "model_disagreement_block_threshold": d("0.350000"),
        "pass_dashboard_score": d("0.700000"),
        "watch_dashboard_score": d("0.400000"),
        "signal_age_weight": d("0.250000"),
        "refresh_failure_weight": d("0.200000"),
        "domain_difference_weight": d("0.200000"),
        "settlement_window_weight": d("0.150000"),
        "model_disagreement_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchStrategySignalDecayDashboardConfig(**values)


def input_row(
    signal_ref: str = "signal-alpha",
    *,
    signal_domain: str = "sports",
    expected_domain: str = "sports",
    signal_observed_at: datetime | None = None,
    last_refresh_attempt_at: datetime | None = None,
    refresh_failure_count: Decimal = d("0.000000"),
    refresh_attempt_count: Decimal = d("4.000000"),
    domain_difference_score: Decimal = d("0.050000"),
    settlement_at: datetime | None = None,
    model_probability_low: Decimal = d("0.520000"),
    model_probability_high: Decimal = d("0.570000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategySignalDecayInputRow:
    return ResearchStrategySignalDecayInputRow(
        signal_ref=signal_ref,
        signal_domain=signal_domain,
        expected_domain=expected_domain,
        signal_observed_at=signal_observed_at or GENERATED_AT - timedelta(minutes=30),
        last_refresh_attempt_at=last_refresh_attempt_at
        or GENERATED_AT
        - timedelta(minutes=30),
        refresh_failure_count=refresh_failure_count,
        refresh_attempt_count=refresh_attempt_count,
        domain_difference_score=domain_difference_score,
        settlement_at=settlement_at or GENERATED_AT + timedelta(days=7),
        model_probability_low=model_probability_low,
        model_probability_high=model_probability_high,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategySignalDecayDashboardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySignalDecayDashboardReport:
    return build_research_strategy_signal_decay_dashboard_report(
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


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


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
        if field.name.endswith(
            ("_count", "_rate", "_score", "_seconds", "_weight", "_threshold"),
        ):
            assert type(item) is Decimal


def test_dashboard_reduces_required_signal_decay_dimensions() -> None:
    summary = report(
        (
            input_row("signal-pass"),
            input_row(
                "signal-watch",
                signal_domain="sports",
                expected_domain="macro",
                signal_observed_at=GENERATED_AT - timedelta(hours=6),
                last_refresh_attempt_at=GENERATED_AT - timedelta(hours=6),
                refresh_failure_count=d("1.000000"),
                refresh_attempt_count=d("5.000000"),
                domain_difference_score=d("0.300000"),
                settlement_at=GENERATED_AT + timedelta(hours=24),
                model_probability_low=d("0.400000"),
                model_probability_high=d("0.600000"),
            ),
            input_row(
                "signal-block",
                signal_domain="weather",
                expected_domain="macro",
                signal_observed_at=GENERATED_AT - timedelta(hours=30),
                last_refresh_attempt_at=GENERATED_AT - timedelta(hours=30),
                refresh_failure_count=d("3.000000"),
                refresh_attempt_count=d("5.000000"),
                domain_difference_score=d("0.800000"),
                settlement_at=GENERATED_AT + timedelta(hours=3),
                model_probability_low=d("0.100000"),
                model_probability_high=d("0.700000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert (
        summary.config_version
        == DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_DASHBOARD_CONFIG_VERSION
    )
    assert summary.dashboard_status == "block"
    assert summary.row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_dashboard_score == d("0.482103")
    assert summary.max_signal_age_seconds == d("108000.000000")
    assert summary.max_refresh_failure_rate == d("0.600000")
    assert summary.max_domain_difference_score == d("0.800000")
    assert summary.min_settlement_seconds_remaining == d("10800.000000")
    assert summary.max_model_disagreement_score == d("0.600000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked = summary.rows[0]
    assert type(blocked) is ResearchStrategySignalDecayDashboardRow
    assert blocked.signal_age_seconds == d("108000.000000")
    assert blocked.refresh_lag_seconds == d("108000.000000")
    assert blocked.refresh_failure_rate == d("0.600000")
    assert blocked.domain_difference_score == d("0.800000")
    assert blocked.settlement_seconds_remaining == d("10800.000000")
    assert blocked.model_disagreement_score == d("0.600000")
    assert blocked.dashboard_score == ZERO
    assert blocked.reason_codes == (
        "research_strategy_signal_decay_dashboard_stale_signal",
        "research_strategy_signal_decay_dashboard_refresh_failure_block",
        "research_strategy_signal_decay_dashboard_domain_difference_block",
        "research_strategy_signal_decay_dashboard_settlement_block_window",
        "research_strategy_signal_decay_dashboard_model_disagreement_block",
        "research_strategy_signal_decay_dashboard_score_block",
    )

    watched = summary.rows[1]
    assert watched.signal_age_seconds == d("21600.000000")
    assert watched.refresh_lag_seconds == d("21600.000000")
    assert watched.refresh_failure_rate == d("0.200000")
    assert watched.domain_difference_score == d("0.300000")
    assert watched.settlement_seconds_remaining == d("86400.000000")
    assert watched.model_disagreement_score == d("0.200000")
    assert watched.signal_age_score == d("0.750000")
    assert watched.refresh_failure_score == d("0.333333")
    assert watched.domain_alignment_score == d("0.400000")
    assert watched.settlement_window_score == d("0.500000")
    assert watched.model_consensus_score == d("0.428571")
    assert watched.dashboard_score == d("0.494881")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "research_strategy_signal_decay_dashboard_aging_signal",
        "research_strategy_signal_decay_dashboard_refresh_failure_watch",
        "research_strategy_signal_decay_dashboard_domain_difference_watch",
        "research_strategy_signal_decay_dashboard_settlement_watch_window",
        "research_strategy_signal_decay_dashboard_model_disagreement_watch",
        "research_strategy_signal_decay_dashboard_score_watch",
    )

    passed = summary.rows[2]
    assert passed.dashboard_score == d("0.951429")
    assert passed.status == "pass"
    assert passed.reason_codes == (
        "research_strategy_signal_decay_dashboard_pass",
    )


def test_empty_dashboard_blocks_and_is_report_only() -> None:
    summary = report(())

    assert summary.dashboard_status == "block"
    assert summary.row_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_dashboard_score == ZERO
    assert summary.max_signal_age_seconds == ZERO
    assert summary.max_refresh_failure_rate == ZERO
    assert summary.max_domain_difference_score == ZERO
    assert summary.min_settlement_seconds_remaining == ZERO
    assert summary.max_model_disagreement_score == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchStrategySignalDecayDashboardReasonCodeCount(
            reason_code="research_strategy_signal_decay_dashboard_no_inputs",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "research_strategy_signal_decay_dashboard_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_payload_uses_decimal_strings_and_safe_redacted_public_surface() -> None:
    summary = report(
        (
            input_row(
                "raw-alpha?wallet=0xdead&auth=secret&order=123",
                signal_domain="sports",
                expected_domain="sports",
            ),
        ),
    )
    payload = research_strategy_signal_decay_dashboard_report_payload(summary)
    encoded = json.dumps(payload, sort_keys=True)
    public_text = repr(payload).lower()
    dataclass_text = repr(asdict(summary)).lower()

    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["dashboard_score"] == "0.951429"
    assert payload["rows"][0]["redacted_signal_ref"].startswith("sha256:")
    assert summary.payload == payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert ": 1.0" not in encoded

    for leaked in ("wallet", "0xdead", "auth", "secret", "order", "raw-alpha"):
        assert leaked not in public_text
        assert leaked not in dataclass_text
    for key in payload_keys(payload):
        lowered = key.lower()
        assert "wallet" not in lowered
        assert "auth" not in lowered
        assert "order" not in lowered


def test_dashboard_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(ResearchStrategySignalDecayDashboardConfig)
    assert is_dataclass(ResearchStrategySignalDecayInputRow)
    assert is_dataclass(ResearchStrategySignalDecayDashboardRow)
    assert is_dataclass(ResearchStrategySignalDecayDashboardReasonCodeCount)
    assert is_dataclass(ResearchStrategySignalDecayDashboardReport)

    cfg = config()
    row = input_row()
    summary = report((row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.refresh_failure_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].dashboard_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.dashboard_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_STRATEGY_SIGNAL_DECAY_DASHBOARD_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="fresh_signal_max_age_seconds"):
        config(fresh_signal_max_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="stale_signal_max_age_seconds"):
        config(
            fresh_signal_max_age_seconds=d("86400.000000"),
            stale_signal_max_age_seconds=d("3600.000000"),
        )
    with pytest.raises(ValueError, match="refresh_failure_watch_threshold"):
        config(refresh_failure_watch_threshold=d("0.400000"))
    with pytest.raises(ValueError, match="settlement_block_window_seconds"):
        config(settlement_block_window_seconds=d("172801.000000"))
    with pytest.raises(ValueError, match="pass_dashboard_score"):
        config(pass_dashboard_score=d("0.300000"))
    with pytest.raises(ValueError, match="signal_age_weight"):
        config(signal_age_weight=d("0.100000"))
    with pytest.raises(ValueError, match="refresh_failure_weight"):
        config(refresh_failure_weight=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    with pytest.raises(ValueError, match="signal_ref"):
        input_row(_StringSubclass("signal-alpha"))
    with pytest.raises(ValueError, match="signal_ref"):
        input_row(" signal-alpha")
    with pytest.raises(ValueError, match="signal_domain"):
        input_row(signal_domain=_StringSubclass("sports"))
    with pytest.raises(ValueError, match="signal_domain"):
        input_row(signal_domain="wallet-domain")
    with pytest.raises(ValueError, match="signal_observed_at"):
        input_row(signal_observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="last_refresh_attempt_at"):
        input_row(
            last_refresh_attempt_at=_DateTimeSubclass(
                2026,
                7,
                8,
                12,
                0,
                tzinfo=UTC,
            ),
        )
    with pytest.raises(ValueError, match="refresh_failure_count"):
        input_row(refresh_failure_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="refresh_failure_count"):
        input_row(
            refresh_failure_count=d("2.000000"),
            refresh_attempt_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="model_probability_low"):
        input_row(model_probability_low=Decimal("NaN"))
    with pytest.raises(ValueError, match="model_probability_high"):
        input_row(
            model_probability_low=d("0.700000"),
            model_probability_high=d("0.600000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_research_strategy_signal_decay_dashboard_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_strategy_signal_decay_dashboard_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))
    with pytest.raises(ValueError, match="signal_observed_at"):
        report((input_row(signal_observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="last_refresh_attempt_at"):
        report(
            (
                input_row(
                    last_refresh_attempt_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    ready_summary = report((input_row(),))
    ready = ready_summary.rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "research_strategy_signal_decay_dashboard_pass",
                "research_strategy_signal_decay_dashboard_score_watch",
            ),
        )
    with pytest.raises(ValueError, match="status"):
        replace(ready, status="block")
    with pytest.raises(ValueError, match="dashboard_score"):
        replace(ready, dashboard_score=ZERO)
    with pytest.raises(ValueError, match="redacted_signal_ref"):
        replace(ready, redacted_signal_ref="raw-alpha?wallet=hidden")

    with pytest.raises(ValueError, match="pass_count"):
        replace(ready_summary, pass_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(ready_summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(ready_summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(ready_summary, readonly=False)
    with pytest.raises(ValueError, match="rows"):
        unordered = report((input_row("signal-z"), input_row("signal-a")))
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    source_row = input_row()
    summary = report((source_row,))

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_network_db_or_live_execution_surfaces() -> None:
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
        "write",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in ("wallet", "auth", "order"):
        assert value not in lowered
