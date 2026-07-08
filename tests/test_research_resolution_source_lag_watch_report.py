from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_source_lag_watch_report import (
    ResearchResolutionSourceLagWatchConfig,
    ResearchResolutionSourceLagWatchInput,
    ResearchResolutionSourceLagWatchReasonCodeCount,
    ResearchResolutionSourceLagWatchReport,
    ResearchResolutionSourceLagWatchRow,
    STATUSES,
    build_research_resolution_source_lag_watch_report,
    research_resolution_source_lag_watch_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedLagShape:
    public_case_key: str
    aggregate_source_age_seconds: Decimal
    oracle_lag_seconds: Decimal
    deadline_proximity: Decimal
    contradiction_pressure: Decimal
    reliability_memory_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionSourceLagWatchConfig:
    values = {
        "fresh_source_age_seconds": d("3600"),
        "stale_source_age_seconds": d("86400"),
        "oracle_watch_lag_seconds": d("1800"),
        "oracle_block_lag_seconds": d("14400"),
        "watch_pressure_threshold": d("0.350000"),
        "block_pressure_threshold": d("0.700000"),
        "aggregate_source_age_weight": d("0.250000"),
        "oracle_lag_weight": d("0.250000"),
        "deadline_proximity_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.200000"),
        "reliability_memory_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchResolutionSourceLagWatchConfig(**values)


def lag_item(
    public_case_key: str = "case-a",
    *,
    aggregate_source_age_seconds: Decimal = d("1800"),
    oracle_lag_seconds: Decimal = d("600"),
    deadline_proximity: Decimal = d("0.100000"),
    contradiction_pressure: Decimal = d("0.050000"),
    reliability_memory_score: Decimal = d("0.950000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchResolutionSourceLagWatchInput:
    return ResearchResolutionSourceLagWatchInput(
        public_case_key=public_case_key,
        aggregate_source_age_seconds=aggregate_source_age_seconds,
        oracle_lag_seconds=oracle_lag_seconds,
        deadline_proximity=deadline_proximity,
        contradiction_pressure=contradiction_pressure,
        reliability_memory_score=reliability_memory_score,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchResolutionSourceLagWatchConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionSourceLagWatchReport:
    return build_research_resolution_source_lag_watch_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_pass_with_zero_digest_surface() -> None:
    lag_report = report(())

    assert STATUSES == ("pass", "watch", "block")
    assert type(lag_report) is ResearchResolutionSourceLagWatchReport
    assert lag_report.generated_at == GENERATED_AT
    assert lag_report.case_count == d("0")
    assert lag_report.pass_count == d("0")
    assert lag_report.watch_count == d("0")
    assert lag_report.block_count == d("0")
    assert lag_report.average_lag_pressure is None
    assert lag_report.max_aggregate_source_age_seconds == d("0")
    assert lag_report.max_oracle_lag_seconds == d("0")
    assert lag_report.status == "pass"
    assert lag_report.reason_codes == ("no_resolution_source_lag_items",)
    assert lag_report.reason_code_counts == (
        ResearchResolutionSourceLagWatchReasonCodeCount(
            reason_code="no_resolution_source_lag_items",
            count=d("1"),
        ),
    )
    assert lag_report.rows == ()
    assert len(lag_report.derived_validation_digest) == 64
    assert lag_report.paper_only is True
    assert lag_report.report_only is True
    assert lag_report.readonly is True


def test_lag_watch_uses_source_age_oracle_deadline_contradiction_and_memory() -> None:
    lag_report = report(
        (
            lag_item(
                "case-c",
                aggregate_source_age_seconds=d("172800"),
                oracle_lag_seconds=d("28800"),
                deadline_proximity=d("0.900000"),
                contradiction_pressure=d("0.800000"),
                reliability_memory_score=d("0.300000"),
                reason_codes=("public_deadline_manual_check",),
            ),
            lag_item("case-a"),
            lag_item(
                "case-b",
                aggregate_source_age_seconds=d("43200"),
                oracle_lag_seconds=d("7200"),
                deadline_proximity=d("0.400000"),
                contradiction_pressure=d("0.350000"),
                reliability_memory_score=d("0.700000"),
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
    assert lag_report.average_lag_pressure == d("0.461806")
    assert lag_report.max_aggregate_source_age_seconds == d("172800")
    assert lag_report.max_oracle_lag_seconds == d("28800")

    pass_row, watch_row, block_row = lag_report.rows
    assert type(pass_row) is ResearchResolutionSourceLagWatchRow
    assert pass_row.aggregate_source_age_pressure == d("0.000000")
    assert pass_row.oracle_lag_pressure == d("0.041667")
    assert pass_row.reliability_memory_gap == d("0.050000")
    assert pass_row.lag_pressure == d("0.045417")
    assert pass_row.status == "pass"

    assert watch_row.aggregate_source_age_pressure == d("0.500000")
    assert watch_row.oracle_lag_pressure == d("0.500000")
    assert watch_row.reliability_memory_gap == d("0.300000")
    assert watch_row.lag_pressure == d("0.430000")
    assert watch_row.status == "watch"

    assert block_row.aggregate_source_age_pressure == d("1.000000")
    assert block_row.oracle_lag_pressure == d("1.000000")
    assert block_row.reliability_memory_gap == d("0.700000")
    assert block_row.lag_pressure == d("0.910000")
    assert block_row.status == "block"
    assert "input_public_deadline_manual_check" in block_row.reason_codes
    assert lag_report.reason_code_counts == tuple(
        sorted(lag_report.reason_code_counts, key=lambda item: item.reason_code),
    )


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    rows = (
        SuppliedLagShape(
            public_case_key="case-b",
            aggregate_source_age_seconds=d("43200"),
            oracle_lag_seconds=d("7200"),
            deadline_proximity=d("0.400000"),
            contradiction_pressure=d("0.350000"),
            reliability_memory_score=d("0.700000"),
            reason_codes=("manual_public_review",),
        ),
        lag_item("case-a"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_resolution_source_lag_watch_report_payload(first_report)
    second_payload = research_resolution_source_lag_watch_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["lag_pressure"] == "0.045417"
    assert first_payload["rows"][1]["oracle_lag_seconds"] == "7200.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert all(not isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "http",
            "source_url",
            "source_text",
            "source_ref",
            "raw_source",
            "market_slug",
            "market_id",
            "condition_id",
            "wallet",
            "auth",
            "order",
            "trade",
            "recommendation",
            "sizing",
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="aggregate_source_age_weight"):
        config(aggregate_source_age_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_pressure_threshold"):
        config(block_pressure_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="oracle_watch_lag_seconds"):
        config(oracle_watch_lag_seconds=d("20000"))
    with pytest.raises(ValueError, match="fresh_source_age_seconds"):
        config(fresh_source_age_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="oracle_lag_weight"):
        config(oracle_lag_weight=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_resolution_source_lag_watch_report(
            (lag_item(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_resolution_source_lag_watch_report(
            (lag_item(),),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_case_key"):
        lag_item(public_case_key="case url")
    with pytest.raises(ValueError, match="public_case_key"):
        lag_item(public_case_key="market-alpha")
    with pytest.raises(ValueError, match="aggregate_source_age_seconds"):
        lag_item(aggregate_source_age_seconds=1800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="oracle_lag_seconds"):
        lag_item(oracle_lag_seconds=d("-1"))
    with pytest.raises(ValueError, match="deadline_proximity"):
        lag_item(deadline_proximity=d("1.100000"))
    with pytest.raises(ValueError, match="contradiction_pressure"):
        lag_item(contradiction_pressure=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        lag_item(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(lag_item(), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    lag_report = report((lag_item(),))

    with pytest.raises(FrozenInstanceError):
        lag_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        lag_report.rows[0].lag_pressure = d("0")  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("BadConfig", (ResearchResolutionSourceLagWatchConfig,), {})
    with pytest.raises(ValueError, match="status"):
        replace(lag_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="lag_pressure"):
        replace(lag_report.rows[0], lag_pressure=d("0.999999"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(lag_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="case_count"):
        replace(lag_report, case_count=d("2"))


def test_owned_module_has_no_db_network_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_resolution_source_lag_watch_report.py"
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
        "wallet",
        "auth",
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
