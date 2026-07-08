from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_market_liquidity_regime_shift_report import (
    DEFAULT_RESEARCH_MARKET_LIQUIDITY_REGIME_SHIFT_REPORT_CONFIG_VERSION,
    ResearchMarketLiquidityRegimeShiftConfig,
    ResearchMarketLiquidityRegimeShiftInput,
    ResearchMarketLiquidityRegimeShiftReasonCodeCount,
    ResearchMarketLiquidityRegimeShiftReport,
    ResearchMarketLiquidityRegimeShiftRow,
    build_research_market_liquidity_regime_shift_report,
    research_market_liquidity_regime_shift_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_liquidity_regime_shift_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> ResearchMarketLiquidityRegimeShiftConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_LIQUIDITY_REGIME_SHIFT_REPORT_CONFIG_VERSION
        ),
        "depth_deterioration_watch_threshold": d("0.200000"),
        "depth_deterioration_block_threshold": d("0.500000"),
        "spread_widening_watch_threshold": d("0.250000"),
        "spread_widening_block_threshold": d("0.750000"),
        "book_age_watch_seconds": d("120.000000"),
        "book_age_block_seconds": d("900.000000"),
        "fee_rate_watch_threshold": d("0.010000"),
        "fee_rate_block_threshold": d("0.030000"),
        "manual_review_watch_threshold": d("0.350000"),
        "manual_review_block_threshold": d("0.700000"),
        "regime_shift_watch_threshold": d("0.350000"),
        "regime_shift_block_threshold": d("0.700000"),
        "depth_weight": d("0.300000"),
        "spread_weight": d("0.250000"),
        "freshness_weight": d("0.200000"),
        "fee_weight": d("0.150000"),
        "manual_review_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchMarketLiquidityRegimeShiftConfig(**values)


def _input(
    analysis_key: str = (
        "candidate_id=raw-candidate-123;market_id=hidden-market;"
        "market_slug=secret-slug;question=private text;token=secret-token"
    ),
    **overrides: object,
) -> ResearchMarketLiquidityRegimeShiftInput:
    values = {
        "analysis_key": analysis_key,
        "current_depth_units": d("125.000000"),
        "baseline_depth_units": d("150.000000"),
        "current_spread_rate": d("0.021000"),
        "baseline_spread_rate": d("0.020000"),
        "book_age_seconds": d("30.000000"),
        "fee_rate": d("0.005000"),
        "manual_review_urgency_score": d("0.100000"),
    }
    values.update(overrides)
    return ResearchMarketLiquidityRegimeShiftInput(**values)


def _report(
    rows: tuple[ResearchMarketLiquidityRegimeShiftInput, ...],
    *,
    cfg: ResearchMarketLiquidityRegimeShiftConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketLiquidityRegimeShiftReport:
    return build_research_market_liquidity_regime_shift_report(
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
        if field.name.endswith(("_count", "_rate", "_ratio", "_score", "_units")):
            assert type(item) is Decimal
        if field.name.endswith("_seconds"):
            assert type(item) is Decimal


def test_report_scores_liquidity_regime_shift_rows_and_rollup() -> None:
    report = _report(
        (
            _input(
                "raw-block-candidate market_id=hidden slug=secret",
                current_depth_units=d("40.000000"),
                baseline_depth_units=d("100.000000"),
                current_spread_rate=d("0.050000"),
                baseline_spread_rate=d("0.020000"),
                book_age_seconds=d("1200.000000"),
                fee_rate=d("0.035000"),
                manual_review_urgency_score=d("0.800000"),
            ),
            _input(
                "watch-case",
                current_depth_units=d("80.000000"),
                baseline_depth_units=d("100.000000"),
                current_spread_rate=d("0.025000"),
                baseline_spread_rate=d("0.020000"),
                book_age_seconds=d("300.000000"),
                fee_rate=d("0.015000"),
                manual_review_urgency_score=d("0.400000"),
            ),
            _input(
                "pass-case",
                current_depth_units=d("95.000000"),
                baseline_depth_units=d("100.000000"),
                current_spread_rate=d("0.021000"),
                baseline_spread_rate=d("0.020000"),
                book_age_seconds=d("30.000000"),
                fee_rate=d("0.005000"),
                manual_review_urgency_score=d("0.100000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_REGIME_SHIFT_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_regime_shift_score == d("0.411111")
    assert report.max_regime_shift_score == d("0.860000")
    assert report.max_depth_deterioration_score == d("0.600000")
    assert report.max_spread_widening_score == d("1.000000")
    assert report.max_book_age_seconds == d("1200.000000")
    assert report.max_fee_rate == d("0.035000")
    assert report.max_manual_review_urgency_score == d("0.800000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is ResearchMarketLiquidityRegimeShiftRow
    assert blocked.liquidity_ref.startswith("sha256:")
    assert blocked.depth_deterioration_score == d("0.600000")
    assert blocked.spread_widening_score == d("1.000000")
    assert blocked.freshness_score == d("1.000000")
    assert blocked.fee_friction_score == d("1.000000")
    assert blocked.regime_shift_score == d("0.860000")
    assert blocked.reason_codes == (
        "depth_deterioration_block",
        "spread_widening_block",
        "book_freshness_block",
        "fee_friction_block",
        "manual_review_urgency_block",
        "regime_shift_score_block",
    )

    watched = report.rows[1]
    assert watched.depth_deterioration_score == d("0.200000")
    assert watched.spread_widening_score == d("0.250000")
    assert watched.freshness_score == d("0.333333")
    assert watched.fee_friction_score == d("0.500000")
    assert watched.regime_shift_score == d("0.304167")
    assert watched.reason_codes == (
        "depth_deterioration_watch",
        "spread_widening_watch",
        "book_freshness_watch",
        "fee_friction_watch",
        "manual_review_urgency_watch",
    )

    passed = report.rows[2]
    assert passed.regime_shift_score == d("0.069167")
    assert passed.reason_codes == ("liquidity_regime_stable_pass",)

    assert report.reason_code_counts == (
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="depth_deterioration_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="spread_widening_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="book_freshness_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="fee_friction_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="manual_review_urgency_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="regime_shift_score_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="depth_deterioration_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="spread_widening_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="book_freshness_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="fee_friction_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="manual_review_urgency_watch",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="liquidity_regime_stable_pass",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        ),
    )
    assert report.reason_codes == tuple(
        row.reason_code for row in report.reason_code_counts
    )
    assert len(report.derived_validation_digest) == 64


def test_empty_report_blocks_research_until_liquidity_inputs_exist() -> None:
    report = _report(())

    assert report.status == "block"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_regime_shift_score == ZERO
    assert report.max_regime_shift_score == ZERO
    assert report.rows == ()
    assert report.reason_code_counts == (
        ResearchMarketLiquidityRegimeShiftReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert report.reason_codes == ("empty_input",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_public_payload_is_deterministic_redacted_and_digest_validated() -> None:
    report = _report(
        (
            _input(
                "candidate_id=abc123&market_id=m-456&market_slug=will-not-leak"
                "&question=private&source_url=https://example.invalid"
                "&dsn=postgres://user:pass@localhost/db&table_name=private"
                "&private_token=secret-token",
            ),
        ),
    )

    payload = research_market_liquidity_regime_shift_report_payload(report)
    duplicate_payload = research_market_liquidity_regime_shift_report_payload(
        _report(
            (
                _input(
                    "candidate_id=abc123&market_id=m-456&market_slug=will-not-leak"
                    "&question=private&source_url=https://example.invalid"
                    "&dsn=postgres://user:pass@localhost/db&table_name=private"
                    "&private_token=secret-token",
                ),
            ),
        ),
    )
    encoded = json.dumps(payload, sort_keys=True)
    rendered = repr(payload).casefold()

    assert payload == report.payload
    assert payload == duplicate_payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["liquidity_ref"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(str(payload["derived_validation_digest"])) == 64
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    for forbidden in (
        "candidate_id",
        "abc123",
        "market_id",
        "m-456",
        "market_slug",
        "will-not-leak",
        "question=private",
        "source_url",
        "https://example.invalid",
        "postgres://",
        "table_name",
        "private_token",
        "secret-token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "sizing",
    ):
        assert forbidden not in rendered
        assert forbidden not in encoded.casefold()

    tampered = dict(payload)
    tampered["pass_count"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_market_liquidity_regime_shift_report_payload(tampered)


def test_public_contracts_are_frozen_decimal_only_and_flagged() -> None:
    assert is_dataclass(ResearchMarketLiquidityRegimeShiftConfig)
    assert is_dataclass(ResearchMarketLiquidityRegimeShiftInput)
    assert is_dataclass(ResearchMarketLiquidityRegimeShiftRow)
    assert is_dataclass(ResearchMarketLiquidityRegimeShiftReasonCodeCount)
    assert is_dataclass(ResearchMarketLiquidityRegimeShiftReport)

    cfg = _config()
    source_row = _input()
    report = _report((source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.current_depth_units = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].regime_shift_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.row_count = d("3.000000")  # type: ignore[misc]

    for value in (cfg, source_row, report, *report.rows, *report.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        _assert_decimal_numeric_fields(value)

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("research-market-liquidity-v0"))
    with pytest.raises(ValueError, match="depth_deterioration_watch_threshold"):
        _config(depth_deterioration_watch_threshold=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="depth"):
        _config(depth_deterioration_watch_threshold=d("0.700000"))
    with pytest.raises(ValueError, match="weights"):
        _config(depth_weight=d("0.350000"))
    with pytest.raises(ValueError, match="paper_only"):
        _config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _config(readonly=False)

    with pytest.raises(ValueError, match="analysis_key"):
        _input(analysis_key="")
    with pytest.raises(ValueError, match="analysis_key"):
        _input(analysis_key=_StringSubclass("alpha"))
    with pytest.raises(ValueError, match="current_depth_units"):
        _input(current_depth_units=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="baseline_depth_units"):
        _input(baseline_depth_units=d("0.000000"))
    with pytest.raises(ValueError, match="current_spread_rate"):
        _input(current_spread_rate=d("1.000001"))
    with pytest.raises(ValueError, match="baseline_spread_rate"):
        _input(baseline_spread_rate=d("0.000000"))
    with pytest.raises(ValueError, match="book_age_seconds"):
        _input(book_age_seconds=d("-0.000001"))
    with pytest.raises(ValueError, match="fee_rate"):
        _input(fee_rate=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="manual_review_urgency_score"):
        _input(manual_review_urgency_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_market_liquidity_regime_shift_report(
            (),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        _report((object(),))  # type: ignore[arg-type]


def test_report_and_payload_reject_manual_drift_and_unsafe_public_values() -> None:
    report = _report((_input(),))
    row = report.rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("liquidity_regime_stable_pass", "fee_friction_watch"))
    with pytest.raises(ValueError, match="status"):
        replace(row, status="watch")
    with pytest.raises(ValueError, match="regime_shift_score"):
        replace(row, regime_shift_score=d("0.900000"))
    with pytest.raises(ValueError, match="liquidity_ref"):
        replace(row, liquidity_ref="raw-liquidity-row")
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="rows"):
        unordered = _report(
            (
                _input("z-watch", fee_rate=d("0.015000")),
                _input("a-block", fee_rate=d("0.040000")),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    payload = research_market_liquidity_regime_shift_report_payload(report)
    for key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question_text",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet_address",
        "order_id",
        "live_url",
        "recommendation",
        "position_size",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            research_market_liquidity_regime_shift_report_payload(unsafe)

    numeric = dict(payload)
    numeric["row_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        research_market_liquidity_regime_shift_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_market_liquidity_regime_shift_report_payload(downgraded)


def test_module_has_no_io_auth_execution_or_trading_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float
