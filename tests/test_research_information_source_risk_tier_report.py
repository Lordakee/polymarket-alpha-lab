from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_information_source_risk_tier_report import (
    ResearchInformationSourceRiskTierConfig,
    ResearchInformationSourceRiskTierReasonCodeCount,
    ResearchInformationSourceRiskTierReport,
    ResearchInformationSourceRiskTierRow,
    ResearchInformationSourceRiskTierSource,
    build_research_information_source_risk_tier_report,
    research_information_source_risk_tier_report_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedSourceShape:
    source_key: str
    reliability_score: Decimal
    independence_score: Decimal
    timeliness_score: Decimal
    verifiability_score: Decimal
    rebuttal_coverage_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchInformationSourceRiskTierConfig:
    values = {
        "config_version": "research-information-source-risk-tier-report-v0",
        "pass_source_score": d("0.750000"),
        "watch_source_score": d("0.500000"),
        "block_component_floor": d("0.250000"),
        "reliability_weight": d("0.300000"),
        "independence_weight": d("0.200000"),
        "timeliness_weight": d("0.200000"),
        "verifiability_weight": d("0.200000"),
        "rebuttal_coverage_weight": d("0.100000"),
        "stale_age_seconds": d("86400"),
    }
    values.update(overrides)
    return ResearchInformationSourceRiskTierConfig(**values)


def source(
    key: str,
    *,
    reliability_score: Decimal = d("0.900000"),
    independence_score: Decimal = d("0.800000"),
    timeliness_score: Decimal = d("1.000000"),
    verifiability_score: Decimal = d("0.800000"),
    rebuttal_coverage_score: Decimal = d("0.700000"),
    observed_at: datetime | None = None,
    reason_codes: tuple[str, ...] = (),
) -> ResearchInformationSourceRiskTierSource:
    return ResearchInformationSourceRiskTierSource(
        source_key=key,
        reliability_score=reliability_score,
        independence_score=independence_score,
        timeliness_score=timeliness_score,
        verifiability_score=verifiability_score,
        rebuttal_coverage_score=rebuttal_coverage_score,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchInformationSourceRiskTierConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchInformationSourceRiskTierReport:
    return build_research_information_source_risk_tier_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_without_rows() -> None:
    risk_report = report(())

    assert type(risk_report) is ResearchInformationSourceRiskTierReport
    assert risk_report.generated_at == GENERATED_AT
    assert risk_report.config_version == "research-information-source-risk-tier-report-v0"
    assert risk_report.source_count == d("0")
    assert risk_report.pass_count == d("0")
    assert risk_report.watch_count == d("0")
    assert risk_report.block_count == d("0")
    assert risk_report.average_source_score is None
    assert risk_report.average_source_risk_score is None
    assert risk_report.status == "block"
    assert risk_report.reason_codes == ("no_information_sources",)
    assert risk_report.reason_code_counts == (
        ResearchInformationSourceRiskTierReasonCodeCount(
            reason_code="no_information_sources",
            count=d("1"),
        ),
    )
    assert risk_report.rows == ()
    assert risk_report.paper_only is True
    assert risk_report.report_only is True
    assert risk_report.readonly is True


def test_reliable_independent_timely_verifiable_sources_pass() -> None:
    risk_report = report(
        (
            source("source-b", reason_codes=("manual_reviewed",)),
            source("source-a"),
        ),
    )

    assert risk_report.status == "pass"
    assert risk_report.source_count == d("2")
    assert risk_report.pass_count == d("2")
    assert risk_report.watch_count == d("0")
    assert risk_report.block_count == d("0")
    assert risk_report.average_source_score == d("0.860000")
    assert risk_report.average_source_risk_score == d("0.140000")
    assert risk_report.reason_codes == ("information_source_risk_tier_pass",)

    row = risk_report.rows[0]
    assert type(row) is ResearchInformationSourceRiskTierRow
    assert row.source_sequence == d("1")
    assert row.reliability_score == d("0.900000")
    assert row.independence_score == d("0.800000")
    assert row.timeliness_score == d("1.000000")
    assert row.verifiability_score == d("0.800000")
    assert row.rebuttal_coverage_score == d("0.700000")
    assert row.component_floor_score == d("0.700000")
    assert row.source_score == d("0.860000")
    assert row.source_risk_score == d("0.140000")
    assert row.observed_at == GENERATED_AT - timedelta(minutes=30)
    assert row.source_age_seconds == d("1800")
    assert row.status == "pass"
    assert row.reason_codes == (
        "fresh_source_observation",
        "information_source_risk_tier_pass",
        "strong_composite_source_score",
    )


def test_watch_and_block_tiers_reflect_weak_components_and_rebuttal_coverage() -> None:
    risk_report = report(
        (
            source(
                "source-block",
                reliability_score=d("0.200000"),
                independence_score=d("0.600000"),
                timeliness_score=d("0.600000"),
                verifiability_score=d("0.600000"),
                rebuttal_coverage_score=d("0.600000"),
                observed_at=GENERATED_AT - timedelta(days=2),
            ),
            source(
                "source-watch",
                reliability_score=d("0.600000"),
                independence_score=d("0.600000"),
                timeliness_score=d("0.600000"),
                verifiability_score=d("0.600000"),
                rebuttal_coverage_score=d("0.600000"),
            ),
        ),
    )

    assert risk_report.status == "block"
    assert risk_report.pass_count == d("0")
    assert risk_report.watch_count == d("1")
    assert risk_report.block_count == d("1")
    assert risk_report.average_source_score == d("0.540000")
    assert risk_report.average_source_risk_score == d("0.460000")

    block_row, watch_row = risk_report.rows
    assert block_row.status == "block"
    assert block_row.source_score == d("0.480000")
    assert block_row.source_risk_score == d("0.520000")
    assert "critical_component_floor" in block_row.reason_codes
    assert "stale_source_observation" in block_row.reason_codes
    assert "weak_reliability_score" in block_row.reason_codes
    assert watch_row.status == "watch"
    assert watch_row.source_score == d("0.600000")
    assert watch_row.source_risk_score == d("0.400000")
    assert watch_row.reason_codes == (
        "fresh_source_observation",
        "information_source_risk_tier_watch",
        "watch_composite_source_score",
    )


def test_supplied_shape_payload_is_json_ready_and_leaks_no_raw_identifiers() -> None:
    supplied = SuppliedSourceShape(
        source_key="private-source-alpha",
        reliability_score=d("0.900000"),
        independence_score=d("0.800000"),
        timeliness_score=d("1.000000"),
        verifiability_score=d("0.800000"),
        rebuttal_coverage_score=d("0.700000"),
        observed_at=GENERATED_AT - timedelta(minutes=30),
        reason_codes=("manual_reviewed",),
    )
    risk_report = report((supplied,))

    payload = research_information_source_risk_tier_report_payload(risk_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == risk_report.payload
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["rows"][0]["source_sequence"] == "1"
    assert payload["rows"][0]["source_score"] == "0.860000"
    assert "private-source-alpha" not in encoded
    assert "source_key" not in encoded
    assert "market-" not in encoded
    assert "candidate-" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded

    forbidden_public_fragments = ("url", "text", "ref", "dsn", "table", "token")
    assert not any(fragment in encoded.lower() for fragment in forbidden_public_fragments)


def test_validation_rejects_bad_types_bad_flags_and_unsafe_identifiers() -> None:
    with pytest.raises(ValueError, match="reliability_weight"):
        config(reliability_weight=d("1.100000"))
    with pytest.raises(ValueError, match="pass_source_score"):
        config(pass_source_score=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_component_floor"):
        config(block_component_floor=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((source("source-a"),), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (source("source-a"),),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="source_key"):
        source(" market-alpha")
    with pytest.raises(ValueError, match="source_key"):
        source("market-123")
    with pytest.raises(ValueError, match="source_key"):
        source("https://example.invalid/source")
    with pytest.raises(ValueError, match="reliability_score"):
        source("source-a", reliability_score=d("1.000001"))
    with pytest.raises(ValueError, match="observed_at"):
        source("source-a", observed_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((source("source-a", observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="reason_codes"):
        source("source-a", reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="reason_codes"):
        source("source-a", reason_codes=("token_seen",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(source("source-a"), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    risk_report = report((source("source-a"),))

    with pytest.raises(FrozenInstanceError):
        risk_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        risk_report.rows[0].source_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_risk_score"):
        replace(risk_report.rows[0], source_risk_score=d("0.100000"))
    with pytest.raises(ValueError, match="source_score"):
        replace(risk_report.rows[0], status="pass", source_score=d("0.700000"))
    with pytest.raises(ValueError, match="status"):
        replace(risk_report, status="watch")


def test_owned_module_has_no_network_database_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_information_source_risk_tier_report.py"
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
        "sqlalchemy",
        "psycopg",
        "sqlite3",
        "web3",
        "wallet",
        "private_key",
        "api_key",
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
