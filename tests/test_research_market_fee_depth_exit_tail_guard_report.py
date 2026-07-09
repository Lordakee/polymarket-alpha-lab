from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_fee_depth_exit_tail_guard_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_FEE_DEPTH_EXIT_TAIL_GUARD_REPORT_CONFIG_VERSION
        ),
        "max_pass_exit_shortfall_ratio": d("0.050000"),
        "max_watch_exit_shortfall_ratio": d("0.250000"),
        "max_pass_fee_depth_burden_ratio": d("0.010000"),
        "max_watch_fee_depth_burden_ratio": d("0.030000"),
        "max_pass_tail_pressure_score": d("0.100000"),
        "max_watch_tail_pressure_score": d("0.350000"),
        "max_pass_stale_depth_age_seconds": d("120.000000"),
        "max_watch_stale_depth_age_seconds": d("600.000000"),
        "max_pass_manual_guard_pressure": d("0.200000"),
        "max_watch_manual_guard_pressure": d("0.600000"),
        "pass_guard_score": d("0.750000"),
        "watch_guard_score": d("0.450000"),
        "depth_coverage_weight": d("0.350000"),
        "fee_depth_weight": d("0.200000"),
        "tail_pressure_weight": d("0.200000"),
        "freshness_weight": d("0.150000"),
        "manual_pressure_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchMarketFeeDepthExitTailGuardConfig(**values)


def observation(
    research_case_key: str = "case-pass",
    *,
    observed_at: datetime | None = None,
    last_depth_update_at: datetime | None = None,
    exit_exposure_probability: Decimal = d("0.100000"),
    near_exit_depth: Decimal = d("0.080000"),
    far_exit_depth: Decimal = d("0.030000"),
    taker_fee_bps: Decimal = d("10.000000"),
    spread_bps: Decimal = d("20.000000"),
    tail_loss_probability: Decimal = d("0.100000"),
    tail_loss_impact: Decimal = d("0.500000"),
    manual_guard_pressure: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketFeeDepthExitTailGuardObservation(
        research_case_key=research_case_key,
        observed_at=observed_at or GENERATED_AT - timedelta(seconds=45),
        last_depth_update_at=last_depth_update_at
        or GENERATED_AT - timedelta(seconds=45),
        exit_exposure_probability=exit_exposure_probability,
        near_exit_depth=near_exit_depth,
        far_exit_depth=far_exit_depth,
        taker_fee_bps=taker_fee_bps,
        spread_bps=spread_bps,
        tail_loss_probability=tail_loss_probability,
        tail_loss_impact=tail_loss_impact,
        manual_guard_pressure=manual_guard_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: Any | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_market_fee_depth_exit_tail_guard_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_empty_input_blocks_fee_depth_exit_tail_guard_review() -> None:
    module = api()
    guard_report = report()

    assert module.FEE_DEPTH_EXIT_TAIL_GUARD_STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_MARKET_FEE_DEPTH_EXIT_TAIL_GUARD_REPORT_CONFIG_VERSION",
        "FEE_DEPTH_EXIT_TAIL_GUARD_STATUSES",
        "ResearchMarketFeeDepthExitTailGuardConfig",
        "ResearchMarketFeeDepthExitTailGuardObservation",
        "ResearchMarketFeeDepthExitTailGuardReasonCodeCount",
        "ResearchMarketFeeDepthExitTailGuardReport",
        "ResearchMarketFeeDepthExitTailGuardRow",
        "build_research_market_fee_depth_exit_tail_guard_report",
        "research_market_fee_depth_exit_tail_guard_report_digest",
        "research_market_fee_depth_exit_tail_guard_report_payload",
    )
    assert type(guard_report) is module.ResearchMarketFeeDepthExitTailGuardReport
    assert is_dataclass(guard_report)
    assert guard_report.generated_at == GENERATED_AT
    assert (
        guard_report.config_version
        == "research-market-fee-depth-exit-tail-guard-report-v0"
    )
    assert guard_report.input_count == ZERO
    assert guard_report.pass_count == ZERO
    assert guard_report.watch_count == ZERO
    assert guard_report.block_count == ZERO
    assert guard_report.average_exit_tail_guard_score is None
    assert guard_report.min_depth_coverage_ratio == ZERO
    assert guard_report.max_exit_shortfall_ratio == ZERO
    assert guard_report.max_fee_depth_burden_ratio == ZERO
    assert guard_report.max_tail_pressure_score == ZERO
    assert guard_report.max_stale_depth_age_seconds == ZERO
    assert guard_report.max_manual_guard_pressure == ZERO
    assert guard_report.status == "block"
    assert guard_report.reason_codes == ("no_fee_depth_exit_tail_guard_observations",)
    assert guard_report.reason_code_counts == (
        module.ResearchMarketFeeDepthExitTailGuardReasonCodeCount(
            reason_code="no_fee_depth_exit_tail_guard_observations",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert guard_report.rows == ()
    assert guard_report.paper_only is True
    assert guard_report.report_only is True
    assert guard_report.readonly is True


def test_scores_pass_watch_and_block_fee_depth_exit_tail_observations() -> None:
    guard_report = report(
        observation(
            "case-watch",
            last_depth_update_at=GENERATED_AT - timedelta(seconds=180),
            near_exit_depth=d("0.050000"),
            far_exit_depth=d("0.040000"),
            taker_fee_bps=d("20.000000"),
            spread_bps=d("30.000000"),
            tail_loss_probability=d("0.300000"),
            tail_loss_impact=d("0.600000"),
            manual_guard_pressure=d("0.300000"),
        ),
        observation(
            "case-block",
            last_depth_update_at=GENERATED_AT - timedelta(seconds=700),
            near_exit_depth=d("0.030000"),
            far_exit_depth=d("0.020000"),
            taker_fee_bps=d("100.000000"),
            spread_bps=d("250.000000"),
            tail_loss_probability=d("0.700000"),
            tail_loss_impact=d("0.600000"),
            manual_guard_pressure=d("0.800000"),
            reason_codes=("manual_guard_review",),
        ),
        observation("case-pass"),
    )

    assert guard_report.input_count == d("3.000000")
    assert guard_report.pass_count == d("1.000000")
    assert guard_report.watch_count == d("1.000000")
    assert guard_report.block_count == d("1.000000")
    assert guard_report.average_exit_tail_guard_score == d("0.564107")
    assert guard_report.min_depth_coverage_ratio == d("0.150000")
    assert guard_report.max_exit_shortfall_ratio == d("0.850000")
    assert guard_report.max_fee_depth_burden_ratio == d("0.035000")
    assert guard_report.max_tail_pressure_score == d("0.420000")
    assert guard_report.max_stale_depth_age_seconds == d("700.000000")
    assert guard_report.max_manual_guard_pressure == d("0.800000")
    assert guard_report.status == "block"

    block_row, pass_row, watch_row = guard_report.rows
    assert tuple(row.guard_group_ref for row in guard_report.rows) == (
        "fee_depth_tail_guard_001",
        "fee_depth_tail_guard_002",
        "fee_depth_tail_guard_003",
    )
    assert tuple(row.status for row in guard_report.rows) == (
        "block",
        "pass",
        "watch",
    )
    assert block_row.total_exit_depth == d("0.050000")
    assert block_row.fee_depth_burden_ratio == d("0.035000")
    assert block_row.net_exit_depth == d("0.015000")
    assert block_row.depth_coverage_ratio == d("0.150000")
    assert block_row.exit_shortfall_ratio == d("0.850000")
    assert block_row.tail_pressure_score == d("0.420000")
    assert block_row.stale_depth_pressure == d("1.000000")
    assert block_row.exit_tail_guard_score == d("0.052500")
    assert block_row.reason_codes == (
        "exit_depth_shortfall_block",
        "fee_depth_burden_block",
        "exit_tail_pressure_block",
        "stale_depth_age_block",
        "manual_guard_pressure_block",
        "exit_tail_guard_score_block",
        "input_manual_guard_review",
    )
    assert pass_row.depth_coverage_ratio == d("1.000000")
    assert pass_row.exit_shortfall_ratio == ZERO
    assert pass_row.fee_depth_burden_ratio == d("0.003000")
    assert pass_row.tail_pressure_score == d("0.050000")
    assert pass_row.stale_depth_age_seconds == d("45.000000")
    assert pass_row.exit_tail_guard_score == d("0.923512")
    assert pass_row.reason_codes == (
        "exit_depth_shortfall_pass",
        "fee_depth_burden_pass",
        "exit_tail_pressure_pass",
        "stale_depth_age_pass",
        "manual_guard_pressure_pass",
        "exit_tail_guard_score_pass",
    )
    assert watch_row.depth_coverage_ratio == d("0.850000")
    assert watch_row.exit_shortfall_ratio == d("0.150000")
    assert watch_row.fee_depth_burden_ratio == d("0.005000")
    assert watch_row.tail_pressure_score == d("0.180000")
    assert watch_row.stale_depth_pressure == d("0.300000")
    assert watch_row.exit_tail_guard_score == d("0.716310")
    assert watch_row.reason_codes == (
        "exit_depth_shortfall_watch",
        "fee_depth_burden_pass",
        "exit_tail_pressure_watch",
        "stale_depth_age_watch",
        "manual_guard_pressure_watch",
        "exit_tail_guard_score_watch",
    )


def test_payload_and_digest_are_deterministic_decimal_strings_and_public_safe() -> None:
    module = api()
    first = report(
        observation("case-z", reason_codes=("zeta", "alpha")),
        observation("case-a"),
    )
    second = report(
        observation("case-a"),
        observation("case-z", reason_codes=("alpha", "zeta")),
    )

    first_payload = module.research_market_fee_depth_exit_tail_guard_report_payload(first)
    second_payload = module.research_market_fee_depth_exit_tail_guard_report_payload(
        second,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert module.research_market_fee_depth_exit_tail_guard_report_digest(first) == (
        module.research_market_fee_depth_exit_tail_guard_report_digest(second)
    )
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert len(first_payload["derived_validation_digest"]) == 64
    int(first_payload["derived_validation_digest"], 16)
    assert first_payload["rows"][0]["guard_group_ref"] == "fee_depth_tail_guard_001"
    assert first_payload["rows"][0]["exit_exposure_probability"] == "0.100000"
    assert first_payload["rows"][0]["depth_coverage_ratio"] == "1.000000"
    assert first_payload["rows"][0]["exit_tail_guard_score"] == "0.923512"
    assert not any(_is_numeric_payload_value(value) for value in _walk_values(first_payload))
    assert ": 0." not in encoded
    assert "case-a" not in encoded
    assert "case-z" not in encoded
    assert not any(_has_forbidden_public_surface_key(key) for key in _walk_keys(first_payload))
    assert module.research_market_fee_depth_exit_tail_guard_report_payload(
        dict(first_payload),
    ) == first_payload

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_fee_depth_exit_tail_guard_report_payload(tampered)
    with pytest.raises(ValueError, match="public payload numerics"):
        module.research_market_fee_depth_exit_tail_guard_report_payload(
            {**first_payload, "input_count": 2},
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.research_market_fee_depth_exit_tail_guard_report_payload(
            {**first_payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_market_fee_depth_exit_tail_guard_report_payload(
            {**first_payload, "wallet_address": "0xabc"},
        )


def test_validation_rejects_non_decimal_values_bad_flags_and_digest_tampering() -> None:
    module = api()
    populated = report(observation())

    for value in (config(), observation(), populated, *populated.rows, *populated.reason_code_counts):
        assert is_dataclass(value)
    with pytest.raises(FrozenInstanceError):
        populated.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        populated.rows[0].exit_tail_guard_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="exit_exposure_probability"):
        observation(exit_exposure_probability=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="near_exit_depth"):
        observation(near_exit_depth=DecimalSubclass("0.080000"))
    with pytest.raises(ValueError, match="exit depth"):
        observation(near_exit_depth=ZERO, far_exit_depth=ZERO)
    with pytest.raises(ValueError, match="tail_loss_probability"):
        observation(tail_loss_probability=d("1.010000"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            observation(),
            generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="unsafe public"):
        observation(reason_codes=("market_id",))
    with pytest.raises(ValueError, match="safe public identifier"):
        observation(reason_codes=("postgres:localhost",))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="research_case_key"):
        report(observation("duplicate"), observation("duplicate"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(populated, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(populated.rows[0], status="blocked")
    with pytest.raises(TypeError):
        type("ConfigSubclass", (module.ResearchMarketFeeDepthExitTailGuardConfig,), {})


def test_owned_module_has_no_external_or_decision_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_fee_depth_exit_tail_guard_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "postgres",
        "supabase",
        "private_key",
        "place_order",
        "cancel_order",
        "order_size",
        "live_trading",
        "trade_recommendation",
        "connect(",
        "open(",
    )

    assert all(term not in source for term in forbidden_terms)

    tree = ast.parse(source)
    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
        "connect",
        "execute",
        "fetch",
        "submit",
        "cancel",
        "order",
        "trade",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")


def _walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_values(item))
    else:
        values.append(value)
    return tuple(values)


def _walk_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(str(key))
            keys.extend(_walk_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_keys(item))
    return tuple(keys)


def _is_numeric_payload_value(value: object) -> bool:
    return isinstance(value, float) or type(value) is int or isinstance(value, Decimal)


def _has_forbidden_public_surface_key(key: str) -> bool:
    normalized = key.lower()
    forbidden_fragments = (
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "size",
        "sizing",
        "recommendation",
    )
    return any(fragment in normalized for fragment in forbidden_fragments)
