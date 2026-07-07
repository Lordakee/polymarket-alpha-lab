from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_source_audit_trail_score import (
    DEFAULT_RESEARCH_SOURCE_AUDIT_TRAIL_SCORE_CONFIG_VERSION,
    ResearchSourceAuditTrailRecord,
    ResearchSourceAuditTrailScoreConfig,
    ResearchSourceAuditTrailScoreReport,
    ResearchSourceAuditTrailScoreRow,
    build_research_source_audit_trail_score_report,
    research_source_audit_trail_score_payload,
    validate_research_source_audit_trail_score_public_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _unsafe(*parts: str) -> str:
    return "".join(parts)


def _record(
    public_record_id: str,
    **overrides: object,
) -> ResearchSourceAuditTrailRecord:
    values: dict[str, object] = {
        "public_record_id": public_record_id,
        "research_theme": "macro_policy",
        "refreshed_at": GENERATED_AT - timedelta(hours=1),
        "revision_count": d("2"),
        "cross_check_count": d("2"),
        "review_count": d("2"),
        "conclusion_count": d("2"),
    }
    values.update(overrides)
    return ResearchSourceAuditTrailRecord(**values)


def _report() -> ResearchSourceAuditTrailScoreReport:
    return build_research_source_audit_trail_score_report(
        (
            _record("pass_record"),
            _record(
                "watch_record",
                revision_count=d("1"),
                cross_check_count=d("2"),
                review_count=d("2"),
                conclusion_count=d("2"),
            ),
            _record(
                "block_record",
                refreshed_at=GENERATED_AT - timedelta(days=3),
                revision_count=d("0"),
                cross_check_count=d("0"),
                review_count=d("0"),
                conclusion_count=d("2"),
            ),
        ),
        config=ResearchSourceAuditTrailScoreConfig(),
        generated_at=GENERATED_AT,
    )


def _assert_no_raw_numerics(value: Any) -> None:
    if type(value) is dict:
        for item in value.values():
            _assert_no_raw_numerics(item)
        return
    if type(value) is list:
        for item in value:
            _assert_no_raw_numerics(item)
        return
    if isinstance(value, (Decimal, float, int)) and type(value) is not bool:
        pytest.fail("serialized payload must use Decimal strings, not raw numerics")


def test_audit_trail_score_reports_pass_watch_and_block_rows() -> None:
    report = _report()

    assert isinstance(report, ResearchSourceAuditTrailScoreReport)
    assert report.config_version == DEFAULT_RESEARCH_SOURCE_AUDIT_TRAIL_SCORE_CONFIG_VERSION
    assert report.audit_status == "block"
    assert report.record_count == d("3.000000")
    assert report.pass_record_count == d("1.000000")
    assert report.watch_record_count == d("1.000000")
    assert report.block_record_count == d("1.000000")
    assert report.attention_record_count == d("2.000000")
    assert report.attention_record_ratio == d("0.666667")
    assert report.stale_refresh_record_count == d("1.000000")
    assert report.missing_revision_record_count == d("2.000000")
    assert report.missing_cross_check_record_count == d("1.000000")
    assert report.missing_review_record_count == d("1.000000")
    assert report.low_score_record_count == d("1.000000")
    assert report.min_audit_trail_score == d("0.000000")
    assert report.mean_audit_trail_score == d("0.618055")
    assert report.max_refresh_age_seconds == d("259200.000000")
    assert tuple((row.public_record_id, row.audit_status) for row in report.rows) == (
        ("block_record", "block"),
        ("watch_record", "watch"),
        ("pass_record", "pass"),
    )
    assert report.rows[0] == ResearchSourceAuditTrailScoreRow(
        public_record_id="block_record",
        research_theme="macro_policy",
        refresh_age_seconds=d("259200.000000"),
        revision_coverage_ratio=d("0.000000"),
        cross_check_coverage_ratio=d("0.000000"),
        review_coverage_ratio=d("0.000000"),
        audit_trail_score=d("0.000000"),
        audit_status="block",
        reason_codes=(
            "research_source_audit_trail_score_stale_refresh",
            "research_source_audit_trail_score_missing_revision",
            "research_source_audit_trail_score_missing_cross_check",
            "research_source_audit_trail_score_missing_review",
            "research_source_audit_trail_score_low_score",
        ),
        derived_validation_digest=report.rows[0].derived_validation_digest,
    )
    assert report.rows[1].audit_trail_score == d("0.864583")
    assert report.rows[2].audit_trail_score == d("0.989583")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)


def test_payload_redacts_numeric_types_validates_digest_and_is_deterministic() -> None:
    records = (
        _record(
            "offset_record",
            refreshed_at=datetime(2026, 7, 7, 7, 0, tzinfo=timezone(timedelta(hours=-4))),
        ),
        _record(
            "watch_record",
            revision_count=d("1"),
            cross_check_count=d("2"),
            review_count=d("2"),
            conclusion_count=d("2"),
        ),
    )
    report_a = build_research_source_audit_trail_score_report(
        records,
        config=ResearchSourceAuditTrailScoreConfig(),
        generated_at=datetime(2026, 7, 7, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    report_b = build_research_source_audit_trail_score_report(
        tuple(reversed(records)),
        config=ResearchSourceAuditTrailScoreConfig(),
        generated_at=GENERATED_AT,
    )

    payload_a = research_source_audit_trail_score_payload(report_a)
    payload_b = research_source_audit_trail_score_payload(report_b)

    assert payload_a == payload_b
    assert payload_a["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload_a["record_count"] == "2.000000"
    assert payload_a["mean_audit_trail_score"] == "0.927083"
    assert payload_a["rows"][0]["refresh_age_seconds"] == "3600.000000"
    assert payload_a["rows"][0]["audit_trail_score"] == "0.864583"
    assert payload_a["rows"][0]["derived_validation_digest"] == (
        report_a.rows[0].derived_validation_digest
    )
    assert payload_a["derived_validation_digest"] == report_a.derived_validation_digest
    assert validate_research_source_audit_trail_score_public_payload(payload_a)
    _assert_no_raw_numerics(payload_a)

    tampered = dict(payload_a)
    tampered["record_count"] = "3.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_audit_trail_score_payload(tampered)

    missing_digest = dict(payload_a)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_source_audit_trail_score_public_payload(missing_digest)


@pytest.mark.parametrize(
    "unsafe_key",
    (
        _unsafe("raw_", "can", "did", "ate", "_id"),
        _unsafe("mar", "ket", "_id"),
        _unsafe("mar", "ket_", "sl", "ug"),
        _unsafe("event_", "ques", "tion"),
        _unsafe("sou", "rce", "_", "ref"),
        _unsafe("sou", "rce_", "ur", "l"),
        _unsafe("sou", "rce_", "tex", "t"),
        "dsn",
        _unsafe("tab", "le", "_name"),
        _unsafe("tok", "en"),
        _unsafe("wal", "let"),
        _unsafe("au", "th"),
        _unsafe("or", "der"),
        _unsafe("tra", "de"),
        _unsafe("posi", "tion"),
    ),
)
def test_payload_rejects_sensitive_public_keys(unsafe_key: str) -> None:
    payload = research_source_audit_trail_score_payload(_report())
    payload[unsafe_key] = "redacted"

    with pytest.raises(ValueError, match="public"):
        research_source_audit_trail_score_payload(payload)


@pytest.mark.parametrize(
    "unsafe_value",
    (
        _unsafe("needs_", "bu", "y"),
        _unsafe("needs_", "se", "ll"),
        _unsafe("make_", "recom", "mendation"),
        _unsafe("contains_", "sou", "rce", "ref"),
    ),
)
def test_payload_rejects_sensitive_public_values(unsafe_value: str) -> None:
    payload = research_source_audit_trail_score_payload(_report())
    payload["operator_note"] = unsafe_value

    with pytest.raises(ValueError, match="public"):
        research_source_audit_trail_score_payload(payload)


def test_decimal_only_frozen_dataclasses_and_hard_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        ResearchSourceAuditTrailScoreConfig(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_SOURCE_AUDIT_TRAIL_SCORE_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="max_refresh_age_seconds"):
        ResearchSourceAuditTrailScoreConfig(max_refresh_age_seconds=86400)
    with pytest.raises(ValueError, match="watch_score_threshold"):
        ResearchSourceAuditTrailScoreConfig(watch_score_threshold=_DecimalSubclass("0.7"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(ResearchSourceAuditTrailScoreConfig(), paper_only=False)
    with pytest.raises(ValueError, match="public_record_id"):
        _record(_unsafe("raw_", "can", "did", "ate"))
    with pytest.raises(ValueError, match="research_theme"):
        _record("safe_id", research_theme=_unsafe("mar", "ket"))
    with pytest.raises(ValueError, match="revision_count"):
        _record("numeric_count", revision_count=1)
    with pytest.raises(ValueError, match="cross_check_count"):
        _record("float_count", cross_check_count=1.0)
    with pytest.raises(ValueError, match="review_count"):
        _record("subclass_count", review_count=_DecimalSubclass("1"))
    with pytest.raises(ValueError, match="refreshed_at"):
        _record("naive_time", refreshed_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_audit_trail_score_report(
            (_record("ok"),),
            config=ResearchSourceAuditTrailScoreConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )

    report = _report()
    with pytest.raises(FrozenInstanceError):
        report.audit_status = "pass"
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in report.rows)


def test_empty_inputs_block_and_tamper_revalidation() -> None:
    empty = build_research_source_audit_trail_score_report(
        (),
        config=ResearchSourceAuditTrailScoreConfig(),
        generated_at=GENERATED_AT,
    )
    assert empty.audit_status == "block"
    assert empty.reason_codes == ("research_source_audit_trail_score_no_inputs",)
    assert empty.record_count == d("0.000000")
    assert empty.mean_audit_trail_score == d("0.000000")
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    report = _report()
    object.__setattr__(report.rows[0], "audit_trail_score", d("0.900000"))
    with pytest.raises(ValueError, match="derived_validation_digest|score"):
        research_source_audit_trail_score_payload(report)


def test_module_scope_is_report_only_and_has_no_external_surface() -> None:
    module = importlib.import_module("polymarket_alpha_lab.research_source_audit_trail_score")
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered_source = source.lower()

    forbidden_surface_tokens = (
        _unsafe("can", "did", "ate_id"),
        _unsafe("market_id"),
        _unsafe("market_", "sl", "ug"),
        _unsafe("market_", "ques", "tion"),
        _unsafe("source_", "ref"),
        _unsafe("source_", "ur", "l"),
        _unsafe("source_", "tex", "t"),
        _unsafe("dsn"),
        _unsafe("table_name"),
        _unsafe("tok", "en"),
        _unsafe("wal", "let"),
        _unsafe("au", "th"),
        _unsafe("ord", "er"),
        _unsafe("tra", "de"),
        _unsafe("posi", "tion"),
        _unsafe("bu", "y"),
        _unsafe("se", "ll"),
        _unsafe("recom", "mendation"),
    )
    assert not any(token in lowered_source for token in forbidden_surface_tokens)
    assert not hasattr(module, "client")
    assert not hasattr(module, "session")

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "asyncio",
        "http",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
