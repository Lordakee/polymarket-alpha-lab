from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_event_liquidity_information_divergence_report import (
    DEFAULT_RESEARCH_EVENT_LIQUIDITY_INFORMATION_DIVERGENCE_REPORT_CONFIG_VERSION,
    ResearchEventLiquidityInformationDivergenceConfig,
    ResearchEventLiquidityInformationDivergenceInput,
    ResearchEventLiquidityInformationDivergenceReasonCodeCount,
    ResearchEventLiquidityInformationDivergenceReport,
    ResearchEventLiquidityInformationDivergenceRow,
    build_research_event_liquidity_information_divergence_report,
    research_event_liquidity_information_divergence_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_event_liquidity_information_divergence_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> ResearchEventLiquidityInformationDivergenceConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_LIQUIDITY_INFORMATION_DIVERGENCE_REPORT_CONFIG_VERSION
        ),
        "pass_depth_units": d("100.000000"),
        "block_depth_units": d("25.000000"),
        "spread_pressure_watch_threshold": d("0.350000"),
        "spread_pressure_block_threshold": d("0.700000"),
        "evidence_age_watch_hours": d("24.000000"),
        "evidence_age_block_hours": d("72.000000"),
        "source_reliability_watch_threshold": d("0.700000"),
        "source_reliability_block_threshold": d("0.400000"),
        "catalyst_pressure_watch_threshold": d("0.400000"),
        "catalyst_pressure_block_threshold": d("0.750000"),
        "divergence_watch_threshold": d("0.400000"),
        "divergence_block_threshold": d("0.700000"),
        "depth_weight": d("0.250000"),
        "spread_weight": d("0.200000"),
        "freshness_weight": d("0.200000"),
        "reliability_weight": d("0.200000"),
        "catalyst_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchEventLiquidityInformationDivergenceConfig(**values)


def _input(
    analysis_key: str = "event-alpha/raw_market_slug?source_id=hidden-token",
    **overrides: object,
) -> ResearchEventLiquidityInformationDivergenceInput:
    values = {
        "analysis_key": analysis_key,
        "aggregate_depth_units": d("125.000000"),
        "spread_pressure_score": d("0.120000"),
        "evidence_age_hours": d("6.000000"),
        "source_reliability_score": d("0.900000"),
        "catalyst_pressure_score": d("0.150000"),
    }
    values.update(overrides)
    return ResearchEventLiquidityInformationDivergenceInput(**values)


def _report(
    rows: tuple[ResearchEventLiquidityInformationDivergenceInput, ...],
    *,
    cfg: ResearchEventLiquidityInformationDivergenceConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventLiquidityInformationDivergenceReport:
    return build_research_event_liquidity_information_divergence_report(
        rows,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(_walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(_walk_values(item))
        return tuple(nested)
    return (value,)


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
        if field.name.endswith(("_count", "_score", "_units", "_hours", "_ratio")):
            assert type(item) is Decimal


def test_report_detects_liquidity_information_divergence_and_sorts_rows() -> None:
    report = _report(
        (
            _input(
                "raw-event-block/market-id=hidden&source_id=secret",
                aggregate_depth_units=d("20.000000"),
                spread_pressure_score=d("0.820000"),
                evidence_age_hours=d("96.000000"),
                source_reliability_score=d("0.350000"),
                catalyst_pressure_score=d("0.860000"),
            ),
            _input(
                "event-watch",
                aggregate_depth_units=d("80.000000"),
                spread_pressure_score=d("0.400000"),
                evidence_age_hours=d("30.000000"),
                source_reliability_score=d("0.650000"),
                catalyst_pressure_score=d("0.450000"),
            ),
            _input(
                "event-pass",
                aggregate_depth_units=d("125.000000"),
                spread_pressure_score=d("0.120000"),
                evidence_age_hours=d("6.000000"),
                source_reliability_score=d("0.900000"),
                catalyst_pressure_score=d("0.150000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        DEFAULT_RESEARCH_EVENT_LIQUIDITY_INFORMATION_DIVERGENCE_REPORT_CONFIG_VERSION
    )
    assert report.public_status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_divergence_score == d("0.435667")
    assert report.max_divergence_score == d("0.873000")
    assert report.average_depth_units == d("75.000000")
    assert report.max_spread_pressure_score == d("0.820000")
    assert report.max_evidence_age_hours == d("96.000000")
    assert report.min_source_reliability_score == d("0.350000")
    assert report.max_catalyst_pressure_score == d("0.860000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.public_status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is ResearchEventLiquidityInformationDivergenceRow
    assert blocked.analysis_digest.startswith("sha256:")
    assert blocked.depth_gap_score == d("1.000000")
    assert blocked.freshness_gap_score == d("1.000000")
    assert blocked.reliability_gap_score == d("0.650000")
    assert blocked.divergence_score == d("0.873000")
    assert blocked.reason_codes == (
        "liquidity_depth_block",
        "spread_pressure_block",
        "evidence_freshness_block",
        "source_reliability_block",
        "catalyst_pressure_block",
        "divergence_score_block",
    )

    watched = report.rows[1]
    assert watched.depth_gap_score == d("0.200000")
    assert watched.freshness_gap_score == d("0.416667")
    assert watched.reliability_gap_score == d("0.350000")
    assert watched.divergence_score == d("0.350833")
    assert watched.reason_codes == (
        "liquidity_depth_watch",
        "spread_pressure_watch",
        "evidence_freshness_watch",
        "source_reliability_watch",
        "catalyst_pressure_watch",
    )

    passed = report.rows[2]
    assert passed.divergence_score == d("0.083167")
    assert passed.reason_codes == ("liquidity_information_alignment_pass",)

    assert report.reason_code_counts == (
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="liquidity_depth_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="spread_pressure_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="evidence_freshness_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="source_reliability_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="catalyst_pressure_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="divergence_score_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="liquidity_depth_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="spread_pressure_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="evidence_freshness_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="source_reliability_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="catalyst_pressure_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="liquidity_information_alignment_pass",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
    )
    assert report.reason_codes == tuple(
        row.reason_code for row in report.reason_code_counts
    )
    assert len(report.derived_validation_digest) == 64


def test_empty_report_is_public_safe_block() -> None:
    report = _report(())

    assert report.public_status == "block"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_divergence_score == ZERO
    assert report.max_divergence_score == ZERO
    assert report.average_depth_units == ZERO
    assert report.max_spread_pressure_score == ZERO
    assert report.max_evidence_age_hours == ZERO
    assert report.min_source_reliability_score == ZERO
    assert report.max_catalyst_pressure_score == ZERO
    assert report.rows == ()
    assert report.reason_code_counts == (
        ResearchEventLiquidityInformationDivergenceReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert report.reason_codes == ("empty_input",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_deterministic_redacted_and_decimal_string_only() -> None:
    report = _report(
        (
            _input("raw-event-id=abc&market_id=hidden&source_id=secret"),
        ),
    )

    payload = research_event_liquidity_information_divergence_payload(report)
    duplicate_payload = research_event_liquidity_information_divergence_payload(
        _report(
            (
                _input("raw-event-id=abc&market_id=hidden&source_id=secret"),
            ),
        ),
    )
    encoded = json.dumps(payload, sort_keys=True)
    rendered = repr(payload).casefold()

    assert payload == report.payload
    assert payload == duplicate_payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["aggregate_depth_units"] == "125.000000"
    assert payload["rows"][0]["analysis_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(str(payload["derived_validation_digest"])) == 64
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    for forbidden in (
        "raw-event-id",
        "market_id",
        "source_id",
        "hidden",
        "secret",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "position",
    ):
        assert forbidden not in rendered
        assert forbidden not in encoded.casefold()


def test_public_contracts_are_frozen_and_decimal_only() -> None:
    assert is_dataclass(ResearchEventLiquidityInformationDivergenceConfig)
    assert is_dataclass(ResearchEventLiquidityInformationDivergenceInput)
    assert is_dataclass(ResearchEventLiquidityInformationDivergenceRow)
    assert is_dataclass(ResearchEventLiquidityInformationDivergenceReasonCodeCount)
    assert is_dataclass(ResearchEventLiquidityInformationDivergenceReport)

    cfg = _config()
    source_row = _input()
    report = _report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.aggregate_depth_units = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].divergence_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.row_count = d("3.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("research-event-liquidity-info-v0"))
    with pytest.raises(ValueError, match="pass_depth_units"):
        _config(pass_depth_units=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_depth_units"):
        _config(block_depth_units=d("150.000000"))
    with pytest.raises(ValueError, match="spread_pressure_watch_threshold"):
        _config(spread_pressure_watch_threshold=_DecimalSubclass("0.350000"))
    with pytest.raises(ValueError, match="source_reliability_block_threshold"):
        _config(source_reliability_block_threshold=d("0.800000"))
    with pytest.raises(ValueError, match="weights"):
        _config(depth_weight=d("0.300000"))
    with pytest.raises(ValueError, match="paper_only"):
        _config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _config(readonly=False)

    with pytest.raises(ValueError, match="analysis_key"):
        _input(analysis_key="")
    with pytest.raises(ValueError, match="analysis_key"):
        _input(analysis_key=_StringSubclass("event-alpha"))
    with pytest.raises(ValueError, match="aggregate_depth_units"):
        _input(aggregate_depth_units=125)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_pressure_score"):
        _input(spread_pressure_score=d("1.000001"))
    with pytest.raises(ValueError, match="evidence_age_hours"):
        _input(evidence_age_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="source_reliability_score"):
        _input(source_reliability_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="catalyst_pressure_score"):
        _input(catalyst_pressure_score=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        build_research_event_liquidity_information_divergence_report(
            (),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        _report((object(),))  # type: ignore[arg-type]


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    ready = _report((_input(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "liquidity_information_alignment_pass",
                "spread_pressure_watch",
            ),
        )
    with pytest.raises(ValueError, match="public_status"):
        replace(ready, public_status="watch")
    with pytest.raises(ValueError, match="divergence_score"):
        replace(ready, divergence_score=d("0.900000"))
    with pytest.raises(ValueError, match="analysis_digest"):
        replace(ready, analysis_digest="raw-event-id")

    report = _report((_input(),))
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="rows"):
        unordered = _report(
            (
                _input("event-z", spread_pressure_score=d("0.400000")),
                _input("event-a", aggregate_depth_units=d("20.000000")),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_public_numeric_fields_are_decimals() -> None:
    source_row = _input()
    report = _report((source_row,))

    _assert_decimal_numeric_fields(source_row)
    _assert_decimal_numeric_fields(report)
    _assert_decimal_numeric_fields(report.rows[0])
    _assert_decimal_numeric_fields(report.reason_code_counts[0])


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
        "event_id",
        "event-id",
        "market_id",
        "market-id",
        "condition_id",
        "condition-id",
        "source_id",
        "source-id",
        "raw_source",
        "raw_market",
        "slug",
        "clob",
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
        "api_key",
        "secret",
        "credential",
        "token",
        "database",
        "network",
        "http",
        "buy",
        "sell",
        "recommend",
        "position",
        "sizing",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.casefold()
    for value in forbidden_fragments:
        assert value not in lowered
