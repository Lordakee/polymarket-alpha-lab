from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_probability_source_memory_guard_report import (
    PROBABILITY_SOURCE_MEMORY_GUARD_STATUSES,
    ResearchMarketProbabilitySourceMemoryGuardConfig,
    ResearchMarketProbabilitySourceMemoryGuardInputRow,
    ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount,
    ResearchMarketProbabilitySourceMemoryGuardReport,
    ResearchMarketProbabilitySourceMemoryGuardReportRow,
    build_research_market_probability_source_memory_guard_report,
    research_market_probability_source_memory_guard_public_payload,
    validate_research_market_probability_source_memory_guard_payload_digest,
)


GENERATED_AT = datetime(2026, 7, 9, 13, 0, tzinfo=UTC)
HEX_A = "a" * 64
HEX_B = "b" * 64
HEX_C = "c" * 64
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> ResearchMarketProbabilitySourceMemoryGuardConfig:
    values = {
        "config_version": "probability-memory-guard-v0",
        "min_pass_evidence_count": d("3.000000"),
        "min_watch_evidence_count": d("2.000000"),
        "min_pass_probability_confidence": d("0.700000"),
        "min_watch_probability_confidence": d("0.450000"),
        "min_pass_memory_quality_score": d("0.800000"),
        "min_watch_memory_quality_score": d("0.550000"),
        "max_pass_stale_evidence_ratio": d("0.100000"),
        "max_watch_stale_evidence_ratio": d("0.350000"),
    }
    values.update(overrides)
    return ResearchMarketProbabilitySourceMemoryGuardConfig(**values)


def item(
    digest: str,
    *,
    observed_at: datetime | None = None,
    evidence_count: Decimal = d("4.000000"),
    stale_evidence_count: Decimal = d("0.000000"),
    probability_confidence: Decimal = d("0.900000"),
    memory_quality_score: Decimal = d("0.920000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketProbabilitySourceMemoryGuardInputRow:
    return ResearchMarketProbabilitySourceMemoryGuardInputRow(
        item_digest=digest,
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(minutes=10)
        ),
        evidence_count=evidence_count,
        stale_evidence_count=stale_evidence_count,
        probability_confidence=probability_confidence,
        memory_quality_score=memory_quality_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchMarketProbabilitySourceMemoryGuardInputRow, ...],
    *,
    config: ResearchMarketProbabilitySourceMemoryGuardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketProbabilitySourceMemoryGuardReport:
    return build_research_market_probability_source_memory_guard_report(
        rows,
        config=config or cfg(),
        generated_at=generated_at,
    )


def test_empty_input_returns_readonly_block_report_with_valid_digest() -> None:
    guard_report = report(())
    payload = research_market_probability_source_memory_guard_public_payload(
        guard_report,
    )

    assert type(guard_report) is ResearchMarketProbabilitySourceMemoryGuardReport
    assert is_dataclass(guard_report)
    assert PROBABILITY_SOURCE_MEMORY_GUARD_STATUSES == ("pass", "watch", "block")
    assert guard_report.generated_at == GENERATED_AT
    assert guard_report.config_version == "probability-memory-guard-v0"
    assert guard_report.status == "block"
    assert guard_report.input_count == ZERO
    assert guard_report.pass_count == ZERO
    assert guard_report.watch_count == ZERO
    assert guard_report.block_count == ZERO
    assert guard_report.average_memory_readiness_score is None
    assert guard_report.min_probability_confidence == ZERO
    assert guard_report.min_memory_quality_score == ZERO
    assert guard_report.max_stale_evidence_ratio == ZERO
    assert guard_report.rows == ()
    assert guard_report.reason_codes == ("no_probability_memory_inputs",)
    assert guard_report.reason_code_counts == (
        ResearchMarketProbabilitySourceMemoryGuardReasonCodeCount(
            reason_code="no_probability_memory_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert guard_report.paper_only is True
    assert guard_report.report_only is True
    assert guard_report.readonly is True
    assert payload["validation_digest"] == guard_report.validation_digest
    assert validate_research_market_probability_source_memory_guard_payload_digest(
        payload,
    )


def test_rows_status_counts_reason_counts_and_scores_are_deterministic() -> None:
    guard_report = report(
        (
            item(
                HEX_C,
                evidence_count=d("1.000000"),
                stale_evidence_count=d("1.000000"),
                probability_confidence=d("0.300000"),
                memory_quality_score=d("0.400000"),
            ),
            item(
                HEX_A,
                reason_codes=("manual_check_complete",),
            ),
            item(
                HEX_B,
                evidence_count=d("2.000000"),
                probability_confidence=d("0.600000"),
                memory_quality_score=d("0.700000"),
            ),
        ),
    )

    assert guard_report.status == "block"
    assert guard_report.input_count == d("3.000000")
    assert guard_report.pass_count == d("1.000000")
    assert guard_report.watch_count == d("1.000000")
    assert guard_report.block_count == d("1.000000")
    assert guard_report.average_memory_readiness_score == d("0.651667")
    assert guard_report.min_probability_confidence == d("0.300000")
    assert guard_report.min_memory_quality_score == d("0.400000")
    assert guard_report.max_stale_evidence_ratio == d("1.000000")
    assert tuple(row.item_digest for row in guard_report.rows) == (HEX_C, HEX_B, HEX_A)
    assert tuple(row.status for row in guard_report.rows) == ("block", "watch", "pass")

    block_row, watch_row, pass_row = guard_report.rows
    assert type(block_row) is ResearchMarketProbabilitySourceMemoryGuardReportRow
    assert block_row.memory_readiness_score == d("0.258333")
    assert block_row.stale_evidence_ratio == d("1.000000")
    assert block_row.reason_codes == (
        "evidence_count_block",
        "memory_quality_block",
        "probability_confidence_block",
        "probability_memory_guard_block",
        "stale_evidence_ratio_block",
    )
    assert watch_row.memory_readiness_score == d("0.741667")
    assert watch_row.reason_codes == (
        "evidence_count_watch",
        "memory_quality_watch",
        "probability_confidence_watch",
        "probability_memory_guard_watch",
    )
    assert pass_row.memory_readiness_score == d("0.955000")
    assert pass_row.reason_codes == (
        "input_manual_check_complete",
        "probability_memory_guard_pass",
    )
    assert guard_report.reason_codes == (
        "evidence_count_block",
        "evidence_count_watch",
        "input_manual_check_complete",
        "memory_quality_block",
        "memory_quality_watch",
        "probability_confidence_block",
        "probability_confidence_watch",
        "probability_memory_guard_block",
        "probability_memory_guard_pass",
        "probability_memory_guard_watch",
        "stale_evidence_ratio_block",
    )
    assert tuple(
        (count.reason_code, count.count, count.row_ratio)
        for count in guard_report.reason_code_counts
    ) == (
        ("evidence_count_block", d("1.000000"), d("0.333333")),
        ("evidence_count_watch", d("1.000000"), d("0.333333")),
        ("input_manual_check_complete", d("1.000000"), d("0.333333")),
        ("memory_quality_block", d("1.000000"), d("0.333333")),
        ("memory_quality_watch", d("1.000000"), d("0.333333")),
        ("probability_confidence_block", d("1.000000"), d("0.333333")),
        ("probability_confidence_watch", d("1.000000"), d("0.333333")),
        ("probability_memory_guard_block", d("1.000000"), d("0.333333")),
        ("probability_memory_guard_pass", d("1.000000"), d("0.333333")),
        ("probability_memory_guard_watch", d("1.000000"), d("0.333333")),
        ("stale_evidence_ratio_block", d("1.000000"), d("0.333333")),
    )


def test_public_payload_is_deterministic_decimal_string_only_and_redacted() -> None:
    first = report(
        (
            item(HEX_B, reason_codes=("zeta", "alpha")),
            item(HEX_A),
        ),
    )
    second = report(
        (
            item(HEX_A),
            item(HEX_B, reason_codes=("alpha", "zeta")),
        ),
    )

    first_payload = research_market_probability_source_memory_guard_public_payload(
        first,
    )
    second_payload = research_market_probability_source_memory_guard_public_payload(
        second,
    )
    payload_without_digest = dict(first_payload)
    validation_digest = payload_without_digest.pop("validation_digest")
    encoded_body = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    encoded_payload = json.dumps(first_payload, ensure_ascii=True, sort_keys=True)

    assert first_payload == second_payload
    assert validation_digest == hashlib.sha256(
        encoded_body.encode("utf-8"),
    ).hexdigest()
    assert len(validation_digest) == 64
    assert first_payload["rows"][0]["memory_readiness_score"] == "0.955000"
    assert first_payload["rows"][0]["evidence_count"] == "4.000000"
    assert not any(
        type(value) in (int, float, Decimal) for value in _walk(first_payload)
    )
    for unsafe in (
        "candidate-secret",
        "market-secret",
        "https://example.test/private",
        "raw source text",
        "postgres://hidden",
        "private table",
        "secret-token",
    ):
        assert unsafe not in encoded_payload
    for unsafe_key in (
        "candidate",
        "raw_market",
        "source_url",
        "url",
        "text",
        "dsn",
        "table",
        "token",
    ):
        assert unsafe_key not in encoded_payload
    assert validate_research_market_probability_source_memory_guard_payload_digest(
        first_payload,
    )

    tampered = dict(first_payload)
    tampered["input_count"] = "9.000000"
    assert not validate_research_market_probability_source_memory_guard_payload_digest(
        tampered,
    )


def test_validation_rejects_non_decimal_values_times_flags_and_raw_terms() -> None:
    with pytest.raises(ValueError, match="min_pass_evidence_count"):
        cfg(min_pass_evidence_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_pass_probability_confidence"):
        cfg(min_pass_probability_confidence=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_pass_memory_quality_score"):
        cfg(min_pass_memory_quality_score=DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="min_watch_evidence_count"):
        cfg(
            min_pass_evidence_count=d("2.000000"),
            min_watch_evidence_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="config_version"):
        cfg(config_version="market-probability-guard-v0")
    with pytest.raises(ValueError, match="item_digest"):
        item(HEX_A.upper())
    with pytest.raises(ValueError, match="item_digest"):
        item("not-a-digest")
    with pytest.raises(ValueError, match="observed_at"):
        item(HEX_A, observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        item(HEX_A, observed_at=DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report((item(HEX_A),), generated_at=datetime(2026, 7, 9, 13, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((item(HEX_A, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="stale_evidence_count"):
        item(HEX_A, evidence_count=d("1.000000"), stale_evidence_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        item(HEX_A, reason_codes=("secret_token",))
    with pytest.raises(ValueError, match="paper_only"):
        item(HEX_A, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(item(HEX_A), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(cfg(), readonly=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    guard_report = report((item(HEX_A),))

    for value in (cfg(), item(HEX_A), guard_report, *guard_report.rows, *guard_report.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field_value is None:
                continue
            if field.name.endswith((
                "_count",
                "_score",
                "_confidence",
                "_ratio",
            )):
                assert type(field_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        guard_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        guard_report.rows[0].memory_quality_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(TypeError):
        class BadRow(ResearchMarketProbabilitySourceMemoryGuardReportRow):
            pass
    with pytest.raises(ValueError, match="status"):
        replace(guard_report.rows[0], status="ready")
    with pytest.raises(ValueError, match="status"):
        replace(guard_report.rows[0], status="block")
    with pytest.raises(ValueError, match="status"):
        replace(guard_report, status="watch")
    with pytest.raises(ValueError, match="validation_digest"):
        replace(guard_report, validation_digest="0" * 64)


def test_owned_module_has_no_private_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_probability_source_memory_guard_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "network",
        "wallet",
        "auth",
        "order",
        "live trading",
        "sizing",
        "recommendation",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        values.extend(value.keys())
        for item_value in value.values():
            values.extend(_walk(item_value))
    elif isinstance(value, list):
        for item_value in value:
            values.extend(_walk(item_value))
    else:
        values.append(value)
    return tuple(values)
