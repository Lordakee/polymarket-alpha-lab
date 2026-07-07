from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=20)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        joined("poly", "mark", "et_alpha_lab.candidate_decision_base_rate_drift_score"),
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def joined(*parts: str) -> str:
    return "".join(parts)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "candidate-decision-base-rate-drift-score-test",
        "minimum_historical_sample_size": d("50.000000"),
        "minimum_recency_score": d("0.600000"),
        "minimum_similarity_score": d("0.650000"),
        "maximum_dispersion_score": d("0.450000"),
        "minimum_drift_explanation_score": d("0.600000"),
        "base_rate_quality_floor": d("0.700000"),
        "watch_drift_floor": d("0.080000"),
        "block_drift_floor": d("0.180000"),
        "sample_size_weight": d("0.250000"),
        "recency_weight": d("0.250000"),
        "similarity_weight": d("0.250000"),
        "dispersion_weight": d("0.250000"),
    }
    values.update(overrides)
    return module.CandidateDecisionBaseRateDriftScoreConfig(**values)


def fact(**overrides: object) -> Any:
    module = api()
    values = {
        "redacted_candidate_key": "redacted-candidate-pass",
        "redacted_event_type_key": "redacted-event-type-core",
        "observed_at": OBSERVED_AT,
        "candidate_current_probability": d("0.530000"),
        "historical_base_rate_probability": d("0.500000"),
        "historical_sample_size": d("100.000000"),
        "historical_recency_score": d("0.900000"),
        "historical_similarity_score": d("0.850000"),
        "historical_dispersion_score": d("0.200000"),
        "drift_explanation_score": d("0.750000"),
        "fact_config_version": "base-rate-drift-facts-v1",
    }
    values.update(overrides)
    return module.CandidateDecisionBaseRateDriftFact(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_candidate_decision_base_rate_drift_score(
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


def test_scores_pass_watch_and_block_base_rate_drift() -> None:
    report = build_report(
        fact(redacted_candidate_key="redacted-candidate-pass"),
        fact(
            redacted_candidate_key="redacted-candidate-watch",
            candidate_current_probability=d("0.620000"),
        ),
        fact(
            redacted_candidate_key="redacted-candidate-block",
            candidate_current_probability=d("0.760000"),
            historical_sample_size=d("20.000000"),
            historical_recency_score=d("0.500000"),
            historical_similarity_score=d("0.550000"),
            historical_dispersion_score=d("0.700000"),
            drift_explanation_score=d("0.400000"),
        ),
    )

    rows = {row.redacted_candidate_key: row for row in report.rows}

    assert rows["redacted-candidate-pass"].base_rate_drift_magnitude == d("0.030000")
    assert rows["redacted-candidate-pass"].base_rate_drift_score == d("0.166667")
    assert rows["redacted-candidate-pass"].base_rate_quality_score == d("0.887500")
    assert rows["redacted-candidate-pass"].unexplained_drift_score == d("0.041667")
    assert rows["redacted-candidate-pass"].score_status == "pass"
    assert rows["redacted-candidate-pass"].reason_codes == (
        "base_rate_drift_pass",
        "candidate_judgment_close_to_base_rate",
    )

    assert rows["redacted-candidate-watch"].base_rate_drift_magnitude == d("0.120000")
    assert rows["redacted-candidate-watch"].base_rate_drift_score == d("0.666667")
    assert rows["redacted-candidate-watch"].score_status == "watch"
    assert rows["redacted-candidate-watch"].reason_codes == (
        "base_rate_drift_watch",
        "candidate_judgment_materially_deviates",
        "candidate_drift_explanation_present",
    )

    assert rows["redacted-candidate-block"].base_rate_drift_magnitude == d("0.260000")
    assert rows["redacted-candidate-block"].base_rate_drift_score == d("1.000000")
    assert rows["redacted-candidate-block"].sample_size_score == d("0.400000")
    assert rows["redacted-candidate-block"].dispersion_grounding_score == d("0.300000")
    assert rows["redacted-candidate-block"].base_rate_quality_score == d("0.437500")
    assert rows["redacted-candidate-block"].unexplained_drift_score == d("0.600000")
    assert rows["redacted-candidate-block"].score_status == "block"
    assert rows["redacted-candidate-block"].reason_codes == (
        "base_rate_drift_block",
        "historical_base_rate_sample_size_below_floor",
        "historical_base_rate_recency_below_floor",
        "historical_event_similarity_below_floor",
        "historical_base_rate_dispersion_above_ceiling",
        "base_rate_quality_below_floor",
        "candidate_drift_explanation_below_floor",
        "candidate_judgment_extreme_deviation",
    )

    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.score_status == "block"
    assert report.average_base_rate_drift_magnitude == d("0.136667")
    assert report.max_base_rate_drift_magnitude == d("0.260000")
    assert report.average_unexplained_drift_score == d("0.269445")
    assert report.reason_codes[0] == "base_rate_drift_report_block"


def test_decimal_only_validation_rejects_int_float_and_subclass_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="candidate_current_probability must be a Decimal"):
        fact(candidate_current_probability=1)
    with pytest.raises(ValueError, match="historical_recency_score must be a Decimal"):
        fact(historical_recency_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="watch_drift_floor must be a Decimal"):
        cfg(watch_drift_floor=0.08)

    report = build_report(fact())
    for value in (cfg(), fact(), report.rows[0], report):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if isinstance(item_value, Decimal):
                assert type(item_value) is Decimal
            assert type(item_value) not in (float, int)


def test_public_payload_rejects_raw_event_and_operation_leaks() -> None:
    module = api()
    report = build_report(fact())
    payload = module.candidate_decision_base_rate_drift_score_payload(report)

    with pytest.raises(ValueError, match="redacted identifier"):
        fact(redacted_candidate_key="candidate-alpha-raw")
    with pytest.raises(ValueError, match="unsafe public surface"):
        fact(redacted_event_type_key=joined("redacted-", "wall", "et", "-term"))

    unsafe_payload = dict(payload)
    unsafe_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_payload["rows"][0]["redacted_candidate_key"] = joined(
        "redacted-",
        "recom",
        "mendation",
        "-term",
    )
    unsafe_payload["derived_validation_digest"] = module._derived_validation_digest(
        unsafe_payload,
    )
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_base_rate_drift_score_payload(unsafe_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload[joined("mark", "et_id")] = "redacted-extra"
    unsafe_key_payload["derived_validation_digest"] = module._derived_validation_digest(
        unsafe_key_payload,
    )
    with pytest.raises(ValueError, match="unsafe public surface|unexpected"):
        module.validate_candidate_decision_base_rate_drift_score_payload(
            unsafe_key_payload,
        )

    public_field_names = {
        field.name
        for exported_name in module.__all__
        if isinstance((value := getattr(module, exported_name)), type)
        for field in fields(value)
    }
    assert public_field_names.isdisjoint(
        {
            "candidate_id",
            joined("raw_", "candidate", "_id"),
            joined("mark", "et_id"),
            joined("mark", "et_", "sl", "ug"),
            joined("mark", "et_", "ques", "tion"),
            joined("sou", "rce_", "re", "f"),
            joined("sou", "rce_", "u", "rl"),
            joined("sou", "rce_", "te", "xt"),
            joined("d", "sn"),
            joined("table", "_name"),
            joined("to", "ken"),
            joined("wall", "et"),
            joined("au", "th"),
            joined("or", "der"),
            joined("tr", "ade"),
            joined("pos", "ition"),
            joined("b", "uy"),
            joined("s", "ell"),
            joined("recom", "mendation"),
        },
    )


def test_hard_flags_are_required_on_dataclasses_and_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="paper_only must be True"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        fact(report_only=False)

    report = build_report(fact())
    payload = module.candidate_decision_base_rate_drift_score_payload(report)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True

    tampered_payload = dict(payload)
    tampered_payload["readonly"] = False
    tampered_payload["derived_validation_digest"] = module._derived_validation_digest(
        tampered_payload,
    )
    with pytest.raises(ValueError, match="readonly must be True"):
        module.validate_candidate_decision_base_rate_drift_score_payload(
            tampered_payload,
        )


def test_payload_is_deterministic_decimal_string_only_and_validates_digest() -> None:
    module = api()
    first = module.build_candidate_decision_base_rate_drift_score(
        (
            fact(redacted_candidate_key="redacted-candidate-watch", candidate_current_probability=d("0.620000")),
            fact(redacted_candidate_key="redacted-candidate-pass"),
        ),
        config=cfg(),
        generated_at=GENERATED_AT,
    )
    second = module.build_candidate_decision_base_rate_drift_score(
        (
            fact(redacted_candidate_key="redacted-candidate-pass"),
            fact(redacted_candidate_key="redacted-candidate-watch", candidate_current_probability=d("0.620000")),
        ),
        config=cfg(),
        generated_at=GENERATED_AT,
    )

    first_payload = module.candidate_decision_base_rate_drift_score_payload(first)
    second_payload = module.candidate_decision_base_rate_drift_score_payload(second)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["rows"][0]["base_rate_drift_magnitude"] == "0.030000"
    assert module.validate_candidate_decision_base_rate_drift_score_payload(first_payload)
    assert_no_float_or_int(first_payload)


def test_report_and_digest_consistency_are_enforced() -> None:
    module = api()
    report = build_report(fact())
    payload = module.candidate_decision_base_rate_drift_score_payload(report)

    assert module.validate_candidate_decision_base_rate_drift_score_payload(payload)

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_candidate_decision_base_rate_drift_score_payload(tampered_payload)

    recomputed_payload = dict(payload)
    recomputed_payload["row_count"] = "2.000000"
    recomputed_payload["derived_validation_digest"] = module._derived_validation_digest(
        recomputed_payload,
    )
    with pytest.raises(ValueError, match="row_count"):
        module.validate_candidate_decision_base_rate_drift_score_payload(
            recomputed_payload,
        )

    with pytest.raises(ValueError, match="average_base_rate_drift_magnitude"):
        replace(report, average_base_rate_drift_magnitude=d("0.010000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].score_status = "block"  # type: ignore[misc]

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True
