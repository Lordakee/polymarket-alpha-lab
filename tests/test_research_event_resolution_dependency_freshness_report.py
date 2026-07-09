from __future__ import annotations

import ast
import dataclasses
import json
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_resolution_dependency_freshness_report import (
    ResearchEventResolutionDependencyFreshnessConfig,
    ResearchEventResolutionDependencyFreshnessInput,
    ResearchEventResolutionDependencyFreshnessReport,
    build_research_event_resolution_dependency_freshness_report,
    research_event_resolution_dependency_freshness_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(hours=1)
RAW_EVENT_REFERENCE = (
    "candidate-a raw market slug and question https://example.invalid/markets/secret-token"
)
RAW_DEPENDENCY_REFERENCE = (
    "official table wallet order trade live url postgresql://user:token@localhost/db"
)


def dependency(
    event_reference: str = RAW_EVENT_REFERENCE,
    dependency_reference: str = RAW_DEPENDENCY_REFERENCE,
    *,
    observed_at: datetime = OBSERVED_AT,
    latest_verified_at: datetime | None = GENERATED_AT,
    dependency_required_count: Decimal = Decimal("4"),
    dependency_verified_count: Decimal = Decimal("4"),
    source_count: Decimal = Decimal("3"),
    authoritative_source_count: Decimal = Decimal("3"),
    contradiction_count: Decimal = Decimal("0"),
    highest_contradiction_severity: Decimal = Decimal("0"),
    resolution_due_at: datetime | None = GENERATED_AT + timedelta(hours=48),
    timing_precision_hours: Decimal = Decimal("0"),
    ambiguity_issue_count: Decimal = Decimal("0"),
    verification_method_count: Decimal = Decimal("3"),
    required_verification_method_count: Decimal = Decimal("3"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchEventResolutionDependencyFreshnessInput:
    return ResearchEventResolutionDependencyFreshnessInput(
        event_reference=event_reference,
        dependency_reference=dependency_reference,
        observed_at=observed_at,
        latest_verified_at=latest_verified_at,
        dependency_required_count=dependency_required_count,
        dependency_verified_count=dependency_verified_count,
        source_count=source_count,
        authoritative_source_count=authoritative_source_count,
        contradiction_count=contradiction_count,
        highest_contradiction_severity=highest_contradiction_severity,
        resolution_due_at=resolution_due_at,
        timing_precision_hours=timing_precision_hours,
        ambiguity_issue_count=ambiguity_issue_count,
        verification_method_count=verification_method_count,
        required_verification_method_count=required_verification_method_count,
        reason_codes=reason_codes,
    )


def test_empty_input_returns_report_only_blocked_digest() -> None:
    report = build_research_event_resolution_dependency_freshness_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionDependencyFreshnessConfig(),
    )

    assert report == ResearchEventResolutionDependencyFreshnessReport(
        generated_at=GENERATED_AT,
        config_version="research_event_resolution_dependency_freshness_report_v0",
        row_count=Decimal("0"),
        pass_count=Decimal("0"),
        watch_count=Decimal("0"),
        block_count=Decimal("0"),
        average_freshness_score=Decimal("0"),
        weakest_freshness_score=Decimal("0"),
        report_status="block",
        reason_codes=("dependency_freshness_report_empty",),
        rows=(),
        reason_code_counts=(("dependency_freshness_report_empty", Decimal("1")),),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_scores_pass_watch_and_block_dependency_freshness_dimensions() -> None:
    report = build_research_event_resolution_dependency_freshness_report(
        (
            dependency(
                "raw pass candidate market question",
                "raw pass dependency url token",
            ),
            dependency(
                "raw watch candidate market question",
                "raw watch dependency url token",
                latest_verified_at=GENERATED_AT - timedelta(hours=36),
                dependency_verified_count=Decimal("3"),
                source_count=Decimal("2"),
                authoritative_source_count=Decimal("1"),
                contradiction_count=Decimal("1"),
                highest_contradiction_severity=Decimal("0.3000"),
                timing_precision_hours=Decimal("84"),
                ambiguity_issue_count=Decimal("1"),
                verification_method_count=Decimal("2"),
                required_verification_method_count=Decimal("4"),
            ),
            dependency(
                "raw block candidate market question",
                "raw block dependency url token",
                latest_verified_at=None,
                dependency_verified_count=Decimal("1"),
                source_count=Decimal("1"),
                authoritative_source_count=Decimal("0"),
                contradiction_count=Decimal("3"),
                highest_contradiction_severity=Decimal("0.9000"),
                resolution_due_at=None,
                timing_precision_hours=Decimal("168"),
                ambiguity_issue_count=Decimal("4"),
                verification_method_count=Decimal("0"),
                required_verification_method_count=Decimal("4"),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionDependencyFreshnessConfig(),
    )

    assert [row.dependency_status for row in report.rows] == ["block", "watch", "pass"]

    block_row, watch_row, pass_row = report.rows
    assert pass_row.freshness_score == Decimal("1.0000")
    assert pass_row.reason_codes == ("dependency_freshness_pass",)

    assert watch_row.dependency_completeness_score == Decimal("0.7500")
    assert watch_row.latest_verified_age_hours == Decimal("36.0000")
    assert watch_row.latest_verified_freshness_score == Decimal("0.5000")
    assert watch_row.source_authority_score == Decimal("0.5000")
    assert watch_row.contradiction_pressure_score == Decimal("0.4000")
    assert watch_row.timing_clarity_score == Decimal("0.5000")
    assert watch_row.ambiguity_risk_score == Decimal("0.2500")
    assert watch_row.verification_coverage_score == Decimal("0.5000")
    assert watch_row.freshness_score == Decimal("0.5850")
    assert watch_row.dependency_status == "watch"
    assert watch_row.reason_codes == (
        "ambiguity_risk_present",
        "contradiction_pressure_present",
        "dependency_freshness_watch",
        "incomplete_dependency_set",
        "stale_verified_dependency_age",
        "thin_verification_coverage",
        "unclear_resolution_timing",
        "weak_source_authority",
    )

    assert block_row.freshness_score == Decimal("0.0550")
    assert block_row.dependency_status == "block"
    assert "missing_verified_dependency_timestamp" in block_row.reason_codes

    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.block_count == Decimal("1")
    assert report.average_freshness_score == Decimal("0.5467")
    assert report.weakest_freshness_score == Decimal("0.0550")
    assert report.report_status == "block"
    assert report.reason_code_counts == (
        ("ambiguity_risk_present", Decimal("2")),
        ("contradiction_pressure_present", Decimal("2")),
        ("dependency_freshness_block", Decimal("1")),
        ("dependency_freshness_pass", Decimal("1")),
        ("dependency_freshness_watch", Decimal("1")),
        ("incomplete_dependency_set", Decimal("2")),
        ("missing_verified_dependency_timestamp", Decimal("1")),
        ("stale_verified_dependency_age", Decimal("2")),
        ("thin_verification_coverage", Decimal("2")),
        ("unclear_resolution_timing", Decimal("2")),
        ("weak_source_authority", Decimal("2")),
    )


def test_payload_uses_decimal_strings_digest_validation_and_no_raw_surfaces() -> None:
    report = build_research_event_resolution_dependency_freshness_report(
        (dependency(),),
        generated_at=GENERATED_AT,
        config=ResearchEventResolutionDependencyFreshnessConfig(),
    )

    payload = research_event_resolution_dependency_freshness_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["rows"][0]["freshness_score"] == "1.0000"
    assert payload["row_count"] == "1.0000"
    assert payload["reason_code_counts"][0][1] == "1.0000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    assert "Decimal" not in encoded

    for raw_fragment in (
        "candidate-a",
        "market",
        "slug",
        "question",
        "https://example.invalid",
        "postgresql://",
        "secret-token",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert raw_fragment not in encoded.lower()

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.0000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_resolution_dependency_freshness_payload(tampered_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["wallet_ref"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_resolution_dependency_freshness_payload(unsafe_key_payload)


def test_validation_rejects_invalid_decimals_datetimes_counts_and_flags() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_event_resolution_dependency_freshness_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
            config=ResearchEventResolutionDependencyFreshnessConfig(),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        dependency(observed_at=datetime(2026, 7, 8, 12, 0))  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        dependency(observed_at=datetime(2026, 7, 8, 12, 0, tzinfo=NoneOffsetTimezone()))  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        dependency(observed_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="dependency_required_count"):
        dependency(dependency_required_count=Decimal("0"))
    with pytest.raises(ValueError, match="dependency_verified_count"):
        dependency(dependency_verified_count=Decimal("5"))
    with pytest.raises(ValueError, match="highest_contradiction_severity"):
        dependency(highest_contradiction_severity=Decimal("1.1000"))
    with pytest.raises(ValueError, match="dependency_completeness_weight"):
        ResearchEventResolutionDependencyFreshnessConfig(
            dependency_completeness_weight=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="freshness weights"):
        ResearchEventResolutionDependencyFreshnessConfig(
            ambiguity_risk_weight=Decimal("0.2000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(ResearchEventResolutionDependencyFreshnessConfig(), paper_only=False)


def test_public_dataclasses_are_frozen_and_reject_subclasses() -> None:
    config = ResearchEventResolutionDependencyFreshnessConfig()
    input_row = dependency()

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        input_row.event_reference = "changed"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(ResearchEventResolutionDependencyFreshnessConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class InputSubclass(ResearchEventResolutionDependencyFreshnessInput):
            pass


def test_static_module_has_no_db_network_scraping_trading_or_filesystem_behavior() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_resolution_dependency_freshness_report.py",
    ).read_text(encoding="utf-8")
    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "selenium",
        "playwright",
        "beautifulsoup",
        "broker",
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
