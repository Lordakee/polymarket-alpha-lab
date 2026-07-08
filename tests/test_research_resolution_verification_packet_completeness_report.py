from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_resolution_verification_packet_completeness_report import (
    DEFAULT_RESEARCH_RESOLUTION_VERIFICATION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION,
    ResearchResolutionVerificationPacketAggregate,
    ResearchResolutionVerificationPacketCompletenessConfig,
    ResearchResolutionVerificationPacketCompletenessReport,
    ResearchResolutionVerificationPacketCompletenessRow,
    build_research_resolution_verification_packet_completeness_report,
    research_resolution_verification_packet_completeness_report_digest,
    research_resolution_verification_packet_completeness_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_resolution_verification_packet_completeness_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchResolutionVerificationPacketCompletenessConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_RESOLUTION_VERIFICATION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION
        ),
        "minimum_rule_citation_coverage_ratio": ONE,
        "block_rule_citation_coverage_ratio": d("0.750000"),
        "minimum_source_agreement_ratio": d("0.800000"),
        "block_source_agreement_ratio": d("0.500000"),
        "watch_stale_evidence_pressure_ratio": d("0.250000"),
        "block_stale_evidence_pressure_ratio": d("0.500000"),
        "watch_ambiguity_flag_pressure_ratio": d("0.100000"),
        "block_ambiguity_flag_pressure_ratio": d("0.250000"),
        "watch_recheck_urgency_ratio": d("0.200000"),
        "block_recheck_urgency_ratio": d("0.500000"),
    }
    values.update(overrides)
    return ResearchResolutionVerificationPacketCompletenessConfig(**values)


def aggregate(
    packet_group_ref: str = "resolution-group-alpha",
    *,
    required_rule_citation_count: Decimal = d("4.000000"),
    cited_rule_count: Decimal = d("4.000000"),
    verification_source_count: Decimal = d("5.000000"),
    agreeing_source_count: Decimal = d("5.000000"),
    evidence_item_count: Decimal = d("10.000000"),
    stale_evidence_count: Decimal = ZERO,
    ambiguity_flag_count: Decimal = ZERO,
    pending_recheck_count: Decimal = ZERO,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchResolutionVerificationPacketAggregate:
    return ResearchResolutionVerificationPacketAggregate(
        packet_group_ref=packet_group_ref,
        required_rule_citation_count=required_rule_citation_count,
        cited_rule_count=cited_rule_count,
        verification_source_count=verification_source_count,
        agreeing_source_count=agreeing_source_count,
        evidence_item_count=evidence_item_count,
        stale_evidence_count=stale_evidence_count,
        ambiguity_flag_count=ambiguity_flag_count,
        pending_recheck_count=pending_recheck_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *aggregates: ResearchResolutionVerificationPacketAggregate,
    cfg: ResearchResolutionVerificationPacketCompletenessConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionVerificationPacketCompletenessReport:
    return build_research_resolution_verification_packet_completeness_report(
        aggregates,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_pass_watch_block_resolution_packet_completeness_and_payload() -> None:
    inputs = (
        aggregate("resolution-group-pass"),
        aggregate(
            "resolution-group-watch",
            cited_rule_count=d("3.000000"),
            agreeing_source_count=d("4.000000"),
            stale_evidence_count=d("3.000000"),
            ambiguity_flag_count=ONE,
            pending_recheck_count=d("2.000000"),
        ),
        aggregate(
            "resolution-group-block",
            required_rule_citation_count=d("4.000000"),
            cited_rule_count=d("2.000000"),
            verification_source_count=d("4.000000"),
            agreeing_source_count=ONE,
            evidence_item_count=d("8.000000"),
            stale_evidence_count=d("5.000000"),
            ambiguity_flag_count=d("3.000000"),
            pending_recheck_count=d("4.000000"),
        ),
    )
    first = report(*inputs)
    second = report(*reversed(inputs))

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_RESOLUTION_VERIFICATION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION
    )
    assert first.packet_group_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.required_rule_citation_count == d("12.000000")
    assert first.cited_rule_count == d("9.000000")
    assert first.rule_citation_coverage_ratio == d("0.750000")
    assert first.source_agreement_ratio == d("0.714286")
    assert first.stale_evidence_pressure_ratio == d("0.285714")
    assert first.ambiguity_flag_pressure_ratio == d("0.142857")
    assert first.recheck_urgency_ratio == d("0.214286")
    assert first.min_completeness_score == d("0.450000")
    assert first.status == "block"
    assert first.reason_codes == (
        "rule_citation_coverage_block",
        "source_agreement_block",
        "stale_evidence_pressure_block",
        "ambiguity_flag_pressure_block",
        "recheck_urgency_block",
        "resolution_verification_packet_completeness_block",
        "rule_citation_coverage_watch",
        "stale_evidence_pressure_watch",
        "ambiguity_flag_pressure_watch",
        "recheck_urgency_watch",
    )
    assert tuple(row.packet_group_ref for row in first.rows) == (
        "resolution-group-block",
        "resolution-group-watch",
        "resolution-group-pass",
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")

    blocked = first.rows[0]
    assert blocked.rule_citation_coverage_ratio == d("0.500000")
    assert blocked.source_agreement_ratio == d("0.250000")
    assert blocked.stale_evidence_pressure_ratio == d("0.625000")
    assert blocked.ambiguity_flag_pressure_ratio == d("0.375000")
    assert blocked.recheck_urgency_ratio == d("0.500000")
    assert blocked.completeness_score == d("0.450000")
    assert blocked.reason_codes == (
        "rule_citation_coverage_block",
        "source_agreement_block",
        "stale_evidence_pressure_block",
        "ambiguity_flag_pressure_block",
        "recheck_urgency_block",
    )
    assert_digest(blocked.validation_digest)
    assert_digest(first.validation_digest)

    payload = research_resolution_verification_packet_completeness_report_payload(first)
    assert payload == research_resolution_verification_packet_completeness_report_payload(
        second,
    )
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["packet_group_count"] == "3.000000"
    assert payload["rows"][0]["completeness_score"] == "0.450000"
    assert payload["rows"][0]["validation_digest"] == blocked.validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = research_resolution_verification_packet_completeness_report_digest(first)
    assert "rows" not in digest
    assert digest["packet_group_count"] == payload["packet_group_count"]
    assert digest["status"] == "block"
    assert digest["validation_digest"] == first.validation_digest
    assert_no_float_or_int_values(digest)


def test_empty_report_blocks_without_resolution_packets() -> None:
    completeness = report()

    assert completeness.packet_group_count == ZERO
    assert completeness.pass_count == ZERO
    assert completeness.watch_count == ZERO
    assert completeness.block_count == ZERO
    assert completeness.min_completeness_score is None
    assert completeness.rule_citation_coverage_ratio == ZERO
    assert completeness.source_agreement_ratio == ZERO
    assert completeness.stale_evidence_pressure_ratio == ZERO
    assert completeness.ambiguity_flag_pressure_ratio == ZERO
    assert completeness.recheck_urgency_ratio == ZERO
    assert completeness.status == "block"
    assert completeness.reason_codes == (
        "resolution_verification_packet_completeness_no_packets",
    )
    assert completeness.rows == ()
    assert completeness.paper_only is True
    assert completeness.report_only is True
    assert completeness.readonly is True
    assert_digest(completeness.validation_digest)


def test_decimal_only_frozen_flags_and_input_validation() -> None:
    completeness = report(aggregate("resolution-group-frozen"))

    assert is_dataclass(ResearchResolutionVerificationPacketCompletenessConfig)
    assert is_dataclass(ResearchResolutionVerificationPacketAggregate)
    assert is_dataclass(ResearchResolutionVerificationPacketCompletenessRow)
    assert is_dataclass(ResearchResolutionVerificationPacketCompletenessReport)
    with pytest.raises(FrozenInstanceError):
        completeness.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        completeness.rows[0].completeness_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        aggregate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(completeness, readonly=False)

    with pytest.raises(ValueError, match="required_rule_citation_count"):
        aggregate(required_rule_citation_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_agreement"):
        aggregate(agreeing_source_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="cited_rule_count"):
        aggregate(
            required_rule_citation_count=ONE,
            cited_rule_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="stale_evidence_count"):
        aggregate(evidence_item_count=ONE, stale_evidence_count=d("2.000000"))
    with pytest.raises(ValueError, match="packet_group_ref"):
        report(aggregate("resolution-group-dupe"), aggregate("resolution-group-dupe"))
    with pytest.raises(ValueError, match="generated_at"):
        report(aggregate("resolution-group-time"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            aggregate("resolution-group-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="block_rule_citation_coverage_ratio"):
        config(
            minimum_rule_citation_coverage_ratio=d("0.700000"),
            block_rule_citation_coverage_ratio=d("0.750000"),
        )
    with pytest.raises(ValueError, match="block_stale_evidence_pressure_ratio"):
        config(
            watch_stale_evidence_pressure_ratio=d("0.600000"),
            block_stale_evidence_pressure_ratio=d("0.500000"),
        )

    for item in (completeness, *completeness.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, tuple):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_validation_digest_and_payload_reject_tampering() -> None:
    completeness = report(aggregate("resolution-group-consistent"))
    row = completeness.rows[0]

    with pytest.raises(ValueError, match="completeness_score must match"):
        replace(row, completeness_score=row.completeness_score - d("0.000001"))
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(completeness, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(
            completeness,
            rows=(
                report(aggregate("resolution-group-zeta")).rows[0],
                row,
            ),
        )
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(completeness, validation_digest="0" * 64)

    payload = research_resolution_verification_packet_completeness_report_payload(
        completeness,
    )
    assert research_resolution_verification_packet_completeness_report_payload(
        payload,
    ) == payload
    with pytest.raises(ValueError, match="readonly"):
        research_resolution_verification_packet_completeness_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_resolution_verification_packet_completeness_report_payload(
            {**payload, "source_url": "https://example.invalid"},
        )
    with pytest.raises(ValueError, match="numeric"):
        research_resolution_verification_packet_completeness_report_payload(
            {**payload, "packet_group_count": 1},
        )


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_resolution_verification_packet_completeness_report as completeness

    assert completeness.__all__ == (
        "DEFAULT_RESEARCH_RESOLUTION_VERIFICATION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION",
        "ResearchResolutionVerificationPacketAggregate",
        "ResearchResolutionVerificationPacketCompletenessConfig",
        "ResearchResolutionVerificationPacketCompletenessReport",
        "ResearchResolutionVerificationPacketCompletenessRow",
        "build_research_resolution_verification_packet_completeness_report",
        "research_resolution_verification_packet_completeness_report_digest",
        "research_resolution_verification_packet_completeness_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "market" "_" "id",
        "market" "-" "id",
        "slug",
        "ques" "tion",
        "source" "_" "url",
        "source" "-" "url",
        "source" "_" "text",
        "source" "-" "text",
        "raw" "_" "source",
        "raw" "-" "source",
        "li" "ve",
        "au" "th",
        "wal" "let",
        "broker",
        "or" "der",
        "can" "cel",
        "re" "place",
        "exchange",
        "private" "_" "key",
        "api" "_" "key",
        "sec" "ret",
        "po" "sition",
        "b" "uy",
        "se" "ll",
        "reco" "mmend",
        "siz" "ing",
        "data" "base",
        "net" "work",
        "req" "uests",
        "ht" "tp",
        "sock" "et",
        "sub" "process",
        "trade",
        "open(",
        "pathlib",
    )
    assert [term for term in forbidden_terms if term in lowered] == []

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "sock" "et",
        "sub" "process",
        "req" "uests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "send",
        "submit",
        "write",
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
