from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal

import pytest


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_source_disagreement_escalation_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def escalation_input(
    *,
    candidate_id: str = "cand-fed-cut",
    market_slug: str = "fed-cuts-july-2026",
    contradiction_rate: str = "0.050000",
    source_reliability_spread: str = "0.020000",
    recency_gap_hours: str = "1.000000",
    time_to_resolution_hours: str = "72.000000",
    market_move_since_disagreement: str = "0.010000",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.StrategyCandidateSourceDisagreementEscalationV10Input(
        candidate_id=candidate_id,
        market_slug=market_slug,
        contradiction_rate=d(contradiction_rate),
        source_reliability_spread=d(source_reliability_spread),
        recency_gap_hours=d(recency_gap_hours),
        time_to_resolution_hours=d(time_to_resolution_hours),
        market_move_since_disagreement=d(market_move_since_disagreement),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def evaluate(*, config=None, **overrides):
    module = api()
    return module.evaluate_strategy_candidate_source_disagreement_escalation_v10(
        escalation_input(**overrides),
        config=config,
    )


def _walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value


def test_clear_source_disagreement_keeps_research_signal_readonly():
    result = evaluate()

    assert is_dataclass(result)
    assert result.config_version == (
        "strategy-candidate-source-disagreement-escalation-v10"
    )
    assert result.escalation_status == "clear"
    assert result.escalation_action == "keep_research_signal"
    assert result.recency_gap_pressure == d("0.041667")
    assert result.resolution_urgency == d("0.000000")
    assert result.escalation_priority_score == d("0.026750")
    assert result.reason_codes == (
        "candidate_source_disagreement_escalation_v10_clear",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert len(result.validation_digest) == 64
    int(result.validation_digest, 16)


def test_critical_disagreement_pauses_candidate_signal_with_full_reason_stack():
    result = evaluate(
        contradiction_rate="0.750000",
        source_reliability_spread="0.450000",
        recency_gap_hours="36.000000",
        time_to_resolution_hours="4.000000",
        market_move_since_disagreement="0.180000",
    )

    assert result.escalation_status == "critical"
    assert result.escalation_action == "pause_candidate_signal"
    assert result.recency_gap_pressure == d("1.000000")
    assert result.resolution_urgency == d("1.000000")
    assert result.escalation_priority_score == d("0.692000")
    assert result.reason_codes == (
        "candidate_source_disagreement_escalation_v10_critical",
        "candidate_source_disagreement_escalation_v10_contradiction_rate_high",
        "candidate_source_disagreement_escalation_v10_reliability_spread_high",
        "candidate_source_disagreement_escalation_v10_recency_gap_stale",
        "candidate_source_disagreement_escalation_v10_resolution_urgent",
        "candidate_source_disagreement_escalation_v10_market_move_material",
    )


def test_high_priority_near_resolution_escalates_research_lead():
    result = evaluate(
        contradiction_rate="0.420000",
        source_reliability_spread="0.250000",
        recency_gap_hours="12.000000",
        time_to_resolution_hours="12.000000",
        market_move_since_disagreement="0.060000",
    )

    assert result.escalation_status == "high"
    assert result.escalation_action == "escalate_research_lead"
    assert result.recency_gap_pressure == d("0.500000")
    assert result.resolution_urgency == d("0.857143")
    assert result.escalation_priority_score == d("0.431429")
    assert result.reason_codes == (
        "candidate_source_disagreement_escalation_v10_high",
        "candidate_source_disagreement_escalation_v10_contradiction_rate_high",
        "candidate_source_disagreement_escalation_v10_reliability_spread_high",
        "candidate_source_disagreement_escalation_v10_resolution_near",
        "candidate_source_disagreement_escalation_v10_market_move_watch",
    )


def test_payload_serializes_decimal_strings_and_contains_no_floats():
    module = api()
    result = evaluate(
        contradiction_rate="0.420000",
        source_reliability_spread="0.250000",
        recency_gap_hours="12.000000",
        time_to_resolution_hours="12.000000",
        market_move_since_disagreement="0.060000",
    )

    payload = module.strategy_candidate_source_disagreement_escalation_v10_payload(
        result,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert result.payload == payload
    assert payload["config_version"] == (
        "strategy-candidate-source-disagreement-escalation-v10"
    )
    assert payload["candidate_id"] == "cand-fed-cut"
    assert payload["contradiction_rate"] == "0.420000"
    assert payload["recency_gap_pressure"] == "0.500000"
    assert payload["resolution_urgency"] == "0.857143"
    assert payload["escalation_priority_score"] == "0.431429"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["validation_digest"] == result.validation_digest
    assert '"0.431429"' in encoded
    assert all(type(value) is not float for value in _walk(payload))


def test_config_overrides_thresholds_and_is_carried_into_digest():
    module = api()
    config = module.StrategyCandidateSourceDisagreementEscalationV10Config(
        config_version="strategy-candidate-source-disagreement-escalation-test-v10",
        watch_priority_score=d("0.020000"),
    )

    result = evaluate(config=config)

    assert result.config_version == (
        "strategy-candidate-source-disagreement-escalation-test-v10"
    )
    assert result.escalation_priority_score == d("0.026750")
    assert result.escalation_status == "watch"
    assert result.escalation_action == "queue_source_recheck"
    assert result.reason_codes == (
        "candidate_source_disagreement_escalation_v10_watch",
    )
    assert len(result.validation_digest) == 64
    assert result.payload["config_version"] == result.config_version
    assert result.payload["validation_digest"] == result.validation_digest


def test_tamper_evident_validation_recomputes_result_fields():
    result = evaluate()

    with pytest.raises(ValueError, match="escalation_priority_score must match"):
        replace(result, escalation_priority_score=d("0.000000"))
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)

    module = api()
    with pytest.raises(ValueError, match="config_version"):
        module.StrategyCandidateSourceDisagreementEscalationV10Config(
            config_version=" strategy-candidate-source-disagreement-escalation-v10",
        )


def test_payload_rejects_unsafe_public_dicts_and_flag_downgrades():
    module = api()
    result = evaluate()

    assert module.strategy_candidate_source_disagreement_escalation_v10_payload(
        result.payload,
    ) == result.payload

    downgraded = dict(result.payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly must be True"):
        module.strategy_candidate_source_disagreement_escalation_v10_payload(
            downgraded,
        )

    missing_flag = dict(result.payload)
    missing_flag.pop("paper_only")
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.strategy_candidate_source_disagreement_escalation_v10_payload(
            missing_flag,
        )

    unsafe_key = dict(result.payload)
    unsafe_key["wall" + "et"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_candidate_source_disagreement_escalation_v10_payload(
            unsafe_key,
        )

    unsafe_value = dict(result.payload)
    unsafe_value["public_note"] = "redacted " + "wall" + "et"
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_candidate_source_disagreement_escalation_v10_payload(
            unsafe_value,
        )


def test_validation_rejects_non_decimal_precision_nonfinite_and_unsafe_flags():
    module = api()

    with pytest.raises(ValueError, match="contradiction_rate must be a Decimal"):
        module.StrategyCandidateSourceDisagreementEscalationV10Input(
            candidate_id="cand-fed-cut",
            market_slug="fed-cuts-july-2026",
            contradiction_rate=0.5,
            source_reliability_spread=d("0.100000"),
            recency_gap_hours=d("1.000000"),
            time_to_resolution_hours=d("72.000000"),
            market_move_since_disagreement=d("0.010000"),
        )

    with pytest.raises(ValueError, match="source_reliability_spread must use"):
        escalation_input(source_reliability_spread="0.1000001")

    with pytest.raises(ValueError, match="recency_gap_hours must be finite"):
        escalation_input(recency_gap_hours="NaN")

    with pytest.raises(ValueError, match="market_move_since_disagreement must be between 0 and 1"):
        escalation_input(market_move_since_disagreement="1.000001")

    with pytest.raises(ValueError, match="time_to_resolution_hours must be nonnegative"):
        escalation_input(time_to_resolution_hours="-1.000000")

    with pytest.raises(ValueError, match="readonly must be True"):
        escalation_input(readonly=False)

    result = evaluate()
    with pytest.raises(FrozenInstanceError):
        result.escalation_status = "critical"  # type: ignore[misc]


def test_public_surface_stays_readonly_and_avoids_live_trading_terms():
    module = api()
    source = module.__loader__.get_source(module.__name__)

    assert source is not None
    lowered = source.lower()
    assert "requests." not in lowered
    assert "sqlite" not in lowered
    assert "open(" not in lowered
    assert "auth_token" not in lowered
    assert "private_key" not in lowered
    assert "place_order" not in lowered
    assert "wallet" not in lowered
