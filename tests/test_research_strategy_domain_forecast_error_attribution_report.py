from __future__ import annotations

import ast
import copy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN, getcontext, setcontext
import hashlib
import importlib
import inspect
import json

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVATION_A = "a" * 64
OBSERVATION_B = "b" * 64
OBSERVATION_C = "c" * 64


class _DecimalSubclass(Decimal):
    pass


def api():
    try:
        return importlib.import_module(
            "polymarket_alpha_lab."
            "research_strategy_domain_forecast_error_attribution_report",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"forecast error attribution report module is missing: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    observation_digest: str = OBSERVATION_A,
    domain_key: str = "macro_rates",
    observed_at: datetime = GENERATED_AT,
    absolute_forecast_error: object = "0.800000",
    source_freshness_score: object = "0.200000",
    authority_disagreement_score: object = "0.600000",
    specialist_divergence_score: object = "0.400000",
    resolution_ambiguity_score: object = "0.200000",
    team_identifier: str = "private-team-alpha",
    source_identifiers: tuple[str, ...] = (
        "private-source-primary",
        "private-source-secondary",
    ),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    report_api = api()

    def decimal_arg(value: object) -> object:
        return d(value) if type(value) is str else value

    return report_api.ResearchStrategyDomainForecastErrorObservation(
        observation_digest=observation_digest,
        domain_key=domain_key,
        observed_at=observed_at,
        absolute_forecast_error=decimal_arg(absolute_forecast_error),
        source_freshness_score=decimal_arg(source_freshness_score),
        authority_disagreement_score=decimal_arg(authority_disagreement_score),
        specialist_divergence_score=decimal_arg(specialist_divergence_score),
        resolution_ambiguity_score=decimal_arg(resolution_ambiguity_score),
        team_identifier=team_identifier,
        source_identifiers=source_identifiers,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations: object):
    return api().build_research_strategy_domain_forecast_error_attribution_report(
        observations,
        generated_at=GENERATED_AT,
    )


def test_attributes_domain_forecast_error_to_diagnostic_factors() -> None:
    report_api = api()
    item = observation()

    report = (
        report_api.build_research_strategy_domain_forecast_error_attribution_report(
            (item,),
            generated_at=GENERATED_AT,
        )
    )

    assert report.status == "moderate"
    assert report.observation_count == d("1.000000")
    assert report.domain_count == d("1.000000")
    assert report.low_count == d("0.000000")
    assert report.moderate_count == d("1.000000")
    assert report.high_count == d("0.000000")
    assert report.average_attribution_score == d("0.400000")
    assert report.max_attribution_score == d("0.400000")

    row = report.rows[0]
    assert row.rank == d("1.000000")
    assert row.domain_key == "macro_rates"
    assert row.observation_count == d("1.000000")
    assert row.average_absolute_forecast_error == d("0.800000")
    assert row.source_staleness_score == d("0.800000")
    assert row.source_freshness_attribution_score == d("0.160000")
    assert row.authority_disagreement_attribution_score == d("0.120000")
    assert row.specialist_divergence_attribution_score == d("0.080000")
    assert row.resolution_ambiguity_attribution_score == d("0.040000")
    assert row.attribution_score == d("0.400000")
    assert row.long_term_learning_score == d("0.500000")
    assert row.human_review_priority_score == d("0.566667")
    assert row.human_review_priority == "high"
    assert row.observation_digests == (OBSERVATION_A,)
    assert row.team_count == d("1.000000")
    assert row.team_digests == (
        _private_digest("team", "private-team-alpha"),
    )
    assert row.source_count == d("2.000000")
    assert row.source_digests == (
        _private_digest("source", "private-source-primary"),
        _private_digest("source", "private-source-secondary"),
    )
    assert row.dominant_attribution_bucket == "source_freshness"
    assert row.status == "moderate"
    assert row.reason_codes == (
        "forecast_error_present",
        "source_freshness_pressure",
        "source_freshness_pressure_high",
        "authority_disagreement_pressure",
        "specialist_divergence_pressure",
        "resolution_ambiguity_pressure",
        "source_freshness_attribution",
        "forecast_error_attribution_moderate",
        "long_term_learning_high",
        "human_review_priority_high",
    )

    source_bucket = report.attribution_buckets[0]
    assert source_bucket.bucket_code == "source_freshness"
    assert source_bucket.domain_count == d("1.000000")
    assert source_bucket.observation_count == d("1.000000")
    assert source_bucket.average_attribution_score == d("0.400000")
    assert report.average_long_term_learning_score == d("0.500000")
    assert report.max_long_term_learning_score == d("0.500000")
    assert report.average_human_review_priority_score == d("0.566667")
    assert report.max_human_review_priority_score == d("0.566667")
    assert report.high_review_priority_count == d("1.000000")
    assert report.medium_review_priority_count == d("0.000000")
    assert report.low_review_priority_count == d("0.000000")


def test_aggregates_domains_and_orders_rows_and_buckets_deterministically() -> None:
    macro_a = observation()
    macro_b = observation(
        observation_digest=OBSERVATION_B,
        absolute_forecast_error="0.400000",
        source_freshness_score="0.600000",
        authority_disagreement_score="0.200000",
        specialist_divergence_score="0.600000",
        resolution_ambiguity_score="0.400000",
    )
    politics = observation(
        observation_digest=OBSERVATION_C,
        domain_key="politics",
        absolute_forecast_error="0.900000",
        source_freshness_score="0.400000",
        authority_disagreement_score="1.000000",
        specialist_divergence_score="0.800000",
        resolution_ambiguity_score="0.600000",
    )

    forward = build_report(macro_a, macro_b, politics)
    reverse = build_report(politics, macro_b, macro_a)

    assert reverse == forward
    assert forward.status == "high"
    assert forward.observation_count == d("3.000000")
    assert forward.domain_count == d("2.000000")
    assert forward.low_count == d("0.000000")
    assert forward.moderate_count == d("1.000000")
    assert forward.high_count == d("1.000000")
    assert forward.average_attribution_score == d("0.472500")
    assert forward.max_attribution_score == d("0.675000")

    politics_row, macro_row = forward.rows
    assert politics_row.rank == d("1.000000")
    assert politics_row.domain_key == "politics"
    assert politics_row.attribution_score == d("0.675000")
    assert politics_row.dominant_attribution_bucket == "authority_disagreement"
    assert politics_row.status == "high"
    assert macro_row.rank == d("2.000000")
    assert macro_row.domain_key == "macro_rates"
    assert macro_row.observation_count == d("2.000000")
    assert macro_row.average_absolute_forecast_error == d("0.600000")
    assert macro_row.source_staleness_score == d("0.600000")
    assert macro_row.attribution_score == d("0.270000")
    assert macro_row.dominant_attribution_bucket == "source_freshness"
    assert macro_row.status == "moderate"

    assert tuple(bucket.bucket_code for bucket in forward.attribution_buckets) == (
        "source_freshness",
        "authority_disagreement",
        "specialist_divergence",
        "resolution_ambiguity",
        "unattributed",
    )
    source_bucket, authority_bucket, *empty_buckets = forward.attribution_buckets
    assert source_bucket.domain_count == d("1.000000")
    assert source_bucket.observation_count == d("2.000000")
    assert source_bucket.average_attribution_score == d("0.270000")
    assert authority_bucket.domain_count == d("1.000000")
    assert authority_bucket.observation_count == d("1.000000")
    assert authority_bucket.average_attribution_score == d("0.675000")
    assert all(bucket.domain_count == d("0.000000") for bucket in empty_buckets)


def test_empty_report_is_canonical_report_only_output() -> None:
    report = build_report()

    assert report.status == "empty"
    assert report.observation_count == d("0.000000")
    assert report.domain_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("empty_forecast_error_observations",)
    assert all(bucket.domain_count == d("0.000000") for bucket in report.attribution_buckets)
    assert all(
        bucket.average_attribution_score == d("0.000000")
        for bucket in report.attribution_buckets
    )
    assert len(report.derived_validation_digest) == 64


def test_public_payload_is_canonical_decimal_only_and_digest_validated() -> None:
    report_api = api()
    first = build_report(
        observation(),
        observation(
            observation_digest=OBSERVATION_B,
            domain_key="politics",
            absolute_forecast_error="0.900000",
            source_freshness_score="0.400000",
            authority_disagreement_score="1.000000",
            specialist_divergence_score="0.800000",
            resolution_ambiguity_score="0.600000",
        ),
    )
    second = build_report(*reversed((
        observation(),
        observation(
            observation_digest=OBSERVATION_B,
            domain_key="politics",
            absolute_forecast_error="0.900000",
            source_freshness_score="0.400000",
            authority_disagreement_score="1.000000",
            specialist_divergence_score="0.800000",
            resolution_ambiguity_score="0.600000",
        ),
    )))

    payload = (
        report_api.research_strategy_domain_forecast_error_attribution_report_payload(
            first,
        )
    )
    second_payload = (
        report_api.research_strategy_domain_forecast_error_attribution_report_payload(
            second,
        )
    )

    assert payload == second_payload
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["observation_count"] == "2.000000"
    assert payload["rows"][0]["attribution_score"] == "0.675000"
    assert payload["attribution_buckets"][0]["domain_count"] == "1.000000"
    assert payload["derived_validation_digest"] == _payload_digest(payload)
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert (
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            payload,
        )
        is True
    )
    json.dumps(payload, sort_keys=True)
    assert all(type(value) is not Decimal for value in _walk(payload))
    assert all(type(value) not in (int, float) for value in _walk(payload))

    forged_digest = copy.deepcopy(payload)
    forged_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_digest,
        )


def test_public_validator_rejects_forged_resigned_derived_values() -> None:
    report_api = api()
    payload = (
        report_api.research_strategy_domain_forecast_error_attribution_report_payload(
            build_report(
                observation(),
                observation(
                    observation_digest=OBSERVATION_B,
                    domain_key="politics",
                    absolute_forecast_error="0.900000",
                    source_freshness_score="0.400000",
                    authority_disagreement_score="1.000000",
                    specialist_divergence_score="0.800000",
                    resolution_ambiguity_score="0.600000",
                ),
            ),
        )
    )

    forged_score = copy.deepcopy(payload)
    forged_score["rows"][0]["attribution_score"] = "0.100000"
    _resign_payload(forged_score)
    with pytest.raises(ValueError, match="attribution_score"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_score,
        )

    forged_bucket = copy.deepcopy(payload)
    forged_bucket["rows"][0]["dominant_attribution_bucket"] = "resolution_ambiguity"
    _resign_payload(forged_bucket)
    with pytest.raises(ValueError, match="dominant_attribution_bucket"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_bucket,
        )

    forged_row_status = copy.deepcopy(payload)
    forged_row_status["rows"][1]["status"] = "high"
    _resign_payload(forged_row_status)
    with pytest.raises(ValueError, match="status"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_row_status,
        )

    forged_reasons = copy.deepcopy(payload)
    forged_reasons["rows"][1]["reason_codes"][-1] = (
        "forecast_error_attribution_high"
    )
    _resign_payload(forged_reasons)
    with pytest.raises(ValueError, match="reason_codes"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_reasons,
        )

    forged_count = copy.deepcopy(payload)
    forged_count["domain_count"] = "3.000000"
    _resign_payload(forged_count)
    with pytest.raises(ValueError, match="domain_count"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_count,
        )

    forged_report_status = copy.deepcopy(payload)
    forged_report_status["status"] = "low"
    _resign_payload(forged_report_status)
    with pytest.raises(ValueError, match="status"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_report_status,
        )

    forged_bucket_count = copy.deepcopy(payload)
    forged_bucket_count["attribution_buckets"][0]["domain_count"] = "2.000000"
    _resign_payload(forged_bucket_count)
    with pytest.raises(ValueError, match="attribution_buckets"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_bucket_count,
        )

    forged_average = copy.deepcopy(payload)
    forged_average["average_attribution_score"] = "0.100000"
    _resign_payload(forged_average)
    with pytest.raises(ValueError, match="average_attribution_score"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_average,
        )

    forged_learning = copy.deepcopy(payload)
    forged_learning["rows"][0]["long_term_learning_score"] = "0.100000"
    _resign_payload(forged_learning)
    with pytest.raises(ValueError, match="long_term_learning_score"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_learning,
        )

    forged_review_priority = copy.deepcopy(payload)
    forged_review_priority["rows"][0]["human_review_priority_score"] = "0.100000"
    _resign_payload(forged_review_priority)
    with pytest.raises(ValueError, match="human_review_priority_score"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_review_priority,
        )

    forged_review_band = copy.deepcopy(payload)
    forged_review_band["rows"][0]["human_review_priority"] = "low"
    _resign_payload(forged_review_band)
    with pytest.raises(ValueError, match="human_review_priority"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_review_band,
        )

    forged_rank = copy.deepcopy(payload)
    forged_rank["rows"][0]["rank"] = "2.000000"
    _resign_payload(forged_rank)
    with pytest.raises(ValueError, match="rank"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_rank,
        )

    forged_observation_count = copy.deepcopy(payload)
    forged_observation_count["rows"][0]["observation_count"] = "2.000000"
    forged_observation_count["observation_count"] = "3.000000"
    _resign_payload(forged_observation_count)
    with pytest.raises(ValueError, match="observation_count"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_observation_count,
        )

    forged_team_count = copy.deepcopy(payload)
    forged_team_count["rows"][0]["team_count"] = "2.000000"
    _resign_payload(forged_team_count)
    with pytest.raises(ValueError, match="team_count"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_team_count,
        )

    forged_source_count = copy.deepcopy(payload)
    forged_source_count["rows"][0]["source_count"] = "3.000000"
    _resign_payload(forged_source_count)
    with pytest.raises(ValueError, match="source_count"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_source_count,
        )

    duplicate_observation_digest = copy.deepcopy(payload)
    duplicate_observation_digest["rows"][1]["observation_digests"] = list(
        duplicate_observation_digest["rows"][0]["observation_digests"],
    )
    _resign_payload(duplicate_observation_digest)
    with pytest.raises(ValueError, match="observation_digests.*unique"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            duplicate_observation_digest,
        )

    forged_report_learning = copy.deepcopy(payload)
    forged_report_learning["average_long_term_learning_score"] = "0.100000"
    _resign_payload(forged_report_learning)
    with pytest.raises(ValueError, match="average_long_term_learning_score"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_report_learning,
        )

    forged_report_review = copy.deepcopy(payload)
    forged_report_review["max_human_review_priority_score"] = "0.100000"
    _resign_payload(forged_report_review)
    with pytest.raises(ValueError, match="max_human_review_priority_score"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_report_review,
        )

    forged_priority_count = copy.deepcopy(payload)
    forged_priority_count["high_review_priority_count"] = "0.000000"
    forged_priority_count["low_review_priority_count"] = "1.000000"
    _resign_payload(forged_priority_count)
    with pytest.raises(ValueError, match="review_priority_count"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            forged_priority_count,
        )


def test_public_validator_rejects_schema_types_and_noncanonical_values() -> None:
    report_api = api()
    payload = (
        report_api.research_strategy_domain_forecast_error_attribution_report_payload(
            build_report(observation()),
        )
    )

    extra_key = copy.deepcopy(payload)
    extra_key["unexpected"] = "value"
    _resign_payload(extra_key)
    with pytest.raises(ValueError, match="payload keys"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            extra_key,
        )

    integer_count = copy.deepcopy(payload)
    integer_count["observation_count"] = 1
    _resign_payload(integer_count)
    with pytest.raises(ValueError, match="observation_count"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            integer_count,
        )

    noncanonical_count = copy.deepcopy(payload)
    noncanonical_count["observation_count"] = "1"
    _resign_payload(noncanonical_count)
    with pytest.raises(ValueError, match="observation_count"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            noncanonical_count,
        )

    float_score = copy.deepcopy(payload)
    float_score["rows"][0]["attribution_score"] = 0.4
    _resign_payload(float_score)
    with pytest.raises(ValueError, match="attribution_score"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            float_score,
        )

    signed_zero = copy.deepcopy(payload)
    signed_zero["rows"][0]["resolution_ambiguity_attribution_score"] = "-0.000000"
    _resign_payload(signed_zero)
    with pytest.raises(
        ValueError,
        match="resolution_ambiguity_attribution_score",
    ):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            signed_zero,
        )

    false_flag = copy.deepcopy(payload)
    false_flag["paper_only"] = False
    _resign_payload(false_flag)
    with pytest.raises(ValueError, match="paper_only"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            false_flag,
        )

    missing_row_key = copy.deepcopy(payload)
    del missing_row_key["rows"][0]["long_term_learning_score"]
    _resign_payload(missing_row_key)
    with pytest.raises(ValueError, match="row keys"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            missing_row_key,
        )

    extra_bucket_key = copy.deepcopy(payload)
    extra_bucket_key["attribution_buckets"][0]["unexpected"] = "value"
    _resign_payload(extra_bucket_key)
    with pytest.raises(ValueError, match="bucket keys"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            extra_bucket_key,
        )


def test_public_validator_rejects_noncanonical_payload_insertion_order() -> None:
    report_api = api()
    payload = (
        report_api.research_strategy_domain_forecast_error_attribution_report_payload(
            build_report(observation()),
        )
    )

    reordered_report = {
        "status": payload["status"],
        **{key: value for key, value in payload.items() if key != "status"},
    }
    _resign_payload(reordered_report)
    with pytest.raises(ValueError, match="payload keys"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            reordered_report,
        )

    reordered_row = copy.deepcopy(payload)
    row = reordered_row["rows"][0]
    reordered_row["rows"][0] = {
        "domain_key": row["domain_key"],
        **{key: value for key, value in row.items() if key != "domain_key"},
    }
    _resign_payload(reordered_row)
    with pytest.raises(ValueError, match="row keys"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            reordered_row,
        )

    reordered_bucket = copy.deepcopy(payload)
    bucket = reordered_bucket["attribution_buckets"][0]
    reordered_bucket["attribution_buckets"][0] = {
        "average_attribution_score": bucket["average_attribution_score"],
        **{
            key: value
            for key, value in bucket.items()
            if key != "average_attribution_score"
        },
    }
    _resign_payload(reordered_bucket)
    with pytest.raises(ValueError, match="bucket keys"):
        report_api.validate_research_strategy_domain_forecast_error_attribution_report_payload(
            reordered_bucket,
        )


def test_uses_fixed_decimal_context_and_preserves_global_context() -> None:
    original_context = getcontext().copy()
    try:
        observations = tuple(
            observation(
                observation_digest=f"{index:064x}",
                domain_key=f"domain_{index:02d}",
            )
            for index in range(1, 12)
        )
        baseline = build_report(*observations)
        getcontext().prec = 1
        getcontext().rounding = ROUND_DOWN

        constrained = build_report(*reversed(observations))

        assert constrained == baseline
        assert getcontext().prec == 1
        assert getcontext().rounding == ROUND_DOWN
    finally:
        setcontext(original_context)


def test_fixed_decimal_context_controls_descending_sort_keys() -> None:
    lower_priority = observation(
        observation_digest=OBSERVATION_A,
        domain_key="alpha_domain",
        absolute_forecast_error="0.800000",
    )
    higher_priority = observation(
        observation_digest=OBSERVATION_B,
        domain_key="zeta_domain",
        absolute_forecast_error="0.810000",
    )
    baseline = build_report(lower_priority, higher_priority)
    assert tuple(row.domain_key for row in baseline.rows) == (
        "zeta_domain",
        "alpha_domain",
    )

    original_context = getcontext().copy()
    try:
        getcontext().prec = 1
        getcontext().rounding = ROUND_DOWN

        constrained = build_report(higher_priority, lower_priority)

        assert constrained == baseline
        assert getcontext().prec == 1
        assert getcontext().rounding == ROUND_DOWN
    finally:
        setcontext(original_context)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("absolute_forecast_error", "1.0000004"),
        ("absolute_forecast_error", "-0.0000004"),
        ("source_freshness_score", "1.0000004"),
        ("authority_disagreement_score", "-0.0000004"),
    ),
)
def test_rejects_raw_ratio_bounds_before_quantization(
    field_name: str,
    value: str,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        observation(**{field_name: value})


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("authority_disagreement_score", Decimal("NaN")),
        ("specialist_divergence_score", Decimal("Infinity")),
        ("resolution_ambiguity_score", Decimal("-Infinity")),
    ),
)
def test_rejects_non_finite_decimals(
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        observation(**{field_name: value})


@pytest.mark.parametrize(
    "signed_zero",
    (
        Decimal("-0"),
        Decimal("-0.000000"),
        Decimal("-0E+20"),
    ),
)
def test_signed_zero_is_canonicalized_at_all_decimal_boundaries(
    signed_zero: Decimal,
) -> None:
    report_api = api()
    item = observation(
        absolute_forecast_error=signed_zero,
        source_freshness_score=signed_zero,
        authority_disagreement_score=signed_zero,
        specialist_divergence_score=signed_zero,
        resolution_ambiguity_score=signed_zero,
    )
    bucket = report_api.ResearchStrategyDomainForecastErrorAttributionBucket(
        bucket_code="unattributed",
        domain_count=signed_zero,
        observation_count=signed_zero,
        average_attribution_score=signed_zero,
    )

    for value in (
        item.absolute_forecast_error,
        item.source_freshness_score,
        item.authority_disagreement_score,
        item.specialist_divergence_score,
        item.resolution_ambiguity_score,
        bucket.domain_count,
        bucket.observation_count,
        bucket.average_attribution_score,
    ):
        assert value == d("0.000000")
        assert value.is_signed() is False

    payload = (
        report_api.research_strategy_domain_forecast_error_attribution_report_payload(
            build_report(item),
        )
    )
    assert "-0.000000" not in json.dumps(payload, sort_keys=True)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_build_revalidates_tampered_config_hard_flags(flag_name: str) -> None:
    report_api = api()
    config = report_api.ResearchStrategyDomainForecastErrorAttributionConfig()
    object.__setattr__(config, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        report_api.build_research_strategy_domain_forecast_error_attribution_report(
            (),
            generated_at=GENERATED_AT,
            config=config,
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_build_revalidates_tampered_observation_hard_flags(flag_name: str) -> None:
    item = observation()
    object.__setattr__(item, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        build_report(item)


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    (
        ("domain_key", "live_trading"),
        ("observation_digests", ("private-observation-secret",)),
        ("team_digests", ("private-team-secret",)),
        (
            "source_digests",
            (
                "https://private.example/?token=secret",
                "private-source-secret",
            ),
        ),
    ),
)
def test_payload_property_revalidates_nested_public_values_before_exposure(
    field_name: str,
    unsafe_value: object,
) -> None:
    report_api = api()
    report = build_report(observation())
    object.__setattr__(report.rows[0], field_name, unsafe_value)
    _resign_report_object(report_api, report)

    with pytest.raises(ValueError, match=field_name):
        report.payload


def test_payload_property_rejects_tampered_non_utc_as_of() -> None:
    report_api = api()
    report = build_report(observation())
    non_utc_as_of = GENERATED_AT.astimezone(timezone(timedelta(hours=5, minutes=30)))
    object.__setattr__(report, "generated_at", non_utc_as_of)
    _resign_report_object(report_api, report)

    with pytest.raises(ValueError, match="generated_at"):
        report.payload


def test_utc_as_of_boundary_is_inclusive_and_future_is_rejected() -> None:
    report_api = api()
    eastern = timezone(timedelta(hours=-4))
    equivalent_as_of = GENERATED_AT.astimezone(eastern)
    item = observation(observed_at=equivalent_as_of)

    report = (
        report_api.build_research_strategy_domain_forecast_error_attribution_report(
            (item,),
            generated_at=equivalent_as_of,
        )
    )

    assert item.observed_at == GENERATED_AT
    assert item.observed_at.tzinfo is UTC
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC

    with pytest.raises(ValueError, match="after generated_at"):
        report_api.build_research_strategy_domain_forecast_error_attribution_report(
            (observation(observed_at=GENERATED_AT + timedelta(microseconds=1)),),
            generated_at=equivalent_as_of,
        )


def test_private_team_and_source_identifiers_are_only_exposed_as_sha256() -> None:
    report_api = api()
    private_team = "private-team-super-secret"
    private_sources = (
        "https://private.example/source?token=secret",
        "private-database-source-alpha",
    )
    report = build_report(
        observation(
            team_identifier=private_team,
            source_identifiers=private_sources,
        ),
    )
    payload = (
        report_api.research_strategy_domain_forecast_error_attribution_report_payload(
            report,
        )
    )
    rendered = json.dumps(payload, sort_keys=True)
    row = payload["rows"][0]

    assert private_team not in rendered
    assert all(source not in rendered for source in private_sources)
    assert row["team_digests"] == [_private_digest("team", private_team)]
    assert row["source_digests"] == sorted(
        _private_digest("source", source) for source in private_sources
    )
    assert all(
        value.startswith("sha256:") and len(value) == len("sha256:") + 64
        for value in (*row["team_digests"], *row["source_digests"])
    )


def test_rows_use_stable_human_review_priority_tie_breaks() -> None:
    alpha = observation(
        observation_digest=OBSERVATION_A,
        domain_key="alpha_domain",
        team_identifier="private-team-zeta",
        source_identifiers=("private-source-zeta",),
    )
    beta = observation(
        observation_digest=OBSERVATION_B,
        domain_key="beta_domain",
        team_identifier="private-team-alpha",
        source_identifiers=("private-source-alpha",),
    )

    forward = build_report(alpha, beta)
    reverse = build_report(beta, alpha)

    assert forward == reverse
    assert tuple(row.domain_key for row in forward.rows) == (
        "alpha_domain",
        "beta_domain",
    )
    assert tuple(row.rank for row in forward.rows) == (
        d("1.000000"),
        d("2.000000"),
    )


def test_public_payload_uses_exact_extended_canonical_schema() -> None:
    payload = api().research_strategy_domain_forecast_error_attribution_report_payload(
        build_report(observation()),
    )

    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "status",
        "observation_count",
        "domain_count",
        "low_count",
        "moderate_count",
        "high_count",
        "high_review_priority_count",
        "medium_review_priority_count",
        "low_review_priority_count",
        "average_attribution_score",
        "max_attribution_score",
        "average_long_term_learning_score",
        "max_long_term_learning_score",
        "average_human_review_priority_score",
        "max_human_review_priority_score",
        "rows",
        "attribution_buckets",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["rows"][0]) == (
        "rank",
        "domain_key",
        "observation_count",
        "observation_digests",
        "team_count",
        "team_digests",
        "source_count",
        "source_digests",
        "average_absolute_forecast_error",
        "source_staleness_score",
        "authority_disagreement_score",
        "specialist_divergence_score",
        "resolution_ambiguity_score",
        "source_freshness_attribution_score",
        "authority_disagreement_attribution_score",
        "specialist_divergence_attribution_score",
        "resolution_ambiguity_attribution_score",
        "attribution_score",
        "long_term_learning_score",
        "human_review_priority_score",
        "human_review_priority",
        "dominant_attribution_bucket",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["attribution_buckets"][0]) == (
        "bucket_code",
        "domain_count",
        "observation_count",
        "average_attribution_score",
        "paper_only",
        "report_only",
        "readonly",
    )


def test_dataclasses_are_frozen_final_decimal_only_and_hard_flagged() -> None:
    report_api = api()
    item = observation()
    report = build_report(item)

    expected_fields = {
        report_api.ResearchStrategyDomainForecastErrorAttributionConfig: (
            "config_version",
            "source_freshness_weight",
            "authority_disagreement_weight",
            "specialist_divergence_weight",
            "resolution_ambiguity_weight",
            "moderate_attribution_threshold",
            "high_attribution_threshold",
            "high_factor_pressure_threshold",
            "paper_only",
            "report_only",
            "readonly",
        ),
        report_api.ResearchStrategyDomainForecastErrorObservation: (
            "observation_digest",
            "domain_key",
            "observed_at",
            "absolute_forecast_error",
            "source_freshness_score",
            "authority_disagreement_score",
            "specialist_divergence_score",
            "resolution_ambiguity_score",
            "team_identifier",
            "source_identifiers",
            "paper_only",
            "report_only",
            "readonly",
        ),
        report_api.ResearchStrategyDomainForecastErrorAttributionRow: (
            "rank",
            "domain_key",
            "observation_count",
            "observation_digests",
            "team_count",
            "team_digests",
            "source_count",
            "source_digests",
            "average_absolute_forecast_error",
            "source_staleness_score",
            "authority_disagreement_score",
            "specialist_divergence_score",
            "resolution_ambiguity_score",
            "source_freshness_attribution_score",
            "authority_disagreement_attribution_score",
            "specialist_divergence_attribution_score",
            "resolution_ambiguity_attribution_score",
            "attribution_score",
            "long_term_learning_score",
            "human_review_priority_score",
            "human_review_priority",
            "dominant_attribution_bucket",
            "status",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        ),
        report_api.ResearchStrategyDomainForecastErrorAttributionBucket: (
            "bucket_code",
            "domain_count",
            "observation_count",
            "average_attribution_score",
            "paper_only",
            "report_only",
            "readonly",
        ),
        report_api.ResearchStrategyDomainForecastErrorAttributionReport: (
            "generated_at",
            "config_version",
            "status",
            "observation_count",
            "domain_count",
            "low_count",
            "moderate_count",
            "high_count",
            "high_review_priority_count",
            "medium_review_priority_count",
            "low_review_priority_count",
            "average_attribution_score",
            "max_attribution_score",
            "average_long_term_learning_score",
            "max_long_term_learning_score",
            "average_human_review_priority_score",
            "max_human_review_priority_score",
            "rows",
            "attribution_buckets",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    }

    public_values = (
        report_api.ResearchStrategyDomainForecastErrorAttributionConfig(),
        item,
        report.rows[0],
        report.attribution_buckets[0],
        report,
    )
    for value in public_values:
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        _assert_public_numbers_are_decimal(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    for dataclass_type, field_names in expected_fields.items():
        assert dataclass_type.__dataclass_params__.frozen is True
        assert tuple(field.name for field in fields(dataclass_type)) == field_names
        with pytest.raises(TypeError, match="subclassing"):
            type("UnsafeSubclass", (dataclass_type,), {})

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="absolute_forecast_error"):
        observation(absolute_forecast_error=1)
    with pytest.raises(ValueError, match="source_freshness_score"):
        observation(source_freshness_score=0.5)
    with pytest.raises(ValueError, match="authority_disagreement_score"):
        observation(
            authority_disagreement_score=_DecimalSubclass("0.500000"),
        )
    with pytest.raises(ValueError, match="observation_digest"):
        observation(observation_digest="not-a-digest")
    with pytest.raises(ValueError, match="unsafe"):
        observation(domain_key="live_trading")

    duplicate = observation()
    with pytest.raises(ValueError, match="unique"):
        build_report(duplicate, duplicate)
    with pytest.raises(ValueError, match="after generated_at"):
        build_report(
            observation(observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 9, 12, 0))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_payload_property_rejects_object_setattr_nested_tampering() -> None:
    report_api = api()
    report = build_report(observation())

    object.__setattr__(report, "readonly", False)
    _resign_report_object(report_api, report)
    with pytest.raises(ValueError, match="readonly"):
        report.payload

    report = build_report(observation())
    object.__setattr__(report.rows[0], "paper_only", False)
    _resign_report_object(report_api, report)
    with pytest.raises(ValueError, match="paper_only"):
        report.payload

    report = build_report(observation())
    object.__setattr__(report, "rows", (object(),))
    with pytest.raises(ValueError, match="rows"):
        report.payload


def test_module_exposes_no_execution_or_investment_action_surface() -> None:
    report_api = api()
    forbidden_name_parts = (
        "file",
        "wallet",
        "order",
        "trade",
        "execution",
        "recommendation",
        "sizing",
        "position",
        "network",
        "database",
        "persist",
        "sqlite",
        "buy",
        "sell",
    )
    for public_name in report_api.__all__:
        lowered = public_name.lower()
        assert not any(part in lowered for part in forbidden_name_parts)

    for dataclass_type in (
        report_api.ResearchStrategyDomainForecastErrorAttributionConfig,
        report_api.ResearchStrategyDomainForecastErrorObservation,
        report_api.ResearchStrategyDomainForecastErrorAttributionRow,
        report_api.ResearchStrategyDomainForecastErrorAttributionBucket,
        report_api.ResearchStrategyDomainForecastErrorAttributionReport,
    ):
        for field in fields(dataclass_type):
            lowered = field.name.lower()
            assert not any(part in lowered for part in forbidden_name_parts)

    source = inspect.getsource(report_api)
    _assert_ast_has_no_io(source)
    syntax_tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(syntax_tree)
    )
    for forbidden_import in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(report_api, forbidden_import)


def _payload_digest(payload: dict[str, object]) -> str:
    digest_values = copy.deepcopy(payload)
    digest_values.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _resign_payload(payload: dict[str, object]) -> None:
    payload["derived_validation_digest"] = _payload_digest(payload)


def _resign_report_object(report_api: object, report: object) -> None:
    object.__setattr__(
        report,
        "derived_validation_digest",
        report_api._report_digest_from_values(  # type: ignore[attr-defined]
            report_api._report_values_without_digest(report),  # type: ignore[attr-defined]
        ),
    )


def _private_digest(kind: str, value: str) -> str:
    digest = hashlib.sha256((kind + "\0" + value).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _walk(value: object):
    if type(value) is dict:
        for key, item in value.items():
            yield key
            yield from _walk(item)
    elif type(value) in (list, tuple):
        for item in value:
            yield from _walk(item)
    else:
        yield value


def _assert_ast_has_no_io(source: str) -> None:
    syntax_tree = ast.parse(source)
    aliases: dict[str, str] = {}
    forbidden_roots = {
        "aiohttp",
        "ccxt",
        "http",
        "httpcore",
        "httpx",
        "importlib",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "shelve",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "tempfile",
        "urllib",
        "urllib3",
        "web3",
    }
    forbidden_calls = {
        "__import__",
        "builtins.open",
        "compile",
        "eval",
        "exec",
        "open",
    }
    forbidden_method_names = {
        "connect",
        "open",
        "read_bytes",
        "read_text",
        "write_bytes",
        "write_text",
    }

    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split(".", maxsplit=1)[0]
                aliases[local_name] = alias.name
                assert alias.name.split(".", maxsplit=1)[0] not in forbidden_roots
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            assert module_name.split(".", maxsplit=1)[0] not in forbidden_roots
            for alias in node.names:
                local_name = alias.asname or alias.name
                aliases[local_name] = f"{module_name}.{alias.name}".strip(".")

    for node in ast.walk(syntax_tree):
        if not isinstance(node, ast.Call):
            continue
        call_name = _ast_call_name(node.func, aliases)
        call_root = call_name.split(".", maxsplit=1)[0]
        assert call_root not in forbidden_roots
        assert call_name not in forbidden_calls
        assert call_name.rsplit(".", maxsplit=1)[-1] not in forbidden_method_names


def _ast_call_name(node: ast.AST, aliases: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        owner = _ast_call_name(node.value, aliases)
        return f"{owner}.{node.attr}" if owner else node.attr
    if isinstance(node, ast.Call):
        return _ast_call_name(node.func, aliases)
    return ""


def _assert_public_numbers_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal: {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_public_numbers_are_decimal(getattr(value, field.name))
        return
    if type(value) in (list, tuple):
        for item in value:
            _assert_public_numbers_are_decimal(item)
