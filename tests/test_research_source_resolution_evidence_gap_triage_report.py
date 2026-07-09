from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
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
        "polymarket_alpha_lab.research_source_resolution_evidence_gap_triage_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_source_authority_score": d("0.800000"),
        "block_source_authority_score": d("0.500000"),
        "freshness_watch_age_seconds": d("3600.000000"),
        "freshness_block_age_seconds": d("7200.000000"),
        "contradiction_watch_pressure": d("0.300000"),
        "contradiction_block_pressure": d("0.600000"),
        "min_corroboration_depth": d("2.000000"),
        "block_corroboration_depth": d("1.000000"),
        "min_extraction_confidence": d("0.800000"),
        "block_extraction_confidence": d("0.500000"),
        "critical_field_watch_missing_count": d("1.000000"),
        "critical_field_block_missing_count": d("2.000000"),
        "deadline_watch_proximity_seconds": d("43200.000000"),
        "deadline_block_proximity_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceResolutionEvidenceGapTriageConfig(**values)


def evidence(
    resolution_bucket: str,
    evidence_family: str,
    *,
    observed_seconds_ago: int = 1200,
    deadline_seconds_from_now: int = 172800,
    source_authority_score: Decimal = d("0.900000"),
    contradiction_pressure: Decimal = d("0.100000"),
    corroboration_depth: Decimal = d("3.000000"),
    extraction_confidence: Decimal = d("0.900000"),
    missing_critical_field_count: Decimal = d("0.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceResolutionEvidenceGapTriageInput(
        resolution_bucket=resolution_bucket,
        evidence_family=evidence_family,
        evidence_observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        resolution_deadline_at=GENERATED_AT + timedelta(seconds=deadline_seconds_from_now),
        source_authority_score=source_authority_score,
        contradiction_pressure=contradiction_pressure,
        corroboration_depth=corroboration_depth,
        extraction_confidence=extraction_confidence,
        missing_critical_field_count=missing_critical_field_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_resolution_evidence_gap_triage_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_triage_report_blocks_material_resolution_evidence_gaps() -> None:
    report = build_report(
        evidence(
            "settlement.criteria",
            "official.feed",
            observed_seconds_ago=10800,
            deadline_seconds_from_now=3600,
            source_authority_score=d("0.400000"),
            contradiction_pressure=d("0.800000"),
            corroboration_depth=d("1.000000"),
            extraction_confidence=d("0.300000"),
            missing_critical_field_count=d("2.000000"),
        ),
        evidence(
            "settlement.criteria",
            "archive.feed",
            observed_seconds_ago=9000,
            deadline_seconds_from_now=3600,
            source_authority_score=d("0.600000"),
            contradiction_pressure=d("0.500000"),
            corroboration_depth=d("1.000000"),
            extraction_confidence=d("0.600000"),
            missing_critical_field_count=d("1.000000"),
        ),
        evidence("verification.criteria", "official.feed"),
    )

    assert report.status == "block"
    assert report.resolution_bucket_count == d("2.000000")
    assert report.evidence_count == d("3.000000")
    assert report.pass_resolution_bucket_count == d("1.000000")
    assert report.watch_resolution_bucket_count == d("0.000000")
    assert report.block_resolution_bucket_count == d("1.000000")
    assert report.low_source_authority_count == d("1.000000")
    assert report.stale_evidence_count == d("1.000000")
    assert report.contradiction_pressure_count == d("1.000000")
    assert report.low_corroboration_count == d("1.000000")
    assert report.low_extraction_confidence_count == d("1.000000")
    assert report.missing_critical_fields_count == d("1.000000")
    assert report.deadline_pressure_count == d("1.000000")
    assert report.highest_evidence_gap_score == d("0.773810")
    assert report.nearest_deadline_seconds == d("3600.000000")
    assert report.reason_codes == (
        "low_source_authority_block",
        "stale_evidence_block",
        "contradiction_pressure_block",
        "low_corroboration_block",
        "low_extraction_confidence_block",
        "missing_critical_fields_block",
        "deadline_proximity_block",
    )

    assert tuple(row.resolution_bucket for row in report.rows) == (
        "settlement.criteria",
        "verification.criteria",
    )

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.evidence_family_count == d("2.000000")
    assert blocked.latest_evidence_age_seconds == d("9000.000000")
    assert blocked.average_source_authority_score == d("0.500000")
    assert blocked.contradiction_pressure == d("0.800000")
    assert blocked.corroboration_depth == d("1.000000")
    assert blocked.minimum_extraction_confidence == d("0.300000")
    assert blocked.missing_critical_field_count == d("2.000000")
    assert blocked.deadline_proximity_seconds == d("3600.000000")
    assert blocked.evidence_gap_score == d("0.773810")
    assert blocked.reason_codes == report.reason_codes

    passed = report.rows[1]
    assert passed.status == "pass"
    assert passed.reason_codes == ("resolution_evidence_gap_clear",)
    assert passed.evidence_gap_score == d("0.066667")
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True


def test_watch_thresholds_report_evidence_gap_pressure_without_blocking() -> None:
    report = build_report(
        evidence(
            "weather.criteria",
            "official.bulletin",
            observed_seconds_ago=5400,
            deadline_seconds_from_now=21600,
            source_authority_score=d("0.650000"),
            contradiction_pressure=d("0.350000"),
            corroboration_depth=d("1.500000"),
            extraction_confidence=d("0.700000"),
            missing_critical_field_count=d("1.000000"),
        ),
    )

    assert report.status == "watch"
    assert report.watch_resolution_bucket_count == d("1.000000")
    assert report.block_resolution_bucket_count == d("0.000000")
    assert report.reason_codes == (
        "low_source_authority_watch",
        "stale_evidence_watch",
        "contradiction_pressure_watch",
        "low_corroboration_watch",
        "low_extraction_confidence_watch",
        "missing_critical_fields_watch",
        "deadline_proximity_watch",
    )
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == report.reason_codes


def test_payload_digest_is_deterministic_decimal_string_only_and_public_safe() -> None:
    module = api()
    report_a = build_report(
        evidence("verification.criteria", "official.feed"),
        evidence(
            "settlement.criteria",
            "official.feed",
            observed_seconds_ago=10800,
            deadline_seconds_from_now=3600,
            source_authority_score=d("0.400000"),
            contradiction_pressure=d("0.800000"),
            corroboration_depth=d("1.000000"),
            extraction_confidence=d("0.300000"),
            missing_critical_field_count=d("2.000000"),
        ),
    )
    report_b = build_report(
        evidence(
            "settlement.criteria",
            "official.feed",
            observed_seconds_ago=10800,
            deadline_seconds_from_now=3600,
            source_authority_score=d("0.400000"),
            contradiction_pressure=d("0.800000"),
            corroboration_depth=d("1.000000"),
            extraction_confidence=d("0.300000"),
            missing_critical_field_count=d("2.000000"),
        ),
        evidence("verification.criteria", "official.feed"),
    )

    payload_a = module.research_source_resolution_evidence_gap_triage_report_payload(
        report_a,
    )
    payload_b = module.research_source_resolution_evidence_gap_triage_report_payload(
        report_b,
    )
    digest_a = module.research_source_resolution_evidence_gap_triage_report_digest(
        report_a,
    )
    digest_b = module.research_source_resolution_evidence_gap_triage_report_digest(
        report_b,
    )

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert payload_a["derived_validation_digest"] == digest_a
    assert payload_a["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload_a["resolution_bucket_count"] == "2.000000"
    assert payload_a["rows"][0]["evidence_gap_score"] >= payload_a["rows"][1][
        "evidence_gap_score"
    ]
    assert len(digest_a) == 64
    int(digest_a, 16)
    json.dumps(payload_a, sort_keys=True)
    assert_no_float_values(payload_a)

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_id",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_url",
    }
    keys = {field.name for cls in (type(report_a), type(report_a.rows[0])) for field in fields(cls)}
    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload_a)
    module.validate_research_source_resolution_evidence_gap_triage_report_digest(
        report_a,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report_a, derived_validation_digest="0" * 64)


def test_validation_flags_statuses_decimal_only_and_safe_scope() -> None:
    module = api()

    with pytest.raises(ValueError, match="min_source_authority_score must be a Decimal"):
        config(min_source_authority_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="source_authority_score must be a Decimal"):
        evidence("settlement.criteria", "official.feed", source_authority_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="missing_critical_field_count must be a Decimal"):
        evidence("settlement.criteria", "official.feed", missing_critical_field_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolution_bucket contains unsafe text"):
        evidence("market-question", "official.feed")
    with pytest.raises(ValueError, match="evidence_family contains unsafe text"):
        evidence("settlement.criteria", "https://example.test/source")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_resolution_evidence_gap_triage_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must not be in the future"):
        build_report(evidence("settlement.criteria", "official.feed", observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="paper_only"):
        evidence("settlement.criteria", "official.feed", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        evidence("settlement.criteria", "official.feed", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        evidence("settlement.criteria", "official.feed", readonly=False)

    report = build_report(evidence("settlement.criteria", "official.feed"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")


def test_exports_frozen_dataclasses_status_vocabulary_and_pure_report_scope() -> None:
    module = api()
    report = build_report(evidence("settlement.criteria", "official.feed"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_RESOLUTION_EVIDENCE_GAP_TRIAGE_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_RESOLUTION_EVIDENCE_GAP_TRIAGE_REPORT_STATUSES",
        "ResearchSourceResolutionEvidenceGapTriageConfig",
        "ResearchSourceResolutionEvidenceGapTriageInput",
        "ResearchSourceResolutionEvidenceGapTriageReport",
        "ResearchSourceResolutionEvidenceGapTriageRow",
        "build_research_source_resolution_evidence_gap_triage_report",
        "research_source_resolution_evidence_gap_triage_report_digest",
        "research_source_resolution_evidence_gap_triage_report_payload",
        "validate_research_source_resolution_evidence_gap_triage_report_digest",
    )
    assert module.RESEARCH_SOURCE_RESOLUTION_EVIDENCE_GAP_TRIAGE_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(config())
    assert is_dataclass(evidence("settlement.criteria", "official.feed"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().min_extraction_confidence = d("0.900000")

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    sources = (
        ("module", source),
        (
            "test",
            Path(__file__).read_text(),
        ),
    )
    imported_modules: set[str] = set()
    for source_label, source_text in sources:
        assert source_text is not None
        tree = ast.parse(source_text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.add(node.module)
            if isinstance(node, ast.Constant):
                assert type(node.value) is not float, source_label
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
        "scrap",
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


def assert_no_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)
    else:
        assert type(value) is not float


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "candidate-",
        "candidate_",
        "market-",
        "market_",
        "token",
        "wallet",
        "order",
        "trade",
        "question",
        "slug",
        "live",
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
