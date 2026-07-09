from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_resolution_authority_conflict_decay_report import (
    RESEARCH_EVENT_RESOLUTION_AUTHORITY_CONFLICT_DECAY_STATUSES,
    ResearchEventResolutionAuthorityConflictDecayConfig,
    ResearchEventResolutionAuthorityConflictDecayInput,
    ResearchEventResolutionAuthorityConflictDecayReport,
    build_research_event_resolution_authority_conflict_decay_report,
    research_event_resolution_authority_conflict_decay_digest,
    research_event_resolution_authority_conflict_decay_payload,
    validate_research_event_resolution_authority_conflict_decay_digest,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=10)
RAW_EVENT_REFERENCE = "candidate-alpha-market-slug-question-source-url-token"


def conflict_input(
    event_reference: str = RAW_EVENT_REFERENCE,
    *,
    observed_at: datetime = OBSERVED_AT,
    first_conflict_seen_at: datetime | None = None,
    last_authority_update_at: datetime | None = OBSERVED_AT - timedelta(hours=1),
    last_conflict_seen_at: datetime | None = None,
    authoritative_signal_count: Decimal = Decimal("4"),
    conflicting_signal_count: Decimal = Decimal("0"),
    independent_authority_count: Decimal = Decimal("2"),
    resolution_evidence_count: Decimal = Decimal("3"),
    conflict_severity_score: Decimal = Decimal("0"),
    conflict_recurrence_count: Decimal = Decimal("0"),
    reason_codes: tuple[str, ...] = ("authority_ready", "verified_packet"),
) -> ResearchEventResolutionAuthorityConflictDecayInput:
    return ResearchEventResolutionAuthorityConflictDecayInput(
        event_reference=event_reference,
        observed_at=observed_at,
        first_conflict_seen_at=first_conflict_seen_at,
        last_authority_update_at=last_authority_update_at,
        last_conflict_seen_at=last_conflict_seen_at,
        authoritative_signal_count=authoritative_signal_count,
        conflicting_signal_count=conflicting_signal_count,
        independent_authority_count=independent_authority_count,
        resolution_evidence_count=resolution_evidence_count,
        conflict_severity_score=conflict_severity_score,
        conflict_recurrence_count=conflict_recurrence_count,
        reason_codes=reason_codes,
    )


def test_empty_input_returns_report_only_pass_digest() -> None:
    report = build_research_event_resolution_authority_conflict_decay_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionAuthorityConflictDecayConfig(),
    )

    assert report == ResearchEventResolutionAuthorityConflictDecayReport(
        generated_at=GENERATED_AT,
        config_version="research_event_resolution_authority_conflict_decay_v1",
        row_count=Decimal("0"),
        pass_count=Decimal("0"),
        watch_count=Decimal("0"),
        block_count=Decimal("0"),
        average_confidence_decay_score=Decimal("0"),
        highest_confidence_decay_score=Decimal("0"),
        highest_conflict_share=Decimal("0"),
        weakest_independence_score=Decimal("0"),
        status="pass",
        rows=(),
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_clear_authority_conflict_decay_scores_pass_with_decimal_only_metrics() -> None:
    report = build_research_event_resolution_authority_conflict_decay_report(
        (conflict_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionAuthorityConflictDecayConfig(),
    )

    row = report.rows[0]
    assert row.event_digest == hashlib.sha256(RAW_EVENT_REFERENCE.encode("utf-8")).hexdigest()
    assert row.authority_update_age_hours == Decimal("1.0000")
    assert row.conflict_age_hours is None
    assert row.hours_since_last_conflict is None
    assert row.conflict_share == Decimal("0.0000")
    assert row.conflict_age_pressure_score == Decimal("0.0000")
    assert row.authority_update_decay_score == Decimal("0.0208")
    assert row.conflict_recency_pressure_score == Decimal("0.0000")
    assert row.independence_score == Decimal("1.0000")
    assert row.resolution_evidence_score == Decimal("1.0000")
    assert row.recurrence_pressure_score == Decimal("0.0000")
    assert row.confidence_decay_score == Decimal("0.0031")
    assert row.status == "pass"
    assert row.reason_codes == ("authority_ready", "pass", "verified_packet")
    assert report.status == "pass"
    assert report.pass_count == Decimal("1.0000")


def test_stale_recurring_authority_conflict_decay_blocks_each_dimension() -> None:
    report = build_research_event_resolution_authority_conflict_decay_report(
        (
            conflict_input(
                first_conflict_seen_at=OBSERVED_AT - timedelta(hours=80),
                last_authority_update_at=None,
                last_conflict_seen_at=OBSERVED_AT - timedelta(hours=2),
                authoritative_signal_count=Decimal("1"),
                conflicting_signal_count=Decimal("3"),
                independent_authority_count=Decimal("0"),
                resolution_evidence_count=Decimal("0"),
                conflict_severity_score=Decimal("0.8"),
                conflict_recurrence_count=Decimal("4"),
                reason_codes=(),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionAuthorityConflictDecayConfig(),
    )

    row = report.rows[0]
    assert row.status == "block"
    assert row.conflict_age_hours == Decimal("80.0000")
    assert row.authority_update_age_hours is None
    assert row.hours_since_last_conflict == Decimal("2.0000")
    assert row.conflict_share == Decimal("0.7500")
    assert row.conflict_age_pressure_score == Decimal("1.0000")
    assert row.authority_update_decay_score == Decimal("1.0000")
    assert row.conflict_recency_pressure_score == Decimal("0.9722")
    assert row.independence_score == Decimal("0.0000")
    assert row.resolution_evidence_score == Decimal("0.0000")
    assert row.recurrence_pressure_score == Decimal("1.0000")
    assert row.confidence_decay_score == Decimal("0.9172")
    assert row.reason_codes == (
        "authority_conflict_age_block",
        "authority_conflict_decay_elevated",
        "authority_conflict_recency_block",
        "authority_conflict_severity_block",
        "authority_conflict_share_block",
        "authority_update_missing",
        "authority_update_staleness_block",
        "block",
        "conflict_recurrence_pressure",
        "resolution_authority_independence_gap",
        "resolution_evidence_gap",
    )
    assert report.status == "block"
    assert report.block_count == Decimal("1.0000")


def test_rows_reason_counts_and_digest_are_deterministic() -> None:
    config = ResearchEventResolutionAuthorityConflictDecayConfig()
    events = (
        conflict_input("z-event", reason_codes=("zeta",)),
        conflict_input(
            "a-event",
            first_conflict_seen_at=OBSERVED_AT - timedelta(hours=12),
            last_conflict_seen_at=OBSERVED_AT - timedelta(hours=8),
            authoritative_signal_count=Decimal("2"),
            conflicting_signal_count=Decimal("1"),
            conflict_severity_score=Decimal("0.2"),
            reason_codes=("alpha",),
        ),
        conflict_input(
            "m-event",
            first_conflict_seen_at=OBSERVED_AT - timedelta(hours=80),
            last_authority_update_at=None,
            last_conflict_seen_at=OBSERVED_AT - timedelta(hours=1),
            authoritative_signal_count=Decimal("1"),
            conflicting_signal_count=Decimal("3"),
            independent_authority_count=Decimal("0"),
            resolution_evidence_count=Decimal("1"),
            conflict_severity_score=Decimal("0.8"),
            conflict_recurrence_count=Decimal("4"),
            reason_codes=("beta",),
        ),
    )

    report = build_research_event_resolution_authority_conflict_decay_report(
        events,
        generated_at=GENERATED_AT,
        config=config,
    )
    reversed_report = build_research_event_resolution_authority_conflict_decay_report(
        tuple(reversed(events)),
        generated_at=GENERATED_AT,
        config=config,
    )

    assert [row.event_digest for row in report.rows] == sorted(row.event_digest for row in report.rows)
    assert reversed_report.rows == report.rows
    assert reversed_report.derived_validation_digest == report.derived_validation_digest
    assert report.reason_code_counts == tuple(sorted(report.reason_code_counts))
    assert report.reason_code_counts[:4] == (
        ("alpha", Decimal("1.0000")),
        ("authority_conflict_age_block", Decimal("1.0000")),
        ("authority_conflict_decay_elevated", Decimal("2.0000")),
        ("authority_conflict_recency_block", Decimal("1.0000")),
    )
    assert ("pass", Decimal("1.0000")) in report.reason_code_counts
    assert ("watch", Decimal("1.0000")) in report.reason_code_counts
    assert ("block", Decimal("1.0000")) in report.reason_code_counts


def test_payload_helper_uses_decimal_strings_redacts_raw_references_and_validates_digest() -> None:
    report = build_research_event_resolution_authority_conflict_decay_report(
        (conflict_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionAuthorityConflictDecayConfig(),
    )

    payload = research_event_resolution_authority_conflict_decay_payload(report)
    encoded = json.dumps(payload, sort_keys=True)
    digest = research_event_resolution_authority_conflict_decay_digest(report)

    assert payload["derived_validation_digest"] == report.derived_validation_digest == digest
    assert len(digest) == 64
    int(digest, 16)
    assert payload["rows"][0]["confidence_decay_score"] == "0.0031"
    assert payload["row_count"] == "1.0000"
    assert payload["reason_code_counts"][0][1] == "1.0000"
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert RAW_EVENT_REFERENCE not in encoded
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    assert "Decimal" not in encoded
    assert not _unsafe_public_fragments(payload)
    validate_research_event_resolution_authority_conflict_decay_digest(report)

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.0000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_resolution_authority_conflict_decay_payload(tampered_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_resolution_authority_conflict_decay_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0], event_digest="candidate-a")]
    with pytest.raises(ValueError, match="unsafe"):
        research_event_resolution_authority_conflict_decay_payload(unsafe_value_payload)


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
        build_research_event_resolution_authority_conflict_decay_report(
            (),
            generated_at=datetime(2026, 7, 9, 12, 0),
            config=ResearchEventResolutionAuthorityConflictDecayConfig(),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        conflict_input(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        conflict_input(observed_at=datetime(2026, 7, 9, 12, 0, tzinfo=NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        conflict_input(observed_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="first_conflict_seen_at"):
        conflict_input(first_conflict_seen_at=OBSERVED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="last_authority_update_at"):
        conflict_input(last_authority_update_at=OBSERVED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="last_conflict_seen_at"):
        conflict_input(last_conflict_seen_at=OBSERVED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="authoritative_signal_count must be a Decimal"):
        conflict_input(authoritative_signal_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="conflict_severity_score must be a Decimal"):
        conflict_input(conflict_severity_score=DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="total signal count"):
        conflict_input(authoritative_signal_count=Decimal("0"), conflicting_signal_count=Decimal("0"))
    with pytest.raises(ValueError, match="decay weights"):
        ResearchEventResolutionAuthorityConflictDecayConfig(
            recurrence_weight=Decimal("0.1000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(ResearchEventResolutionAuthorityConflictDecayConfig(), paper_only=False)

    report = build_research_event_resolution_authority_conflict_decay_report(
        (conflict_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionAuthorityConflictDecayConfig(),
    )
    with pytest.raises(ValueError, match="status"):
        dataclasses.replace(report, status="ready")
    with pytest.raises(ValueError, match="status"):
        dataclasses.replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        dataclasses.replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="reason_code contains unsafe text"):
        conflict_input(reason_codes=("market_slug",))


def test_public_dataclasses_are_frozen_reject_subclasses_and_export_safe_statuses() -> None:
    config = ResearchEventResolutionAuthorityConflictDecayConfig()
    input_row = conflict_input()

    assert RESEARCH_EVENT_RESOLUTION_AUTHORITY_CONFLICT_DECAY_STATUSES == (
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
        class ConfigSubclass(ResearchEventResolutionAuthorityConflictDecayConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class InputSubclass(ResearchEventResolutionAuthorityConflictDecayInput):
            pass


def test_static_module_has_no_forbidden_side_effect_behavior() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_resolution_authority_conflict_decay_report.py",
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


def _unsafe_public_fragments(value: object) -> tuple[str, ...]:
    fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "source url",
        "source_url",
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
