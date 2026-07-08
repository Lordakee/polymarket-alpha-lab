from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import ast
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_source_claim_resolution_provenance_report as api
from polymarket_alpha_lab.research_source_claim_resolution_provenance_report import (
    ResearchSourceClaimResolutionProvenanceConfig,
    ResearchSourceClaimResolutionProvenanceObservation,
    ResearchSourceClaimResolutionProvenanceReport,
    ResearchSourceClaimResolutionProvenanceRow,
    build_research_source_claim_resolution_provenance_report,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    claim_group: str = "claim_group_alpha",
    source_family: str = "official",
    source_tier: str = "official",
    retrieved_at: datetime = NOW - timedelta(minutes=30),
    provenance_completeness: Decimal = Decimal("1.000000"),
    supports_resolution: bool = True,
    contradicts_resolution: bool = False,
    has_capture_timestamp: bool = True,
    has_resolution_timestamp: bool = True,
    has_source_family_trace: bool = True,
    has_method_trace: bool = True,
) -> ResearchSourceClaimResolutionProvenanceObservation:
    return ResearchSourceClaimResolutionProvenanceObservation(
        claim_group=claim_group,
        source_family=source_family,
        source_tier=source_tier,
        retrieved_at=retrieved_at,
        provenance_completeness=provenance_completeness,
        supports_resolution=supports_resolution,
        contradicts_resolution=contradicts_resolution,
        has_capture_timestamp=has_capture_timestamp,
        has_resolution_timestamp=has_resolution_timestamp,
        has_source_family_trace=has_source_family_trace,
        has_method_trace=has_method_trace,
    )


def report(
    *observations: ResearchSourceClaimResolutionProvenanceObservation,
    config: ResearchSourceClaimResolutionProvenanceConfig | None = None,
) -> ResearchSourceClaimResolutionProvenanceReport:
    return build_research_source_claim_resolution_provenance_report(
        observations,
        generated_at=NOW.astimezone(UTC),
        config=config,
    )


def test_empty_input_returns_report_only_block_status() -> None:
    provenance_report = report()

    assert provenance_report.status == "block"
    assert provenance_report.report_next_step == (
        "block_report_only_source_claim_resolution_provenance_review"
    )
    assert provenance_report.claim_group_count == d("0.000000")
    assert provenance_report.source_family_count == d("0.000000")
    assert provenance_report.official_source_count == d("0.000000")
    assert provenance_report.pass_count == d("0.000000")
    assert provenance_report.watch_count == d("0.000000")
    assert provenance_report.block_count == d("0.000000")
    assert provenance_report.average_provenance_completeness == d("0.000000")
    assert provenance_report.average_retrieval_freshness == d("0.000000")
    assert provenance_report.average_contradiction_risk == d("0.000000")
    assert provenance_report.reason_codes == (
        "source_claim_resolution_provenance_empty",
    )
    assert provenance_report.rows == ()
    assert provenance_report.paper_only is True
    assert provenance_report.report_only is True
    assert provenance_report.readonly is True


def test_passes_with_complete_fresh_official_quorum_without_contradiction() -> None:
    provenance_report = report(
        observation(source_family="official"),
        observation(source_family="resolution_agency"),
        observation(source_family="primary_archive", source_tier="primary"),
    )

    row = provenance_report.rows[0]
    assert provenance_report.status == "pass"
    assert provenance_report.report_next_step == (
        "allow_report_only_source_claim_resolution_provenance_review"
    )
    assert provenance_report.claim_group_count == d("1.000000")
    assert provenance_report.source_family_count == d("3.000000")
    assert provenance_report.official_source_count == d("2.000000")
    assert provenance_report.pass_count == d("1.000000")
    assert provenance_report.watch_count == d("0.000000")
    assert provenance_report.block_count == d("0.000000")
    assert provenance_report.average_provenance_completeness == d("1.000000")
    assert provenance_report.average_retrieval_freshness == d("0.968750")
    assert provenance_report.average_contradiction_risk == d("0.000000")
    assert row.status == "pass"
    assert row.source_count == d("3.000000")
    assert row.official_source_count == d("2.000000")
    assert row.official_source_quorum_met is True
    assert row.provenance_completeness_score == d("1.000000")
    assert row.retrieval_freshness_score == d("0.968750")
    assert row.contradiction_risk_score == d("0.000000")
    assert row.reason_codes == (
        "source_claim_resolution_fresh_retrieval",
        "source_claim_resolution_official_quorum_met",
        "source_claim_resolution_provenance_complete",
        "source_claim_resolution_provenance_pass",
    )


def test_minor_contradiction_routes_to_watch_instead_of_crashing() -> None:
    provenance_report = report(
        observation(source_family="official"),
        observation(source_family="resolution_agency"),
        observation(source_family="primary_archive", source_tier="primary"),
        observation(
            source_family="independent_archive",
            source_tier="primary",
            supports_resolution=False,
            contradicts_resolution=True,
        ),
    )

    row = provenance_report.rows[0]
    assert row.status == "watch"
    assert row.contradiction_risk_score == d("0.250000")
    assert "source_claim_resolution_provenance_watch" in row.reason_codes
    assert provenance_report.status == "watch"


def test_stale_low_quorum_and_contradictory_groups_are_sorted_and_blocked() -> None:
    provenance_report = report(
        observation(
            claim_group="claim_group_beta",
            source_family="community_archive",
            source_tier="secondary",
            retrieved_at=NOW - timedelta(hours=30),
            provenance_completeness=d("0.300000"),
            supports_resolution=False,
            contradicts_resolution=True,
            has_method_trace=False,
        ),
        observation(
            claim_group="claim_group_alpha",
            source_family="official",
            source_tier="official",
            retrieved_at=NOW - timedelta(hours=2),
            provenance_completeness=d("0.680000"),
            has_capture_timestamp=False,
        ),
        observation(
            claim_group="claim_group_alpha",
            source_family="primary_archive",
            source_tier="primary",
            retrieved_at=NOW - timedelta(hours=2),
            provenance_completeness=d("0.720000"),
            has_capture_timestamp=False,
        ),
    )

    assert provenance_report.status == "block"
    assert tuple(row.claim_group for row in provenance_report.rows) == (
        "claim_group_alpha",
        "claim_group_beta",
    )
    watch_row, block_row = provenance_report.rows
    assert watch_row.status == "watch"
    assert watch_row.provenance_completeness_score == d("0.700000")
    assert watch_row.official_source_quorum_met is False
    assert watch_row.reason_codes == (
        "source_claim_resolution_capture_trace_gap",
        "source_claim_resolution_official_quorum_gap",
        "source_claim_resolution_provenance_watch",
    )
    assert block_row.status == "block"
    assert block_row.retrieval_freshness_score == d("0.000000")
    assert block_row.contradiction_risk_score == d("1.000000")
    assert block_row.reason_codes == (
        "source_claim_resolution_contradiction_block",
        "source_claim_resolution_method_trace_gap",
        "source_claim_resolution_official_quorum_gap",
        "source_claim_resolution_provenance_block",
        "source_claim_resolution_provenance_incomplete",
        "source_claim_resolution_stale_retrieval",
    )
    assert provenance_report.reason_codes == (
        "source_claim_resolution_capture_trace_gap",
        "source_claim_resolution_contradiction_block",
        "source_claim_resolution_method_trace_gap",
        "source_claim_resolution_official_quorum_gap",
        "source_claim_resolution_provenance_block",
        "source_claim_resolution_provenance_incomplete",
        "source_claim_resolution_provenance_watch",
        "source_claim_resolution_stale_retrieval",
    )


def test_payload_serialization_is_deterministic_and_digest_validated() -> None:
    forward = report(
        observation(claim_group="claim_group_beta", source_family="official"),
        observation(
            claim_group="claim_group_alpha",
            source_family="resolution_agency",
        ),
        observation(
            claim_group="claim_group_alpha",
            source_family="official",
        ),
    )
    reverse = report(
        observation(
            claim_group="claim_group_alpha",
            source_family="official",
        ),
        observation(
            claim_group="claim_group_alpha",
            source_family="resolution_agency",
        ),
        observation(claim_group="claim_group_beta", source_family="official"),
    )

    assert forward == reverse
    payload = api.research_source_claim_resolution_provenance_report_payload(forward)
    assert payload == forward.payload
    assert json.dumps(payload, sort_keys=True)
    assert payload["status"] == "watch"
    assert payload["claim_group_count"] == "2.000000"
    assert payload["average_provenance_completeness"] == "1.000000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["derived_validation_digest"] == forward.derived_validation_digest
    assert len(forward.derived_validation_digest) == 64

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(forward, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(forward, generated_at=NOW + timedelta(seconds=1))


def test_validation_enforces_frozen_dataclasses_decimal_numerics_and_flags() -> None:
    provenance_report = report(
        observation(source_family="official"),
        observation(source_family="resolution_agency"),
    )

    with pytest.raises(FrozenInstanceError):
        provenance_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadRow(ResearchSourceClaimResolutionProvenanceRow):
            pass

    with pytest.raises(ValueError, match="provenance_completeness must be a Decimal"):
        observation(provenance_completeness=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_research_source_claim_resolution_provenance_report(
            (),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="retrieved_at must not be after generated_at"):
        report(observation(retrieved_at=NOW + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="source_tier must be supported"):
        observation(source_tier="blog")
    with pytest.raises(ValueError, match="config report_only must be True"):
        ResearchSourceClaimResolutionProvenanceConfig(report_only=False)
    with pytest.raises(ValueError, match="observation readonly must be True"):
        replace(observation(), readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(provenance_report, paper_only=False)


def test_public_payload_has_no_raw_identifiers_or_unsafe_surfaces() -> None:
    provenance_report = report(
        observation(source_family="official"),
        observation(source_family="resolution_agency"),
    )
    payload = provenance_report.payload

    _assert_public_payload_is_sanitized(payload)
    _assert_no_non_decimal_public_numbers(provenance_report)
    _assert_no_decimal_objects(payload)

    for public_name in api.__all__:
        _assert_safe_public_key(public_name)
    for dataclass_type in (
        ResearchSourceClaimResolutionProvenanceConfig,
        ResearchSourceClaimResolutionProvenanceObservation,
        ResearchSourceClaimResolutionProvenanceRow,
        ResearchSourceClaimResolutionProvenanceReport,
    ):
        for field in fields(dataclass_type):
            _assert_safe_public_key(field.name)

    source = Path(
        "src/polymarket_alpha_lab/"
        "research_source_claim_resolution_provenance_report.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "ccxt",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden_name in forbidden_import_fragments:
        assert not hasattr(api, forbidden_name)


def _assert_public_payload_is_sanitized(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _assert_safe_public_key(key)
            _assert_public_payload_is_sanitized(child)
    elif isinstance(value, list):
        for child in value:
            _assert_public_payload_is_sanitized(child)
    elif isinstance(value, str):
        lowered = value.lower()
        assert "://" not in lowered
        assert "?" not in lowered
        assert "raw" not in lowered
        assert "wallet" not in lowered
        assert "order" not in lowered
        assert "trade" not in lowered
        assert "token" not in lowered
        assert "source text" not in lowered
    elif type(value) is bool:
        return
    else:
        assert not isinstance(value, (Decimal, datetime, float, int))


def _assert_safe_public_key(key: str) -> None:
    lowered = key.lower()
    forbidden_fragments = (
        "candidate",
        "market_id",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "auth",
        "network",
        "database",
        "db",
        "sizing",
        "recommendation",
        "recommend",
        "live",
    )
    assert not any(fragment in lowered for fragment in forbidden_fragments), key


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
