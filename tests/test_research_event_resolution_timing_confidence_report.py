from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_resolution_timing_confidence_report import (
    ResearchEventResolutionTimingConfidenceConfig,
    ResearchEventResolutionTimingConfidenceInput,
    ResearchEventResolutionTimingConfidenceReport,
    build_research_event_resolution_timing_confidence_report,
    research_event_resolution_timing_confidence_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=15)
RAW_EVENT_REFERENCE = "candidate-a-market-slug-question-url-token"


def timing_input(
    event_reference: str = RAW_EVENT_REFERENCE,
    *,
    observed_at: datetime = OBSERVED_AT,
    event_window_started_at: datetime | None = OBSERVED_AT - timedelta(hours=6),
    event_window_ended_at: datetime | None = OBSERVED_AT + timedelta(hours=30),
    latest_verified_signal_at: datetime | None = OBSERVED_AT - timedelta(hours=2),
    deadline_at: datetime | None = OBSERVED_AT + timedelta(hours=24),
    event_window_clarity_score: Decimal = Decimal("1"),
    source_authority_score: Decimal = Decimal("0.9"),
    contradiction_count: Decimal = Decimal("0"),
    highest_contradiction_severity: Decimal = Decimal("0"),
    required_dependency_count: Decimal = Decimal("3"),
    verified_dependency_count: Decimal = Decimal("3"),
    ambiguity_risk_score: Decimal = Decimal("0.1"),
    reason_codes: tuple[str, ...] = ("official_calendar", "resolution_ready"),
) -> ResearchEventResolutionTimingConfidenceInput:
    return ResearchEventResolutionTimingConfidenceInput(
        event_reference=event_reference,
        observed_at=observed_at,
        event_window_started_at=event_window_started_at,
        event_window_ended_at=event_window_ended_at,
        latest_verified_signal_at=latest_verified_signal_at,
        deadline_at=deadline_at,
        event_window_clarity_score=event_window_clarity_score,
        source_authority_score=source_authority_score,
        contradiction_count=contradiction_count,
        highest_contradiction_severity=highest_contradiction_severity,
        required_dependency_count=required_dependency_count,
        verified_dependency_count=verified_dependency_count,
        ambiguity_risk_score=ambiguity_risk_score,
        reason_codes=reason_codes,
    )


def test_empty_input_returns_report_only_digest() -> None:
    report = build_research_event_resolution_timing_confidence_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionTimingConfidenceConfig(),
    )

    assert report == ResearchEventResolutionTimingConfidenceReport(
        generated_at=GENERATED_AT,
        config_version="research_event_resolution_timing_confidence_v1",
        row_count=Decimal("0"),
        pass_count=Decimal("0"),
        watch_count=Decimal("0"),
        block_count=Decimal("0"),
        average_confidence_score=Decimal("0"),
        weakest_confidence_score=Decimal("0"),
        rows=(),
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_clear_timing_event_scores_pass_with_decimal_only_dimensions() -> None:
    report = build_research_event_resolution_timing_confidence_report(
        (timing_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionTimingConfidenceConfig(),
    )

    row = report.rows[0]
    assert row.event_digest == hashlib.sha256(RAW_EVENT_REFERENCE.encode("utf-8")).hexdigest()
    assert row.latest_verified_signal_age_hours == Decimal("2.0000")
    assert row.hours_until_deadline == Decimal("24.0000")
    assert row.event_window_clarity_score == Decimal("1.0000")
    assert row.latest_verified_signal_recency_score == Decimal("0.9583")
    assert row.source_authority_score == Decimal("0.9000")
    assert row.contradiction_pressure_score == Decimal("0.0000")
    assert row.dependency_completeness_score == Decimal("1.0000")
    assert row.ambiguity_risk_score == Decimal("0.1000")
    assert row.deadline_proximity_score == Decimal("1.0000")
    assert row.confidence_score == Decimal("0.9687")
    assert row.timing_status == "pass"
    assert row.reason_codes == ("official_calendar", "pass", "resolution_ready")
    assert report.pass_count == Decimal("1")


def test_weak_timing_event_blocks_and_flags_each_confidence_dimension() -> None:
    report = build_research_event_resolution_timing_confidence_report(
        (
            timing_input(
                latest_verified_signal_at=None,
                deadline_at=OBSERVED_AT + timedelta(hours=2),
                event_window_clarity_score=Decimal("0.2"),
                source_authority_score=Decimal("0.2"),
                contradiction_count=Decimal("2"),
                highest_contradiction_severity=Decimal("0.8"),
                required_dependency_count=Decimal("3"),
                verified_dependency_count=Decimal("1"),
                ambiguity_risk_score=Decimal("0.9"),
                reason_codes=(),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionTimingConfidenceConfig(),
    )

    row = report.rows[0]
    assert row.timing_status == "block"
    assert row.latest_verified_signal_age_hours is None
    assert row.latest_verified_signal_recency_score == Decimal("0.0000")
    assert row.contradiction_pressure_score == Decimal("0.7334")
    assert row.dependency_completeness_score == Decimal("0.3333")
    assert row.deadline_proximity_score == Decimal("0.1667")
    assert row.confidence_score == Decimal("0.1867")
    assert row.reason_codes == (
        "ambiguous_resolution",
        "block",
        "contradiction_pressure",
        "deadline_pressure",
        "event_window_unclear",
        "incomplete_dependencies",
        "low_timing_confidence",
        "missing_latest_signal",
        "weak_source_authority",
    )
    assert report.block_count == Decimal("1")


def test_rows_reason_counts_and_digest_are_deterministic() -> None:
    config = ResearchEventResolutionTimingConfidenceConfig()
    inputs = (
        timing_input("z-event", source_authority_score=Decimal("0.55"), reason_codes=("zeta",)),
        timing_input("a-event", reason_codes=("alpha",)),
        timing_input(
            "m-event",
            latest_verified_signal_at=OBSERVED_AT - timedelta(hours=60),
            reason_codes=("beta",),
        ),
    )

    report = build_research_event_resolution_timing_confidence_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
    )
    reversed_report = build_research_event_resolution_timing_confidence_report(
        tuple(reversed(inputs)),
        generated_at=GENERATED_AT,
        config=config,
    )

    assert [row.event_digest for row in report.rows] == sorted(row.event_digest for row in report.rows)
    assert report.reason_code_counts == (
        ("alpha", Decimal("1")),
        ("beta", Decimal("1")),
        ("block", Decimal("1")),
        ("pass", Decimal("1")),
        ("stale_verified_signal", Decimal("1")),
        ("watch", Decimal("1")),
        ("weak_source_authority", Decimal("1")),
        ("zeta", Decimal("1")),
    )
    assert reversed_report.rows == report.rows
    assert reversed_report.derived_validation_digest == report.derived_validation_digest


def test_payload_helper_uses_decimal_strings_redacts_raw_references_and_revalidates_digest() -> None:
    report = build_research_event_resolution_timing_confidence_report(
        (timing_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionTimingConfidenceConfig(),
    )

    payload = research_event_resolution_timing_confidence_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["confidence_score"] == "0.9687"
    assert payload["row_count"] == "1.0000"
    assert payload["reason_code_counts"][0][1] == "1.0000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert RAW_EVENT_REFERENCE not in encoded
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    assert "Decimal" not in encoded
    assert not _unsafe_public_fragments(payload)

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.0000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_resolution_timing_confidence_payload(tampered_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_resolution_timing_confidence_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0], event_digest="candidate-a")]
    with pytest.raises(ValueError, match="unsafe"):
        research_event_resolution_timing_confidence_payload(unsafe_value_payload)


def test_validation_rejects_invalid_decimals_datetimes_counts_and_flags() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_event_resolution_timing_confidence_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
            config=ResearchEventResolutionTimingConfidenceConfig(),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        timing_input(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        timing_input(observed_at=datetime(2026, 7, 8, 12, 0, tzinfo=NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        timing_input(observed_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="latest_verified_signal_at"):
        timing_input(latest_verified_signal_at=OBSERVED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="event_window_clarity_score"):
        timing_input(event_window_clarity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="verified_dependency_count"):
        timing_input(required_dependency_count=Decimal("1"), verified_dependency_count=Decimal("2"))
    with pytest.raises(ValueError, match="confidence weights"):
        ResearchEventResolutionTimingConfidenceConfig(deadline_proximity_weight=Decimal("0.2000"))
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(ResearchEventResolutionTimingConfidenceConfig(), paper_only=False)


def test_public_dataclasses_are_frozen_and_reject_subclasses() -> None:
    config = ResearchEventResolutionTimingConfidenceConfig()
    input_row = timing_input()

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        input_row.event_reference = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(ResearchEventResolutionTimingConfidenceConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class InputSubclass(ResearchEventResolutionTimingConfidenceInput):
            pass


def test_static_module_has_no_forbidden_side_effect_behavior() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_resolution_timing_confidence_report.py",
    ).read_text(encoding="utf-8")
    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "open(",
        "broker",
        "database",
        "persist",
        "private_key",
    )

    assert not [term for term in forbidden_terms if term in source.lower()]

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk_values(child))
    return (value,)


def _unsafe_public_fragments(value: object) -> tuple[str, ...]:
    fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "http",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = key.lower()
            findings.extend(fragment for fragment in fragments if fragment in normalized_key)
            findings.extend(_unsafe_public_fragments(item))
    elif isinstance(value, list):
        for item in value:
            findings.extend(_unsafe_public_fragments(item))
    elif type(value) is str:
        normalized_value = value.lower()
        findings.extend(fragment for fragment in fragments if fragment in normalized_value)
    return tuple(findings)
