from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 7, 6, 11, 0, tzinfo=UTC)
MARKET_CLOSE_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")

UNSAFE_PUBLIC_TERMS = (
    "li" + "ve",
    "au" + "th",
    "wall" + "et",
    "ord" + "er",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sign" + "ing",
    "mut" + "ation",
    "b" + "uy",
    "s" + "ell",
    "tr" + "ade",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_resolution_delay_capital_lockup_penalty_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_RESOLUTION_DELAY_CAPITAL_LOCKUP_PENALTY_V2_CONFIG_VERSION
        ),
        "high_settlement_delay_hours": d("72.000000"),
        "high_capital_lockup_hours": d("168.000000"),
        "high_claim_latency_hours": d("24.000000"),
        "watch_penalty_score": d("0.350000"),
        "blocked_penalty_score": d("0.700000"),
        "watch_unresolved_outcome_source_risk": d("0.250000"),
        "blocked_unresolved_outcome_source_risk": d("0.500000"),
    }
    values.update(overrides)
    return module.StrategyResolutionDelayCapitalLockupPenaltyV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_reference": "candidate-alpha",
        "market_slug": "alpha-market",
        "evaluated_at": EVALUATED_AT,
        "market_close_at": MARKET_CLOSE_AT,
        "expected_settlement_delay_hours": d("24.000000"),
        "capital_lockup_hours": d("72.000000"),
        "outcome_source_confidence_ratio": d("0.850000"),
        "expected_claim_latency_hours": d("6.000000"),
        "opportunity_cost_pressure": d("0.200000"),
        "reason_codes": ("resolution_delay_capital_lockup_input",),
    }
    values.update(overrides)
    return module.StrategyResolutionDelayCapitalLockupPenaltyV2Candidate(**values)


def report(*candidates: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_strategy_resolution_delay_capital_lockup_penalty_v2_report(
        candidates,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_int_or_decimal_payload_values(value: Any) -> None:
    if type(value) in (float, int, Decimal):
        raise AssertionError(f"unexpected public payload scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_int_or_decimal_payload_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_int_or_decimal_payload_values(item)


def test_report_penalizes_lockup_delay_source_claim_and_opportunity_pressure() -> None:
    result = report(
        candidate(
            candidate_reference="sensitive-alpha",
            market_slug="alpha-blocked",
            expected_settlement_delay_hours=d("96.000000"),
            capital_lockup_hours=d("240.000000"),
            outcome_source_confidence_ratio=d("0.400000"),
            expected_claim_latency_hours=d("30.000000"),
            opportunity_cost_pressure=d("0.900000"),
        ),
        candidate(
            candidate_reference="watch-alpha",
            market_slug="beta-watch",
            expected_settlement_delay_hours=d("40.000000"),
            capital_lockup_hours=d("120.000000"),
            outcome_source_confidence_ratio=d("0.700000"),
            expected_claim_latency_hours=d("12.000000"),
            opportunity_cost_pressure=d("0.300000"),
        ),
        candidate(
            candidate_reference="clear-alpha",
            market_slug="gamma-clear",
            expected_settlement_delay_hours=d("8.000000"),
            capital_lockup_hours=d("24.000000"),
            outcome_source_confidence_ratio=d("0.950000"),
            expected_claim_latency_hours=d("2.000000"),
            opportunity_cost_pressure=d("0.050000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert (
        result.config_version
        == "strategy-resolution-delay-capital-lockup-penalty-v2-phase1"
    )
    assert result.candidate_count == d("3")
    assert result.blocked_count == d("1")
    assert result.watch_count == d("1")
    assert result.paper_ok_count == d("1")
    assert result.max_total_lockup_penalty_score == d("0.910000")
    assert result.max_capital_lockup_hours == d("240.000000")
    assert result.max_settlement_delay_hours == d("96.000000")
    assert result.max_claim_latency_hours == d("30.000000")
    assert result.max_unresolved_outcome_source_risk == d("0.600000")
    assert result.max_opportunity_cost_pressure == d("0.900000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "capital_lockup_penalty_blocked",
        "claim_latency_penalty_blocked",
        "opportunity_cost_pressure_blocked",
        "outcome_source_risk_blocked",
        "settlement_delay_penalty_blocked",
    )
    assert len(result.derived_validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    blocked, watched, paper_ok = result.rows
    assert tuple(row.penalty_status for row in result.rows) == (
        "blocked",
        "watch",
        "paper_ok",
    )

    assert blocked.penalty_rank == d("1")
    assert blocked.redacted_candidate_reference.startswith("candidate_ref_")
    assert "sensitive-alpha" not in blocked.redacted_candidate_reference
    assert blocked.settlement_delay_penalty == d("1.000000")
    assert blocked.capital_lockup_penalty == d("1.000000")
    assert blocked.unresolved_outcome_source_risk == d("0.600000")
    assert blocked.outcome_source_penalty == d("0.600000")
    assert blocked.claim_latency_penalty == d("1.000000")
    assert blocked.opportunity_cost_penalty == d("0.900000")
    assert blocked.total_lockup_penalty_score == d("0.910000")
    assert blocked.reason_codes == (
        "capital_lockup_penalty_blocked",
        "claim_latency_penalty_blocked",
        "opportunity_cost_pressure_blocked",
        "outcome_source_risk_blocked",
        "resolution_delay_capital_lockup_input",
        "settlement_delay_capital_lockup_penalty_blocked",
        "settlement_delay_penalty_blocked",
    )

    assert watched.penalty_rank == d("2")
    assert watched.settlement_delay_penalty == d("0.555556")
    assert watched.capital_lockup_penalty == d("0.714286")
    assert watched.unresolved_outcome_source_risk == d("0.300000")
    assert watched.claim_latency_penalty == d("0.500000")
    assert watched.opportunity_cost_penalty == d("0.300000")
    assert watched.total_lockup_penalty_score == d("0.507460")

    assert paper_ok.penalty_rank == d("3")
    assert paper_ok.total_lockup_penalty_score == d("0.095159")
    assert paper_ok.reason_codes == (
        "capital_lockup_penalty_clear",
        "claim_latency_penalty_clear",
        "opportunity_cost_pressure_clear",
        "outcome_source_risk_clear",
        "resolution_delay_capital_lockup_input",
        "settlement_delay_capital_lockup_penalty_paper_ok",
        "settlement_delay_penalty_clear",
    )


def test_empty_report_is_current_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.candidate_count == ZERO
    assert empty.blocked_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.paper_ok_count == ZERO
    assert empty.max_total_lockup_penalty_score == ZERO
    assert empty.max_capital_lockup_hours == ZERO
    assert empty.max_settlement_delay_hours == ZERO
    assert empty.max_claim_latency_hours == ZERO
    assert empty.max_unresolved_outcome_source_risk == ZERO
    assert empty.max_opportunity_cost_pressure == ZERO
    assert empty.status == "paper_ok"
    assert empty.reason_codes == (
        "resolution_delay_capital_lockup_penalty_v2_empty",
    )
    assert empty.rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(candidate())
    for value in (config(), empty, *populated.rows, populated):
        for item in fields(value):
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "derived_validation_digest",
            }:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_hours",
                    "_risk",
                    "_pressure",
                    "_penalty",
                    "_score",
                    "_rank",
                    "_ratio",
                ),
            ):
                assert type(item_value) is Decimal


def test_public_payload_uses_decimal_strings_and_rejects_unsafe_text() -> None:
    module = api()
    result = report(
        candidate(
            candidate_reference="payload-alpha",
            market_slug="payload-market",
            evaluated_at=datetime(2026, 7, 6, 7, 0, tzinfo=timezone(timedelta(hours=-4))),
            market_close_at=datetime(
                2026,
                7,
                8,
                8,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_resolution_delay_capital_lockup_penalty_v2_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["max_total_lockup_penalty_score"] == "0.290476"
    assert payload["rows"][0]["evaluated_at"] == "2026-07-06T11:00:00+00:00"
    assert payload["rows"][0]["market_close_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["capital_lockup_hours"] == "72.000000"
    assert payload["rows"][0]["derived_validation_digest"] == (
        result.rows[0].derived_validation_digest
    )
    assert "payload-alpha" not in rendered
    assert_no_float_int_or_decimal_payload_values(payload)

    for term in UNSAFE_PUBLIC_TERMS:
        with pytest.raises(ValueError, match="unsafe public"):
            module._payload_value({"safe_key": f"prefix-{term}-suffix"})
        with pytest.raises(ValueError, match="unsafe public"):
            module._payload_value({f"prefix_{term}_suffix": "safe"})


def test_validates_decimal_only_time_flags_frozen_and_derived_digest() -> None:
    module = api()

    shifted = report(
        candidate(
            evaluated_at=datetime(2026, 7, 6, 6, 0, tzinfo=timezone(timedelta(hours=-5))),
            market_close_at=datetime(
                2026,
                7,
                8,
                5,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    assert shifted.generated_at == GENERATED_AT
    assert shifted.rows[0].evaluated_at == EVALUATED_AT
    assert shifted.rows[0].market_close_at == MARKET_CLOSE_AT

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(generated_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="evaluated_at must be exactly datetime"):
        candidate(evaluated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="capital_lockup_hours must be exactly Decimal"):
        candidate(capital_lockup_hours=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="capital_lockup_hours must be exactly Decimal"):
        candidate(capital_lockup_hours=1)

    item = report(candidate()).rows[0]
    with pytest.raises(FrozenInstanceError):
        item.penalty_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="readonly must be True"):
        replace(item, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(item, total_lockup_penalty_score=d("0.999999"))

    original = report(candidate())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(original, candidate_count=d("2"))

    with pytest.raises(ValueError, match="config must be exactly"):
        module.build_strategy_resolution_delay_capital_lockup_penalty_v2_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="duplicate candidate_reference"):
        report(candidate(), candidate())

    with pytest.raises(ValueError, match="unsafe public"):
        candidate(market_slug="prefix-" + UNSAFE_PUBLIC_TERMS[0])


def test_source_scope_has_no_external_or_action_surfaces() -> None:
    module = api()
    source_paths = (
        Path(module.__file__),
        Path(__file__),
    )
    for path in source_paths:
        text = path.read_text()
        tree = ast.parse(text)
        imports = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        assert not {
            "req" + "uests",
            "ht" + "tpx",
            "url" + "lib",
            "sql" + "ite3",
            "psy" + "copg",
            "supa" + "base",
            "we" + "b3",
        } & imports
        lower_text = text.lower()
        for term in UNSAFE_PUBLIC_TERMS:
            assert term not in lower_text

    assert module.__all__ == (
        "DEFAULT_STRATEGY_RESOLUTION_DELAY_CAPITAL_LOCKUP_PENALTY_V2_CONFIG_VERSION",
        "StrategyResolutionDelayCapitalLockupPenaltyV2Candidate",
        "StrategyResolutionDelayCapitalLockupPenaltyV2Config",
        "StrategyResolutionDelayCapitalLockupPenaltyV2Report",
        "StrategyResolutionDelayCapitalLockupPenaltyV2Row",
        "build_strategy_resolution_delay_capital_lockup_penalty_v2_report",
        "strategy_resolution_delay_capital_lockup_penalty_v2_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
