from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_liquidity_resolution_memory_ladder_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_market_liquidity_resolution_memory_ladder_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_LIQUIDITY_RESOLUTION_MEMORY_LADDER_REPORT_CONFIG_VERSION
        ),
        "minimum_pass_liquidity_score": d("0.800000"),
        "minimum_watch_liquidity_score": d("0.500000"),
        "minimum_pass_resolution_memory": d("0.800000"),
        "minimum_watch_resolution_memory": d("0.500000"),
        "minimum_pass_resolution_window_seconds": d("3600.000000"),
        "minimum_watch_resolution_window_seconds": d("900.000000"),
        "maximum_pass_pressure_score": d("0.200000"),
        "maximum_watch_pressure_score": d("0.600000"),
        "liquidity_score_weight": d("0.400000"),
        "resolution_memory_weight": d("0.400000"),
        "resolution_window_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchMarketLiquidityResolutionMemoryLadderConfig(**values)


def ladder_input(
    private_ref: str = "private-alpha",
    *,
    observed_at: datetime = GENERATED_AT,
    liquidity_score: Decimal = d("0.900000"),
    resolution_memory: Decimal = d("0.900000"),
    resolution_window_seconds: Decimal = d("7200.000000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketLiquidityResolutionMemoryLadderInput(
        private_ref=private_ref,
        observed_at=observed_at,
        liquidity_score=liquidity_score,
        resolution_memory=resolution_memory,
        resolution_window_seconds=resolution_window_seconds,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_market_liquidity_resolution_memory_ladder_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in payload_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in payload_values(child))
    return (value,)


def test_empty_report_is_pass_readonly_decimal_and_digest_validated() -> None:
    module = api()
    result = build_report()

    assert type(result) is module.ResearchMarketLiquidityResolutionMemoryLadderReport
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen is True
    assert result.generated_at == GENERATED_AT
    assert result.status == "pass"
    assert result.input_count == d("0.000000")
    assert result.row_count == d("0.000000")
    assert result.pass_count == d("0.000000")
    assert result.watch_count == d("0.000000")
    assert result.block_count == d("0.000000")
    assert result.average_ladder_score == d("0.000000")
    assert result.max_pressure_score == d("0.000000")
    assert result.min_liquidity_score == d("0.000000")
    assert result.min_resolution_memory == d("0.000000")
    assert result.min_resolution_window_seconds == d("0.000000")
    assert result.reason_codes == ("ladder_no_inputs",)
    assert result.reason_code_counts == ()
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]

    payload = module.research_market_liquidity_resolution_memory_ladder_report_payload(
        result,
    )
    assert payload == result.public_payload
    assert payload["generated_at"] == "2026-07-09T16:00:00+00:00"
    assert payload["input_count"] == "0.000000"
    assert payload["average_ladder_score"] == "0.000000"
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert json.dumps(payload, sort_keys=True)
    assert (
        module.validate_research_market_liquidity_resolution_memory_ladder_public_payload(
            payload,
        )
        == payload
    )
    _assert_no_public_float_or_int(payload)
    _assert_no_unsafe_public_fragments(payload)


def test_status_rollups_rows_and_payload_are_deterministic() -> None:
    module = api()
    unsafe_private_ref = (
        "raw-candidate-42/market-99/https://example.test/source"
        "?token=secret&dsn=hidden&table=markets"
    )
    first = build_report(
        ladder_input("pass-private"),
        ladder_input(
            unsafe_private_ref,
            liquidity_score=d("0.400000"),
            resolution_memory=d("0.200000"),
            resolution_window_seconds=d("600.000000"),
            reason_codes=("manual_review",),
        ),
        ladder_input(
            "watch-private",
            observed_at=datetime(2026, 7, 9, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
            liquidity_score=d("0.600000"),
            resolution_memory=d("0.650000"),
            resolution_window_seconds=d("1800.000000"),
        ),
    )
    second = build_report(
        ladder_input(
            "watch-private",
            liquidity_score=d("0.600000"),
            resolution_memory=d("0.650000"),
            resolution_window_seconds=d("1800.000000"),
        ),
        ladder_input(unsafe_private_ref, liquidity_score=d("0.400000"), resolution_memory=d("0.200000"), resolution_window_seconds=d("600.000000"), reason_codes=("manual_review",)),
        ladder_input("pass-private"),
    )

    assert module.LIQUIDITY_RESOLUTION_MEMORY_LADDER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert first.status == "block"
    assert first.input_count == d("3.000000")
    assert first.row_count == d("3.000000")
    assert first.pass_count == d("1.000000")
    assert first.watch_count == d("1.000000")
    assert first.block_count == d("1.000000")
    assert first.low_liquidity_count == d("2.000000")
    assert first.low_resolution_memory_count == d("2.000000")
    assert first.short_resolution_window_count == d("2.000000")
    assert first.average_ladder_score == d("0.575556")
    assert first.max_pressure_score == d("0.760000")
    assert first.min_liquidity_score == d("0.400000")
    assert first.min_resolution_memory == d("0.200000")
    assert first.min_resolution_window_seconds == d("600.000000")
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert {row.status for row in first.rows} <= {"pass", "watch", "block"}
    assert first.rows[0].reason_codes == (
        "input_manual_review",
        "ladder_liquidity_block",
        "ladder_memory_block",
        "ladder_resolution_window_block",
        "ladder_pressure_block",
        "ladder_status_block",
    )
    assert first.rows[1].reason_codes == (
        "ladder_liquidity_watch",
        "ladder_memory_watch",
        "ladder_resolution_window_watch",
        "ladder_pressure_watch",
        "ladder_status_watch",
    )
    assert first.rows[2].reason_codes == ("ladder_status_pass",)
    assert first.reason_codes == (
        "input_manual_review",
        "ladder_liquidity_watch",
        "ladder_liquidity_block",
        "ladder_memory_watch",
        "ladder_memory_block",
        "ladder_resolution_window_watch",
        "ladder_resolution_window_block",
        "ladder_pressure_watch",
        "ladder_pressure_block",
        "ladder_status_watch",
        "ladder_status_block",
    )
    assert first.reason_code_counts[0].reason_code == "input_manual_review"
    assert first.reason_code_counts[0].count == d("1.000000")

    first_payload = (
        module.research_market_liquidity_resolution_memory_ladder_report_payload(first)
    )
    second_payload = second.public_payload
    assert first_payload == second_payload
    assert not any(isinstance(value, Decimal) for value in payload_values(first_payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in payload_values(first_payload)
    )

    digest_payload = dict(first_payload)
    provided_digest = digest_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(digest_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert provided_digest == expected_digest
    assert (
        module.validate_research_market_liquidity_resolution_memory_ladder_public_payload(
            first_payload,
        )
        == first_payload
    )

    rendered = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "raw-candidate-42",
        "market-99",
        "https://example.test",
        "source?token",
        "secret",
        "dsn",
        "table",
        "pass-private",
        "watch-private",
    ):
        assert forbidden not in rendered
    _assert_no_unsafe_public_fragments(first_payload)


def test_dataclasses_are_frozen_exact_decimal_only_and_flags_are_hard() -> None:
    module = api()
    result = build_report(ladder_input("pass-private"))

    for cls in (
        module.ResearchMarketLiquidityResolutionMemoryLadderConfig,
        module.ResearchMarketLiquidityResolutionMemoryLadderInput,
        module.ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount,
        module.ResearchMarketLiquidityResolutionMemoryLadderRow,
        module.ResearchMarketLiquidityResolutionMemoryLadderReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    _assert_decimal_public_fields(result)
    for row in result.rows:
        _assert_decimal_public_fields(row)
    for item in result.reason_code_counts:
        _assert_decimal_public_fields(item)

    with pytest.raises(ValueError, match="liquidity_score"):
        ladder_input("bad-liquidity", liquidity_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolution_memory"):
        ladder_input("bad-memory", resolution_memory=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="resolution_window_seconds"):
        ladder_input("bad-window", resolution_window_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="liquidity_score_weight"):
        config(liquidity_score_weight=d("0.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        ladder_input("bad-flag", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)


def test_public_payload_validator_rejects_leaks_numerics_and_digest_tampering() -> None:
    module = api()
    payload = module.research_market_liquidity_resolution_memory_ladder_report_payload(
        build_report(ladder_input("watch-private", liquidity_score=d("0.600000"))),
    )

    assert (
        module.validate_research_market_liquidity_resolution_memory_ladder_public_payload(
            payload,
        )
        == payload
    )
    with pytest.raises(ValueError, match="unsafe public field"):
        module.validate_research_market_liquidity_resolution_memory_ladder_public_payload(
            {**payload, "candidate_id": "redacted"},
        )
    with pytest.raises(ValueError, match="unsafe public field"):
        module.validate_research_market_liquidity_resolution_memory_ladder_public_payload(
            {**payload, "market_slug": "redacted"},
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_research_market_liquidity_resolution_memory_ladder_public_payload(
            {**payload, "rows": [{**payload["rows"][0], "public_row_ref": "https://example.test"}]},
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_research_market_liquidity_resolution_memory_ladder_public_payload(
            {**payload, "input_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_liquidity_resolution_memory_ladder_public_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_liquidity_resolution_memory_ladder_public_payload(
            {**payload, "input_count": "9.000000"},
        )


def test_module_scope_is_report_only_readonly_and_forbidden_surface_free() -> None:
    module = api()

    assert set(module.__all__) == {
        "DEFAULT_RESEARCH_MARKET_LIQUIDITY_RESOLUTION_MEMORY_LADDER_REPORT_CONFIG_VERSION",
        "LIQUIDITY_RESOLUTION_MEMORY_LADDER_STATUSES",
        "ResearchMarketLiquidityResolutionMemoryLadderConfig",
        "ResearchMarketLiquidityResolutionMemoryLadderInput",
        "ResearchMarketLiquidityResolutionMemoryLadderReasonCodeCount",
        "ResearchMarketLiquidityResolutionMemoryLadderRow",
        "ResearchMarketLiquidityResolutionMemoryLadderReport",
        "build_research_market_liquidity_resolution_memory_ladder_report",
        "research_market_liquidity_resolution_memory_ladder_report_payload",
        "validate_research_market_liquidity_resolution_memory_ladder_public_payload",
    }

    tree = ast.parse(MODULE_PATH.read_text())
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    identifier_names: set[str] = set()
    string_values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Name):
            identifier_names.add(node.id)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_values.append(node.value)

    assert not imported_roots.intersection(
        {
            "requests",
            "urllib",
            "httpx",
            "socket",
            "websocket",
            "psycopg",
            "sqlite3",
            "sqlalchemy",
            "supabase",
            "subprocess",
        },
    )
    assert not called_names.intersection(
        {
            "open",
            "connect",
            "request",
            "post",
            "put",
            "patch",
            "delete",
            "execute",
            "commit",
            "rollback",
            "place_order",
            "submit_order",
            "cancel_order",
            "recommend",
        },
    )
    forbidden_identifiers = {
        "auth",
        "database",
        "dsn",
        "live_trading",
        "network_client",
        "order_client",
        "order_size",
        "recommendation",
        "source_text",
        "source_url",
        "table",
        "token",
        "wallet",
    }
    assert not identifier_names.intersection(forbidden_identifiers)
    assert not any(_has_forbidden_literal_fragment(value) for value in string_values)


def _assert_decimal_public_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal


def _assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_public_float_or_int(item)


def _assert_no_unsafe_public_fragments(value: Any) -> None:
    if isinstance(value, str):
        assert not _has_forbidden_literal_fragment(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            assert not _has_forbidden_literal_fragment(key)
            _assert_no_unsafe_public_fragments(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_unsafe_public_fragments(item)


def _has_forbidden_literal_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(
        fragment in normalized
        for fragment in (
            "://",
            "api_key",
            "auth",
            "candidate_id",
            "database",
            "dsn",
            "live trading",
            "market_id",
            "market_slug",
            "order",
            "private_key",
            "question",
            "recommendation",
            "source text",
            "source url",
            "table",
            "token",
            "wallet",
        )
    )
