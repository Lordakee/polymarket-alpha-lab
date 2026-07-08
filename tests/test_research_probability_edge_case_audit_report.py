from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_probability_edge_case_audit_report import (
    DEFAULT_RESEARCH_PROBABILITY_EDGE_CASE_AUDIT_CONFIG_VERSION,
    ResearchProbabilityEdgeCaseAuditConfig,
    ResearchProbabilityEdgeCaseAuditInput,
    ResearchProbabilityEdgeCaseAuditPublicDigest,
    ResearchProbabilityEdgeCaseAuditReport,
    build_research_probability_edge_case_audit_report,
    research_probability_edge_case_audit_digest,
    research_probability_edge_case_audit_digest_payload,
    research_probability_edge_case_audit_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_probability_edge_case_audit_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchProbabilityEdgeCaseAuditConfig:
    values: dict[str, object] = {
        "config_version": "research-probability-edge-case-audit-test-v0",
        "watch_extreme_probability_tail_threshold": d("0.050000"),
        "block_extreme_probability_tail_threshold": d("0.010000"),
        "min_pass_liquidity_score": d("0.500000"),
        "min_watch_liquidity_score": d("0.200000"),
        "watch_short_settlement_hours": d("24.000000"),
        "block_short_settlement_hours": d("6.000000"),
        "watch_evidence_conflict_score": d("0.500000"),
        "block_evidence_conflict_score": d("0.800000"),
    }
    values.update(overrides)
    return ResearchProbabilityEdgeCaseAuditConfig(**values)


def input_row(
    audit_key: str,
    *,
    probability: str,
    liquidity: str,
    settlement_hours: str,
    conflict: str,
    observed_at: datetime = GENERATED_AT,
    public_summary: str = "manual audit boundary check",
) -> ResearchProbabilityEdgeCaseAuditInput:
    return ResearchProbabilityEdgeCaseAuditInput(
        audit_key=audit_key,
        model_probability=d(probability),
        liquidity_score=d(liquidity),
        settlement_hours=d(settlement_hours),
        evidence_conflict_score=d(conflict),
        observed_at=observed_at,
        public_summary=public_summary,
    )


def report(
    *rows: ResearchProbabilityEdgeCaseAuditInput,
    cfg: ResearchProbabilityEdgeCaseAuditConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchProbabilityEdgeCaseAuditReport:
    return build_research_probability_edge_case_audit_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_pass_watch_and_block_statuses_cover_boundary_risk_factors() -> None:
    audit_report = report(
        input_row(
            "pass-case",
            probability="0.420000",
            liquidity="0.800000",
            settlement_hours="72.000000",
            conflict="0.100000",
        ),
        input_row(
            "watch-case",
            probability="0.040000",
            liquidity="0.400000",
            settlement_hours="18.000000",
            conflict="0.600000",
        ),
        input_row(
            "block-case",
            probability="0.995000",
            liquidity="0.100000",
            settlement_hours="3.000000",
            conflict="0.900000",
        ),
    )

    assert audit_report.config_version == "research-probability-edge-case-audit-test-v0"
    assert audit_report.status == "block"
    assert audit_report.case_count == d("3.000000")
    assert audit_report.pass_count == d("1.000000")
    assert audit_report.watch_count == d("1.000000")
    assert audit_report.block_count == d("1.000000")
    assert audit_report.extreme_probability_count == d("2.000000")
    assert audit_report.low_liquidity_count == d("2.000000")
    assert audit_report.short_settlement_count == d("2.000000")
    assert audit_report.conflict_evidence_count == d("2.000000")
    assert tuple(row.audit_key for row in audit_report.rows) == (
        "block-case",
        "watch-case",
        "pass-case",
    )

    block_row = audit_report.rows[0]
    assert block_row.status == "block"
    assert block_row.probability_tail_distance == d("0.005000")
    assert block_row.reason_codes == (
        "edge_case_audit_block",
        "evidence_conflict_block",
        "extreme_probability_block",
        "low_liquidity_block",
        "short_settlement_block",
    )

    watch_row = audit_report.rows[1]
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "edge_case_audit_watch",
        "evidence_conflict_watch",
        "extreme_probability_watch",
        "low_liquidity_watch",
        "short_settlement_watch",
    )
    assert audit_report.reason_codes == (
        "edge_case_audit_block",
        "edge_case_audit_pass",
        "edge_case_audit_watch",
        "evidence_conflict_block",
        "evidence_conflict_watch",
        "extreme_probability_block",
        "extreme_probability_watch",
        "low_liquidity_block",
        "low_liquidity_watch",
        "short_settlement_block",
        "short_settlement_watch",
    )
    assert audit_report.reason_code_counts == (
        ("edge_case_audit_block", d("1.000000")),
        ("edge_case_audit_pass", d("1.000000")),
        ("edge_case_audit_watch", d("1.000000")),
        ("evidence_conflict_block", d("1.000000")),
        ("evidence_conflict_watch", d("1.000000")),
        ("extreme_probability_block", d("1.000000")),
        ("extreme_probability_watch", d("1.000000")),
        ("low_liquidity_block", d("1.000000")),
        ("low_liquidity_watch", d("1.000000")),
        ("short_settlement_block", d("1.000000")),
        ("short_settlement_watch", d("1.000000")),
    )


def test_empty_report_blocks_for_missing_audit_inputs() -> None:
    audit_report = report()

    assert audit_report.status == "block"
    assert audit_report.case_count == d("0.000000")
    assert audit_report.rows == ()
    assert audit_report.reason_codes == ("edge_case_audit_missing_inputs",)
    assert audit_report.reason_code_counts == (
        ("edge_case_audit_missing_inputs", d("1.000000")),
    )


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("model_probability", 1),
        ("liquidity_score", 0.5),
        ("settlement_hours", "12.000000"),
        ("evidence_conflict_score", _DecimalSubclass("0.500000")),
    ),
)
def test_inputs_require_exact_decimal_values(field_name: str, value: object) -> None:
    values: dict[str, object] = {
        "audit_key": "strict-case",
        "model_probability": d("0.500000"),
        "liquidity_score": d("0.600000"),
        "settlement_hours": d("48.000000"),
        "evidence_conflict_score": d("0.200000"),
        "observed_at": GENERATED_AT,
        "public_summary": "manual audit boundary check",
    }
    values[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        ResearchProbabilityEdgeCaseAuditInput(**values)


def test_config_and_datetime_type_rejection_are_strict() -> None:
    with pytest.raises(ValueError, match="block_extreme_probability_tail_threshold"):
        config(
            watch_extreme_probability_tail_threshold=d("0.010000"),
            block_extreme_probability_tail_threshold=d("0.050000"),
        )
    with pytest.raises(ValueError, match="min_pass_liquidity_score"):
        config(min_pass_liquidity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        input_row(
            "bad-time",
            probability="0.500000",
            liquidity="0.600000",
            settlement_hours="48.000000",
            conflict="0.200000",
            observed_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_probability_edge_case_audit_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )


@pytest.mark.parametrize(
    ("field_name", "unsafe_value"),
    (
        ("audit_key", "raw-market-slug"),
        ("audit_key", "candidate-123"),
        ("public_summary", "source url contains raw text"),
        ("public_summary", "recommend buying yes here"),
        ("public_summary", "wallet order token details"),
    ),
)
def test_public_surface_rejects_leaky_identifiers_sources_and_advice(
    field_name: str,
    unsafe_value: str,
) -> None:
    values: dict[str, object] = {
        "audit_key": "safe-case",
        "model_probability": d("0.500000"),
        "liquidity_score": d("0.600000"),
        "settlement_hours": d("48.000000"),
        "evidence_conflict_score": d("0.200000"),
        "observed_at": GENERATED_AT,
        "public_summary": "manual audit boundary check",
    }
    values[field_name] = unsafe_value

    with pytest.raises(ValueError, match=field_name):
        ResearchProbabilityEdgeCaseAuditInput(**values)


def test_hard_flags_are_required_and_dataclasses_are_frozen() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchProbabilityEdgeCaseAuditConfig(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(
            "flag-case",
            probability="0.500000",
            liquidity="0.600000",
            settlement_hours="48.000000",
            conflict="0.200000",
        ).__class__(
            audit_key="flag-case",
            model_probability=d("0.500000"),
            liquidity_score=d("0.600000"),
            settlement_hours=d("48.000000"),
            evidence_conflict_score=d("0.200000"),
            observed_at=GENERATED_AT,
            public_summary="manual audit boundary check",
            report_only=False,
        )

    row = input_row(
        "frozen-case",
        probability="0.500000",
        liquidity="0.600000",
        settlement_hours="48.000000",
        conflict="0.200000",
        observed_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )
    assert row.observed_at == GENERATED_AT
    with pytest.raises(FrozenInstanceError):
        row.audit_key = "changed"  # type: ignore[misc]


def test_payload_is_deterministic_decimal_string_only_and_public_safe() -> None:
    audit_report = report(
        input_row(
            "zeta-case",
            probability="0.040000",
            liquidity="0.400000",
            settlement_hours="18.000000",
            conflict="0.600000",
            observed_at=GENERATED_AT.astimezone(timezone(timedelta(hours=3))),
        ),
        input_row(
            "alpha-case",
            probability="0.420000",
            liquidity="0.800000",
            settlement_hours="72.000000",
            conflict="0.100000",
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    first_payload = research_probability_edge_case_audit_report_payload(audit_report)
    second_payload = research_probability_edge_case_audit_report_payload(audit_report)
    encoded = json.dumps(first_payload, sort_keys=True)
    lowered = encoded.lower()

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["case_count"] == "2.000000"
    assert first_payload["rows"][0]["audit_key"] == "zeta-case"
    assert first_payload["rows"][0]["model_probability"] == "0.040000"
    assert first_payload["rows"][0]["observed_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(
        type(value) in (Decimal, float, int) for value in walk_values(first_payload)
    )
    assert all(
        forbidden not in lowered
        for forbidden in (
            "candidate",
            "market",
            "slug",
            "question",
            "source",
            "url",
            "text",
            "dsn",
            "table",
            "token",
            "wallet",
            "order",
            "trade",
            "position",
            "buy",
            "sell",
            "recommend",
        )
    )


def test_digest_is_public_deterministic_and_consistent_with_report() -> None:
    audit_report = report(
        input_row(
            "block-case",
            probability="0.995000",
            liquidity="0.100000",
            settlement_hours="3.000000",
            conflict="0.900000",
        ),
        input_row(
            "pass-case",
            probability="0.420000",
            liquidity="0.800000",
            settlement_hours="72.000000",
            conflict="0.100000",
        ),
    )

    digest = research_probability_edge_case_audit_digest(audit_report)
    digest_payload = research_probability_edge_case_audit_digest_payload(digest)
    report_payload = research_probability_edge_case_audit_report_payload(audit_report)

    assert type(digest) is ResearchProbabilityEdgeCaseAuditPublicDigest
    assert digest.generated_at == audit_report.generated_at
    assert digest.status == audit_report.status
    assert digest.case_count == audit_report.case_count
    assert digest.reason_codes == audit_report.reason_codes
    assert digest.reason_code_counts == audit_report.reason_code_counts
    assert "rows" not in digest_payload
    assert digest_payload == research_probability_edge_case_audit_digest_payload(digest)
    for key in (
        "generated_at",
        "config_version",
        "status",
        "case_count",
        "pass_count",
        "watch_count",
        "block_count",
        "reason_codes",
        "reason_code_counts",
        "paper_only",
        "report_only",
        "readonly",
    ):
        assert digest_payload[key] == report_payload[key]


def test_manual_report_consistency_and_public_status_validation() -> None:
    audit_report = report(
        input_row(
            "pass-case",
            probability="0.420000",
            liquidity="0.800000",
            settlement_hours="72.000000",
            conflict="0.100000",
        ),
    )

    with pytest.raises(ValueError, match="status"):
        replace(audit_report, status="review")
    with pytest.raises(ValueError, match="case_count"):
        replace(audit_report, case_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            audit_report,
            reason_code_counts=(("edge_case_audit_pass", d("2.000000")),),
        )
    with pytest.raises(ValueError, match="report"):
        research_probability_edge_case_audit_report_payload(object())  # type: ignore[arg-type]


def test_module_is_report_only_and_exposes_no_io_or_execution_surface() -> None:
    import polymarket_alpha_lab.research_probability_edge_case_audit_report as module

    source = MODULE_PATH.read_text(encoding="utf-8").lower()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PROBABILITY_EDGE_CASE_AUDIT_CONFIG_VERSION",
        "ResearchProbabilityEdgeCaseAuditConfig",
        "ResearchProbabilityEdgeCaseAuditInput",
        "ResearchProbabilityEdgeCaseAuditPublicDigest",
        "ResearchProbabilityEdgeCaseAuditReport",
        "ResearchProbabilityEdgeCaseAuditRow",
        "build_research_probability_edge_case_audit_report",
        "research_probability_edge_case_audit_digest",
        "research_probability_edge_case_audit_digest_payload",
        "research_probability_edge_case_audit_report_payload",
    )
    assert DEFAULT_RESEARCH_PROBABILITY_EDGE_CASE_AUDIT_CONFIG_VERSION.endswith("-v0")
    assert all(
        field.default is True
        for public_type in (
            ResearchProbabilityEdgeCaseAuditConfig,
            ResearchProbabilityEdgeCaseAuditInput,
            ResearchProbabilityEdgeCaseAuditReport,
            ResearchProbabilityEdgeCaseAuditPublicDigest,
        )
        for field in fields(public_type)
        if field.name in {"paper_only", "report_only", "readonly"}
    )
    assert all(
        forbidden not in source
        for forbidden in (
            "requests",
            "urllib",
            "httpx",
            "aiohttp",
            "socket",
            "subprocess",
            "pathlib",
            "open(",
            "connect(",
            "execute(",
            "commit(",
            "rollback(",
            "send(",
            "submit(",
        )
    )


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(walk_values(item))
    else:
        values.append(value)
    return tuple(values)
