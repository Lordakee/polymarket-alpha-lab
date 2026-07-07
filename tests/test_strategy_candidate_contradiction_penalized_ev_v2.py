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


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
EVALUATED_AT = datetime(2026, 7, 7, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_contradiction_penalized_ev_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_STRATEGY_CANDIDATE_CONTRADICTION_PENALIZED_EV_V2_CONFIG_VERSION
        ),
        "watch_penalized_ev_floor": d("0.010000"),
        "pass_penalized_ev_floor": d("0.030000"),
        "watch_contradiction_severity": d("0.040000"),
        "block_contradiction_severity": d("0.120000"),
        "official_source_conflict_block": d("0.800000"),
        "source_contradiction_weight": d("0.200000"),
        "official_source_conflict_weight": d("0.300000"),
        "resolution_ambiguity_weight": d("0.100000"),
        "liquidity_risk_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.StrategyCandidateContradictionPenalizedEvV2Config(**values)


def candidate(**overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-pass",
        "market_id": "market-pass",
        "evaluated_at": EVALUATED_AT,
        "forecast_probability": d("0.640000"),
        "market_probability": d("0.560000"),
        "confidence_score": d("0.900000"),
        "source_contradiction": d("0.020000"),
        "official_source_conflict": d("0.000000"),
        "resolution_ambiguity": d("0.010000"),
        "taker_cost": d("0.005000"),
        "spread_cost": d("0.006000"),
        "slippage_cost": d("0.004000"),
        "liquidity_risk": d("0.100000"),
        "reason_codes": ("candidate_input",),
    }
    values.update(overrides)
    return module.StrategyCandidateContradictionPenalizedEvV2Candidate(**values)


def report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_candidate_contradiction_penalized_ev_v2(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_public_numbers_are_decimal(value: object) -> None:
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if type(value) is Decimal:
        return
    if isinstance(value, tuple):
        for item in value:
            assert_public_numbers_are_decimal(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            assert_public_numbers_are_decimal(getattr(value, field.name))


def assert_json_payload_has_no_decimal_int_or_float(value: Any) -> None:
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"unexpected JSON numeric value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_json_payload_has_no_decimal_int_or_float(item)
    if isinstance(value, list):
        for item in value:
            assert_json_payload_has_no_decimal_int_or_float(item)


def test_scores_phase_1_ev_penalized_by_contradiction_costs_and_liquidity_risk() -> None:
    result = report(
        candidate(
            candidate_id="candidate-pass",
            market_id="market-pass",
        ),
        candidate(
            candidate_id="candidate-watch",
            market_id="market-watch",
            forecast_probability=d("0.610000"),
            market_probability=d("0.550000"),
            confidence_score=d("0.800000"),
            source_contradiction=d("0.050000"),
            official_source_conflict=d("0.000000"),
            resolution_ambiguity=d("0.050000"),
            taker_cost=d("0.006000"),
            spread_cost=d("0.006000"),
            slippage_cost=d("0.006000"),
            liquidity_risk=d("0.100000"),
        ),
        candidate(
            candidate_id="candidate-block",
            market_id="market-block",
            forecast_probability=d("0.700000"),
            market_probability=d("0.500000"),
            confidence_score=d("0.900000"),
            source_contradiction=d("0.300000"),
            official_source_conflict=d("0.200000"),
            resolution_ambiguity=d("0.300000"),
            taker_cost=d("0.005000"),
            spread_cost=d("0.006000"),
            slippage_cost=d("0.004000"),
            liquidity_risk=d("0.200000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-candidate-contradiction-penalized-ev-v2"
    assert result.candidate_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.average_contradiction_penalized_ev == d("0.020667")
    assert result.max_contradiction_severity == d("0.150000")
    assert result.max_execution_cost == d("0.018000")
    assert result.report_status == "blocked"
    assert result.reason_codes == (
        "contradiction_severity_block",
        "low_penalized_ev_watch",
        "source_contradiction_penalty",
        "official_source_conflict",
        "resolution_ambiguity_penalty",
        "execution_cost_penalty",
        "liquidity_risk_penalty",
        "contradiction_penalized_ev_pass",
    )
    assert len(result.derived_validation_digest) == 64
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    blocked, passed, watched = result.rows
    assert blocked.candidate_id == "candidate-block"
    assert blocked.raw_edge == d("0.200000")
    assert blocked.confidence_adjusted_edge == d("0.180000")
    assert blocked.contradiction_severity == d("0.150000")
    assert blocked.execution_cost == d("0.015000")
    assert blocked.liquidity_risk_penalty == d("0.010000")
    assert blocked.total_penalty == d("0.175000")
    assert blocked.contradiction_penalized_ev == d("0.005000")
    assert blocked.ev_status == "blocked"
    assert blocked.reason_codes == (
        "candidate_input",
        "contradiction_severity_block",
        "low_penalized_ev_watch",
        "source_contradiction_penalty",
        "official_source_conflict",
        "resolution_ambiguity_penalty",
        "execution_cost_penalty",
        "liquidity_risk_penalty",
    )
    assert len(blocked.derived_validation_digest) == 64

    assert passed.raw_edge == d("0.080000")
    assert passed.confidence_adjusted_edge == d("0.072000")
    assert passed.contradiction_severity == d("0.005000")
    assert passed.execution_cost == d("0.015000")
    assert passed.liquidity_risk_penalty == d("0.005000")
    assert passed.total_penalty == d("0.025000")
    assert passed.contradiction_penalized_ev == d("0.047000")
    assert passed.ev_status == "pass"
    assert passed.reason_codes == (
        "candidate_input",
        "source_contradiction_penalty",
        "resolution_ambiguity_penalty",
        "execution_cost_penalty",
        "liquidity_risk_penalty",
        "contradiction_penalized_ev_pass",
    )

    assert watched.raw_edge == d("0.060000")
    assert watched.confidence_adjusted_edge == d("0.048000")
    assert watched.contradiction_severity == d("0.015000")
    assert watched.execution_cost == d("0.018000")
    assert watched.liquidity_risk_penalty == d("0.005000")
    assert watched.total_penalty == d("0.038000")
    assert watched.contradiction_penalized_ev == d("0.010000")
    assert watched.ev_status == "watch"
    assert watched.reason_codes == (
        "candidate_input",
        "low_penalized_ev_watch",
        "source_contradiction_penalty",
        "resolution_ambiguity_penalty",
        "execution_cost_penalty",
        "liquidity_risk_penalty",
    )

    assert_public_numbers_are_decimal(result)


def test_empty_report_is_decimal_zeroed_and_readonly() -> None:
    result = report()

    assert result.candidate_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.average_contradiction_penalized_ev == ZERO
    assert result.max_contradiction_severity == ZERO
    assert result.max_execution_cost == ZERO
    assert result.report_status == "pass"
    assert result.rows == ()
    assert result.reason_codes == ("empty_candidate_set",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numbers_are_decimal(result)


def test_payload_serializes_decimals_as_strings_and_rejects_digest_tampering() -> None:
    module = api()
    result = report(
        candidate(),
        generated_at=datetime(2026, 7, 7, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_candidate_contradiction_penalized_ev_v2_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert payload == result.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["raw_edge"] == "0.080000"
    assert payload["rows"][0]["contradiction_penalized_ev"] == "0.047000"
    assert payload["rows"][0]["derived_validation_digest"] in rendered
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_json_payload_has_no_decimal_int_or_float(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result.rows[0], derived_validation_digest="0" * 64)

    tampered = result.payload
    tampered["rows"][0]["contradiction_penalized_ev"] = "0.999000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_contradiction_penalized_ev_v2_payload(tampered)

    tampered_report = result.payload
    tampered_report["candidate_count"] = "2"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_contradiction_penalized_ev_v2_payload(tampered_report)


def test_dataclasses_are_frozen_final_and_hard_flags_are_enforced() -> None:
    module = api()
    subject = candidate()
    result = report(subject)

    for klass in (
        module.StrategyCandidateContradictionPenalizedEvV2Config,
        module.StrategyCandidateContradictionPenalizedEvV2Candidate,
        module.StrategyCandidateContradictionPenalizedEvV2Row,
        module.StrategyCandidateContradictionPenalizedEvV2Report,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        subject.candidate_id = "other-candidate"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.report_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadCandidate(module.StrategyCandidateContradictionPenalizedEvV2Candidate):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        candidate(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_candidate_contradiction_penalized_ev_v2_payload(
            {**result.payload, "paper_only": False},
        )


def test_rejects_non_decimal_inputs_and_inconsistent_public_dataclasses() -> None:
    module = api()
    valid_candidate = candidate()
    cfg = config()

    with pytest.raises(ValueError, match="candidates"):
        module.build_strategy_candidate_contradiction_penalized_ev_v2(
            "bad",
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="Candidate"):
        module.build_strategy_candidate_contradiction_penalized_ev_v2(
            [object()],
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_candidate_contradiction_penalized_ev_v2(
            [valid_candidate],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_strategy_candidate_contradiction_penalized_ev_v2(
            [valid_candidate],
            config=cfg,
            generated_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="datetime"):
        candidate(evaluated_at=_DatetimeSubclass(2026, 7, 7, 11, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        candidate(evaluated_at=datetime(2026, 7, 7, 11, 45, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="evaluated_at"):
        report(replace(valid_candidate, evaluated_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate candidate_id"):
        report(valid_candidate, valid_candidate)
    with pytest.raises(ValueError, match="Decimal"):
        candidate(forecast_probability=d("0.640000"), taker_cost=0.005)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="exact Decimal"):
        candidate(confidence_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="between zero and one"):
        candidate(source_contradiction=d("1.100000"))
    with pytest.raises(ValueError, match="watch_penalized_ev_floor"):
        config(watch_penalized_ev_floor=d("0.040000"))
    with pytest.raises(ValueError, match="block_contradiction_severity"):
        config(block_contradiction_severity=d("0.020000"))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report(valid_candidate), candidate_count=d("2"))
    with pytest.raises(ValueError, match="raw_edge"):
        replace(report(valid_candidate).rows[0], raw_edge=d("0.010000"))


def test_rejects_unsafe_public_text_and_exposes_no_runtime_side_effect_surfaces() -> None:
    module = api()
    unsafe_terms = (
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

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            candidate(candidate_id=f"candidate-{term}")
        with pytest.raises(ValueError, match="unsafe public"):
            candidate(reason_codes=("candidate_input", f"{term}_reason"))

    source_path = Path(module.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
        if isinstance(node, ast.Call):
            called = node.func
            called_name = ""
            if isinstance(called, ast.Name):
                called_name = called.id
            if isinstance(called, ast.Attribute):
                called_name = called.attr
            assert called_name not in {
                "connect",
                "execute",
                "open",
                "request",
                "send",
                "write",
            }

    assert not (
        set(imports)
        & {
            "asyncio",
            "csv",
            "http",
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
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in unsafe_terms)
    for klass in (
        module.StrategyCandidateContradictionPenalizedEvV2Config,
        module.StrategyCandidateContradictionPenalizedEvV2Candidate,
        module.StrategyCandidateContradictionPenalizedEvV2Row,
        module.StrategyCandidateContradictionPenalizedEvV2Report,
    ):
        for field in fields(klass):
            lowered = field.name.lower()
            assert not any(term in lowered for term in unsafe_terms)
