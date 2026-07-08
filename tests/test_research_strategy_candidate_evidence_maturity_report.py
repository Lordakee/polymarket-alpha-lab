from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_candidate_evidence_maturity_report import (
    DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EVIDENCE_MATURITY_REPORT_CONFIG_VERSION,
    ResearchStrategyCandidateEvidenceMaturityConfig,
    ResearchStrategyCandidateEvidenceMaturityInput,
    ResearchStrategyCandidateEvidenceMaturityReasonCodeCount,
    ResearchStrategyCandidateEvidenceMaturityReport,
    ResearchStrategyCandidateEvidenceMaturityRow,
    build_research_strategy_candidate_evidence_maturity_report,
    research_strategy_candidate_evidence_maturity_report_digest,
    research_strategy_candidate_evidence_maturity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_candidate_evidence_maturity_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> ResearchStrategyCandidateEvidenceMaturityConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EVIDENCE_MATURITY_REPORT_CONFIG_VERSION
        ),
        "required_source_class_count": d("3.000000"),
        "stale_evidence_watch_seconds": d("172800.000000"),
        "stale_evidence_block_seconds": d("604800.000000"),
        "source_class_coverage_watch": d("0.800000"),
        "source_class_coverage_block": d("0.500000"),
        "claim_consistency_watch": d("0.800000"),
        "claim_consistency_block": d("0.600000"),
        "resolution_rule_clarity_watch": d("0.800000"),
        "resolution_rule_clarity_block": d("0.600000"),
        "manual_review_watch": d("0.400000"),
        "manual_review_block": d("0.750000"),
    }
    values.update(overrides)
    return ResearchStrategyCandidateEvidenceMaturityConfig(**values)


def candidate(
    screening_key: str = "candidate-alpha",
    *,
    source_class_count: Decimal = d("3.000000"),
    evidence_observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    claim_consistency_score: Decimal = d("0.950000"),
    resolution_rule_clarity_score: Decimal = d("0.900000"),
    manual_review_pressure: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyCandidateEvidenceMaturityInput:
    return ResearchStrategyCandidateEvidenceMaturityInput(
        screening_key=screening_key,
        source_class_count=source_class_count,
        evidence_observed_at=evidence_observed_at,
        claim_consistency_score=claim_consistency_score,
        resolution_rule_clarity_score=resolution_rule_clarity_score,
        manual_review_pressure=manual_review_pressure,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchStrategyCandidateEvidenceMaturityInput,
    config: ResearchStrategyCandidateEvidenceMaturityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyCandidateEvidenceMaturityReport:
    return build_research_strategy_candidate_evidence_maturity_report(
        rows,
        config=cfg() if config is None else config,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_pass_report_uses_public_hash_rows_decimal_payload_and_digest() -> None:
    maturity = report(candidate("candidate-pass"))

    assert is_dataclass(maturity)
    assert maturity.generated_at == GENERATED_AT
    assert maturity.config_version == (
        DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EVIDENCE_MATURITY_REPORT_CONFIG_VERSION
    )
    assert maturity.candidate_count == d("1.000000")
    assert maturity.pass_count == d("1.000000")
    assert maturity.watch_count == ZERO
    assert maturity.block_count == ZERO
    assert maturity.status == "pass"
    assert maturity.reason_codes == ("candidate_evidence_maturity_pass",)
    assert maturity.paper_only is True
    assert maturity.report_only is True
    assert maturity.readonly is True

    row = maturity.rows[0]
    assert row.aggregate_row_number == d("1.000000")
    assert row.aggregate_row_hash == hashlib.sha256(
        b"candidate-pass",
    ).hexdigest()
    assert row.status == "pass"
    assert row.source_class_coverage_score == d("1.000000")
    assert row.evidence_age_seconds == d("3600.000000")
    assert row.evidence_age_pressure_score == ZERO
    assert row.claim_consistency_gap_score == d("0.050000")
    assert row.resolution_rule_gap_score == d("0.100000")
    assert row.manual_review_urgency_score == d("0.100000")
    assert row.reason_codes == ("evidence_maturity_clear",)
    assert not hasattr(row, "screening_key")

    payload = research_strategy_candidate_evidence_maturity_report_payload(maturity)
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["rows"][0]["aggregate_row_hash"] == row.aggregate_row_hash
    assert "screening_key" not in payload["rows"][0]
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["public_digest"] == (
        research_strategy_candidate_evidence_maturity_report_digest(maturity)
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)
    json.dumps(payload, sort_keys=True)


def test_watch_and_block_rows_roll_up_public_status_values() -> None:
    maturity = report(
        candidate(
            "candidate-watch",
            source_class_count=d("2.000000"),
            evidence_observed_at=GENERATED_AT - timedelta(days=3),
            claim_consistency_score=d("0.750000"),
        ),
        candidate(
            "candidate-block",
            source_class_count=d("1.000000"),
            evidence_observed_at=GENERATED_AT - timedelta(days=8),
            claim_consistency_score=d("0.550000"),
            resolution_rule_clarity_score=d("0.500000"),
            manual_review_pressure=d("0.800000"),
        ),
    )

    assert maturity.status == "block"
    assert maturity.pass_count == ZERO
    assert maturity.watch_count == d("1.000000")
    assert maturity.block_count == d("1.000000")
    assert maturity.source_class_coverage_watch_count == d("2.000000")
    assert maturity.stale_evidence_count == d("2.000000")
    assert maturity.claim_consistency_watch_count == d("2.000000")
    assert maturity.resolution_rule_clarity_watch_count == d("1.000000")
    assert maturity.manual_review_urgent_count == d("1.000000")
    assert maturity.reason_codes == (
        "candidate_evidence_maturity_block",
        "claim_consistency_block",
        "claim_consistency_watch",
        "evidence_stale_block",
        "evidence_stale_watch",
        "manual_review_urgency_block",
        "resolution_rule_clarity_block",
        "source_class_coverage_block",
        "source_class_coverage_watch",
    )
    assert tuple(row.status for row in maturity.rows) == ("block", "watch")
    assert maturity.rows[0].reason_codes == (
        "claim_consistency_block",
        "evidence_stale_block",
        "manual_review_urgency_block",
        "resolution_rule_clarity_block",
        "source_class_coverage_block",
    )
    assert maturity.rows[1].reason_codes == (
        "claim_consistency_watch",
        "evidence_stale_watch",
        "source_class_coverage_watch",
    )


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    maturity = report()

    assert maturity.status == "block"
    assert maturity.candidate_count == ZERO
    assert maturity.pass_count == ZERO
    assert maturity.watch_count == ZERO
    assert maturity.block_count == ZERO
    assert maturity.mean_manual_review_urgency_score == ZERO
    assert maturity.max_manual_review_urgency_score == ZERO
    assert maturity.reason_codes == ("candidate_evidence_maturity_no_inputs",)
    assert maturity.reason_code_counts == (
        ResearchStrategyCandidateEvidenceMaturityReasonCodeCount(
            reason_code="candidate_evidence_maturity_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert maturity.rows == ()


def test_utc_normalization_and_decimal_only_validation() -> None:
    maturity = report(
        candidate(
            evidence_observed_at=datetime(
                2026,
                7,
                8,
                7,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            8,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert maturity.generated_at == GENERATED_AT
    assert maturity.rows[0].evidence_observed_at == datetime(
        2026,
        7,
        8,
        11,
        0,
        tzinfo=UTC,
    )
    assert maturity.rows[0].evidence_age_seconds == d("3600.000000")

    with pytest.raises(ValueError, match="required_source_class_count"):
        cfg(required_source_class_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_class_count"):
        candidate(source_class_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="claim_consistency_score"):
        candidate(claim_consistency_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        candidate(evidence_observed_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("aware-evidence"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="evidence_observed_at"):
        candidate(
            evidence_observed_at=datetime(
                2026,
                7,
                8,
                11,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="evidence_observed_at"):
        report(candidate(evidence_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=["manual_review_watch"])  # type: ignore[arg-type]

    for public_value in (maturity, *maturity.rows, *maturity.reason_code_counts):
        for field in fields(public_value):
            value = getattr(public_value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_public_leak_rejection_at_construction_and_payload_boundary() -> None:
    for unsafe_value in (
        "raw_candidate_id:abc",
        "market_id:123",
        "market_slug:event",
        "question:will-it-happen",
        "source_url:https://example.invalid",
        "source_text:verbatim",
        "dsn=postgres://example",
        "table_name:research",
        "private_token=secret",
        "wallet-address",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            candidate(screening_key=unsafe_value)

    maturity = report(candidate("candidate-safe"))
    object.__setattr__(maturity.rows[0], "aggregate_row_hash", "source_url:https")
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_candidate_evidence_maturity_report_payload(maturity)


def test_hard_flags_frozen_dataclasses_and_payload_revalidation() -> None:
    maturity = report(candidate("candidate-frozen"))

    assert is_dataclass(ResearchStrategyCandidateEvidenceMaturityConfig)
    assert is_dataclass(ResearchStrategyCandidateEvidenceMaturityInput)
    assert is_dataclass(ResearchStrategyCandidateEvidenceMaturityRow)
    assert is_dataclass(ResearchStrategyCandidateEvidenceMaturityReasonCodeCount)
    assert is_dataclass(ResearchStrategyCandidateEvidenceMaturityReport)
    with pytest.raises(FrozenInstanceError):
        maturity.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        maturity.rows[0].manual_review_urgency_score = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(maturity, readonly=False)

    object.__setattr__(maturity.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        research_strategy_candidate_evidence_maturity_report_payload(maturity)


def test_deterministic_payload_sorting_reason_counts_and_public_exports() -> None:
    first = report(
        candidate(
            "zeta-watch",
            source_class_count=d("2.000000"),
            reason_codes=("manual_review_watch",),
        ),
        candidate(
            "beta-block",
            source_class_count=d("1.000000"),
            evidence_observed_at=GENERATED_AT - timedelta(days=8),
            claim_consistency_score=d("0.500000"),
        ),
        candidate("alpha-pass"),
    )
    second = report(
        candidate("alpha-pass"),
        candidate(
            "beta-block",
            source_class_count=d("1.000000"),
            evidence_observed_at=GENERATED_AT - timedelta(days=8),
            claim_consistency_score=d("0.500000"),
        ),
        candidate(
            "zeta-watch",
            source_class_count=d("2.000000"),
            reason_codes=("manual_review_watch",),
        ),
    )

    assert research_strategy_candidate_evidence_maturity_report_payload(first) == (
        research_strategy_candidate_evidence_maturity_report_payload(second)
    )
    assert research_strategy_candidate_evidence_maturity_report_digest(first) == (
        research_strategy_candidate_evidence_maturity_report_digest(second)
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert first.reason_code_counts == (
        ResearchStrategyCandidateEvidenceMaturityReasonCodeCount(
            reason_code="claim_consistency_block",
            count=d("1.000000"),
        ),
        ResearchStrategyCandidateEvidenceMaturityReasonCodeCount(
            reason_code="evidence_maturity_clear",
            count=d("1.000000"),
        ),
        ResearchStrategyCandidateEvidenceMaturityReasonCodeCount(
            reason_code="evidence_stale_block",
            count=d("1.000000"),
        ),
        ResearchStrategyCandidateEvidenceMaturityReasonCodeCount(
            reason_code="manual_review_watch",
            count=d("1.000000"),
        ),
        ResearchStrategyCandidateEvidenceMaturityReasonCodeCount(
            reason_code="source_class_coverage_block",
            count=d("1.000000"),
        ),
        ResearchStrategyCandidateEvidenceMaturityReasonCodeCount(
            reason_code="source_class_coverage_watch",
            count=d("1.000000"),
        ),
    )

    with pytest.raises(ValueError, match="public_digest"):
        replace(first, public_digest="0" * 64)
    with pytest.raises(ValueError, match="candidate_count"):
        replace(first, candidate_count=d("9.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(first, status="pass")

    import polymarket_alpha_lab.research_strategy_candidate_evidence_maturity_report as maturity_module

    assert maturity_module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EVIDENCE_MATURITY_REPORT_CONFIG_VERSION",
        "ResearchStrategyCandidateEvidenceMaturityConfig",
        "ResearchStrategyCandidateEvidenceMaturityInput",
        "ResearchStrategyCandidateEvidenceMaturityReasonCodeCount",
        "ResearchStrategyCandidateEvidenceMaturityReport",
        "ResearchStrategyCandidateEvidenceMaturityRow",
        "build_research_strategy_candidate_evidence_maturity_report",
        "research_strategy_candidate_evidence_maturity_report_digest",
        "research_strategy_candidate_evidence_maturity_report_payload",
    )


def test_static_forbidden_public_surfaces_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "order",
        "trade",
        "trading",
        "position_size",
        "buy",
        "sell",
        "recommend",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
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
                assert func.id not in {"float", "open", "__import__", "asdict"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(alias.name != "asdict" for alias in node.names)
