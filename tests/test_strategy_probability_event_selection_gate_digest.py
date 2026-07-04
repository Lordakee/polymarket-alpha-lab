from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_probability_event_selection_gate_digest.py"
)
GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 7, 3, 11, 55, tzinfo=UTC)
EVIDENCE_AT = datetime(2026, 7, 3, 11, 45, tzinfo=UTC)
MEMORY_AT = datetime(2026, 7, 3, 11, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_probability_event_selection_gate_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "public-alpha",
        "event_title": "Will Alpha resolve yes?",
        "side": "yes",
        "evaluated_at": EVALUATED_AT,
        "market_implied_probability": d("0.600000"),
        "model_probability": d("0.690000"),
        "spread_probability_cost": d("0.010000"),
        "slippage_probability_cost": d("0.005000"),
        "external_cost_buffer_probability": d("0.010000"),
        "evidence_fresh_at": EVIDENCE_AT,
        "team_memory_updated_at": MEMORY_AT,
        "team_memory_confidence": d("0.850000"),
        "reason_codes": ("candidate_positive_edge",),
    }
    values.update(overrides)
    return module.StrategyProbabilityEventSelectionGateDigestCandidate(**values)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-probability-event-selection-gate-digest-v0",
        "min_net_probability_edge": d("0.020000"),
        "watch_net_probability_edge": d("0.005000"),
        "taker_fee_rate": d("0.020000"),
        "max_evidence_age_seconds": d("1800"),
        "max_team_memory_age_seconds": d("3600"),
        "min_team_memory_confidence": d("0.700000"),
    }
    values.update(overrides)
    return module.StrategyProbabilityEventSelectionGateDigestConfig(**values)


def report(*, candidates=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_probability_event_selection_gate_digest(
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
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_digest_gates_binary_probability_candidates_with_costs_context_and_reason_codes() -> None:
    result = report(
        candidates=(
            candidate(
                candidate_reference="select-alpha",
                side="yes",
                market_implied_probability=d("0.600000"),
                model_probability=d("0.700000"),
                spread_probability_cost=d("0.010000"),
                slippage_probability_cost=d("0.005000"),
                external_cost_buffer_probability=d("0.010000"),
                evidence_fresh_at=datetime(2026, 7, 3, 11, 50, tzinfo=UTC),
                team_memory_confidence=d("0.900000"),
            ),
            candidate(
                candidate_reference="watch-alpha",
                side="no",
                market_implied_probability=d("0.600000"),
                model_probability=d("0.350000"),
                spread_probability_cost=d("0.010000"),
                slippage_probability_cost=d("0.005000"),
                external_cost_buffer_probability=d("0.010000"),
                evidence_fresh_at=datetime(2026, 7, 3, 11, 15, tzinfo=UTC),
                team_memory_confidence=d("0.650000"),
            ),
            candidate(
                candidate_reference="secret-market-wallet-token-alpha",
                side="yes",
                market_implied_probability=d("0.600000"),
                model_probability=d("0.620000"),
                spread_probability_cost=d("0.015000"),
                slippage_probability_cost=d("0.010000"),
                external_cost_buffer_probability=d("0.010000"),
                evidence_fresh_at=datetime(2026, 7, 3, 11, 55, tzinfo=UTC),
                team_memory_confidence=d("0.800000"),
            ),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-probability-event-selection-gate-digest-v0"
    assert result.candidate_count == d("3")
    assert result.select_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.max_net_probability_edge == d("0.217000")
    assert result.max_required_edge_shortfall == d("0.032000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "candidate_positive_edge",
        "evidence_freshness_watch",
        "event_selection_blocked",
        "event_selection_selected",
        "event_selection_watch",
        "external_cost_buffer_present",
        "spread_cost_present",
        "slippage_cost_present",
        "taker_fee_cost_present",
        "team_memory_confidence_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.selection_status for row in result.rows) == (
        "blocked",
        "watch",
        "select",
    )
    blocked, watched, selected = result.rows

    assert blocked.redacted_candidate_reference.startswith("candidate_ref_")
    assert "secret" not in blocked.redacted_candidate_reference
    assert "wallet" not in blocked.redacted_candidate_reference
    assert "token" not in blocked.redacted_candidate_reference
    assert blocked.side == "yes"
    assert blocked.side_model_probability == d("0.620000")
    assert blocked.side_market_implied_probability == d("0.600000")
    assert blocked.gross_probability_edge == d("0.020000")
    assert blocked.taker_fee_probability_cost == d("0.012000")
    assert blocked.total_probability_cost == d("0.047000")
    assert blocked.net_probability_edge == d("-0.027000")
    assert blocked.required_edge_shortfall == d("0.032000")
    assert blocked.selection_status == "blocked"
    assert blocked.reason_codes == (
        "candidate_positive_edge",
        "event_selection_blocked",
        "taker_fee_cost_present",
        "spread_cost_present",
        "slippage_cost_present",
        "external_cost_buffer_present",
    )

    assert watched.side == "no"
    assert watched.side_model_probability == d("0.650000")
    assert watched.side_market_implied_probability == d("0.400000")
    assert watched.gross_probability_edge == d("0.250000")
    assert watched.net_probability_edge == d("0.217000")
    assert watched.selection_status == "watch"
    assert "evidence_freshness_watch" in watched.reason_codes
    assert "team_memory_confidence_watch" in watched.reason_codes

    assert selected.side_model_probability == d("0.700000")
    assert selected.side_market_implied_probability == d("0.600000")
    assert selected.taker_fee_probability_cost == d("0.012000")
    assert selected.total_probability_cost == d("0.037000")
    assert selected.net_probability_edge == d("0.063000")
    assert selected.required_edge_shortfall == ZERO
    assert selected.selection_status == "select"
    assert selected.reason_codes == (
        "candidate_positive_edge",
        "event_selection_selected",
        "taker_fee_cost_present",
        "spread_cost_present",
        "slippage_cost_present",
        "external_cost_buffer_present",
    )


def test_empty_report_is_watch_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == d("0")
    assert empty.select_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.blocked_count == d("0")
    assert empty.max_net_probability_edge == ZERO
    assert empty.max_required_edge_shortfall == ZERO
    assert empty.status == "watch"
    assert empty.reason_codes == ("event_selection_gate_digest_empty",)
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
                    "_probability",
                    "_cost",
                    "_edge",
                    "_shortfall",
                    "_seconds",
                    "_confidence",
                    "_rate",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_redacts_references_uses_decimal_strings_and_no_floats() -> None:
    module = api()
    result = report(
        candidates=(
            candidate(
                candidate_reference="secret-market-wallet-token-alpha",
                side="yes",
                market_implied_probability=d("0.600000"),
                model_probability=d("0.620000"),
                spread_probability_cost=d("0.015000"),
                slippage_probability_cost=d("0.010000"),
                external_cost_buffer_probability=d("0.010000"),
            ),
        ),
        generated_at=datetime(2026, 7, 3, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_probability_event_selection_gate_digest_payload(result)
    rendered = repr(payload).lower()
    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["max_required_edge_shortfall"] == "0.032000"
    assert payload["rows"][0]["redacted_candidate_reference"].startswith(
        "candidate_ref_",
    )
    assert payload["rows"][0]["side_market_implied_probability"] == "0.600000"
    assert payload["rows"][0]["taker_fee_probability_cost"] == "0.012000"
    assert payload["rows"][0]["net_probability_edge"] == "-0.027000"
    assert "secret-market" not in rendered
    assert "wallet" not in rendered
    assert "token" not in rendered
    assert_no_float_values(payload)


def test_validation_rejects_float_inputs_subclasses_stale_future_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="config"):
        module.build_strategy_probability_event_selection_gate_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="model_probability"):
        candidate(model_probability=0.64)
    with pytest.raises(ValueError, match="market_implied_probability"):
        candidate(market_implied_probability=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="spread_probability_cost"):
        candidate(spread_probability_cost=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="evaluated_at"):
        candidate(evaluated_at=_DatetimeSubclass(2026, 7, 3, 11, 55, tzinfo=UTC))
    with pytest.raises(ValueError, match="evidence_fresh_at"):
        report(
            candidates=(
                candidate(
                    evidence_fresh_at=datetime(2026, 7, 3, 12, 1, tzinfo=UTC),
                ),
            ),
        )
    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(candidates=(candidate(), candidate()))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)

    frozen = candidate()
    with pytest.raises(FrozenInstanceError):
        frozen.side = "no"  # type: ignore[misc]


def test_no_side_uses_complementary_binary_event_probability_not_asset_price_logic() -> None:
    result = report(
        candidates=(
            candidate(
                candidate_reference="no-select-alpha",
                side="no",
                market_implied_probability=d("0.700000"),
                model_probability=d("0.200000"),
                spread_probability_cost=d("0.005000"),
                slippage_probability_cost=d("0.005000"),
                external_cost_buffer_probability=d("0.005000"),
                team_memory_confidence=d("0.900000"),
            ),
        ),
    )

    row = result.rows[0]
    assert row.side_model_probability == d("0.800000")
    assert row.side_market_implied_probability == d("0.300000")
    assert row.gross_probability_edge == d("0.500000")
    assert row.selection_status == "select"


def test_payload_requires_report_type_and_hard_flags() -> None:
    module = api()
    result = report(candidates=(candidate(),))

    with pytest.raises(ValueError, match="report must be"):
        module.strategy_probability_event_selection_gate_digest_payload(object())

    with pytest.raises(ValueError, match="readonly must be True"):
        module.strategy_probability_event_selection_gate_digest_payload(
            replace(result, readonly=False),
        )


def test_module_scope_has_no_external_io_live_execution_or_sensitive_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "order",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
