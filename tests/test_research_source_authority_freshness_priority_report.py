from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_authority_freshness_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "authority_watch_floor": d("0.700000"),
        "authority_block_floor": d("0.500000"),
        "freshness_watch_age_seconds": d("1800.000000"),
        "freshness_block_age_seconds": d("3600.000000"),
        "corroboration_watch_depth": d("2.000000"),
        "corroboration_block_depth": d("0.000000"),
        "contradiction_watch_pressure": d("0.300000"),
        "contradiction_block_pressure": d("0.600000"),
        "extraction_confidence_watch_floor": d("0.800000"),
        "extraction_confidence_block_floor": d("0.600000"),
        "missing_fields_watch_count": d("1.000000"),
        "missing_fields_block_count": d("2.000000"),
        "deadline_watch_seconds_remaining": d("1800.000000"),
        "deadline_block_seconds_remaining": d("600.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityFreshnessPriorityConfig(**values)


def review_item(
    review_bucket: str,
    *,
    source_authority_score: Decimal = d("0.900000"),
    latest_verification_age_seconds: Decimal = d("600.000000"),
    corroboration_depth_count: Decimal = d("3.000000"),
    contradiction_pressure_score: Decimal = d("0.100000"),
    extraction_confidence_score: Decimal = d("0.950000"),
    missing_required_field_count: Decimal = d("0.000000"),
    required_field_count: Decimal = d("4.000000"),
    deadline_seconds_remaining: Decimal = d("3600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceAuthorityFreshnessPriorityInput(
        review_bucket=review_bucket,
        source_authority_score=source_authority_score,
        latest_verification_age_seconds=latest_verification_age_seconds,
        corroboration_depth_count=corroboration_depth_count,
        contradiction_pressure_score=contradiction_pressure_score,
        extraction_confidence_score=extraction_confidence_score,
        missing_required_field_count=missing_required_field_count,
        required_field_count=required_field_count,
        deadline_seconds_remaining=deadline_seconds_remaining,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_authority_freshness_priority_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_empty_report_is_pass_readonly_digest_validated_and_decimal_only() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceAuthorityFreshnessPriorityReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.review_item_count == d("0.000000")
    assert report.pass_review_item_count == d("0.000000")
    assert report.watch_review_item_count == d("0.000000")
    assert report.block_review_item_count == d("0.000000")
    assert report.low_authority_count == d("0.000000")
    assert report.stale_verification_count == d("0.000000")
    assert report.thin_corroboration_count == d("0.000000")
    assert report.contradiction_pressure_count == d("0.000000")
    assert report.low_extraction_confidence_count == d("0.000000")
    assert report.missing_field_count == d("0.000000")
    assert report.deadline_proximity_count == d("0.000000")
    assert report.highest_priority_score == d("0.000000")
    assert report.oldest_latest_verification_age_seconds == d("0.000000")
    assert report.lowest_source_authority_score == d("0.000000")
    assert report.lowest_extraction_confidence_score == d("0.000000")
    assert report.highest_contradiction_pressure_score == d("0.000000")
    assert report.nearest_deadline_seconds_remaining == d("0.000000")
    assert report.reason_codes == ("research_source_authority_freshness_priority_empty",)
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert (
        report.derived_validation_digest
        == module.research_source_authority_freshness_priority_report_digest(report)
    )
    module.validate_research_source_authority_freshness_priority_report_digest(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_priority_report_scores_authority_freshness_and_review_pressure() -> None:
    report = build_report(
        review_item("wire_confirmed"),
        review_item(
            "community_fast",
            source_authority_score=d("0.650000"),
            latest_verification_age_seconds=d("2400.000000"),
            corroboration_depth_count=d("1.000000"),
            contradiction_pressure_score=d("0.400000"),
            extraction_confidence_score=d("0.750000"),
            missing_required_field_count=d("1.000000"),
            required_field_count=d("2.000000"),
            deadline_seconds_remaining=d("1200.000000"),
        ),
        review_item(
            "official_filing",
            source_authority_score=d("0.400000"),
            latest_verification_age_seconds=d("4200.000000"),
            corroboration_depth_count=d("0.000000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_confidence_score=d("0.500000"),
            missing_required_field_count=d("2.000000"),
            required_field_count=d("2.000000"),
            deadline_seconds_remaining=d("300.000000"),
        ),
    )

    assert report.status == "block"
    assert report.review_item_count == d("3.000000")
    assert report.pass_review_item_count == d("1.000000")
    assert report.watch_review_item_count == d("1.000000")
    assert report.block_review_item_count == d("1.000000")
    assert report.low_authority_count == d("2.000000")
    assert report.stale_verification_count == d("2.000000")
    assert report.thin_corroboration_count == d("2.000000")
    assert report.contradiction_pressure_count == d("2.000000")
    assert report.low_extraction_confidence_count == d("2.000000")
    assert report.missing_field_count == d("2.000000")
    assert report.deadline_proximity_count == d("2.000000")
    assert report.highest_priority_score == d("0.792500")
    assert report.oldest_latest_verification_age_seconds == d("4200.000000")
    assert report.lowest_source_authority_score == d("0.400000")
    assert report.lowest_extraction_confidence_score == d("0.500000")
    assert report.highest_contradiction_pressure_score == d("0.700000")
    assert report.nearest_deadline_seconds_remaining == d("300.000000")
    assert tuple(row.review_bucket for row in report.rows) == (
        "official_filing",
        "community_fast",
        "wire_confirmed",
    )
    assert report.reason_codes == (
        "research_source_authority_freshness_priority_low_authority_block",
        "research_source_authority_freshness_priority_stale_verification_block",
        "research_source_authority_freshness_priority_thin_corroboration_block",
        "research_source_authority_freshness_priority_contradiction_pressure_block",
        "research_source_authority_freshness_priority_low_extraction_confidence_block",
        "research_source_authority_freshness_priority_missing_fields_block",
        "research_source_authority_freshness_priority_deadline_proximity_block",
        "research_source_authority_freshness_priority_low_authority_watch",
        "research_source_authority_freshness_priority_stale_verification_watch",
        "research_source_authority_freshness_priority_thin_corroboration_watch",
        "research_source_authority_freshness_priority_contradiction_pressure_watch",
        "research_source_authority_freshness_priority_low_extraction_confidence_watch",
        "research_source_authority_freshness_priority_missing_fields_watch",
        "research_source_authority_freshness_priority_deadline_proximity_watch",
    )

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.authority_band == "low"
    assert blocked.freshness_band == "stale"
    assert blocked.corroboration_depth_score == d("0.000000")
    assert blocked.field_completeness_score == d("0.000000")
    assert blocked.deadline_pressure_score == d("0.833333")
    assert blocked.priority_score == d("0.792500")

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.authority_band == "medium"
    assert watched.freshness_band == "aging"
    assert watched.corroboration_depth_score == d("0.500000")
    assert watched.field_completeness_score == d("0.500000")
    assert watched.deadline_pressure_score == d("0.333333")
    assert watched.priority_score == d("0.437917")

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.authority_band == "high"
    assert passed.freshness_band == "fresh"
    assert passed.priority_score == d("0.072917")
    assert passed.reason_codes == ("research_source_authority_freshness_priority_clear",)


def test_status_vocabulary_is_only_pass_watch_block() -> None:
    module = api()
    pass_report = build_report(review_item("wire_confirmed"))
    watch_report = build_report(
        review_item(
            "community_fast",
            source_authority_score=d("0.650000"),
        ),
    )
    block_report = build_report(
        review_item(
            "official_filing",
            contradiction_pressure_score=d("0.700000"),
        ),
    )

    assert module.RESEARCH_SOURCE_AUTHORITY_FRESHNESS_PRIORITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert pass_report.status == "pass"
    assert pass_report.rows[0].status == "pass"
    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"


def test_payload_and_digest_are_deterministic_json_ready_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        review_item("wire_confirmed"),
        review_item(
            "official_filing",
            source_authority_score=d("0.400000"),
            latest_verification_age_seconds=d("4200.000000"),
            corroboration_depth_count=d("0.000000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_confidence_score=d("0.500000"),
            missing_required_field_count=d("2.000000"),
            required_field_count=d("2.000000"),
            deadline_seconds_remaining=d("300.000000"),
        ),
    )
    report_b = build_report(
        review_item(
            "official_filing",
            source_authority_score=d("0.400000"),
            latest_verification_age_seconds=d("4200.000000"),
            corroboration_depth_count=d("0.000000"),
            contradiction_pressure_score=d("0.700000"),
            extraction_confidence_score=d("0.500000"),
            missing_required_field_count=d("2.000000"),
            required_field_count=d("2.000000"),
            deadline_seconds_remaining=d("300.000000"),
        ),
        review_item("wire_confirmed"),
    )

    payload_a = module.research_source_authority_freshness_priority_report_payload(report_a)
    payload_b = module.research_source_authority_freshness_priority_report_payload(report_b)
    digest_a = module.research_source_authority_freshness_priority_report_digest(report_a)
    digest_b = module.research_source_authority_freshness_priority_report_digest(report_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["review_item_count"] == "2.000000"
    assert payload_a["rows"][0]["priority_score"] >= payload_a["rows"][1]["priority_score"]
    json.dumps(payload_a, sort_keys=True)
    assert_no_public_numeric_values(payload_a)

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
    }
    keys = {field.name for cls in (type(report_a), type(report_a.rows[0])) for field in fields(cls)}
    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload_a)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_validation_rejects_non_decimal_inputs_unsafe_labels_flags_and_statuses() -> None:
    module = api()

    with pytest.raises(ValueError, match="authority_watch_floor must be a Decimal"):
        config(authority_watch_floor=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="source_authority_score must be a Decimal"):
        review_item("wire_confirmed", source_authority_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="corroboration_depth_count must be a Decimal"):
        review_item("wire_confirmed", corroboration_depth_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="corroboration_depth_count must be a whole Decimal"):
        review_item("wire_confirmed", corroboration_depth_count=d("1.500000"))
    with pytest.raises(ValueError, match="latest_verification_age_seconds must be nonnegative"):
        review_item("wire_confirmed", latest_verification_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="missing_required_field_count must not exceed"):
        review_item(
            "wire_confirmed",
            missing_required_field_count=d("5.000000"),
            required_field_count=d("4.000000"),
        )
    with pytest.raises(ValueError, match="review_bucket contains unsafe text"):
        review_item("candidate-123")
    with pytest.raises(ValueError, match="review_bucket contains unsafe text"):
        review_item("market_review")
    with pytest.raises(ValueError, match="review_bucket contains unsafe text"):
        review_item("event_slug")
    with pytest.raises(ValueError, match="review_bucket contains unsafe text"):
        review_item("source_url")
    with pytest.raises(ValueError, match="review_bucket contains unsafe text"):
        review_item("table_name")
    with pytest.raises(ValueError, match="review_bucket contains unsafe text"):
        review_item("live_feed")
    with pytest.raises(ValueError, match="review_bucket contains unsafe text"):
        review_item("market_slug")
    with pytest.raises(ValueError, match="review_bucket contains unsafe text"):
        review_item("https://example.invalid/path")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_authority_freshness_priority_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="paper_only"):
        review_item("wire_confirmed", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        review_item("wire_confirmed", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        review_item("wire_confirmed", readonly=False)

    report = build_report(review_item("wire_confirmed"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="clear")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")


def test_exports_frozen_dataclasses_and_public_api() -> None:
    module = api()
    report = build_report(review_item("wire_confirmed"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_AUTHORITY_FRESHNESS_PRIORITY_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_AUTHORITY_FRESHNESS_PRIORITY_STATUSES",
        "ResearchSourceAuthorityFreshnessPriorityConfig",
        "ResearchSourceAuthorityFreshnessPriorityInput",
        "ResearchSourceAuthorityFreshnessPriorityReport",
        "ResearchSourceAuthorityFreshnessPriorityRow",
        "build_research_source_authority_freshness_priority_report",
        "research_source_authority_freshness_priority_report_digest",
        "research_source_authority_freshness_priority_report_payload",
        "validate_research_source_authority_freshness_priority_report_digest",
    )
    assert is_dataclass(config())
    assert is_dataclass(review_item("wire_confirmed"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().authority_watch_floor = d("0.800000")


def test_module_scope_is_pure_public_safe_report_only() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)
    else:
        assert type(value) is not float
        assert type(value) is not int


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "question",
        "source_text",
        " table",
        "dsn",
        "token",
        "wallet",
        "order",
        "trade",
        "live_surface",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
