from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, Decimal, localcontext
from types import MappingProxyType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_resolution_authority_gap_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_payload_digest(payload: dict[str, object]) -> str:
    canonical_payload = dict(payload)
    canonical_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_authority_coverage_ratio": d("0.800000"),
        "block_authority_coverage_ratio": d("0.500000"),
        "freshness_watch_age_seconds": d("3600.000000"),
        "freshness_block_age_seconds": d("7200.000000"),
        "min_independence_score": d("0.700000"),
        "block_independence_score": d("0.500000"),
        "contradiction_watch_severity": d("0.300000"),
        "contradiction_block_severity": d("0.600000"),
        "min_rule_mapping_score": d("0.800000"),
        "block_rule_mapping_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchSourceResolutionAuthorityGapConfig(**values)


def evidence(
    criteria_group: str,
    source_family: str,
    *,
    observed_seconds_ago: int = 1200,
    authority_coverage_ratio: Decimal = d("0.900000"),
    independence_score: Decimal = d("0.850000"),
    contradiction_severity: Decimal = d("0.100000"),
    rule_mapping_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceResolutionAuthorityGapInput(
        criteria_group=criteria_group,
        source_family=source_family,
        evidence_observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        authority_coverage_ratio=authority_coverage_ratio,
        independence_score=independence_score,
        contradiction_severity=contradiction_severity,
        rule_mapping_score=rule_mapping_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_resolution_authority_gap_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_authority_gap_report_blocks_material_resolution_criteria_gaps() -> None:
    report = build_report(
        evidence(
            "settlement.criteria",
            "official.agency",
            observed_seconds_ago=10800,
            authority_coverage_ratio=d("0.400000"),
            independence_score=d("0.400000"),
            contradiction_severity=d("0.800000"),
            rule_mapping_score=d("0.300000"),
        ),
        evidence(
            "settlement.criteria",
            "independent.archive",
            observed_seconds_ago=9000,
            authority_coverage_ratio=d("0.600000"),
            independence_score=d("0.600000"),
            contradiction_severity=d("0.500000"),
            rule_mapping_score=d("0.600000"),
        ),
        evidence("verification.criteria", "official.feed"),
    )

    assert report.status == "block"
    assert report.criteria_group_count == d("2.000000")
    assert report.evidence_count == d("3.000000")
    assert report.pass_criteria_group_count == d("1.000000")
    assert report.watch_criteria_group_count == d("0.000000")
    assert report.block_criteria_group_count == d("1.000000")
    assert report.low_authority_coverage_count == d("1.000000")
    assert report.stale_evidence_count == d("1.000000")
    assert report.low_independence_count == d("1.000000")
    assert report.contradiction_severity_count == d("1.000000")
    assert report.weak_rule_mapping_count == d("1.000000")
    assert report.highest_authority_gap_score == d("0.645000")
    assert report.oldest_latest_evidence_age_seconds == d("9000.000000")
    assert report.reason_codes == (
        "low_authority_coverage_block",
        "stale_evidence_block",
        "low_independence_block",
        "contradiction_severity_block",
        "weak_rule_mapping_block",
    )

    assert tuple(row.criteria_group for row in report.rows) == (
        "settlement.criteria",
        "verification.criteria",
    )

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.source_family_count == d("2.000000")
    assert blocked.latest_evidence_age_seconds == d("9000.000000")
    assert blocked.average_authority_coverage_ratio == d("0.500000")
    assert blocked.average_independence_score == d("0.500000")
    assert blocked.contradiction_severity == d("0.800000")
    assert blocked.average_rule_mapping_score == d("0.450000")
    assert blocked.authority_gap_score == d("0.645000")
    assert blocked.reason_codes == report.reason_codes

    passed = report.rows[1]
    assert passed.status == "pass"
    assert passed.reason_codes == ("resolution_authority_gap_clear",)
    assert passed.authority_gap_score == d("0.055833")
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True


def test_watch_thresholds_are_reported_without_blocking() -> None:
    report = build_report(
        evidence(
            "weather.criteria",
            "official.bulletin",
            observed_seconds_ago=5400,
            authority_coverage_ratio=d("0.650000"),
            independence_score=d("0.650000"),
            contradiction_severity=d("0.350000"),
            rule_mapping_score=d("0.700000"),
        ),
    )

    assert report.status == "watch"
    assert report.watch_criteria_group_count == d("1.000000")
    assert report.block_criteria_group_count == d("0.000000")
    assert report.reason_codes == (
        "low_authority_coverage_watch",
        "stale_evidence_watch",
        "low_independence_watch",
        "contradiction_severity_watch",
        "weak_rule_mapping_watch",
    )
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == report.reason_codes


def test_payload_digest_is_deterministic_decimal_string_only_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        evidence("verification.criteria", "official.feed"),
        evidence(
            "settlement.criteria",
            "official.agency",
            observed_seconds_ago=10800,
            authority_coverage_ratio=d("0.400000"),
            independence_score=d("0.400000"),
            contradiction_severity=d("0.800000"),
            rule_mapping_score=d("0.300000"),
        ),
    )
    report_b = build_report(
        evidence(
            "settlement.criteria",
            "official.agency",
            observed_seconds_ago=10800,
            authority_coverage_ratio=d("0.400000"),
            independence_score=d("0.400000"),
            contradiction_severity=d("0.800000"),
            rule_mapping_score=d("0.300000"),
        ),
        evidence("verification.criteria", "official.feed"),
    )

    payload_a = module.research_source_resolution_authority_gap_report_payload(report_a)
    payload_b = module.research_source_resolution_authority_gap_report_payload(report_b)
    digest_a = module.research_source_resolution_authority_gap_report_digest(report_a)
    digest_b = module.research_source_resolution_authority_gap_report_digest(report_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert digest_a == canonical_payload_digest(payload_a)
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["criteria_group_count"] == "2.000000"
    assert payload_a["rows"][0]["authority_gap_score"] >= payload_a["rows"][1][
        "authority_gap_score"
    ]
    assert len(digest_a) == 64
    int(digest_a, 16)
    json.dumps(payload_a, sort_keys=True)
    assert_no_float_values(payload_a)

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_id",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
    }
    keys = {field.name for cls in (type(report_a), type(report_a.rows[0])) for field in fields(cls)}
    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload_a)
    module.validate_research_source_resolution_authority_gap_report_digest(report_a)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_payload_rejects_resigned_invalid_status_and_non_decimal_numeric() -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.agency"))

    object.__setattr__(report, "status", "ready")
    object.__setattr__(
        report,
        "derived_validation_digest",
        canonical_payload_digest(module.json_ready_no_floats(report)),
    )
    with pytest.raises(ValueError, match="status"):
        module.research_source_resolution_authority_gap_report_payload(report)

    report = build_report(evidence("settlement.criteria", "official.agency"))
    object.__setattr__(report.rows[0], "status", "ready")
    object.__setattr__(
        report,
        "derived_validation_digest",
        canonical_payload_digest(module.json_ready_no_floats(report)),
    )
    with pytest.raises(ValueError, match="status"):
        module.research_source_resolution_authority_gap_report_payload(report)

    report = build_report(evidence("settlement.criteria", "official.agency"))
    object.__setattr__(report, "criteria_group_count", 1)
    object.__setattr__(
        report,
        "derived_validation_digest",
        canonical_payload_digest(module.json_ready_no_floats(report)),
    )
    with pytest.raises(ValueError, match="criteria_group_count must be a Decimal"):
        module.research_source_resolution_authority_gap_report_payload(report)


def test_payload_rejects_resigned_row_reason_mutation_consistent_with_report() -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.agency"))
    row = report.rows[0]

    object.__setattr__(row, "status", "watch")
    object.__setattr__(row, "reason_codes", ("low_authority_coverage_watch",))
    object.__setattr__(report, "pass_criteria_group_count", d("0.000000"))
    object.__setattr__(report, "watch_criteria_group_count", d("1.000000"))
    object.__setattr__(report, "low_authority_coverage_count", d("1.000000"))
    object.__setattr__(report, "status", "watch")
    object.__setattr__(
        report,
        "reason_codes",
        ("low_authority_coverage_watch",),
    )
    object.__setattr__(
        report,
        "derived_validation_digest",
        canonical_payload_digest(module.json_ready_no_floats(report)),
    )

    with pytest.raises(
        ValueError,
        match="reason_codes must match row metrics and config",
    ):
        module.research_source_resolution_authority_gap_report_payload(report)


def test_payload_rejects_resigned_row_score_mutation_consistent_with_report() -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.agency"))

    object.__setattr__(report.rows[0], "authority_gap_score", d("0.500000"))
    object.__setattr__(report, "highest_authority_gap_score", d("0.500000"))
    object.__setattr__(
        report,
        "derived_validation_digest",
        canonical_payload_digest(module.json_ready_no_floats(report)),
    )

    with pytest.raises(
        ValueError,
        match="authority_gap_score must match row metrics and config",
    ):
        module.research_source_resolution_authority_gap_report_payload(report)


@pytest.mark.parametrize(
    ("field_name", "replacement", "message"),
    (
        ("criteria_group_count", "2.000000", "criteria_group_count must match rows"),
        ("evidence_count", "2.000000", "evidence_count must match rows"),
        (
            "pass_criteria_group_count",
            "0.000000",
            "pass_criteria_group_count must match rows",
        ),
        (
            "watch_criteria_group_count",
            "1.000000",
            "watch_criteria_group_count must match rows",
        ),
        (
            "block_criteria_group_count",
            "1.000000",
            "block_criteria_group_count must match rows",
        ),
        (
            "low_authority_coverage_count",
            "1.000000",
            "low_authority_coverage_count must match rows",
        ),
        (
            "stale_evidence_count",
            "1.000000",
            "stale_evidence_count must match rows",
        ),
        (
            "low_independence_count",
            "1.000000",
            "low_independence_count must match rows",
        ),
        (
            "contradiction_severity_count",
            "1.000000",
            "contradiction_severity_count must match rows",
        ),
        (
            "weak_rule_mapping_count",
            "1.000000",
            "weak_rule_mapping_count must match rows",
        ),
        ("status", "watch", "status must match rows"),
        (
            "reason_codes",
            ["low_authority_coverage_watch"],
            "reason_codes must match rows",
        ),
        (
            "highest_authority_gap_score",
            "0.999999",
            "highest_authority_gap_score must match rows",
        ),
        (
            "oldest_latest_evidence_age_seconds",
            "9999.000000",
            "oldest_latest_evidence_age_seconds must match rows",
        ),
    ),
)
def test_payload_digest_rejects_resigned_derived_report_field_mutations(
    field_name: str,
    replacement: object,
    message: str,
) -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.agency"))
    payload = module.research_source_resolution_authority_gap_report_payload(report)
    forged_payload = json.loads(json.dumps(payload))
    forged_payload[field_name] = replacement
    forged_payload["derived_validation_digest"] = canonical_payload_digest(forged_payload)

    with pytest.raises(ValueError, match=message):
        module.research_source_resolution_authority_gap_report_payload(forged_payload)


def test_payload_rejects_resigned_row_derivations_with_stale_report_aggregates() -> None:
    module = api()
    report = build_report(
        evidence("settlement.criteria", "official.agency"),
        evidence("verification.criteria", "official.feed"),
    )
    blocked_report = build_report(
        evidence(
            "settlement.criteria",
            "official.agency",
            authority_coverage_ratio=d("0.400000"),
        ),
    )
    payload = module.research_source_resolution_authority_gap_report_payload(report)
    blocked_payload = module.research_source_resolution_authority_gap_report_payload(
        blocked_report,
    )
    forged_payload = json.loads(json.dumps(payload))
    forged_payload["rows"][0] = blocked_payload["rows"][0]
    forged_payload["derived_validation_digest"] = canonical_payload_digest(forged_payload)

    with pytest.raises(
        ValueError,
        match="pass_criteria_group_count must match rows",
    ):
        module._payload_validation_digest(forged_payload)


def test_payload_rejects_resigned_row_rank_mutation() -> None:
    module = api()
    report = build_report(
        evidence(
            "settlement.criteria",
            "official.agency",
            authority_coverage_ratio=d("0.400000"),
        ),
        evidence("verification.criteria", "official.feed"),
    )
    payload = module.research_source_resolution_authority_gap_report_payload(report)
    forged_payload = json.loads(json.dumps(payload))
    forged_payload["rows"].reverse()
    forged_payload["derived_validation_digest"] = canonical_payload_digest(forged_payload)

    with pytest.raises(
        ValueError,
        match="rows must use deterministic authority gap sort",
    ):
        module._payload_validation_digest(forged_payload)


def test_payload_carries_exact_config_snapshot_for_semantic_revalidation() -> None:
    module = api()
    cfg = config(
        min_authority_coverage_ratio=d("0.950000"),
        freshness_block_age_seconds=d("9000.000000"),
    )
    report = build_report(
        evidence("settlement.criteria", "official.agency"),
        cfg=cfg,
    )
    payload = module.research_source_resolution_authority_gap_report_payload(report)

    assert set(payload["config"]) == {
        "config_version",
        "min_authority_coverage_ratio",
        "block_authority_coverage_ratio",
        "freshness_watch_age_seconds",
        "freshness_block_age_seconds",
        "min_independence_score",
        "block_independence_score",
        "contradiction_watch_severity",
        "contradiction_block_severity",
        "min_rule_mapping_score",
        "block_rule_mapping_score",
        "paper_only",
        "report_only",
        "readonly",
    }
    assert payload["config"]["min_authority_coverage_ratio"] == "0.950000"
    assert payload["config"]["freshness_block_age_seconds"] == "9000.000000"

    extra_config_field_payload = json.loads(json.dumps(payload))
    extra_config_field_payload["config"]["unexpected_field"] = "unexpected"
    with pytest.raises(ValueError, match="config.*public payload schema"):
        module._payload_validation_digest(extra_config_field_payload)

    missing_config_field_payload = json.loads(json.dumps(payload))
    missing_config_field_payload["config"].pop("readonly")
    with pytest.raises(ValueError, match="config.*public payload schema"):
        module._payload_validation_digest(missing_config_field_payload)


def test_report_uses_a_defensive_config_snapshot() -> None:
    module = api()
    cfg = config()
    report = build_report(
        evidence("settlement.criteria", "official.agency"),
        cfg=cfg,
    )

    assert report.config is not cfg
    object.__setattr__(
        cfg,
        "min_authority_coverage_ratio",
        d("0.950000"),
    )

    assert report.config.min_authority_coverage_ratio == d("0.800000")
    module.validate_research_source_resolution_authority_gap_report_digest(report)


def test_report_revalidates_bypassed_nested_row_and_config_snapshots() -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.agency"))
    object.__setattr__(report.rows[0], "average_evidence_age_seconds", 1200)

    with pytest.raises(
        ValueError,
        match="average_evidence_age_seconds must be a Decimal",
    ):
        replace(report, derived_validation_digest="")

    report = build_report(evidence("settlement.criteria", "official.agency"))
    object.__setattr__(
        report.config,
        "min_authority_coverage_ratio",
        d("NaN"),
    )

    with pytest.raises(
        ValueError,
        match="min_authority_coverage_ratio must be finite",
    ):
        replace(report, derived_validation_digest="")


def test_public_mapping_round_trip_rebuilds_exact_nested_dataclasses() -> None:
    module = api()
    report = build_report(
        evidence("settlement.criteria", "official.agency"),
        evidence("verification.criteria", "official.feed"),
    )
    payload = module.research_source_resolution_authority_gap_report_payload(report)
    public_mapping = MappingProxyType(json.loads(json.dumps(payload)))

    rebuilt = module._report_from_public_payload(public_mapping)

    assert type(rebuilt) is module.ResearchSourceResolutionAuthorityGapReport
    assert type(rebuilt.config) is module.ResearchSourceResolutionAuthorityGapConfig
    assert type(rebuilt.rows) is tuple
    assert all(
        type(row) is module.ResearchSourceResolutionAuthorityGapRow
        for row in rebuilt.rows
    )
    assert (
        module.research_source_resolution_authority_gap_report_payload(public_mapping)
        == payload
    )
    assert (
        module.research_source_resolution_authority_gap_report_digest(public_mapping)
        == payload["derived_validation_digest"]
    )
    module.validate_research_source_resolution_authority_gap_report_digest(
        public_mapping,
    )


@pytest.mark.parametrize(
    ("path", "field_name"),
    (
        ((), "status"),
        (("config",), "readonly"),
        (("rows", 0), "status"),
    ),
)
@pytest.mark.parametrize("mutation", ("missing", "extra"))
def test_public_mapping_reconstruction_rejects_missing_and_extra_fields(
    path: tuple[object, ...],
    field_name: str,
    mutation: str,
) -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.agency"))
    payload = module.research_source_resolution_authority_gap_report_payload(report)
    forged = json.loads(json.dumps(payload))
    target: Any = forged
    for part in path:
        target = target[part]
    if mutation == "missing":
        target.pop(field_name)
    else:
        target["unexpected_field"] = "unexpected"
    forged["derived_validation_digest"] = canonical_payload_digest(forged)

    with pytest.raises(ValueError, match="public payload schema"):
        module.research_source_resolution_authority_gap_report_payload(forged)


def test_payload_digest_rejects_noncanonical_public_schema() -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.agency"))
    payload = module.json_ready_no_floats(report)

    extra_field_payload = dict(payload)
    extra_field_payload["unexpected_field"] = "unexpected"
    with pytest.raises(ValueError, match="public payload schema"):
        module._payload_validation_digest(extra_field_payload)

    missing_field_payload = dict(payload)
    missing_field_payload.pop("status")
    with pytest.raises(ValueError, match="public payload schema"):
        module._payload_validation_digest(missing_field_payload)

    wrong_rows_container_payload = dict(payload)
    wrong_rows_container_payload["rows"] = tuple(payload["rows"])
    with pytest.raises(ValueError, match="rows must be a list"):
        module._payload_validation_digest(wrong_rows_container_payload)

    wrong_reason_container_payload = dict(payload)
    wrong_reason_container_payload["reason_codes"] = tuple(payload["reason_codes"])
    with pytest.raises(ValueError, match="reason_codes must be a list"):
        module._payload_validation_digest(wrong_reason_container_payload)


def test_row_counts_are_whole_and_source_families_cannot_exceed_evidence() -> None:
    report = build_report(evidence("settlement.criteria", "official.agency"))

    with pytest.raises(ValueError, match="evidence_count must be a whole Decimal"):
        replace(report.rows[0], evidence_count=d("1.500000"))
    with pytest.raises(
        ValueError,
        match="source_family_count must not exceed evidence_count",
    ):
        replace(report.rows[0], source_family_count=d("2.000000"))


@pytest.mark.parametrize(
    ("factory", "field_name"),
    (
        (config, "contradiction_watch_severity"),
        (
            lambda **overrides: evidence(
                "settlement.criteria",
                "official.agency",
                **overrides,
            ),
            "authority_coverage_ratio",
        ),
    ),
)
def test_signed_zero_decimal_inputs_are_rejected(
    factory: Any,
    field_name: str,
) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must not be signed zero"):
        factory(**{field_name: d("-0.000000")})


@pytest.mark.parametrize(
    "value",
    (
        d("NaN"),
        d("sNaN"),
        d("Infinity"),
        d("-Infinity"),
    ),
)
def test_non_finite_decimal_inputs_are_rejected(value: Decimal) -> None:
    with pytest.raises(
        ValueError,
        match="authority_coverage_ratio must be finite",
    ):
        evidence(
            "settlement.criteria",
            "official.agency",
            authority_coverage_ratio=value,
        )


def test_signed_zero_is_rejected_in_public_payloads() -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.agency"))
    payload = module.research_source_resolution_authority_gap_report_payload(report)
    forged_payload = json.loads(json.dumps(payload))
    forged_payload["rows"][0]["contradiction_severity"] = "-0.000000"
    forged_payload["derived_validation_digest"] = canonical_payload_digest(forged_payload)

    with pytest.raises(
        ValueError,
        match="contradiction_severity must not be signed zero",
    ):
        module._payload_validation_digest(forged_payload)


def test_raw_decimal_bounds_are_checked_before_quantization() -> None:
    with pytest.raises(
        ValueError,
        match="authority_coverage_ratio must be nonnegative",
    ):
        evidence(
            "settlement.criteria",
            "official.agency",
            authority_coverage_ratio=d("-0.0000001"),
        )

    with pytest.raises(
        ValueError,
        match="min_authority_coverage_ratio must be between zero and one",
    ):
        config(min_authority_coverage_ratio=d("1.0000001"))


def test_decimal_arithmetic_is_independent_of_ambient_context() -> None:
    inputs = (
        evidence(
            "settlement.criteria",
            "official.agency",
            observed_seconds_ago=10800,
            authority_coverage_ratio=d("0.400000"),
            independence_score=d("0.400000"),
            contradiction_severity=d("0.800000"),
            rule_mapping_score=d("0.300000"),
        ),
        evidence(
            "settlement.criteria",
            "independent.archive",
            observed_seconds_ago=9000,
            authority_coverage_ratio=d("0.600000"),
            independence_score=d("0.600000"),
            contradiction_severity=d("0.500000"),
            rule_mapping_score=d("0.600000"),
        ),
    )
    expected = build_report(*inputs)

    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        actual = build_report(*inputs)

    assert actual == expected
    assert actual.rows[0].authority_gap_score == d("0.645000")


def test_input_normalization_uses_a_complete_stable_tie_break() -> None:
    module = api()
    lower = evidence(
        "settlement.criteria",
        "official.agency",
        authority_coverage_ratio=d("0.700000"),
        independence_score=d("0.800000"),
        contradiction_severity=d("0.100000"),
        rule_mapping_score=d("0.900000"),
    )
    higher = evidence(
        "settlement.criteria",
        "official.agency",
        authority_coverage_ratio=d("0.900000"),
        independence_score=d("0.600000"),
        contradiction_severity=d("0.200000"),
        rule_mapping_score=d("0.800000"),
    )

    forward = module._normalize_inputs((higher, lower), generated_at=GENERATED_AT)
    reverse = module._normalize_inputs((lower, higher), generated_at=GENERATED_AT)

    assert forward == reverse
    assert tuple(row.authority_coverage_ratio for row in forward) == (
        d("0.700000"),
        d("0.900000"),
    )


def test_public_payload_sort_uses_criteria_group_as_complete_score_tie_break() -> None:
    module = api()
    report = build_report(
        evidence("alpha.criteria", "official.agency"),
        evidence("beta.criteria", "official.feed"),
    )
    assert report.rows[0].authority_gap_score == report.rows[1].authority_gap_score
    payload = module.research_source_resolution_authority_gap_report_payload(report)
    forged = json.loads(json.dumps(payload))
    forged["rows"].reverse()
    forged["derived_validation_digest"] = canonical_payload_digest(forged)

    with pytest.raises(
        ValueError,
        match="rows must use deterministic authority gap sort",
    ):
        module.research_source_resolution_authority_gap_report_payload(forged)


@pytest.mark.parametrize("nested_path", ((), ("config",), ("rows", 0)))
def test_payload_digest_rejects_noncanonical_field_order(
    nested_path: tuple[object, ...],
) -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.agency"))
    payload = module.research_source_resolution_authority_gap_report_payload(report)
    forged_payload = json.loads(json.dumps(payload))

    target: Any = forged_payload
    for part in nested_path:
        target = target[part]
    reordered = {key: target[key] for key in reversed(tuple(target))}
    if not nested_path:
        forged_payload = reordered
    elif nested_path == ("config",):
        forged_payload["config"] = reordered
    else:
        forged_payload["rows"][0] = reordered
    forged_payload["derived_validation_digest"] = canonical_payload_digest(forged_payload)

    with pytest.raises(ValueError, match="canonical field order"):
        module._payload_validation_digest(forged_payload)


def test_private_source_families_are_redacted_from_public_payloads() -> None:
    module = api()
    private_source_family = "confidential.internal"
    report = build_report(
        evidence("settlement.criteria", private_source_family),
    )
    payload = module.research_source_resolution_authority_gap_report_payload(report)

    assert private_source_family not in json.dumps(payload, sort_keys=True)
    assert set(payload["rows"][0]) == set(module.ROW_PUBLIC_PAYLOAD_FIELDS)


def test_contradiction_thresholds_require_a_nonempty_watch_band() -> None:
    with pytest.raises(
        ValueError,
        match="contradiction_watch_severity must be below contradiction_block_severity",
    ):
        config(
            contradiction_watch_severity=d("0.600000"),
            contradiction_block_severity=d("0.600000"),
        )


def test_validation_flags_statuses_decimal_only_and_safe_scope() -> None:
    module = api()

    with pytest.raises(ValueError, match="min_authority_coverage_ratio must be a Decimal"):
        config(min_authority_coverage_ratio=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="authority_coverage_ratio must be a Decimal"):
        evidence("settlement.criteria", "official.agency", authority_coverage_ratio=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_severity must be a Decimal"):
        evidence("settlement.criteria", "official.agency", contradiction_severity=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="criteria_group contains unsafe text"):
        evidence("market-question", "official.agency")
    with pytest.raises(ValueError, match="source_family contains unsafe text"):
        evidence("settlement.criteria", "https://example.test/source")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_resolution_authority_gap_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must not be in the future"):
        build_report(evidence("settlement.criteria", "official.agency", observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="paper_only"):
        evidence("settlement.criteria", "official.agency", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        evidence("settlement.criteria", "official.agency", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        evidence("settlement.criteria", "official.agency", readonly=False)

    report = build_report(evidence("settlement.criteria", "official.agency"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")


@pytest.mark.parametrize(
    ("criteria_group", "source_family"),
    (
        (".settlement", "official.agency"),
        ("settlement..criteria", "official.agency"),
        ("Settlement.criteria", "official.agency"),
        ("settlement.criteria", "official..agency"),
        ("settlement.criteria", "official.αγency"),
    ),
)
def test_inputs_require_canonical_ascii_public_identifiers(
    criteria_group: str,
    source_family: str,
) -> None:
    with pytest.raises(ValueError, match="must be a public identifier"):
        evidence(criteria_group, source_family)


def test_exports_frozen_dataclasses_status_vocabulary_and_pure_report_scope() -> None:
    module = api()
    input_row = evidence("settlement.criteria", "official.agency")
    report = build_report(input_row)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_STATUSES",
        "ResearchSourceResolutionAuthorityGapConfig",
        "ResearchSourceResolutionAuthorityGapInput",
        "ResearchSourceResolutionAuthorityGapReport",
        "ResearchSourceResolutionAuthorityGapRow",
        "build_research_source_resolution_authority_gap_report",
        "research_source_resolution_authority_gap_report_digest",
        "research_source_resolution_authority_gap_report_payload",
        "validate_research_source_resolution_authority_gap_report_digest",
    )
    assert module.RESEARCH_SOURCE_RESOLUTION_AUTHORITY_GAP_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(config())
    assert is_dataclass(input_row)
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        input_row.source_family = "independent.archive"
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().min_independence_score = d("0.800000")

    for public_type in (
        module.ResearchSourceResolutionAuthorityGapConfig,
        module.ResearchSourceResolutionAuthorityGapInput,
        module.ResearchSourceResolutionAuthorityGapReport,
        module.ResearchSourceResolutionAuthorityGapRow,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Derived{public_type.__name__}", (public_type,), {})

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    public_names = set(module.__all__)
    for public_type in (
        module.ResearchSourceResolutionAuthorityGapConfig,
        module.ResearchSourceResolutionAuthorityGapInput,
        module.ResearchSourceResolutionAuthorityGapReport,
        module.ResearchSourceResolutionAuthorityGapRow,
    ):
        public_names.update(field.name for field in fields(public_type))
    forbidden_surface_fragments = (
        "authentication",
        "live_execution",
        "order",
        "recommend",
        "sizing",
        "stake",
        "trade",
        "wallet",
    )
    assert not any(
        fragment in public_name.lower()
        for public_name in public_names
        for fragment in forbidden_surface_fragments
    )


def assert_no_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)
    else:
        assert type(value) is not float


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "market-",
        "token",
        "wallet",
        "order",
        "trade",
        "question",
        "slug",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
