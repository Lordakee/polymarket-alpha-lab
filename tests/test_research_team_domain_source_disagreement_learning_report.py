from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Context, Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_team_domain_source_disagreement_learning_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_team_domain_source_disagreement_learning_report.py",
)
GENERATED_AT = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_pass_review_quality_score": d("0.800000"),
        "min_watch_review_quality_score": d("0.600000"),
        "max_pass_repeat_disagreement_ratio": d("0.100000"),
        "max_watch_repeat_disagreement_ratio": d("0.300000"),
        "max_pass_open_follow_up_count": d("0"),
        "max_watch_open_follow_up_count": d("2"),
        "high_learning_priority_threshold": d("0.600000"),
        "medium_learning_priority_threshold": d("0.300000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSourceDisagreementLearningConfig(**values)


def disagreement(
    disagreement_key: str = "private-disagreement-alpha",
    **overrides: object,
) -> Any:
    module = api()
    values = {
        "disagreement_key": disagreement_key,
        "team_label": "policy-team",
        "domain_label": "election-policy",
        "disagreement_type": "interpretation_conflict",
        "reviewer_reference": "person://reviewer-secret-alpha",
        "primary_source_reference": "https://primary.example/private?token=alpha",
        "conflicting_source_reference": "db://conflicting-source/private-alpha",
        "review_count": d("4"),
        "correct_review_count": d("4"),
        "independent_review_count": d("4"),
        "learning_capture_count": d("4"),
        "repeated_disagreement_count": d("0"),
        "open_follow_up_count": d("0"),
        "observed_at": GENERATED_AT - timedelta(hours=2),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSourceDisagreementLearningInput(**values)


def report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_team_domain_source_disagreement_learning_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign_row(row: dict[str, Any]) -> None:
    row["derived_validation_digest"] = canonical_digest(row)


def resign_payload(payload: dict[str, Any]) -> None:
    for row in payload["rows"]:
        resign_row(row)
    payload["derived_validation_digest"] = canonical_digest(payload)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_dataclass_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool or item is None or type(item) is str:
            continue
        if isinstance(item, datetime):
            assert type(item) is datetime
            continue
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_dataclass_numeric_fields_are_decimal(nested)
            continue
        assert type(item) is Decimal, f"{field.name} is not exact Decimal: {item!r}"


def assert_public_numeric_values_are_strings(value: object) -> None:
    assert type(value) is not int
    assert type(value) is not float
    assert type(value) is not Decimal
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_strings(item)
    elif isinstance(value, list):
        for item in value:
            assert_public_numeric_values_are_strings(item)


def test_report_records_disagreement_types_review_quality_and_learning_priority() -> None:
    passing = disagreement(
        "private-pass-case",
        team_label="policy-team",
        domain_label="election-policy",
        disagreement_type="interpretation_conflict",
    )
    watched = disagreement(
        "private-watch-case",
        team_label="macro-team",
        domain_label="central-bank-policy",
        disagreement_type="timing_conflict",
        correct_review_count=d("3"),
        independent_review_count=d("3"),
        learning_capture_count=d("2"),
        repeated_disagreement_count=d("1"),
        open_follow_up_count=d("1"),
    )
    blocked = disagreement(
        "private-block-case",
        team_label="legal-team",
        domain_label="court-procedure",
        disagreement_type="factual_conflict",
        correct_review_count=d("2"),
        independent_review_count=d("1"),
        learning_capture_count=d("1"),
        repeated_disagreement_count=d("2"),
        open_follow_up_count=d("3"),
    )

    result = report(passing, blocked, watched)
    rebuilt = report(watched, passing, blocked)

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == (
        "research-team-domain-source-disagreement-learning-report-v1"
    )
    assert result.input_count == d("3")
    assert result.row_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.high_priority_count == d("1")
    assert result.medium_priority_count == d("1")
    assert result.low_priority_count == d("1")
    assert result.disagreement_type_count == d("3")
    assert result.watch_block_ratio == d("0.666667")
    assert result.average_review_quality_score == d("0.666667")
    assert result.max_learning_priority_score == d("0.729167")
    assert result.status == "block"
    assert result.report_mode == "paper_source_disagreement_learning_block"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.derived_validation_digest)
    assert_dataclass_numeric_fields_are_decimal(result)

    assert tuple(row.learning_rank for row in result.rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.learning_priority for row in result.rows) == (
        "high",
        "medium",
        "low",
    )

    blocked_row = result.rows[0]
    assert blocked_row.disagreement_fingerprint == hashlib.sha256(
        b"private-block-case",
    ).hexdigest()
    assert blocked_row.disagreement_type == "factual_conflict"
    assert blocked_row.resolution_accuracy_ratio == d("0.500000")
    assert blocked_row.independent_review_ratio == d("0.250000")
    assert blocked_row.learning_capture_ratio == d("0.250000")
    assert blocked_row.repeat_disagreement_ratio == d("0.500000")
    assert blocked_row.open_follow_up_ratio == d("0.750000")
    assert blocked_row.review_quality_score == d("0.333333")
    assert blocked_row.learning_priority_score == d("0.729167")
    assert blocked_row.reason_codes == (
        "review_quality_block",
        "repeat_disagreement_block",
        "open_follow_up_block",
        "learning_priority_high",
    )

    watched_row = result.rows[1]
    assert watched_row.review_quality_score == d("0.666667")
    assert watched_row.learning_priority_score == d("0.383333")
    assert watched_row.reason_codes == (
        "review_quality_watch",
        "repeat_disagreement_watch",
        "open_follow_up_watch",
        "learning_priority_medium",
    )

    passed_row = result.rows[2]
    assert passed_row.review_quality_score == d("1.000000")
    assert passed_row.learning_priority_score == d("0.125000")
    assert passed_row.reason_codes == (
        "source_disagreement_learning_pass",
        "learning_priority_low",
    )

    assert tuple(
        (item.disagreement_type, item.count)
        for item in result.disagreement_type_counts
    ) == (
        ("factual_conflict", d("1")),
        ("timing_conflict", d("1")),
        ("interpretation_conflict", d("1")),
    )
    assert result.derived_validation_digest == rebuilt.derived_validation_digest
    assert result.rows == rebuilt.rows


def test_learning_rows_use_fingerprint_tie_break_for_identical_public_fields() -> None:
    keys = (
        "private-tie-charlie",
        "private-tie-alpha",
        "private-tie-bravo",
    )
    items = tuple(
        disagreement(
            key,
            team_label="tie-team",
            domain_label="tie-domain",
            disagreement_type="interpretation_conflict",
            observed_at=GENERATED_AT - timedelta(hours=1),
        )
        for key in keys
    )

    result = report(items[2], items[0], items[1])
    rebuilt = report(items[1], items[2], items[0])
    expected_fingerprints = tuple(
        sorted(hashlib.sha256(key.encode()).hexdigest() for key in keys),
    )

    assert tuple(row.learning_rank for row in result.rows) == (d("1"), d("2"), d("3"))
    assert tuple(
        row.disagreement_fingerprint for row in result.rows
    ) == expected_fingerprints
    assert result.rows == rebuilt.rows
    assert result.derived_validation_digest == rebuilt.derived_validation_digest


def test_mixed_severity_reason_codes_use_global_canonical_order() -> None:
    result = report(
        disagreement(
            "private-mixed-severity-reasons",
            correct_review_count=d("3"),
            independent_review_count=d("3"),
            learning_capture_count=d("2"),
            repeated_disagreement_count=d("2"),
        ),
    )

    assert result.rows[0].status == "block"
    assert result.rows[0].reason_codes == (
        "repeat_disagreement_block",
        "review_quality_watch",
        "learning_priority_medium",
    )
    assert result.reason_codes == result.rows[0].reason_codes


def test_empty_report_is_blocked_and_decimal_zeroed() -> None:
    result = report()

    assert result.input_count == d("0")
    assert result.row_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.high_priority_count == d("0")
    assert result.medium_priority_count == d("0")
    assert result.low_priority_count == d("0")
    assert result.disagreement_type_count == d("0")
    assert result.watch_block_ratio == d("0.000000")
    assert result.average_review_quality_score == d("0.000000")
    assert result.max_learning_priority_score == d("0.000000")
    assert result.status == "block"
    assert result.report_mode == "paper_source_disagreement_learning_block"
    assert result.reason_codes == (
        "research_team_domain_source_disagreement_learning_report_empty",
    )
    assert result.disagreement_type_counts == ()
    assert result.reason_code_counts == ()
    assert result.rows == ()
    assert_digest(result.derived_validation_digest)


def test_public_payload_is_canonical_exact_and_private_reference_free() -> None:
    module = api()
    private_reviewer = "person://reviewer-name-secret"
    private_primary = "https://source.example/private?token=primary-secret"
    private_conflicting = "db://source-table/private-conflict-secret"
    result = report(
        disagreement(
            reviewer_reference=private_reviewer,
            primary_source_reference=private_primary,
            conflicting_source_reference=private_conflicting,
        ),
    )

    payload = module.research_team_domain_source_disagreement_learning_report_payload(
        result,
    )
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert set(payload) == module.REPORT_PAYLOAD_KEYS
    assert set(payload["rows"][0]) == module.ROW_PAYLOAD_KEYS
    assert set(payload["disagreement_type_counts"][0]) == (
        module.TYPE_COUNT_PAYLOAD_KEYS
    )
    assert set(payload["reason_code_counts"][0]) == module.REASON_COUNT_PAYLOAD_KEYS
    assert payload["generated_at"] == "2026-07-10T12:00:00+00:00"
    assert payload["input_count"] == "1"
    assert payload["average_review_quality_score"] == "1.000000"
    assert payload["rows"][0]["review_count"] == "4"
    assert payload["rows"][0]["learning_priority_score"] == "0.125000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.research_team_domain_source_disagreement_learning_report_digest(
        payload,
    ) == payload["derived_validation_digest"]
    assert (
        module.validate_research_team_domain_source_disagreement_learning_report_digest(
            payload,
        )
        is True
    )
    assert private_reviewer not in encoded
    assert private_primary not in encoded
    assert private_conflicting not in encoded
    for private_key in (
        "reviewer_reference",
        "primary_source_reference",
        "conflicting_source_reference",
    ):
        assert private_key not in encoded
    for forbidden in (
        "recommendation",
        "position_size",
        "wallet",
        "order",
        "live_trading",
    ):
        assert forbidden not in encoded.lower()
    assert_public_numeric_values_are_strings(payload)
    assert (
        module.research_team_domain_source_disagreement_learning_report_payload(
            payload,
        )
        == payload
    )


def test_payload_rejects_exact_schema_violations_and_resigned_derived_forgery() -> None:
    module = api()
    payload = module.research_team_domain_source_disagreement_learning_report_payload(
        report(disagreement()),
    )

    extra = dict(payload)
    extra["reviewer_reference"] = "private-person"
    extra["derived_validation_digest"] = canonical_digest(extra)
    with pytest.raises(ValueError, match="exact schema|unsafe"):
        module.research_team_domain_source_disagreement_learning_report_payload(extra)

    missing = dict(payload)
    missing.pop("report_mode")
    missing["derived_validation_digest"] = canonical_digest(missing)
    with pytest.raises(ValueError, match="exact schema"):
        module.research_team_domain_source_disagreement_learning_report_payload(missing)

    wrong_numeric_type = dict(payload)
    wrong_numeric_type["input_count"] = 1
    with pytest.raises(ValueError, match="Decimal-derived strings"):
        module.research_team_domain_source_disagreement_learning_report_payload(
            wrong_numeric_type,
        )

    forged_row = json.loads(json.dumps(payload))
    forged_row["rows"][0]["review_quality_score"] = "0.111111"
    resign_row(forged_row["rows"][0])
    forged_row["derived_validation_digest"] = canonical_digest(forged_row)
    with pytest.raises(ValueError, match="review_quality_score|derived fields"):
        module.research_team_domain_source_disagreement_learning_report_payload(
            forged_row,
        )

    forged_report = json.loads(json.dumps(payload))
    forged_report["pass_count"] = "0"
    forged_report["watch_count"] = "1"
    forged_report["status"] = "watch"
    forged_report["report_mode"] = "paper_source_disagreement_learning_watch"
    forged_report["derived_validation_digest"] = canonical_digest(forged_report)
    with pytest.raises(ValueError, match="derived fields|pass_count|status"):
        module.research_team_domain_source_disagreement_learning_report_payload(
            forged_report,
        )

    bad_digest = dict(payload)
    bad_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_source_disagreement_learning_report_payload(
            bad_digest,
        )


def test_public_payload_rejects_reordered_schema_keys_even_when_resigned() -> None:
    module = api()
    payload = module.research_team_domain_source_disagreement_learning_report_payload(
        report(disagreement()),
    )
    keys = list(payload)
    reordered = {
        keys[1]: payload[keys[1]],
        keys[0]: payload[keys[0]],
        **{key: payload[key] for key in keys[2:]},
    }
    reordered["derived_validation_digest"] = canonical_digest(reordered)

    with pytest.raises(ValueError, match="exact schema"):
        module.research_team_domain_source_disagreement_learning_report_payload(
            reordered,
        )

    reordered_row = json.loads(json.dumps(payload))
    row_keys = list(reordered_row["rows"][0])
    reordered_row["rows"][0] = {
        row_keys[1]: reordered_row["rows"][0][row_keys[1]],
        row_keys[0]: reordered_row["rows"][0][row_keys[0]],
        **{key: reordered_row["rows"][0][key] for key in row_keys[2:]},
    }
    resign_payload(reordered_row)
    with pytest.raises(ValueError, match="exact schema"):
        module.research_team_domain_source_disagreement_learning_report_payload(
            reordered_row,
        )

    reordered_reason_count = json.loads(json.dumps(payload))
    reason_count_keys = list(reordered_reason_count["reason_code_counts"][0])
    reordered_reason_count["reason_code_counts"][0] = {
        reason_count_keys[1]: reordered_reason_count["reason_code_counts"][0][
            reason_count_keys[1]
        ],
        reason_count_keys[0]: reordered_reason_count["reason_code_counts"][0][
            reason_count_keys[0]
        ],
        **{
            key: reordered_reason_count["reason_code_counts"][0][key]
            for key in reason_count_keys[2:]
        },
    }
    resign_payload(reordered_reason_count)
    with pytest.raises(ValueError, match="exact schema"):
        module.research_team_domain_source_disagreement_learning_report_payload(
            reordered_reason_count,
        )


def test_public_mapping_payload_rejects_non_json_container_types() -> None:
    module = api()
    payload = module.research_team_domain_source_disagreement_learning_report_payload(
        report(disagreement("private-json-container-contract")),
    )
    payload["rows"] = tuple(payload["rows"])

    with pytest.raises(ValueError, match="unsupported|JSON array|list"):
        module.research_team_domain_source_disagreement_learning_report_payload(payload)


def test_public_payload_rederives_resigned_learning_and_aggregate_fields() -> None:
    module = api()
    payload = module.research_team_domain_source_disagreement_learning_report_payload(
        report(
            disagreement("private-pass-forgery"),
            disagreement(
                "private-watch-forgery",
                correct_review_count=d("3"),
                independent_review_count=d("3"),
                learning_capture_count=d("2"),
                repeated_disagreement_count=d("1"),
                open_follow_up_count=d("1"),
            ),
            disagreement(
                "private-block-forgery",
                disagreement_type="factual_conflict",
                correct_review_count=d("2"),
                independent_review_count=d("1"),
                learning_capture_count=d("1"),
                repeated_disagreement_count=d("2"),
                open_follow_up_count=d("3"),
            ),
        ),
    )

    def forge_row_status(forged: dict[str, Any]) -> None:
        forged["rows"][0]["status"] = "pass"

    def forge_row_reason_codes(forged: dict[str, Any]) -> None:
        forged["rows"][0]["reason_codes"] = [
            "review_quality_block",
            "learning_priority_high",
        ]

    def forge_row_score(forged: dict[str, Any]) -> None:
        forged["rows"][1]["learning_priority_score"] = "0.000000"

    def forge_row_count(forged: dict[str, Any]) -> None:
        forged["rows"][0]["open_follow_up_count"] = "2"

    def forge_row_order(forged: dict[str, Any]) -> None:
        forged["rows"] = [
            forged["rows"][1],
            forged["rows"][0],
            forged["rows"][2],
        ]

    def forge_report_count(forged: dict[str, Any]) -> None:
        forged["watch_count"] = "2"

    def forge_type_aggregate(forged: dict[str, Any]) -> None:
        forged["disagreement_type_counts"][0][
            "average_review_quality_score"
        ] = "0.000000"

    def forge_reason_aggregate(forged: dict[str, Any]) -> None:
        forged["reason_code_counts"][0]["count"] = "2"

    cases = (
        (forge_row_status, "status"),
        (forge_row_reason_codes, "reason_codes"),
        (forge_row_score, "learning_priority_score"),
        (forge_row_count, "derived fields"),
        (forge_row_order, "payload.rows"),
        (forge_report_count, "watch_count"),
        (forge_type_aggregate, "disagreement_type_counts"),
        (forge_reason_aggregate, "reason_code_counts"),
    )
    for mutator, match in cases:
        forged = json.loads(json.dumps(payload))
        mutator(forged)
        resign_payload(forged)
        with pytest.raises(ValueError, match=match):
            module.research_team_domain_source_disagreement_learning_report_payload(
                forged,
            )


def test_dataclasses_recompute_all_derived_fields_and_reject_tampering() -> None:
    result = report(disagreement())
    row = result.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="resolution_accuracy_ratio"):
        replace(row, resolution_accuracy_ratio=d("0.999999"))
    with pytest.raises(ValueError, match="review_quality_score"):
        replace(row, review_quality_score=d("0.999999"))
    with pytest.raises(ValueError, match="learning_priority_score"):
        replace(row, learning_priority_score=d("0.999999"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count"):
        replace(result, pass_count=d("0"))
    with pytest.raises(ValueError, match="average_review_quality_score"):
        replace(result, average_review_quality_score=d("0.999999"))
    with pytest.raises(ValueError, match="rows must be sorted"):
        replace(
            result,
            input_count=d("2"),
            row_count=d("2"),
            pass_count=d("2"),
            low_priority_count=d("2"),
            disagreement_type_count=d("1"),
            rows=(
                report(disagreement("zeta-private")).rows[0],
                report(disagreement("alpha-private")).rows[0],
            ),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    reason_count_result = report(disagreement("private-reason-count-tamper"))
    object.__setattr__(reason_count_result.reason_code_counts[0], "count", d("2"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        api().research_team_domain_source_disagreement_learning_report_payload(
            reason_count_result,
        )

    object.__setattr__(row, "learning_priority_score", d("0.999999"))
    with pytest.raises(ValueError, match="derived fields|learning_priority_score"):
        api().research_team_domain_source_disagreement_learning_report_payload(result)


def test_report_construction_rejects_a_nested_row_with_a_stale_digest() -> None:
    result = report(disagreement("private-nested-row-digest-tamper"))
    object.__setattr__(result.rows[0], "team_label", "tampered-team")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="")


def test_dataclass_digest_autofill_accepts_only_the_empty_string_sentinel() -> None:
    result = report(disagreement("private-exact-digest-type"))

    assert_digest(result.rows[0].derived_validation_digest)
    assert_digest(result.derived_validation_digest)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result.rows[0], derived_validation_digest=None)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest=None)


def test_row_dataclass_rejects_status_and_reason_semantic_tampering() -> None:
    row = report(disagreement("private-row-status-reason-tamper")).rows[0]

    with pytest.raises(ValueError, match="reason_codes must match status"):
        replace(row, status="block", derived_validation_digest="")
    with pytest.raises(ValueError, match="reason_codes must match status"):
        replace(
            row,
            reason_codes=("review_quality_watch", "learning_priority_low"),
            derived_validation_digest="",
        )
    with pytest.raises(ValueError, match="reason_codes must match status"):
        replace(
            row,
            status="block",
            reason_codes=(
                "review_quality_block",
                "review_quality_watch",
                "learning_priority_low",
            ),
            derived_validation_digest="",
        )


def test_build_revalidates_input_private_fields_after_object_setattr_tampering() -> None:
    tampered_config = config()
    object.__setattr__(
        tampered_config,
        "min_watch_review_quality_score",
        d("0.900000"),
    )
    with pytest.raises(ValueError, match="min_watch_review_quality_score"):
        report(disagreement("private-config-tamper"), cfg=tampered_config)

    blank_key = disagreement()
    object.__setattr__(blank_key, "disagreement_key", "")
    with pytest.raises(ValueError, match="disagreement_key"):
        report(blank_key)

    collapsed_sources = disagreement()
    object.__setattr__(
        collapsed_sources,
        "primary_source_reference",
        collapsed_sources.conflicting_source_reference,
    )
    with pytest.raises(ValueError, match="primary_source_reference"):
        report(collapsed_sources)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("review_count", Decimal("NaN")),
        ("review_count", Decimal("Infinity")),
        ("review_count", Decimal("-Infinity")),
        ("review_count", Decimal("-0")),
        ("correct_review_count", Decimal("-0.000000")),
        ("open_follow_up_count", Decimal("-0")),
    ),
)
def test_non_finite_and_signed_zero_decimals_are_rejected(
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match="finite|signed zero"):
        disagreement(**{field_name: value})


def test_ratio_decimal_raw_bounds_are_checked_before_quantizing() -> None:
    with pytest.raises(ValueError, match="min_pass_review_quality_score"):
        config(min_pass_review_quality_score=d("1.0000004"))


def test_fixed_decimal_context_rejects_unrepresentable_magnitudes_cleanly() -> None:
    module = api()

    with pytest.raises(ValueError, match="review_count"):
        disagreement(review_count=d("1E+1000"))

    payload = module.research_team_domain_source_disagreement_learning_report_payload(
        report(disagreement("private-unrepresentable-payload-decimal")),
    )
    payload["rows"][0]["review_count"] = "1E+1000"
    resign_payload(payload)
    with pytest.raises(ValueError, match="review_count"):
        module.research_team_domain_source_disagreement_learning_report_payload(payload)


def test_decimal_arithmetic_uses_fixed_context_not_ambient_context() -> None:
    module = api()
    item = disagreement(
        review_count=d("3"),
        correct_review_count=d("1"),
        independent_review_count=d("1"),
        learning_capture_count=d("1"),
    )
    cfg = config()

    with localcontext(Context(prec=1)):
        result = module.build_research_team_domain_source_disagreement_learning_report(
            (item,),
            config=cfg,
            generated_at=GENERATED_AT,
        )

    assert result.rows[0].resolution_accuracy_ratio == d("0.333333")
    assert result.rows[0].independent_review_ratio == d("0.333333")
    assert result.rows[0].learning_capture_ratio == d("0.333333")
    assert result.rows[0].review_quality_score == d("0.333333")
    assert result.rows[0].learning_priority_score == d("0.291667")


def test_decimal_sorting_uses_fixed_values_not_ambient_context_rounding() -> None:
    low_score = disagreement(
        "private-low-priority-score",
        review_count=d("100"),
        correct_review_count=d("100"),
        independent_review_count=d("100"),
        learning_capture_count=d("100"),
    )
    high_score = disagreement(
        "private-high-priority-score",
        review_count=d("100"),
        correct_review_count=d("100"),
        independent_review_count=d("100"),
        learning_capture_count=d("100"),
        repeated_disagreement_count=d("1"),
    )
    expected = report(low_score, high_score)

    with localcontext(Context(prec=1)):
        actual = report(low_score, high_score)

    assert tuple(row.learning_priority_score for row in actual.rows) == (
        d("0.127500"),
        d("0.125000"),
    )
    assert actual.rows == expected.rows
    assert actual.derived_validation_digest == expected.derived_validation_digest


def test_exact_types_bounds_duplicates_and_config_invariants_are_rejected() -> None:
    module = api()

    assert module.RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_TYPES == (
        "authority_conflict",
        "factual_conflict",
        "coverage_gap",
        "timing_conflict",
        "interpretation_conflict",
    )
    assert module.RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_PRIORITIES == (
        "high",
        "medium",
        "low",
    )

    with pytest.raises(ValueError, match="review_count"):
        disagreement(review_count=4)
    with pytest.raises(ValueError, match="review_count"):
        disagreement(review_count=_DecimalSubclass("4"))
    with pytest.raises(ValueError, match="review_count"):
        disagreement(review_count=d("4.5"))
    with pytest.raises(ValueError, match="correct_review_count"):
        disagreement(correct_review_count=d("5"))
    with pytest.raises(ValueError, match="independent_review_count"):
        disagreement(independent_review_count=d("5"))
    with pytest.raises(ValueError, match="learning_capture_count"):
        disagreement(learning_capture_count=d("5"))
    with pytest.raises(ValueError, match="repeated_disagreement_count"):
        disagreement(repeated_disagreement_count=d("5"))
    with pytest.raises(ValueError, match="disagreement_type"):
        disagreement(disagreement_type="unknown_conflict")
    with pytest.raises(ValueError, match="observed_at"):
        disagreement(observed_at=datetime(2026, 7, 10, 10, 0))
    with pytest.raises(ValueError, match="observed_at"):
        disagreement(
            observed_at=_DatetimeSubclass(2026, 7, 10, 10, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        disagreement(
            observed_at=datetime(
                2026,
                7,
                10,
                10,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(disagreement(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="disagreement_key values must be unique"):
        report(disagreement(), disagreement())
    with pytest.raises(ValueError, match="primary_source_reference"):
        disagreement(
            primary_source_reference="same-private-source",
            conflicting_source_reference="same-private-source",
        )
    with pytest.raises(ValueError, match="paper_only"):
        disagreement(paper_only=False)
    with pytest.raises(ValueError, match="min_watch_review_quality_score"):
        config(
            min_pass_review_quality_score=d("0.500000"),
            min_watch_review_quality_score=d("0.600000"),
        )
    with pytest.raises(ValueError, match="max_pass_repeat_disagreement_ratio"):
        config(
            max_pass_repeat_disagreement_ratio=d("0.400000"),
            max_watch_repeat_disagreement_ratio=d("0.300000"),
        )
    with pytest.raises(ValueError, match="medium_learning_priority_threshold"):
        config(
            high_learning_priority_threshold=d("0.200000"),
            medium_learning_priority_threshold=d("0.300000"),
        )

    shifted = report(
        disagreement(
            observed_at=datetime(
                2026,
                7,
                10,
                4,
                0,
                tzinfo=timezone(timedelta(hours=-6)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            10,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    assert shifted.generated_at == GENERATED_AT
    assert shifted.rows[0].observed_at == datetime(2026, 7, 10, 10, 0, tzinfo=UTC)


def test_as_of_boundary_is_inclusive_and_future_rows_are_always_rejected() -> None:
    module = api()
    at_boundary = report(disagreement(observed_at=GENERATED_AT))

    assert at_boundary.rows[0].observed_at == GENERATED_AT

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        replace(
            at_boundary,
            generated_at=GENERATED_AT - timedelta(microseconds=1),
            derived_validation_digest="",
        )

    forged = module.research_team_domain_source_disagreement_learning_report_payload(
        at_boundary,
    )
    forged["rows"][0]["observed_at"] = (
        GENERATED_AT + timedelta(microseconds=1)
    ).isoformat()
    resign_payload(forged)

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        module.research_team_domain_source_disagreement_learning_report_payload(forged)


def test_public_dataclasses_are_final_and_export_surface_is_exact() -> None:
    module = api()
    expected_exports = {
        "DEFAULT_RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_REPORT_CONFIG_VERSION",
        "RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_PRIORITIES",
        "RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_LEARNING_STATUSES",
        "RESEARCH_TEAM_DOMAIN_SOURCE_DISAGREEMENT_TYPES",
        "REPORT_PAYLOAD_KEYS",
        "ROW_PAYLOAD_KEYS",
        "TYPE_COUNT_PAYLOAD_KEYS",
        "REASON_COUNT_PAYLOAD_KEYS",
        "ResearchTeamDomainSourceDisagreementLearningConfig",
        "ResearchTeamDomainSourceDisagreementLearningInput",
        "ResearchTeamDomainSourceDisagreementLearningReasonCodeCount",
        "ResearchTeamDomainSourceDisagreementLearningReport",
        "ResearchTeamDomainSourceDisagreementLearningRow",
        "ResearchTeamDomainSourceDisagreementLearningTypeCount",
        "build_research_team_domain_source_disagreement_learning_report",
        "research_team_domain_source_disagreement_learning_report_digest",
        "research_team_domain_source_disagreement_learning_report_payload",
        "validate_research_team_domain_source_disagreement_learning_report_digest",
    }
    assert set(module.__all__) == expected_exports

    for class_name in (
        "ResearchTeamDomainSourceDisagreementLearningConfig",
        "ResearchTeamDomainSourceDisagreementLearningInput",
        "ResearchTeamDomainSourceDisagreementLearningReasonCodeCount",
        "ResearchTeamDomainSourceDisagreementLearningReport",
        "ResearchTeamDomainSourceDisagreementLearningRow",
        "ResearchTeamDomainSourceDisagreementLearningTypeCount",
    ):
        cls = getattr(module, class_name)
        with pytest.raises(TypeError, match="subclass"):
            type(f"Bad{class_name}", (cls,), {})


def test_module_is_pure_report_only_readonly_and_has_no_io_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    banned_import_roots = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "send",
        "submit",
        "update",
        "urlopen",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not {alias.name.split(".")[0] for alias in node.names} & (
                banned_import_roots
            )
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in banned_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in banned_calls

    public_fields = {
        field.name
        for class_name in (
            "ResearchTeamDomainSourceDisagreementLearningRow",
            "ResearchTeamDomainSourceDisagreementLearningReport",
            "ResearchTeamDomainSourceDisagreementLearningTypeCount",
            "ResearchTeamDomainSourceDisagreementLearningReasonCodeCount",
        )
        for field in fields(getattr(api(), class_name))
    }
    assert not public_fields & {
        "reviewer_reference",
        "primary_source_reference",
        "conflicting_source_reference",
        "recommendation",
        "position",
        "position_size",
    }
