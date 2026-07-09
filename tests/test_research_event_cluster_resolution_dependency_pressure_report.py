from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_cluster_resolution_dependency_pressure_report import (
    RESEARCH_EVENT_CLUSTER_RESOLUTION_DEPENDENCY_PRESSURE_STATUSES,
    ResearchEventClusterResolutionDependencyPressureConfig,
    ResearchEventClusterResolutionDependencyPressureInput,
    ResearchEventClusterResolutionDependencyPressureReport,
    build_research_event_cluster_resolution_dependency_pressure_report,
    research_event_cluster_resolution_dependency_pressure_digest,
    research_event_cluster_resolution_dependency_pressure_payload,
    validate_research_event_cluster_resolution_dependency_pressure_digest,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=10)
RAW_CLUSTER_REFERENCE = "candidate-a-market-slug-question-url-token-table-wallet-order-trade"


def dependency_input(
    cluster_reference: str = RAW_CLUSTER_REFERENCE,
    *,
    observed_at: datetime = OBSERVED_AT,
    event_count: Decimal = Decimal("5"),
    dependent_resolution_count: Decimal = Decimal("4"),
    unresolved_dependency_count: Decimal = Decimal("1"),
    upstream_blocker_count: Decimal = Decimal("0"),
    stale_dependency_count: Decimal = Decimal("0"),
    conflict_dependency_count: Decimal = Decimal("0"),
    dependency_coverage_score: Decimal = Decimal("0.90"),
    longest_dependency_age_hours: Decimal = Decimal("4"),
    minimum_expected_resolution_buffer_hours: Decimal = Decimal("24"),
    review_acknowledged: bool = True,
    reason_codes: tuple[str, ...] = ("dependency_map_ready",),
) -> ResearchEventClusterResolutionDependencyPressureInput:
    return ResearchEventClusterResolutionDependencyPressureInput(
        cluster_reference=cluster_reference,
        observed_at=observed_at,
        event_count=event_count,
        dependent_resolution_count=dependent_resolution_count,
        unresolved_dependency_count=unresolved_dependency_count,
        upstream_blocker_count=upstream_blocker_count,
        stale_dependency_count=stale_dependency_count,
        conflict_dependency_count=conflict_dependency_count,
        dependency_coverage_score=dependency_coverage_score,
        longest_dependency_age_hours=longest_dependency_age_hours,
        minimum_expected_resolution_buffer_hours=minimum_expected_resolution_buffer_hours,
        review_acknowledged=review_acknowledged,
        reason_codes=reason_codes,
    )


def test_empty_input_returns_report_only_pass_digest() -> None:
    report = build_research_event_cluster_resolution_dependency_pressure_report(
        (),
        generated_at=GENERATED_AT,
        config=ResearchEventClusterResolutionDependencyPressureConfig(),
    )

    assert report == ResearchEventClusterResolutionDependencyPressureReport(
        generated_at=GENERATED_AT,
        config_version="research_event_cluster_resolution_dependency_pressure_report_v1",
        row_count=Decimal("0.0000"),
        pass_count=Decimal("0.0000"),
        watch_count=Decimal("0.0000"),
        block_count=Decimal("0.0000"),
        total_event_count=Decimal("0.0000"),
        total_dependent_resolution_count=Decimal("0.0000"),
        total_unresolved_dependency_count=Decimal("0.0000"),
        average_dependency_pressure_score=Decimal("0.0000"),
        highest_dependency_pressure_score=Decimal("0.0000"),
        weakest_dependency_coverage_score=Decimal("0.0000"),
        status="pass",
        rows=(),
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_clear_dependency_cluster_scores_pass_with_decimal_only_dimensions() -> None:
    report = build_research_event_cluster_resolution_dependency_pressure_report(
        (dependency_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventClusterResolutionDependencyPressureConfig(),
    )

    row = report.rows[0]
    assert row.cluster_digest == hashlib.sha256(RAW_CLUSTER_REFERENCE.encode("utf-8")).hexdigest()
    assert row.dependency_density_score == Decimal("0.8000")
    assert row.unresolved_dependency_ratio == Decimal("0.2500")
    assert row.blocker_pressure_score == Decimal("0.0000")
    assert row.stale_dependency_ratio == Decimal("0.0000")
    assert row.conflict_dependency_ratio == Decimal("0.0000")
    assert row.dependency_coverage_score == Decimal("0.9000")
    assert row.timing_buffer_pressure_score == Decimal("0.1667")
    assert row.dependency_pressure_score == Decimal("0.0942")
    assert row.status == "pass"
    assert row.reason_codes == ("dependency_map_ready", "pass")
    assert report.status == "pass"
    assert report.pass_count == Decimal("1.0000")


def test_blocked_dependency_cluster_flags_all_pressure_dimensions() -> None:
    report = build_research_event_cluster_resolution_dependency_pressure_report(
        (
            dependency_input(
                event_count=Decimal("6"),
                dependent_resolution_count=Decimal("5"),
                unresolved_dependency_count=Decimal("4"),
                upstream_blocker_count=Decimal("3"),
                stale_dependency_count=Decimal("4"),
                conflict_dependency_count=Decimal("3"),
                dependency_coverage_score=Decimal("0.4"),
                longest_dependency_age_hours=Decimal("30"),
                minimum_expected_resolution_buffer_hours=Decimal("12"),
                review_acknowledged=False,
                reason_codes=(),
            ),
        ),
        generated_at=GENERATED_AT,
        config=ResearchEventClusterResolutionDependencyPressureConfig(),
    )

    row = report.rows[0]
    assert row.unresolved_dependency_ratio == Decimal("0.8000")
    assert row.blocker_pressure_score == Decimal("0.6000")
    assert row.stale_dependency_ratio == Decimal("0.8000")
    assert row.conflict_dependency_ratio == Decimal("0.6000")
    assert row.timing_buffer_pressure_score == Decimal("1.0000")
    assert row.dependency_pressure_score == Decimal("0.7200")
    assert row.status == "block"
    assert row.reason_codes == (
        "block",
        "conflict_dependency_pressure",
        "dependency_coverage_gap",
        "dependency_pressure_elevated",
        "review_acknowledgement_missing",
        "stale_dependency_pressure",
        "timing_buffer_pressure",
        "unresolved_dependency_pressure",
        "upstream_blocker_pressure",
    )
    assert report.status == "block"
    assert report.block_count == Decimal("1.0000")


def test_rows_reason_counts_and_digest_are_deterministic() -> None:
    config = ResearchEventClusterResolutionDependencyPressureConfig()
    inputs = (
        dependency_input("z-cluster", reason_codes=("zeta",)),
        dependency_input(
            "a-cluster",
            unresolved_dependency_count=Decimal("2"),
            reason_codes=("alpha",),
        ),
        dependency_input(
            "m-cluster",
            dependency_coverage_score=Decimal("0.4"),
            reason_codes=("beta",),
        ),
    )

    report = build_research_event_cluster_resolution_dependency_pressure_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
    )
    reversed_report = build_research_event_cluster_resolution_dependency_pressure_report(
        tuple(reversed(inputs)),
        generated_at=GENERATED_AT,
        config=config,
    )

    assert [row.cluster_digest for row in report.rows] == sorted(
        row.cluster_digest for row in report.rows
    )
    assert reversed_report.rows == report.rows
    assert reversed_report.derived_validation_digest == report.derived_validation_digest
    assert report.reason_code_counts == (
        ("alpha", Decimal("1.0000")),
        ("beta", Decimal("1.0000")),
        ("block", Decimal("1.0000")),
        ("dependency_coverage_gap", Decimal("1.0000")),
        ("pass", Decimal("1.0000")),
        ("unresolved_dependency_pressure", Decimal("1.0000")),
        ("watch", Decimal("1.0000")),
        ("zeta", Decimal("1.0000")),
    )


def test_payload_helper_uses_decimal_strings_redacts_raw_references_and_validates_digest() -> None:
    report = build_research_event_cluster_resolution_dependency_pressure_report(
        (dependency_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventClusterResolutionDependencyPressureConfig(),
    )

    payload = research_event_cluster_resolution_dependency_pressure_payload(report)
    encoded = json.dumps(payload, sort_keys=True)
    digest = research_event_cluster_resolution_dependency_pressure_digest(report)

    assert payload["derived_validation_digest"] == report.derived_validation_digest == digest
    assert len(digest) == 64
    int(digest, 16)
    assert payload["rows"][0]["dependency_pressure_score"] == "0.0942"
    assert payload["row_count"] == "1.0000"
    assert payload["reason_code_counts"][0][1] == "1.0000"
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert RAW_CLUSTER_REFERENCE not in encoded
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is int for value in _walk_values(payload))
    assert "Decimal" not in encoded
    assert not _unsafe_public_fragments(payload)
    validate_research_event_cluster_resolution_dependency_pressure_digest(report)

    tampered_payload = dict(payload)
    tampered_payload["row_count"] = "2.0000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_cluster_resolution_dependency_pressure_payload(tampered_payload)

    unsafe_key_payload = dict(payload)
    unsafe_key_payload["market_slug"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_cluster_resolution_dependency_pressure_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [dict(payload["rows"][0], cluster_digest="candidate-a")]
    with pytest.raises(ValueError, match="unsafe"):
        research_event_cluster_resolution_dependency_pressure_payload(unsafe_value_payload)


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
        build_research_event_cluster_resolution_dependency_pressure_report(
            (),
            generated_at=datetime(2026, 7, 9, 12, 0),
            config=ResearchEventClusterResolutionDependencyPressureConfig(),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        dependency_input(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        dependency_input(observed_at=datetime(2026, 7, 9, 12, 0, tzinfo=NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        dependency_input(observed_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_research_event_cluster_resolution_dependency_pressure_report(
            (dependency_input(observed_at=GENERATED_AT + timedelta(seconds=1)),),
            generated_at=GENERATED_AT,
            config=ResearchEventClusterResolutionDependencyPressureConfig(),
        )
    with pytest.raises(ValueError, match="event_count must be a Decimal"):
        dependency_input(event_count=5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="dependency_coverage_score must be a Decimal"):
        dependency_input(dependency_coverage_score=DecimalSubclass("0.1"))
    with pytest.raises(ValueError, match="dependent_resolution_count"):
        dependency_input(event_count=Decimal("4"), dependent_resolution_count=Decimal("5"))
    with pytest.raises(ValueError, match="review_acknowledged must be a bool"):
        dependency_input(review_acknowledged=True)  # sanity check first
        dependency_input(review_acknowledged="yes")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pressure weights"):
        ResearchEventClusterResolutionDependencyPressureConfig(
            timing_buffer_pressure_weight=Decimal("0.2000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        dataclasses.replace(
            ResearchEventClusterResolutionDependencyPressureConfig(),
            paper_only=False,
        )

    report = build_research_event_cluster_resolution_dependency_pressure_report(
        (dependency_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventClusterResolutionDependencyPressureConfig(),
    )
    with pytest.raises(ValueError, match="status"):
        dataclasses.replace(report, status="blocked")
    with pytest.raises(ValueError, match="status"):
        dataclasses.replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        dataclasses.replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="reason_code contains unsafe text"):
        dependency_input(reason_codes=("market_slug",))


def test_public_dataclasses_are_frozen_reject_subclasses_and_export_safe_statuses() -> None:
    report = build_research_event_cluster_resolution_dependency_pressure_report(
        (dependency_input(),),
        generated_at=GENERATED_AT,
        config=ResearchEventClusterResolutionDependencyPressureConfig(),
    )
    config = ResearchEventClusterResolutionDependencyPressureConfig()
    input_row = dependency_input()

    assert RESEARCH_EVENT_CLUSTER_RESOLUTION_DEPENDENCY_PRESSURE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert dataclasses.is_dataclass(config)
    assert dataclasses.is_dataclass(input_row)
    assert dataclasses.is_dataclass(report.rows[0])
    assert dataclasses.is_dataclass(report)

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        input_row.cluster_reference = "changed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(ResearchEventClusterResolutionDependencyPressureConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        class InputSubclass(ResearchEventClusterResolutionDependencyPressureInput):
            pass


def test_static_module_has_no_forbidden_side_effect_behavior() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_event_cluster_resolution_dependency_pressure_report.py",
    ).read_text(encoding="utf-8")
    forbidden_terms = (
        "requests",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "open(",
        "broker",
        "private_key",
        "recommendation",
        "sizing",
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
        "url",
        "http",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "auth",
        "network",
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
