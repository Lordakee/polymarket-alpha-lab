from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from hashlib import sha256
import importlib
import json
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, ROUND_UP, localcontext
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)

CONFIG_FIELDS = (
    "config_version",
    "min_pass_authority_coverage_ratio",
    "min_watch_authority_coverage_ratio",
    "max_pass_freshness_lag_seconds",
    "max_watch_freshness_lag_seconds",
    "max_pass_contradiction_pressure_ratio",
    "max_watch_contradiction_pressure_ratio",
    "min_pass_extraction_confidence_score",
    "min_watch_extraction_confidence_score",
    "max_pass_missing_critical_field_count",
    "max_watch_missing_critical_field_count",
    "min_pass_available_reviewer_capacity_count",
    "min_watch_available_reviewer_capacity_count",
    "paper_only",
    "report_only",
    "readonly",
)
INPUT_FIELDS = (
    "domain_label",
    "verification_queue_label",
    "evidence_family_label",
    "required_authority_reference_count",
    "covered_authority_reference_count",
    "freshness_lag_seconds",
    "contradiction_signal_count",
    "reviewed_claim_count",
    "extraction_confidence_score",
    "missing_critical_field_count",
    "available_reviewer_capacity_count",
    "observed_at",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_FIELDS = (
    "bottleneck_rank",
    "domain_label",
    "verification_queue_label",
    "evidence_family_label",
    "status",
    "bottleneck_pressure_score",
    "required_authority_reference_count",
    "covered_authority_reference_count",
    "authority_coverage_ratio",
    "freshness_lag_seconds",
    "contradiction_signal_count",
    "reviewed_claim_count",
    "contradiction_pressure_ratio",
    "extraction_confidence_score",
    "missing_critical_field_count",
    "available_reviewer_capacity_count",
    "reviewer_capacity_gap_count",
    "reviewer_capacity_gap_ratio",
    "observed_at",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_FIELDS = (
    "generated_at",
    "config_version",
    "config",
    "input_count",
    "bottleneck_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_authority_coverage_ratio",
    "max_freshness_lag_seconds",
    "max_contradiction_pressure_ratio",
    "min_extraction_confidence_score",
    "total_missing_critical_field_count",
    "min_available_reviewer_capacity_count",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_verification_bottleneck_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(
    domain_label: str = "macro_policy",
    verification_queue_label: str = "settlement_review",
    evidence_family_label: str = "official_release",
    *,
    required_authority_reference_count: Decimal = d("5"),
    covered_authority_reference_count: Decimal = d("5"),
    freshness_lag_seconds: Decimal = d("3600.000000"),
    contradiction_signal_count: Decimal = d("0"),
    reviewed_claim_count: Decimal = d("10"),
    extraction_confidence_score: Decimal = d("0.950000"),
    missing_critical_field_count: Decimal = d("0"),
    available_reviewer_capacity_count: Decimal = d("3"),
    observed_at: datetime = GENERATED_AT,
):
    module = api()
    return module.ResearchSourceVerificationBottleneckInput(
        domain_label=domain_label,
        verification_queue_label=verification_queue_label,
        evidence_family_label=evidence_family_label,
        required_authority_reference_count=required_authority_reference_count,
        covered_authority_reference_count=covered_authority_reference_count,
        freshness_lag_seconds=freshness_lag_seconds,
        contradiction_signal_count=contradiction_signal_count,
        reviewed_claim_count=reviewed_claim_count,
        extraction_confidence_score=extraction_confidence_score,
        missing_critical_field_count=missing_critical_field_count,
        available_reviewer_capacity_count=available_reviewer_capacity_count,
        observed_at=observed_at,
    )


def _config(**overrides: object):
    module = api()
    return module.ResearchSourceVerificationBottleneckConfig(**overrides)


def _build_report(*rows, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_source_verification_bottleneck_report(
        rows,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def _resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = deepcopy(payload)
    digest_material = dict(resigned)
    digest_material.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_material,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    resigned["derived_validation_digest"] = sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return resigned


def _row_identity(row: object) -> tuple[str, str, str]:
    return (
        getattr(row, "domain_label"),
        getattr(row, "verification_queue_label"),
        getattr(row, "evidence_family_label"),
    )


def _input_at_metric_value(field_name: str, value: Decimal):
    if field_name == "authority_coverage_ratio":
        scaled = value * d("1000000")
        assert scaled == scaled.to_integral_value()
        return _input(
            required_authority_reference_count=d("1000000"),
            covered_authority_reference_count=scaled,
        )
    if field_name == "contradiction_pressure_ratio":
        scaled = value * d("1000000")
        assert scaled == scaled.to_integral_value()
        return _input(
            contradiction_signal_count=scaled,
            reviewed_claim_count=d("1000000"),
        )
    return _input(**{field_name: value})


def test_bottleneck_report_rolls_up_statuses_metrics_payload_and_digest() -> None:
    module = api()
    pass_input = _input(
        "macro_policy",
        "settlement_review",
        "official_release",
    )
    watch_input = _input(
        "weather_events",
        "evidence_review",
        "agency_bulletin",
        required_authority_reference_count=d("4"),
        covered_authority_reference_count=d("3"),
        freshness_lag_seconds=d("90000.000000"),
        contradiction_signal_count=d("1"),
        reviewed_claim_count=d("10"),
        extraction_confidence_score=d("0.800000"),
        missing_critical_field_count=d("1"),
        available_reviewer_capacity_count=d("1"),
    )
    block_input = _input(
        "company_actions",
        "resolution_review",
        "issuer_filing",
        required_authority_reference_count=d("5"),
        covered_authority_reference_count=d("2"),
        freshness_lag_seconds=d("400000.000000"),
        contradiction_signal_count=d("4"),
        reviewed_claim_count=d("8"),
        extraction_confidence_score=d("0.400000"),
        missing_critical_field_count=d("3"),
        available_reviewer_capacity_count=d("0"),
    )

    report = _build_report(pass_input, watch_input, block_input)
    permuted = _build_report(block_input, pass_input, watch_input)
    payload = module.research_source_verification_bottleneck_report_payload(report)
    permuted_payload = module.research_source_verification_bottleneck_report_payload(
        permuted,
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("3")
    assert report.bottleneck_count == d("2")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_authority_coverage_ratio == d("0.716667")
    assert report.max_freshness_lag_seconds == d("400000.000000")
    assert report.max_contradiction_pressure_ratio == d("0.500000")
    assert report.min_extraction_confidence_score == d("0.400000")
    assert report.total_missing_critical_field_count == d("4")
    assert report.min_available_reviewer_capacity_count == d("0")
    assert report.reason_codes == (
        "research_source_verification_authority_coverage_block",
        "research_source_verification_freshness_lag_block",
        "research_source_verification_contradiction_pressure_block",
        "research_source_verification_extraction_confidence_block",
        "research_source_verification_missing_critical_fields_block",
        "research_source_verification_reviewer_capacity_block",
        "research_source_verification_authority_coverage_watch",
        "research_source_verification_freshness_lag_watch",
        "research_source_verification_contradiction_pressure_watch",
        "research_source_verification_extraction_confidence_watch",
        "research_source_verification_missing_critical_fields_watch",
        "research_source_verification_reviewer_capacity_watch",
        "research_source_verification_clear",
    )
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert report.derived_validation_digest == (
        module.research_source_verification_bottleneck_report_digest(report)
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    blocked = report.rows[0]
    assert blocked.domain_label == "company_actions"
    assert blocked.authority_coverage_ratio == d("0.400000")
    assert blocked.contradiction_pressure_ratio == d("0.500000")
    assert blocked.reviewer_capacity_gap_count == d("2")
    assert blocked.reviewer_capacity_gap_ratio == d("1.000000")
    assert blocked.bottleneck_pressure_score == d("1.000000")
    assert blocked.reason_codes == (
        "research_source_verification_authority_coverage_block",
        "research_source_verification_freshness_lag_block",
        "research_source_verification_contradiction_pressure_block",
        "research_source_verification_extraction_confidence_block",
        "research_source_verification_missing_critical_fields_block",
        "research_source_verification_reviewer_capacity_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.authority_coverage_ratio == d("0.750000")
    assert watched.contradiction_pressure_ratio == d("0.100000")
    assert watched.reason_codes == (
        "research_source_verification_authority_coverage_watch",
        "research_source_verification_freshness_lag_watch",
        "research_source_verification_contradiction_pressure_watch",
        "research_source_verification_extraction_confidence_watch",
        "research_source_verification_missing_critical_fields_watch",
        "research_source_verification_reviewer_capacity_watch",
    )

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.reason_codes == ("research_source_verification_clear",)

    assert payload == permuted_payload
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["config"]["config_version"] == report.config_version
    assert payload["rows"][0]["authority_coverage_ratio"] == "0.400000"
    assert payload["rows"][0]["freshness_lag_seconds"] == "400000.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    assert _unsafe_public_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_empty_report_is_pass_report_only_and_timezone_normalized() -> None:
    module = api()
    local_generated_at = datetime(
        2026,
        7,
        8,
        10,
        30,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    report = _build_report(generated_at=local_generated_at)
    payload = module.research_source_verification_bottleneck_report_payload(report)

    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.reason_codes == ("research_source_verification_empty",)
    assert report.input_count == d("0")
    assert report.bottleneck_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.average_authority_coverage_ratio == d("0.000000")
    assert report.max_freshness_lag_seconds == d("0.000000")
    assert report.max_contradiction_pressure_ratio == d("0.000000")
    assert report.min_extraction_confidence_score == d("0.000000")
    assert report.total_missing_critical_field_count == d("0")
    assert report.min_available_reviewer_capacity_count == d("0")
    assert report.rows == ()
    assert payload["generated_at"] == "2026-07-08T14:30:00+00:00"
    assert payload["status"] == "pass"
    assert payload["rows"] == []
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert _float_paths(payload) == ()
    assert _unsafe_public_paths(payload) == ()


def test_utc_datetime_normalization_clears_noncanonical_fold() -> None:
    folded = datetime(2026, 7, 8, 14, 30, tzinfo=UTC, fold=1)

    input_row = _input(observed_at=folded)
    report = _build_report(input_row, generated_at=folded)

    assert input_row.observed_at.tzinfo is UTC
    assert input_row.observed_at.fold == 0
    assert report.generated_at.tzinfo is UTC
    assert report.generated_at.fold == 0
    assert report.rows[0].observed_at.tzinfo is UTC
    assert report.rows[0].observed_at.fold == 0


def test_decimal_frozen_flags_and_consistency_are_validated() -> None:
    module = api()
    report = _build_report(_input())

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report, status="ready")
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="required_authority_reference_count must be a Decimal"):
        _input(required_authority_reference_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="extraction_confidence_score must be finite"):
        _input(extraction_confidence_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="missing_critical_field_count must be nonnegative"):
        _input(missing_critical_field_count=d("-1"))
    with pytest.raises(ValueError, match="reviewed_claim_count must be integral"):
        _input(reviewed_claim_count=d("1.500000"))
    with pytest.raises(ValueError, match="covered_authority_reference_count"):
        _input(covered_authority_reference_count=d("6"))
    with pytest.raises(ValueError, match="contradiction_signal_count"):
        _input(contradiction_signal_count=d("2"), reviewed_claim_count=d("1"))
    with pytest.raises(ValueError, match="min_watch_authority_coverage_ratio"):
        _config(
            min_pass_authority_coverage_ratio=d("0.500000"),
            min_watch_authority_coverage_ratio=d("0.800000"),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_verification_bottleneck_report(
            (_input(),),
            config=_config(),
            generated_at=datetime(2026, 7, 8, 14, 30),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.ResearchSourceVerificationBottleneckConfig(readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="rows must be sorted"):
        unordered = _build_report(
            _input("z_domain", "z_queue", "z_family"),
            _input("a_domain", "a_queue", "a_family"),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


@pytest.mark.parametrize("surface", ("builder", "resigned_payload"))
def test_observed_at_must_not_be_after_generated_at(surface: str) -> None:
    module = api()

    if surface == "builder":
        with pytest.raises(
            ValueError,
            match="observed_at must not be after generated_at",
        ):
            _build_report(
                _input(observed_at=GENERATED_AT + timedelta(microseconds=1)),
            )
        return

    payload = module.research_source_verification_bottleneck_report_payload(
        _build_report(_input()),
    )
    payload["rows"][0]["observed_at"] = (
        GENERATED_AT + timedelta(microseconds=1)
    ).isoformat()

    with pytest.raises(
        ValueError,
        match="observed_at must not be after generated_at",
    ):
        module.research_source_verification_bottleneck_report_payload(
            _resign_payload(payload),
        )


@pytest.mark.parametrize("invalid_inputs", (None, 1, True, object()))
def test_builder_rejects_non_iterable_inputs_with_value_error(
    invalid_inputs: object,
) -> None:
    module = api()

    with pytest.raises(ValueError, match="inputs must be an iterable"):
        module.build_research_source_verification_bottleneck_report(
            invalid_inputs,  # type: ignore[arg-type]
            config=_config(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "expected_error"),
    (
        (
            "min_pass_authority_coverage_ratio",
            1,
            "min_pass_authority_coverage_ratio must be a Decimal",
        ),
        (
            "max_pass_contradiction_pressure_ratio",
            d("-0"),
            "max_pass_contradiction_pressure_ratio must not be signed zero",
        ),
        (
            "max_pass_freshness_lag_seconds",
            d("86400"),
            "max_pass_freshness_lag_seconds must use canonical Decimal precision",
        ),
    ),
)
def test_builder_revalidates_tampered_config_decimal_surfaces(
    field_name: str,
    invalid_value: object,
    expected_error: str,
) -> None:
    config = _config()
    object.__setattr__(config, field_name, invalid_value)

    with pytest.raises(ValueError, match=expected_error):
        _build_report(config=config)


def test_direct_rows_reject_forged_derived_status_reasons_gaps_and_score() -> None:
    report = _build_report(
        _input(
            required_authority_reference_count=d("4"),
            covered_authority_reference_count=d("3"),
            freshness_lag_seconds=d("90000"),
            contradiction_signal_count=d("1"),
            reviewed_claim_count=d("10"),
            extraction_confidence_score=d("0.800000"),
            missing_critical_field_count=d("1"),
            available_reviewer_capacity_count=d("1"),
        ),
    )
    row = report.rows[0]

    with pytest.raises(ValueError, match="reason_codes must match row inputs"):
        replace(
            row,
            status="pass",
            reason_codes=("research_source_verification_clear",),
        )
    with pytest.raises(ValueError, match="reason_codes must match row inputs"):
        replace(
            row,
            reason_codes=(
                "research_source_verification_authority_coverage_watch",
            ),
        )
    with pytest.raises(ValueError, match="reviewer_capacity_gap_count"):
        replace(row, reviewer_capacity_gap_count=d("0"))
    with pytest.raises(ValueError, match="reviewer_capacity_gap_ratio"):
        replace(row, reviewer_capacity_gap_ratio=d("0.250000"))
    with pytest.raises(ValueError, match="bottleneck_pressure_score"):
        replace(row, bottleneck_pressure_score=d("0.123456"))


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    (
        ("bottleneck_rank", 1),
        ("bottleneck_pressure_score", 0),
        ("authority_coverage_ratio", 1),
        ("contradiction_pressure_ratio", 0),
        ("reviewer_capacity_gap_count", 0),
        ("reviewer_capacity_gap_ratio", 0),
    ),
)
def test_report_revalidates_tampered_row_derived_decimal_surfaces(
    field_name: str,
    invalid_value: object,
) -> None:
    report = _build_report(_input())
    object.__setattr__(report.rows[0], field_name, invalid_value)

    with pytest.raises(ValueError, match=rf"{field_name} must be a Decimal"):
        replace(report, derived_validation_digest="")


def test_report_revalidates_tampered_row_canonical_utc_surface() -> None:
    report = _build_report(_input())
    offset_observed_at = GENERATED_AT.astimezone(
        timezone(timedelta(hours=-4)),
    )
    object.__setattr__(report.rows[0], "observed_at", offset_observed_at)

    with pytest.raises(ValueError, match="observed_at must be canonical UTC"):
        replace(report, derived_validation_digest="")


@pytest.mark.parametrize(
    ("surface", "expected_error"),
    (
        ("row_status", "status must be pass, watch, or block"),
        ("row_reason_codes", "reason_codes must be a tuple"),
        ("config_version", "config_version must be a non-empty string"),
    ),
)
def test_report_revalidates_tampered_nested_exact_types(
    surface: str,
    expected_error: str,
) -> None:
    class StringSubclass(str):
        pass

    class TupleSubclass(tuple):
        pass

    report = _build_report(_input())
    if surface == "row_status":
        object.__setattr__(report.rows[0], "status", StringSubclass("pass"))
    elif surface == "row_reason_codes":
        object.__setattr__(
            report.rows[0],
            "reason_codes",
            TupleSubclass(report.rows[0].reason_codes),
        )
    else:
        object.__setattr__(
            report.config,
            "config_version",
            StringSubclass(report.config.config_version),
        )

    with pytest.raises(ValueError, match=expected_error):
        replace(report, derived_validation_digest="")


def test_noop_resign_is_accepted_and_preserves_the_public_payload() -> None:
    module = api()
    payload = module.research_source_verification_bottleneck_report_payload(
        _build_report(_input()),
    )

    resigned = _resign_payload(payload)

    assert resigned == payload
    assert module.research_source_verification_bottleneck_report_payload(resigned) == payload


def test_resigned_forged_payloads_reject_specific_derived_semantic_mismatches() -> None:
    module = api()
    payload = module.research_source_verification_bottleneck_report_payload(
        _build_report(
            _input(
                required_authority_reference_count=d("4"),
                covered_authority_reference_count=d("3"),
                freshness_lag_seconds=d("90000"),
                contradiction_signal_count=d("1"),
                reviewed_claim_count=d("10"),
                extraction_confidence_score=d("0.800000"),
                missing_critical_field_count=d("1"),
                available_reviewer_capacity_count=d("1"),
            ),
        ),
    )

    cases = (
        (
            "report status",
            lambda value: value.__setitem__("status", "pass"),
            "status must match rows",
        ),
        (
            "report reasons",
            lambda value: value.__setitem__(
                "reason_codes",
                ["research_source_verification_clear"],
            ),
            "reason_codes must match rows",
        ),
        (
            "input count",
            lambda value: value.__setitem__("input_count", "2.000000"),
            "input_count must match rows",
        ),
        (
            "bottleneck count",
            lambda value: value.__setitem__("bottleneck_count", "0.000000"),
            "bottleneck_count must match rows",
        ),
        (
            "pass count",
            lambda value: value.__setitem__("pass_count", "1.000000"),
            "pass_count must match rows",
        ),
        (
            "watch count",
            lambda value: value.__setitem__("watch_count", "0.000000"),
            "watch_count must match rows",
        ),
        (
            "block count",
            lambda value: value.__setitem__("block_count", "1.000000"),
            "block_count must match rows",
        ),
        (
            "average authority coverage",
            lambda value: value.__setitem__(
                "average_authority_coverage_ratio",
                "0.999999",
            ),
            "average_authority_coverage_ratio must match rows",
        ),
        (
            "max freshness",
            lambda value: value.__setitem__(
                "max_freshness_lag_seconds",
                "89999.000000",
            ),
            "max_freshness_lag_seconds must match rows",
        ),
        (
            "max contradiction pressure",
            lambda value: value.__setitem__(
                "max_contradiction_pressure_ratio",
                "0.200000",
            ),
            "max_contradiction_pressure_ratio must match rows",
        ),
        (
            "min extraction confidence",
            lambda value: value.__setitem__(
                "min_extraction_confidence_score",
                "0.900000",
            ),
            "min_extraction_confidence_score must match rows",
        ),
        (
            "total missing fields",
            lambda value: value.__setitem__(
                "total_missing_critical_field_count",
                "0.000000",
            ),
            "total_missing_critical_field_count must match rows",
        ),
        (
            "min reviewer capacity",
            lambda value: value.__setitem__(
                "min_available_reviewer_capacity_count",
                "2.000000",
            ),
            "min_available_reviewer_capacity_count must match rows",
        ),
        (
            "row status",
            lambda value: value["rows"][0].__setitem__("status", "pass"),
            "status must match reason_codes",
        ),
        (
            "row reasons",
            lambda value: value["rows"][0].__setitem__(
                "reason_codes",
                ["research_source_verification_authority_coverage_watch"],
            ),
            "reason_codes must match row inputs",
        ),
        (
            "row pressure",
            lambda value: value["rows"][0].__setitem__(
                "bottleneck_pressure_score",
                "0.123456",
            ),
            "bottleneck_pressure_score must match row inputs",
        ),
        (
            "row reviewer gap count",
            lambda value: value["rows"][0].__setitem__(
                "reviewer_capacity_gap_count",
                "0.000000",
            ),
            "reviewer_capacity_gap_count must match reviewer capacity",
        ),
        (
            "row reviewer gap ratio",
            lambda value: value["rows"][0].__setitem__(
                "reviewer_capacity_gap_ratio",
                "0.250000",
            ),
            "reviewer_capacity_gap_ratio must match reviewer capacity",
        ),
        (
            "row authority ratio",
            lambda value: value["rows"][0].__setitem__(
                "authority_coverage_ratio",
                "0.800000",
            ),
            "authority_coverage_ratio must match authority counts",
        ),
        (
            "row contradiction ratio",
            lambda value: value["rows"][0].__setitem__(
                "contradiction_pressure_ratio",
                "0.200000",
            ),
            "contradiction_pressure_ratio must match contradiction counts",
        ),
        (
            "row rank",
            lambda value: value["rows"][0].__setitem__(
                "bottleneck_rank",
                "2.000000",
            ),
            "bottleneck_rank must match deterministic row order",
        ),
    )
    for _case_name, mutate, expected_error in cases:
        forged = deepcopy(payload)
        mutate(forged)
        forged = _resign_payload(forged)
        with pytest.raises(ValueError, match=expected_error):
            module.research_source_verification_bottleneck_report_payload(forged)


def test_resigned_row_reordering_duplicate_keys_and_joint_rank_order_forgery_fail() -> None:
    module = api()
    payload = module.research_source_verification_bottleneck_report_payload(
        _build_report(
            _input("a_domain", "queue", "family"),
            _input("b_domain", "queue", "family"),
        ),
    )

    reordered = deepcopy(payload)
    reordered["rows"].reverse()
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        module.research_source_verification_bottleneck_report_payload(
            _resign_payload(reordered),
        )

    duplicate_key = deepcopy(payload)
    duplicate_key["rows"][1]["domain_label"] = duplicate_key["rows"][0]["domain_label"]
    with pytest.raises(
        ValueError,
        match="rows must not contain duplicate source verification keys",
    ):
        module.research_source_verification_bottleneck_report_payload(
            _resign_payload(duplicate_key),
        )

    joint_rank_order = deepcopy(payload)
    joint_rank_order["rows"].reverse()
    for index, row in enumerate(joint_rank_order["rows"], start=1):
        row["bottleneck_rank"] = f"{index}.000000"
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        module.research_source_verification_bottleneck_report_payload(
            _resign_payload(joint_rank_order),
        )


def test_payload_requires_exact_report_and_row_json_schemas() -> None:
    module = api()
    payload = module.research_source_verification_bottleneck_report_payload(
        _build_report(_input()),
    )

    assert tuple(payload) == REPORT_FIELDS
    assert tuple(payload["config"]) == CONFIG_FIELDS
    assert tuple(payload["rows"][0]) == ROW_FIELDS

    invalid_payloads: list[dict[str, Any]] = []
    extra_report_field = deepcopy(payload)
    extra_report_field["unexpected"] = "safe"
    invalid_payloads.append(extra_report_field)
    missing_report_field = deepcopy(payload)
    missing_report_field.pop("status")
    invalid_payloads.append(missing_report_field)
    tuple_rows = deepcopy(payload)
    tuple_rows["rows"] = tuple(tuple_rows["rows"])
    invalid_payloads.append(tuple_rows)
    numeric_decimal = deepcopy(payload)
    numeric_decimal["input_count"] = 1
    invalid_payloads.append(numeric_decimal)
    extra_config_field = deepcopy(payload)
    extra_config_field["config"]["unexpected"] = "safe"
    invalid_payloads.append(extra_config_field)
    numeric_config_decimal = deepcopy(payload)
    numeric_config_decimal["config"]["min_pass_authority_coverage_ratio"] = 0.9
    invalid_payloads.append(numeric_config_decimal)
    extra_row_field = deepcopy(payload)
    extra_row_field["rows"][0]["unexpected"] = "safe"
    invalid_payloads.append(extra_row_field)
    missing_row_field = deepcopy(payload)
    missing_row_field["rows"][0].pop("status")
    invalid_payloads.append(missing_row_field)
    tuple_reason_codes = deepcopy(payload)
    tuple_reason_codes["rows"][0]["reason_codes"] = tuple(
        tuple_reason_codes["rows"][0]["reason_codes"],
    )
    invalid_payloads.append(tuple_reason_codes)

    for invalid_payload in invalid_payloads:
        with pytest.raises(ValueError, match="schema"):
            module.research_source_verification_bottleneck_report_payload(
                _resign_payload(invalid_payload),
            )


@pytest.mark.parametrize("cycle_surface", ("config", "rows"))
def test_public_payload_rejects_cyclic_containers(cycle_surface: str) -> None:
    module = api()
    payload = module.research_source_verification_bottleneck_report_payload(
        _build_report(_input()),
    )
    if cycle_surface == "config":
        payload["config"] = payload
    else:
        payload["rows"].append(payload["rows"])

    with pytest.raises(ValueError, match="public payload must not contain cycles"):
        module.research_source_verification_bottleneck_report_payload(payload)


def test_payload_requires_canonical_key_order_at_every_schema_level() -> None:
    module = api()
    payload = module.research_source_verification_bottleneck_report_payload(
        _build_report(_input()),
    )

    reordered_report = {
        key: payload[key]
        for key in (*REPORT_FIELDS[1:], REPORT_FIELDS[0])
    }
    reordered_config = deepcopy(payload)
    reordered_config["config"] = {
        key: reordered_config["config"][key]
        for key in (*CONFIG_FIELDS[1:], CONFIG_FIELDS[0])
    }
    reordered_row = deepcopy(payload)
    reordered_row["rows"][0] = {
        key: reordered_row["rows"][0][key]
        for key in (*ROW_FIELDS[1:], ROW_FIELDS[0])
    }

    for noncanonical in (reordered_report, reordered_config, reordered_row):
        with pytest.raises(ValueError, match="schema"):
            module.research_source_verification_bottleneck_report_payload(
                _resign_payload(noncanonical),
            )


@pytest.mark.parametrize("invalid_digest", [None, False, 0, (), []])
def test_direct_report_rejects_non_string_digest_sentinels(
    invalid_digest: object,
) -> None:
    report = _build_report(_input())

    with pytest.raises(ValueError, match="sha256"):
        replace(
            report,
            derived_validation_digest=invalid_digest,  # type: ignore[arg-type]
        )


def test_custom_config_is_committed_and_revalidated_from_public_payload() -> None:
    module = api()
    config = _config(
        min_pass_authority_coverage_ratio=d("0.800000"),
        min_watch_authority_coverage_ratio=d("0.600000"),
    )
    report = _build_report(
        _input(
            required_authority_reference_count=d("20"),
            covered_authority_reference_count=d("17"),
        ),
        config=config,
    )
    payload = module.research_source_verification_bottleneck_report_payload(report)

    assert report.status == "pass"
    assert payload["config"]["min_pass_authority_coverage_ratio"] == "0.800000"
    assert (
        module.research_source_verification_bottleneck_report_payload(payload)
        == payload
    )

    forged = deepcopy(payload)
    forged["config"]["min_pass_authority_coverage_ratio"] = "0.900000"
    forged["config"]["min_watch_authority_coverage_ratio"] = "0.700000"
    with pytest.raises(ValueError):
        module.research_source_verification_bottleneck_report_payload(
            _resign_payload(forged),
        )


def test_direct_report_revalidates_rows_against_embedded_config() -> None:
    report = _build_report(
        _input(
            required_authority_reference_count=d("20"),
            covered_authority_reference_count=d("17"),
        ),
    )
    permissive_config = _config(
        min_pass_authority_coverage_ratio=d("0.800000"),
        min_watch_authority_coverage_ratio=d("0.600000"),
    )

    with pytest.raises(ValueError, match="reason_codes must match row inputs"):
        replace(
            report,
            config=permissive_config,
            derived_validation_digest="",
        )


def test_decimal_arithmetic_and_sorting_ignore_ambient_context() -> None:
    higher_pressure = _input(
        "z_domain",
        "z_queue",
        "z_family",
        required_authority_reference_count=d("1000000"),
        covered_authority_reference_count=d("833333"),
    )
    lower_pressure = _input(
        "a_domain",
        "a_queue",
        "a_family",
        required_authority_reference_count=d("1000000"),
        covered_authority_reference_count=d("833334"),
    )
    large_count = d("123456789012345678901234567890")
    large_total_input = _input(
        missing_critical_field_count=large_count,
    )
    baseline = _build_report(higher_pressure, lower_pressure)
    baseline_total = _build_report(large_total_input, _input("other", "queue", "family"))

    with localcontext() as context:
        context.prec = 2
        constrained = _build_report(higher_pressure, lower_pressure)
        constrained_total = _build_report(
            large_total_input,
            _input("other", "queue", "family"),
        )

    assert constrained == baseline
    assert tuple(row.domain_label for row in constrained.rows) == (
        "z_domain",
        "a_domain",
    )
    assert baseline_total.total_missing_critical_field_count == large_count
    assert constrained_total == baseline_total


def test_sorting_uses_all_severity_metrics_before_complete_public_key_ties() -> None:
    severe = _input(
        "z_domain",
        "z_queue",
        "z_family",
        required_authority_reference_count=d("5"),
        covered_authority_reference_count=d("0"),
        freshness_lag_seconds=d("400000"),
        contradiction_signal_count=d("4"),
        reviewed_claim_count=d("8"),
        extraction_confidence_score=d("0.400000"),
        missing_critical_field_count=d("3"),
        available_reviewer_capacity_count=d("0"),
    )
    freshness_only = _input(
        "a_domain",
        "z_queue",
        "z_family",
        freshness_lag_seconds=d("400000"),
    )
    public_key_tie_b = _input(
        "m_domain",
        "b_queue",
        "z_family",
        freshness_lag_seconds=d("400000"),
    )
    public_key_tie_a = _input(
        "m_domain",
        "a_queue",
        "z_family",
        freshness_lag_seconds=d("400000"),
    )

    expected_order = (
        ("z_domain", "z_queue", "z_family"),
        ("a_domain", "z_queue", "z_family"),
        ("m_domain", "a_queue", "z_family"),
        ("m_domain", "b_queue", "z_family"),
    )
    first = _build_report(
        public_key_tie_b,
        freshness_only,
        severe,
        public_key_tie_a,
    )
    second = _build_report(
        severe,
        public_key_tie_a,
        public_key_tie_b,
        freshness_only,
    )

    assert tuple(
        (
            row.domain_label,
            row.verification_queue_label,
            row.evidence_family_label,
        )
        for row in first.rows
    ) == expected_order
    assert first == second


def test_all_eleven_sort_key_components_break_ties_in_order_and_ignore_input_order() -> None:
    module = api()
    severe = {
        "required_authority_reference_count": d("10"),
        "covered_authority_reference_count": d("0"),
        "freshness_lag_seconds": d("400000"),
        "contradiction_signal_count": d("5"),
        "reviewed_claim_count": d("10"),
        "extraction_confidence_score": d("0.400000"),
        "missing_critical_field_count": d("3"),
        "available_reviewer_capacity_count": d("0"),
    }
    cases = (
        (
            "status",
            _input("k01_block", "queue", "family", **severe),
            _input(
                "k01_watch",
                "queue",
                "family",
                required_authority_reference_count=d("10"),
                covered_authority_reference_count=d("8"),
            ),
        ),
        (
            "bottleneck_pressure_score",
            _input(
                "k02_high",
                "queue",
                "family",
                required_authority_reference_count=d("10"),
                covered_authority_reference_count=d("7"),
            ),
            _input(
                "k02_low",
                "queue",
                "family",
                required_authority_reference_count=d("10"),
                covered_authority_reference_count=d("8"),
            ),
        ),
        (
            "authority_coverage_ratio",
            _input("k03_low", "queue", "family", **severe),
            _input(
                "k03_high",
                "queue",
                "family",
                **{**severe, "covered_authority_reference_count": d("1")},
            ),
        ),
        (
            "freshness_lag_seconds",
            _input(
                "k04_high",
                "queue",
                "family",
                **{**severe, "freshness_lag_seconds": d("500000")},
            ),
            _input("k04_low", "queue", "family", **severe),
        ),
        (
            "contradiction_pressure_ratio",
            _input("k05_high", "queue", "family", **severe),
            _input(
                "k05_low",
                "queue",
                "family",
                **{**severe, "contradiction_signal_count": d("4")},
            ),
        ),
        (
            "extraction_confidence_score",
            _input(
                "k06_low",
                "queue",
                "family",
                **{**severe, "extraction_confidence_score": d("0.300000")},
            ),
            _input("k06_high", "queue", "family", **severe),
        ),
        (
            "missing_critical_field_count",
            _input(
                "k07_high",
                "queue",
                "family",
                **{**severe, "missing_critical_field_count": d("4")},
            ),
            _input("k07_low", "queue", "family", **severe),
        ),
        (
            "available_reviewer_capacity_count",
            _input("k08_low", "queue", "family", **severe),
            _input(
                "k08_high",
                "queue",
                "family",
                **{**severe, "available_reviewer_capacity_count": d("1")},
            ),
        ),
        (
            "domain_label",
            _input("a_k09", "queue", "family", **severe),
            _input("z_k09", "queue", "family", **severe),
        ),
        (
            "verification_queue_label",
            _input("k10", "a_queue", "family", **severe),
            _input("k10", "z_queue", "family", **severe),
        ),
        (
            "evidence_family_label",
            _input("k11", "queue", "a_family", **severe),
            _input("k11", "queue", "z_family", **severe),
        ),
    )

    for component_name, expected_first, expected_second in cases:
        forward = _build_report(expected_second, expected_first)
        reverse = _build_report(expected_first, expected_second)
        expected_order = (
            _row_identity(expected_first),
            _row_identity(expected_second),
        )
        assert tuple(map(_row_identity, forward.rows)) == expected_order, component_name
        assert forward == reverse, component_name
        assert len(module._row_sort_key(forward.rows[0])) == 11
        assert module._row_sort_key(forward.rows[0]) < module._row_sort_key(
            forward.rows[1],
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "pass_limit",
        "watch_limit",
        "quantum",
        "high_is_bad",
        "watch_reason",
        "block_reason",
    ),
    (
        (
            "authority_coverage_ratio",
            d("0.900000"),
            d("0.700000"),
            d("0.000001"),
            False,
            "research_source_verification_authority_coverage_watch",
            "research_source_verification_authority_coverage_block",
        ),
        (
            "freshness_lag_seconds",
            d("86400.000000"),
            d("259200.000000"),
            d("1.000000"),
            True,
            "research_source_verification_freshness_lag_watch",
            "research_source_verification_freshness_lag_block",
        ),
        (
            "contradiction_pressure_ratio",
            d("0.000000"),
            d("0.250000"),
            d("0.000001"),
            True,
            "research_source_verification_contradiction_pressure_watch",
            "research_source_verification_contradiction_pressure_block",
        ),
        (
            "extraction_confidence_score",
            d("0.900000"),
            d("0.700000"),
            d("0.000001"),
            False,
            "research_source_verification_extraction_confidence_watch",
            "research_source_verification_extraction_confidence_block",
        ),
        (
            "missing_critical_field_count",
            d("0.000000"),
            d("2.000000"),
            d("1.000000"),
            True,
            "research_source_verification_missing_critical_fields_watch",
            "research_source_verification_missing_critical_fields_block",
        ),
        (
            "available_reviewer_capacity_count",
            d("2.000000"),
            d("1.000000"),
            d("1.000000"),
            False,
            "research_source_verification_reviewer_capacity_watch",
            "research_source_verification_reviewer_capacity_block",
        ),
    ),
)
def test_metric_pass_and_watch_endpoints_with_one_legal_quantum(
    field_name: str,
    pass_limit: Decimal,
    watch_limit: Decimal,
    quantum: Decimal,
    high_is_bad: bool,
    watch_reason: str,
    block_reason: str,
) -> None:
    pass_row = _build_report(_input_at_metric_value(field_name, pass_limit)).rows[0]
    watch_side_value = pass_limit + quantum if high_is_bad else pass_limit - quantum
    watch_side_row = _build_report(
        _input_at_metric_value(field_name, watch_side_value),
    ).rows[0]
    watch_endpoint_row = _build_report(
        _input_at_metric_value(field_name, watch_limit),
    ).rows[0]
    block_side_value = watch_limit + quantum if high_is_bad else watch_limit - quantum
    block_side_row = _build_report(
        _input_at_metric_value(field_name, block_side_value),
    ).rows[0]

    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("research_source_verification_clear",)
    assert watch_side_row.status == "watch"
    assert watch_reason in watch_side_row.reason_codes
    assert watch_endpoint_row.status == "watch"
    assert watch_reason in watch_endpoint_row.reason_codes
    assert block_side_row.status == "block"
    assert block_reason in block_side_row.reason_codes


@pytest.mark.parametrize(
    ("field_name", "threshold", "quantum"),
    (
        ("freshness_lag_seconds", d("86400.000000"), d("1.000000")),
        ("contradiction_pressure_ratio", d("0.250000"), d("0.000001")),
        ("missing_critical_field_count", d("2.000000"), d("1.000000")),
    ),
)
def test_high_is_bad_equal_pass_watch_threshold_has_no_watch_interval(
    field_name: str,
    threshold: Decimal,
    quantum: Decimal,
) -> None:
    config_overrides = {
        "freshness_lag_seconds": {
            "max_pass_freshness_lag_seconds": threshold,
            "max_watch_freshness_lag_seconds": threshold,
        },
        "contradiction_pressure_ratio": {
            "max_pass_contradiction_pressure_ratio": threshold,
            "max_watch_contradiction_pressure_ratio": threshold,
        },
        "missing_critical_field_count": {
            "max_pass_missing_critical_field_count": threshold,
            "max_watch_missing_critical_field_count": threshold,
        },
    }[field_name]
    config = _config(**config_overrides)

    endpoint = _build_report(
        _input_at_metric_value(field_name, threshold),
        config=config,
    ).rows[0]
    above_endpoint = _build_report(
        _input_at_metric_value(field_name, threshold + quantum),
        config=config,
    ).rows[0]

    assert endpoint.status == "pass"
    assert above_endpoint.status == "block"


@pytest.mark.parametrize(
    ("field_name", "threshold", "quantum"),
    (
        ("authority_coverage_ratio", d("0.700000"), d("0.000001")),
        ("extraction_confidence_score", d("0.700000"), d("0.000001")),
        ("available_reviewer_capacity_count", d("1.000000"), d("1.000000")),
    ),
)
def test_low_is_bad_equal_pass_watch_threshold_has_no_watch_interval(
    field_name: str,
    threshold: Decimal,
    quantum: Decimal,
) -> None:
    config_overrides = {
        "authority_coverage_ratio": {
            "min_pass_authority_coverage_ratio": threshold,
            "min_watch_authority_coverage_ratio": threshold,
        },
        "extraction_confidence_score": {
            "min_pass_extraction_confidence_score": threshold,
            "min_watch_extraction_confidence_score": threshold,
        },
        "available_reviewer_capacity_count": {
            "min_pass_available_reviewer_capacity_count": threshold,
            "min_watch_available_reviewer_capacity_count": threshold,
        },
    }[field_name]
    config = _config(**config_overrides)

    endpoint = _build_report(
        _input_at_metric_value(field_name, threshold),
        config=config,
    ).rows[0]
    below_endpoint = _build_report(
        _input_at_metric_value(field_name, threshold - quantum),
        config=config,
    ).rows[0]

    assert endpoint.status == "pass"
    assert below_endpoint.status == "block"
    assert below_endpoint.bottleneck_pressure_score == d("1.000000")


def test_hostile_decimal_context_does_not_change_input_or_payload_results() -> None:
    module = api()
    baseline_input = _input(
        required_authority_reference_count=d("1000000"),
        covered_authority_reference_count=d("833333"),
        freshness_lag_seconds=d("90000"),
        contradiction_signal_count=d("1"),
        reviewed_claim_count=d("3"),
        extraction_confidence_score=d("0.812345"),
        missing_critical_field_count=d("1"),
        available_reviewer_capacity_count=d("1"),
    )
    baseline_report = _build_report(baseline_input)
    baseline_payload = module.research_source_verification_bottleneck_report_payload(
        baseline_report,
    )

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_UP
        for signal in context.traps:
            context.traps[signal] = True
        hostile_input = _input(
            required_authority_reference_count=Decimal("1000000"),
            covered_authority_reference_count=Decimal("833333"),
            freshness_lag_seconds=Decimal("90000"),
            contradiction_signal_count=Decimal("1"),
            reviewed_claim_count=Decimal("3"),
            extraction_confidence_score=Decimal("0.812345"),
            missing_critical_field_count=Decimal("1"),
            available_reviewer_capacity_count=Decimal("1"),
        )
        hostile_report = _build_report(hostile_input)
        reparsed_payload = module.research_source_verification_bottleneck_report_payload(
            deepcopy(baseline_payload),
        )

    assert hostile_input == baseline_input
    assert hostile_report == baseline_report
    assert reparsed_payload == baseline_payload


def test_raw_decimal_bounds_and_signed_zero_are_rejected_before_quantization() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        _input(extraction_confidence_score=d("1.0000004"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        _input(extraction_confidence_score=d("-0.0000004"))
    with pytest.raises(ValueError, match="nonnegative"):
        _input(missing_critical_field_count=d("-0.0000004"))
    with pytest.raises(ValueError, match="integral"):
        _input(missing_critical_field_count=d("1.0000004"))
    with pytest.raises(ValueError, match="signed zero"):
        _input(
            required_authority_reference_count=d("-0"),
            covered_authority_reference_count=d("-0"),
        )
    with pytest.raises(ValueError, match="signed zero"):
        _input(extraction_confidence_score=d("-0.000000"))
    with pytest.raises(ValueError, match="signed zero"):
        _config(min_pass_authority_coverage_ratio=d("-0"))
    with pytest.raises(ValueError, match="canonical Decimal precision"):
        _input(missing_critical_field_count=d("9" * 59))


@pytest.mark.parametrize(
    "invalid_decimal",
    ["-0.000000", "NaN", "Infinity", "-Infinity"],
)
def test_public_payload_rejects_signed_zero_and_non_finite_decimals(
    invalid_decimal: str,
) -> None:
    module = api()
    payload = module.research_source_verification_bottleneck_report_payload(
        _build_report(_input()),
    )
    payload["average_authority_coverage_ratio"] = invalid_decimal

    with pytest.raises(ValueError):
        module.research_source_verification_bottleneck_report_payload(
            _resign_payload(payload),
        )


def test_signed_zero_nonfinite_snan_and_decimal_subclasses_are_rejected() -> None:
    module = api()

    class DecimalSubclass(Decimal):
        pass

    direct_cases = (
        (Decimal("-0"), "signed zero"),
        (Decimal("NaN"), "finite"),
        (Decimal("sNaN"), "finite"),
        (Decimal("Infinity"), "finite"),
        (Decimal("-Infinity"), "finite"),
        (DecimalSubclass("0.500000"), "must be a Decimal"),
    )
    for invalid_decimal, expected_error in direct_cases:
        with pytest.raises(ValueError, match=expected_error):
            _input(extraction_confidence_score=invalid_decimal)
        with pytest.raises(ValueError, match=expected_error):
            _config(min_pass_authority_coverage_ratio=invalid_decimal)

    payload = module.research_source_verification_bottleneck_report_payload(
        _build_report(_input()),
    )
    for invalid_decimal in (
        "-0.000000",
        "NaN",
        "sNaN",
        "Infinity",
        "-Infinity",
    ):
        forged = deepcopy(payload)
        forged["average_authority_coverage_ratio"] = invalid_decimal
        with pytest.raises(ValueError):
            module.research_source_verification_bottleneck_report_payload(
                _resign_payload(forged),
            )

    forged_subclass = deepcopy(payload)
    forged_subclass["average_authority_coverage_ratio"] = DecimalSubclass("1")
    with pytest.raises(ValueError, match="public schema"):
        module.research_source_verification_bottleneck_report_payload(
            forged_subclass,
        )


def test_public_payload_rejects_noncanonical_decimal_utc_bool_container_and_reasons() -> None:
    module = api()
    payload = module.research_source_verification_bottleneck_report_payload(
        _build_report(
            _input(
                required_authority_reference_count=d("4"),
                covered_authority_reference_count=d("3"),
                freshness_lag_seconds=d("90000"),
                contradiction_signal_count=d("1"),
                reviewed_claim_count=d("10"),
                extraction_confidence_score=d("0.800000"),
                missing_critical_field_count=d("1"),
                available_reviewer_capacity_count=d("1"),
            ),
        ),
    )

    schema_cases: list[dict[str, Any]] = []

    report_decimal = deepcopy(payload)
    report_decimal["input_count"] = "1"
    schema_cases.append(report_decimal)

    config_decimal = deepcopy(payload)
    config_decimal["config"]["min_pass_authority_coverage_ratio"] = "0.9"
    schema_cases.append(config_decimal)

    row_decimal = deepcopy(payload)
    row_decimal["rows"][0]["bottleneck_rank"] = "1.0"
    schema_cases.append(row_decimal)

    report_utc = deepcopy(payload)
    report_utc["generated_at"] = "2026-07-08T10:30:00-04:00"
    schema_cases.append(report_utc)

    row_utc = deepcopy(payload)
    row_utc["rows"][0]["observed_at"] = "2026-07-08T14:30:00Z"
    schema_cases.append(row_utc)

    tuple_rows = deepcopy(payload)
    tuple_rows["rows"] = tuple(tuple_rows["rows"])
    schema_cases.append(tuple_rows)

    tuple_report_reasons = deepcopy(payload)
    tuple_report_reasons["reason_codes"] = tuple(
        tuple_report_reasons["reason_codes"],
    )
    schema_cases.append(tuple_report_reasons)

    tuple_row_reasons = deepcopy(payload)
    tuple_row_reasons["rows"][0]["reason_codes"] = tuple(
        tuple_row_reasons["rows"][0]["reason_codes"],
    )
    schema_cases.append(tuple_row_reasons)

    reversed_reasons = deepcopy(payload)
    reversed_reasons["rows"][0]["reason_codes"].reverse()
    schema_cases.append(reversed_reasons)

    duplicate_reasons = deepcopy(payload)
    duplicate_reasons["rows"][0]["reason_codes"].append(
        duplicate_reasons["rows"][0]["reason_codes"][0],
    )
    schema_cases.append(duplicate_reasons)

    for noncanonical in schema_cases:
        with pytest.raises(ValueError):
            module.research_source_verification_bottleneck_report_payload(
                _resign_payload(noncanonical),
            )

    bool_cases: list[dict[str, Any]] = []
    report_bool = deepcopy(payload)
    report_bool["paper_only"] = 1
    bool_cases.append(report_bool)
    config_bool = deepcopy(payload)
    config_bool["config"]["report_only"] = 1
    bool_cases.append(config_bool)
    row_bool = deepcopy(payload)
    row_bool["rows"][0]["readonly"] = 1
    bool_cases.append(row_bool)
    for noncanonical in bool_cases:
        with pytest.raises(ValueError, match="must be True"):
            module.research_source_verification_bottleneck_report_payload(
                _resign_payload(noncanonical),
            )

    class DictSubclass(dict):
        pass

    class ListSubclass(list):
        pass

    with pytest.raises(ValueError, match="report must be"):
        module.research_source_verification_bottleneck_report_payload(
            DictSubclass(payload),
        )
    list_subclass = deepcopy(payload)
    list_subclass["rows"] = ListSubclass(list_subclass["rows"])
    with pytest.raises(ValueError, match="public schema"):
        module.research_source_verification_bottleneck_report_payload(
            _resign_payload(list_subclass),
        )


def test_public_dataclasses_are_exact_final_and_frozen() -> None:
    module = api()
    config = _config()
    input_row = _input()
    report = _build_report(input_row)
    row = report.rows[0]

    assert tuple(field.name for field in fields(config)) == CONFIG_FIELDS
    assert tuple(field.name for field in fields(input_row)) == INPUT_FIELDS
    assert tuple(field.name for field in fields(row)) == ROW_FIELDS
    assert tuple(field.name for field in fields(report)) == REPORT_FIELDS

    for value, field_name in (
        (config, "readonly"),
        (input_row, "domain_label"),
        (row, "status"),
        (report, "status"),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(value, field_name, getattr(value, field_name))

    for public_type in (
        module.ResearchSourceVerificationBottleneckConfig,
        module.ResearchSourceVerificationBottleneckInput,
        module.ResearchSourceVerificationBottleneckRow,
        module.ResearchSourceVerificationBottleneckReport,
    ):
        with pytest.raises(TypeError):
            type("ForbiddenSubclass", (public_type,), {})


def test_public_contract_rejects_sensitive_surfaces_and_duplicates() -> None:
    module = api()
    unsafe_values = (
        "candidate_123",
        "market_id",
        "market_slug",
        "question",
        "https://example.invalid",
        "source_url",
        "source_text",
        "postgres_dsn",
        "raw_table_name",
        "wallet_token",
        "open_order",
        "live_trade",
        "private_source_alpha",
        "confidential_source",
        "anonymous_source",
        "whistleblower_jane",
        "source_identity_alice",
    )

    for unsafe_value in unsafe_values:
        with pytest.raises(ValueError):
            _input(domain_label=unsafe_value)

    with pytest.raises(ValueError, match="duplicate"):
        _build_report(_input(), _input())
    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_verification_bottleneck_report_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
                "candidate_id": "abc",
            },
        )

    payload = module.research_source_verification_bottleneck_report_payload(
        _build_report(_input()),
    )
    assert _unsafe_public_paths(payload) == ()


def test_public_label_privacy_filter_uses_tokens_not_substring_fragments() -> None:
    for accepted_label in (
        "border_policy",
        "stable_signal",
        "delivery_queue",
    ):
        assert _input(domain_label=accepted_label).domain_label == accepted_label

    for sensitive_label in (
        "api_key",
        "service_secret",
        "user_password",
        "database_credential",
        "reviewer_email",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            _input(domain_label=sensitive_label)


def test_object_payload_path_canonically_rebuilds_all_nested_public_values() -> None:
    module = api()

    empty_report = _build_report()
    empty_payload = module.research_source_verification_bottleneck_report_payload(
        empty_report,
    )
    object.__setattr__(empty_report.config, "paper_only", False)
    forged_empty_payload = deepcopy(empty_payload)
    forged_empty_payload["config"]["paper_only"] = False
    object.__setattr__(
        empty_report,
        "derived_validation_digest",
        _resign_payload(forged_empty_payload)["derived_validation_digest"],
    )
    with pytest.raises(ValueError, match="paper_only"):
        module.research_source_verification_bottleneck_report_payload(empty_report)

    row_flag_report = _build_report(_input())
    row_flag_payload = module.research_source_verification_bottleneck_report_payload(
        row_flag_report,
    )
    object.__setattr__(row_flag_report.rows[0], "readonly", False)
    forged_row_flag_payload = deepcopy(row_flag_payload)
    forged_row_flag_payload["rows"][0]["readonly"] = False
    object.__setattr__(
        row_flag_report,
        "derived_validation_digest",
        _resign_payload(forged_row_flag_payload)["derived_validation_digest"],
    )
    with pytest.raises(ValueError, match="readonly"):
        module.research_source_verification_bottleneck_report_payload(row_flag_report)

    report_count = _build_report(_input())
    report_count_payload = module.research_source_verification_bottleneck_report_payload(
        report_count,
    )
    object.__setattr__(report_count, "input_count", 1)
    forged_report_count_payload = deepcopy(report_count_payload)
    forged_report_count_payload["input_count"] = 1
    object.__setattr__(
        report_count,
        "derived_validation_digest",
        _resign_payload(forged_report_count_payload)["derived_validation_digest"],
    )
    with pytest.raises(ValueError, match="public schema"):
        module.research_source_verification_bottleneck_report_payload(report_count)

    config_count = _build_report(_input())
    config_count_payload = module.research_source_verification_bottleneck_report_payload(
        config_count,
    )
    object.__setattr__(
        config_count.config,
        "max_pass_freshness_lag_seconds",
        86400,
    )
    forged_config_count_payload = deepcopy(config_count_payload)
    forged_config_count_payload["config"]["max_pass_freshness_lag_seconds"] = 86400
    object.__setattr__(
        config_count,
        "derived_validation_digest",
        _resign_payload(forged_config_count_payload)["derived_validation_digest"],
    )
    with pytest.raises(ValueError, match="public schema"):
        module.research_source_verification_bottleneck_report_payload(config_count)

    row_count = _build_report(_input())
    row_count_payload = module.research_source_verification_bottleneck_report_payload(
        row_count,
    )
    object.__setattr__(
        row_count.rows[0],
        "required_authority_reference_count",
        5,
    )
    forged_row_count_payload = deepcopy(row_count_payload)
    forged_row_count_payload["rows"][0]["required_authority_reference_count"] = 5
    object.__setattr__(
        row_count,
        "derived_validation_digest",
        _resign_payload(forged_row_count_payload)["derived_validation_digest"],
    )
    with pytest.raises(ValueError, match="public schema"):
        module.research_source_verification_bottleneck_report_payload(row_count)


def _resolved_ast_name(node: ast.AST, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        parent = _resolved_ast_name(node.value, aliases)
        if parent is not None:
            return f"{parent}.{node.attr}"
    return None


def _ast_io_violations(source: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    banned_import_roots = {
        "aiohttp",
        "bs4",
        "boto3",
        "ftplib",
        "http",
        "httpx",
        "os",
        "paramiko",
        "pathlib",
        "psycopg",
        "requests",
        "scrapy",
        "selenium",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
    }
    pathlib_methods = {
        "open",
        "read_bytes",
        "read_text",
        "write_bytes",
        "write_text",
    }
    aliases: dict[str, str] = {
        "__import__": "__import__",
    }
    path_values: set[str] = set()
    violations: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local_name = alias.asname or alias.name.split(".", 1)[0]
                aliases[local_name] = alias.name
                root = alias.name.split(".", 1)[0]
                if root in banned_import_roots:
                    violations.add(f"import:{root}")
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            root = node.module.split(".", 1)[0]
            if root in banned_import_roots:
                violations.add(f"import:{root}")
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
        value = node.value
        if value is None:
            continue
        resolved = _resolved_ast_name(value, aliases)
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            if resolved is not None:
                aliases[target.id] = resolved
            if isinstance(value, ast.Call):
                constructor = _resolved_ast_name(value.func, aliases)
                if constructor == "pathlib.Path":
                    path_values.add(target.id)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            resolved = _resolved_ast_name(node.func, aliases)
            if resolved in {
                "__import__",
                "builtins.__import__",
                "importlib.import_module",
            }:
                if node.args and isinstance(node.args[0], ast.Constant):
                    target = node.args[0].value
                    if type(target) is str:
                        root = target.split(".", 1)[0]
                        if root in banned_import_roots:
                            violations.add(f"dynamic-import:{root}")
            if resolved is not None:
                root = resolved.split(".", 1)[0]
                if root in banned_import_roots:
                    violations.add(f"call:{resolved}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in pathlib_methods:
                receiver = node.func.value
                if isinstance(receiver, ast.Name) and receiver.id in path_values:
                    violations.add(f"pathlib:{node.func.attr}")
                elif isinstance(receiver, ast.Call):
                    constructor = _resolved_ast_name(receiver.func, aliases)
                    if constructor == "pathlib.Path":
                        violations.add(f"pathlib:{node.func.attr}")
        elif isinstance(node, ast.Attribute):
            resolved = _resolved_ast_name(node, aliases)
            if resolved == "os.environ":
                violations.add("access:os.environ")
        elif isinstance(node, ast.Subscript):
            resolved = _resolved_ast_name(node.value, aliases)
            if resolved == "os.environ":
                violations.add("access:os.environ")

    return tuple(sorted(violations))


def test_module_is_pure_report_only_without_io_db_network_or_scraping_calls() -> None:
    module = api()
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_VERIFICATION_BOTTLENECK_REPORT_CONFIG_VERSION",
        "ResearchSourceVerificationBottleneckConfig",
        "ResearchSourceVerificationBottleneckInput",
        "ResearchSourceVerificationBottleneckReport",
        "ResearchSourceVerificationBottleneckRow",
        "build_research_source_verification_bottleneck_report",
        "research_source_verification_bottleneck_report_digest",
        "research_source_verification_bottleneck_report_payload",
    )
    assert _ast_io_violations(source) == ()


@pytest.mark.parametrize(
    ("source", "expected_violation"),
    (
        (
            "import importlib as il\nload = il.import_module\nload('socket')\n",
            "dynamic-import:socket",
        ),
        (
            "load = __import__\nload('http.client')\n",
            "dynamic-import:http",
        ),
        (
            "from pathlib import Path as P\np = P('x')\np.read_text()\n",
            "pathlib:read_text",
        ),
        (
            "from pathlib import Path as P\nP('x').write_bytes(b'x')\n",
            "pathlib:write_bytes",
        ),
        (
            "from subprocess import run as invoke\ninvoke(['true'])\n",
            "call:subprocess.run",
        ),
        (
            "import socket as network\nnetwork.create_connection(('x', 80))\n",
            "call:socket.create_connection",
        ),
        (
            "import http.client as hc\nhc.HTTPConnection('x')\n",
            "call:http.client.HTTPConnection",
        ),
        (
            "import os as operating_system\noperating_system.system('true')\n",
            "call:os.system",
        ),
        (
            "from os import environ as env\nvalue = env['TOKEN']\n",
            "access:os.environ",
        ),
    ),
)
def test_no_io_ast_guard_detects_dynamic_alias_and_io_surfaces(
    source: str,
    expected_violation: str,
) -> None:
    assert expected_violation in _ast_io_violations(source)


def _float_paths(value: Any, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _unsafe_public_paths(value: Any, path: str = "$") -> tuple[str, ...]:
    fragments = (
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "url",
        "://",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    paths: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in fragments):
                paths.append(f"{path}.{key}")
            paths.extend(_unsafe_public_paths(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_unsafe_public_paths(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in fragments):
            paths.append(path)
    return tuple(paths)
