from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
import ast
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
SHA_A = "sha256:" + ("a" * 64)
SHA_B = "sha256:" + ("b" * 64)
SHA_C = "sha256:" + ("c" * 64)
PRECEDENT_A = "sha256:" + ("1" * 64)
PRECEDENT_B = "sha256:" + ("2" * 64)
PRECEDENT_C = "sha256:" + ("3" * 64)
SOURCE_A = "sha256:" + ("4" * 64)
SOURCE_B = "sha256:" + ("5" * 64)
SOURCE_C = "sha256:" + ("6" * 64)
MEMORY_A = "sha256:" + ("7" * 64)
MEMORY_B = "sha256:" + ("8" * 64)
MEMORY_C = "sha256:" + ("9" * 64)
CAL_A = "sha256:" + ("d" * 64)
CAL_B = "sha256:" + ("e" * 64)
CAL_C = "sha256:" + ("f" * 64)
REVIEW_A = "sha256:" + ("0" * 64)
REVIEW_B = "sha256:" + ("b" * 64)
REVIEW_C = "sha256:" + ("c" * 64)


class _DecimalSubclass(Decimal):
    pass


class _TzInfoSubclass(tzinfo):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_specialist_evidence_reuse_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "min_pass_precedent_relevance_score": d("0.750000"),
        "min_watch_precedent_relevance_score": d("0.500000"),
        "source_watch_age_seconds": d("86400.000000"),
        "source_block_age_seconds": d("259200.000000"),
        "memory_watch_age_seconds": d("86400.000000"),
        "memory_block_age_seconds": d("259200.000000"),
        "min_pass_calibration_contribution_score": d("0.650000"),
        "min_watch_calibration_contribution_score": d("0.400000"),
        "contradiction_watch_gap_ratio": d("0.250000"),
        "contradiction_block_gap_ratio": d("0.500000"),
        "peer_review_watch_gap_ratio": d("0.250000"),
        "peer_review_block_gap_ratio": d("0.500000"),
        "precedent_relevance_weight": d("0.200000"),
        "source_freshness_weight": d("0.150000"),
        "stale_memory_weight": d("0.150000"),
        "calibration_contribution_weight": d("0.200000"),
        "contradiction_handling_weight": d("0.150000"),
        "peer_review_coverage_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchTeamSpecialistEvidenceReuseQualityReportConfig(**values)


def reuse_record(
    team_ref: str,
    specialist_ref: str,
    evidence_reuse_digest: str,
    precedent_bundle_digest: str,
    source_bundle_digest: str,
    memory_snapshot_digest: str,
    calibration_digest: str,
    peer_review_digest: str,
    *,
    precedent_relevance_score: str,
    source_age_seconds: int,
    memory_age_seconds: int,
    calibration_contribution_score: str,
    contradiction_total: str,
    contradiction_resolved: str,
    peer_review_required: str,
    peer_review_completed: str,
):
    module = api()
    return module.ResearchTeamSpecialistEvidenceReuseQualityRecord(
        team_ref=team_ref,
        specialist_ref=specialist_ref,
        evidence_reuse_digest=evidence_reuse_digest,
        precedent_bundle_digest=precedent_bundle_digest,
        source_bundle_digest=source_bundle_digest,
        memory_snapshot_digest=memory_snapshot_digest,
        calibration_digest=calibration_digest,
        peer_review_digest=peer_review_digest,
        observed_at=GENERATED_AT - timedelta(seconds=600),
        source_last_observed_at=GENERATED_AT - timedelta(seconds=source_age_seconds),
        memory_refreshed_at=GENERATED_AT - timedelta(seconds=memory_age_seconds),
        precedent_relevance_score=d(precedent_relevance_score),
        calibration_contribution_score=d(calibration_contribution_score),
        contradiction_total_count=d(contradiction_total),
        contradiction_resolved_count=d(contradiction_resolved),
        peer_review_required_count=d(peer_review_required),
        peer_review_completed_count=d(peer_review_completed),
    )


def build_report(
    *records: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_team_specialist_evidence_reuse_quality_report(
        records,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_decimal_only_numerics(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_decimal_only_numerics(getattr(value, field.name))
        return
    if type(value) is dict:
        for item in value.values():
            assert_decimal_only_numerics(item)
        return
    if type(value) in (list, tuple):
        for item in value:
            assert_decimal_only_numerics(item)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_float_values(item)
    if type(value) in (list, tuple):
        for item in value:
            assert_no_float_values(item)


def test_scores_specialist_evidence_reuse_quality_from_required_dimensions() -> None:
    module = api()

    report = build_report(
        reuse_record(
            "team-beta",
            "specialist-weather",
            SHA_C,
            PRECEDENT_C,
            SOURCE_C,
            MEMORY_C,
            CAL_C,
            REVIEW_C,
            precedent_relevance_score="0.300000",
            source_age_seconds=300_000,
            memory_age_seconds=300_000,
            calibration_contribution_score="0.300000",
            contradiction_total="4",
            contradiction_resolved="1",
            peer_review_required="4",
            peer_review_completed="1",
        ),
        reuse_record(
            "team-alpha",
            "specialist-macro",
            SHA_A,
            PRECEDENT_A,
            SOURCE_A,
            MEMORY_A,
            CAL_A,
            REVIEW_A,
            precedent_relevance_score="0.900000",
            source_age_seconds=600,
            memory_age_seconds=600,
            calibration_contribution_score="0.850000",
            contradiction_total="2",
            contradiction_resolved="2",
            peer_review_required="2",
            peer_review_completed="2",
        ),
        reuse_record(
            "team-alpha",
            "specialist-rates",
            SHA_B,
            PRECEDENT_B,
            SOURCE_B,
            MEMORY_B,
            CAL_B,
            REVIEW_B,
            precedent_relevance_score="0.650000",
            source_age_seconds=90_000,
            memory_age_seconds=90_000,
            calibration_contribution_score="0.500000",
            contradiction_total="4",
            contradiction_resolved="3",
            peer_review_required="4",
            peer_review_completed="3",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        module.DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_REPORT_CONFIG_VERSION
    )
    assert module.RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert report.status == "block"
    assert report.reuse_record_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.low_precedent_relevance_count == d("2")
    assert report.stale_source_count == d("2")
    assert report.stale_memory_count == d("2")
    assert report.low_calibration_contribution_count == d("2")
    assert report.contradiction_gap_count == d("2")
    assert report.peer_review_gap_count == d("2")
    assert report.max_evidence_reuse_risk_score == d("0.805000")
    assert report.average_evidence_reuse_risk_score == d("0.401621")
    assert report.reason_codes == (
        "precedent_relevance_block",
        "precedent_relevance_watch",
        "source_freshness_block",
        "source_freshness_watch",
        "stale_memory_block",
        "stale_memory_watch",
        "calibration_contribution_block",
        "calibration_contribution_watch",
        "contradiction_handling_block",
        "contradiction_handling_watch",
        "peer_review_coverage_block",
        "peer_review_coverage_watch",
    )

    passed, watched, blocked = report.rows
    assert (passed.team_ref, passed.specialist_ref) == ("team-alpha", "specialist-macro")
    assert passed.precedent_relevance_gap == d("0.100000")
    assert passed.source_freshness_component == d("0.002315")
    assert passed.stale_memory_component == d("0.002315")
    assert passed.calibration_contribution_gap == d("0.150000")
    assert passed.contradiction_handling_gap_ratio == d("0.000000")
    assert passed.peer_review_coverage_gap_ratio == d("0.000000")
    assert passed.evidence_reuse_risk_score == d("0.050695")
    assert passed.status == "pass"
    assert passed.reason_codes == ("evidence_reuse_quality_pass",)

    assert (watched.team_ref, watched.specialist_ref) == ("team-alpha", "specialist-rates")
    assert watched.evidence_reuse_risk_score == d("0.349167")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "precedent_relevance_watch",
        "source_freshness_watch",
        "stale_memory_watch",
        "calibration_contribution_watch",
        "contradiction_handling_watch",
        "peer_review_coverage_watch",
    )

    assert (blocked.team_ref, blocked.specialist_ref) == ("team-beta", "specialist-weather")
    assert blocked.evidence_reuse_risk_score == d("0.805000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "precedent_relevance_block",
        "source_freshness_block",
        "stale_memory_block",
        "calibration_contribution_block",
        "contradiction_handling_block",
        "peer_review_coverage_block",
    )
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_only_numerics(report)


def test_empty_report_blocks_without_live_or_identifier_surface() -> None:
    module = api()

    report = build_report()

    assert report.status == "block"
    assert report.reuse_record_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.block_count == d("0")
    assert report.rows == ()
    assert report.max_evidence_reuse_risk_score == d("0.000000")
    assert report.average_evidence_reuse_risk_score == d("0.000000")
    assert report.reason_codes == ("evidence_reuse_quality_empty",)
    assert report.reason_code_counts == (
        module.ResearchTeamSpecialistEvidenceReuseQualityReasonCodeCount(
            reason_code="evidence_reuse_quality_empty",
            count=d("1"),
        ),
    )
    assert_decimal_only_numerics(report)


def test_payload_serialization_is_deterministic_tamper_evident_and_redacted() -> None:
    module = api()
    first = reuse_record(
        "team-alpha",
        "specialist-rates",
        SHA_B,
        PRECEDENT_B,
        SOURCE_B,
        MEMORY_B,
        CAL_B,
        REVIEW_B,
        precedent_relevance_score="0.650000",
        source_age_seconds=90_000,
        memory_age_seconds=90_000,
        calibration_contribution_score="0.500000",
        contradiction_total="4",
        contradiction_resolved="3",
        peer_review_required="4",
        peer_review_completed="3",
    )
    second = reuse_record(
        "team-alpha",
        "specialist-macro",
        SHA_A,
        PRECEDENT_A,
        SOURCE_A,
        MEMORY_A,
        CAL_A,
        REVIEW_A,
        precedent_relevance_score="0.900000",
        source_age_seconds=600,
        memory_age_seconds=600,
        calibration_contribution_score="0.850000",
        contradiction_total="2",
        contradiction_resolved="2",
        peer_review_required="2",
        peer_review_completed="2",
    )

    report_a = build_report(first, second)
    report_b = build_report(second, first)
    payload = module.research_team_specialist_evidence_reuse_quality_report_payload(report_a)
    encoded = json.dumps(payload, sort_keys=True)

    assert report_a.rows == report_b.rows
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["reuse_record_count"] == "2"
    assert payload["rows"][0]["evidence_reuse_risk_score"] == "0.050695"
    assert payload["rows"][0]["evidence_reuse_digest"] == SHA_A
    assert payload["rows"][0]["derived_validation_digest"] == (
        report_a.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == report_a.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    json.loads(encoded)

    leaked_fragments = (
        "candidate-raw-123",
        "market_id",
        "market-slug",
        "will-this-happen",
        "https://example.test/source",
        "postgres://",
        "secret-token",
        "wallet",
        "order",
        "trade",
        "live",
    )
    assert not any(fragment in encoded for fragment in leaked_fragments)

    tampered = dict(payload)
    tampered["block_count"] = "7"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_specialist_evidence_reuse_quality_report_payload(tampered)

    object.__setattr__(report_a.rows[0], "evidence_reuse_risk_score", d("0.000001"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.research_team_specialist_evidence_reuse_quality_report_payload(report_a)

    with pytest.raises(ValueError, match="Decimal"):
        module.research_team_specialist_evidence_reuse_quality_report_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="float"):
        module.research_team_specialist_evidence_reuse_quality_report_payload(
            {"score": 0.5, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_team_specialist_evidence_reuse_quality_report_payload(
            {
                "market_id": "raw-market",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_enforces_exact_decimal_types_hard_flags_and_safe_refs() -> None:
    module = api()

    with pytest.raises(ValueError, match="precedent_relevance_weight"):
        config(precedent_relevance_weight=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_freshness_weight"):
        config(source_freshness_weight=_DecimalSubclass("0.150000"))
    with pytest.raises(ValueError, match="weights must sum"):
        config(peer_review_coverage_weight=d("0.140000"))
    with pytest.raises(ValueError, match="source_block_age_seconds"):
        config(source_block_age_seconds=d("86400.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)

    record = reuse_record(
        "team-alpha",
        "specialist-macro",
        SHA_A,
        PRECEDENT_A,
        SOURCE_A,
        MEMORY_A,
        CAL_A,
        REVIEW_A,
        precedent_relevance_score="0.900000",
        source_age_seconds=600,
        memory_age_seconds=600,
        calibration_contribution_score="0.850000",
        contradiction_total="2",
        contradiction_resolved="2",
        peer_review_required="2",
        peer_review_completed="2",
    )
    report = build_report(record)

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(record, readonly=False)
    with pytest.raises(ValueError, match="unsafe public"):
        replace(record, team_ref="candidate-raw-123")
    with pytest.raises(ValueError, match="must not exceed total"):
        replace(record, contradiction_resolved_count=d("3"))
    with pytest.raises(ValueError, match="must not be in the future"):
        build_report(replace(record, source_last_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="timezone-aware"):
        build_report(record, generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="datetime"):
        build_report(record, generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_TzInfoSubclass()))
    for field_name in (
        "low_precedent_relevance_count",
        "stale_source_count",
        "stale_memory_count",
        "low_calibration_contribution_count",
        "contradiction_gap_count",
        "peer_review_gap_count",
    ):
        with pytest.raises(ValueError, match=field_name):
            replace(report, **{field_name: d("1"), "derived_validation_digest": ""})
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=(), derived_validation_digest="")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_module_scope_has_no_db_network_wallet_order_trade_or_live_surface() -> None:
    module = api()
    source_text = inspect.getsource(module)
    tree = ast.parse(source_text)

    assert module.RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_REPORT_CONFIG_VERSION",
        "RESEARCH_TEAM_SPECIALIST_EVIDENCE_REUSE_QUALITY_STATUSES",
        "ResearchTeamSpecialistEvidenceReuseQualityReasonCodeCount",
        "ResearchTeamSpecialistEvidenceReuseQualityRecord",
        "ResearchTeamSpecialistEvidenceReuseQualityReport",
        "ResearchTeamSpecialistEvidenceReuseQualityReportConfig",
        "ResearchTeamSpecialistEvidenceReuseQualityRow",
        "build_research_team_specialist_evidence_reuse_quality_report",
        "research_team_specialist_evidence_reuse_quality_report_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }
    forbidden_source_terms = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "private_key",
        "network",
        "connect(",
        "open(",
        "subprocess",
        "pathlib",
    )
    lowered = source_text.lower()
    assert all(term not in lowered for term in forbidden_source_terms)

    public_surface = " ".join(module.__all__)
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type) and is_dataclass(exported):
            public_surface += " " + " ".join(field.name for field in fields(exported))
    lowered_public_surface = public_surface.lower()
    assert all(
        term not in lowered_public_surface
        for term in (
            "candidate_id",
            "market_id",
            "market_slug",
            "question",
            "source_url",
            "source_text",
            "dsn",
            "table_name",
            "token",
            "wallet",
            "order",
            "trade",
            "sizing",
            "recommendation",
            "execution",
            "auth",
            "live",
        )
    )
