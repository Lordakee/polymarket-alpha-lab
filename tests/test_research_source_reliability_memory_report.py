from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_source_reliability_memory_report as api
from polymarket_alpha_lab.research_source_reliability_memory_report import (
    ResearchSourceReliabilityMemoryConfig,
    ResearchSourceReliabilityMemoryObservation,
    ResearchSourceReliabilityMemoryReport,
    ResearchSourceReliabilityMemoryRow,
    build_research_source_reliability_memory_report,
    research_source_reliability_memory_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_class: str,
    research_domain: str,
    days_ago: int,
    reliability_score: str,
    corroboration_success_rate: str,
    correction_rate: str,
    evidence_count: str,
    stale_age_seconds: str,
    *,
    reason_codes: tuple[str, ...] = (),
) -> ResearchSourceReliabilityMemoryObservation:
    return ResearchSourceReliabilityMemoryObservation(
        source_class=source_class,
        research_domain=research_domain,
        observed_at=GENERATED_AT - timedelta(days=days_ago),
        reliability_score=d(reliability_score),
        corroboration_success_rate=d(corroboration_success_rate),
        correction_rate=d(correction_rate),
        evidence_count=d(evidence_count),
        stale_age_seconds=d(stale_age_seconds),
        reason_codes=reason_codes,
    )


def config(**overrides: object) -> ResearchSourceReliabilityMemoryConfig:
    values = {
        "config_version": "research-source-reliability-memory-report-v0",
        "min_memory_points": d("3"),
        "pass_reliability_floor": d("0.700000"),
        "block_reliability_floor": d("0.500000"),
        "stale_age_watch_seconds": d("86400"),
        "stale_age_block_seconds": d("604800"),
    }
    values.update(overrides)
    return ResearchSourceReliabilityMemoryConfig(**values)


def report(
    observations: tuple[ResearchSourceReliabilityMemoryObservation, ...],
    *,
    cfg: ResearchSourceReliabilityMemoryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceReliabilityMemoryReport:
    return build_research_source_reliability_memory_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def stable_official_observations() -> tuple[ResearchSourceReliabilityMemoryObservation, ...]:
    return (
        observation("official", "elections", 10, "0.800000", "0.900000", "0.000000", "1", "3600"),
        observation("official", "elections", 5, "0.800000", "0.900000", "0.000000", "1", "7200"),
        observation("official", "elections", 0, "0.800000", "0.900000", "0.000000", "1", "1800"),
    )


def test_memory_report_rolls_up_by_class_and_domain_without_raw_source_material() -> None:
    memory_report = report(stable_official_observations())

    assert api.STATUSES == ("pass", "watch", "block")
    assert type(memory_report) is ResearchSourceReliabilityMemoryReport
    assert memory_report.status == "pass"
    assert memory_report.source_group_count == d("1")
    assert memory_report.observation_count == d("3")
    assert memory_report.pass_count == d("1")
    assert memory_report.watch_count == d("0")
    assert memory_report.block_count == d("0")
    assert memory_report.average_evidence_weight == d("0.850000")
    assert memory_report.average_research_priority_score == d("0.150000")
    assert memory_report.max_latest_stale_age_seconds == d("1800")
    assert memory_report.reason_codes == ("source_reliability_memory_pass",)
    assert memory_report.paper_only is True
    assert memory_report.report_only is True
    assert memory_report.readonly is True

    row = memory_report.rows[0]
    assert type(row) is ResearchSourceReliabilityMemoryRow
    assert row.source_class == "official"
    assert row.research_domain == "elections"
    assert row.memory_point_count == d("3")
    assert row.evidence_count == d("3")
    assert row.long_term_reliability_score == d("0.800000")
    assert row.latest_reliability_score == d("0.800000")
    assert row.corroboration_success_rate == d("0.900000")
    assert row.correction_rate == d("0.000000")
    assert row.evidence_weight == d("0.850000")
    assert row.research_priority_score == d("0.150000")
    assert row.status == "pass"

    payload = research_source_reliability_memory_report_payload(memory_report)
    encoded = json.dumps(payload, sort_keys=True)
    assert "source_name" not in encoded
    assert "source_url" not in encoded
    assert "source_ref" not in encoded
    assert "source_text" not in encoded
    assert "http://" not in encoded
    assert "https://" not in encoded
    assert "nytimes" not in encoded.lower()
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_watch_and_block_rows_are_prioritized_by_research_priority_score() -> None:
    memory_report = report(
        stable_official_observations()
        + (
            observation("community", "sports", 8, "0.600000", "0.600000", "0.100000", "1", "90000"),
            observation("community", "sports", 3, "0.600000", "0.600000", "0.100000", "1", "90000"),
            observation(
                "community",
                "sports",
                0,
                "0.600000",
                "0.600000",
                "0.100000",
                "1",
                "90000",
                reason_codes=("manual_reviewed",),
            ),
            observation("rumor", "politics", 2, "0.400000", "0.500000", "0.200000", "1", "7200"),
            observation("rumor", "politics", 0, "0.400000", "0.500000", "0.200000", "1", "7200"),
        ),
    )

    assert memory_report.status == "block"
    assert memory_report.pass_count == d("1")
    assert memory_report.watch_count == d("1")
    assert memory_report.block_count == d("1")
    assert tuple((row.source_class, row.research_domain) for row in memory_report.rows) == (
        ("rumor", "politics"),
        ("community", "sports"),
        ("official", "elections"),
    )

    block_row, watch_row, pass_row = memory_report.rows
    assert block_row.status == "block"
    assert block_row.evidence_weight == d("0.350000")
    assert block_row.research_priority_score == d("0.650000")
    assert block_row.reason_codes == (
        "insufficient_reliability_memory",
        "source_reliability_memory_block",
        "weak_long_term_reliability_block",
    )
    assert watch_row.status == "watch"
    assert watch_row.evidence_weight == d("0.550000")
    assert watch_row.research_priority_score == d("0.450000")
    assert "input_manual_reviewed" in watch_row.reason_codes
    assert "stale_source_memory_watch" in watch_row.reason_codes
    assert pass_row.status == "pass"


def test_payload_digest_is_stable_json_ready_and_rejects_tampering() -> None:
    reversed_inputs = tuple(reversed(stable_official_observations()))
    first = report(reversed_inputs)
    second = report(stable_official_observations())

    assert first.derived_validation_digest == second.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    payload = research_source_reliability_memory_report_payload(first)
    json.dumps(payload, sort_keys=True)
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["rows"][0]["evidence_weight"] == "0.850000"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="average_evidence_weight"):
        replace(first, average_evidence_weight=d("0.840000"))


def test_frozen_dataclasses_and_decimal_only_public_numbers_are_enforced() -> None:
    memory_report = report(stable_official_observations())

    with pytest.raises(FrozenInstanceError):
        memory_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        memory_report.rows[0].evidence_weight = d("0.1")  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("BadConfig", (ResearchSourceReliabilityMemoryConfig,), {})

    with pytest.raises(ValueError, match="pass_reliability_floor"):
        config(pass_reliability_floor=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_reliability_floor"):
        config(block_reliability_floor=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(stable_official_observations(), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="reliability_score"):
        ResearchSourceReliabilityMemoryObservation(
            source_class="official",
            research_domain="elections",
            observed_at=GENERATED_AT,
            reliability_score=0.8,  # type: ignore[arg-type]
            corroboration_success_rate=d("0.900000"),
            correction_rate=d("0.000000"),
            evidence_count=d("1"),
            stale_age_seconds=d("1"),
        )
    with pytest.raises(ValueError, match="evidence_count"):
        observation("official", "elections", 1, "0.8", "0.9", "0", "1.5", "1")


def test_hard_flags_public_leakage_and_execution_terms_are_rejected() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(stable_official_observations()[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report(stable_official_observations()), readonly=False)

    for value in (
        "https://example.com/raw",
        "source_ref_123",
        "source-text",
        "raw-source-name",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "execution",
        "execute",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            observation(value, "elections", 1, "0.8", "0.9", "0", "1", "1")

    with pytest.raises(ValueError, match="unsafe public"):
        observation("official", "live-market", 1, "0.8", "0.9", "0", "1", "1")
    with pytest.raises(ValueError, match="observed_at"):
        report((observation("official", "elections", -1, "0.8", "0.9", "0", "1", "1"),))
    with pytest.raises(ValueError, match="reason_codes"):
        observation(
            "official",
            "elections",
            1,
            "0.8",
            "0.9",
            "0",
            "1",
            "1",
            reason_codes=("Needs Review",),
        )


def test_owned_module_has_no_db_network_write_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_reliability_memory_report.py"
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
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "supabase",
        ".write(",
        "db_",
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
