from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, ROUND_UP, Decimal, localcontext

import pytest


GENERATED_AT = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    try:
        return importlib.import_module(
            "polymarket_alpha_lab."
            "research_team_specialist_forecast_attribution_report",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"specialist forecast attribution report module is missing: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    observation_digest: str = "a" * 64,
    specialist_identifier: str = "private-specialist-alpha@example.com",
    source_identifiers: tuple[str, ...] = (
        "https://private.example/source?token=hidden",
        "source-secret-alpha",
    ),
    observed_at: datetime = GENERATED_AT,
    forecast_probability: object = "0.800000",
    resolved_probability: object = "0.700000",
    evidence_quality_score: object = "0.800000",
    timeliness_score: object = "0.600000",
    disagreement_handling_score: object = "0.700000",
    outcome_learning_score: object = "0.900000",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    report_api = api()

    def decimal_arg(value: object) -> object:
        return d(value) if type(value) is str else value

    return report_api.ResearchTeamSpecialistForecastAttributionObservation(
        observation_digest=observation_digest,
        specialist_identifier=specialist_identifier,
        source_identifiers=source_identifiers,
        observed_at=observed_at,
        forecast_probability=decimal_arg(forecast_probability),
        resolved_probability=decimal_arg(resolved_probability),
        evidence_quality_score=decimal_arg(evidence_quality_score),
        timeliness_score=decimal_arg(timeliness_score),
        disagreement_handling_score=decimal_arg(
            disagreement_handling_score,
        ),
        outcome_learning_score=decimal_arg(outcome_learning_score),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations: object):
    return api().build_research_team_specialist_forecast_attribution_report(
        observations,
        generated_at=GENERATED_AT,
    )


def sample_observations() -> tuple[object, ...]:
    return (
        observation(),
        observation(
            observation_digest="b" * 64,
            source_identifiers=("source-secret-alpha", "token=private-beta"),
            forecast_probability="0.600000",
            resolved_probability="0.300000",
            evidence_quality_score="0.600000",
            timeliness_score="0.800000",
            disagreement_handling_score="0.500000",
            outcome_learning_score="0.700000",
        ),
        observation(
            observation_digest="c" * 64,
            specialist_identifier="private-specialist-beta",
            source_identifiers=("source-secret-beta",),
            forecast_probability="0.900000",
            resolved_probability="0.100000",
            evidence_quality_score="0.800000",
            timeliness_score="0.200000",
            disagreement_handling_score="0.200000",
            outcome_learning_score="0.100000",
        ),
        observation(
            observation_digest="d" * 64,
            specialist_identifier="private-specialist-gamma",
            source_identifiers=("source-secret-gamma",),
            forecast_probability="0.800000",
            resolved_probability="0.300000",
            evidence_quality_score="0.400000",
            timeliness_score="0.500000",
            disagreement_handling_score="0.500000",
            outcome_learning_score="1.000000",
        ),
    )


def score_observation(
    *,
    calibration_score: object = "0.500000",
    evidence_quality_score: object = "0.500000",
    timeliness_score: object = "0.500000",
    disagreement_handling_score: object = "0.500000",
    outcome_learning_score: object = "0.500000",
):
    calibration = (
        d(calibration_score)
        if type(calibration_score) is str
        else calibration_score
    )
    assert type(calibration) is Decimal
    return observation(
        forecast_probability=d("1.000000") - calibration,
        resolved_probability="0.000000",
        evidence_quality_score=evidence_quality_score,
        timeliness_score=timeliness_score,
        disagreement_handling_score=disagreement_handling_score,
        outcome_learning_score=outcome_learning_score,
    )


def test_builds_ranked_five_factor_attribution_without_identifier_leakage() -> None:
    report_api = api()
    alpha_a, alpha_b, beta, gamma = sample_observations()

    forward = build_report(alpha_a, alpha_b, beta, gamma)
    reverse = build_report(gamma, beta, alpha_b, alpha_a)

    assert reverse == forward
    assert report_api.SPECIALIST_FORECAST_ATTRIBUTION_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert forward.status == "block"
    assert forward.observation_count == d("4.000000")
    assert forward.specialist_count == d("3.000000")
    assert forward.pass_count == d("1.000000")
    assert forward.watch_count == d("1.000000")
    assert forward.block_count == d("1.000000")
    assert forward.average_attribution_score == d("0.538333")
    assert forward.max_attribution_score == d("0.735000")
    assert forward.average_calibration_contribution_score == d("0.150000")
    assert forward.average_evidence_quality_contribution_score == d("0.126667")
    assert forward.average_timeliness_contribution_score == d("0.070000")
    assert forward.average_disagreement_handling_contribution_score == d(
        "0.065000",
    )
    assert forward.average_outcome_learning_contribution_score == d("0.126667")

    passed, watched, blocked = forward.rows
    assert tuple(row.rank for row in forward.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in forward.rows) == ("pass", "watch", "block")
    assert passed.observation_count == d("2.000000")
    assert passed.source_count == d("3.000000")
    assert passed.average_absolute_forecast_error == d("0.200000")
    assert passed.calibration_score == d("0.800000")
    assert passed.evidence_quality_score == d("0.700000")
    assert passed.timeliness_score == d("0.700000")
    assert passed.disagreement_handling_score == d("0.600000")
    assert passed.outcome_learning_score == d("0.800000")
    assert passed.calibration_contribution_score == d("0.240000")
    assert passed.evidence_quality_contribution_score == d("0.140000")
    assert passed.timeliness_contribution_score == d("0.105000")
    assert passed.disagreement_handling_contribution_score == d("0.090000")
    assert passed.outcome_learning_contribution_score == d("0.160000")
    assert passed.attribution_score == d("0.735000")
    assert passed.dominant_contribution == "calibration"
    assert passed.reason_codes == (
        "specialist_forecast_attribution_pass",
        "calibration_support",
        "evidence_quality_support",
        "timeliness_support",
        "outcome_learning_support",
        "calibration_dominant",
    )
    assert watched.attribution_score == d("0.580000")
    assert watched.dominant_contribution == "outcome_learning"
    assert blocked.attribution_score == d("0.300000")
    assert blocked.dominant_contribution == "evidence_quality"

    assert tuple(bucket.contribution_code for bucket in forward.contribution_buckets) == (
        "calibration",
        "evidence_quality",
        "timeliness",
        "disagreement_handling",
        "outcome_learning",
    )
    assert tuple(bucket.specialist_count for bucket in forward.contribution_buckets) == (
        d("1.000000"),
        d("1.000000"),
        d("0.000000"),
        d("0.000000"),
        d("1.000000"),
    )

    payload = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            forward,
        )
    )
    rendered = json.dumps(payload, sort_keys=True)
    assert payload["observation_count"] == "4.000000"
    assert payload["rows"][0]["attribution_score"] == "0.735000"
    assert payload["rows"][0]["specialist_digest"].startswith("sha256:")
    assert all(
        source_digest.startswith("sha256:")
        for row in payload["rows"]
        for source_digest in row["source_digests"]
    )
    for private_value in (
        "private-specialist-alpha@example.com",
        "private-specialist-beta",
        "private-specialist-gamma",
        "private.example",
        "source-secret-alpha",
        "source-secret-beta",
        "source-secret-gamma",
        "token=private-beta",
        "token=hidden",
    ):
        assert private_value not in rendered


def test_private_identifiers_use_domain_separated_sha256_references() -> None:
    private_identifier = "shared-private-identifier"
    report = build_report(
        observation(
            specialist_identifier=private_identifier,
            source_identifiers=(private_identifier,),
        ),
    )
    row = report.rows[0]

    expected_specialist_digest = hashlib.sha256(
        f"specialist\0{private_identifier}".encode("utf-8"),
    ).hexdigest()
    expected_source_digest = hashlib.sha256(
        f"source\0{private_identifier}".encode("utf-8"),
    ).hexdigest()
    assert row.specialist_digest == f"sha256:{expected_specialist_digest}"
    assert row.source_digests == (f"sha256:{expected_source_digest}",)
    assert row.specialist_digest != row.source_digests[0]
    assert private_identifier not in json.dumps(report.payload, sort_keys=True)


def test_tied_rows_use_digest_tiebreaker_and_reject_resigned_reordering() -> None:
    report_api = api()
    first = observation(
        observation_digest="e" * 64,
        specialist_identifier="private-specialist-tie-zeta",
        source_identifiers=("private-source-tie-zeta",),
    )
    second = observation(
        observation_digest="f" * 64,
        specialist_identifier="private-specialist-tie-alpha",
        source_identifiers=("private-source-tie-alpha",),
    )

    forward = build_report(first, second)
    reverse = build_report(second, first)
    assert forward == reverse
    assert forward.rows[0].attribution_score == forward.rows[1].attribution_score
    assert tuple(row.specialist_digest for row in forward.rows) == tuple(
        sorted(row.specialist_digest for row in forward.rows),
    )

    forged = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            forward,
        )
    )
    forged["rows"].reverse()
    for index, row in enumerate(forged["rows"], start=1):
        row["rank"] = f"{index}.000000"
    _resign_payload(forged)
    with pytest.raises(ValueError, match="deterministic sequence"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged,
        )


@pytest.mark.parametrize(
    (
        "calibration_score",
        "evidence_quality_score",
        "expected_score",
        "expected_status",
    ),
    (
        ("0.700000", "0.699995", "0.699999", "watch"),
        ("0.700000", "0.700000", "0.700000", "pass"),
        ("0.700000", "0.700005", "0.700001", "pass"),
        ("0.400000", "0.399995", "0.399999", "block"),
        ("0.400000", "0.400000", "0.400000", "watch"),
        ("0.400000", "0.400005", "0.400001", "watch"),
    ),
)
def test_attribution_status_boundaries_use_exact_quantized_score(
    calibration_score: str,
    evidence_quality_score: str,
    expected_score: str,
    expected_status: str,
) -> None:
    item = score_observation(
        calibration_score=calibration_score,
        evidence_quality_score=evidence_quality_score,
        timeliness_score=calibration_score,
        disagreement_handling_score=calibration_score,
        outcome_learning_score=calibration_score,
    )

    report = build_report(item)
    row = report.rows[0]

    assert row.attribution_score == d(expected_score)
    assert row.status == expected_status
    assert report.status == expected_status


@pytest.mark.parametrize(
    "component",
    (
        "calibration",
        "evidence_quality",
        "timeliness",
        "disagreement_handling",
        "outcome_learning",
    ),
)
@pytest.mark.parametrize(
    ("score", "has_support", "has_drag"),
    (
        ("0.699999", False, False),
        ("0.700000", True, False),
        ("0.700001", True, False),
        ("0.399999", False, True),
        ("0.400000", False, False),
        ("0.400001", False, False),
    ),
)
def test_each_component_support_and_drag_boundary_uses_one_quantum(
    component: str,
    score: str,
    has_support: bool,
    has_drag: bool,
) -> None:
    values: dict[str, object] = {
        "calibration_score": "0.500000",
        "evidence_quality_score": "0.500000",
        "timeliness_score": "0.500000",
        "disagreement_handling_score": "0.500000",
        "outcome_learning_score": "0.500000",
    }
    values[f"{component}_score"] = score

    row = build_report(score_observation(**values)).rows[0]

    assert (f"{component}_support" in row.reason_codes) is has_support
    assert (f"{component}_drag" in row.reason_codes) is has_drag


def test_seventh_decimal_place_uses_round_half_even() -> None:
    rounds_to_even = score_observation(
        evidence_quality_score=d("0.7000005"),
    )
    rounds_from_odd = score_observation(
        evidence_quality_score=d("0.7000015"),
    )

    assert rounds_to_even.evidence_quality_score == d("0.700000")
    assert rounds_from_odd.evidence_quality_score == d("0.700002")


def test_quantized_components_aggregate_before_status_boundary() -> None:
    row = build_report(
        score_observation(
            calibration_score="0.699999",
            evidence_quality_score="0.699999",
            timeliness_score="0.699999",
            disagreement_handling_score="0.699999",
            outcome_learning_score="0.699999",
        ),
    ).rows[0]

    assert (
        row.calibration_contribution_score,
        row.evidence_quality_contribution_score,
        row.timeliness_contribution_score,
        row.disagreement_handling_contribution_score,
        row.outcome_learning_contribution_score,
    ) == (
        d("0.210000"),
        d("0.140000"),
        d("0.105000"),
        d("0.105000"),
        d("0.140000"),
    )
    assert row.attribution_score == d("0.700000")
    assert row.status == "pass"


def test_all_tied_contributions_use_canonical_calibration_priority() -> None:
    row = build_report(
        score_observation(
            calibration_score="0.500000",
            evidence_quality_score="0.750000",
            timeliness_score="1.000000",
            disagreement_handling_score="1.000000",
            outcome_learning_score="0.750000",
        ),
    ).rows[0]

    assert (
        row.calibration_contribution_score,
        row.evidence_quality_contribution_score,
        row.timeliness_contribution_score,
        row.disagreement_handling_contribution_score,
        row.outcome_learning_contribution_score,
    ) == (d("0.150000"),) * 5
    assert row.dominant_contribution == "calibration"
    assert row.reason_codes[-1] == "calibration_dominant"


def test_empty_report_is_blocked_canonical_and_report_only() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.observation_count == d("0.000000")
    assert report.specialist_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_attribution_score == d("0.000000")
    assert report.max_attribution_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "specialist_forecast_attribution_report_block",
        "empty_specialist_forecasts",
    )
    assert tuple(
        bucket.contribution_code for bucket in report.contribution_buckets
    ) == (
        "calibration",
        "evidence_quality",
        "timeliness",
        "disagreement_handling",
        "outcome_learning",
    )
    assert all(
        bucket.specialist_count == d("0.000000")
        and bucket.observation_count == d("0.000000")
        and bucket.average_attribution_score == d("0.000000")
        for bucket in report.contribution_buckets
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64


def test_empty_report_payload_routes_through_validator_and_rejects_resigned_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report_api = api()
    report = build_report()
    validation_calls: list[dict[str, object]] = []
    original_validator = (
        report_api.validate_research_team_specialist_forecast_attribution_report_payload
    )

    def validating(payload: dict[str, object]) -> bool:
        validation_calls.append(payload)
        return original_validator(payload)

    monkeypatch.setattr(
        report_api,
        "validate_research_team_specialist_forecast_attribution_report_payload",
        validating,
    )
    payload = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            report,
        )
    )

    assert validation_calls == [payload]
    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "status",
        "observation_count",
        "specialist_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_attribution_score",
        "max_attribution_score",
        "average_calibration_contribution_score",
        "average_evidence_quality_contribution_score",
        "average_timeliness_contribution_score",
        "average_disagreement_handling_contribution_score",
        "average_outcome_learning_contribution_score",
        "rows",
        "contribution_buckets",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert payload["rows"] == []
    assert payload["derived_validation_digest"] == _payload_digest(payload)

    reordered_schema = {key: payload[key] for key in reversed(tuple(payload))}
    _resign_payload(reordered_schema)
    with pytest.raises(ValueError, match="payload keys"):
        original_validator(reordered_schema)

    reordered_buckets = copy.deepcopy(payload)
    reordered_buckets["contribution_buckets"].reverse()
    _resign_payload(reordered_buckets)
    with pytest.raises(ValueError, match="contribution_buckets"):
        original_validator(reordered_buckets)

    forged_status = copy.deepcopy(payload)
    forged_status["status"] = "pass"
    _resign_payload(forged_status)
    with pytest.raises(ValueError, match="status"):
        original_validator(forged_status)


def test_payload_is_exact_canonical_decimal_only_and_sha256_validated() -> None:
    report_api = api()
    report = build_report(*sample_observations())
    payload = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            report,
        )
    )

    assert payload["generated_at"] == "2026-07-10T12:00:00+00:00"
    assert payload["observation_count"] == "4.000000"
    assert payload["rows"][0]["rank"] == "1.000000"
    assert payload["contribution_buckets"][0]["specialist_count"] == "1.000000"
    assert payload["derived_validation_digest"] == _payload_digest(payload)
    assert (
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            payload,
        )
        is True
    )
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert all(type(value) is not Decimal for value in _walk(payload))
    assert all(type(value) not in (int, float) for value in _walk(payload))

    bad_digest = copy.deepcopy(payload)
    bad_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            bad_digest,
        )


def test_resigned_payload_recomputes_status_reasons_scores_counts_ranks_and_aggregates() -> None:
    report_api = api()
    payload = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            build_report(*sample_observations()),
        )
    )

    forged_rank = copy.deepcopy(payload)
    forged_rank["rows"][0]["rank"] = "2.000000"
    _resign_payload(forged_rank)
    with pytest.raises(ValueError, match="rank"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_rank,
        )

    forged_observation_count = copy.deepcopy(payload)
    forged_observation_count["rows"][0]["observation_count"] = "3.000000"
    _resign_payload(forged_observation_count)
    with pytest.raises(ValueError, match="observation_count"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_observation_count,
        )

    forged_source_count = copy.deepcopy(payload)
    forged_source_count["rows"][0]["source_count"] = "2.000000"
    _resign_payload(forged_source_count)
    with pytest.raises(ValueError, match="source_count"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_source_count,
        )

    forged_calibration = copy.deepcopy(payload)
    forged_calibration["rows"][0]["calibration_score"] = "0.700000"
    _resign_payload(forged_calibration)
    with pytest.raises(ValueError, match="calibration_score"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_calibration,
        )

    forged_component = copy.deepcopy(payload)
    forged_component["rows"][0]["evidence_quality_contribution_score"] = "0.100000"
    _resign_payload(forged_component)
    with pytest.raises(ValueError, match="evidence_quality_contribution_score"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_component,
        )

    forged_score = copy.deepcopy(payload)
    forged_score["rows"][0]["attribution_score"] = "0.700000"
    _resign_payload(forged_score)
    with pytest.raises(ValueError, match="attribution_score"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_score,
        )

    forged_dominant = copy.deepcopy(payload)
    forged_dominant["rows"][0]["dominant_contribution"] = "outcome_learning"
    _resign_payload(forged_dominant)
    with pytest.raises(ValueError, match="dominant_contribution"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_dominant,
        )

    forged_status = copy.deepcopy(payload)
    forged_status["rows"][0]["status"] = "watch"
    _resign_payload(forged_status)
    with pytest.raises(ValueError, match="status"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_status,
        )

    forged_reasons = copy.deepcopy(payload)
    forged_reasons["rows"][0]["reason_codes"][-1] = "outcome_learning_dominant"
    _resign_payload(forged_reasons)
    with pytest.raises(ValueError, match="reason_codes"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_reasons,
        )

    forged_count = copy.deepcopy(payload)
    forged_count["specialist_count"] = "4.000000"
    _resign_payload(forged_count)
    with pytest.raises(ValueError, match="specialist_count"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_count,
        )

    forged_report_status = copy.deepcopy(payload)
    forged_report_status["status"] = "watch"
    _resign_payload(forged_report_status)
    with pytest.raises(ValueError, match="status"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_report_status,
        )

    forged_average = copy.deepcopy(payload)
    forged_average["average_attribution_score"] = "0.500000"
    _resign_payload(forged_average)
    with pytest.raises(ValueError, match="average_attribution_score"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_average,
        )

    forged_bucket = copy.deepcopy(payload)
    forged_bucket["contribution_buckets"][0]["specialist_count"] = "2.000000"
    _resign_payload(forged_bucket)
    with pytest.raises(ValueError, match="contribution_buckets"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_bucket,
        )

    forged_report_reasons = copy.deepcopy(payload)
    forged_report_reasons["reason_codes"] = [
        "specialist_forecast_attribution_report_block",
    ]
    _resign_payload(forged_report_reasons)
    with pytest.raises(ValueError, match="reason_codes"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            forged_report_reasons,
        )


def test_resigned_payload_rejects_observation_digest_reuse_across_specialists() -> None:
    report_api = api()
    payload = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            build_report(*sample_observations()),
        )
    )
    payload["rows"][1]["observation_digests"] = [
        payload["rows"][0]["observation_digests"][0],
    ]
    _resign_payload(payload)

    with pytest.raises(ValueError, match="observation_digests"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            payload,
        )


@pytest.mark.parametrize(
    ("field_name", "forged_value", "error_match"),
    (
        (
            "average_absolute_forecast_error",
            "0.100000",
            "calibration_score",
        ),
        (
            "evidence_quality_score",
            "0.600000",
            "evidence_quality_contribution_score",
        ),
        ("timeliness_score", "0.600000", "timeliness_contribution_score"),
        (
            "disagreement_handling_score",
            "0.500000",
            "disagreement_handling_contribution_score",
        ),
        (
            "outcome_learning_score",
            "0.700000",
            "outcome_learning_contribution_score",
        ),
        (
            "calibration_contribution_score",
            "0.200000",
            "calibration_contribution_score",
        ),
        (
            "timeliness_contribution_score",
            "0.100000",
            "timeliness_contribution_score",
        ),
        (
            "disagreement_handling_contribution_score",
            "0.080000",
            "disagreement_handling_contribution_score",
        ),
        (
            "outcome_learning_contribution_score",
            "0.150000",
            "outcome_learning_contribution_score",
        ),
    ),
)
def test_resigned_payload_recomputes_remaining_row_derivations(
    field_name: str,
    forged_value: str,
    error_match: str,
) -> None:
    report_api = api()
    payload = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            build_report(*sample_observations()),
        )
    )
    payload["rows"][0][field_name] = forged_value
    _resign_payload(payload)

    with pytest.raises(ValueError, match=error_match):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            payload,
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_attribution_score",
        "average_calibration_contribution_score",
        "average_evidence_quality_contribution_score",
        "average_timeliness_contribution_score",
        "average_disagreement_handling_contribution_score",
        "average_outcome_learning_contribution_score",
    ),
)
def test_resigned_payload_recomputes_remaining_report_derivations(
    field_name: str,
) -> None:
    report_api = api()
    payload = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            build_report(*sample_observations()),
        )
    )
    payload[field_name] = "0.000000"
    _resign_payload(payload)

    with pytest.raises(ValueError, match=field_name):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            payload,
        )


@pytest.mark.parametrize(
    ("field_name", "forged_value"),
    (
        ("contribution_code", "timeliness"),
        ("specialist_count", "0.000000"),
        ("observation_count", "0.000000"),
        ("average_attribution_score", "0.000000"),
    ),
)
def test_resigned_payload_recomputes_every_bucket_derivation(
    field_name: str,
    forged_value: str,
) -> None:
    report_api = api()
    payload = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            build_report(*sample_observations()),
        )
    )
    payload["contribution_buckets"][0][field_name] = forged_value
    _resign_payload(payload)

    with pytest.raises(ValueError, match="contribution_buckets"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            payload,
        )


def test_payload_validator_enforces_exact_schema_types_flags_and_canonical_values() -> None:
    report_api = api()
    payload = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            build_report(*sample_observations()),
        )
    )

    extra_report_key = copy.deepcopy(payload)
    extra_report_key["unexpected"] = "value"
    _resign_payload(extra_report_key)
    with pytest.raises(ValueError, match="payload keys"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            extra_report_key,
        )

    missing_report_key = copy.deepcopy(payload)
    missing_report_key.pop("status")
    _resign_payload(missing_report_key)
    with pytest.raises(ValueError, match="payload keys"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            missing_report_key,
        )

    extra_row_key = copy.deepcopy(payload)
    extra_row_key["rows"][0]["unexpected"] = "value"
    _resign_payload(extra_row_key)
    with pytest.raises(ValueError, match="row keys"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            extra_row_key,
        )

    extra_bucket_key = copy.deepcopy(payload)
    extra_bucket_key["contribution_buckets"][0]["unexpected"] = "value"
    _resign_payload(extra_bucket_key)
    with pytest.raises(ValueError, match="bucket keys"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            extra_bucket_key,
        )

    integer_count = copy.deepcopy(payload)
    integer_count["observation_count"] = 4
    _resign_payload(integer_count)
    with pytest.raises(ValueError, match="observation_count"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            integer_count,
        )

    float_score = copy.deepcopy(payload)
    float_score["rows"][0]["attribution_score"] = 0.735
    _resign_payload(float_score)
    with pytest.raises(ValueError, match="attribution_score"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            float_score,
        )

    noncanonical_count = copy.deepcopy(payload)
    noncanonical_count["observation_count"] = "4"
    _resign_payload(noncanonical_count)
    with pytest.raises(ValueError, match="observation_count"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            noncanonical_count,
        )

    signed_zero = copy.deepcopy(payload)
    signed_zero["rows"][0]["timeliness_score"] = "-0.000000"
    _resign_payload(signed_zero)
    with pytest.raises(ValueError, match="timeliness_score"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            signed_zero,
        )

    false_flag = copy.deepcopy(payload)
    false_flag["rows"][0]["readonly"] = False
    _resign_payload(false_flag)
    with pytest.raises(ValueError, match="readonly"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            false_flag,
        )


@pytest.mark.parametrize(
    ("layer", "error_match"),
    (
        ("report", "payload keys"),
        ("row", "row keys"),
        ("bucket", "bucket keys"),
    ),
)
def test_payload_requires_exact_canonical_key_order_even_when_resigned(
    layer: str,
    error_match: str,
) -> None:
    report_api = api()
    payload = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            build_report(*sample_observations()),
        )
    )

    if layer == "report":
        payload = {key: payload[key] for key in reversed(tuple(payload))}
    elif layer == "row":
        row = payload["rows"][0]
        payload["rows"][0] = {key: row[key] for key in reversed(tuple(row))}
    else:
        bucket = payload["contribution_buckets"][0]
        payload["contribution_buckets"][0] = {
            key: bucket[key]
            for key in reversed(tuple(bucket))
        }
    _resign_payload(payload)

    with pytest.raises(ValueError, match=error_match):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            payload,
        )


@pytest.mark.parametrize(
    ("layer", "defect", "error_match"),
    (
        ("row", "missing", "row keys"),
        ("row", "unknown", "row keys"),
        ("row", "type", "JSON objects"),
        ("row", "reorder", "row keys"),
        ("bucket", "missing", "bucket keys"),
        ("bucket", "unknown", "bucket keys"),
        ("bucket", "type", "JSON objects"),
        ("bucket", "reorder", "bucket keys"),
    ),
)
def test_payload_row_and_bucket_schema_rejects_every_shape_defect(
    layer: str,
    defect: str,
    error_match: str,
) -> None:
    report_api = api()
    payload = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            build_report(*sample_observations()),
        )
    )
    collection_name = "rows" if layer == "row" else "contribution_buckets"
    item = payload[collection_name][0]

    if defect == "missing":
        item.pop(next(iter(item)))
    elif defect == "unknown":
        item["unexpected"] = "value"
    elif defect == "type":
        payload[collection_name][0] = []
    else:
        payload[collection_name][0] = {
            key: item[key]
            for key in reversed(tuple(item))
        }
    _resign_payload(payload)

    with pytest.raises(ValueError, match=error_match):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            payload,
        )


def test_payload_rejects_datetime_decimal_and_hard_flag_type_drift() -> None:
    report_api = api()
    canonical = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            build_report(*sample_observations()),
        )
    )

    datetime_object = copy.deepcopy(canonical)
    datetime_object["generated_at"] = GENERATED_AT
    with pytest.raises(ValueError, match="generated_at"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            datetime_object,
        )

    noncanonical_datetime = copy.deepcopy(canonical)
    noncanonical_datetime["generated_at"] = "2026-07-10T12:00:00Z"
    _resign_payload(noncanonical_datetime)
    with pytest.raises(ValueError, match="generated_at"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            noncanonical_datetime,
        )

    for layer, field_name in (
        ("report", "observation_count"),
        ("row", "attribution_score"),
        ("bucket", "specialist_count"),
    ):
        decimal_object = copy.deepcopy(canonical)
        if layer == "report":
            container = decimal_object
        elif layer == "row":
            container = decimal_object["rows"][0]
        else:
            container = decimal_object["contribution_buckets"][0]
        container[field_name] = d(container[field_name])
        with pytest.raises(ValueError, match=field_name):
            report_api.validate_research_team_specialist_forecast_attribution_report_payload(
                decimal_object,
            )

    for layer in ("report", "row", "bucket"):
        for flag in ("paper_only", "report_only", "readonly"):
            false_flag = copy.deepcopy(canonical)
            if layer == "report":
                container = false_flag
            elif layer == "row":
                container = false_flag["rows"][0]
            else:
                container = false_flag["contribution_buckets"][0]
            container[flag] = False
            _resign_payload(false_flag)
            with pytest.raises(ValueError, match=flag):
                report_api.validate_research_team_specialist_forecast_attribution_report_payload(
                    false_flag,
                )


def test_resigned_payload_rejects_bucket_and_unequal_score_row_reordering() -> None:
    report_api = api()
    canonical = (
        report_api.research_team_specialist_forecast_attribution_report_payload(
            build_report(*sample_observations()),
        )
    )

    reordered_rows = copy.deepcopy(canonical)
    reordered_rows["rows"].reverse()
    assert (
        reordered_rows["rows"][0]["attribution_score"]
        != reordered_rows["rows"][1]["attribution_score"]
    )
    for index, row in enumerate(reordered_rows["rows"], start=1):
        row["rank"] = f"{index}.000000"
    _resign_payload(reordered_rows)
    with pytest.raises(ValueError, match="deterministic sequence"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            reordered_rows,
        )

    reordered_buckets = copy.deepcopy(canonical)
    reordered_buckets["contribution_buckets"].reverse()
    _resign_payload(reordered_buckets)
    with pytest.raises(ValueError, match="contribution_buckets"):
        report_api.validate_research_team_specialist_forecast_attribution_report_payload(
            reordered_buckets,
        )


def test_raw_bounds_nonfinite_signed_zero_exact_types_and_hard_flags() -> None:
    report_api = api()

    with pytest.raises(ValueError, match="forecast_probability"):
        observation(forecast_probability=d("1.0000004"))
    with pytest.raises(ValueError, match="resolved_probability"):
        observation(resolved_probability=d("-0.0000004"))
    with pytest.raises(ValueError, match="evidence_quality_score"):
        observation(evidence_quality_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="timeliness_score"):
        observation(timeliness_score=Decimal("Infinity"))
    with pytest.raises(ValueError, match="disagreement_handling_score"):
        observation(disagreement_handling_score=Decimal("-0"))
    with pytest.raises(ValueError, match="outcome_learning_score"):
        observation(outcome_learning_score=0.5)
    with pytest.raises(ValueError, match="forecast_probability"):
        observation(forecast_probability=1)
    with pytest.raises(ValueError, match="forecast_probability"):
        observation(forecast_probability=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="specialist_identifier"):
        observation(
            specialist_identifier=_StringSubclass("private-specialist"),
        )
    with pytest.raises(ValueError, match="source_identifiers"):
        observation(source_identifiers=())
    with pytest.raises(ValueError, match="source_identifiers"):
        observation(source_identifiers=["private-source"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observation_digest"):
        observation(observation_digest="A" * 64)
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 10, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(
            observed_at=_DateTimeSubclass(2026, 7, 10, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)

    with pytest.raises(ValueError, match="calibration_weight"):
        report_api.ResearchTeamSpecialistForecastAttributionConfig(
            calibration_weight=d("1.0000004"),
        )
    with pytest.raises(ValueError, match="component_drag_threshold"):
        report_api.ResearchTeamSpecialistForecastAttributionConfig(
            component_drag_threshold=Decimal("-0"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        report_api.ResearchTeamSpecialistForecastAttributionConfig(
            paper_only=False,
        )
    with pytest.raises(ValueError, match="config"):
        report_api.build_research_team_specialist_forecast_attribution_report(
            (),
            generated_at=GENERATED_AT,
            config=object(),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report_api.build_research_team_specialist_forecast_attribution_report(
            (),
            generated_at=_DateTimeSubclass(2026, 7, 10, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="after generated_at"):
        build_report(
            observation(observed_at=GENERATED_AT + timedelta(microseconds=1)),
        )
    duplicate = observation()
    with pytest.raises(ValueError, match="unique"):
        build_report(duplicate, duplicate)
    with pytest.raises(ValueError, match="observations"):
        build_report(object())


def test_build_and_payload_validation_ignore_ambient_decimal_context() -> None:
    report_api = api()
    observations = sample_observations()

    with localcontext() as context:
        context.prec = 4
        context.rounding = ROUND_DOWN
        low_precision = build_report(*observations)
        low_precision_payload = (
            report_api.research_team_specialist_forecast_attribution_report_payload(
                low_precision,
            )
        )
        assert (
            report_api.validate_research_team_specialist_forecast_attribution_report_payload(
                low_precision_payload,
            )
            is True
        )

    with localcontext() as context:
        context.prec = 48
        context.rounding = ROUND_UP
        high_precision = build_report(*observations)
        high_precision_payload = (
            report_api.research_team_specialist_forecast_attribution_report_payload(
                high_precision,
            )
        )
        assert (
            report_api.validate_research_team_specialist_forecast_attribution_report_payload(
                high_precision_payload,
            )
            is True
        )

    assert low_precision == high_precision
    assert low_precision_payload == high_precision_payload
    assert low_precision.average_attribution_score == d("0.538333")


def test_dataclasses_are_frozen_final_decimal_only_and_reject_manual_drift() -> None:
    report_api = api()
    item = observation()
    report = build_report(*sample_observations())
    public_values = (
        report_api.ResearchTeamSpecialistForecastAttributionConfig(),
        item,
        report.rows[0],
        report.contribution_buckets[0],
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

    for dataclass_type in (
        report_api.ResearchTeamSpecialistForecastAttributionConfig,
        report_api.ResearchTeamSpecialistForecastAttributionObservation,
        report_api.ResearchTeamSpecialistForecastAttributionRow,
        report_api.ResearchTeamSpecialistForecastAttributionBucket,
        report_api.ResearchTeamSpecialistForecastAttributionReport,
    ):
        with pytest.raises(TypeError, match="subclassing"):
            type("UnsafeSubclass", (dataclass_type,), {})

    with pytest.raises(ValueError, match="source_count"):
        replace(report.rows[0], source_count=d("2.000000"))
    with pytest.raises(ValueError, match="attribution_score"):
        replace(report.rows[0], attribution_score=d("0.500000"))
    with pytest.raises(ValueError, match="rank"):
        changed_rank = replace(report.rows[0], rank=d("2.000000"))
        replace(report, rows=(changed_rank, *report.rows[1:]))
    with pytest.raises(ValueError, match="average_attribution_score"):
        replace(report, average_attribution_score=d("0.500000"))
    with pytest.raises(ValueError, match="contribution_buckets"):
        changed_bucket = replace(
            report.contribution_buckets[0],
            specialist_count=d("2.000000"),
        )
        replace(
            report,
            contribution_buckets=(
                changed_bucket,
                *report.contribution_buckets[1:],
            ),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_module_has_no_network_persistence_wallet_auth_order_or_live_surface() -> None:
    report_api = api()
    source = inspect.getsource(report_api)
    _assert_ast_has_no_io(source)

    forbidden_public_parts = (
        "wallet",
        "trade",
        "position",
        "sizing",
        "recommendation",
        "execution",
        "authentication",
        "database",
        "persistence",
        "live",
    )
    for public_name in report_api.__all__:
        lowered = public_name.lower()
        assert not any(part in lowered for part in forbidden_public_parts)
    for dataclass_type in (
        report_api.ResearchTeamSpecialistForecastAttributionConfig,
        report_api.ResearchTeamSpecialistForecastAttributionObservation,
        report_api.ResearchTeamSpecialistForecastAttributionRow,
        report_api.ResearchTeamSpecialistForecastAttributionBucket,
        report_api.ResearchTeamSpecialistForecastAttributionReport,
    ):
        for field in fields(dataclass_type):
            lowered = field.name.lower()
            assert not any(part in lowered for part in forbidden_public_parts)


@pytest.mark.parametrize(
    "unsafe_source",
    (
        "import requests as client\nclient.get('https://example.com')\n",
        "from httpx import get as fetch\nfetch('https://example.com')\n",
        "import aiohttp as web\nweb.ClientSession()\n",
        "import urllib3 as pool\npool.PoolManager().request('GET', 'https://x')\n",
        "import tempfile as scratch\nscratch.NamedTemporaryFile()\n",
        "from pathlib import Path as P\nP('x').write_text('unsafe')\n",
        "import subprocess as process\nprocess.run(['true'])\n",
        "import socket as network\nnetwork.socket()\n",
        "import importlib as loader\nloader.import_module('requests')\n",
        "from importlib import import_module as load\nload('socket')\n",
        "__import__('subprocess').run(['true'])\n",
    ),
)
def test_ast_no_io_guard_detects_aliases_dynamic_imports_and_io_modules(
    unsafe_source: str,
) -> None:
    with pytest.raises(AssertionError):
        _assert_ast_has_no_io(unsafe_source)


def test_ast_no_io_guard_allows_pure_object_methods() -> None:
    _assert_ast_has_no_io(
        "values = {'answer': 42}\n"
        "answer = values.get('answer')\n"
        "encoded = str(answer).encode('utf-8')\n",
    )


def _ast_call_name(node: ast.AST, aliases: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        owner = _ast_call_name(node.value, aliases)
        return f"{owner}.{node.attr}" if owner else node.attr
    if isinstance(node, ast.Call):
        return _ast_call_name(node.func, aliases)
    return ""


def _assert_ast_has_no_io(source: str) -> None:
    syntax_tree = ast.parse(source)
    aliases: dict[str, str] = {}
    forbidden_roots = {
        "aiohttp",
        "ccxt",
        "http",
        "httpcore",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
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
        "NamedTemporaryFile",
        "Popen",
        "TemporaryDirectory",
        "mkdir",
        "open",
        "read_bytes",
        "read_text",
        "touch",
        "unlink",
        "urlopen",
        "write_bytes",
        "write_text",
    }

    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                root = imported.name.split(".", 1)[0]
                assert root not in forbidden_roots
                local_name = imported.asname or root
                aliases[local_name] = imported.name if imported.asname else root
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            root = node.module.split(".", 1)[0]
            assert root not in forbidden_roots
            for imported in node.names:
                local_name = imported.asname or imported.name
                aliases[local_name] = f"{node.module}.{imported.name}"
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    for node in ast.walk(syntax_tree):
        if not isinstance(node, ast.Call):
            continue
        call_name = _ast_call_name(node.func, aliases)
        if call_name in {"__import__", "importlib.import_module"}:
            raise AssertionError("dynamic imports are not allowed")
        root = call_name.split(".", 1)[0]
        assert root not in forbidden_roots
        assert call_name.rsplit(".", 1)[-1] not in forbidden_calls


def _payload_digest(payload: dict[str, object]) -> str:
    values = copy.deepcopy(payload)
    values.pop("derived_validation_digest", None)
    canonical = json.dumps(
        values,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _resign_payload(payload: dict[str, object]) -> None:
    payload["derived_validation_digest"] = _payload_digest(payload)


def _walk(value: object):
    if type(value) is dict:
        for item in value.values():
            yield from _walk(item)
    elif type(value) in (list, tuple):
        for item in value:
            yield from _walk(item)
    else:
        yield value


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
