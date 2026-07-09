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


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "research_source_primary_evidence_crosscheck_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "authority_watch_floor": d("0.700000"),
        "authority_block_floor": d("0.500000"),
        "stale_watch_age_seconds": d("1800.000000"),
        "stale_block_age_seconds": d("3600.000000"),
        "crosscheck_watch_count": d("2.000000"),
        "crosscheck_block_count": d("0.000000"),
        "independent_evidence_watch_count": d("2.000000"),
        "independent_evidence_block_count": d("0.000000"),
        "contradiction_watch_pressure": d("0.300000"),
        "contradiction_block_pressure": d("0.600000"),
        "retrieval_gap_watch_score": d("0.300000"),
        "retrieval_gap_block_score": d("0.600000"),
        "extraction_confidence_watch_floor": d("0.800000"),
        "extraction_confidence_block_floor": d("0.600000"),
        "resolution_watch_seconds_remaining": d("1800.000000"),
        "resolution_block_seconds_remaining": d("600.000000"),
    }
    values.update(overrides)
    return module.ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig(**values)


def evidence_item(
    evidence_key: str,
    *,
    primary_authority_score: Decimal = d("0.900000"),
    latest_primary_age_seconds: Decimal = d("600.000000"),
    crosscheck_count: Decimal = d("3.000000"),
    independent_evidence_count: Decimal = d("3.000000"),
    contradiction_pressure: Decimal = d("0.100000"),
    retrieval_gap_score: Decimal = d("0.050000"),
    extraction_confidence: Decimal = d("0.950000"),
    resolution_window_seconds_remaining: Decimal = d("3600.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourcePrimaryEvidenceCrosscheckPriorityInput(
        evidence_key=evidence_key,
        primary_authority_score=primary_authority_score,
        latest_primary_age_seconds=latest_primary_age_seconds,
        crosscheck_count=crosscheck_count,
        independent_evidence_count=independent_evidence_count,
        contradiction_pressure=contradiction_pressure,
        retrieval_gap_score=retrieval_gap_score,
        extraction_confidence=extraction_confidence,
        resolution_window_seconds_remaining=resolution_window_seconds_remaining,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def public_item(key: str, value: str) -> Any:
    module = api()
    return module.ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem(
        key,
        value,
    )


def build_report(*rows: Any, cfg: Any | None = None, public_payload: tuple[Any, ...] = ()) -> Any:
    module = api()
    return module.build_research_source_primary_evidence_crosscheck_priority_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
        public_payload=public_payload,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_empty_report_is_pass_readonly_and_digest_validated() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourcePrimaryEvidenceCrosscheckPriorityReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.item_count == d("0.000000")
    assert report.pass_item_count == d("0.000000")
    assert report.watch_item_count == d("0.000000")
    assert report.block_item_count == d("0.000000")
    assert report.low_authority_count == d("0.000000")
    assert report.stale_primary_evidence_count == d("0.000000")
    assert report.thin_crosscheck_count == d("0.000000")
    assert report.insufficient_independent_evidence_count == d("0.000000")
    assert report.contradiction_pressure_count == d("0.000000")
    assert report.retrieval_gap_count == d("0.000000")
    assert report.low_extraction_confidence_count == d("0.000000")
    assert report.resolution_window_count == d("0.000000")
    assert report.highest_priority_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("research_source_primary_evidence_crosscheck_priority_empty",)
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert (
        report.derived_validation_digest
        == module.research_source_primary_evidence_crosscheck_priority_report_digest(report)
    )
    module.validate_research_source_primary_evidence_crosscheck_priority_report_digest(report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_priority_report_scores_and_sorts_crosscheck_pressure() -> None:
    report = build_report(
        evidence_item("wire_confirmed"),
        evidence_item(
            "community_fast",
            primary_authority_score=d("0.650000"),
            latest_primary_age_seconds=d("2400.000000"),
            crosscheck_count=d("1.000000"),
            independent_evidence_count=d("1.000000"),
            contradiction_pressure=d("0.400000"),
            retrieval_gap_score=d("0.350000"),
            extraction_confidence=d("0.750000"),
            resolution_window_seconds_remaining=d("1200.000000"),
        ),
        evidence_item(
            "agency_conflict",
            primary_authority_score=d("0.400000"),
            latest_primary_age_seconds=d("4200.000000"),
            crosscheck_count=d("0.000000"),
            independent_evidence_count=d("0.000000"),
            contradiction_pressure=d("0.700000"),
            retrieval_gap_score=d("0.750000"),
            extraction_confidence=d("0.500000"),
            resolution_window_seconds_remaining=d("300.000000"),
        ),
    )

    assert report.status == "block"
    assert report.item_count == d("3.000000")
    assert report.pass_item_count == d("1.000000")
    assert report.watch_item_count == d("1.000000")
    assert report.block_item_count == d("1.000000")
    assert report.low_authority_count == d("2.000000")
    assert report.stale_primary_evidence_count == d("2.000000")
    assert report.thin_crosscheck_count == d("2.000000")
    assert report.insufficient_independent_evidence_count == d("2.000000")
    assert report.contradiction_pressure_count == d("2.000000")
    assert report.retrieval_gap_count == d("2.000000")
    assert report.low_extraction_confidence_count == d("2.000000")
    assert report.resolution_window_count == d("2.000000")
    assert report.highest_priority_score == d("0.812500")
    assert report.oldest_latest_primary_age_seconds == d("4200.000000")
    assert report.lowest_primary_authority_score == d("0.400000")
    assert report.lowest_extraction_confidence == d("0.500000")
    assert report.highest_contradiction_pressure == d("0.700000")
    assert report.highest_retrieval_gap_score == d("0.750000")
    assert report.nearest_resolution_window_seconds_remaining == d("300.000000")
    assert tuple(row.evidence_key for row in report.rows) == (
        "agency_conflict",
        "community_fast",
        "wire_confirmed",
    )
    assert report.reason_codes == (
        "research_source_primary_evidence_crosscheck_priority_low_authority_block",
        "research_source_primary_evidence_crosscheck_priority_stale_primary_block",
        "research_source_primary_evidence_crosscheck_priority_thin_crosscheck_block",
        "research_source_primary_evidence_crosscheck_priority_independence_block",
        "research_source_primary_evidence_crosscheck_priority_contradiction_block",
        "research_source_primary_evidence_crosscheck_priority_retrieval_gap_block",
        "research_source_primary_evidence_crosscheck_priority_low_extraction_block",
        "research_source_primary_evidence_crosscheck_priority_resolution_window_block",
        "research_source_primary_evidence_crosscheck_priority_low_authority_watch",
        "research_source_primary_evidence_crosscheck_priority_stale_primary_watch",
        "research_source_primary_evidence_crosscheck_priority_thin_crosscheck_watch",
        "research_source_primary_evidence_crosscheck_priority_independence_watch",
        "research_source_primary_evidence_crosscheck_priority_contradiction_watch",
        "research_source_primary_evidence_crosscheck_priority_retrieval_gap_watch",
        "research_source_primary_evidence_crosscheck_priority_low_extraction_watch",
        "research_source_primary_evidence_crosscheck_priority_resolution_window_watch",
    )

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.authority_band == "low"
    assert blocked.freshness_band == "stale"
    assert blocked.crosscheck_depth_score == d("0.000000")
    assert blocked.independent_evidence_score == d("0.000000")
    assert blocked.resolution_window_pressure_score == d("0.833333")
    assert blocked.priority_score == d("0.812500")

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.authority_band == "medium"
    assert watched.freshness_band == "aging"
    assert watched.crosscheck_depth_score == d("0.500000")
    assert watched.independent_evidence_score == d("0.500000")
    assert watched.resolution_window_pressure_score == d("0.333333")
    assert watched.priority_score == d("0.438750")

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.authority_band == "high"
    assert passed.freshness_band == "fresh"
    assert passed.priority_score == d("0.066250")
    assert passed.reason_codes == (
        "research_source_primary_evidence_crosscheck_priority_clear",
    )


def test_status_vocabulary_is_only_pass_watch_block() -> None:
    module = api()
    pass_report = build_report(evidence_item("wire_confirmed"))
    watch_report = build_report(
        evidence_item("community_fast", primary_authority_score=d("0.650000")),
    )
    block_report = build_report(
        evidence_item("agency_conflict", contradiction_pressure=d("0.700000")),
    )

    assert module.RESEARCH_SOURCE_PRIMARY_EVIDENCE_CROSSCHECK_PRIORITY_STATUSES == (
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


def test_payload_digest_json_ready_deterministic_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        evidence_item("wire_confirmed"),
        evidence_item(
            "agency_conflict",
            primary_authority_score=d("0.400000"),
            latest_primary_age_seconds=d("4200.000000"),
            crosscheck_count=d("0.000000"),
            independent_evidence_count=d("0.000000"),
            contradiction_pressure=d("0.700000"),
            retrieval_gap_score=d("0.750000"),
            extraction_confidence=d("0.500000"),
            resolution_window_seconds_remaining=d("300.000000"),
        ),
        public_payload=(public_item("basis", "sanitized crosscheck priority metrics"),),
    )
    report_b = build_report(
        evidence_item(
            "agency_conflict",
            primary_authority_score=d("0.400000"),
            latest_primary_age_seconds=d("4200.000000"),
            crosscheck_count=d("0.000000"),
            independent_evidence_count=d("0.000000"),
            contradiction_pressure=d("0.700000"),
            retrieval_gap_score=d("0.750000"),
            extraction_confidence=d("0.500000"),
            resolution_window_seconds_remaining=d("300.000000"),
        ),
        evidence_item("wire_confirmed"),
        public_payload=(public_item("basis", "sanitized crosscheck priority metrics"),),
    )

    payload_a = module.research_source_primary_evidence_crosscheck_priority_report_payload(
        report_a,
    )
    payload_b = module.research_source_primary_evidence_crosscheck_priority_report_payload(
        report_b,
    )
    digest_a = module.research_source_primary_evidence_crosscheck_priority_report_digest(
        report_a,
    )
    digest_b = module.research_source_primary_evidence_crosscheck_priority_report_digest(
        report_b,
    )

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["item_count"] == "2.000000"
    assert payload_a["rows"][0]["priority_score"] >= payload_a["rows"][1]["priority_score"]
    json.dumps(payload_a, sort_keys=True)
    assert_no_public_numeric_values(payload_a)
    assert_payload_has_no_leaked_values(payload_a)

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "slug",
        "question",
        "url",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
    }
    keys = {field.name for cls in (type(report_a), type(report_a.rows[0])) for field in fields(cls)}
    assert unsafe_keys.isdisjoint(keys)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, public_payload=(public_item("basis", "changed metrics"),))


def test_validation_rejects_non_decimal_inputs_unsafe_labels_flags_and_statuses() -> None:
    module = api()

    with pytest.raises(ValueError, match="authority_watch_floor must be a Decimal"):
        config(authority_watch_floor=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="primary_authority_score must be a Decimal"):
        evidence_item("wire_confirmed", primary_authority_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="crosscheck_count must be a Decimal"):
        evidence_item("wire_confirmed", crosscheck_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="crosscheck_count must be a whole Decimal"):
        evidence_item("wire_confirmed", crosscheck_count=d("1.500000"))
    with pytest.raises(ValueError, match="latest_primary_age_seconds must be nonnegative"):
        evidence_item("wire_confirmed", latest_primary_age_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_primary_evidence_crosscheck_priority_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_source_primary_evidence_crosscheck_priority_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="evidence_key contains unsafe text"):
        evidence_item("candidate-123")
    with pytest.raises(ValueError, match="evidence_key contains unsafe text"):
        evidence_item("market_slug")
    with pytest.raises(ValueError, match="evidence_key contains unsafe text"):
        evidence_item("https://example.invalid/path")
    with pytest.raises(ValueError, match="key contains unsafe text"):
        public_item("source_url", "sanitized metrics")
    with pytest.raises(ValueError, match="value contains unsafe text"):
        public_item("basis", "wallet credential")
    with pytest.raises(ValueError, match="paper_only"):
        evidence_item("wire_confirmed", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        evidence_item("wire_confirmed", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        evidence_item("wire_confirmed", readonly=False)

    report = build_report(evidence_item("wire_confirmed"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="clear")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")
    with pytest.raises(ValueError, match="item_count"):
        replace(report, item_count=d("2.000000"))


def test_exports_frozen_dataclasses_and_public_api() -> None:
    module = api()
    report = build_report(evidence_item("wire_confirmed"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_PRIMARY_EVIDENCE_CROSSCHECK_PRIORITY_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_PRIMARY_EVIDENCE_CROSSCHECK_PRIORITY_STATUSES",
        "ResearchSourcePrimaryEvidenceCrosscheckPriorityConfig",
        "ResearchSourcePrimaryEvidenceCrosscheckPriorityInput",
        "ResearchSourcePrimaryEvidenceCrosscheckPriorityPublicPayloadItem",
        "ResearchSourcePrimaryEvidenceCrosscheckPriorityReport",
        "ResearchSourcePrimaryEvidenceCrosscheckPriorityRow",
        "build_research_source_primary_evidence_crosscheck_priority_report",
        "research_source_primary_evidence_crosscheck_priority_report_digest",
        "research_source_primary_evidence_crosscheck_priority_report_payload",
        "validate_research_source_primary_evidence_crosscheck_priority_report_digest",
    )
    assert is_dataclass(config())
    assert is_dataclass(evidence_item("wire_confirmed"))
    assert is_dataclass(public_item("basis", "sanitized metrics"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().authority_watch_floor = d("0.800000")

    with pytest.raises(TypeError):

        class BadReport(module.ResearchSourcePrimaryEvidenceCrosscheckPriorityReport):
            pass


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
        "auth",
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "wallet",
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
        "slug",
        "question",
        "source_text",
        "source url",
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
