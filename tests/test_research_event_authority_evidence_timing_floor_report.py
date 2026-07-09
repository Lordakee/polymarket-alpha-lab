from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


SENSITIVE_INPUT_VALUES = (
    "candidate-secret-alpha",
    "candidate-secret-block",
    "candidate-secret-watch",
    "market-raw-alpha",
    "market-raw-block",
    "market-raw-watch",
    "will-the-private-question-leak",
    "blocked-private-question",
    "watch-private-question",
    "private-market-slug",
    "blocked-market-slug",
    "watch-market-slug",
    "https://authority.example/private-alpha",
    "https://authority.example/private-block",
    "https://authority.example/private-watch",
    "raw evidence text alpha",
    "raw evidence text block",
    "raw evidence text watch",
)

FORBIDDEN_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source_url",
    "source_text",
    "https://",
    "http://",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "trading",
    "live",
    "sizing",
    "recommendation",
    "database",
    "network",
)


class DecimalSubclass(Decimal):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_event_authority_evidence_timing_floor_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def event(
    *,
    raw_candidate_id: str = "candidate-secret-alpha",
    raw_market_id: str = "market-raw-alpha",
    raw_market_slug: str = "private-market-slug",
    raw_market_question: str = "will-the-private-question-leak",
    source_url: str = "https://authority.example/private-alpha",
    source_text: str = "raw evidence text alpha",
    authority_observed_at: datetime = GENERATED_AT - timedelta(seconds=180),
    evidence_observed_at: datetime = GENERATED_AT - timedelta(seconds=120),
    timing_floor_at: datetime = GENERATED_AT + timedelta(seconds=1800),
    authority_evidence_count: Decimal = d("3.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    report_module = module()
    return report_module.ResearchEventAuthorityEvidenceTimingFloorInput(
        raw_candidate_id=raw_candidate_id,
        raw_market_id=raw_market_id,
        raw_market_slug=raw_market_slug,
        raw_market_question=raw_market_question,
        source_url=source_url,
        source_text=source_text,
        authority_observed_at=authority_observed_at,
        evidence_observed_at=evidence_observed_at,
        timing_floor_at=timing_floor_at,
        authority_evidence_count=authority_evidence_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def blocked_event():
    return event(
        raw_candidate_id="candidate-secret-block",
        raw_market_id="market-raw-block",
        raw_market_slug="blocked-market-slug",
        raw_market_question="blocked-private-question",
        source_url="https://authority.example/private-block",
        source_text="raw evidence text block",
        authority_observed_at=GENERATED_AT - timedelta(seconds=3600),
        evidence_observed_at=GENERATED_AT - timedelta(seconds=2400),
        timing_floor_at=GENERATED_AT + timedelta(seconds=30),
        authority_evidence_count=d("1.000000"),
    )


def watch_event():
    return event(
        raw_candidate_id="candidate-secret-watch",
        raw_market_id="market-raw-watch",
        raw_market_slug="watch-market-slug",
        raw_market_question="watch-private-question",
        source_url="https://authority.example/private-watch",
        source_text="raw evidence text watch",
        authority_observed_at=GENERATED_AT - timedelta(seconds=780),
        evidence_observed_at=GENERATED_AT - timedelta(seconds=700),
        timing_floor_at=GENERATED_AT + timedelta(seconds=300),
        authority_evidence_count=d("2.000000"),
    )


def report(*rows: object):
    report_module = module()
    return report_module.build_research_event_authority_evidence_timing_floor_report(
        rows,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )


def expected_digest(payload: dict[str, object]) -> str:
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    encoded = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def assert_no_public_numerics(value: object) -> None:
    if type(value) in {int, float}:
        raise AssertionError(f"public payload leaked numeric type: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_public_numerics(item)


def assert_no_public_leakage(payload: dict[str, object]) -> None:
    rendered = json.dumps(payload, sort_keys=True)
    rendered_lower = rendered.lower()
    for marker in SENSITIVE_INPUT_VALUES:
        assert marker not in rendered
    for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
        assert fragment not in rendered_lower


def test_empty_input_returns_blocked_report_only_digest() -> None:
    report_module = module()

    timing_report = report()

    assert isinstance(
        timing_report,
        report_module.ResearchEventAuthorityEvidenceTimingFloorReport,
    )
    for klass in (
        report_module.ResearchEventAuthorityEvidenceTimingFloorConfig,
        report_module.ResearchEventAuthorityEvidenceTimingFloorInput,
        report_module.ResearchEventAuthorityEvidenceTimingFloorRow,
        report_module.ResearchEventAuthorityEvidenceTimingFloorReasonCodeCount,
        report_module.ResearchEventAuthorityEvidenceTimingFloorReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen
    with pytest.raises(FrozenInstanceError):
        timing_report.status = "pass"

    assert timing_report.generated_at == GENERATED_AT
    assert timing_report.config_version == (
        "research-event-authority-evidence-timing-floor-report-v0"
    )
    assert timing_report.status == "block"
    assert timing_report.input_count == d("0.000000")
    assert timing_report.row_count == d("0.000000")
    assert timing_report.pass_count == d("0.000000")
    assert timing_report.watch_count == d("0.000000")
    assert timing_report.block_count == d("0.000000")
    assert timing_report.rows == ()
    assert timing_report.reason_codes == (
        "event_authority_evidence_timing_floor_empty",
    )
    assert timing_report.reason_code_counts == (
        report_module.ResearchEventAuthorityEvidenceTimingFloorReasonCodeCount(
            reason_code="event_authority_evidence_timing_floor_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert timing_report.paper_only is True
    assert timing_report.report_only is True
    assert timing_report.readonly is True

    payload = report_module.research_event_authority_evidence_timing_floor_report_payload(
        timing_report,
    )
    assert payload["derived_validation_digest"] == expected_digest(payload)
    report_module.validate_research_event_authority_evidence_timing_floor_public_payload(
        payload,
    )
    assert_no_public_numerics(payload)
    assert_no_public_leakage(payload)


def test_status_counts_reason_codes_and_public_payload_are_deterministic() -> None:
    report_module = module()

    first = report(watch_event(), event(), blocked_event())
    second = report(watch_event(), event(), blocked_event())

    assert first == second
    assert first.status == "block"
    assert first.input_count == d("3.000000")
    assert first.row_count == d("3.000000")
    assert first.block_count == d("1.000000")
    assert first.watch_count == d("1.000000")
    assert first.pass_count == d("1.000000")
    assert first.min_timing_floor_remaining_seconds == d("30.000000")
    assert first.max_authority_evidence_lag_seconds == d("1200.000000")
    assert first.max_evidence_age_seconds == d("2400.000000")
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert all(row.status in {"pass", "watch", "block"} for row in first.rows)

    blocked, watched, passed = first.rows
    assert blocked.reason_codes == (
        "event_authority_evidence_stale_block",
        "event_authority_evidence_lag_block",
        "event_authority_evidence_timing_floor_block",
        "event_authority_evidence_quorum_block",
    )
    assert watched.reason_codes == (
        "event_authority_evidence_stale_watch",
        "event_authority_evidence_timing_floor_watch",
    )
    assert passed.reason_codes == ("event_authority_evidence_timing_floor_pass",)
    assert first.reason_codes == (
        "event_authority_evidence_stale_block",
        "event_authority_evidence_lag_block",
        "event_authority_evidence_timing_floor_block",
        "event_authority_evidence_quorum_block",
        "event_authority_evidence_stale_watch",
        "event_authority_evidence_timing_floor_watch",
        "event_authority_evidence_timing_floor_watch_present",
    )

    payload = report_module.research_event_authority_evidence_timing_floor_report_payload(
        first,
    )
    assert payload == (
        report_module.research_event_authority_evidence_timing_floor_report_payload(
            second,
        )
    )
    assert payload["derived_validation_digest"] == expected_digest(payload)
    assert all(row["status"] in {"pass", "watch", "block"} for row in payload["rows"])
    assert_no_public_numerics(payload)
    assert_no_public_leakage(payload)
    report_module.validate_research_event_authority_evidence_timing_floor_public_payload(
        payload,
    )


def test_rejects_non_decimal_numbers_and_flag_downgrades() -> None:
    report_module = module()

    with pytest.raises(ValueError, match="Decimal"):
        report_module.ResearchEventAuthorityEvidenceTimingFloorConfig(
            watch_evidence_age_seconds=600,
        )
    with pytest.raises(ValueError, match="Decimal"):
        event(authority_evidence_count=DecimalSubclass("3.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        event(paper_only=False)


def test_public_payload_validation_rejects_tampering_and_unsafe_fields() -> None:
    report_module = module()
    payload = report_module.research_event_authority_evidence_timing_floor_report_payload(
        report(event()),
    )

    tampered_digest = dict(payload)
    tampered_digest["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="digest"):
        report_module.validate_research_event_authority_evidence_timing_floor_public_payload(
            tampered_digest,
        )

    unsafe = dict(payload)
    unsafe["market_id"] = "market-raw-alpha"
    unsafe["derived_validation_digest"] = expected_digest(unsafe)
    with pytest.raises(ValueError, match="unsafe"):
        report_module.validate_research_event_authority_evidence_timing_floor_public_payload(
            unsafe,
        )

    numeric_payload = dict(payload)
    numeric_payload["pass_count"] = 1
    numeric_payload["derived_validation_digest"] = expected_digest(numeric_payload)
    with pytest.raises(ValueError, match="Decimal-derived strings"):
        report_module.validate_research_event_authority_evidence_timing_floor_public_payload(
            numeric_payload,
        )

    invalid_status = dict(payload)
    invalid_status["status"] = "blocked"
    invalid_status["derived_validation_digest"] = expected_digest(invalid_status)
    with pytest.raises(ValueError, match="status"):
        report_module.validate_research_event_authority_evidence_timing_floor_public_payload(
            invalid_status,
        )
