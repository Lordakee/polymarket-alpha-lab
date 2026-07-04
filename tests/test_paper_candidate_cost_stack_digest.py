from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "paper_candidate_cost_stack_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 3, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.paper_candidate_cost_stack_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "paper-candidate-cost-stack-digest-v0",
        "watch_net_probability_edge": d("0.030000"),
        "max_pass_cost_to_edge_ratio": d("0.500000"),
        "max_watch_cost_to_edge_ratio": d("0.750000"),
    }
    values.update(overrides)
    return module.PaperCandidateCostStackDigestConfig(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "public-alpha",
        "market_slug": "alpha-market",
        "observed_at": OBSERVED_AT,
        "expected_probability_edge": d("0.100000"),
        "fee_probability_cost": d("0.010000"),
        "spread_probability_cost": d("0.010000"),
        "slippage_probability_cost": d("0.010000"),
        "gas_probability_cost": d("0.005000"),
        "settlement_probability_cost": d("0.005000"),
        "reason_codes": ("candidate_positive_edge",),
    }
    values.update(overrides)
    return module.PaperCandidateCostStackDigestCandidate(**values)


def report(*, candidates=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_paper_candidate_cost_stack_digest(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_digest_scores_candidate_cost_stack_and_orders_by_risk() -> None:
    result = report(
        candidates=(
            candidate(
                candidate_reference="pass-alpha",
                market_slug="gamma-pass",
                expected_probability_edge=d("0.100000"),
                fee_probability_cost=d("0.010000"),
                spread_probability_cost=d("0.010000"),
                slippage_probability_cost=d("0.010000"),
                gas_probability_cost=d("0.005000"),
                settlement_probability_cost=d("0.005000"),
            ),
            candidate(
                candidate_reference="watch-alpha",
                market_slug="beta-watch",
                expected_probability_edge=d("0.070000"),
                fee_probability_cost=d("0.010000"),
                spread_probability_cost=d("0.010000"),
                slippage_probability_cost=d("0.010000"),
                gas_probability_cost=d("0.005000"),
                settlement_probability_cost=d("0.005000"),
            ),
            candidate(
                candidate_reference="secret-wallet-token-alpha",
                market_slug="alpha-blocked",
                expected_probability_edge=d("0.050000"),
                fee_probability_cost=d("0.010000"),
                spread_probability_cost=d("0.020000"),
                slippage_probability_cost=d("0.020000"),
                gas_probability_cost=d("0.005000"),
                settlement_probability_cost=d("0.005000"),
            ),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "paper-candidate-cost-stack-digest-v0"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.total_probability_cost == d("0.140000")
    assert result.max_total_probability_cost == d("0.060000")
    assert result.min_net_probability_edge == d("-0.010000")
    assert result.max_cost_to_edge_ratio == d("1.200000")
    assert result.max_edge_shortfall == d("0.010000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "cost_stack_blocked",
        "cost_stack_passed",
        "cost_stack_watch",
        "fee_cost_present",
        "gas_cost_present",
        "settlement_cost_present",
        "slippage_cost_present",
        "spread_cost_present",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.cost_stack_status for row in result.rows) == (
        "blocked",
        "watch",
        "pass",
    )
    blocked, watched, passed = result.rows

    assert blocked.redacted_candidate_reference.startswith("candidate_ref_")
    assert "secret" not in blocked.redacted_candidate_reference
    assert "wallet" not in blocked.redacted_candidate_reference
    assert "token" not in blocked.redacted_candidate_reference
    assert blocked.market_slug == "alpha-blocked"
    assert blocked.total_probability_cost == d("0.060000")
    assert blocked.net_probability_edge == d("-0.010000")
    assert blocked.cost_to_edge_ratio == d("1.200000")
    assert blocked.edge_shortfall == d("0.010000")
    assert blocked.reason_codes == (
        "candidate_positive_edge",
        "cost_stack_blocked",
        "fee_cost_present",
        "spread_cost_present",
        "slippage_cost_present",
        "gas_cost_present",
        "settlement_cost_present",
    )

    assert watched.cost_stack_status == "watch"
    assert watched.total_probability_cost == d("0.040000")
    assert watched.net_probability_edge == d("0.030000")
    assert watched.cost_to_edge_ratio == d("0.571429")
    assert watched.edge_shortfall == ZERO
    assert "cost_stack_watch" in watched.reason_codes

    assert passed.cost_stack_status == "pass"
    assert passed.total_probability_cost == d("0.040000")
    assert passed.net_probability_edge == d("0.060000")
    assert passed.cost_to_edge_ratio == d("0.400000")
    assert passed.edge_shortfall == ZERO
    assert passed.reason_codes == (
        "candidate_positive_edge",
        "cost_stack_passed",
        "fee_cost_present",
        "spread_cost_present",
        "slippage_cost_present",
        "gas_cost_present",
        "settlement_cost_present",
    )


def test_empty_report_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.total_probability_cost == ZERO
    assert empty.max_total_probability_cost == ZERO
    assert empty.min_net_probability_edge == ZERO
    assert empty.max_cost_to_edge_ratio == ZERO
    assert empty.max_edge_shortfall == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("cost_stack_digest_empty",)
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(candidates=(candidate(),))
    for value in (empty, *populated.rows, populated):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_cost",
                    "_edge",
                    "_ratio",
                    "_shortfall",
                    "_probability",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_redacts_references_uses_decimal_strings_and_no_floats() -> None:
    module = api()
    result = report(
        candidates=(
            candidate(
                candidate_reference="secret-wallet-token-alpha",
                market_slug="payload-market",
                expected_probability_edge=d("0.050000"),
                fee_probability_cost=d("0.010000"),
                spread_probability_cost=d("0.020000"),
                slippage_probability_cost=d("0.020000"),
                gas_probability_cost=d("0.005000"),
                settlement_probability_cost=d("0.005000"),
            ),
        ),
        generated_at=datetime(2026, 7, 3, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.paper_candidate_cost_stack_digest_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["total_probability_cost"] == "0.060000"
    assert payload["max_cost_to_edge_ratio"] == "1.200000"
    assert payload["rows"][0]["redacted_candidate_reference"].startswith(
        "candidate_ref_",
    )
    assert payload["rows"][0]["total_probability_cost"] == "0.060000"
    assert payload["rows"][0]["net_probability_edge"] == "-0.010000"
    assert "secret" not in rendered
    assert "wallet" not in rendered
    assert "token" not in rendered
    assert_no_float_values(payload)


def test_validation_rejects_bad_types_precision_duplicates_dates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_paper_candidate_cost_stack_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="Decimal"):
        candidate(expected_probability_edge=0.1)
    with pytest.raises(ValueError, match="six decimal"):
        candidate(fee_probability_cost=d("0.0000001"))
    with pytest.raises(ValueError, match="datetime"):
        candidate(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        candidate(observed_at=datetime(2026, 7, 3, 11, 45))
    with pytest.raises(ValueError, match="timezone-aware"):
        candidate(observed_at=datetime(2026, 7, 3, 11, 45, tzinfo=_NoneOffsetTz()))
    with pytest.raises(ValueError, match="market_slug contains sensitive material"):
        candidate(market_slug="secret-wallet-market")
    with pytest.raises(ValueError, match="reason_codes contains sensitive material"):
        candidate(reason_codes=("bearer_token",))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        candidate(report_only=False)
    with pytest.raises(ValueError, match="max_pass_cost_to_edge_ratio"):
        config(
            max_pass_cost_to_edge_ratio=d("0.800000"),
            max_watch_cost_to_edge_ratio=d("0.750000"),
        )
    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(candidates=(candidate(), candidate()))
    with pytest.raises(ValueError, match="observed_at"):
        report(
            candidates=(
                candidate(observed_at=datetime(2026, 7, 3, 12, 1, tzinfo=UTC)),
            ),
        )

    result = report(candidates=(candidate(),))
    with pytest.raises(FrozenInstanceError):
        result.rows[0].cost_stack_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(result.rows[0], readonly=False)


def test_static_phase1_reducer_surface_has_no_io_or_execution_behavior() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    exported_names = set(module.__all__)

    forbidden_import_roots = {
        "httpx",
        "psycopg",
        "requests",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "execute",
        "open",
        "request",
        "send",
        "submit",
    }
    forbidden_public_fragments = (
        "auth",
        "broker",
        "cancel",
        "exchange_mutation",
        "live",
        "order",
        "private_key",
        "sign",
        "trade",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            assert name not in forbidden_calls

    for name in exported_names:
        lowered = name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_fragments)

    for unsafe_key in (
        "auth_token",
        "wallet_address",
        "live_order_id",
        "trade_request",
        "cancel_request",
        "replace_request",
    ):
        with pytest.raises(ValueError, match="unsafe surface field"):
            module._reject_unsafe_fields("phase1 boundary probe", {unsafe_key: "x"})
