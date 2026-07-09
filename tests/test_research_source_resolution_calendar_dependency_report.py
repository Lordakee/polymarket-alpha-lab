from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_resolution_calendar_dependency_report import (
    ResearchSourceResolutionCalendarDependencyConfig,
    ResearchSourceResolutionCalendarDependencyInput,
    ResearchSourceResolutionCalendarDependencyReport,
    ResearchSourceResolutionCalendarDependencyRow,
    build_research_source_resolution_calendar_dependency_report,
    research_source_resolution_calendar_dependency_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def dependency(
    index: int,
    *,
    review_bucket: str = "alpha-pass",
    evidence_bucket: str | None = None,
    depends_on_dated_release: bool = False,
    depends_on_scheduled_decision: bool = False,
    depends_on_event_window: bool = False,
    timing_ambiguity_unresolved: bool = False,
    calendar_observed_at: datetime | None = None,
    dependency_scheduled_at: datetime | None = None,
    event_window_starts_at: datetime | None = None,
    event_window_ends_at: datetime | None = None,
    timing_clarity_score: Decimal = d("1.000000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchSourceResolutionCalendarDependencyInput:
    return ResearchSourceResolutionCalendarDependencyInput(
        review_bucket=review_bucket,
        evidence_bucket=evidence_bucket or f"evidence-{index:03d}",
        private_candidate_reference=(
            f"raw_candidate_id=CAND-{index:03d}; token=secret-{index}"
        ),
        private_market_reference=(
            f"market_id=0xMARKET{index:03d}; market_slug=will-alpha-{index}; "
            f"market_question=Will Alpha resolve {index}?"
        ),
        private_source_material=(
            "https://calendar.example.test/private?"
            f"dsn=postgres://user:pass@host/db&table=calendar_table_{index}; "
            f"wallet=0xabc; order={index}; trade={index}; live feed; source text"
        ),
        depends_on_dated_release=depends_on_dated_release,
        depends_on_scheduled_decision=depends_on_scheduled_decision,
        depends_on_event_window=depends_on_event_window,
        timing_ambiguity_unresolved=timing_ambiguity_unresolved,
        calendar_observed_at=calendar_observed_at
        if calendar_observed_at is not None
        else GENERATED_AT - timedelta(minutes=20),
        dependency_scheduled_at=dependency_scheduled_at,
        event_window_starts_at=event_window_starts_at,
        event_window_ends_at=event_window_ends_at,
        timing_clarity_score=timing_clarity_score,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchSourceResolutionCalendarDependencyInput, ...],
    *,
    config: ResearchSourceResolutionCalendarDependencyConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceResolutionCalendarDependencyReport:
    return build_research_source_resolution_calendar_dependency_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def test_report_scores_calendar_dependencies_without_public_private_surfaces() -> None:
    calendar_report = report(
        (
            dependency(
                1,
                review_bucket="alpha-pass",
                evidence_bucket="evidence-pass",
            ),
            dependency(
                2,
                review_bucket="beta-watch",
                evidence_bucket="evidence-watch",
                depends_on_dated_release=True,
                depends_on_scheduled_decision=True,
                calendar_observed_at=GENERATED_AT - timedelta(hours=12),
                dependency_scheduled_at=GENERATED_AT + timedelta(hours=4),
                timing_clarity_score=d("0.800000"),
                reason_codes=("release_pending",),
            ),
            dependency(
                3,
                review_bucket="gamma-block",
                evidence_bucket="evidence-block",
                depends_on_dated_release=True,
                depends_on_scheduled_decision=True,
                depends_on_event_window=True,
                timing_ambiguity_unresolved=True,
                calendar_observed_at=GENERATED_AT - timedelta(days=4),
                timing_clarity_score=d("0.300000"),
                reason_codes=("calendar_missing",),
            ),
        ),
    )

    assert calendar_report.status == "block"
    assert calendar_report.row_count == d("3.000000")
    assert calendar_report.dated_release_dependency_count == d("2.000000")
    assert calendar_report.scheduled_decision_dependency_count == d("2.000000")
    assert calendar_report.event_window_dependency_count == d("1.000000")
    assert calendar_report.stale_calendar_count == d("1.000000")
    assert calendar_report.unresolved_timing_ambiguity_count == d("1.000000")
    assert calendar_report.pass_count == d("1.000000")
    assert calendar_report.watch_count == d("1.000000")
    assert calendar_report.block_count == d("1.000000")
    assert calendar_report.average_dependency_score == d("0.513333")
    assert calendar_report.max_dependency_score == d("1.000000")

    pass_row, watch_row, block_row = calendar_report.rows
    assert type(pass_row) is ResearchSourceResolutionCalendarDependencyRow
    assert pass_row.review_bucket == "alpha-pass"
    assert pass_row.status == "pass"
    assert pass_row.active_calendar_dependency_count == d("0.000000")
    assert pass_row.calendar_age_seconds == d("1200.000000")
    assert pass_row.stale_calendar_score == d("0.000000")
    assert pass_row.unresolved_timing_ambiguity_score == d("0.000000")
    assert pass_row.dependency_score == d("0.000000")
    assert pass_row.reason_codes == (
        "calendar_dependency_pass",
        "calendar_fresh",
        "no_calendar_dependency",
        "timing_clarity_clear",
    )

    assert watch_row.review_bucket == "beta-watch"
    assert watch_row.status == "watch"
    assert watch_row.active_calendar_dependency_count == d("2.000000")
    assert watch_row.calendar_age_seconds == d("43200.000000")
    assert watch_row.stale_calendar_score == d("0.500000")
    assert watch_row.unresolved_timing_ambiguity_score == d("0.200000")
    assert watch_row.dependency_score == d("0.540000")
    assert watch_row.reason_codes == (
        "calendar_age_watch",
        "calendar_dependency_watch",
        "dated_release_dependency",
        "input_release_pending",
        "scheduled_decision_dependency",
        "timing_clarity_clear",
    )

    assert block_row.review_bucket == "gamma-block"
    assert block_row.status == "block"
    assert block_row.active_calendar_dependency_count == d("3.000000")
    assert block_row.calendar_age_seconds == d("345600.000000")
    assert block_row.stale_calendar_score == d("1.000000")
    assert block_row.unresolved_timing_ambiguity_score == d("1.000000")
    assert block_row.dependency_score == d("1.000000")
    assert block_row.reason_codes == (
        "calendar_dependency_block",
        "calendar_stale",
        "dated_release_dependency",
        "event_window_dependency",
        "event_window_missing",
        "input_calendar_missing",
        "scheduled_anchor_missing",
        "scheduled_decision_dependency",
        "timing_ambiguity_unresolved",
    )

    payload = research_source_resolution_calendar_dependency_report_payload(
        calendar_report,
    )
    encoded = json.dumps(payload, sort_keys=True).lower()

    for forbidden in (
        "raw_candidate_id",
        "cand-001",
        "market_id",
        "market_slug",
        "market_question",
        "will alpha resolve",
        "https://calendar.example.test",
        "dsn=postgres",
        "calendar_table",
        "token=secret",
        "wallet=0xabc",
        "order=1",
        "trade=1",
        "live feed",
        "source text",
        "private_candidate_reference",
        "private_market_reference",
        "private_source_material",
    ):
        assert forbidden not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))


def test_digest_is_deterministic_and_validated_for_report_and_payload() -> None:
    first = report(
        (
            dependency(
                2,
                review_bucket="beta-watch",
                depends_on_dated_release=True,
                calendar_observed_at=GENERATED_AT - timedelta(hours=8),
                dependency_scheduled_at=GENERATED_AT + timedelta(days=1),
            ),
            dependency(1, review_bucket="alpha-pass"),
        ),
    )
    second = report(
        (
            dependency(1, review_bucket="alpha-pass"),
            dependency(
                2,
                review_bucket="beta-watch",
                depends_on_dated_release=True,
                calendar_observed_at=GENERATED_AT - timedelta(hours=8),
                dependency_scheduled_at=GENERATED_AT + timedelta(days=1),
            ),
        ),
    )

    payload = research_source_resolution_calendar_dependency_report_payload(first)
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
        research_source_resolution_calendar_dependency_report_payload(tampered_payload)


def test_validation_rejects_bad_numerics_flags_statuses_and_future_calendars() -> None:
    with pytest.raises(ValueError, match="fresh_calendar_age_seconds"):
        ResearchSourceResolutionCalendarDependencyConfig(
            fresh_calendar_age_seconds=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="watch_dependency_score"):
        ResearchSourceResolutionCalendarDependencyConfig(
            watch_dependency_score=DecimalSubclass("0.250000"),
        )
    with pytest.raises(ValueError, match="block_active_calendar_dependency_count"):
        ResearchSourceResolutionCalendarDependencyConfig(
            watch_active_calendar_dependency_count=d("3.000000"),
            block_active_calendar_dependency_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="depends_on_dated_release"):
        replace(dependency(1), depends_on_dated_release=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timing_clarity_score"):
        dependency(1, timing_clarity_score=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        dependency(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(dependency(1), paper_only=False)
    with pytest.raises(ValueError, match="calendar_observed_at"):
        report(
            (
                dependency(
                    1,
                    calendar_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_resolution_calendar_dependency_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="status"):
        replace(report((dependency(1),)).rows[0], status="blocked")


def test_public_dataclasses_are_frozen_and_payload_requires_hard_flags() -> None:
    calendar_report = report((dependency(1),))
    payload = research_source_resolution_calendar_dependency_report_payload(
        calendar_report,
    )

    assert calendar_report.paper_only is True
    assert calendar_report.report_only is True
    assert calendar_report.readonly is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(FrozenInstanceError):
        calendar_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        calendar_report.rows[0].dependency_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="dependency_score"):
        replace(calendar_report.rows[0], dependency_score=d("0.750000"))

    bad_payload = dict(payload)
    bad_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_source_resolution_calendar_dependency_report_payload(bad_payload)

    unsafe_payload = dict(payload)
    unsafe_payload["market_slug"] = "unsafe"
    with pytest.raises(ValueError, match="unsafe"):
        research_source_resolution_calendar_dependency_report_payload(unsafe_payload)


def test_owned_module_has_no_db_network_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_resolution_calendar_dependency_report.py"
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
        "auth",
        "recommendation",
        "recommend",
        "open(",
        "connect(",
    )

    assert all(term not in source for term in forbidden_terms)


def test_public_api_is_exactly_the_report_only_surface() -> None:
    from polymarket_alpha_lab import research_source_resolution_calendar_dependency_report as api

    assert api.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_RESOLUTION_CALENDAR_DEPENDENCY_REPORT_CONFIG_VERSION",
        "ResearchSourceResolutionCalendarDependencyConfig",
        "ResearchSourceResolutionCalendarDependencyInput",
        "ResearchSourceResolutionCalendarDependencyReport",
        "ResearchSourceResolutionCalendarDependencyRow",
        "build_research_source_resolution_calendar_dependency_report",
        "research_source_resolution_calendar_dependency_report_payload",
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
