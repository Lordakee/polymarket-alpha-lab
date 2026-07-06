from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 11, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_decision_margin_of_safety_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "strategy-candidate-decision-margin-of-safety-score-v2-test",
        "required_margin_of_safety": d("0.030000"),
        "thin_edge_floor": d("0.010000"),
        "minimum_source_confidence_score": d("0.600000"),
        "source_confidence_boost_weight": d("0.100000"),
        "thin_edge_penalty_weight": d("0.250000"),
        "risk_penalty_weight": d("0.100000"),
        "liquidity_risk_weight": d("0.400000"),
        "resolution_risk_weight": d("0.400000"),
        "correlation_risk_weight": d("0.200000"),
        "high_risk_penalty_floor": d("0.050000"),
        "ready_score_floor": d("0.700000"),
        "watch_score_floor": d("0.400000"),
    }
    values.update(overrides)
    return module.StrategyCandidateDecisionMarginOfSafetyScoreV2Config(**values)


def observation(**overrides: object) -> Any:
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_id": "market-alpha",
        "observed_at": OBSERVED_AT,
        "cost_adjusted_edge": d("0.036000"),
        "source_confidence_score": d("0.900000"),
        "liquidity_risk_score": d("0.100000"),
        "resolution_risk_score": d("0.100000"),
        "correlation_risk_score": d("0.100000"),
        "source_count": d("4.000000"),
        "independent_source_count": d("2.000000"),
        "source_config_version": "source-config-v1",
    }
    values.update(overrides)
    return module.StrategyCandidateDecisionMarginOfSafetyScoreV2Observation(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_strategy_candidate_decision_margin_of_safety_score_v2(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def assert_no_float_or_int(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)
        return
    assert type(value) not in (float, int)


def unsafe_terms() -> tuple[str, ...]:
    return (
        "".join(("li", "ve")),
        "".join(("au", "th")),
        "".join(("wall", "et")),
        "".join(("or", "der")),
        "".join(("net", "work")),
        "".join(("data", "base")),
        "".join(("per", "sist")),
        "".join(("sign", "ing")),
        "".join(("muta", "tion")),
        "".join(("b", "uy")),
        "".join(("s", "ell")),
        "".join(("tr", "ade")),
    )


def test_margin_of_safety_scoring_and_decimal_report_rollups() -> None:
    report = build_report(
        observation(candidate_id="candidate-alpha"),
        observation(
            candidate_id="candidate-beta",
            cost_adjusted_edge=d("0.018000"),
            source_confidence_score=d("0.600000"),
        ),
    )

    rows = {row.candidate_id: row for row in report.rows}
    assert rows["candidate-alpha"].raw_margin_of_safety == d("0.006000")
    assert rows["candidate-alpha"].margin_of_safety_score == d("1.000000")
    assert rows["candidate-alpha"].risk_penalty == d("0.010000")
    assert rows["candidate-alpha"].source_confidence_boost == d("0.030000")
    assert rows["candidate-alpha"].final_margin_of_safety_score == d("1.000000")
    assert rows["candidate-alpha"].score_status == "ready"

    assert rows["candidate-beta"].raw_margin_of_safety == d("-0.012000")
    assert rows["candidate-beta"].margin_of_safety_score == d("0.600000")
    assert rows["candidate-beta"].source_confidence_boost == d("0.000000")
    assert rows["candidate-beta"].final_margin_of_safety_score == d("0.590000")
    assert rows["candidate-beta"].score_status == "watch"
    assert "negative_margin_of_safety" in rows["candidate-beta"].reason_codes

    assert report.row_count == d("2.000000")
    assert report.ready_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.score_status == "watch"
    assert report.average_margin_of_safety_score == d("0.795000")
    assert report.average_source_confidence_boost == d("0.015000")
    assert report.max_risk_penalty == d("0.010000")

    for item in (cfg(), *report.rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if field.name.endswith(
                (
                    "_count",
                    "_score",
                    "_edge",
                    "_risk",
                    "_weight",
                    "_floor",
                    "_penalty",
                    "_boost",
                    "_safety",
                ),
            ):
                assert type(value) is Decimal


def test_thin_edge_penalties_block_weak_candidates() -> None:
    report = build_report(
        observation(
            candidate_id="candidate-thin",
            cost_adjusted_edge=d("0.006000"),
        ),
    )

    row = report.rows[0]
    assert row.margin_of_safety_score == d("0.200000")
    assert row.thin_edge_penalty == d("0.100000")
    assert row.source_confidence_boost == d("0.030000")
    assert row.final_margin_of_safety_score == d("0.120000")
    assert row.score_status == "blocked"
    assert row.reason_codes[:3] == (
        "margin_of_safety_blocked_score",
        "negative_margin_of_safety",
        "thin_edge_penalty",
    )
    assert report.blocked_count == d("1.000000")
    assert report.score_status == "blocked"


def test_source_confidence_boost_can_lift_margin_status() -> None:
    report = build_report(
        observation(
            candidate_id="candidate-high-confidence",
            cost_adjusted_edge=d("0.021000"),
            source_confidence_score=d("0.900000"),
        ),
        observation(
            candidate_id="candidate-base-confidence",
            cost_adjusted_edge=d("0.021000"),
            source_confidence_score=d("0.600000"),
        ),
    )

    rows = {row.candidate_id: row for row in report.rows}
    assert rows["candidate-high-confidence"].margin_of_safety_score == d("0.700000")
    assert rows["candidate-high-confidence"].source_confidence_boost == d("0.030000")
    assert rows["candidate-high-confidence"].final_margin_of_safety_score == d("0.720000")
    assert rows["candidate-high-confidence"].score_status == "ready"
    assert "source_confidence_boost" in rows["candidate-high-confidence"].reason_codes

    assert rows["candidate-base-confidence"].source_confidence_boost == d("0.000000")
    assert rows["candidate-base-confidence"].final_margin_of_safety_score == d("0.690000")
    assert rows["candidate-base-confidence"].score_status == "watch"


def test_payload_serialization_and_validation_are_canonical() -> None:
    module = api()
    report = build_report(observation())
    payload = module.strategy_candidate_decision_margin_of_safety_score_v2_payload(report)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["average_margin_of_safety_score"] == "1.000000"
    assert payload["rows"][0]["cost_adjusted_edge"] == "0.036000"
    assert payload["rows"][0]["source_confidence_boost"] == "0.030000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert module.validate_strategy_candidate_decision_margin_of_safety_score_v2_payload(
        payload,
    )
    assert_no_float_or_int(payload)
    json.dumps(payload, sort_keys=True)


def test_dataclasses_are_frozen_and_reject_subclassing() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_STRATEGY_CANDIDATE_DECISION_MARGIN_OF_SAFETY_SCORE_V2_CONFIG_VERSION",
        "StrategyCandidateDecisionMarginOfSafetyScoreV2Config",
        "StrategyCandidateDecisionMarginOfSafetyScoreV2Observation",
        "StrategyCandidateDecisionMarginOfSafetyScoreV2Row",
        "StrategyCandidateDecisionMarginOfSafetyScoreV2Report",
        "build_strategy_candidate_decision_margin_of_safety_score_v2",
        "strategy_candidate_decision_margin_of_safety_score_v2_payload",
        "validate_strategy_candidate_decision_margin_of_safety_score_v2_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(observation())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].score_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.StrategyCandidateDecisionMarginOfSafetyScoreV2Config):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(
            module.StrategyCandidateDecisionMarginOfSafetyScoreV2Observation,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.StrategyCandidateDecisionMarginOfSafetyScoreV2Row):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.StrategyCandidateDecisionMarginOfSafetyScoreV2Report):
            pass

    with pytest.raises(ValueError, match="cost_adjusted_edge must be a Decimal"):
        observation(cost_adjusted_edge=DecimalSubclass("0.020000"))


def test_hard_flags_are_enforced() -> None:
    module = api()
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        cfg(readonly=False)

    report = build_report(observation())
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(report, report_only=False)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert module.strategy_candidate_decision_margin_of_safety_score_v2_payload(report)[
        "readonly"
    ] is True

    payload = module.strategy_candidate_decision_margin_of_safety_score_v2_payload(report)
    flag_payload = dict(payload)
    flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.validate_strategy_candidate_decision_margin_of_safety_score_v2_payload(
            flag_payload,
        )


def test_digest_tampering_is_rejected_for_report_and_payload() -> None:
    module = api()
    report = build_report(observation())

    with pytest.raises(ValueError, match="average_margin_of_safety_score"):
        replace(report, average_margin_of_safety_score=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.strategy_candidate_decision_margin_of_safety_score_v2_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_strategy_candidate_decision_margin_of_safety_score_v2_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "final_margin_of_safety_score", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_decision_margin_of_safety_score_v2_payload(report)


def test_unsafe_public_payload_keys_and_values_are_rejected() -> None:
    module = api()

    for term in unsafe_terms():
        with pytest.raises(ValueError, match="unsafe public surface"):
            observation(candidate_id=f"candidate-{term}")

    payload = module.strategy_candidate_decision_margin_of_safety_score_v2_payload(
        build_report(observation()),
    )
    unsafe_key_payload = dict(payload)
    unsafe_key_payload["".join(("wall", "et"))] = "forbidden"
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_strategy_candidate_decision_margin_of_safety_score_v2_payload(
            unsafe_key_payload,
        )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_value_payload["rows"][0]["candidate_id"] = (
        "candidate-" + "".join(("tr", "ade"))
    )
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_strategy_candidate_decision_margin_of_safety_score_v2_payload(
            unsafe_value_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["row_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        module.validate_strategy_candidate_decision_margin_of_safety_score_v2_payload(
            numeric_payload,
        )


def test_module_omits_unsafe_public_surfaces() -> None:
    module = api()
    public_names = set(module.__all__) | {
        name for name in dir(module) if not name.startswith("_")
    }
    for public_name in public_names:
        lower_name = public_name.lower()
        assert "db" not in lower_name
        for term in unsafe_terms():
            assert term not in lower_name

    source = inspect.getsource(module)
    for forbidden in (
        "requests",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "subprocess",
        "Path(",
        "open(",
        ".write(",
        ".read(",
    ):
        assert forbidden not in source
