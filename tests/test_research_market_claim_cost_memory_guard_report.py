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


MODULE_NAME = "polymarket_alpha_lab.research_market_claim_cost_memory_guard_report"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_market_claim_cost_memory_guard_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 14, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_CLAIM_COST_MEMORY_GUARD_REPORT_CONFIG_VERSION
        ),
        "maximum_pass_claim_cost_rate": d("0.020000"),
        "maximum_watch_claim_cost_rate": d("0.050000"),
        "minimum_pass_memory_hit_count": d("3.000000"),
        "minimum_watch_memory_hit_count": d("1.000000"),
        "maximum_pass_memory_loss_rate": d("0.100000"),
        "maximum_watch_memory_loss_rate": d("0.250000"),
        "minimum_pass_memory_confidence_score": d("0.750000"),
        "minimum_watch_memory_confidence_score": d("0.500000"),
        "claim_cost_weight": d("0.350000"),
        "memory_depth_weight": d("0.200000"),
        "memory_loss_weight": d("0.250000"),
        "memory_confidence_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchMarketClaimCostMemoryGuardConfig(**values)


def claim_input(
    private_claim_ref: str = "private-alpha",
    *,
    observed_at: datetime = OBSERVED_AT,
    claim_cost_rate: Decimal = d("0.010000"),
    memory_hit_count: Decimal = d("5.000000"),
    memory_loss_rate: Decimal = d("0.050000"),
    memory_confidence_score: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketClaimCostMemoryGuardInput(
        private_claim_ref=private_claim_ref,
        observed_at=observed_at,
        claim_cost_rate=claim_cost_rate,
        memory_hit_count=memory_hit_count,
        memory_loss_rate=memory_loss_rate,
        memory_confidence_score=memory_confidence_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: object, cfg: object | None = None) -> Any:
    module = api()
    return module.build_research_market_claim_cost_memory_guard_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=GENERATED_AT,
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(
            item for nested in value.values() for item in walk_payload_values(nested)
        )
    if isinstance(value, list):
        return tuple(item for nested in value for item in walk_payload_values(nested))
    return (value,)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_scores_claim_cost_memory_guard_pass_watch_and_block_rows() -> None:
    module = api()
    result = build_report(
        claim_input(
            "block-private",
            claim_cost_rate=d("0.060000"),
            memory_hit_count=ZERO,
            memory_loss_rate=d("0.300000"),
            memory_confidence_score=d("0.400000"),
            reason_codes=("manual_check",),
        ),
        claim_input(
            "watch-private",
            claim_cost_rate=d("0.035000"),
            memory_hit_count=d("2.000000"),
            memory_loss_rate=d("0.175000"),
            memory_confidence_score=d("0.625000"),
        ),
        claim_input("pass-private"),
    )

    assert module.CLAIM_COST_MEMORY_GUARD_STATUSES == ("pass", "watch", "block")
    assert type(result) is module.ResearchMarketClaimCostMemoryGuardReport
    assert result.generated_at == GENERATED_AT
    assert result.status == "block"
    assert result.input_count == d("3.000000")
    assert result.row_count == d("3.000000")
    assert result.pass_count == ONE
    assert result.watch_count == ONE
    assert result.block_count == ONE
    assert result.high_claim_cost_count == d("2.000000")
    assert result.low_memory_depth_count == d("2.000000")
    assert result.high_memory_loss_count == d("2.000000")
    assert result.low_memory_confidence_count == d("2.000000")
    assert result.average_guard_score == d("0.500000")
    assert result.max_claim_cost_rate == d("0.060000")
    assert result.min_memory_hit_count == ZERO
    assert result.max_memory_loss_rate == d("0.300000")
    assert result.min_memory_confidence_score == d("0.400000")

    block_row, watch_row, pass_row = result.rows
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.public_row_ref for row in result.rows) == (
        "claim_cost_memory_guard_row_001",
        "claim_cost_memory_guard_row_002",
        "claim_cost_memory_guard_row_003",
    )
    assert block_row.guard_score == ZERO
    assert block_row.reason_codes == (
        "claim_cost_memory_guard_status_block",
        "claim_cost_rate_block",
        "claim_memory_confidence_block",
        "claim_memory_depth_block",
        "claim_memory_loss_block",
        "input_manual_check",
    )
    assert watch_row.claim_cost_score == d("0.500000")
    assert watch_row.memory_depth_score == d("0.500000")
    assert watch_row.memory_loss_score == d("0.500000")
    assert watch_row.memory_confidence_component_score == d("0.500000")
    assert watch_row.guard_score == d("0.500000")
    assert pass_row.guard_score == ONE
    assert pass_row.reason_codes == (
        "claim_cost_memory_guard_status_pass",
        "claim_cost_rate_pass",
        "claim_memory_confidence_pass",
        "claim_memory_depth_pass",
        "claim_memory_loss_pass",
    )


def test_public_payload_is_deterministic_digest_bound_decimal_only_and_safe() -> None:
    module = api()
    private_ref = (
        "raw candidate-alpha market-alpha source_url=https://example.invalid "
        "source_text=secret dsn=postgres table=events token=secret wallet order "
        "live trading sizing recommendation"
    )
    first = build_report(
        claim_input(
            private_ref,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            claim_cost_rate=d("0.060000"),
            memory_hit_count=ZERO,
            memory_loss_rate=d("0.300000"),
            memory_confidence_score=d("0.400000"),
        ),
    )
    second = build_report(
        claim_input(
            private_ref,
            claim_cost_rate=d("0.060000"),
            memory_hit_count=ZERO,
            memory_loss_rate=d("0.300000"),
            memory_confidence_score=d("0.400000"),
        ),
    )

    payload = module.research_market_claim_cost_memory_guard_report_payload(first)
    digest_payload = dict(payload)
    provided_digest = digest_payload.pop("derived_validation_digest")
    encoded_digest_payload = json.dumps(
        digest_payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    encoded_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload == module.research_market_claim_cost_memory_guard_report_payload(
        second,
    )
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert provided_digest == hashlib.sha256(
        encoded_digest_payload.encode("utf-8"),
    ).hexdigest()
    assert module.research_market_claim_cost_memory_guard_report_digest(first) == (
        first.derived_validation_digest
    )
    assert payload["generated_at"] == "2026-07-09T15:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["claim_cost_rate"] == "0.060000"
    assert payload["rows"][0]["claim_ref_digest"] == first.rows[0].claim_ref_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert private_ref not in encoded_payload
    assert all(
        fragment not in encoded_payload.lower()
        for fragment in (
            "candidate-alpha",
            "market-alpha",
            "source_url",
            "source_text",
            "https://example.invalid",
            "dsn=postgres",
            "table=events",
            "token=secret",
            "wallet",
            "order",
            "live",
            "trading",
            "sizing",
            "recommendation",
        )
    )
    assert not any(isinstance(value, Decimal) for value in walk_payload_values(payload))
    assert not any(
        isinstance(value, (float, int)) and not isinstance(value, bool)
        for value in walk_payload_values(payload)
    )


def test_payload_validation_rejects_tampering_numeric_literals_and_unsafe_surfaces() -> None:
    module = api()
    payload = module.research_market_claim_cost_memory_guard_report_payload(
        build_report(claim_input("private-payload")),
    )

    assert module.validate_research_market_claim_cost_memory_guard_report_payload(
        payload,
    ) == payload
    assert module.research_market_claim_cost_memory_guard_report_payload(payload) == payload

    tampered = dict(payload, pass_count="0.000000")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_claim_cost_memory_guard_report_payload(tampered)

    numeric_literal = dict(payload, row_count=1)
    with pytest.raises(ValueError, match="Decimal-derived string"):
        module.validate_research_market_claim_cost_memory_guard_report_payload(
            numeric_literal,
        )

    unsafe_key = dict(payload)
    unsafe_key["source_url"] = "https://example.invalid"
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_research_market_claim_cost_memory_guard_report_payload(
            unsafe_key,
        )


def test_validation_enforces_frozen_decimal_only_flags_statuses_and_digest() -> None:
    module = api()
    result = build_report(claim_input("private-validation"))

    for item in (config(), claim_input(), result, *result.reason_code_counts, *result.rows):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].guard_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        claim_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="claim_cost_rate"):
        claim_input(claim_cost_rate=0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_hit_count"):
        claim_input(memory_hit_count=DecimalSubclass("5.000000"))
    with pytest.raises(ValueError, match="memory_loss_rate"):
        claim_input(memory_loss_rate=d("1.100000"))
    with pytest.raises(ValueError, match="observed_at"):
        claim_input(observed_at=datetime(2026, 7, 9, 14, 45))
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_market_claim_cost_memory_guard_report(
            (),
            config=config(),
            generated_at=DatetimeSubclass(2026, 7, 9, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="private_claim_ref values"):
        build_report(claim_input("dupe"), claim_input("dupe"))
    with pytest.raises(ValueError, match="status"):
        replace(result.rows[0], status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="maximum_pass_claim_cost_rate"):
        config(maximum_pass_claim_cost_rate=DecimalSubclass("0.020000"))
    with pytest.raises(ValueError, match="maximum_pass_claim_cost_rate"):
        config(maximum_pass_claim_cost_rate=d("0.060000"))
    with pytest.raises(ValueError, match="minimum_pass_memory_hit_count"):
        config(minimum_pass_memory_hit_count=d("0.500000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(claim_cost_weight=d("0.360000"))
    with pytest.raises(ValueError, match="reason_codes"):
        claim_input(reason_codes=("token_seen",))

    public_classes = (
        module.ResearchMarketClaimCostMemoryGuardConfig,
        module.ResearchMarketClaimCostMemoryGuardInput,
        module.ResearchMarketClaimCostMemoryGuardRow,
        module.ResearchMarketClaimCostMemoryGuardReasonCodeCount,
        module.ResearchMarketClaimCostMemoryGuardReport,
    )
    for klass in public_classes:
        assert klass.__dataclass_params__.frozen is True
        for field in fields(klass):
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "config_version",
                "private_claim_ref",
                "claim_ref_digest",
                "public_row_ref",
                "status",
                "reason_code",
                "reason_codes",
                "reason_code_counts",
                "rows",
                "derived_validation_digest",
                "observed_at",
                "generated_at",
            }:
                continue
            assert field.type in (Decimal, "Decimal")


def test_empty_input_blocks_without_private_reference_surface() -> None:
    result = build_report()

    assert result.input_count == ZERO
    assert result.row_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.average_guard_score == ZERO
    assert result.max_claim_cost_rate == ZERO
    assert result.min_memory_hit_count == ZERO
    assert result.max_memory_loss_rate == ZERO
    assert result.min_memory_confidence_score == ZERO
    assert result.status == "block"
    assert result.rows == ()
    assert result.reason_codes == ("claim_cost_memory_guard_no_inputs",)
    assert_digest(result.derived_validation_digest)


def test_owned_module_has_no_runtime_side_effect_or_decision_surface() -> None:
    module = api()
    module_text = MODULE_PATH.read_text(encoding="utf-8").lower()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))

    assert module.__all__ == (
        "CLAIM_COST_MEMORY_GUARD_STATUSES",
        "DEFAULT_RESEARCH_MARKET_CLAIM_COST_MEMORY_GUARD_REPORT_CONFIG_VERSION",
        "ResearchMarketClaimCostMemoryGuardConfig",
        "ResearchMarketClaimCostMemoryGuardInput",
        "ResearchMarketClaimCostMemoryGuardReasonCodeCount",
        "ResearchMarketClaimCostMemoryGuardReport",
        "ResearchMarketClaimCostMemoryGuardRow",
        "build_research_market_claim_cost_memory_guard_report",
        "research_market_claim_cost_memory_guard_report_digest",
        "research_market_claim_cost_memory_guard_report_payload",
        "validate_research_market_claim_cost_memory_guard_report_payload",
    )
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "read_text",
        "write_text",
        "connect(",
        "execute(",
        "database",
        "network",
        "db",
        "wallet",
        "auth",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in module_text

    forbidden_calls = {
        "open",
        "connect",
        "execute",
        "request",
        "create_order",
        "submit_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
