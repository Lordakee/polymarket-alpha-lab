from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_evidence_priority_queue_report import (
    DEFAULT_RESEARCH_STRATEGY_EVIDENCE_PRIORITY_QUEUE_REPORT_CONFIG_VERSION,
    ResearchStrategyEvidencePriorityQueueConfig,
    ResearchStrategyEvidencePriorityQueueGap,
    ResearchStrategyEvidencePriorityQueueReasonCodeCount,
    ResearchStrategyEvidencePriorityQueueReport,
    ResearchStrategyEvidencePriorityQueueRow,
    build_research_strategy_evidence_priority_queue_report,
    research_strategy_evidence_priority_queue_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 16, 15, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedGapShape:
    public_gap_label: str
    evidence_gap_code: str
    gap_age_hours: Decimal
    evidence_coverage_score: Decimal
    review_pressure_score: Decimal
    unresolved_review_count: Decimal
    upstream_status: str = "pass"
    upstream_reason_codes: tuple[str, ...] = ()
    market_id: str | None = None
    source_text: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyEvidencePriorityQueueConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_EVIDENCE_PRIORITY_QUEUE_REPORT_CONFIG_VERSION
        ),
        "stale_gap_age_hours": d("24.000000"),
        "block_gap_age_hours": d("72.000000"),
        "low_coverage_score": d("0.500000"),
        "watch_review_pressure": d("0.350000"),
        "block_review_pressure": d("0.700000"),
        "watch_priority_score": d("0.350000"),
        "block_priority_score": d("0.700000"),
        "unresolved_review_block_count": d("3.000000"),
        "urgency_weight": d("0.450000"),
        "review_pressure_weight": d("0.350000"),
        "coverage_gap_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchStrategyEvidencePriorityQueueConfig(**values)


def gap(
    public_gap_label: str = "alpha-public-gap",
    *,
    evidence_gap_code: str = "coverage_gap",
    gap_age_hours: Decimal = d("2.000000"),
    evidence_coverage_score: Decimal = d("0.950000"),
    review_pressure_score: Decimal = d("0.050000"),
    unresolved_review_count: Decimal = ZERO,
    upstream_status: str = "pass",
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyEvidencePriorityQueueGap:
    return ResearchStrategyEvidencePriorityQueueGap(
        public_gap_label=public_gap_label,
        evidence_gap_code=evidence_gap_code,
        gap_age_hours=gap_age_hours,
        evidence_coverage_score=evidence_coverage_score,
        review_pressure_score=review_pressure_score,
        unresolved_review_count=unresolved_review_count,
        upstream_status=upstream_status,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    gaps: tuple[object, ...],
    *,
    cfg: ResearchStrategyEvidencePriorityQueueConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyEvidencePriorityQueueReport:
    return build_research_strategy_evidence_priority_queue_report(
        gaps,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_with_report_only_digest() -> None:
    queue_report = report(())
    payload = research_strategy_evidence_priority_queue_report_payload(queue_report)

    assert type(queue_report) is ResearchStrategyEvidencePriorityQueueReport
    assert queue_report.generated_at == GENERATED_AT
    assert queue_report.config_version == (
        DEFAULT_RESEARCH_STRATEGY_EVIDENCE_PRIORITY_QUEUE_REPORT_CONFIG_VERSION
    )
    assert queue_report.status == "block"
    assert queue_report.gap_count == ZERO
    assert queue_report.pass_count == ZERO
    assert queue_report.watch_count == ZERO
    assert queue_report.block_count == ZERO
    assert queue_report.average_priority_score is None
    assert queue_report.max_priority_score is None
    assert queue_report.rows == ()
    assert queue_report.reason_codes == ("no_evidence_gaps",)
    assert queue_report.reason_code_counts == (
        ResearchStrategyEvidencePriorityQueueReasonCodeCount(
            reason_code="no_evidence_gaps",
            count=d("1.000000"),
        ),
    )
    assert queue_report.paper_only is True
    assert queue_report.report_only is True
    assert queue_report.readonly is True
    assert payload["validation_digest"] == queue_report.validation_digest
    assert queue_report.validation_digest == _expected_digest(payload)
    assert_no_float_or_int_values(payload)


def test_queue_ranks_sanitized_gaps_by_urgency_and_review_pressure() -> None:
    queue_report = report(
        (
            gap("alpha-public-gap", evidence_gap_code="complete_public_evidence"),
            gap(
                "gamma-public-gap",
                evidence_gap_code="aging_public_evidence",
                gap_age_hours=d("36.000000"),
                evidence_coverage_score=d("0.650000"),
                review_pressure_score=d("0.400000"),
                unresolved_review_count=d("1.000000"),
            ),
            gap(
                "beta-public-gap",
                evidence_gap_code="missing_public_evidence",
                gap_age_hours=d("96.000000"),
                evidence_coverage_score=d("0.200000"),
                review_pressure_score=d("0.850000"),
                unresolved_review_count=d("3.000000"),
                upstream_status="watch",
            ),
        ),
    )

    assert queue_report.status == "block"
    assert queue_report.gap_count == d("3.000000")
    assert queue_report.pass_count == d("1.000000")
    assert queue_report.watch_count == d("1.000000")
    assert queue_report.block_count == d("1.000000")
    assert queue_report.average_priority_score == d("0.453750")
    assert queue_report.max_priority_score == d("0.915000")
    assert tuple(row.public_gap_label for row in queue_report.rows) == (
        "beta-public-gap",
        "gamma-public-gap",
        "alpha-public-gap",
    )
    assert tuple(row.queue_rank for row in queue_report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in queue_report.rows) == ("block", "watch", "pass")

    blocked, watched, passing = queue_report.rows
    assert type(blocked) is ResearchStrategyEvidencePriorityQueueRow
    assert blocked.gap_age_pressure_score == d("1.000000")
    assert blocked.coverage_gap_score == d("0.800000")
    assert blocked.urgency_score == d("0.900000")
    assert blocked.review_load_score == d("1.000000")
    assert blocked.priority_score == d("0.915000")
    assert blocked.reason_codes == (
        "coverage_gap_block",
        "evidence_gap_age_block",
        "evidence_priority_block",
        "review_pressure_block",
        "upstream_status_watch",
    )
    assert watched.priority_score == d("0.401250")
    assert watched.status == "watch"
    assert "evidence_priority_watch" in watched.reason_codes
    assert passing.priority_score == d("0.045000")
    assert passing.status == "pass"
    assert passing.reason_codes == (
        "coverage_gap_low",
        "evidence_gap_age_low",
        "evidence_priority_pass",
        "review_pressure_low",
        "upstream_status_pass",
    )


def test_payload_is_deterministic_decimal_only_and_public_safe() -> None:
    first = report(
        (
            gap("zeta-public-gap", evidence_gap_code="manual_review_gap"),
            gap("alpha-public-gap", upstream_reason_codes=("fresh_public_evidence",)),
        ),
    )
    second = report(tuple(reversed(first.rows)))

    payload = research_strategy_evidence_priority_queue_report_payload(first)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == research_strategy_evidence_priority_queue_report_payload(first)
    assert payload == research_strategy_evidence_priority_queue_report_payload(second)
    assert first.validation_digest == _expected_digest(payload)
    assert tuple(row["public_gap_label"] for row in payload["rows"]) == (
        "alpha-public-gap",
        "zeta-public-gap",
    )
    assert payload["gap_count"] == "2.000000"
    assert payload["rows"][0]["queue_rank"] == "1.000000"
    assert payload["rows"][0]["validation_digest"] == first.rows[0].validation_digest
    assert first.rows[0].validation_digest == _expected_digest(payload["rows"][0])
    assert_no_float_or_int_values(payload)
    assert all(
        token not in encoded.lower()
        for token in (
            "candidate_id",
            "market_id",
            "market_slug",
            "slug",
            "question",
            "url",
            "source_text",
            "dsn",
            "table",
            "token",
            "wallet",
            "order",
            "trade",
            "buy",
            "sell",
            "recommend",
            "sizing",
        )
    )


def test_validation_rejects_bad_types_flags_statuses_and_raw_public_surfaces() -> None:
    queue_report = report((gap(),))

    with pytest.raises(FrozenInstanceError):
        queue_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        queue_report.rows[0].priority_score = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="validation_digest"):
        replace(queue_report, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="validation_digest"):
        replace(queue_report.rows[0], priority_score=d("0.999999"))
    with pytest.raises(ValueError, match="paper_only"):
        gap(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(queue_report, readonly=False)

    with pytest.raises(ValueError, match="weights"):
        config(coverage_gap_weight=d("0.300000"))
    with pytest.raises(ValueError, match="watch_priority_score"):
        config(watch_priority_score=0.35)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_priority_score"):
        config(block_priority_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((gap(),), generated_at=datetime(2026, 7, 8, 16, 15))
    with pytest.raises(ValueError, match="generated_at"):
        report((gap(),), generated_at=_DatetimeSubclass(2026, 7, 8, 16, 15, tzinfo=UTC))
    with pytest.raises(ValueError, match="upstream_status"):
        gap(upstream_status="ready")
    with pytest.raises(ValueError, match="public_gap_label"):
        gap(public_gap_label=" market-alpha")
    with pytest.raises(ValueError, match="public_gap_label"):
        gap(public_gap_label="https://example.invalid/gap")
    with pytest.raises(ValueError, match="public_gap_label"):
        gap(public_gap_label="market-slug-alpha")
    with pytest.raises(ValueError, match="evidence_gap_code"):
        gap(evidence_gap_code="Needs Review")
    with pytest.raises(ValueError, match="gap_age_hours"):
        gap(gap_age_hours=24)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_coverage_score"):
        gap(evidence_coverage_score=d("1.100000"))
    with pytest.raises(ValueError, match="review_pressure_score"):
        gap(review_pressure_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="unresolved_review_count"):
        gap(unresolved_review_count=d("1.500000"))
    with pytest.raises(ValueError, match="unsafe public"):
        report(
            (
                SuppliedGapShape(
                    public_gap_label="safe-public-gap",
                    evidence_gap_code="safe_public_gap",
                    gap_age_hours=d("1.000000"),
                    evidence_coverage_score=d("0.900000"),
                    review_pressure_score=d("0.100000"),
                    unresolved_review_count=ZERO,
                    market_id="m-123",
                ),
            ),
        )
    with pytest.raises(ValueError, match="unsafe public"):
        report(
            (
                SuppliedGapShape(
                    public_gap_label="safe-public-gap",
                    evidence_gap_code="safe_public_gap",
                    gap_age_hours=d("1.000000"),
                    evidence_coverage_score=d("0.900000"),
                    review_pressure_score=d("0.100000"),
                    unresolved_review_count=ZERO,
                    source_text="verbatim text is not public-safe",
                ),
            ),
        )


def test_owned_module_has_no_io_execution_or_decision_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_evidence_priority_queue_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "sqlite",
        "sqlalchemy",
        "database",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "sizing",
    )

    assert all(term not in source for term in forbidden_terms)


def _expected_digest(payload: dict[str, object]) -> str:
    without_digest = dict(payload)
    without_digest.pop("validation_digest")
    encoded = json.dumps(
        without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) is bool:
        return
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)
