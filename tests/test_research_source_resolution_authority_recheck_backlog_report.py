from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_resolution_authority_recheck_backlog_report import (
    ResearchSourceResolutionAuthorityRecheckBacklogConfig,
    ResearchSourceResolutionAuthorityRecheckBacklogInput,
    ResearchSourceResolutionAuthorityRecheckBacklogReport,
    ResearchSourceResolutionAuthorityRecheckBacklogRow,
    build_research_source_resolution_authority_recheck_backlog_report,
    research_source_resolution_authority_recheck_backlog_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(
    index: int,
    *,
    review_bucket: str = "alpha-pass",
    authority_bucket: str | None = None,
    authority_last_checked_at: datetime | None = None,
    contradiction_pressure_score: Decimal = d("0.000000"),
    rule_ambiguity_score: Decimal = d("0.000000"),
    source_availability_score: Decimal = d("1.000000"),
    reviewer_coverage_score: Decimal = d("1.000000"),
    resolution_deadline_at: datetime | None = None,
    reason_codes: tuple[str, ...] = (),
) -> ResearchSourceResolutionAuthorityRecheckBacklogInput:
    return ResearchSourceResolutionAuthorityRecheckBacklogInput(
        review_bucket=review_bucket,
        authority_bucket=authority_bucket or f"authority-{index:03d}",
        private_candidate_reference=(
            f"raw_candidate_id=CAND-{index:03d}; token=secret-{index}"
        ),
        private_market_reference=(
            f"market_id=0xMARKET{index:03d}; market_slug=will-alpha-{index}; "
            f"market_question=Will Alpha resolve {index}?"
        ),
        private_resolution_material=(
            "https://authority.example.test/private?"
            f"dsn=postgres://user:pass@host/db&table=authority_table_{index}; "
            f"wallet=0xabc; order={index}; trade={index}; live feed; source text"
        ),
        authority_last_checked_at=authority_last_checked_at
        if authority_last_checked_at is not None
        else GENERATED_AT - timedelta(minutes=20),
        contradiction_pressure_score=contradiction_pressure_score,
        rule_ambiguity_score=rule_ambiguity_score,
        source_availability_score=source_availability_score,
        reviewer_coverage_score=reviewer_coverage_score,
        resolution_deadline_at=resolution_deadline_at,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchSourceResolutionAuthorityRecheckBacklogInput, ...],
    *,
    config: ResearchSourceResolutionAuthorityRecheckBacklogConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceResolutionAuthorityRecheckBacklogReport:
    return build_research_source_resolution_authority_recheck_backlog_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def test_prioritizes_authority_rechecks_without_public_private_surfaces() -> None:
    backlog_report = report(
        (
            candidate(
                1,
                review_bucket="alpha-pass",
                authority_bucket="authority-pass",
            ),
            candidate(
                2,
                review_bucket="beta-watch",
                authority_bucket="authority-watch",
                authority_last_checked_at=GENERATED_AT - timedelta(hours=12),
                contradiction_pressure_score=d("0.400000"),
                rule_ambiguity_score=d("0.200000"),
                source_availability_score=d("0.600000"),
                reviewer_coverage_score=d("0.800000"),
                resolution_deadline_at=GENERATED_AT + timedelta(hours=24),
                reason_codes=("review_window_open",),
            ),
            candidate(
                3,
                review_bucket="gamma-block",
                authority_bucket="authority-block",
                authority_last_checked_at=GENERATED_AT - timedelta(days=4),
                contradiction_pressure_score=d("0.800000"),
                rule_ambiguity_score=d("0.700000"),
                source_availability_score=d("0.250000"),
                reviewer_coverage_score=d("0.200000"),
                resolution_deadline_at=GENERATED_AT - timedelta(minutes=1),
                reason_codes=("authority_packet_stale",),
            ),
        ),
    )

    assert backlog_report.status == "block"
    assert backlog_report.row_count == d("3.000000")
    assert backlog_report.stale_authority_count == d("2.000000")
    assert backlog_report.contradiction_pressure_count == d("2.000000")
    assert backlog_report.rule_ambiguity_count == d("1.000000")
    assert backlog_report.source_availability_gap_count == d("2.000000")
    assert backlog_report.reviewer_coverage_gap_count == d("1.000000")
    assert backlog_report.deadline_proximity_count == d("2.000000")
    assert backlog_report.pass_count == d("1.000000")
    assert backlog_report.watch_count == d("1.000000")
    assert backlog_report.block_count == d("1.000000")
    assert backlog_report.average_recheck_priority_score == d("0.401570")
    assert backlog_report.max_recheck_priority_score == d("0.841667")

    block_row, watch_row, pass_row = backlog_report.rows
    assert type(block_row) is ResearchSourceResolutionAuthorityRecheckBacklogRow
    assert block_row.review_bucket == "gamma-block"
    assert block_row.status == "block"
    assert block_row.authority_age_seconds == d("345600.000000")
    assert block_row.authority_freshness_score == d("1.000000")
    assert block_row.source_unavailability_score == d("0.750000")
    assert block_row.reviewer_coverage_gap_score == d("0.800000")
    assert block_row.deadline_proximity_score == d("1.000000")
    assert block_row.recheck_priority_score == d("0.841667")
    assert block_row.reason_codes == (
        "authority_freshness_block",
        "authority_recheck_backlog_block",
        "contradiction_pressure_block",
        "deadline_proximity_block",
        "input_authority_packet_stale",
        "reviewer_coverage_block",
        "rule_ambiguity_block",
        "source_availability_block",
    )

    assert watch_row.review_bucket == "beta-watch"
    assert watch_row.status == "watch"
    assert watch_row.authority_age_seconds == d("43200.000000")
    assert watch_row.authority_freshness_score == d("0.478261")
    assert watch_row.source_unavailability_score == d("0.400000")
    assert watch_row.reviewer_coverage_gap_score == d("0.200000")
    assert watch_row.deadline_proximity_score == d("0.500000")
    assert watch_row.recheck_priority_score == d("0.363044")
    assert "input_review_window_open" in watch_row.reason_codes

    assert pass_row.review_bucket == "alpha-pass"
    assert pass_row.status == "pass"
    assert pass_row.recheck_priority_score == d("0.000000")
    assert pass_row.reason_codes == (
        "authority_freshness_clear",
        "authority_recheck_backlog_pass",
        "contradiction_pressure_clear",
        "deadline_proximity_clear",
        "reviewer_coverage_clear",
        "rule_ambiguity_clear",
        "source_availability_clear",
    )

    payload = research_source_resolution_authority_recheck_backlog_report_payload(
        backlog_report,
    )
    encoded = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "raw_candidate_id",
        "cand-001",
        "market_id",
        "market_slug",
        "market_question",
        "will alpha resolve",
        "https://authority.example.test",
        "dsn=postgres",
        "authority_table",
        "token=secret",
        "wallet=0xabc",
        "order=1",
        "trade=1",
        "live feed",
        "source text",
        "private_candidate_reference",
        "private_market_reference",
        "private_resolution_material",
    ):
        assert forbidden not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))


def test_digest_is_deterministic_and_validated_for_report_and_payload() -> None:
    first = report(
        (
            candidate(
                2,
                review_bucket="beta-watch",
                authority_last_checked_at=GENERATED_AT - timedelta(hours=8),
                contradiction_pressure_score=d("0.400000"),
            ),
            candidate(1, review_bucket="alpha-pass"),
        ),
    )
    second = report(
        (
            candidate(1, review_bucket="alpha-pass"),
            candidate(
                2,
                review_bucket="beta-watch",
                authority_last_checked_at=GENERATED_AT - timedelta(hours=8),
                contradiction_pressure_score=d("0.400000"),
            ),
        ),
    )

    payload = research_source_resolution_authority_recheck_backlog_report_payload(first)
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered_payload = dict(payload)
    tampered_payload["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_resolution_authority_recheck_backlog_report_payload(tampered_payload)


def test_decimal_math_uses_fixed_local_context_and_canonicalizes_signed_zero() -> None:
    expected = report(
        (
            candidate(
                1,
                review_bucket="a-low",
                authority_last_checked_at=GENERATED_AT - timedelta(hours=12),
                contradiction_pressure_score=d("-0.000000"),
                rule_ambiguity_score=d("0.200000"),
                source_availability_score=d("0.600000"),
                reviewer_coverage_score=d("0.800000"),
                resolution_deadline_at=GENERATED_AT + timedelta(hours=24),
            ),
            candidate(
                2,
                review_bucket="z-high",
                authority_last_checked_at=GENERATED_AT - timedelta(hours=12),
                contradiction_pressure_score=d("0.006000"),
                rule_ambiguity_score=d("0.200000"),
                source_availability_score=d("0.600000"),
                reviewer_coverage_score=d("0.800000"),
                resolution_deadline_at=GENERATED_AT + timedelta(hours=24),
            ),
        ),
    )

    with localcontext() as ambient:
        ambient.prec = 2
        ambient.rounding = ROUND_DOWN
        actual = report(
            (
                candidate(
                    1,
                    review_bucket="a-low",
                    authority_last_checked_at=GENERATED_AT - timedelta(hours=12),
                    contradiction_pressure_score=d("-0.000000"),
                    rule_ambiguity_score=d("0.200000"),
                    source_availability_score=d("0.600000"),
                    reviewer_coverage_score=d("0.800000"),
                    resolution_deadline_at=GENERATED_AT + timedelta(hours=24),
                ),
                candidate(
                    2,
                    review_bucket="z-high",
                    authority_last_checked_at=GENERATED_AT - timedelta(hours=12),
                    contradiction_pressure_score=d("0.006000"),
                    rule_ambiguity_score=d("0.200000"),
                    source_availability_score=d("0.600000"),
                    reviewer_coverage_score=d("0.800000"),
                    resolution_deadline_at=GENERATED_AT + timedelta(hours=24),
                ),
            ),
        )

    assert actual == expected
    zero_row = next(row for row in actual.rows if row.review_bucket == "a-low")
    assert zero_row.contradiction_pressure_score == d("0.000000")
    assert zero_row.contradiction_pressure_score.is_signed() is False
    assert (
        next(
            row
            for row in actual.payload["rows"]
            if row["review_bucket"] == "a-low"
        )["contradiction_pressure_score"]
        == "0.000000"
    )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("contradiction_pressure_score", d("-0.0000004")),
        ("contradiction_pressure_score", d("1.0000004")),
        ("source_availability_score", d("-0.0000004")),
        ("reviewer_coverage_score", d("1.0000004")),
        ("rule_ambiguity_score", d("NaN")),
        ("rule_ambiguity_score", d("Infinity")),
    ),
)
def test_ratio_validation_uses_raw_bounds_and_rejects_non_finite(
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        candidate(1, **{field_name: value})


def test_payload_schema_is_exact_and_canonical_even_when_resigned() -> None:
    payload = research_source_resolution_authority_recheck_backlog_report_payload(
        report((candidate(1),)),
    )

    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "row_count",
        "stale_authority_count",
        "contradiction_pressure_count",
        "rule_ambiguity_count",
        "source_availability_gap_count",
        "reviewer_coverage_gap_count",
        "deadline_proximity_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_recheck_priority_score",
        "max_recheck_priority_score",
        "status",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["rows"][0]) == (
        "review_bucket",
        "authority_bucket",
        "authority_age_seconds",
        "authority_freshness_score",
        "contradiction_pressure_score",
        "rule_ambiguity_score",
        "source_availability_score",
        "source_unavailability_score",
        "reviewer_coverage_score",
        "reviewer_coverage_gap_score",
        "deadline_proximity_score",
        "recheck_priority_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )

    malformed_payloads: list[dict[str, object]] = []

    extra_report_field = copy.deepcopy(payload)
    extra_report_field["public_note"] = "safe-looking-but-not-canonical"
    malformed_payloads.append(_resign_payload(extra_report_field))

    missing_report_field = copy.deepcopy(payload)
    missing_report_field.pop("deadline_proximity_count")
    malformed_payloads.append(_resign_payload(missing_report_field))

    extra_row_field = copy.deepcopy(payload)
    extra_row_field["rows"][0]["public_note"] = "safe-looking-but-not-canonical"
    malformed_payloads.append(_resign_payload(extra_row_field))

    missing_row_field = copy.deepcopy(payload)
    missing_row_field["rows"][0].pop("authority_age_seconds")
    malformed_payloads.append(_resign_payload(missing_row_field))

    noncanonical_decimal = copy.deepcopy(payload)
    noncanonical_decimal["row_count"] = "1.0"
    malformed_payloads.append(_resign_payload(noncanonical_decimal))

    for malformed_payload in malformed_payloads:
        with pytest.raises(ValueError, match="schema|canonical"):
            research_source_resolution_authority_recheck_backlog_report_payload(
                malformed_payload,
            )


def test_resigned_payload_rejects_noncanonical_report_field_order() -> None:
    payload = research_source_resolution_authority_recheck_backlog_report_payload(
        report((candidate(1),)),
    )
    items = tuple(payload.items())
    reordered_payload = dict((items[1], items[0], *items[2:]))

    with pytest.raises(ValueError, match="canonical|order|schema"):
        research_source_resolution_authority_recheck_backlog_report_payload(
            _resign_payload(reordered_payload),
        )


def test_resigned_payload_rejects_noncanonical_row_field_order() -> None:
    payload = research_source_resolution_authority_recheck_backlog_report_payload(
        report((candidate(1),)),
    )
    row_items = tuple(payload["rows"][0].items())
    reordered_payload = copy.deepcopy(payload)
    reordered_payload["rows"][0] = dict((row_items[1], row_items[0], *row_items[2:]))

    with pytest.raises(ValueError, match="canonical|order|schema"):
        research_source_resolution_authority_recheck_backlog_report_payload(
            _resign_payload(reordered_payload),
        )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda payload: payload.__setitem__("stale_authority_count", "0.000000"),
        lambda payload: payload.__setitem__(
            "average_recheck_priority_score",
            "0.999999",
        ),
        lambda payload: payload.__setitem__("status", "pass"),
        lambda payload: payload.__setitem__(
            "reason_codes",
            ["authority_recheck_backlog_pass"],
        ),
        lambda payload: payload["rows"].reverse(),
        lambda payload: payload["rows"][0].__setitem__(
            "source_unavailability_score",
            "0.000000",
        ),
        lambda payload: payload["rows"][0].__setitem__(
            "recheck_priority_score",
            "0.000000",
        ),
        lambda payload: payload["rows"][0].__setitem__("status", "pass"),
        lambda payload: payload["rows"][0].__setitem__(
            "reason_codes",
            ["authority_recheck_backlog_pass"],
        ),
    ),
)
def test_resigned_payload_recomputes_all_derived_values(
    mutation: object,
) -> None:
    payload = research_source_resolution_authority_recheck_backlog_report_payload(
        report(
            (
                candidate(1, review_bucket="alpha-pass"),
                candidate(
                    2,
                    review_bucket="beta-block",
                    authority_last_checked_at=GENERATED_AT - timedelta(days=4),
                    contradiction_pressure_score=d("0.800000"),
                    rule_ambiguity_score=d("0.700000"),
                    source_availability_score=d("0.250000"),
                    reviewer_coverage_score=d("0.200000"),
                    resolution_deadline_at=GENERATED_AT - timedelta(minutes=1),
                ),
            ),
        ),
    )
    tampered = copy.deepcopy(payload)
    mutation(tampered)

    with pytest.raises(ValueError, match="must (?:match|equal)|canonical|order"):
        research_source_resolution_authority_recheck_backlog_report_payload(
            _resign_payload(tampered),
        )


def test_resigned_payload_rederives_status_reasons_and_counts_from_row_scores() -> None:
    payload = research_source_resolution_authority_recheck_backlog_report_payload(
        report((candidate(1),)),
    )
    tampered = copy.deepcopy(payload)
    block_reason_codes = [
        "authority_freshness_block",
        "authority_recheck_backlog_block",
        "contradiction_pressure_block",
        "deadline_proximity_block",
        "reviewer_coverage_block",
        "rule_ambiguity_block",
        "source_availability_block",
    ]
    tampered.update(
        {
            "stale_authority_count": "1.000000",
            "contradiction_pressure_count": "1.000000",
            "rule_ambiguity_count": "1.000000",
            "source_availability_gap_count": "1.000000",
            "reviewer_coverage_gap_count": "1.000000",
            "deadline_proximity_count": "1.000000",
            "pass_count": "0.000000",
            "block_count": "1.000000",
            "status": "block",
            "reason_codes": block_reason_codes,
        },
    )
    tampered["rows"][0]["status"] = "block"
    tampered["rows"][0]["reason_codes"] = block_reason_codes

    with pytest.raises(ValueError, match="must (?:match|equal)|canonical|order"):
        research_source_resolution_authority_recheck_backlog_report_payload(
            _resign_payload(tampered),
        )


def test_sort_order_is_stable_with_explicit_status_and_identifier_tiebreaks() -> None:
    block = candidate(
        1,
        review_bucket="zeta-block",
        authority_bucket="authority-z",
        contradiction_pressure_score=d("0.700000"),
    )
    watch = candidate(
        2,
        review_bucket="alpha-watch",
        authority_bucket="authority-a",
        contradiction_pressure_score=d("0.400000"),
        rule_ambiguity_score=d("0.300000"),
    )
    tie_b = candidate(
        3,
        review_bucket="same-watch",
        authority_bucket="authority-b",
        contradiction_pressure_score=d("0.400000"),
        rule_ambiguity_score=d("0.300000"),
    )
    tie_a = candidate(
        4,
        review_bucket="same-watch",
        authority_bucket="authority-a",
        contradiction_pressure_score=d("0.400000"),
        rule_ambiguity_score=d("0.300000"),
    )

    first = report((tie_b, watch, block, tie_a))
    second = report((tie_a, block, tie_b, watch))

    expected_keys = (
        ("zeta-block", "authority-z"),
        ("alpha-watch", "authority-a"),
        ("same-watch", "authority-a"),
        ("same-watch", "authority-b"),
    )
    assert tuple(
        (row.review_bucket, row.authority_bucket) for row in first.rows
    ) == expected_keys
    assert first.rows == second.rows
    assert first.derived_validation_digest == second.derived_validation_digest


def test_validation_rejects_bad_numerics_flags_statuses_and_future_authority() -> None:
    with pytest.raises(ValueError, match="fresh_authority_age_seconds"):
        ResearchSourceResolutionAuthorityRecheckBacklogConfig(
            fresh_authority_age_seconds=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="watch_priority_score"):
        ResearchSourceResolutionAuthorityRecheckBacklogConfig(
            watch_priority_score=DecimalSubclass("0.250000"),
        )
    with pytest.raises(ValueError, match="block_priority_score"):
        ResearchSourceResolutionAuthorityRecheckBacklogConfig(
            watch_priority_score=d("0.700000"),
            block_priority_score=d("0.500000"),
        )
    config = ResearchSourceResolutionAuthorityRecheckBacklogConfig()
    object.__setattr__(config, "watch_priority_score", d("2.000000"))
    with pytest.raises(ValueError, match="watch_priority_score"):
        report((candidate(1),), config=config)
    with pytest.raises(ValueError, match="contradiction_pressure_score"):
        candidate(1, contradiction_pressure_score=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(1), paper_only=False)
    with pytest.raises(ValueError, match="authority_last_checked_at"):
        report(
            (
                candidate(
                    1,
                    authority_last_checked_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_resolution_authority_recheck_backlog_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="status"):
        replace(report((candidate(1),)).rows[0], status="blocked")


def test_public_dataclasses_are_frozen_and_payload_requires_hard_flags() -> None:
    backlog_report = report((candidate(1),))
    payload = research_source_resolution_authority_recheck_backlog_report_payload(
        backlog_report,
    )

    assert backlog_report.paper_only is True
    assert backlog_report.report_only is True
    assert backlog_report.readonly is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(FrozenInstanceError):
        backlog_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        backlog_report.rows[0].recheck_priority_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="recheck_priority_score"):
        replace(backlog_report.rows[0], recheck_priority_score=d("0.750000"))

    bad_payload = dict(payload)
    bad_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_source_resolution_authority_recheck_backlog_report_payload(bad_payload)

    unsafe_payload = dict(payload)
    unsafe_payload["market_slug"] = "unsafe"
    with pytest.raises(ValueError, match="unsafe"):
        research_source_resolution_authority_recheck_backlog_report_payload(unsafe_payload)


def test_object_setattr_tampering_is_rechecked_even_when_report_is_resigned() -> None:
    backlog_report = report((candidate(1),))
    tampered_payload = dict(backlog_report.payload)
    tampered_payload["paper_only"] = False
    tampered_payload = _resign_payload(tampered_payload)

    object.__setattr__(backlog_report, "paper_only", False)
    object.__setattr__(
        backlog_report,
        "derived_validation_digest",
        tampered_payload["derived_validation_digest"],
    )

    with pytest.raises(ValueError, match="paper_only"):
        backlog_report.payload


def test_object_setattr_extra_public_attributes_are_rejected() -> None:
    backlog_report = report((candidate(1),))
    object.__setattr__(backlog_report, "market_slug", "unsafe")

    with pytest.raises(ValueError, match="tampered|unsafe|unexpected"):
        backlog_report.payload


def test_public_dataclasses_are_exact_frozen_and_non_subclassable() -> None:
    instances = (
        ResearchSourceResolutionAuthorityRecheckBacklogConfig(),
        candidate(1),
        report((candidate(1),)).rows[0],
        report((candidate(1),)),
    )

    for instance in instances:
        assert instance.__dataclass_params__.frozen is True
        with pytest.raises(FrozenInstanceError):
            instance.paper_only = False
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Derived{type(instance).__name__}", (type(instance),), {})


def test_owned_module_has_no_db_network_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_resolution_authority_recheck_backlog_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "private_key",
        "open(",
        "connect(",
    )

    assert all(term not in source for term in forbidden_terms)


def test_public_api_is_exactly_the_report_only_surface() -> None:
    from polymarket_alpha_lab import (
        research_source_resolution_authority_recheck_backlog_report as api,
    )

    assert api.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_RECHECK_BACKLOG_REPORT_CONFIG_VERSION",
        "ResearchSourceResolutionAuthorityRecheckBacklogConfig",
        "ResearchSourceResolutionAuthorityRecheckBacklogInput",
        "ResearchSourceResolutionAuthorityRecheckBacklogReport",
        "ResearchSourceResolutionAuthorityRecheckBacklogRow",
        "build_research_source_resolution_authority_recheck_backlog_report",
        "research_source_resolution_authority_recheck_backlog_report_payload",
    )


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _resign_payload(payload: dict[str, object]) -> dict[str, object]:
    unsigned_payload = copy.deepcopy(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    payload["derived_validation_digest"] = hashlib.sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return payload
