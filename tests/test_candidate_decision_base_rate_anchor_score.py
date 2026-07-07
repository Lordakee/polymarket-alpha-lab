from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=15)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        joined("poly", "mark", "et_alpha_lab.candidate_decision_base_rate_anchor_score"),
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def joined(*parts: str) -> str:
    return "".join(parts)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "candidate-decision-base-rate-anchor-score-test",
        "minimum_base_rate_sample_size": d("30.000000"),
        "minimum_recency_score": d("0.600000"),
        "minimum_similarity_score": d("0.650000"),
        "maximum_dispersion_score": d("0.400000"),
        "minimum_specialist_calibration_score": d("0.650000"),
        "minimum_deviation_justification_score": d("0.600000"),
        "material_deviation_floor": d("0.050000"),
        "sample_size_weight": d("0.200000"),
        "recency_weight": d("0.150000"),
        "similarity_weight": d("0.200000"),
        "dispersion_weight": d("0.150000"),
        "specialist_calibration_weight": d("0.150000"),
        "deviation_justification_weight": d("0.150000"),
        "pass_score_floor": d("0.750000"),
        "watch_score_floor": d("0.500000"),
    }
    values.update(overrides)
    return module.CandidateDecisionBaseRateAnchorScoreConfig(**values)


def fact(**overrides: object) -> Any:
    module = api()
    values = {
        "redacted_candidate_id": "candidate-redacted-alpha",
        "redacted_team_id": "team-redacted-research",
        "redacted_domain_id": "domain-redacted-elections",
        "observed_at": OBSERVED_AT,
        "candidate_forecast_probability": d("0.680000"),
        "base_rate_probability": d("0.620000"),
        "base_rate_sample_size": d("60.000000"),
        "base_rate_recency_score": d("0.900000"),
        "base_rate_similarity_score": d("0.800000"),
        "base_rate_dispersion_score": d("0.200000"),
        "specialist_calibration_score": d("0.850000"),
        "deviation_justification_score": d("0.750000"),
        "base_rate_ref": "redacted-base-rate-ref-alpha",
        "specialist_calibration_ref": "redacted-calibration-ref-alpha",
        "deviation_justification_ref": "redacted-deviation-ref-alpha",
        "fact_config_version": "base-rate-facts-v1",
    }
    values.update(overrides)
    return module.CandidateDecisionBaseRateAnchorFact(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_candidate_decision_base_rate_anchor_score(
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


def test_scores_structured_base_rate_facts_with_deterministic_reason_codes() -> None:
    report = build_report(
        fact(
            redacted_candidate_id="candidate-redacted-weak",
            base_rate_sample_size=d("12.000000"),
            base_rate_recency_score=d("0.500000"),
            base_rate_similarity_score=d("0.550000"),
            base_rate_dispersion_score=d("0.700000"),
            specialist_calibration_score=d("0.500000"),
            deviation_justification_score=d("0.400000"),
            candidate_forecast_probability=d("0.740000"),
            base_rate_probability=d("0.620000"),
            base_rate_ref="redacted-base-rate-ref-weak",
            specialist_calibration_ref="redacted-calibration-ref-weak",
            deviation_justification_ref="redacted-deviation-ref-weak",
        ),
        fact(redacted_candidate_id="candidate-redacted-alpha"),
    )

    rows = {row.redacted_candidate_id: row for row in report.rows}
    passed = rows["candidate-redacted-alpha"]
    weak = rows["candidate-redacted-weak"]

    assert tuple(row.redacted_candidate_id for row in report.rows) == (
        "candidate-redacted-alpha",
        "candidate-redacted-weak",
    )
    assert passed.rank == d("1.000000")
    assert passed.forecast_base_rate_deviation == d("0.060000")
    assert passed.sample_size_score == d("1.000000")
    assert passed.dispersion_grounding_score == d("0.800000")
    assert passed.base_rate_anchor_score == d("0.855000")
    assert passed.score_status == "pass"
    assert passed.reason_codes == (
        "base_rate_anchor_pass",
        "candidate_forecast_materially_deviates",
        "candidate_deviation_justified",
    )

    assert weak.sample_size_score == d("0.400000")
    assert weak.dispersion_grounding_score == d("0.300000")
    assert weak.base_rate_anchor_score == d("0.445000")
    assert weak.score_status == "block"
    assert weak.reason_codes == (
        "base_rate_anchor_blocked_score",
        "base_rate_sample_size_below_floor",
        "base_rate_recency_below_floor",
        "base_rate_similarity_below_floor",
        "base_rate_dispersion_above_ceiling",
        "specialist_calibration_below_floor",
        "candidate_deviation_justification_below_floor",
        "candidate_forecast_materially_deviates",
        "candidate_forecast_deviation_unjustified",
    )

    assert report.row_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.score_status == "block"
    assert report.average_base_rate_anchor_score == d("0.650000")
    assert report.max_forecast_base_rate_deviation == d("0.120000")
    assert report.reason_codes[:2] == (
        "base_rate_anchor_report_blocked",
        "base_rate_anchor_pass",
    )


def test_public_status_vocabulary_uses_pass_watch_block_not_legacy_values() -> None:
    module = api()
    report = build_report(
        fact(redacted_candidate_id="candidate-redacted-pass"),
        fact(
            redacted_candidate_id="candidate-redacted-watch",
            base_rate_recency_score=d("0.600000"),
            base_rate_similarity_score=d("0.650000"),
            base_rate_dispersion_score=d("0.400000"),
            specialist_calibration_score=d("0.650000"),
            deviation_justification_score=d("0.600000"),
            base_rate_ref="redacted-base-rate-ref-watch",
            specialist_calibration_ref="redacted-calibration-ref-watch",
            deviation_justification_ref="redacted-deviation-ref-watch",
        ),
        fact(
            redacted_candidate_id="candidate-redacted-weak",
            base_rate_sample_size=d("12.000000"),
            base_rate_recency_score=d("0.500000"),
            base_rate_similarity_score=d("0.550000"),
            base_rate_dispersion_score=d("0.700000"),
            specialist_calibration_score=d("0.500000"),
            deviation_justification_score=d("0.400000"),
            candidate_forecast_probability=d("0.740000"),
            base_rate_probability=d("0.620000"),
            base_rate_ref="redacted-base-rate-ref-weak",
            specialist_calibration_ref="redacted-calibration-ref-weak",
            deviation_justification_ref="redacted-deviation-ref-weak",
        ),
    )

    rows = {row.redacted_candidate_id: row for row in report.rows}
    assert rows["candidate-redacted-pass"].score_status == "pass"
    assert rows["candidate-redacted-watch"].score_status == "watch"
    assert rows["candidate-redacted-weak"].score_status == "block"
    assert report.score_status == "block"

    payload = module.candidate_decision_base_rate_anchor_score_payload(report)
    payload_statuses = {payload["score_status"]} | {
        row["score_status"] for row in payload["rows"]
    }
    assert payload_statuses == {"pass", "watch", "block"}
    assert "ready" not in payload_statuses
    assert "blocked" not in payload_statuses

    legacy_report_payload = dict(payload)
    legacy_report_payload["score_status"] = "blocked"
    legacy_report_payload["derived_validation_digest"] = module._derived_validation_digest(
        legacy_report_payload,
    )
    with pytest.raises(ValueError, match="score_status"):
        module.validate_candidate_decision_base_rate_anchor_score_payload(
            legacy_report_payload,
        )

    legacy_row_payload = dict(payload)
    legacy_row_payload["rows"] = [dict(row) for row in payload["rows"]]
    legacy_row_payload["rows"][0]["score_status"] = "ready"
    legacy_row_payload["derived_validation_digest"] = module._derived_validation_digest(
        legacy_row_payload,
    )
    with pytest.raises(ValueError, match="score_status"):
        module.validate_candidate_decision_base_rate_anchor_score_payload(
            legacy_row_payload,
        )


def test_payload_serialization_validation_and_redacted_reference_safety() -> None:
    module = api()
    report = build_report(fact())
    payload = module.candidate_decision_base_rate_anchor_score_payload(report)

    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["row_count"] == "1.000000"
    assert payload["average_base_rate_anchor_score"] == "0.855000"
    assert payload["rows"][0]["base_rate_anchor_score"] == "0.855000"
    assert payload["rows"][0]["redacted_refs"] == [
        "redacted-base-rate-ref-alpha",
        "redacted-calibration-ref-alpha",
        "redacted-deviation-ref-alpha",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert module.validate_candidate_decision_base_rate_anchor_score_payload(payload)
    assert_no_float_or_int(payload)

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_candidate_decision_base_rate_anchor_score_payload(tampered_payload)

    unsafe_ref_payload = dict(payload)
    unsafe_ref_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_ref_payload["rows"][0]["redacted_refs"] = [
        "redacted-base-rate-ref-alpha",
        "https://example.invalid/raw",
        "redacted-deviation-ref-alpha",
    ]
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_base_rate_anchor_score_payload(
            unsafe_ref_payload,
        )


def test_public_payload_validation_rejects_recomputed_inconsistent_payloads() -> None:
    module = api()
    report = build_report(fact())
    payload = module.candidate_decision_base_rate_anchor_score_payload(report)

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.000000"
    tampered_payload["derived_validation_digest"] = module._derived_validation_digest(
        tampered_payload,
    )

    with pytest.raises(ValueError, match="row_count"):
        module.validate_candidate_decision_base_rate_anchor_score_payload(
            tampered_payload,
        )

    deviation_payload = dict(payload)
    deviation_payload["rows"] = [dict(payload["rows"][0])]
    deviation_payload["rows"][0]["forecast_base_rate_deviation"] = "0.010000"
    deviation_payload["max_forecast_base_rate_deviation"] = "0.010000"
    deviation_payload["derived_validation_digest"] = module._derived_validation_digest(
        deviation_payload,
    )

    with pytest.raises(ValueError, match="forecast_base_rate_deviation"):
        module.validate_candidate_decision_base_rate_anchor_score_payload(
            deviation_payload,
        )


def test_unsafe_decision_operation_terms_are_rejected_even_with_matching_digest() -> None:
    module = api()
    report = build_report(fact())
    payload = module.candidate_decision_base_rate_anchor_score_payload(report)

    unsafe_payload = dict(payload)
    unsafe_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_payload["rows"][0]["redacted_candidate_id"] = joined(
        "candidate-redacted-",
        "recom",
        "mendation",
    )
    unsafe_payload["derived_validation_digest"] = module._derived_validation_digest(
        unsafe_payload,
    )

    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_candidate_decision_base_rate_anchor_score_payload(
            unsafe_payload,
        )

    with pytest.raises(ValueError, match="unsafe public surface"):
        fact(redacted_candidate_id="candidate-redacted-sizing")
    with pytest.raises(ValueError, match="unsafe public surface"):
        fact(redacted_candidate_id=joined("redacted-", "trad", "ing-term"))
    with pytest.raises(ValueError, match="unsafe public surface"):
        fact(base_rate_ref=joined("redacted-", "execu", "tion-term"))
    with pytest.raises(ValueError, match="unsafe public surface"):
        fact(base_rate_ref=joined("redacted-", "sou", "rce-term"))
    with pytest.raises(ValueError, match="unsafe public surface"):
        fact(base_rate_ref=joined("redacted-", "ac", "tion-term"))


def test_public_identifiers_must_be_redacted_and_direction_neutral() -> None:
    module = api()

    with pytest.raises(ValueError, match="redacted identifier"):
        fact(redacted_candidate_id="public-alpha")
    with pytest.raises(ValueError, match="redacted identifier"):
        fact(redacted_team_id="research-desk-alpha")
    with pytest.raises(ValueError, match="redacted identifier"):
        fact(redacted_domain_id="event-family-alpha")

    above = fact(
        redacted_candidate_id="redacted-candidate-above",
        candidate_forecast_probability=d("0.680000"),
        base_rate_probability=d("0.620000"),
        base_rate_ref="redacted-base-rate-ref-above",
        specialist_calibration_ref="redacted-calibration-ref-above",
        deviation_justification_ref="redacted-deviation-ref-above",
    )
    below = fact(
        redacted_candidate_id="redacted-candidate-below",
        candidate_forecast_probability=d("0.560000"),
        base_rate_probability=d("0.620000"),
        base_rate_ref="redacted-base-rate-ref-below",
        specialist_calibration_ref="redacted-calibration-ref-below",
        deviation_justification_ref="redacted-deviation-ref-below",
    )
    report = module.build_candidate_decision_base_rate_anchor_score(
        (above, below),
        config=cfg(),
        generated_at=GENERATED_AT,
    )

    rows = {row.redacted_candidate_id: row for row in report.rows}
    above_row = rows["redacted-candidate-above"]
    below_row = rows["redacted-candidate-below"]

    assert above_row.forecast_base_rate_deviation == d("0.060000")
    assert below_row.forecast_base_rate_deviation == d("0.060000")
    assert above_row.base_rate_anchor_score == below_row.base_rate_anchor_score
    assert above_row.reason_codes == below_row.reason_codes

    public_field_names = {
        field.name
        for exported_name in module.__all__
        if isinstance((value := getattr(module, exported_name)), type)
        for field in fields(value)
    }
    assert public_field_names.isdisjoint(
        {
            "candidate_id",
            "team_id",
            "domain_id",
            joined("s", "ide"),
            joined("outcome_", "s", "ide"),
            joined("raw_", "candidate", "_id"),
            joined("raw_", "sou", "rce", "_id"),
            joined("sou", "rce_", "u", "rl"),
            joined("sou", "rce_", "reference"),
        },
    )
    assert {"redacted_candidate_id", "redacted_team_id", "redacted_domain_id"} <= (
        public_field_names
    )


def test_validation_rejects_bad_types_values_duplicates_dates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="base_rate_sample_size must be a Decimal"):
        fact(base_rate_sample_size=30)
    with pytest.raises(ValueError, match="base_rate_recency_score must be a Decimal"):
        fact(base_rate_recency_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="base_rate_dispersion_score"):
        fact(base_rate_dispersion_score=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        fact(paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        module.build_candidate_decision_base_rate_anchor_score(
            (fact(),),
            config=cfg(),
            generated_at=DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(fact(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate candidate/team/domain"):
        build_report(fact(), fact())
    with pytest.raises(ValueError, match="weights must sum"):
        cfg(sample_size_weight=d("0.300000"))
    with pytest.raises(ValueError, match="redacted"):
        fact(base_rate_ref="https://example.invalid/raw")


def test_dataclasses_are_frozen_final_and_self_consistent() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_BASE_RATE_ANCHOR_SCORE_CONFIG_VERSION",
        "BOUNDARY_STATEMENT",
        "CandidateDecisionBaseRateAnchorScoreConfig",
        "CandidateDecisionBaseRateAnchorFact",
        "CandidateDecisionBaseRateAnchorScoreRow",
        "CandidateDecisionBaseRateAnchorScoreReport",
        "build_candidate_decision_base_rate_anchor_score",
        "candidate_decision_base_rate_anchor_score_payload",
        "validate_candidate_decision_base_rate_anchor_score_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    report = build_report(fact())
    for value in (cfg(), fact(), report.rows[0], report):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if isinstance(item_value, Decimal):
                assert type(item_value) is Decimal
            assert type(item_value) not in (float, int)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].score_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="average_base_rate_anchor_score"):
        replace(report, average_base_rate_anchor_score=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeFact(module.CandidateDecisionBaseRateAnchorFact):
            pass

    rebuilt = build_report(fact())
    changed = build_report(fact(base_rate_similarity_score=d("0.790000")))
    assert report.derived_validation_digest == rebuilt.derived_validation_digest
    assert report.derived_validation_digest != changed.derived_validation_digest


def test_report_rejects_noncontiguous_rank_even_with_matching_digest() -> None:
    module = api()
    report = build_report(fact())
    bad_row = replace(report.rows[0], rank=d("2.000000"))
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values["rows"] = (bad_row,)
    values["derived_validation_digest"] = module._derived_validation_digest(
        module._payload_value(values),
    )

    with pytest.raises(ValueError, match="rank"):
        module.CandidateDecisionBaseRateAnchorScoreReport(**values)


def test_public_surface_excludes_raw_event_fields_and_live_operation_surfaces() -> None:
    module = api()
    public_field_names = {
        field.name
        for exported_name in module.__all__
        if isinstance((value := getattr(module, exported_name)), type)
        for field in fields(value)
    }
    forbidden_public_fields = {
        joined("mark", "et_id"),
        joined("mark", "et_", "sl", "ug"),
        joined("normalized_", "mark", "et_", "ques", "tion"),
        joined("ques", "tion"),
        joined("sou", "rce_", "u", "rl"),
        joined("sou", "rce_", "u", "rls"),
        joined("raw_", "mark", "et_id"),
    }
    assert public_field_names.isdisjoint(forbidden_public_fields)

    public_names = set(module.__all__) | {
        name for name in dir(module) if not name.startswith("_")
    }
    for public_name in public_names:
        lower_name = public_name.lower()
        assert joined("mark", "et") not in lower_name
        assert joined("sl", "ug") not in lower_name
        assert joined("ques", "tion") not in lower_name
        assert joined("u", "rl") not in lower_name

    module_text = getattr(inspect, joined("get", "sou", "rce"))(module)
    lowered = module_text.lower()
    for forbidden in (
        joined("requests"),
        joined("h", "ttpx"),
        joined("u", "rllib"),
        joined("web", "socket"),
        joined("socket"),
        joined("sqlite"),
        joined("sql", "alchemy"),
        joined("psycopg"),
        joined("supabase"),
        joined("os.", "environ"),
        joined("get", "env"),
        joined("sub", "process"),
        joined("Path", "("),
        joined("open", "("),
        joined(".w", "rite("),
        joined(".r", "ead("),
        joined("private", "_key"),
        joined("wall", "et"),
    ):
        assert forbidden not in lowered

    tree = ast.parse(
        (
            Path("src")
            / joined("poly", "mark", "et_alpha_lab")
            / "candidate_decision_base_rate_anchor_score.py"
        ).read_text(encoding="utf-8"),
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
