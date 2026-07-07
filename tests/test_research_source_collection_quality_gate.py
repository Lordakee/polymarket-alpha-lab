from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_collection_quality_gate import (
    ResearchSourceCollectionItem,
    ResearchSourceCollectionQualityGateConfig,
    ResearchSourceCollectionQualityGateReasonCodeCount,
    ResearchSourceCollectionQualityGateReport,
    ResearchSourceCollectionQualityGateRow,
    ResearchSourceCollectionQualityPublicPayloadItem,
    build_research_source_collection_quality_gate_report,
    research_source_collection_quality_gate_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedSourceShape:
    collection_id: str
    claim_id: str
    source_id: str
    source_family: str
    source_kind: str
    stance: str
    collected_at: datetime
    verification_status: str
    counterevidence_checked: bool
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceCollectionQualityGateConfig:
    values = {
        "config_version": "research-source-collection-quality-gate-v0",
        "fresh_age_seconds": d("3600"),
        "stale_age_seconds": d("86400"),
        "min_source_count": d("2"),
        "min_source_family_count": d("2"),
        "min_counterevidence_check_count": d("1"),
        "pass_quality_score": d("0.750000"),
        "watch_quality_score": d("0.450000"),
        "independence_weight": d("0.300000"),
        "timeliness_weight": d("0.250000"),
        "verifiability_weight": d("0.250000"),
        "counterevidence_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchSourceCollectionQualityGateConfig(**values)


def source(
    index: int,
    *,
    collection_id: str = "collection-alpha",
    claim_id: str = "claim-alpha",
    source_family: str = "official",
    source_kind: str = "official",
    stance: str = "supports",
    collected_at: datetime | None = None,
    verification_status: str = "verified",
    counterevidence_checked: bool = True,
    reason_codes: tuple[str, ...] = (),
) -> ResearchSourceCollectionItem:
    return ResearchSourceCollectionItem(
        collection_id=collection_id,
        claim_id=claim_id,
        source_id=f"source-{index:03d}",
        source_family=source_family,
        source_kind=source_kind,
        stance=stance,
        collected_at=(
            collected_at if collected_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
        verification_status=verification_status,
        counterevidence_checked=counterevidence_checked,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSourceCollectionQualityGateConfig | None = None,
    generated_at: datetime = GENERATED_AT,
    public_payload: tuple[object, ...] = (),
) -> ResearchSourceCollectionQualityGateReport:
    return build_research_source_collection_quality_gate_report(
        rows,
        generated_at=generated_at,
        config=cfg or config(),
        public_payload=public_payload,
    )


def test_empty_input_returns_blocked_report_only_gate() -> None:
    gate_report = report(())

    assert type(gate_report) is ResearchSourceCollectionQualityGateReport
    assert gate_report.generated_at == GENERATED_AT
    assert gate_report.config_version == "research-source-collection-quality-gate-v0"
    assert gate_report.gate_status == "blocked"
    assert gate_report.status == "blocked"
    assert gate_report.collection_count == d("0")
    assert gate_report.pass_count == d("0")
    assert gate_report.watch_count == d("0")
    assert gate_report.blocked_count == d("0")
    assert gate_report.average_quality_score is None
    assert gate_report.rows == ()
    assert gate_report.reason_codes == ("no_source_collection_results",)
    assert gate_report.reason_code_counts == (
        ResearchSourceCollectionQualityGateReasonCodeCount(
            reason_code="no_source_collection_results",
            count=d("1"),
        ),
    )
    assert gate_report.paper_only is True
    assert gate_report.report_only is True
    assert gate_report.readonly is True


def test_independent_timely_verifiable_counterevidence_sources_pass() -> None:
    gate_report = report(
        (
            source(
                2,
                source_family="venue",
                source_kind="primary",
                collected_at=GENERATED_AT - timedelta(hours=2),
                reason_codes=("manual_reviewed",),
            ),
            source(
                3,
                source_family="analysis",
                source_kind="analysis",
                stance="context",
                collected_at=GENERATED_AT - timedelta(hours=3),
            ),
            source(
                1,
                source_family="official",
                collected_at=GENERATED_AT - timedelta(minutes=30),
            ),
        ),
        public_payload=(
            ResearchSourceCollectionQualityPublicPayloadItem(
                payload_id="payload-001",
                collection_id="collection-alpha",
                claim_id="claim-alpha",
                public_summary="Independent source collection passed quality gate",
                reason_codes=("summary_checked",),
            ),
        ),
    )

    assert gate_report.gate_status == "pass"
    assert gate_report.collection_count == d("1")
    assert gate_report.pass_count == d("1")
    assert gate_report.watch_count == d("0")
    assert gate_report.blocked_count == d("0")
    assert gate_report.average_quality_score == d("0.982639")
    assert gate_report.reason_codes == ("research_source_collection_quality_pass",)

    row = gate_report.rows[0]
    assert type(row) is ResearchSourceCollectionQualityGateRow
    assert row.collection_id == "collection-alpha"
    assert row.claim_id == "claim-alpha"
    assert row.source_count == d("3")
    assert row.source_family_count == d("3")
    assert row.verifiable_source_count == d("3")
    assert row.counterevidence_checked_count == d("3")
    assert row.stale_source_count == d("0")
    assert row.unverified_source_count == d("0")
    assert row.latest_collected_at == GENERATED_AT - timedelta(minutes=30)
    assert row.latest_source_age_seconds == d("1800")
    assert row.independence_score == d("1.000000")
    assert row.timeliness_score == d("0.930556")
    assert row.verifiability_score == d("1.000000")
    assert row.counterevidence_score == d("1.000000")
    assert row.quality_score == d("0.982639")
    assert row.gate_status == "pass"
    assert row.status == "pass"
    assert row.source_ids == ("source-001", "source-002", "source-003")
    assert row.source_families == ("analysis", "official", "venue")
    assert row.reason_codes == (
        "all_sources_verifiable",
        "counterevidence_coverage_met",
        "fresh_collection",
        "independent_sources_met",
        "input_manual_reviewed",
        "research_source_collection_quality_pass",
        "verifiable_sources_present",
    )


def test_missing_independence_verifiability_and_counterevidence_block() -> None:
    gate_report = report(
        (
            source(
                1,
                collection_id="collection-risk",
                claim_id="claim-risk",
                source_family="same_family",
                source_kind="secondary",
                stance="supports",
                collected_at=GENERATED_AT - timedelta(days=2),
                verification_status="unverified",
                counterevidence_checked=False,
                reason_codes=("needs_review",),
            ),
        ),
    )

    row = gate_report.rows[0]
    assert gate_report.gate_status == "blocked"
    assert gate_report.blocked_count == d("1")
    assert gate_report.average_quality_score == d("0.150000")
    assert row.source_count == d("1")
    assert row.source_family_count == d("1")
    assert row.verifiable_source_count == d("0")
    assert row.counterevidence_checked_count == d("0")
    assert row.stale_source_count == d("1")
    assert row.unverified_source_count == d("1")
    assert row.independence_score == d("0.500000")
    assert row.timeliness_score == d("0.000000")
    assert row.verifiability_score == d("0.000000")
    assert row.counterevidence_score == d("0.000000")
    assert row.quality_score == d("0.150000")
    assert row.gate_status == "blocked"
    assert row.reason_codes == (
        "input_needs_review",
        "insufficient_source_independence",
        "missing_counterevidence_coverage",
        "missing_verifiable_sources",
        "research_source_collection_quality_blocked",
        "stale_collection",
        "unverified_sources_present",
    )


def test_rows_reason_counts_and_payload_are_deterministic_without_floats() -> None:
    gate_report = report(
        (
            source(
                3,
                collection_id="z-collection",
                claim_id="claim-z",
                source_family="official",
                verification_status="partially_verified",
                reason_codes=("zeta", "alpha"),
            ),
            SuppliedSourceShape(
                collection_id="a-collection",
                claim_id="claim-a",
                source_id="shape-source",
                source_family="official",
                source_kind="official",
                stance="supports",
                collected_at=GENERATED_AT - timedelta(minutes=30),
                verification_status="verified",
                counterevidence_checked=True,
            ),
            source(
                2,
                collection_id="z-collection",
                claim_id="claim-z",
                source_family="analysis",
                source_kind="analysis",
                stance="contradicts",
                verification_status="verified",
            ),
        ),
    )

    payload = research_source_collection_quality_gate_report_payload(gate_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.collection_id for row in gate_report.rows) == (
        "a-collection",
        "z-collection",
    )
    assert tuple(
        (count.reason_code, count.count)
        for count in gate_report.reason_code_counts
        if count.reason_code.startswith("input_")
    ) == (("input_alpha", d("1")), ("input_zeta", d("1")))
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][1]["quality_score"] == str(gate_report.rows[1].quality_score)
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded


def test_validation_rejects_bad_types_enums_future_times_flags_and_payloads() -> None:
    with pytest.raises(ValueError, match="independence_weight"):
        config(independence_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_quality_score"):
        config(pass_quality_score=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_quality_score"):
        config(watch_quality_score=_DecimalSubclass("0.450000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((source(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (source(1),),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_id"):
        ResearchSourceCollectionItem(
            collection_id="collection-alpha",
            claim_id="claim-alpha",
            source_id="https://unsafe.example/source",
            source_family="official",
            source_kind="official",
            stance="supports",
            collected_at=GENERATED_AT,
            verification_status="verified",
            counterevidence_checked=True,
        )
    with pytest.raises(ValueError, match="source_kind"):
        source(1, source_kind="feed")
    with pytest.raises(ValueError, match="stance"):
        source(1, stance="unknown")
    with pytest.raises(ValueError, match="verification_status"):
        source(1, verification_status="unchecked")
    with pytest.raises(ValueError, match="collected_at"):
        source(1, collected_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="collected_at"):
        report((source(1, collected_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="counterevidence_checked"):
        replace(source(1), counterevidence_checked=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        source(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(source(1), paper_only=False)
    with pytest.raises(ValueError, match="public_summary"):
        ResearchSourceCollectionQualityPublicPayloadItem(
            payload_id="payload-001",
            collection_id="collection-alpha",
            claim_id="claim-alpha",
            public_summary="see https://unsafe.example",
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    gate_report = report((source(1), source(2, source_family="analysis")))

    with pytest.raises(FrozenInstanceError):
        gate_report.gate_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        gate_report.rows[0].quality_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_ids"):
        replace(gate_report.rows[0], source_ids=("source-001",))
    with pytest.raises(ValueError, match="gate_status"):
        replace(gate_report, gate_status="blocked")


def test_owned_module_has_no_network_filesystem_db_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_collection_quality_gate.py"
    )
    source_text = module_path.read_text(encoding="utf-8").lower()
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
        "psycopg",
        "sqlalchemy",
        "ccxt",
        "web3",
        "trade(",
        "place_order",
    )

    assert all(term not in source_text for term in forbidden_terms)


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
