from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_event_resolution_authority_watchlist_report as api
from polymarket_alpha_lab.research_event_resolution_authority_watchlist_report import (
    RESEARCH_EVENT_RESOLUTION_AUTHORITY_WATCHLIST_STATUSES,
    ResearchEventResolutionAuthorityWatchlistConfig,
    ResearchEventResolutionAuthorityWatchlistInput,
    ResearchEventResolutionAuthorityWatchlistReport,
    ResearchEventResolutionAuthorityWatchlistRow,
    build_research_event_resolution_authority_watchlist_report,
    research_event_resolution_authority_watchlist_report_digest,
    research_event_resolution_authority_watchlist_report_json,
    research_event_resolution_authority_watchlist_report_payload,
    validate_research_event_resolution_authority_watchlist_digest,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
RAW_EVENT_REFERENCE = "candidate-alpha-market-slug-question-url-token"
RAW_AUTHORITY_REFERENCE = "https://authority.example/raw-resolution-text"


def watch_item(
    *,
    event_reference: str = RAW_EVENT_REFERENCE,
    authority_reference: str = RAW_AUTHORITY_REFERENCE,
    authority_tier: str = "official",
    last_checked_at: datetime | None = GENERATED_AT - timedelta(minutes=5),
    expected_check_cadence_seconds: Decimal = Decimal("3600"),
    unresolved_dependency_count: Decimal = Decimal("0"),
    conflict_signal_count: Decimal = Decimal("0"),
    verification_coverage: Decimal = Decimal("0.950000"),
    deadline_at: datetime | None = GENERATED_AT + timedelta(days=7),
    reason_codes: tuple[str, ...] = (),
) -> ResearchEventResolutionAuthorityWatchlistInput:
    return ResearchEventResolutionAuthorityWatchlistInput(
        event_reference=event_reference,
        authority_reference=authority_reference,
        authority_tier=authority_tier,
        last_checked_at=last_checked_at,
        expected_check_cadence_seconds=expected_check_cadence_seconds,
        unresolved_dependency_count=unresolved_dependency_count,
        conflict_signal_count=conflict_signal_count,
        verification_coverage=verification_coverage,
        deadline_at=deadline_at,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchEventResolutionAuthorityWatchlistInput, ...],
    *,
    config: ResearchEventResolutionAuthorityWatchlistConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventResolutionAuthorityWatchlistReport:
    return build_research_event_resolution_authority_watchlist_report(
        rows,
        generated_at=generated_at,
        config=config or ResearchEventResolutionAuthorityWatchlistConfig(),
    )


def test_triages_resolution_authorities_into_pass_watch_and_block() -> None:
    built = report(
        (
            watch_item(
                event_reference="event-pass-raw-market-question",
                authority_reference="official-resolution-url-pass",
            ),
            watch_item(
                event_reference="event-watch-raw-market-question",
                authority_reference="proxy-resolution-url-watch",
                authority_tier="proxy",
                last_checked_at=GENERATED_AT - timedelta(minutes=75),
                unresolved_dependency_count=Decimal("2"),
                conflict_signal_count=Decimal("1"),
                verification_coverage=Decimal("0.700000"),
                deadline_at=GENERATED_AT + timedelta(hours=12),
            ),
            watch_item(
                event_reference="event-block-raw-market-question",
                authority_reference="unknown-resolution-url-block",
                authority_tier="unknown",
                last_checked_at=None,
                unresolved_dependency_count=Decimal("4"),
                conflict_signal_count=Decimal("3"),
                verification_coverage=Decimal("0.200000"),
                deadline_at=GENERATED_AT + timedelta(minutes=30),
            ),
        ),
    )

    assert built.status == "block"
    assert built.authority_count == Decimal("3.000000")
    assert built.pass_count == Decimal("1.000000")
    assert built.watch_count == Decimal("1.000000")
    assert built.block_count == Decimal("1.000000")
    assert built.average_watchlist_score == Decimal("0.481389")
    assert built.highest_watchlist_score == Decimal("0.932500")
    assert built.stale_or_missing_count == Decimal("2.000000")
    assert built.low_coverage_count == Decimal("2.000000")
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    block_row, watch_row, pass_row = built.rows
    assert [row.status for row in built.rows] == ["block", "watch", "pass"]
    assert block_row.check_age_seconds is None
    assert block_row.age_to_cadence_ratio is None
    assert block_row.watchlist_score == Decimal("0.932500")
    assert "authority_check_missing" in block_row.reason_codes
    assert "deadline_pressure_block" in block_row.reason_codes
    assert watch_row.check_age_seconds == Decimal("4500.000000")
    assert watch_row.age_to_cadence_ratio == Decimal("1.250000")
    assert watch_row.watchlist_score == Decimal("0.491667")
    assert "authority_stale_watch" in watch_row.reason_codes
    assert "coverage_gap_watch" in watch_row.reason_codes
    assert pass_row.check_age_seconds == Decimal("300.000000")
    assert pass_row.age_to_cadence_ratio == Decimal("0.083333")
    assert pass_row.watchlist_score == Decimal("0.020000")
    assert pass_row.reason_codes == (
        "authority_recent",
        "coverage_sufficient",
        "authority_watchlist_pass",
    )


def test_payload_json_and_sha256_digest_are_deterministic_and_redacted() -> None:
    built = report((watch_item(),))

    payload = research_event_resolution_authority_watchlist_report_payload(built)
    encoded = research_event_resolution_authority_watchlist_report_json(built)
    assert encoded == json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(
            digest_payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()

    assert payload["derived_validation_digest"] == built.derived_validation_digest
    assert built.derived_validation_digest == expected_digest
    assert payload["authority_count"] == "1.000000"
    assert payload["rows"][0]["event_digest"] == hashlib.sha256(
        RAW_EVENT_REFERENCE.encode("utf-8"),
    ).hexdigest()
    assert payload["rows"][0]["authority_digest"] == hashlib.sha256(
        RAW_AUTHORITY_REFERENCE.encode("utf-8"),
    ).hexdigest()
    assert payload["rows"][0]["watchlist_score"] == "0.020000"
    assert payload["paper_only"] is True
    assert RAW_EVENT_REFERENCE not in encoded
    assert RAW_AUTHORITY_REFERENCE not in encoded
    assert "authority.example" not in encoded
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(type(value) is int for value in walk_values(payload))
    assert not unsafe_public_fragments(payload)
    validate_research_event_resolution_authority_watchlist_digest(built)


def test_dataclasses_validate_flags_types_statuses_and_digest_tampering() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    class DecimalSubclass(Decimal):
        pass

    built = report((watch_item(),))
    assert is_dataclass(built)
    assert is_dataclass(built.rows[0])
    assert RESEARCH_EVENT_RESOLUTION_AUTHORITY_WATCHLIST_STATUSES == (
        "pass",
        "watch",
        "block",
    )

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].watchlist_score = Decimal("0")  # type: ignore[misc]
    with pytest.raises(TypeError, match="does not support subclassing"):

        class RowSubclass(ResearchEventResolutionAuthorityWatchlistRow):
            pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report((), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="last_checked_at must be timezone-aware"):
        watch_item(last_checked_at=datetime(2026, 7, 9, 12, 0, tzinfo=NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="last_checked_at must be a datetime"):
        watch_item(last_checked_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="last_checked_at must not be after generated_at"):
        report((watch_item(last_checked_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="deadline_at must not be before generated_at"):
        report((watch_item(deadline_at=GENERATED_AT - timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="expected_check_cadence_seconds must be a Decimal"):
        watch_item(expected_check_cadence_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="verification_coverage must be a Decimal"):
        watch_item(verification_coverage=DecimalSubclass("0.5"))
    with pytest.raises(ValueError, match="unresolved_dependency_count"):
        watch_item(unresolved_dependency_count=Decimal("1.5"))
    with pytest.raises(ValueError, match="reason_code contains unsafe text"):
        watch_item(reason_codes=("market_slug",))
    with pytest.raises(ValueError, match="reason_code must be supported"):
        watch_item(reason_codes=("opaque_internal_id",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(ResearchEventResolutionAuthorityWatchlistConfig(), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="ready")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)


def test_public_digest_revalidates_flags_and_canonical_row_reasons() -> None:
    built = report((watch_item(),))

    object.__setattr__(built, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        research_event_resolution_authority_watchlist_report_digest(built)
    object.__setattr__(built, "paper_only", True)

    object.__setattr__(built.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        research_event_resolution_authority_watchlist_report_digest(built)
    object.__setattr__(built.rows[0], "readonly", True)

    object.__setattr__(built.rows[0], "reason_codes", ("opaque_internal_id",))
    object.__setattr__(built, "reason_codes", ("opaque_internal_id",))
    with pytest.raises(ValueError, match="reason_code must be supported"):
        research_event_resolution_authority_watchlist_report_digest(built)


def test_public_api_has_no_io_execution_or_unsafe_payload_surface() -> None:
    payload = research_event_resolution_authority_watchlist_report_payload(
        report((watch_item(),)),
    )
    assert not unsafe_public_fragments(payload)

    for public_name in api.__all__:
        assert not any(fragment in public_name.lower() for fragment in UNSAFE_FRAGMENTS)

    for cls in (
        ResearchEventResolutionAuthorityWatchlistConfig,
        ResearchEventResolutionAuthorityWatchlistInput,
        ResearchEventResolutionAuthorityWatchlistRow,
        ResearchEventResolutionAuthorityWatchlistReport,
    ):
        for field in fields(cls):
            assert not any(fragment in field.name.lower() for fragment in UNSAFE_FRAGMENTS)

    source = Path(
        "src/polymarket_alpha_lab/research_event_resolution_authority_watchlist_report.py",
    ).read_text(encoding="utf-8")
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


UNSAFE_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
)


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in walk_values(child))
    return (value,)


def unsafe_public_fragments(value: object) -> tuple[str, ...]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized_key = key.lower()
            findings.extend(fragment for fragment in UNSAFE_FRAGMENTS if fragment in normalized_key)
            findings.extend(unsafe_public_fragments(item))
    elif isinstance(value, list):
        for item in value:
            findings.extend(unsafe_public_fragments(item))
    elif type(value) is str:
        normalized_value = value.lower()
        findings.extend(fragment for fragment in UNSAFE_FRAGMENTS if fragment in normalized_value)
        if "://" in normalized_value:
            findings.append("url_scheme")
    return tuple(findings)
