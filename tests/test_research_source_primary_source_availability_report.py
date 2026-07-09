from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_primary_source_availability_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "max_fresh_age_seconds": d("3600.000000"),
        "block_stale_age_seconds": d("10800.000000"),
        "authority_watch_threshold": d("0.700000"),
        "authority_block_threshold": d("0.400000"),
        "minimum_corroborating_source_count": d("2.000000"),
        "access_watch_threshold": d("0.800000"),
        "access_block_threshold": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchSourcePrimarySourceAvailabilityConfig(**values)


def signal(
    review_scope: str,
    *,
    primary_source_available: bool = True,
    observed_seconds_ago: int | None = 900,
    primary_evidence_count: Decimal = d("1.000000"),
    authority_score: Decimal = d("0.950000"),
    corroborating_source_count: Decimal = d("3.000000"),
    access_success_ratio: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourcePrimarySourceAvailabilitySignal(
        review_scope=review_scope,
        primary_source_available=primary_source_available,
        latest_primary_evidence_at=(
            None
            if observed_seconds_ago is None
            else GENERATED_AT - timedelta(seconds=observed_seconds_ago)
        ),
        primary_evidence_count=primary_evidence_count,
        authority_score=authority_score,
        corroborating_source_count=corroborating_source_count,
        access_success_ratio=access_success_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_primary_source_availability_report(
        signals,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_blocks_without_exposing_live_or_market_surfaces() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourcePrimarySourceAvailabilityReport
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.review_scope_count == d("0.000000")
    assert report.available_primary_source_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.lowest_strategy_review_readiness_score == d("0.000000")
    assert report.highest_primary_evidence_age_seconds == d("0.000000")
    assert report.reason_codes == ("no_primary_source_scopes",)
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert report.derived_validation_digest == (
        module.research_source_primary_source_availability_report_digest(report)
    )
    assert module.validate_research_source_primary_source_availability_report_digest(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.research_source_primary_source_availability_report_payload(report)
    assert_no_unsafe_public_payload(payload)
    assert_no_float_or_int_values(payload)


def test_primary_source_availability_scores_pass_watch_and_block_dimensions() -> None:
    report = build_report(
        signal(
            "official-resolution",
            primary_source_available=True,
            observed_seconds_ago=900,
            primary_evidence_count=d("2.000000"),
            authority_score=d("0.950000"),
            corroborating_source_count=d("3.000000"),
            access_success_ratio=d("0.900000"),
        ),
        signal(
            "agency-confirmation",
            primary_source_available=True,
            observed_seconds_ago=5400,
            primary_evidence_count=d("1.000000"),
            authority_score=d("0.650000"),
            corroborating_source_count=d("1.000000"),
            access_success_ratio=d("0.750000"),
        ),
        signal(
            "manual-review-gap",
            primary_source_available=False,
            observed_seconds_ago=None,
            primary_evidence_count=d("0.000000"),
            authority_score=d("0.300000"),
            corroborating_source_count=d("0.000000"),
            access_success_ratio=d("0.400000"),
        ),
    )

    assert report.status == "block"
    assert report.review_scope_count == d("3.000000")
    assert report.available_primary_source_count == d("2.000000")
    assert report.fresh_primary_source_count == d("1.000000")
    assert report.authoritative_primary_source_count == d("1.000000")
    assert report.corroborated_primary_source_count == d("1.000000")
    assert report.accessible_primary_source_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.lowest_strategy_review_readiness_score == d("0.140000")
    assert report.highest_primary_evidence_age_seconds == d("5400.000000")
    assert report.reason_codes == (
        "accessibility_block",
        "accessibility_watch",
        "authority_score_block",
        "authority_score_watch",
        "corroboration_gap_block",
        "corroboration_gap_watch",
        "missing_primary_source",
        "stale_primary_source_watch",
    )

    blocked, watched, passed = report.rows
    assert (blocked.review_scope, blocked.status) == ("manual-review-gap", "block")
    assert blocked.primary_evidence_age_seconds is None
    assert blocked.freshness_score == d("0.000000")
    assert blocked.strategy_review_readiness_score == d("0.140000")
    assert blocked.reason_codes == (
        "primary_source_availability_block",
        "accessibility_block",
        "authority_score_block",
        "corroboration_gap_block",
        "missing_primary_source",
    )

    assert (watched.review_scope, watched.status) == ("agency-confirmation", "watch")
    assert watched.primary_evidence_age_seconds == d("5400.000000")
    assert watched.freshness_score == d("0.500000")
    assert watched.corroboration_score == d("0.500000")
    assert watched.strategy_review_readiness_score == d("0.680000")
    assert watched.reason_codes == (
        "primary_source_availability_watch",
        "accessibility_watch",
        "authority_score_watch",
        "corroboration_gap_watch",
        "stale_primary_source_watch",
    )

    assert (passed.review_scope, passed.status) == ("official-resolution", "pass")
    assert passed.primary_evidence_age_seconds == d("900.000000")
    assert passed.freshness_score == d("1.000000")
    assert passed.corroboration_score == d("1.000000")
    assert passed.strategy_review_readiness_score == d("0.970000")
    assert passed.reason_codes == ("primary_source_availability_pass",)


def test_payload_is_deterministic_immutable_json_ready_and_digest_validated() -> None:
    module = api()
    report_a = build_report(
        signal("official-resolution"),
        signal(
            "agency-confirmation",
            observed_seconds_ago=5400,
            authority_score=d("0.650000"),
            corroborating_source_count=d("1.000000"),
            access_success_ratio=d("0.750000"),
        ),
    )
    report_b = build_report(
        signal(
            "agency-confirmation",
            observed_seconds_ago=5400,
            authority_score=d("0.650000"),
            corroborating_source_count=d("1.000000"),
            access_success_ratio=d("0.750000"),
        ),
        signal("official-resolution"),
    )

    payload_a = module.research_source_primary_source_availability_report_payload(report_a)
    payload_b = module.research_source_primary_source_availability_report_payload(report_b)
    digest_a = module.research_source_primary_source_availability_report_digest(report_a)

    assert payload_a == payload_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["review_scope_count"] == "2.000000"
    assert payload_a["rows"][0]["review_scope"] == "agency-confirmation"
    assert payload_a["rows"][0]["strategy_review_readiness_score"] == "0.680000"
    json.dumps(payload_a, sort_keys=True)
    assert_no_unsafe_public_payload(payload_a)
    assert_no_float_or_int_values(payload_a)

    with pytest.raises(TypeError, match="immutable"):
        payload_a["status"] = "pass"
    with pytest.raises(TypeError, match="immutable"):
        payload_a["rows"].append({})
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_validation_rejects_bad_numeric_types_flags_timestamps_and_public_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="config_version must be supported"):
        config(config_version="research-source-primary-source-availability-report-v999")
    with pytest.raises(ValueError, match="max_fresh_age_seconds"):
        config(max_fresh_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_watch_threshold"):
        config(authority_watch_threshold=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="block_stale_age_seconds"):
        config(block_stale_age_seconds=d("3600.000000"))
    with pytest.raises(ValueError, match="minimum_corroborating_source_count"):
        config(minimum_corroborating_source_count=d("2.0000004"))
    with pytest.raises(ValueError, match="review_scope"):
        signal("market_slug_yes_2026")
    with pytest.raises(ValueError, match="review_scope"):
        signal("https://example.test/source")
    with pytest.raises(ValueError, match="review_scope"):
        signal("candidate_id_123")
    with pytest.raises(ValueError, match="primary_evidence_count"):
        signal("official-resolution", primary_evidence_count=d("-1.000000"))
    with pytest.raises(ValueError, match="primary_evidence_count"):
        signal("official-resolution", primary_evidence_count=d("-0.0000004"))
    with pytest.raises(ValueError, match="primary_evidence_count must be quantizable"):
        signal("official-resolution", primary_evidence_count=d("1e1000"))
    with pytest.raises(ValueError, match="authority_score"):
        signal("official-resolution", authority_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_score"):
        signal("official-resolution", authority_score=d("1.0000004"))
    with pytest.raises(ValueError, match="corroborating_source_count"):
        signal("official-resolution", corroborating_source_count=d("1.500000"))
    with pytest.raises(ValueError, match="corroborating_source_count"):
        signal("official-resolution", corroborating_source_count=d("1.0000004"))
    with pytest.raises(ValueError, match="access_success_ratio"):
        signal("official-resolution", access_success_ratio=d("1.500000"))
    with pytest.raises(ValueError, match="access_success_ratio"):
        signal("official-resolution", access_success_ratio=d("-0.0000004"))
    with pytest.raises(ValueError, match="latest_primary_evidence_at"):
        build_report(signal("official-resolution", observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="paper_only"):
        signal("official-resolution", paper_only=False)

    report = build_report(signal("official-resolution"))
    bad_age_row = replace(
        report.rows[0],
        primary_evidence_age_seconds=d("901.000000"),
        derived_validation_digest="",
    )
    with pytest.raises(ValueError, match="primary_evidence_age_seconds"):
        replace(report, rows=(bad_age_row,))

    with pytest.raises(ValueError, match="config_version must be supported"):
        replace(
            report,
            config_version="research-source-primary-source-availability-report-v999",
        )
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError):
        class _BadRow(module.ResearchSourcePrimarySourceAvailabilityRow):  # type: ignore[misc, valid-type]
            pass


@pytest.mark.parametrize(
    "unsafe_scope",
    (
        "auth",
        "auth-reference",
        "authentication-reference",
        "credential-reference",
        "password-reference",
        "api_key-reference",
        "database-reference",
        "network-reference",
        "file_path-reference",
        "position_sizing-review",
        "strategy-recommendation",
        "execution-instruction",
    ),
)
def test_signal_rejects_prohibited_report_only_public_surfaces(
    unsafe_scope: str,
) -> None:
    with pytest.raises(ValueError, match="review_scope"):
        signal(unsafe_scope)


def test_module_imports_no_network_database_or_live_execution_surfaces() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_primary_source_availability_report.py"
    )
    tree = ast.parse(source_path.read_text())
    forbidden_roots = {
        "asyncpg",
        "boto3",
        "httpx",
        "psycopg",
        "psycopg2",
        "requests",
        "socket",
        "sqlalchemy",
        "subprocess",
        "urllib",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(forbidden_roots)


def assert_no_float_or_int_values(payload: object) -> None:
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))


def assert_no_unsafe_public_payload(payload: object) -> None:
    unsafe_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "raw_url",
        "url",
        "source_text",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "http://",
        "https://",
        "www.",
    )
    for key, value in _walk_payload_items(payload):
        lowered_key = key.lower()
        assert not any(fragment in lowered_key for fragment in unsafe_fragments)
        if type(value) is str:
            lowered_value = value.lower()
            assert not any(fragment in lowered_value for fragment in unsafe_fragments)


def _walk_payload_items(value: object) -> tuple[tuple[str, object], ...]:
    items: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            items.append((key, item))
            items.extend(_walk_payload_items(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            items.extend(_walk_payload_items(item))
    return tuple(items)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(_walk_payload_values(item))
    return tuple(values)
