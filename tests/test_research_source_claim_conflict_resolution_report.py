from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_source_claim_conflict_resolution_report as api
from polymarket_alpha_lab.research_source_claim_conflict_resolution_report import (
    DEFAULT_RESEARCH_SOURCE_CLAIM_CONFLICT_RESOLUTION_REPORT_CONFIG_VERSION,
    ResearchSourceClaimConflictResolutionConfig,
    ResearchSourceClaimConflictResolutionInput,
    ResearchSourceClaimConflictResolutionReport,
    ResearchSourceClaimConflictResolutionRow,
    build_research_source_claim_conflict_resolution_report,
    research_source_claim_conflict_resolution_report_public_payload,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def conflict_input(
    *,
    claim_ref: str = "claim_ref_alpha",
    authority_tier: str = "official",
    freshness_lag_seconds: Decimal = d("1800.000000"),
    corroboration_count: Decimal = d("3.000000"),
    resolution_dependency: str = "none",
) -> ResearchSourceClaimConflictResolutionInput:
    return ResearchSourceClaimConflictResolutionInput(
        claim_ref=claim_ref,
        authority_tier=authority_tier,
        freshness_lag_seconds=freshness_lag_seconds,
        corroboration_count=corroboration_count,
        resolution_dependency=resolution_dependency,
    )


def build_report(
    *inputs: ResearchSourceClaimConflictResolutionInput,
    config: ResearchSourceClaimConflictResolutionConfig | None = None,
) -> ResearchSourceClaimConflictResolutionReport:
    return build_research_source_claim_conflict_resolution_report(
        inputs,
        generated_at=NOW,
        config=config,
    )


def test_deterministic_public_payload_and_digest_validation() -> None:
    forward = build_report(
        conflict_input(claim_ref="claim_ref_beta", authority_tier="secondary"),
        conflict_input(claim_ref="claim_ref_alpha"),
    )
    reverse = build_report(
        conflict_input(claim_ref="claim_ref_alpha"),
        conflict_input(claim_ref="claim_ref_beta", authority_tier="secondary"),
    )

    assert forward == reverse
    assert forward.derived_validation_digest == reverse.derived_validation_digest
    payload = research_source_claim_conflict_resolution_report_public_payload(forward)
    assert payload == forward.public_payload
    assert payload == reverse.public_payload
    assert json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["conflict_count"] == "2.000000"
    assert payload["pass_count"] == "1.000000"
    assert payload["watch_count"] == "1.000000"
    assert payload["derived_validation_digest"] == forward.derived_validation_digest
    assert len(forward.derived_validation_digest) == 64
    api.validate_research_source_claim_conflict_resolution_public_payload(payload)

    tampered = dict(payload)
    tampered["watch_count"] = "0.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_research_source_claim_conflict_resolution_public_payload(tampered)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(forward, derived_validation_digest="0" * 64)


def test_public_payload_prevents_raw_identifiers_and_live_surfaces() -> None:
    report = build_report(conflict_input(), conflict_input(claim_ref="claim_ref_beta"))
    payload = report.public_payload

    _assert_public_payload_is_sanitized(payload)
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)

    for public_name in api.__all__:
        _assert_safe_public_key(public_name)
    for dataclass_type in (
        ResearchSourceClaimConflictResolutionConfig,
        ResearchSourceClaimConflictResolutionInput,
        ResearchSourceClaimConflictResolutionRow,
        ResearchSourceClaimConflictResolutionReport,
    ):
        for field in fields(dataclass_type):
            _assert_safe_public_key(field.name)

    source = Path(
        "src/polymarket_alpha_lab/"
        "research_source_claim_conflict_resolution_report.py",
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

    with pytest.raises(ValueError, match="claim_ref"):
        conflict_input(claim_ref="market_slug_123")
    with pytest.raises(ValueError, match="public payload"):
        api.validate_research_source_claim_conflict_resolution_public_payload(
            {
                **payload,
                "operator_token": "secret",
            },
        )


def test_custom_config_thresholds_change_triage_without_changing_version() -> None:
    base = build_report(
        conflict_input(
            claim_ref="claim_ref_custom",
            authority_tier="primary",
            freshness_lag_seconds=d("3000.000000"),
            corroboration_count=d("3.000000"),
            resolution_dependency="none",
        ),
    )
    strict_config = ResearchSourceClaimConflictResolutionConfig(
        min_pass_authority_score=d("0.900000"),
        max_pass_freshness_lag_seconds=d("1200.000000"),
        min_pass_corroboration_count=d("4.000000"),
    )
    strict = build_report(
        conflict_input(
            claim_ref="claim_ref_custom",
            authority_tier="primary",
            freshness_lag_seconds=d("3000.000000"),
            corroboration_count=d("3.000000"),
            resolution_dependency="none",
        ),
        config=strict_config,
    )

    assert base.rows[0].status == "pass"
    assert strict.rows[0].status == "watch"
    assert strict.status == "watch"
    assert strict.config_version == (
        DEFAULT_RESEARCH_SOURCE_CLAIM_CONFLICT_RESOLUTION_REPORT_CONFIG_VERSION
    )
    assert strict.rows[0].reason_codes == (
        "claim_conflict_authority_watch",
        "claim_conflict_freshness_watch",
        "claim_conflict_corroboration_watch",
        "claim_conflict_dependency_clear",
        "claim_conflict_resolution_watch",
    )


def test_row_and_report_consistency_validation() -> None:
    report = build_report(conflict_input())
    row = report.rows[0]

    with pytest.raises(ValueError, match="pass rows"):
        replace(
            row,
            reason_codes=(
                "claim_conflict_authority_pass",
                "claim_conflict_resolution_pass",
            ),
        )
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("claim_conflict_empty",))


def test_status_boundaries_for_pass_watch_and_block() -> None:
    report = build_report(
        conflict_input(
            claim_ref="claim_ref_exact_pass",
            authority_tier="primary",
            freshness_lag_seconds=d("3600.000000"),
            corroboration_count=d("3.000000"),
            resolution_dependency="none",
        ),
        conflict_input(
            claim_ref="claim_ref_watch",
            authority_tier="secondary",
            freshness_lag_seconds=d("86400.000000"),
            corroboration_count=d("2.000000"),
            resolution_dependency="pending",
        ),
        conflict_input(
            claim_ref="claim_ref_block_authority",
            authority_tier="community",
            freshness_lag_seconds=d("1800.000000"),
            corroboration_count=d("3.000000"),
            resolution_dependency="none",
        ),
        conflict_input(
            claim_ref="claim_ref_block_dependency",
            authority_tier="official",
            freshness_lag_seconds=d("1800.000000"),
            corroboration_count=d("3.000000"),
            resolution_dependency="blocked",
        ),
    )

    rows = {row.claim_ref: row for row in report.rows}
    assert rows["claim_ref_exact_pass"].status == "pass"
    assert rows["claim_ref_watch"].status == "watch"
    assert rows["claim_ref_watch"].freshness_score == d("0.000000")
    assert rows["claim_ref_block_authority"].status == "block"
    assert rows["claim_ref_block_dependency"].status == "block"
    assert report.status == "block"
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("2.000000")


def test_validation_enforces_frozen_exact_types_decimals_and_flags() -> None:
    report = build_report(conflict_input())

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadRow(ResearchSourceClaimConflictResolutionRow):
            pass

    with pytest.raises(ValueError, match="freshness_lag_seconds must be a Decimal"):
        conflict_input(freshness_lag_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_research_source_claim_conflict_resolution_report(
            (),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="authority_tier must be supported"):
        conflict_input(authority_tier="blog")
    with pytest.raises(ValueError, match="resolution_dependency must be supported"):
        conflict_input(resolution_dependency="external")
    with pytest.raises(ValueError, match="config readonly must be True"):
        ResearchSourceClaimConflictResolutionConfig(readonly=False)
    with pytest.raises(ValueError, match="input report_only must be True"):
        replace(conflict_input(), report_only=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(report, paper_only=False)


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
        forbidden_fragments = (
            "://",
            "?",
            "raw",
            "candidate",
            "market_id",
            "market_slug",
            "slug",
            "question",
            "source_url",
            "source_text",
            "source text",
            "dsn",
            "table_name",
            "token",
            "wallet",
            "order",
            "trade",
            "live_trading",
            "sizing",
            "recommend",
        )
        assert not any(fragment in lowered for fragment in forbidden_fragments)
    elif type(value) is bool:
        return
    else:
        assert not isinstance(value, (Decimal, datetime, float, int))


def _assert_safe_public_key(key: str) -> None:
    lowered = key.lower()
    forbidden_fragments = (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "source_url",
        "source_text",
        "raw",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "network",
        "database",
        "sizing",
        "recommendation",
        "recommend",
        "live_trading",
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
        assert type(value) is Decimal
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
