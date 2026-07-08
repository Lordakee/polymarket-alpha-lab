from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_team_forecast_review_rotation_report import (
    DEFAULT_RESEARCH_TEAM_FORECAST_REVIEW_ROTATION_REPORT_CONFIG_VERSION,
    FORECAST_REVIEW_ROTATION_STATUSES,
    ResearchTeamForecastReviewRotationConfig,
    ResearchTeamForecastReviewRotationInput,
    ResearchTeamForecastReviewRotationReasonCodeCount,
    ResearchTeamForecastReviewRotationReport,
    build_research_team_forecast_review_rotation_report,
    research_team_forecast_review_rotation_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 18, 30, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=20)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchTeamForecastReviewRotationConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_TEAM_FORECAST_REVIEW_ROTATION_REPORT_CONFIG_VERSION
        ),
        "max_pass_capacity_utilization_ratio": d("0.800000"),
        "max_watch_capacity_utilization_ratio": d("1.000000"),
        "min_pass_domain_expertise_score": d("0.750000"),
        "min_watch_domain_expertise_score": d("0.550000"),
        "min_pass_calibration_score": d("0.700000"),
        "min_watch_calibration_score": d("0.500000"),
        "min_pass_memory_freshness_score": d("0.700000"),
        "min_watch_memory_freshness_score": d("0.500000"),
        "max_pass_sla_pressure_score": d("0.400000"),
        "max_watch_sla_pressure_score": d("0.700000"),
    }
    values.update(overrides)
    return ResearchTeamForecastReviewRotationConfig(**values)


def rotation_input(
    public_domain_code: str = "politics",
    *,
    reviewer_capacity_count: Decimal = d("2.000000"),
    available_review_minutes: Decimal = d("360.000000"),
    pending_review_count: Decimal = d("4.000000"),
    estimated_review_minutes: Decimal = d("30.000000"),
    domain_expertise_score: Decimal = d("0.860000"),
    calibration_score: Decimal = d("0.820000"),
    memory_freshness_score: Decimal = d("0.780000"),
    sla_pressure_score: Decimal = d("0.250000"),
    observed_at: datetime = OBSERVED_AT,
    public_reason_codes: tuple[str, ...] = ("aggregate_review_ready",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamForecastReviewRotationInput:
    return ResearchTeamForecastReviewRotationInput(
        public_domain_code=public_domain_code,
        reviewer_capacity_count=reviewer_capacity_count,
        available_review_minutes=available_review_minutes,
        pending_review_count=pending_review_count,
        estimated_review_minutes=estimated_review_minutes,
        domain_expertise_score=domain_expertise_score,
        calibration_score=calibration_score,
        memory_freshness_score=memory_freshness_score,
        sla_pressure_score=sla_pressure_score,
        observed_at=observed_at,
        public_reason_codes=public_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchTeamForecastReviewRotationInput,
    cfg: ResearchTeamForecastReviewRotationConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchTeamForecastReviewRotationReport:
    return build_research_team_forecast_review_rotation_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload(value: Any) -> None:
    unsafe_fragments = (
        "event",
        "market",
        "source",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    )
    if isinstance(value, dict):
        for key, child in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in unsafe_fragments)
            walk_payload(child)
    elif isinstance(value, list):
        for child in value:
            walk_payload(child)
    elif isinstance(value, str):
        lowered_value = value.lower()
        assert not any(fragment in lowered_value for fragment in unsafe_fragments)
    else:
        assert type(value) not in (Decimal, datetime, float, int)


def test_rotation_report_scores_pass_watch_and_block_public_plan() -> None:
    digest = report(
        rotation_input(
            "macro",
            reviewer_capacity_count=d("1.000000"),
            available_review_minutes=d("120.000000"),
            pending_review_count=d("7.000000"),
            estimated_review_minutes=d("30.000000"),
            domain_expertise_score=d("0.400000"),
            calibration_score=d("0.450000"),
            memory_freshness_score=d("0.300000"),
            sla_pressure_score=d("0.850000"),
            public_reason_codes=("aggregate_macro_review_pressure",),
        ),
        rotation_input(
            "crypto",
            reviewer_capacity_count=d("2.000000"),
            available_review_minutes=d("300.000000"),
            pending_review_count=d("9.000000"),
            estimated_review_minutes=d("30.000000"),
            domain_expertise_score=d("0.650000"),
            calibration_score=d("0.600000"),
            memory_freshness_score=d("0.620000"),
            sla_pressure_score=d("0.550000"),
        ),
        rotation_input("politics"),
        generated_at=datetime(
            2026,
            7,
            8,
            13,
            30,
            tzinfo=timezone(timedelta(hours=-5)),
        ),
    )

    assert is_dataclass(digest)
    assert digest.__dataclass_params__.frozen
    assert FORECAST_REVIEW_ROTATION_STATUSES == ("pass", "watch", "block")
    assert digest.generated_at == GENERATED_AT
    assert (
        digest.config_version
        == "research-team-forecast-review-rotation-report-v1"
    )
    assert digest.rotation_plan_status == "block"
    assert digest.public_plan_label == "forecast_review_rotation_block"
    assert digest.input_count == d("3.000000")
    assert digest.row_count == d("3.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.block_count == d("1.000000")
    assert digest.total_available_review_minutes == d("780.000000")
    assert digest.total_review_load_minutes == d("600.000000")
    assert digest.total_capacity_gap_minutes == d("90.000000")
    assert digest.average_capacity_utilization_ratio == d("0.994444")
    assert digest.max_capacity_utilization_ratio == d("1.750000")
    assert digest.min_domain_expertise_score == d("0.400000")
    assert digest.min_calibration_score == d("0.450000")
    assert digest.min_memory_freshness_score == d("0.300000")
    assert digest.max_sla_pressure_score == d("0.850000")
    assert digest.max_rotation_pressure_score == d("1.000000")
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert len(digest.derived_validation_digest) == 64

    blocked, watched, passed = digest.rows
    assert tuple(row.rotation_status for row in digest.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert blocked.public_domain_code == "macro"
    assert blocked.review_load_minutes == d("210.000000")
    assert blocked.capacity_utilization_ratio == d("1.750000")
    assert blocked.capacity_gap_minutes == d("90.000000")
    assert blocked.reason_codes == (
        "aggregate_macro_review_pressure",
        "forecast_review_capacity_overloaded_block",
        "forecast_review_domain_expertise_low_block",
        "forecast_review_calibration_low_block",
        "forecast_review_memory_stale_block",
        "forecast_review_sla_pressure_high_block",
    )
    assert watched.public_domain_code == "crypto"
    assert watched.reason_codes == (
        "aggregate_review_ready",
        "forecast_review_capacity_tight_watch",
        "forecast_review_domain_expertise_thin_watch",
        "forecast_review_calibration_thin_watch",
        "forecast_review_memory_thin_watch",
        "forecast_review_sla_pressure_elevated_watch",
    )
    assert passed.public_domain_code == "politics"
    assert passed.reason_codes == (
        "aggregate_review_ready",
        "forecast_review_rotation_pass",
    )

    assert digest.reason_codes == (
        "aggregate_macro_review_pressure",
        "aggregate_review_ready",
        "forecast_review_capacity_overloaded_block",
        "forecast_review_capacity_tight_watch",
        "forecast_review_domain_expertise_low_block",
        "forecast_review_domain_expertise_thin_watch",
        "forecast_review_calibration_low_block",
        "forecast_review_calibration_thin_watch",
        "forecast_review_memory_stale_block",
        "forecast_review_memory_thin_watch",
        "forecast_review_sla_pressure_high_block",
        "forecast_review_sla_pressure_elevated_watch",
        "forecast_review_rotation_block_present",
        "forecast_review_rotation_watch_present",
    )
    assert digest.reason_code_counts[0] == (
        ResearchTeamForecastReviewRotationReasonCodeCount(
            reason_code="aggregate_macro_review_pressure",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
    )


def test_empty_rotation_plan_blocks_with_decimal_counts_and_flags() -> None:
    digest = report()

    assert digest.rotation_plan_status == "block"
    assert digest.public_plan_label == "forecast_review_rotation_block"
    assert digest.input_count == ZERO
    assert digest.row_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.block_count == ZERO
    assert digest.total_available_review_minutes == ZERO
    assert digest.total_review_load_minutes == ZERO
    assert digest.total_capacity_gap_minutes == ZERO
    assert digest.average_capacity_utilization_ratio == ZERO
    assert digest.rows == ()
    assert digest.reason_codes == ("forecast_review_rotation_empty",)
    assert digest.reason_code_counts == (
        ResearchTeamForecastReviewRotationReasonCodeCount(
            reason_code="forecast_review_rotation_empty",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )

    populated = report(rotation_input())
    for public_record in (digest, populated, *populated.rows, *populated.reason_code_counts):
        assert public_record.paper_only is True
        assert public_record.report_only is True
        assert public_record.readonly is True
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    first = report(
        rotation_input(
            "crypto",
            reviewer_capacity_count=d("2.000000"),
            available_review_minutes=d("300.000000"),
            pending_review_count=d("9.000000"),
            estimated_review_minutes=d("30.000000"),
            domain_expertise_score=d("0.650000"),
            calibration_score=d("0.600000"),
            memory_freshness_score=d("0.620000"),
            sla_pressure_score=d("0.550000"),
            observed_at=datetime(
                2026,
                7,
                8,
                7,
                55,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        rotation_input("politics"),
    )
    second = report(rotation_input("politics"), first.rows[0].to_input())

    assert first == second
    payload = research_team_forecast_review_rotation_report_payload(first)
    assert payload == research_team_forecast_review_rotation_report_payload(second)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-08T18:30:00+00:00"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T14:55:00+00:00"
    assert payload["rows"][0]["capacity_utilization_ratio"] == "0.900000"
    assert payload["reason_code_counts"][0]["count"] == "2.000000"
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    walk_payload(payload)

    tampered = replace(first, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_forecast_review_rotation_report_payload(tampered)


def test_validation_rejects_bad_inputs_and_public_identifier_leaks() -> None:
    good = rotation_input()
    digest = report(good)

    with pytest.raises(FrozenInstanceError):
        good.public_domain_code = "macro"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.rotation_plan_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="subclass"):
        type("BadConfig", (ResearchTeamForecastReviewRotationConfig,), {})
    with pytest.raises(ValueError, match="reviewer_capacity_count must be a Decimal"):
        rotation_input(reviewer_capacity_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reviewer_capacity_count must be a Decimal"):
        ResearchTeamForecastReviewRotationInput(
            public_domain_code="politics",
            reviewer_capacity_count=_DecimalSubclass("2.000000"),
            available_review_minutes=d("360.000000"),
            pending_review_count=d("4.000000"),
            estimated_review_minutes=d("30.000000"),
            domain_expertise_score=d("0.860000"),
            calibration_score=d("0.820000"),
            memory_freshness_score=d("0.780000"),
            sla_pressure_score=d("0.250000"),
            observed_at=OBSERVED_AT,
            public_reason_codes=("aggregate_review_ready",),
        )
    with pytest.raises(ValueError, match="public_domain_code must be a plain str"):
        rotation_input(public_domain_code=_StringSubclass("politics"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsafe public"):
        rotation_input(public_domain_code="market-123")
    with pytest.raises(ValueError, match="unsafe public"):
        rotation_input(public_reason_codes=("source_latency",))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        rotation_input(observed_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(good, generated_at=_DatetimeSubclass(2026, 7, 8, 18, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at cannot be after generated_at"):
        report(rotation_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="paper_only"):
        rotation_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="max_pass_capacity_utilization_ratio"):
        config(
            max_pass_capacity_utilization_ratio=d("1.100000"),
            max_watch_capacity_utilization_ratio=d("1.000000"),
        )
    with pytest.raises(ValueError, match="min_watch_domain_expertise_score"):
        config(
            min_pass_domain_expertise_score=d("0.600000"),
            min_watch_domain_expertise_score=d("0.700000"),
        )
    with pytest.raises(ValueError, match="rows"):
        replace(digest, row_count=d("2.000000"))


def test_module_has_no_durable_network_or_execution_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_forecast_review_rotation_report.py"
    )
    tree = ast.parse(module_path.read_text())
    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "psycopg",
        "psycopg2",
        "supabase",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }
    forbidden_calls = {
        "open",
        "write",
        "writelines",
        "write_text",
        "write_bytes",
        "connect",
        "request",
        "post",
        "put",
        "patch",
        "delete",
        "submit",
        "cancel",
        "replace_order",
        "sign",
        "trade",
        "buy",
        "sell",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            assert call_name not in forbidden_calls
