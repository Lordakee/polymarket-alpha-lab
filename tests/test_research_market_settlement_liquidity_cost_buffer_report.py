from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab import (
    research_market_settlement_liquidity_cost_buffer_report as report_module,
)
from polymarket_alpha_lab.research_market_settlement_liquidity_cost_buffer_report import (
    DEFAULT_RESEARCH_MARKET_SETTLEMENT_LIQUIDITY_COST_BUFFER_CONFIG_VERSION,
    ResearchMarketSettlementLiquidityCostBufferCandidate,
    ResearchMarketSettlementLiquidityCostBufferConfig,
    ResearchMarketSettlementLiquidityCostBufferReasonCodeCount,
    ResearchMarketSettlementLiquidityCostBufferReport,
    ResearchMarketSettlementLiquidityCostBufferRow,
    build_research_market_settlement_liquidity_cost_buffer_report,
    research_market_settlement_liquidity_cost_buffer_digest,
    research_market_settlement_liquidity_cost_buffer_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_market_settlement_liquidity_cost_buffer_report.py",
)
PAYLOAD_VALIDATOR_NAME = (
    "validate_research_market_settlement_liquidity_cost_buffer_report_payload"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketSettlementLiquidityCostBufferConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_MARKET_SETTLEMENT_LIQUIDITY_COST_BUFFER_CONFIG_VERSION
        ),
        "pass_max_liquidity_cost_buffer_score": d("0.300000"),
        "watch_max_liquidity_cost_buffer_score": d("0.650000"),
        "settlement_cost_load_watch_ratio": d("0.200000"),
        "settlement_cost_load_block_ratio": d("0.500000"),
        "liquidity_buffer_gap_watch_ratio": d("0.150000"),
        "liquidity_buffer_gap_block_ratio": d("0.400000"),
        "exit_cost_buffer_watch_ratio": d("0.250000"),
        "exit_cost_buffer_block_ratio": d("0.600000"),
        "settlement_delay_watch_hours": d("24.000000"),
        "settlement_delay_block_hours": d("72.000000"),
        "settlement_cost_load_weight": d("0.300000"),
        "liquidity_buffer_gap_weight": d("0.300000"),
        "exit_cost_buffer_weight": d("0.250000"),
        "settlement_delay_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchMarketSettlementLiquidityCostBufferConfig(**values)


def candidate(
    raw_candidate_id: str,
    *,
    observed_at: datetime = GENERATED_AT,
    settlement_cost_ratio: Decimal = d("0.050000"),
    liquidity_buffer_ratio: Decimal = d("0.150000"),
    projected_exit_cost_ratio: Decimal = d("0.050000"),
    settlement_delay_hours: Decimal = d("6.000000"),
    sensitive_context: str | None = (
        "candidate-id market-id market-slug settlement question "
        "https://example.invalid/source source text postgres://host/db "
        "fills_table token abc wallet order trade buy sell recommend"
    ),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketSettlementLiquidityCostBufferCandidate:
    return ResearchMarketSettlementLiquidityCostBufferCandidate(
        raw_candidate_id=raw_candidate_id,
        observed_at=observed_at,
        settlement_cost_ratio=settlement_cost_ratio,
        liquidity_buffer_ratio=liquidity_buffer_ratio,
        projected_exit_cost_ratio=projected_exit_cost_ratio,
        settlement_delay_hours=settlement_delay_hours,
        sensitive_context=sensitive_context,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchMarketSettlementLiquidityCostBufferCandidate,
    cfg: ResearchMarketSettlementLiquidityCostBufferConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketSettlementLiquidityCostBufferReport:
    return build_research_market_settlement_liquidity_cost_buffer_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def payload_with_fresh_digest(payload: dict[str, Any]) -> dict[str, Any]:
    refreshed = deepcopy(payload)
    unsigned = dict(refreshed)
    unsigned.pop("public_report_digest", None)
    canonical = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    refreshed["public_report_digest"] = sha256(canonical.encode("utf-8")).hexdigest()
    return refreshed


def test_combines_settlement_cost_liquidity_exit_and_delay_into_statuses() -> None:
    buffer_report = report(
        candidate("raw-pass"),
        candidate(
            "raw-watch",
            settlement_cost_ratio=d("0.250000"),
            liquidity_buffer_ratio=d("0.050000"),
            projected_exit_cost_ratio=d("0.300000"),
            settlement_delay_hours=d("30.000000"),
        ),
        candidate(
            "raw-block",
            settlement_cost_ratio=d("0.550000"),
            liquidity_buffer_ratio=d("0.050000"),
            projected_exit_cost_ratio=d("0.700000"),
            settlement_delay_hours=d("96.000000"),
        ),
    )

    assert type(buffer_report) is ResearchMarketSettlementLiquidityCostBufferReport
    assert buffer_report.generated_at == GENERATED_AT
    assert buffer_report.config_version == (
        DEFAULT_RESEARCH_MARKET_SETTLEMENT_LIQUIDITY_COST_BUFFER_CONFIG_VERSION
    )
    assert buffer_report.candidate_count == d("3.000000")
    assert buffer_report.pass_count == ONE
    assert buffer_report.watch_count == ONE
    assert buffer_report.block_count == ONE
    assert buffer_report.settlement_cost_load_count == d("2.000000")
    assert buffer_report.liquidity_buffer_gap_count == d("2.000000")
    assert buffer_report.exit_cost_buffer_count == d("2.000000")
    assert buffer_report.settlement_delay_pressure_count == d("2.000000")
    assert buffer_report.mean_liquidity_cost_buffer_score == d("0.516944")
    assert buffer_report.max_settlement_cost_ratio == d("0.550000")
    assert buffer_report.min_liquidity_buffer_ratio == d("0.050000")
    assert buffer_report.max_projected_exit_cost_ratio == d("0.700000")
    assert buffer_report.max_settlement_delay_hours == d("96.000000")
    assert buffer_report.status == "block"
    assert buffer_report.reason_codes == (
        "settlement_cost_load_detected",
        "liquidity_buffer_gap_detected",
        "exit_cost_buffer_detected",
        "settlement_delay_pressure_detected",
        "composite_liquidity_cost_buffer_detected",
    )
    assert buffer_report.paper_only is True
    assert buffer_report.report_only is True
    assert buffer_report.readonly is True

    first, second, third = buffer_report.rows
    assert type(first) is ResearchMarketSettlementLiquidityCostBufferRow
    assert tuple(row.status for row in buffer_report.rows) == ("block", "watch", "pass")
    assert first.row_number == ONE
    assert first.settlement_cost_load_score == ONE
    assert first.liquidity_buffer_gap_ratio == d("0.500000")
    assert first.liquidity_buffer_gap_score == ONE
    assert first.exit_cost_buffer_score == ONE
    assert first.settlement_delay_score == ONE
    assert first.liquidity_cost_buffer_score == ONE
    assert first.reason_codes == (
        "settlement_cost_load_blocking",
        "liquidity_buffer_gap_blocking",
        "exit_cost_buffer_blocking",
        "settlement_delay_pressure_blocking",
        "composite_liquidity_cost_buffer_blocking",
    )
    assert second.liquidity_buffer_gap_ratio == d("0.200000")
    assert second.liquidity_cost_buffer_score == d("0.487500")
    assert second.reason_codes == (
        "settlement_cost_load_watch",
        "liquidity_buffer_gap_watch",
        "exit_cost_buffer_watch",
        "settlement_delay_pressure_watch",
        "composite_liquidity_cost_buffer_watch",
    )
    assert third.liquidity_buffer_gap_ratio == ZERO
    assert third.liquidity_cost_buffer_score == d("0.063333")
    assert third.reason_codes == ("settlement_liquidity_cost_buffer_clear",)


def test_composite_score_boundaries_do_not_misclassify_statuses() -> None:
    pass_boundary = report(
        candidate(
            "raw-pass-boundary",
            settlement_cost_ratio=d("0.150000"),
            liquidity_buffer_ratio=d("0.050000"),
            projected_exit_cost_ratio=d("0.216000"),
            settlement_delay_hours=d("21.600000"),
        ),
    )

    pass_row = pass_boundary.rows[0]
    assert pass_row.liquidity_cost_buffer_score == d("0.300000")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("settlement_liquidity_cost_buffer_clear",)
    assert pass_boundary.status == "pass"

    watch_boundary = report(
        candidate(
            "raw-watch-boundary",
            settlement_cost_ratio=d("0.400000"),
            liquidity_buffer_ratio=d("0.120000"),
            projected_exit_cost_ratio=d("0.300000"),
            settlement_delay_hours=d("36.000000"),
        ),
    )

    watch_row = watch_boundary.rows[0]
    assert watch_row.liquidity_cost_buffer_score == d("0.650000")
    assert watch_row.status == "watch"
    assert "composite_liquidity_cost_buffer_watch" in watch_row.reason_codes
    assert "composite_liquidity_cost_buffer_blocking" not in watch_row.reason_codes
    assert watch_boundary.status == "watch"


def test_payload_digest_is_deterministic_public_safe_and_decimal_only() -> None:
    left = report(
        candidate("raw-z-pass"),
        candidate(
            "raw-a-block",
            settlement_cost_ratio=d("0.550000"),
            liquidity_buffer_ratio=d("0.050000"),
            projected_exit_cost_ratio=d("0.700000"),
            settlement_delay_hours=d("96.000000"),
        ),
        candidate(
            "raw-m-watch",
            settlement_cost_ratio=d("0.250000"),
            liquidity_buffer_ratio=d("0.050000"),
            projected_exit_cost_ratio=d("0.300000"),
            settlement_delay_hours=d("30.000000"),
        ),
    )
    right = report(
        candidate(
            "raw-m-watch",
            settlement_cost_ratio=d("0.250000"),
            liquidity_buffer_ratio=d("0.050000"),
            projected_exit_cost_ratio=d("0.300000"),
            settlement_delay_hours=d("30.000000"),
        ),
        candidate("raw-z-pass"),
        candidate(
            "raw-a-block",
            settlement_cost_ratio=d("0.550000"),
            liquidity_buffer_ratio=d("0.050000"),
            projected_exit_cost_ratio=d("0.700000"),
            settlement_delay_hours=d("96.000000"),
        ),
    )

    left_payload = research_market_settlement_liquidity_cost_buffer_report_payload(left)
    right_payload = research_market_settlement_liquidity_cost_buffer_report_payload(right)

    assert left_payload == right_payload
    assert research_market_settlement_liquidity_cost_buffer_digest(left) == (
        left.public_report_digest
    )
    assert left.public_report_digest == right.public_report_digest
    assert len(left.public_report_digest) == 64
    assert left_payload["candidate_count"] == "3.000000"
    assert left_payload["rows"][0]["liquidity_cost_buffer_score"] == "1.000000"
    assert_no_float(left_payload)
    json.dumps(left_payload, sort_keys=True)

    encoded = json.dumps(left_payload, sort_keys=True)
    for sensitive_value in (
        "raw-z-pass",
        "raw-a-block",
        "raw-m-watch",
        "candidate-id",
        "market-id",
        "market-slug",
        "settlement question",
        "https://example.invalid/source",
        "source text",
        "postgres://host/db",
        "fills_table",
        "token abc",
        "wallet order trade",
        "buy sell recommend",
    ):
        assert sensitive_value not in encoded
    for sensitive_key in (
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        assert sensitive_key not in encoded

    object.__setattr__(left, "public_report_digest", "0" * 64)
    with pytest.raises(ValueError, match="public_report_digest"):
        research_market_settlement_liquidity_cost_buffer_report_payload(left)


def test_public_payload_digest_covers_hard_flags_and_validator_round_trips() -> None:
    payload = research_market_settlement_liquidity_cost_buffer_report_payload(
        report(candidate("raw-validator-round-trip")),
    )
    unsigned = dict(payload)
    provided_digest = unsigned.pop("public_report_digest")
    canonical = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert provided_digest == sha256(canonical.encode("utf-8")).hexdigest()
    assert PAYLOAD_VALIDATOR_NAME in report_module.__all__
    validator = getattr(report_module, PAYLOAD_VALIDATOR_NAME)
    assert validator(payload) == payload


def test_public_payload_validator_rejects_schema_numeric_flag_and_unsafe_tampering() -> None:
    validator = getattr(report_module, PAYLOAD_VALIDATOR_NAME, None)
    assert validator is not None
    payload = research_market_settlement_liquidity_cost_buffer_report_payload(
        report(candidate("raw-validator-tamper")),
    )

    with pytest.raises(ValueError, match="payload must be a dict"):
        validator([])  # type: ignore[arg-type]

    digest_tampered = dict(payload)
    digest_tampered["candidate_count"] = "9.000000"
    with pytest.raises(ValueError, match="public_report_digest"):
        validator(digest_tampered)

    numeric_payload = payload_with_fresh_digest({**payload, "candidate_count": 1})
    with pytest.raises(ValueError, match="public payload numerics"):
        validator(numeric_payload)

    extra_field_payload = payload_with_fresh_digest(
        {**payload, "safe_extra_field": "unexpected"},
    )
    with pytest.raises(ValueError, match="schema"):
        validator(extra_field_payload)

    missing_field_payload = dict(payload)
    missing_field_payload.pop("status")
    with pytest.raises(ValueError, match="schema"):
        validator(payload_with_fresh_digest(missing_field_payload))

    nested_false_flag = deepcopy(payload)
    nested_false_flag["rows"][0]["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        validator(payload_with_fresh_digest(nested_false_flag))

    inconsistent_rollup = payload_with_fresh_digest(
        {**payload, "pass_count": "9.000000"},
    )
    with pytest.raises(ValueError, match="pass_count"):
        validator(inconsistent_rollup)

    noncanonical_row_number = deepcopy(payload)
    noncanonical_row_number["rows"][0]["row_number"] = "2.000000"
    with pytest.raises(ValueError, match="row_number"):
        validator(payload_with_fresh_digest(noncanonical_row_number))

    for unsafe_key in (
        "candidate_reference",
        "market_reference",
        "source_id",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token_id",
        "wallet_id",
        "order_id",
        "trade_id",
        "auth_token",
        "live_trading",
        "network_client",
        "database_name",
        "persist_result",
        "position_sizing",
        "recommendation",
        "execution",
    ):
        unsafe_payload = payload_with_fresh_digest(
            {**payload, unsafe_key: "forbidden"},
        )
        with pytest.raises(ValueError, match="unsafe public payload"):
            validator(unsafe_payload)

    unsafe_value_payload = payload_with_fresh_digest(
        {**payload, "config_version": "unsafe-wallet-identifier"},
    )
    with pytest.raises(ValueError, match="unsafe public payload"):
        validator(unsafe_value_payload)


def test_empty_inputs_block_with_public_reason_count() -> None:
    buffer_report = report()

    assert buffer_report.status == "block"
    assert buffer_report.candidate_count == ZERO
    assert buffer_report.reason_codes == (
        "no_settlement_liquidity_cost_buffer_candidates",
    )
    assert buffer_report.reason_code_counts == (
        ResearchMarketSettlementLiquidityCostBufferReasonCodeCount(
            reason_code="no_settlement_liquidity_cost_buffer_candidates",
            count=ONE,
        ),
    )
    assert buffer_report.rows == ()


def test_validation_rejects_non_decimal_bad_time_bad_status_and_flags() -> None:
    with pytest.raises(ValueError, match="settlement_delay_hours"):
        candidate("bad-int", settlement_delay_hours=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="projected_exit_cost_ratio"):
        candidate("bad-float", projected_exit_cost_ratio=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="settlement_cost_ratio"):
        candidate("bad-subclass", settlement_cost_ratio=_DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="observed_at"):
        candidate("bad-time", observed_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("ok"), generated_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate("subclass-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 14, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        candidate("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(candidate("flag-report")), readonly=False)
    with pytest.raises(ValueError, match="settlement_delay_block_hours must exceed"):
        config(settlement_delay_block_hours=d("24.000000"))

    buffer_report = report(candidate("status-check"))
    with pytest.raises(ValueError, match="status"):
        replace(buffer_report.rows[0], status="blocked")


def test_public_dataclasses_are_frozen_and_module_has_no_live_surfaces() -> None:
    buffer_report = report(candidate("frozen"))

    with pytest.raises(FrozenInstanceError):
        buffer_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        buffer_report.rows[0].liquidity_cost_buffer_score = d("0.500000")  # type: ignore[misc]

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
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
        "write_text",
        "write_bytes",
        "create_order",
        "cancel_order",
        "private_key",
        "api_key",
        "secret",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "urllib",
        "httpx",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "post",
        "request",
        "send",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)
