from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_source_resolution_authority_revision_lag_report import (
    ResearchSourceResolutionAuthorityRevisionLagConfig,
    ResearchSourceResolutionAuthorityRevisionLagInput,
    ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount,
    ResearchSourceResolutionAuthorityRevisionLagReport,
    ResearchSourceResolutionAuthorityRevisionLagRow,
    STATUSES,
    build_research_source_resolution_authority_revision_lag_report,
    research_source_resolution_authority_revision_lag_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedRevisionLagShape:
    public_case_key: str
    source_revision_lag_seconds: Decimal
    authority_revision_lag_seconds: Decimal
    authority_score: Decimal
    revision_conflict_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceResolutionAuthorityRevisionLagConfig:
    values = {
        "source_revision_watch_lag_seconds": d("1800"),
        "source_revision_block_lag_seconds": d("7200"),
        "authority_revision_watch_lag_seconds": d("3600"),
        "authority_revision_block_lag_seconds": d("14400"),
        "authority_score_watch_threshold": d("0.700000"),
        "authority_score_block_threshold": d("0.500000"),
        "revision_conflict_watch_threshold": d("0.300000"),
        "revision_conflict_block_threshold": d("0.600000"),
        "watch_pressure_threshold": d("0.350000"),
        "block_pressure_threshold": d("0.700000"),
        "source_revision_lag_weight": d("0.300000"),
        "authority_revision_lag_weight": d("0.300000"),
        "authority_gap_weight": d("0.200000"),
        "revision_conflict_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchSourceResolutionAuthorityRevisionLagConfig(**values)


def lag_item(
    public_case_key: str = "case-a",
    *,
    source_revision_lag_seconds: Decimal = d("600"),
    authority_revision_lag_seconds: Decimal = d("1200"),
    authority_score: Decimal = d("0.950000"),
    revision_conflict_score: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSourceResolutionAuthorityRevisionLagInput:
    return ResearchSourceResolutionAuthorityRevisionLagInput(
        public_case_key=public_case_key,
        source_revision_lag_seconds=source_revision_lag_seconds,
        authority_revision_lag_seconds=authority_revision_lag_seconds,
        authority_score=authority_score,
        revision_conflict_score=revision_conflict_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchSourceResolutionAuthorityRevisionLagConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceResolutionAuthorityRevisionLagReport:
    return build_research_source_resolution_authority_revision_lag_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_pass_with_zero_digest_surface() -> None:
    lag_report = report(())

    assert STATUSES == ("pass", "watch", "block")
    assert type(lag_report) is ResearchSourceResolutionAuthorityRevisionLagReport
    assert is_dataclass(lag_report)
    assert lag_report.generated_at == GENERATED_AT
    assert lag_report.case_count == d("0")
    assert lag_report.pass_count == d("0")
    assert lag_report.watch_count == d("0")
    assert lag_report.block_count == d("0")
    assert lag_report.average_revision_lag_pressure is None
    assert lag_report.max_source_revision_lag_seconds == d("0")
    assert lag_report.max_authority_revision_lag_seconds == d("0")
    assert lag_report.lowest_authority_score == d("0")
    assert lag_report.highest_revision_conflict_score == d("0")
    assert lag_report.status == "pass"
    assert lag_report.reason_codes == ("no_authority_revision_lag_items",)
    assert lag_report.reason_code_counts == (
        ResearchSourceResolutionAuthorityRevisionLagReasonCodeCount(
            reason_code="no_authority_revision_lag_items",
            count=d("1"),
        ),
    )
    assert lag_report.rows == ()
    assert len(lag_report.derived_validation_digest) == 64
    int(lag_report.derived_validation_digest, 16)
    assert lag_report.paper_only is True
    assert lag_report.report_only is True
    assert lag_report.readonly is True


def test_revision_lag_report_scores_source_authority_and_conflict_pressure() -> None:
    lag_report = report(
        (
            lag_item(
                "case-c",
                source_revision_lag_seconds=d("10800"),
                authority_revision_lag_seconds=d("18000"),
                authority_score=d("0.450000"),
                revision_conflict_score=d("0.750000"),
                reason_codes=("manual_public_revision_review",),
            ),
            lag_item("case-a"),
            lag_item(
                "case-b",
                source_revision_lag_seconds=d("3600"),
                authority_revision_lag_seconds=d("7200"),
                authority_score=d("0.650000"),
                revision_conflict_score=d("0.400000"),
            ),
        ),
    )

    assert tuple(row.public_case_key for row in lag_report.rows) == (
        "case-a",
        "case-b",
        "case-c",
    )
    assert lag_report.status == "block"
    assert lag_report.case_count == d("3")
    assert lag_report.pass_count == d("1")
    assert lag_report.watch_count == d("1")
    assert lag_report.block_count == d("1")
    assert lag_report.average_revision_lag_pressure == d("0.460000")
    assert lag_report.max_source_revision_lag_seconds == d("10800")
    assert lag_report.max_authority_revision_lag_seconds == d("18000")
    assert lag_report.lowest_authority_score == d("0.450000")
    assert lag_report.highest_revision_conflict_score == d("0.750000")

    pass_row, watch_row, block_row = lag_report.rows
    assert type(pass_row) is ResearchSourceResolutionAuthorityRevisionLagRow
    assert pass_row.source_revision_lag_pressure == d("0.083333")
    assert pass_row.source_revision_lag_band == "fresh"
    assert pass_row.authority_revision_lag_pressure == d("0.083333")
    assert pass_row.authority_revision_lag_band == "fresh"
    assert pass_row.authority_gap == d("0.050000")
    assert pass_row.revision_lag_pressure == d("0.070000")
    assert pass_row.status == "pass"

    assert watch_row.source_revision_lag_pressure == d("0.500000")
    assert watch_row.source_revision_lag_band == "late"
    assert watch_row.authority_revision_lag_pressure == d("0.500000")
    assert watch_row.authority_revision_lag_band == "late"
    assert watch_row.authority_gap == d("0.350000")
    assert watch_row.revision_lag_pressure == d("0.450000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "authority_revision_lag_watch",
        "authority_score_watch",
        "revision_conflict_watch",
        "revision_lag_watch",
        "source_revision_lag_watch",
    )

    assert block_row.source_revision_lag_pressure == d("1.000000")
    assert block_row.source_revision_lag_band == "stale"
    assert block_row.authority_revision_lag_pressure == d("1.000000")
    assert block_row.authority_revision_lag_band == "stale"
    assert block_row.authority_gap == d("0.550000")
    assert block_row.revision_lag_pressure == d("0.860000")
    assert block_row.status == "block"
    assert "input_manual_public_revision_review" in block_row.reason_codes


def test_custom_pressure_thresholds_drive_row_validation() -> None:
    custom_report = report(
        (
            lag_item(
                "case-custom",
                source_revision_lag_seconds=d("7200"),
                authority_revision_lag_seconds=d("7200"),
                authority_score=d("0.500000"),
                revision_conflict_score=d("0.500000"),
            ),
        ),
        cfg=config(
            watch_pressure_threshold=d("0.350000"),
            block_pressure_threshold=d("0.600000"),
        ),
    )

    assert custom_report.status == "block"
    assert custom_report.block_count == d("1")
    assert custom_report.rows[0].revision_lag_pressure == d("0.650000")
    assert custom_report.rows[0].status == "block"
    assert "revision_lag_block" in custom_report.rows[0].reason_codes
    payload = research_source_resolution_authority_revision_lag_report_payload(
        custom_report,
    )
    assert payload["rows"][0]["revision_lag_pressure"] == "0.650000"


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    rows = (
        SuppliedRevisionLagShape(
            public_case_key="case-b",
            source_revision_lag_seconds=d("3600"),
            authority_revision_lag_seconds=d("7200"),
            authority_score=d("0.650000"),
            revision_conflict_score=d("0.400000"),
            reason_codes=("manual_public_revision_review",),
        ),
        lag_item("case-a"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_source_resolution_authority_revision_lag_report_payload(
        first_report,
    )
    second_payload = research_source_resolution_authority_revision_lag_report_payload(
        second_report,
    )
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["rows"][0]["revision_lag_pressure"] == "0.070000"
    assert first_payload["rows"][1]["authority_revision_lag_seconds"] == "7200.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert all(not isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "raw_candidate",
            "candidate_id",
            "raw_market",
            "market_id",
            "market_slug",
            "\"slug\"",
            "\"question\"",
            "source_url",
            "source_text",
            "dsn",
            "\"table\"",
            "auth_token",
            "wallet",
            "order",
            "trade",
            "live_trading",
            "sizing",
            "recommendation",
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="source_revision_lag_weight"):
        config(source_revision_lag_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_pressure_threshold"):
        config(block_pressure_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="source_revision_watch_lag_seconds"):
        config(source_revision_watch_lag_seconds=d("8000"))
    with pytest.raises(ValueError, match="authority_score_block_threshold"):
        config(authority_score_block_threshold=d("0.800000"))
    with pytest.raises(ValueError, match="source_revision_block_lag_seconds"):
        config(source_revision_block_lag_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_revision_lag_weight"):
        config(authority_revision_lag_weight=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_resolution_authority_revision_lag_report(
            (lag_item(),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_source_resolution_authority_revision_lag_report(
            (lag_item(),),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_case_key"):
        lag_item(public_case_key="case url")
    with pytest.raises(ValueError, match="public_case_key"):
        lag_item(public_case_key="market-alpha")
    with pytest.raises(ValueError, match="source_revision_lag_seconds"):
        lag_item(source_revision_lag_seconds=600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_revision_lag_seconds"):
        lag_item(authority_revision_lag_seconds=d("-1"))
    with pytest.raises(ValueError, match="authority_score"):
        lag_item(authority_score=d("1.100000"))
    with pytest.raises(ValueError, match="revision_conflict_score"):
        lag_item(revision_conflict_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        lag_item(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(lag_item(), paper_only=False)
    with pytest.raises(ValueError, match="duplicate public_case_key"):
        report((lag_item("case-a"), lag_item("case-a")))


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    lag_report = report((lag_item(),))

    with pytest.raises(FrozenInstanceError):
        lag_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        lag_report.rows[0].revision_lag_pressure = d("0")  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("BadConfig", (ResearchSourceResolutionAuthorityRevisionLagConfig,), {})
    with pytest.raises(ValueError, match="status"):
        replace(lag_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="revision_lag_pressure"):
        replace(lag_report.rows[0], revision_lag_pressure=d("0.999999"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(lag_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="case_count"):
        replace(lag_report, case_count=d("2"))


def test_owned_module_has_no_db_network_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_resolution_authority_revision_lag_report.py"
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
        "source_url",
        "source_text",
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "dsn",
        "wallet",
        "order",
        "trade",
        "live execution",
        "execute(",
        "recommendation",
        "sizing",
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
