from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 59, 30, tzinfo=UTC)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _IntSubclass(int):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_probability_edge_cost_gate_v2"
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-probability-edge-cost-gate-v2",
        "min_cost_adjusted_edge": d("0.010000"),
        "min_liquidity_usdc": d("100.000000"),
        "min_depth_shares": d("50.000000"),
        "max_candidate_age_seconds": d("120.000000"),
    }
    values.update(overrides)
    return module.StrategyProbabilityEdgeCostGateV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_slug": "market-alpha",
        "question": "Will alpha happen?",
        "side": "yes",
        "observed_at": OBSERVED_AT,
        "forecast_probability": d("0.700000"),
        "market_probability": d("0.600000"),
        "taker_fee_rate": d("0.020000"),
        "spread_probability": d("0.010000"),
        "expected_slippage_probability": d("0.003000"),
        "settlement_delay_days": d("2.000000"),
        "settlement_delay_penalty_rate": d("0.002000"),
        "available_liquidity_usdc": d("150.000000"),
        "available_depth_shares": d("80.000000"),
        "reason_codes": ("seed",),
    }
    values.update(overrides)
    return module.StrategyProbabilityEdgeCostGateV2Candidate(**values)


def report(*candidates: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_probability_edge_cost_gate_v2_report(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def test_gate_computes_cost_adjusted_edge_and_readonly_statuses() -> None:
    result = report(
        candidate(candidate_id="ready", market_slug="market-ready"),
        candidate(
            candidate_id="watch",
            market_slug="market-watch",
            forecast_probability=d("0.638000"),
        ),
        candidate(
            candidate_id="blocked",
            market_slug="market-blocked",
            forecast_probability=d("0.620000"),
        ),
    )

    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-probability-edge-cost-gate-v2"
    assert result.candidate_count == 3
    assert result.row_count == 3
    assert result.ready_count == 1
    assert result.watch_count == 1
    assert result.blocked_count == 1
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.derived_validation_digest) == 64

    ready, watch, blocked = result.rows
    assert ready.candidate_id == "ready"
    assert ready.gross_probability_edge == d("0.100000")
    assert ready.taker_fee_cost_probability == d("0.012000")
    assert ready.spread_cost_probability == d("0.010000")
    assert ready.expected_slippage_probability == d("0.003000")
    assert ready.settlement_delay_cost_probability == d("0.004000")
    assert ready.total_cost_probability == d("0.029000")
    assert ready.cost_adjusted_edge == d("0.071000")
    assert ready.decision_threshold_probability == d("0.629000")
    assert ready.edge_to_threshold_probability == d("0.071000")
    assert ready.liquidity_coverage_ratio == d("1.500000")
    assert ready.depth_coverage_ratio == d("1.600000")
    assert ready.age_seconds == d("30.000000")
    assert ready.gate_status == "ready"
    assert ready.risk_label == "low_cost_risk"
    assert ready.reason_codes == ("cost_adjusted_edge_ready", "seed")
    assert len(ready.derived_validation_digest) == 64

    assert watch.candidate_id == "watch"
    assert watch.cost_adjusted_edge == d("0.009000")
    assert watch.decision_threshold_probability == d("0.629000")
    assert watch.edge_to_threshold_probability == d("0.009000")
    assert watch.gate_status == "watch"
    assert watch.risk_label == "medium_cost_risk"
    assert "edge_below_minimum" in watch.reason_codes

    assert blocked.candidate_id == "blocked"
    assert blocked.cost_adjusted_edge == d("-0.009000")
    assert blocked.decision_threshold_probability == d("0.629000")
    assert blocked.edge_to_threshold_probability == d("-0.009000")
    assert blocked.gate_status == "blocked"
    assert blocked.risk_label == "high_cost_risk"
    assert "edge_not_positive_after_costs" in blocked.reason_codes


def test_liquidity_depth_and_staleness_thresholds_gate_candidates() -> None:
    result = report(
        candidate(
            candidate_id="thin-liquidity",
            market_slug="market-thin-liquidity",
            available_liquidity_usdc=d("75.000000"),
        ),
        candidate(
            candidate_id="thin-depth",
            market_slug="market-thin-depth",
            available_depth_shares=d("40.000000"),
        ),
        candidate(
            candidate_id="stale",
            market_slug="market-stale",
            observed_at=datetime(2026, 7, 6, 11, 56, tzinfo=UTC),
        ),
    )

    thin_liquidity = next(row for row in result.rows if row.candidate_id == "thin-liquidity")
    assert thin_liquidity.gate_status == "blocked"
    assert thin_liquidity.liquidity_coverage_ratio == d("0.750000")
    assert "liquidity_below_minimum" in thin_liquidity.reason_codes

    thin_depth = next(row for row in result.rows if row.candidate_id == "thin-depth")
    assert thin_depth.gate_status == "blocked"
    assert thin_depth.depth_coverage_ratio == d("0.800000")
    assert "depth_below_minimum" in thin_depth.reason_codes

    stale = next(row for row in result.rows if row.candidate_id == "stale")
    assert stale.gate_status == "watch"
    assert stale.age_seconds == d("240.000000")
    assert "candidate_stale" in stale.reason_codes


def test_no_candidates_returns_empty_digest_checked_report() -> None:
    result = report()

    assert result.candidate_count == 0
    assert result.row_count == 0
    assert result.ready_count == 0
    assert result.watch_count == 0
    assert result.blocked_count == 0
    assert result.first_observed_at is None
    assert result.latest_observed_at is None
    assert result.rows == ()
    assert len(result.derived_validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_payload_is_json_ready_decimal_strings_and_safe_public_content() -> None:
    result = report(candidate(candidate_id="payload"))

    payload = api().strategy_probability_edge_cost_gate_v2_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["candidate_id"] == "payload"
    assert payload["rows"][0]["cost_adjusted_edge"] == "0.071000"
    assert payload["rows"][0]["decision_threshold_probability"] == "0.629000"
    assert payload["rows"][0]["edge_to_threshold_probability"] == "0.071000"
    assert payload["rows"][0]["age_seconds"] == "30.000000"
    assert payload["rows"][0]["derived_validation_digest"] == result.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert isinstance(key, str)
                lowered_key = key.lower()
                assert not any(fragment in lowered_key for fragment in FORBIDDEN_PUBLIC_FRAGMENTS)
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        else:
            assert not isinstance(value, float)
            assert not isinstance(value, Decimal)
            if isinstance(value, str):
                lowered_value = value.lower()
                assert not any(
                    fragment in lowered_value for fragment in FORBIDDEN_PUBLIC_FRAGMENTS
                )

    walk(payload)


def test_dataclasses_are_frozen_flags_are_hard_and_digests_reject_tamper() -> None:
    row = report(candidate()).rows[0]

    with pytest.raises(FrozenInstanceError):
        row.gate_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        config().min_cost_adjusted_edge = d("0.020000")

    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report(candidate()), paper_only=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, gate_status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report(candidate()), ready_count=0)


def test_rejects_unsafe_public_values_and_unexpected_public_surface() -> None:
    module = api()

    for field_name, bad_value in (
        ("candidate_id", "candidate-wallet"),
        ("market_slug", "market-network"),
        ("question", "Will this mention buy?"),
        ("reason_codes", ("needs-auth",)),
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            candidate(**{field_name: bad_value})

    for field_name, bad_value in (
        ("config_version", "live-config"),
        ("min_cost_adjusted_edge", 0.01),
    ):
        with pytest.raises(ValueError, match=field_name):
            config(**{field_name: bad_value})

    exported_names = set(module.__all__)
    assert exported_names == {
        "StrategyProbabilityEdgeCostGateV2Candidate",
        "StrategyProbabilityEdgeCostGateV2Config",
        "StrategyProbabilityEdgeCostGateV2Report",
        "StrategyProbabilityEdgeCostGateV2Row",
        "build_strategy_probability_edge_cost_gate_v2_report",
        "strategy_probability_edge_cost_gate_v2_payload",
    }
    for name in exported_names:
        lowered_name = name.lower()
        assert not any(fragment in lowered_name for fragment in FORBIDDEN_PUBLIC_FRAGMENTS)


def test_validates_decimal_only_inputs_utc_datetimes_and_report_consistency() -> None:
    module = api()
    eastern = timezone(timedelta(hours=-4))
    result = report(
        candidate(observed_at=datetime(2026, 7, 6, 7, 59, 30, tzinfo=eastern)),
        generated_at=datetime(2026, 7, 6, 8, 0, 0, tzinfo=eastern),
    )
    assert result.generated_at == GENERATED_AT
    assert result.rows[0].observed_at == OBSERVED_AT
    assert result.rows[0].age_seconds == d("30.000000")

    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_probability_edge_cost_gate_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="candidates"):
        module.build_strategy_probability_edge_cost_gate_v2_report(
            "not-candidates",
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="StrategyProbabilityEdgeCostGateV2Candidate"):
        module.build_strategy_probability_edge_cost_gate_v2_report(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="candidate_id"):
        candidate(candidate_id=_StringSubclass("candidate-alpha"))
    with pytest.raises(ValueError, match="candidate_count"):
        module.StrategyProbabilityEdgeCostGateV2Report(
            generated_at=GENERATED_AT,
            config_version="strategy-probability-edge-cost-gate-v2",
            candidate_count=_IntSubclass(1),
            row_count=0,
            ready_count=0,
            watch_count=0,
            blocked_count=0,
            first_observed_at=None,
            latest_observed_at=None,
            rows=(),
            derived_validation_digest="0" * 64,
        )
    with pytest.raises(ValueError, match="forecast_probability"):
        candidate(forecast_probability=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="forecast_probability"):
        candidate(forecast_probability=0.7)
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate(), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        report(candidate(observed_at=datetime(2026, 7, 6, 11, 59, 30)))
    with pytest.raises(ValueError, match="must not be after generated_at"):
        report(candidate(observed_at=datetime(2026, 7, 6, 12, 0, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="rows must be sorted"):
        module.StrategyProbabilityEdgeCostGateV2Report(
            generated_at=GENERATED_AT,
            config_version="strategy-probability-edge-cost-gate-v2",
            candidate_count=2,
            row_count=2,
            ready_count=1,
            watch_count=1,
            blocked_count=0,
            first_observed_at=OBSERVED_AT,
            latest_observed_at=OBSERVED_AT,
            rows=(
                report(candidate(candidate_id="watch", forecast_probability=d("0.638000"))).rows[0],
                report(candidate(candidate_id="ready")).rows[0],
            ),
        )


def test_module_scope_has_no_io_or_execution_surface() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")

    blocked_snippets = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "clob",
        "private_key",
        "secret",
        "place_",
        "execute",
        "subprocess",
        "open(",
        "Path(",
    )
    lowered_source = source.lower()
    assert not any(snippet in lowered_source for snippet in blocked_snippets)
