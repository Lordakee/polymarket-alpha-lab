from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_resolution_authority_timing_gap_report import (
    RESEARCH_EVENT_RESOLUTION_AUTHORITY_TIMING_GAP_STATUSES,
    ResearchEventResolutionAuthorityTimingGapConfig,
    ResearchEventResolutionAuthorityTimingGapInput,
    ResearchEventResolutionAuthorityTimingGapReport,
    build_research_event_resolution_authority_timing_gap_report,
    research_event_resolution_authority_timing_gap_digest,
    research_event_resolution_authority_timing_gap_payload,
    validate_research_event_resolution_authority_timing_gap_digest,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=15)
RAW_EVENT_REFERENCE = "candidate-a-market-slug-question-url-token"


def timing_input(
    event_reference: str = RAW_EVENT_REFERENCE,
    *,
    observed_at: datetime = OBSERVED_AT,
    authority_last_updated_at: datetime | None = OBSERVED_AT - timedelta(hours=3),
    expected_update_cadence_hours: Decimal = Decimal("12"),
    latest_verified_at: datetime | None = OBSERVED_AT - timedelta(hours=2),
    deadline_at: datetime | None = OBSERVED_AT + timedelta(hours=24),
    contradiction_count: Decimal = Decimal("0"),
    highest_contradiction_severity: Decimal = Decimal("0"),
    verification_required_count: Decimal = Decimal("3"),
    verification_completed_count: Decimal = Decimal("3"),
    ambiguity_risk_score: Decimal = Decimal("0.1"),
    reason_codes: tuple[str, ...] = ("authority_ready", "verified_packet"),
) -> ResearchEventResolutionAuthorityTimingGapInput:
    return ResearchEventResolutionAuthorityTimingGapInput(
        event_reference=event_reference,
        observed_at=observed_at,
        authority_last_updated_at=authority_last_updated_at,
        expected_update_cadence_hours=expected_update_cadence_hours,
        latest_verified_at=latest_verified_at,
        deadline_at=deadline_at,
        contradiction_count=contradiction_count,
        highest_contradiction_severity=highest_contradiction_severity,
        verification_required_count=verification_required_count,
        verification_completed_count=verification_completed_count,
        ambiguity_risk_score=ambiguity_risk_score,
        reason_codes=reason_codes,
    )


def test_empty_input_returns_report_only_digest() -> None:
    report = build_research_event_resolution_authority_timing_gap_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionAuthorityTimingGapConfig(),
    )

    assert report == ResearchEventResolutionAuthorityTimingGapReport(
        generated_at=GENERATED_AT,
        config_version="research_event_resolution_authority_timing_gap_v1",
        row_count=Decimal("0"),
        pass_count=Decimal("0"),
        watch_count=Decimal("0"),
        block_count=Decimal("0"),
        average_gap_score=Decimal("0"),
        highest_gap_score=Decimal("0"),
        weakest_authority_freshness_score=Decimal("0"),
        status="pass",
        rows=(),
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_clear_authority_timing_gap_scores_pass_with_decimal_only_dimensions() -> None:
    report = build_research_event_resolution_authority_timing_gap_report(
        (timing_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionAuthorityTimingGapConfig(),
    )

    row = report.rows[0]
    assert row.event_digest == hashlib.sha256(RAW_EVENT_REFERENCE.encode("utf-8")).hexdigest()
    assert row.authority_age_hours == Decimal("3.0000")
    assert row.latest_verified_age_hours == Decimal("2.0000")
    assert row.hours_until_deadline == Decimal("24.0000")
    assert row.expected_update_cadence_hours == Decimal("12.0000")
    assert row.authority_freshness_score == Decimal("0.9583")
    assert row.cadence_adherence_score == Decimal("1.0000")
    assert row.latest_verified_age_score == Decimal("0.9583")
    assert row.contradiction_pressure_score == Decimal("0.0000")
    assert row.verification_coverage_score == Decimal("1.0000")
    assert row.ambiguity_risk_score == Decimal("0.1000")
    assert row.deadline_proximity_score == Decimal("1.0000")
    assert row.gap_score == Decimal("0.0246")
    assert row.status == "pass"
    assert row.reason_codes == ("authority_ready", "pass", "verified_packet")
    assert report.status == "pass"
    assert report.pass_count == Decimal("1.0000")


def test_stale_conflicted_authority_timing_gap_blocks_each_dimension() -> None:
    report = build_research_event_resolution_authority_timing_gap_report(
        (
            timing_input(
                authority_last_updated_at=None,
                latest_verified_at=None,
                deadline_at=OBSERVED_AT + timedelta(hours=2),
                contradiction_count=Decimal("2"),
                highest_contradiction_severity=Decimal("0.8"),
                verification_required_count=Decimal("3"),
                verification_completed_count=Decimal("1"),
                ambiguity_risk_score=Decimal("0.9"),
                reason_codes=(),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionAuthorityTimingGapConfig(),
    )

    row = report.rows[0]
    assert row.status == "block"
    assert row.authority_age_hours is None
    assert row.latest_verified_age_hours is None
    assert row.authority_freshness_score == Decimal("0.0000")
    assert row.cadence_adherence_score == Decimal("0.0000")
    assert row.latest_verified_age_score == Decimal("0.0000")
    assert row.contradiction_pressure_score == Decimal("0.7334")
    assert row.verification_coverage_score == Decimal("0.3333")
    assert row.deadline_proximity_score == Decimal("0.1667")
    assert row.gap_score == Decimal("0.8833")
    assert row.reason_codes == (
        "ambiguity_risk",
        "authority_freshness_gap",
        "authority_update_missing",
        "block",
        "cadence_adherence_gap",
        "contradiction_pressure",
        "deadline_pressure",
        "latest_verified_missing",
        "latest_verified_stale",
        "timing_gap_elevated",
        "verification_coverage_gap",
    )
    assert report.status == "block"
    assert report.block_count == Decimal("1.0000")


def test_rows_reason_counts_and_digest_are_deterministic() -> None:
    config = ResearchEventResolutionAuthorityTimingGapConfig()
    events = (
        timing_input("z-event", reason_codes=("zeta",)),
        timing_input(
            "a-event",
            authority_last_updated_at=OBSERVED_AT - timedelta(hours=20),
            reason_codes=("alpha",),
        ),
        timing_input(
            "m-event",
            latest_verified_at=OBSERVED_AT - timedelta(hours=60),
            reason_codes=("beta",),
        ),
    )

    report = build_research_event_resolution_authority_timing_gap_report(
        events,
        generated_at=GENERATED_AT,
        config=config,
    )
    reversed_report = build_research_event_resolution_authority_timing_gap_report(
        tuple(reversed(events)),
        generated_at=GENERATED_AT,
        config=config,
    )

    assert [row.event_digest for row in report.rows] == sorted(row.event_digest for row in report.rows)
    assert reversed_report.rows == report.rows
    assert reversed_report.derived_validation_digest == report.derived_validation_digest
    assert report.reason_code_counts == (
        ("alpha", Decimal("1.0000")),
        ("beta", Decimal("1.0000")),
        ("block", Decimal("1.0000")),
        ("cadence_adherence_gap", Decimal("1.0000")),
        ("latest_verified_stale", Decimal("1.0000")),
        ("pass", Decimal("1.0000")),
        ("watch", Decimal("1.0000")),
        ("zeta", Decimal("1.0000")),
    )


def test_payload_helper_uses_decimal_strings_redacts_raw_references_and_validates_digest() -> None:
    report = build_research_event_resolution_authority_timing_gap_report(
        (timing_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionAuthorityTimingGapConfig(),
    )

    payload = research_event_resolution_authority_timing_gap_payload(report)
    encoded = json.dumps(payload, sort_keys=True)
    digest = research_event_resolution_authority_timing_gap_digest(report)

    assert payload["derived_validation_digest"] == report.derived_validation_digest == digest
    assert len(digest) == 64
    int(digest, 16)
    assert payload["rows"][0]["gap_score"] == "0.0246"
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
    validate_research_event_resolution_authority_timing_gap_digest(report)

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.0000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_resolution_authority_timing_gap_payload(tampered_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_resolution_authority_timing_gap_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0], event_digest="candidate-a")]
    with pytest.raises(ValueError, match="unsafe"):
        research_event_resolution_authority_timing_gap_payload(unsafe_value_payload)

    numeric_payload = _with_recomputed_payload_digest(dict(payload, row_count=1))
    with pytest.raises(ValueError, match="numeric|JSON"):
        research_event_resolution_authority_timing_gap_payload(numeric_payload)


def test_validation_rejects_invalid_decimals_datetimes_counts_statuses_and_flags() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_event_resolution_authority_timing_gap_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
            config=ResearchEventResolutionAuthorityTimingGapConfig(),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        timing_input(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        timing_input(observed_at=datetime(2026, 7, 8, 12, 0, tzinfo=NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        timing_input(observed_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="latest_verified_at"):
        timing_input(latest_verified_at=OBSERVED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="deadline_at"):
        timing_input(deadline_at=OBSERVED_AT - timedelta(seconds=1))
    with pytest.raises(ValueError, match="expected_update_cadence_hours must be a Decimal"):
        timing_input(expected_update_cadence_hours=12)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ambiguity_risk_score must be a Decimal"):
        timing_input(ambiguity_risk_score=DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="verification_completed_count"):
        timing_input(
            verification_required_count=Decimal("1"),
            verification_completed_count=Decimal("2"),
        )
    with pytest.raises(ValueError, match="gap weights"):
        ResearchEventResolutionAuthorityTimingGapConfig(deadline_proximity_weight=Decimal("0.2000"))
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(ResearchEventResolutionAuthorityTimingGapConfig(), paper_only=False)

    report = build_research_event_resolution_authority_timing_gap_report(
        (timing_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionAuthorityTimingGapConfig(),
    )
    with pytest.raises(ValueError, match="status"):
        dataclasses.replace(report, status="ready")
    with pytest.raises(ValueError, match="status"):
        dataclasses.replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        dataclasses.replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="reason_code contains unsafe text"):
        timing_input(reason_codes=("market_slug",))
    with pytest.raises(ValueError, match="reason_code contains unsafe text"):
        timing_input(reason_codes=("source_text",))


def test_public_dataclasses_are_frozen_reject_subclasses_and_export_safe_statuses() -> None:
    config = ResearchEventResolutionAuthorityTimingGapConfig()
    input_row = timing_input()

    assert RESEARCH_EVENT_RESOLUTION_AUTHORITY_TIMING_GAP_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert dataclasses.is_dataclass(config)
    assert dataclasses.is_dataclass(input_row)

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        input_row.event_reference = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(ResearchEventResolutionAuthorityTimingGapConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class InputSubclass(ResearchEventResolutionAuthorityTimingGapInput):
            pass


def test_static_module_has_no_forbidden_side_effect_behavior() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_resolution_authority_timing_gap_report.py",
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
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
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


def _with_recomputed_payload_digest(payload: dict[str, object]) -> dict[str, object]:
    digest_payload = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    payload["derived_validation_digest"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return payload


def _unsafe_public_fragments(value: object) -> tuple[str, ...]:
    fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "text",
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
