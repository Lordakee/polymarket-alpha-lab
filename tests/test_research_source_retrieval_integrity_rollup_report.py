from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_retrieval_integrity_rollup_report import (
    ResearchSourceRetrievalIntegrityEvidence,
    ResearchSourceRetrievalIntegrityRollupConfig,
    ResearchSourceRetrievalIntegrityRollupReasonCodeCount,
    ResearchSourceRetrievalIntegrityRollupReport,
    ResearchSourceRetrievalIntegrityRollupRow,
    build_research_source_retrieval_integrity_rollup_report,
    research_source_retrieval_integrity_rollup_report_public_digest,
    research_source_retrieval_integrity_rollup_report_public_payload,
    validate_research_source_retrieval_integrity_rollup_report_public_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedRetrievalShape:
    retrieval_channel: str
    retrieved_at: datetime
    parse_confidence: Decimal
    family_quorum_count: Decimal
    contradiction_pressure: Decimal
    candidate_id: str = "candidate-raw-123"
    market_slug: str = "raw-market-slug"
    question_text: str = "Will this raw question leak?"
    raw_url: str = "https://example.test/raw"
    source_text: str = "raw page text"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceRetrievalIntegrityRollupConfig:
    values = {
        "config_version": "research-source-retrieval-integrity-rollup-report-v0",
        "fresh_retrieval_age_seconds": d("3600.000000"),
        "stale_retrieval_age_seconds": d("86400.000000"),
        "minimum_family_quorum_count": d("2.000000"),
        "pass_integrity_score": d("0.700000"),
        "watch_integrity_score": d("0.400000"),
        "watch_freshness_score": d("0.500000"),
        "block_freshness_score": d("0.250000"),
        "watch_parse_confidence": d("0.700000"),
        "block_parse_confidence": d("0.400000"),
        "watch_contradiction_pressure": d("0.350000"),
        "block_contradiction_pressure": d("0.650000"),
        "freshness_weight": d("0.300000"),
        "parse_confidence_weight": d("0.300000"),
        "family_quorum_weight": d("0.250000"),
        "contradiction_pressure_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchSourceRetrievalIntegrityRollupConfig(**values)


def evidence(
    *,
    retrieval_channel: str = "web",
    retrieved_at: datetime | None = None,
    parse_confidence: Decimal = d("0.900000"),
    family_quorum_count: Decimal = d("2.000000"),
    contradiction_pressure: Decimal = d("0.100000"),
) -> ResearchSourceRetrievalIntegrityEvidence:
    return ResearchSourceRetrievalIntegrityEvidence(
        retrieval_channel=retrieval_channel,
        retrieved_at=(
            retrieved_at if retrieved_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
        parse_confidence=parse_confidence,
        family_quorum_count=family_quorum_count,
        contradiction_pressure=contradiction_pressure,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSourceRetrievalIntegrityRollupConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceRetrievalIntegrityRollupReport:
    return build_research_source_retrieval_integrity_rollup_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_with_public_digest() -> None:
    rollup = report(())

    assert type(rollup) is ResearchSourceRetrievalIntegrityRollupReport
    assert rollup.generated_at == GENERATED_AT
    assert rollup.config_version == "research-source-retrieval-integrity-rollup-report-v0"
    assert rollup.input_count == d("0.000000")
    assert rollup.channel_count == d("0.000000")
    assert rollup.pass_count == d("0.000000")
    assert rollup.watch_count == d("0.000000")
    assert rollup.block_count == d("0.000000")
    assert rollup.integrity_score == d("0.000000")
    assert rollup.status == "block"
    assert rollup.rows == ()
    assert rollup.reason_code_counts == (
        ResearchSourceRetrievalIntegrityRollupReasonCodeCount(
            reason_code="research_source_retrieval_integrity_rollup_no_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert rollup.reason_codes == (
        "research_source_retrieval_integrity_rollup_no_inputs",
    )
    assert len(rollup.public_digest) == 64
    assert rollup.paper_only is True
    assert rollup.report_only is True
    assert rollup.readonly is True


def test_fresh_confident_quorum_supported_retrieval_channels_pass() -> None:
    rollup = report(
        (
            evidence(
                retrieval_channel="web",
                retrieved_at=GENERATED_AT - timedelta(minutes=30),
                parse_confidence=d("0.950000"),
                family_quorum_count=d("3.000000"),
                contradiction_pressure=d("0.050000"),
            ),
            evidence(
                retrieval_channel="scraping",
                retrieved_at=GENERATED_AT - timedelta(hours=2),
                parse_confidence=d("0.850000"),
                family_quorum_count=d("2.000000"),
                contradiction_pressure=d("0.150000"),
            ),
        ),
    )

    assert rollup.status == "pass"
    assert rollup.input_count == d("2.000000")
    assert rollup.channel_count == d("2.000000")
    assert rollup.pass_count == d("2.000000")
    assert rollup.watch_count == d("0.000000")
    assert rollup.block_count == d("0.000000")
    assert rollup.average_retrieval_freshness_score == d("0.958334")
    assert rollup.average_parse_confidence == d("0.900000")
    assert rollup.average_family_quorum_ratio == d("1.000000")
    assert rollup.max_contradiction_pressure == d("0.150000")
    assert rollup.integrity_score == d("0.942500")
    assert rollup.reason_codes == (
        "research_source_retrieval_integrity_rollup_pass",
    )

    scraping, web = rollup.rows
    assert type(scraping) is ResearchSourceRetrievalIntegrityRollupRow
    assert scraping.retrieval_channel == "scraping"
    assert scraping.observation_count == d("1.000000")
    assert scraping.latest_retrieval_age_seconds == d("7200.000000")
    assert scraping.retrieval_freshness_score == d("0.916667")
    assert scraping.parse_confidence == d("0.850000")
    assert scraping.family_quorum_count == d("2.000000")
    assert scraping.family_quorum_ratio == d("1.000000")
    assert scraping.contradiction_pressure == d("0.150000")
    assert scraping.integrity_score == d("0.907500")
    assert scraping.status == "pass"
    assert web.retrieval_channel == "web"
    assert web.integrity_score == d("0.977500")


def test_stale_low_parse_low_quorum_and_contradiction_pressure_block() -> None:
    rollup = report(
        (
            evidence(
                retrieval_channel="web",
                retrieved_at=GENERATED_AT - timedelta(days=2),
                parse_confidence=d("0.200000"),
                family_quorum_count=d("0.000000"),
                contradiction_pressure=d("0.900000"),
            ),
        ),
    )

    row = rollup.rows[0]
    assert rollup.status == "block"
    assert rollup.block_count == d("1.000000")
    assert rollup.integrity_score == d("0.075000")
    assert row.retrieval_freshness_score == d("0.000000")
    assert row.family_quorum_ratio == d("0.000000")
    assert row.status == "block"
    assert row.reason_codes == (
        "research_source_retrieval_integrity_rollup_contradiction_pressure_block",
        "research_source_retrieval_integrity_rollup_family_quorum_block",
        "research_source_retrieval_integrity_rollup_integrity_score_block",
        "research_source_retrieval_integrity_rollup_parse_confidence_block",
        "research_source_retrieval_integrity_rollup_retrieval_freshness_block",
    )


def test_public_payload_is_deterministic_decimal_string_only_and_sanitized() -> None:
    supplied = SuppliedRetrievalShape(
        retrieval_channel="web",
        retrieved_at=GENERATED_AT - timedelta(minutes=45),
        parse_confidence=d("0.900000"),
        family_quorum_count=d("2.000000"),
        contradiction_pressure=d("0.100000"),
    )
    rollup = report((supplied,))

    payload = research_source_retrieval_integrity_rollup_report_public_payload(rollup)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))

    assert payload["public_digest"] == (
        research_source_retrieval_integrity_rollup_report_public_digest(payload)
    )
    validate_research_source_retrieval_integrity_rollup_report_public_payload(payload)
    assert research_source_retrieval_integrity_rollup_report_public_payload(rollup) == payload
    assert payload["rows"][0]["integrity_score"] == "0.955000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(payload))
    for forbidden in (
        "candidate-raw-123",
        "raw-market-slug",
        "Will this raw question leak?",
        "https://example.test/raw",
        "raw page text",
        "candidate_id",
        "market_slug",
        "question_text",
        "raw_url",
        "source_text",
    ):
        assert forbidden not in encoded


def test_public_digest_validation_rejects_tampered_payload_or_report() -> None:
    rollup = report((evidence(),))
    payload = research_source_retrieval_integrity_rollup_report_public_payload(rollup)
    tampered = {**payload, "status": "pass" if payload["status"] != "pass" else "watch"}

    with pytest.raises(ValueError, match="public_digest"):
        validate_research_source_retrieval_integrity_rollup_report_public_payload(tampered)
    with pytest.raises(ValueError, match="public_digest"):
        replace(rollup, public_digest="0" * 64)


def test_validation_rejects_bad_types_statuses_times_flags_and_payload_surfaces() -> None:
    with pytest.raises(ValueError, match="freshness_weight"):
        config(freshness_weight=d("0.100000"))
    with pytest.raises(ValueError, match="parse_confidence_weight"):
        config(parse_confidence_weight=0.3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_contradiction_pressure"):
        config(block_contradiction_pressure=_DecimalSubclass("0.650000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((evidence(),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="retrieval_channel"):
        evidence(retrieval_channel="rss")
    with pytest.raises(ValueError, match="retrieved_at"):
        evidence(retrieved_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="parse_confidence"):
        evidence(parse_confidence=d("1.100000"))
    with pytest.raises(ValueError, match="family_quorum_count"):
        evidence(family_quorum_count=d("-1.000000"))
    with pytest.raises(ValueError, match="contradiction_pressure"):
        evidence(contradiction_pressure=d("-0.100000"))
    with pytest.raises(ValueError, match="retrieved_at"):
        report((evidence(retrieved_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(evidence(), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(report((evidence(),)), status="blocked")

    payload = research_source_retrieval_integrity_rollup_report_public_payload(
        report((evidence(),)),
    )
    unsafe_payload = {**payload, "raw_url": "https://example.test/unsafe"}
    with pytest.raises(ValueError, match="unsafe public payload"):
        validate_research_source_retrieval_integrity_rollup_report_public_payload(
            unsafe_payload,
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    rollup = report((evidence(),))

    with pytest.raises(FrozenInstanceError):
        rollup.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        rollup.rows[0].integrity_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="integrity_score"):
        replace(rollup.rows[0], integrity_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(rollup, status="watch")


def test_owned_module_has_no_io_execution_or_action_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_retrieval_integrity_rollup_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "web3",
        "pathlib",
        "open(",
        "connect(",
        "private_key",
        "credential",
    )

    assert all(term not in source for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
