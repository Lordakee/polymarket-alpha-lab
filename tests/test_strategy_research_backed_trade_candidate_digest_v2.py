from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 7, 6, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_research_backed_trade_candidate_digest_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": "strategy-research-backed-candidate-digest-v2-test",
        "min_ready_research_readiness_score": d("0.800000"),
        "min_watch_research_readiness_score": d("0.650000"),
        "min_ready_official_source_anchor_count": d("2.000000"),
        "min_watch_official_source_anchor_count": d("1.000000"),
        "max_ready_source_age_seconds": d("1800.000000"),
        "max_watch_source_age_seconds": d("7200.000000"),
        "min_ready_cost_adjusted_edge": d("0.030000"),
        "min_watch_cost_adjusted_edge": d("0.010000"),
        "max_ready_expected_value_gap": d("0.010000"),
        "max_watch_expected_value_gap": d("0.025000"),
        "max_ready_uncertainty_band_probability": d("0.040000"),
        "max_watch_uncertainty_band_probability": d("0.075000"),
        "min_ready_exit_depth_to_candidate_ratio": d("1.500000"),
        "min_watch_exit_depth_to_candidate_ratio": d("1.000000"),
        "max_ready_portfolio_impact_ratio": d("0.080000"),
        "max_watch_portfolio_impact_ratio": d("0.150000"),
    }
    values.update(overrides)
    return module.StrategyResearchBackedTradeCandidateDigestV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "candidate_reference": "candidate-alpha",
        "market_slug": "macro-release-positive",
        "question": "Will official data resolve positively?",
        "outcome_name": "Yes",
        "side": "yes",
        "evaluated_at": GENERATED_AT - timedelta(minutes=20),
        "research_readiness_score": d("0.900000"),
        "official_source_anchors": ("agency-release", "official-table"),
        "latest_official_source_at": SOURCE_AT,
        "model_probability": d("0.650000"),
        "market_probability": d("0.580000"),
        "entry_cost_probability": d("0.010000"),
        "exit_cost_probability": d("0.005000"),
        "expected_value_probability_edge": d("0.055000"),
        "uncertainty_band_probability": d("0.020000"),
        "exit_depth_to_candidate_ratio": d("2.000000"),
        "portfolio_impact_ratio": d("0.040000"),
        "safety_gate_clear": True,
        "reason_codes": ("operator_reviewed",),
    }
    values.update(overrides)
    return module.StrategyResearchBackedTradeCandidateDigestV2Candidate(**values)


def report(*candidates: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_research_backed_trade_candidate_digest_v2(
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


def assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_scalars(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric_scalars(item)


def test_builds_ranked_digest_for_final_candidates() -> None:
    digest = report(
        candidate(candidate_reference="candidate-ready"),
        candidate(
            candidate_reference="candidate-watch",
            market_slug="macro-watch",
            research_readiness_score=d("0.700000"),
            official_source_anchors=("agency-release",),
            latest_official_source_at=GENERATED_AT - timedelta(hours=1),
            model_probability=d("0.600000"),
            market_probability=d("0.575000"),
            entry_cost_probability=d("0.010000"),
            exit_cost_probability=d("0.005000"),
            expected_value_probability_edge=d("0.025000"),
            uncertainty_band_probability=d("0.060000"),
            exit_depth_to_candidate_ratio=d("1.200000"),
            portfolio_impact_ratio=d("0.100000"),
        ),
        candidate(
            candidate_reference="candidate-blocked",
            market_slug="macro-blocked",
            research_readiness_score=d("0.500000"),
            official_source_anchors=(),
            latest_official_source_at=GENERATED_AT - timedelta(hours=4),
            model_probability=d("0.560000"),
            market_probability=d("0.570000"),
            entry_cost_probability=d("0.010000"),
            exit_cost_probability=d("0.005000"),
            expected_value_probability_edge=d("0.040000"),
            uncertainty_band_probability=d("0.090000"),
            exit_depth_to_candidate_ratio=d("0.500000"),
            portfolio_impact_ratio=d("0.200000"),
            safety_gate_clear=False,
        ),
    )

    assert is_dataclass(digest)
    assert digest.generated_at == GENERATED_AT
    assert digest.status == "blocked"
    assert digest.candidate_count == d("3.000000")
    assert digest.ready_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert digest.highest_cost_adjusted_edge == d("0.055000")
    assert digest.lowest_liquidity_exit_ratio == d("0.500000")
    assert digest.max_portfolio_impact_ratio == d("0.200000")
    assert digest.top_candidate_reference == "candidate-ready"
    assert digest.reason_codes[0] == "digest_blocked"
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    assert tuple(row.candidate_status for row in digest.rows) == (
        "ready",
        "watch",
        "blocked",
    )
    ready, watched, blocked = digest.rows
    assert ready.candidate_rank == d("1.000000")
    assert ready.cost_adjusted_edge == d("0.055000")
    assert ready.expected_value_consistency_gap == ZERO
    assert ready.source_age_seconds == d("900.000000")
    assert ready.official_source_anchor_count == d("2.000000")
    assert ready.safety_status == "ready"
    assert ready.reason_codes == (
        "operator_reviewed",
        "research_readiness_ready",
        "official_source_anchors_ready",
        "source_freshness_ready",
        "cost_adjusted_edge_ready",
        "expected_value_consistency_ready",
        "safety_gate_ready",
        "uncertainty_band_ready",
        "liquidity_exit_ready",
        "portfolio_impact_ready",
    )
    assert watched.candidate_status == "watch"
    assert watched.expected_value_consistency_gap == d("0.015000")
    assert "source_freshness_watch" in watched.reason_codes
    assert blocked.candidate_status == "blocked"
    assert "safety_gate_blocked" in blocked.reason_codes
    assert "liquidity_exit_blocked" in blocked.reason_codes


def test_payload_uses_decimal_strings_digest_and_rejects_unsafe_surface() -> None:
    module = api()
    digest = report(
        candidate(
            evaluated_at=datetime(2026, 7, 6, 7, 40, tzinfo=timezone(timedelta(hours=-4))),
            latest_official_source_at=datetime(
                2026,
                7,
                6,
                7,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
    )

    payload = module.strategy_research_backed_trade_candidate_digest_v2_payload(digest)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["highest_cost_adjusted_edge"] == "0.055000"
    assert payload["rows"][0]["candidate_rank"] == "1.000000"
    assert payload["rows"][0]["source_age_seconds"] == "900.000000"
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == digest.derived_validation_digest
    assert all(
        character in "0123456789abcdef"
        for character in payload["derived_validation_digest"]
    )
    assert module.strategy_research_backed_trade_candidate_digest_v2_payload(payload) == payload
    json.dumps(payload, sort_keys=True)
    assert_no_float_values(payload)
    assert_no_public_numeric_scalars(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(digest, status="empty")

    tampered = dict(payload)
    tampered["status"] = "empty"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        module.strategy_research_backed_trade_candidate_digest_v2_payload(tampered)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_research_backed_trade_candidate_digest_v2_payload(missing_digest)

    unsafe_keys = (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_client",
        "database_url",
        "persist_path",
        "signing_key",
        "mutation_id",
        "buy_button",
        "sell_button",
        "trade_id",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            module.strategy_research_backed_trade_candidate_digest_v2_payload(
                unsafe_payload,
            )

    unsafe_values = (
        "live mode enabled",
        "auth token configured",
        "wallet address configured",
        "order submission configured",
        "network request configured",
        "database writer configured",
        "persist output configured",
        "signing key configured",
        "mutation enabled",
        "buy signal configured",
        "sell signal configured",
        "trade instruction configured",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_rows = [dict(payload["rows"][0])]
        unsafe_rows[0]["market_slug"] = unsafe_value
        unsafe_payload["rows"] = unsafe_rows
        with pytest.raises(ValueError, match="unsafe"):
            module.strategy_research_backed_trade_candidate_digest_v2_payload(
                unsafe_payload,
            )


def test_dataclasses_are_frozen_decimal_only_exact_and_readonly() -> None:
    module = api()
    cfg = config()
    source = candidate()
    digest = report(source)
    values = (cfg, source, digest.rows[0], digest)

    assert module.__all__ == (
        "DEFAULT_STRATEGY_RESEARCH_BACKED_CANDIDATE_DIGEST_V2_CONFIG_VERSION",
        "StrategyResearchBackedTradeCandidateDigestV2Candidate",
        "StrategyResearchBackedTradeCandidateDigestV2Config",
        "StrategyResearchBackedTradeCandidateDigestV2Report",
        "StrategyResearchBackedTradeCandidateDigestV2Row",
        "build_strategy_research_backed_trade_candidate_digest_v2",
        "strategy_research_backed_trade_candidate_digest_v2_payload",
        "validate_strategy_research_backed_trade_candidate_digest_v2_payload",
    )
    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]
        for field in fields(value):
            field_value = getattr(value, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal

    with pytest.raises(ValueError, match="model_probability must be a Decimal"):
        candidate(model_probability=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(digest.rows[0], readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(digest, candidate_count=d("4.000000"))


def test_rejects_bad_inputs_duplicates_times_and_thresholds() -> None:
    module = api()

    with pytest.raises(ValueError, match="candidates must be an iterable"):
        module.build_strategy_research_backed_trade_candidate_digest_v2(
            "not-a-candidate",
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="candidates must contain"):
        report(object())
    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(candidate(), candidate())
    with pytest.raises(ValueError, match="latest_official_source_at must not be after generated_at"):
        report(candidate(latest_official_source_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="evaluated_at must not be after generated_at"):
        report(candidate(evaluated_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(candidate(candidate_reference="candidate-time"), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="ready.*watch"):
        config(
            min_ready_research_readiness_score=d("0.600000"),
            min_watch_research_readiness_score=d("0.700000"),
        )
    with pytest.raises(ValueError, match="must be nonnegative"):
        candidate(exit_depth_to_candidate_ratio=d("-0.010000"))
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_research_backed_trade_candidate_digest_v2(
            (candidate(candidate_reference="candidate-config"),),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_empty_digest_is_readonly_and_zeroed() -> None:
    digest = report()

    assert digest.status == "empty"
    assert digest.candidate_count == ZERO
    assert digest.ready_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.blocked_count == ZERO
    assert digest.highest_cost_adjusted_edge == ZERO
    assert digest.lowest_liquidity_exit_ratio == ZERO
    assert digest.max_portfolio_impact_ratio == ZERO
    assert digest.top_candidate_reference is None
    assert digest.reason_codes == ("digest_empty",)
    assert digest.rows == ()
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_module_is_pure_readonly_report_only_and_has_no_io_surface() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
        "json",
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
        "request",
        "submit",
        "cancel",
        "order",
        "buy",
        "sell",
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
