from __future__ import annotations

import hashlib
from itertools import permutations
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN, localcontext
from typing import Any

import pytest

from polymarket_alpha_lab.research_source_claim_resolution_authority_decay_scorecard_report import (
    ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
    ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence,
    ResearchSourceClaimResolutionAuthorityDecayScorecardReport,
    ResearchSourceClaimResolutionAuthorityDecayScorecardRow,
    build_research_source_claim_resolution_authority_decay_scorecard_report,
    research_source_claim_resolution_authority_decay_scorecard_report_public_payload,
    validate_research_source_claim_resolution_authority_decay_scorecard_report_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "db",
    "network",
    "wallet",
    "auth",
    "order",
    "live",
    "trading",
    "sizing",
    "recommendation",
)


def d(value: str) -> Decimal:
    return Decimal(value)


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    unsigned = dict(resigned)
    unsigned.pop("derived_validation_digest", None)
    canonical = json.dumps(
        unsigned,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    resigned["derived_validation_digest"] = hashlib.sha256(canonical).hexdigest()
    return resigned


def evidence(
    claim_id: str,
    evidence_id: str,
    issuer_id: str,
    resolution_id: str,
    issuer_kind: str,
    *,
    observed_delta_seconds: int = 600,
    issuer_score: Decimal = d("0.900000"),
    resolution_alignment: Decimal = d("0.900000"),
    parse_confidence: Decimal = d("0.900000"),
) -> ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence:
    return ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence(
        claim_id=claim_id,
        evidence_id=evidence_id,
        issuer_id=issuer_id,
        resolution_id=resolution_id,
        issuer_kind=issuer_kind,
        observed_at=GENERATED_AT - timedelta(seconds=observed_delta_seconds),
        issuer_score=issuer_score,
        resolution_alignment=resolution_alignment,
        parse_confidence=parse_confidence,
    )


def complete_evidence() -> tuple[ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence, ...]:
    return (
        evidence(
            "claim-alpha",
            "evidence-beta",
            "issuer-official",
            "resolution-alpha",
            "official",
            issuer_score=d("1.000000"),
            resolution_alignment=d("0.960000"),
            parse_confidence=d("0.950000"),
        ),
        evidence(
            "claim-alpha",
            "evidence-alpha",
            "issuer-archive",
            "resolution-alpha",
            "archive",
            issuer_score=d("0.850000"),
            resolution_alignment=d("0.920000"),
            parse_confidence=d("0.900000"),
        ),
        evidence(
            "claim-beta",
            "evidence-gamma",
            "issuer-independent",
            "resolution-beta",
            "independent",
            issuer_score=d("0.900000"),
            resolution_alignment=d("0.930000"),
            parse_confidence=d("0.940000"),
        ),
    )


def build_report(
    evidence_rows: tuple[ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence, ...] = complete_evidence(),
    *,
    config: ResearchSourceClaimResolutionAuthorityDecayScorecardConfig | None = None,
) -> ResearchSourceClaimResolutionAuthorityDecayScorecardReport:
    return build_research_source_claim_resolution_authority_decay_scorecard_report(
        evidence_rows,
        config=config or ResearchSourceClaimResolutionAuthorityDecayScorecardConfig(),
        generated_at=GENERATED_AT,
    )


def assert_no_public_numeric_scalars(value: object) -> None:
    if value is None or type(value) is bool or type(value) is str:
        return
    if isinstance(value, (int, float, Decimal)):
        raise AssertionError(f"public payload contains numeric scalar: {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_public_numeric_scalars(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_public_numeric_scalars(item)
        return
    raise AssertionError(f"unexpected public payload value: {value!r}")


def assert_no_forbidden_public_fragments(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        normalized = value.lower()
        for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
            assert fragment not in normalized
        return
    if type(value) is dict:
        for key, item in value.items():
            assert_no_forbidden_public_fragments(key)
            if key == "derived_validation_digest":
                continue
            assert_no_forbidden_public_fragments(item)
        return
    if type(value) is list:
        for item in value:
            assert_no_forbidden_public_fragments(item)
        return
    raise AssertionError(f"unexpected public payload value: {value!r}")


def test_complete_scorecard_passes_with_decimal_only_sanitized_payload() -> None:
    report = build_report(tuple(reversed(complete_evidence())))

    assert report.status == "pass"
    assert report.reason_codes == ("scorecard_pass",)
    assert report.evidence_count == d("3")
    assert report.pass_count == d("3")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.average_decay_score == d("0.928333")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)

    payload = research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
        report,
    )

    assert payload["status"] == "pass"
    assert payload["average_decay_score"] == "0.928333"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert [row["item_ref"] for row in payload["score_rows"]] == sorted(
        row["item_ref"] for row in payload["score_rows"]
    )
    assert_no_public_numeric_scalars(payload)
    assert_no_forbidden_public_fragments(payload)
    assert validate_research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
        payload,
    )


def test_public_payload_is_deterministic_across_input_order() -> None:
    first = research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
        build_report(complete_evidence()),
    )
    second = research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
        build_report(tuple(reversed(complete_evidence()))),
    )

    assert first == second


def test_public_payload_is_stable_across_every_input_permutation() -> None:
    expected = research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
        build_report(complete_evidence()),
    )

    for evidence_order in permutations(complete_evidence()):
        assert (
            research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
                build_report(evidence_order),
            )
            == expected
        )


def test_scorecard_uses_only_pass_watch_block_statuses() -> None:
    stale_watch = evidence(
        "claim-watch",
        "evidence-watch",
        "issuer-watch",
        "resolution-watch",
        "archive",
        observed_delta_seconds=5000,
        issuer_score=d("0.700000"),
        resolution_alignment=d("0.700000"),
        parse_confidence=d("0.700000"),
    )
    block_low_confidence = evidence(
        "claim-block",
        "evidence-block",
        "issuer-block",
        "resolution-block",
        "independent",
        issuer_score=d("0.300000"),
        resolution_alignment=d("0.300000"),
        parse_confidence=d("0.300000"),
    )

    watch_report = build_report((stale_watch,))
    block_report = build_report((block_low_confidence,))
    empty_report = build_report(())

    assert watch_report.status == "watch"
    assert watch_report.score_rows[0].status == "watch"
    assert block_report.status == "block"
    assert block_report.score_rows[0].status == "block"
    assert empty_report.status == "block"
    for report in (watch_report, block_report, empty_report):
        payload = research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
            report,
        )
        statuses = {payload["status"]}
        statuses.update(row["status"] for row in payload["score_rows"])
        assert statuses <= {"pass", "watch", "block"}
        assert "blocked" not in repr(payload)


def test_derived_validation_digest_rejects_report_and_payload_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)

    payload = research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
        report,
    )
    tampered = dict(payload)
    tampered["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
            tampered,
        )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
            missing_digest,
        )


def test_public_payload_rejects_unsafe_keys_values_numeric_scalars_and_false_flags() -> None:
    payload = research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
        build_report(),
    )

    for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
        unsafe_key_payload = dict(payload)
        unsafe_key_payload[f"{fragment}_field"] = "redacted"
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
                unsafe_key_payload,
            )

        unsafe_value_payload = dict(payload)
        unsafe_value_payload["config_version"] = f"contains-{fragment}"
        with pytest.raises(ValueError, match="unsafe public payload"):
            research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
                unsafe_value_payload,
            )

    numeric_payload = dict(payload)
    numeric_payload["evidence_count"] = 3
    with pytest.raises(ValueError, match="Decimal strings"):
        research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
            numeric_payload,
        )

    false_flag_payload = dict(payload)
    false_flag_payload["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
            false_flag_payload,
        )


def test_decimal_only_validation_rejects_float_and_integer_inputs() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        evidence(
            "claim-bad-decimal",
            "evidence-bad-decimal",
            "issuer-bad-decimal",
            "resolution-bad-decimal",
            "archive",
            issuer_score=0.7,  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Decimal"):
        ResearchSourceClaimResolutionAuthorityDecayScorecardConfig(
            fresh_age_seconds=60,  # type: ignore[arg-type]
        )


def test_decimal_bounds_are_checked_before_quantization() -> None:
    with pytest.raises(ValueError, match="issuer_score"):
        evidence(
            "claim-raw-negative",
            "evidence-raw-negative",
            "issuer-raw-negative",
            "resolution-raw-negative",
            "archive",
            issuer_score=d("-0.0000004"),
        )

    with pytest.raises(ValueError, match="issuer_score"):
        evidence(
            "claim-raw-over-one",
            "evidence-raw-over-one",
            "issuer-raw-over-one",
            "resolution-raw-over-one",
            "archive",
            issuer_score=d("1.0000004"),
        )

    with pytest.raises(ValueError, match="fresh_age_seconds"):
        ResearchSourceClaimResolutionAuthorityDecayScorecardConfig(
            fresh_age_seconds=d("-0.0000004"),
        )


@pytest.mark.parametrize("value", (d("-0"), d("-0.000000"), d("NaN"), d("Infinity")))
def test_signed_zero_and_non_finite_decimals_are_rejected(value: Decimal) -> None:
    with pytest.raises(ValueError, match="issuer_score"):
        evidence(
            "claim-invalid-decimal",
            "evidence-invalid-decimal",
            "issuer-invalid-decimal",
            "resolution-invalid-decimal",
            "archive",
            issuer_score=value,
        )


def test_calculation_is_independent_of_the_process_decimal_context() -> None:
    expected = build_report()

    with localcontext() as context:
        context.prec = 2
        context.rounding = ROUND_DOWN
        actual = build_report()

    assert actual == expected
    assert actual.payload == expected.payload


def test_config_version_fully_determines_the_supported_calculation() -> None:
    with pytest.raises(ValueError, match="supported configuration"):
        ResearchSourceClaimResolutionAuthorityDecayScorecardConfig(
            issuer_weight=d("0.400000"),
            resolution_alignment_weight=d("0.300000"),
            parse_confidence_weight=d("0.300000"),
        )


def test_rejects_non_iterable_duplicates_future_rows_raw_values_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="iterable"):
        build_research_source_claim_resolution_authority_decay_scorecard_report(
            "not rows",  # type: ignore[arg-type]
            config=ResearchSourceClaimResolutionAuthorityDecayScorecardConfig(),
            generated_at=GENERATED_AT,
        )

    duplicate = complete_evidence()[0]
    with pytest.raises(ValueError, match="unique"):
        build_report((duplicate, duplicate))

    future = replace(complete_evidence()[0], observed_at=GENERATED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="observed_at"):
        build_report((future,))

    with pytest.raises(ValueError, match="unsafe"):
        evidence(
            "https://example.invalid/raw",
            "evidence-raw",
            "issuer-raw",
            "resolution-raw",
            "official",
        )

    with pytest.raises(ValueError, match="paper_only"):
        replace(complete_evidence()[0], paper_only=False)


def test_report_consistency_rejects_manual_mismatches() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="evidence_count"):
        replace(report, evidence_count=d("4"))
    with pytest.raises(ValueError, match="average_decay_score"):
        replace(report, average_decay_score=d("0.500000"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="watch")


def test_resigned_payload_rejects_noncanonical_schema_values() -> None:
    payload = research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
        build_report(),
    )

    noncanonical_count = json.loads(json.dumps(payload))
    noncanonical_count["evidence_count"] = "3.0"

    noncanonical_ratio = json.loads(json.dumps(payload))
    noncanonical_ratio["score_rows"][0]["issuer_score"] = "0.85"

    noncanonical_datetime = json.loads(json.dumps(payload))
    noncanonical_datetime["generated_at"] = "2026-07-06T12:00:00Z"

    noncanonical_reasons = json.loads(json.dumps(payload))
    noncanonical_reasons["score_rows"][0]["reason_codes"] = [
        "scorecard_pass",
        "scorecard_pass",
    ]

    noncanonical_item_ref = json.loads(json.dumps(payload))
    noncanonical_item_ref["score_rows"][0]["item_ref"] = "item-000099"

    for tampered in (
        noncanonical_count,
        noncanonical_ratio,
        noncanonical_datetime,
        noncanonical_reasons,
        noncanonical_item_ref,
    ):
        with pytest.raises(ValueError, match="canonical"):
            validate_research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
                resign_payload(tampered),
            )


def test_resigned_payload_recomputes_all_derived_fields() -> None:
    payload = research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
        build_report(),
    )

    forged_recency = json.loads(json.dumps(payload))
    forged_recency["score_rows"][0]["recency_factor"] = "0.500000"

    forged_decay_score = json.loads(json.dumps(payload))
    forged_decay_score["score_rows"][0]["decay_score"] = "0.800000"

    forged_row_status = json.loads(json.dumps(payload))
    forged_row_status["score_rows"][0]["status"] = "watch"
    forged_row_status["score_rows"][0]["reason_codes"] = ["decay_score_watch"]

    forged_count = json.loads(json.dumps(payload))
    forged_count["evidence_count"] = "4"

    forged_average = json.loads(json.dumps(payload))
    forged_average["average_decay_score"] = "0.900000"

    forged_report_status = json.loads(json.dumps(payload))
    forged_report_status["status"] = "watch"
    forged_report_status["reason_codes"] = ["decay_score_watch"]

    for tampered in (
        forged_recency,
        forged_decay_score,
        forged_row_status,
        forged_count,
        forged_average,
        forged_report_status,
    ):
        with pytest.raises(ValueError, match="must match"):
            validate_research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
                resign_payload(tampered),
            )


def test_resigned_payload_rejects_rows_outside_complete_canonical_sort() -> None:
    payload = research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
        build_report(),
    )
    reordered = json.loads(json.dumps(payload))
    reordered["score_rows"][0], reordered["score_rows"][-1] = (
        reordered["score_rows"][-1],
        reordered["score_rows"][0],
    )
    for index, row in enumerate(reordered["score_rows"], start=1):
        row["item_ref"] = f"item-{index:06d}"

    with pytest.raises(ValueError, match="sorted deterministically"):
        validate_research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
            resign_payload(reordered),
        )


def test_public_payload_never_exposes_private_evidence_identifiers() -> None:
    private_values = {
        value
        for evidence_row in complete_evidence()
        for value in (
            evidence_row.claim_id,
            evidence_row.evidence_id,
            evidence_row.issuer_id,
            evidence_row.resolution_id,
        )
    }
    serialized = json.dumps(
        research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
            build_report(),
        ),
        sort_keys=True,
    )

    assert all(private_value not in serialized for private_value in private_values)


def test_dataclasses_are_frozen() -> None:
    config = ResearchSourceClaimResolutionAuthorityDecayScorecardConfig()
    evidence_row = complete_evidence()[0]
    report = build_report()
    row = report.score_rows[0]

    frozen_values: tuple[Any, ...] = (config, evidence_row, row, report)
    for value in frozen_values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    assert isinstance(row, ResearchSourceClaimResolutionAuthorityDecayScorecardRow)


@pytest.mark.parametrize(
    "record_type",
    (
        ResearchSourceClaimResolutionAuthorityDecayScorecardConfig,
        ResearchSourceClaimResolutionAuthorityDecayScorecardEvidence,
        ResearchSourceClaimResolutionAuthorityDecayScorecardRow,
        ResearchSourceClaimResolutionAuthorityDecayScorecardReport,
    ),
)
def test_public_dataclasses_reject_subclassing(record_type: type[Any]) -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):
        type("ForbiddenSubclass", (record_type,), {})


def test_builder_revalidates_object_setattr_tampered_evidence() -> None:
    tampered = complete_evidence()[0]
    object.__setattr__(tampered, "issuer_score", d("0.1000004"))

    with pytest.raises(ValueError, match="evidence"):
        build_report((tampered,))


def test_builder_revalidates_object_setattr_tampered_supported_config() -> None:
    tampered = ResearchSourceClaimResolutionAuthorityDecayScorecardConfig()
    object.__setattr__(tampered, "fresh_age_seconds", d("1800.000000"))

    with pytest.raises(ValueError, match="supported configuration"):
        build_report(config=tampered)


def test_report_revalidates_object_setattr_tampered_derived_row() -> None:
    report = build_report()
    tampered_rows = list(report.score_rows)
    tampered_row = tampered_rows[0]
    object.__setattr__(tampered_row, "recency_factor", d("0.500000"))

    with pytest.raises(ValueError, match="recency_factor"):
        replace(report, score_rows=tuple(tampered_rows), derived_validation_digest="")


def test_public_payload_revalidates_resigned_object_setattr_tampered_row() -> None:
    report = build_report()
    payload = json.loads(json.dumps(report.payload))
    payload["score_rows"][0]["recency_factor"] = "0.500000"
    resigned = resign_payload(payload)

    object.__setattr__(report.score_rows[0], "recency_factor", d("0.500000"))
    object.__setattr__(
        report,
        "derived_validation_digest",
        resigned["derived_validation_digest"],
    )

    with pytest.raises(ValueError, match="recency_factor"):
        research_source_claim_resolution_authority_decay_scorecard_report_public_payload(
            report,
        )


def test_builder_revalidates_object_setattr_noncanonical_utc_evidence() -> None:
    tampered = complete_evidence()[0]
    object.__setattr__(
        tampered,
        "observed_at",
        tampered.observed_at.astimezone(timezone(timedelta(hours=2))),
    )

    with pytest.raises(ValueError, match="canonical UTC"):
        build_report((tampered,))
