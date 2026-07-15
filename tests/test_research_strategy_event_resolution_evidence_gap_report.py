from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
import json

import pytest

from polymarket_alpha_lab.research_strategy_event_resolution_evidence_gap_report import (
    ResearchStrategyEventResolutionEvidenceGapConfig,
    ResearchStrategyEventResolutionEvidenceGapInput,
    build_research_strategy_event_resolution_evidence_gap_report,
    research_strategy_event_resolution_evidence_gap_report_digest,
    research_strategy_event_resolution_evidence_gap_report_from_payload,
    research_strategy_event_resolution_evidence_gap_report_payload,
)


GENERATED_AT = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def event_input(
    private_event_ref: str,
    *,
    private_source_refs: tuple[str, ...],
    required_evidence_count: Decimal,
    verifiable_evidence_count: Decimal,
    authoritative_source_count: Decimal,
    fresh_source_count: Decimal,
    conflicting_source_count: Decimal,
    latest_evidence_age_hours: int,
) -> ResearchStrategyEventResolutionEvidenceGapInput:
    return ResearchStrategyEventResolutionEvidenceGapInput(
        private_event_ref=private_event_ref,
        private_source_refs=private_source_refs,
        required_evidence_count=required_evidence_count,
        verifiable_evidence_count=verifiable_evidence_count,
        authoritative_source_count=authoritative_source_count,
        fresh_source_count=fresh_source_count,
        conflicting_source_count=conflicting_source_count,
        latest_evidence_at=GENERATED_AT
        - timedelta(hours=latest_evidence_age_hours),
    )


def test_report_scores_and_ranks_resolution_evidence_gaps_without_leaking_refs() -> None:
    report = build_research_strategy_event_resolution_evidence_gap_report(
        (
            event_input(
                "private-pass-event",
                private_source_refs=(
                    "https://official.example/pass",
                    "private-pass-source-2",
                    "private-pass-source-3",
                    "private-pass-source-4",
                ),
                required_evidence_count=d("4"),
                verifiable_evidence_count=d("4"),
                authoritative_source_count=d("3"),
                fresh_source_count=d("4"),
                conflicting_source_count=d("0"),
                latest_evidence_age_hours=2,
            ),
            event_input(
                "private-block-event",
                private_source_refs=(
                    "secret-block-source-1",
                    "secret-block-source-2",
                    "secret-block-source-3",
                ),
                required_evidence_count=d("4"),
                verifiable_evidence_count=d("1"),
                authoritative_source_count=d("0"),
                fresh_source_count=d("0"),
                conflicting_source_count=d("1"),
                latest_evidence_age_hours=48,
            ),
            event_input(
                "private-watch-event",
                private_source_refs=(
                    "confidential-watch-source-1",
                    "confidential-watch-source-2",
                    "confidential-watch-source-3",
                    "confidential-watch-source-4",
                ),
                required_evidence_count=d("4"),
                verifiable_evidence_count=d("3"),
                authoritative_source_count=d("2"),
                fresh_source_count=d("2"),
                conflicting_source_count=d("0"),
                latest_evidence_age_hours=6,
            ),
        ),
        config=ResearchStrategyEventResolutionEvidenceGapConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.status == "block"
    assert report.event_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.review_required_count == d("2.000000")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.manual_review_rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.public_row_id for row in report.rows) == (
        "event_resolution_evidence_gap_000001",
        "event_resolution_evidence_gap_000002",
        "event_resolution_evidence_gap_000003",
    )
    assert report.rows[0].evidence_coverage_ratio == d("0.250000")
    assert report.rows[0].source_authority_ratio == d("0.000000")
    assert report.rows[0].evidence_freshness_score == d("0.000000")
    assert report.rows[0].conflict_ratio == d("1.000000")
    assert report.rows[0].manual_review_priority_score == d("0.912500")
    assert len(report.derived_validation_digest) == 64

    payload = research_strategy_event_resolution_evidence_gap_report_payload(report)
    serialized = repr(payload).lower()
    for secret in (
        "private-pass-event",
        "private-block-event",
        "private-watch-event",
        "official.example",
        "secret-block-source",
        "confidential-watch-source",
    ):
        assert secret not in serialized
    assert payload["rows"][0]["manual_review_rank"] == "1.000000"
    assert payload["rows"][0]["manual_review_priority_score"] == "0.912500"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True


def test_resigned_payload_rederives_every_status_reason_score_count_rank_and_aggregate() -> None:
    report = build_research_strategy_event_resolution_evidence_gap_report(
        (
            event_input(
                "private-block-event",
                private_source_refs=("source-a", "source-b"),
                required_evidence_count=d("4"),
                verifiable_evidence_count=d("1"),
                authoritative_source_count=d("0"),
                fresh_source_count=d("0"),
                conflicting_source_count=d("1"),
                latest_evidence_age_hours=48,
            ),
        ),
        config=ResearchStrategyEventResolutionEvidenceGapConfig(),
        generated_at=GENERATED_AT,
    )
    payload = research_strategy_event_resolution_evidence_gap_report_payload(report)

    assert set(payload) == {
        "generated_at",
        "config_version",
        "config",
        "status",
        "event_count",
        "pass_count",
        "watch_count",
        "block_count",
        "review_required_count",
        "average_evidence_coverage_ratio",
        "average_source_authority_ratio",
        "average_evidence_freshness_score",
        "average_conflict_ratio",
        "average_manual_review_priority_score",
        "max_manual_review_priority_score",
        "total_conflicting_source_count",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    restored = research_strategy_event_resolution_evidence_gap_report_from_payload(
        payload
    )
    assert research_strategy_event_resolution_evidence_gap_report_payload(
        restored
    ) == payload

    mutations = (
        ("status", lambda item: item.__setitem__("status", "pass")),
        (
            "reason_codes",
            lambda item: item["rows"][0].__setitem__(
                "reason_codes",
                ["event_resolution_evidence_sufficient"],
            ),
        ),
        (
            "manual_review_priority_score",
            lambda item: item["rows"][0].__setitem__(
                "manual_review_priority_score",
                "0.000000",
            ),
        ),
        ("block_count", lambda item: item.__setitem__("block_count", "0.000000")),
        (
            "manual_review_rank",
            lambda item: item["rows"][0].__setitem__(
                "manual_review_rank",
                "2.000000",
            ),
        ),
        (
            "average_manual_review_priority_score",
            lambda item: item.__setitem__(
                "average_manual_review_priority_score",
                "0.000000",
            ),
        ),
    )
    for expected_error, mutate in mutations:
        tampered = deepcopy(payload)
        mutate(tampered)
        tampered["derived_validation_digest"] = (
            research_strategy_event_resolution_evidence_gap_report_digest(tampered)
        )
        with pytest.raises(ValueError, match=expected_error):
            research_strategy_event_resolution_evidence_gap_report_from_payload(
                tampered
            )


def test_decimal_validation_uses_raw_bounds_before_six_decimal_quantization() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        event_input(
            "float-count",
            private_source_refs=("source-a",),
            required_evidence_count=1,  # type: ignore[arg-type]
            verifiable_evidence_count=d("1"),
            authoritative_source_count=d("1"),
            fresh_source_count=d("1"),
            conflicting_source_count=d("0"),
            latest_evidence_age_hours=1,
        )
    with pytest.raises(ValueError, match="finite"):
        ResearchStrategyEventResolutionEvidenceGapConfig(
            coverage_gap_weight=Decimal("NaN")
        )
    with pytest.raises(ValueError, match="signed zero"):
        ResearchStrategyEventResolutionEvidenceGapConfig(
            conflict_weight=Decimal("-0")
        )
    with pytest.raises(ValueError, match="weights"):
        ResearchStrategyEventResolutionEvidenceGapConfig(
            coverage_gap_weight=d("0.3500004")
        )
    with pytest.raises(ValueError, match="coverage"):
        ResearchStrategyEventResolutionEvidenceGapConfig(
            pass_min_evidence_coverage_ratio=d("0.4999996"),
            watch_min_evidence_coverage_ratio=d("0.5000004"),
        )
    with pytest.raises(ValueError, match="conflict"):
        ResearchStrategyEventResolutionEvidenceGapConfig(
            pass_max_conflict_ratio=d("0.1000004"),
            watch_max_conflict_ratio=d("0.0999996"),
        )


def test_resigned_object_setattr_mutations_are_revalidated_at_public_boundaries() -> None:
    valid_input = event_input(
        "private-valid-event",
        private_source_refs=("source-a",),
        required_evidence_count=d("1"),
        verifiable_evidence_count=d("1"),
        authoritative_source_count=d("1"),
        fresh_source_count=d("1"),
        conflicting_source_count=d("0"),
        latest_evidence_age_hours=1,
    )

    tampered_config = ResearchStrategyEventResolutionEvidenceGapConfig()
    object.__setattr__(tampered_config, "paper_only", False)
    with pytest.raises(ValueError, match="config"):
        build_research_strategy_event_resolution_evidence_gap_report(
            (valid_input,),
            config=tampered_config,
            generated_at=GENERATED_AT,
        )

    tampered_input = event_input(
        "private-mutated-event",
        private_source_refs=("source-a",),
        required_evidence_count=d("1"),
        verifiable_evidence_count=d("1"),
        authoritative_source_count=d("1"),
        fresh_source_count=d("1"),
        conflicting_source_count=d("0"),
        latest_evidence_age_hours=1,
    )
    object.__setattr__(tampered_input, "private_event_ref", " private-mutated-event ")
    with pytest.raises(ValueError, match="private_event_ref"):
        build_research_strategy_event_resolution_evidence_gap_report(
            (tampered_input,),
            config=ResearchStrategyEventResolutionEvidenceGapConfig(),
            generated_at=GENERATED_AT,
        )

    report = build_research_strategy_event_resolution_evidence_gap_report(
        (valid_input,),
        config=ResearchStrategyEventResolutionEvidenceGapConfig(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(report.rows[0], "paper_only", False)
    object.__setattr__(
        report,
        "derived_validation_digest",
        research_strategy_event_resolution_evidence_gap_report_digest(report),
    )
    with pytest.raises(ValueError, match="row"):
        research_strategy_event_resolution_evidence_gap_report_payload(report)

    report = build_research_strategy_event_resolution_evidence_gap_report(
        (valid_input,),
        config=ResearchStrategyEventResolutionEvidenceGapConfig(),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(report.reason_code_counts[0], "paper_only", False)
    object.__setattr__(
        report,
        "derived_validation_digest",
        research_strategy_event_resolution_evidence_gap_report_digest(report),
    )
    with pytest.raises(ValueError, match="reason count"):
        research_strategy_event_resolution_evidence_gap_report_payload(report)


def test_public_payloads_use_strict_key_order_and_sha256_canonical_digest() -> None:
    report = build_research_strategy_event_resolution_evidence_gap_report(
        (
            event_input(
                "private-key-order-event",
                private_source_refs=("source-a",),
                required_evidence_count=d("1"),
                verifiable_evidence_count=d("1"),
                authoritative_source_count=d("1"),
                fresh_source_count=d("1"),
                conflicting_source_count=d("0"),
                latest_evidence_age_hours=1,
            ),
        ),
        config=ResearchStrategyEventResolutionEvidenceGapConfig(),
        generated_at=GENERATED_AT,
    )
    payload = research_strategy_event_resolution_evidence_gap_report_payload(report)

    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "config",
        "status",
        "event_count",
        "pass_count",
        "watch_count",
        "block_count",
        "review_required_count",
        "average_evidence_coverage_ratio",
        "average_source_authority_ratio",
        "average_evidence_freshness_score",
        "average_conflict_ratio",
        "average_manual_review_priority_score",
        "max_manual_review_priority_score",
        "total_conflicting_source_count",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    )
    assert tuple(payload["config"]) == (
        "config_version",
        "freshness_target_hours",
        "pass_min_evidence_coverage_ratio",
        "watch_min_evidence_coverage_ratio",
        "pass_min_source_authority_ratio",
        "watch_min_source_authority_ratio",
        "pass_min_evidence_freshness_score",
        "watch_min_evidence_freshness_score",
        "pass_max_conflict_ratio",
        "watch_max_conflict_ratio",
        "coverage_gap_weight",
        "authority_gap_weight",
        "freshness_gap_weight",
        "conflict_weight",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["rows"][0]) == (
        "public_row_id",
        "manual_review_rank",
        "source_count",
        "required_evidence_count",
        "verifiable_evidence_count",
        "authoritative_source_count",
        "fresh_source_count",
        "conflicting_source_count",
        "latest_evidence_at",
        "latest_evidence_age_hours",
        "evidence_coverage_ratio",
        "source_authority_ratio",
        "fresh_source_ratio",
        "latest_evidence_recency_score",
        "evidence_freshness_score",
        "conflict_ratio",
        "manual_review_priority_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["reason_code_counts"][0]) == (
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    )

    unsigned_payload = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert payload["derived_validation_digest"] == sha256(
        encoded.encode("utf-8")
    ).hexdigest()

    def move_first_key_to_end(mapping: dict[str, object]) -> dict[str, object]:
        reordered = dict(mapping)
        first_key = next(iter(reordered))
        value = reordered.pop(first_key)
        reordered[first_key] = value
        return reordered

    mutations = (
        lambda item: move_first_key_to_end(item),
        lambda item: item.__setitem__("config", move_first_key_to_end(item["config"])),
        lambda item: item["rows"].__setitem__(
            0,
            move_first_key_to_end(item["rows"][0]),
        ),
        lambda item: item["reason_code_counts"].__setitem__(
            0,
            move_first_key_to_end(item["reason_code_counts"][0]),
        ),
    )
    for mutate in mutations:
        tampered = deepcopy(payload)
        tampered = mutate(tampered) or tampered
        with pytest.raises(ValueError, match="schema"):
            research_strategy_event_resolution_evidence_gap_report_from_payload(
                tampered
            )


def test_equal_status_score_rows_use_public_tie_breaks_for_reconstruction() -> None:
    one_source = event_input(
        "private-z-one-source-event",
        private_source_refs=("source-one",),
        required_evidence_count=d("1"),
        verifiable_evidence_count=d("1"),
        authoritative_source_count=d("1"),
        fresh_source_count=d("1"),
        conflicting_source_count=d("0"),
        latest_evidence_age_hours=0,
    )
    two_sources = event_input(
        "private-a-two-source-event",
        private_source_refs=("source-two-a", "source-two-b"),
        required_evidence_count=d("2"),
        verifiable_evidence_count=d("2"),
        authoritative_source_count=d("2"),
        fresh_source_count=d("2"),
        conflicting_source_count=d("0"),
        latest_evidence_age_hours=0,
    )

    report = build_research_strategy_event_resolution_evidence_gap_report(
        (one_source, two_sources),
        config=ResearchStrategyEventResolutionEvidenceGapConfig(),
        generated_at=GENERATED_AT,
    )
    payload = research_strategy_event_resolution_evidence_gap_report_payload(report)

    assert tuple(row["manual_review_priority_score"] for row in payload["rows"]) == (
        "0.000000",
        "0.000000",
    )
    assert tuple(row["source_count"] for row in payload["rows"]) == (
        "1.000000",
        "2.000000",
    )

    tampered = deepcopy(payload)
    swapped_rows = [dict(tampered["rows"][1]), dict(tampered["rows"][0])]
    for index, row in enumerate(swapped_rows, start=1):
        row["public_row_id"] = f"event_resolution_evidence_gap_{index:06d}"
        row["manual_review_rank"] = f"{index}.000000"
    tampered["rows"] = swapped_rows
    tampered["derived_validation_digest"] = (
        research_strategy_event_resolution_evidence_gap_report_digest(tampered)
    )

    with pytest.raises(ValueError, match="rows"):
        research_strategy_event_resolution_evidence_gap_report_from_payload(tampered)


def test_empty_report_and_tied_rows_are_canonical_frozen_and_order_independent() -> None:
    config = ResearchStrategyEventResolutionEvidenceGapConfig()
    empty = build_research_strategy_event_resolution_evidence_gap_report(
        (),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert empty.status == "no_inputs"
    assert empty.event_count == d("0.000000")
    assert empty.review_required_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == ("event_resolution_evidence_gap_no_inputs",)
    assert empty.reason_code_counts[0].count == d("1.000000")
    assert empty.reason_code_counts[0].row_ratio == d("0.000000")
    assert research_strategy_event_resolution_evidence_gap_report_payload(
        research_strategy_event_resolution_evidence_gap_report_from_payload(
            research_strategy_event_resolution_evidence_gap_report_payload(empty)
        )
    ) == research_strategy_event_resolution_evidence_gap_report_payload(empty)

    first = event_input(
        "private-event-a",
        private_source_refs=("private-source-a",),
        required_evidence_count=d("2"),
        verifiable_evidence_count=d("1"),
        authoritative_source_count=d("1"),
        fresh_source_count=d("1"),
        conflicting_source_count=d("0"),
        latest_evidence_age_hours=4,
    )
    second = event_input(
        "private-event-b",
        private_source_refs=("private-source-b",),
        required_evidence_count=d("2"),
        verifiable_evidence_count=d("1"),
        authoritative_source_count=d("1"),
        fresh_source_count=d("1"),
        conflicting_source_count=d("0"),
        latest_evidence_age_hours=4,
    )
    forward = build_research_strategy_event_resolution_evidence_gap_report(
        (first, second),
        config=config,
        generated_at=GENERATED_AT,
    )
    reverse = build_research_strategy_event_resolution_evidence_gap_report(
        (second, first),
        config=config,
        generated_at=GENERATED_AT,
    )

    assert research_strategy_event_resolution_evidence_gap_report_payload(
        forward
    ) == research_strategy_event_resolution_evidence_gap_report_payload(reverse)
    assert "private-event-a" not in repr(first)
    assert "private-source-a" not in repr(first)
    with pytest.raises(FrozenInstanceError):
        forward.status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(ResearchStrategyEventResolutionEvidenceGapConfig):
            pass


def test_status_uses_raw_derived_ratios_before_display_quantization() -> None:
    report = build_research_strategy_event_resolution_evidence_gap_report(
        (
            event_input(
                "raw-bound-event",
                private_source_refs=("source-a", "source-b"),
                required_evidence_count=d("3"),
                verifiable_evidence_count=d("2"),
                authoritative_source_count=d("2"),
                fresh_source_count=d("2"),
                conflicting_source_count=d("0"),
                latest_evidence_age_hours=0,
            ),
        ),
        config=ResearchStrategyEventResolutionEvidenceGapConfig(
            pass_min_evidence_coverage_ratio=d("0.8000000"),
            watch_min_evidence_coverage_ratio=d("0.6666667"),
        ),
        generated_at=GENERATED_AT,
    )

    row = report.rows[0]
    assert row.evidence_coverage_ratio == d("0.666667")
    assert report.config.watch_min_evidence_coverage_ratio == d("0.666667")
    assert row.status == "block"
    assert row.reason_codes[0] == "verifiable_evidence_coverage_block"


def test_event_with_no_source_evidence_is_reported_without_fake_freshness() -> None:
    report = build_research_strategy_event_resolution_evidence_gap_report(
        (
            ResearchStrategyEventResolutionEvidenceGapInput(
                private_event_ref="private-no-evidence-event",
                private_source_refs=(),
                required_evidence_count=d("2"),
                verifiable_evidence_count=d("0"),
                authoritative_source_count=d("0"),
                fresh_source_count=d("0"),
                conflicting_source_count=d("0"),
                latest_evidence_at=None,
            ),
        ),
        config=ResearchStrategyEventResolutionEvidenceGapConfig(),
        generated_at=GENERATED_AT,
    )

    row = report.rows[0]
    assert row.source_count == d("0.000000")
    assert row.latest_evidence_at is None
    assert row.latest_evidence_age_hours is None
    assert row.evidence_coverage_ratio == d("0.000000")
    assert row.source_authority_ratio == d("0.000000")
    assert row.evidence_freshness_score == d("0.000000")
    assert row.conflict_ratio == d("0.000000")
    assert row.manual_review_priority_score == d("0.850000")
    assert row.status == "block"
    assert row.reason_codes == (
        "verifiable_evidence_coverage_block",
        "source_authority_block",
        "evidence_freshness_block",
    )

    payload = research_strategy_event_resolution_evidence_gap_report_payload(report)
    assert payload["rows"][0]["latest_evidence_at"] is None
    assert payload["rows"][0]["latest_evidence_age_hours"] is None
    assert research_strategy_event_resolution_evidence_gap_report_payload(
        research_strategy_event_resolution_evidence_gap_report_from_payload(payload)
    ) == payload
