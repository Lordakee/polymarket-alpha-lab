from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_post_settlement_calibration_queue_report import (
    DEFAULT_RESEARCH_STRATEGY_POST_SETTLEMENT_CALIBRATION_QUEUE_REPORT_CONFIG_VERSION,
    POST_SETTLEMENT_CALIBRATION_QUEUE_STATUSES,
    ResearchStrategyPostSettlementCalibrationQueueConfig,
    ResearchStrategyPostSettlementCalibrationQueueInput,
    ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount,
    ResearchStrategyPostSettlementCalibrationQueueReport,
    ResearchStrategyPostSettlementCalibrationQueueRow,
    build_research_strategy_post_settlement_calibration_queue_report,
    research_strategy_post_settlement_calibration_queue_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 13, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(hours=2)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyPostSettlementCalibrationQueueConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_POST_SETTLEMENT_CALIBRATION_QUEUE_REPORT_CONFIG_VERSION
        ),
        "min_pass_resolved_event_count": d("8.000000"),
        "min_watch_resolved_event_count": d("3.000000"),
        "max_pass_calibration_error": d("0.060000"),
        "max_watch_calibration_error": d("0.140000"),
        "min_pass_source_provenance_quality": d("0.800000"),
        "min_watch_source_provenance_quality": d("0.550000"),
        "max_pass_team_feedback_age_seconds": d("86400.000000"),
        "max_watch_team_feedback_age_seconds": d("604800.000000"),
    }
    values.update(overrides)
    return ResearchStrategyPostSettlementCalibrationQueueConfig(**values)


def input_row(
    domain_team: str = "macro",
    feedback_bucket: str = "settled_accuracy",
    *,
    resolved_event_count: Decimal = d("12.000000"),
    feedback_ready_ratio: Decimal = d("0.920000"),
    calibration_error: Decimal = d("0.030000"),
    source_provenance_quality: Decimal = d("0.880000"),
    team_feedback_age_seconds: Decimal = d("3600.000000"),
    observed_at: datetime = OBSERVED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyPostSettlementCalibrationQueueInput:
    return ResearchStrategyPostSettlementCalibrationQueueInput(
        domain_team=domain_team,
        feedback_bucket=feedback_bucket,
        resolved_event_count=resolved_event_count,
        feedback_ready_ratio=feedback_ready_ratio,
        calibration_error=calibration_error,
        source_provenance_quality=source_provenance_quality,
        team_feedback_age_seconds=team_feedback_age_seconds,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchStrategyPostSettlementCalibrationQueueInput,
    cfg: ResearchStrategyPostSettlementCalibrationQueueConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyPostSettlementCalibrationQueueReport:
    return build_research_strategy_post_settlement_calibration_queue_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected public numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)


def payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(payload_keys(item))
        return tuple(keys)
    return ()


def test_calibration_queue_aggregates_pass_watch_and_block_statuses() -> None:
    digest = report(
        input_row(
            "macro",
            "settled_accuracy",
            resolved_event_count=d("12.000000"),
            feedback_ready_ratio=d("0.920000"),
            calibration_error=d("0.030000"),
            source_provenance_quality=d("0.880000"),
            team_feedback_age_seconds=d("3600.000000"),
        ),
        input_row(
            "sports",
            "late_resolution",
            resolved_event_count=d("5.000000"),
            feedback_ready_ratio=d("0.650000"),
            calibration_error=d("0.100000"),
            source_provenance_quality=d("0.620000"),
            team_feedback_age_seconds=d("172800.000000"),
        ),
        input_row(
            "crypto",
            "source_trace",
            resolved_event_count=d("1.000000"),
            feedback_ready_ratio=d("0.300000"),
            calibration_error=d("0.220000"),
            source_provenance_quality=d("0.300000"),
            team_feedback_age_seconds=d("900000.000000"),
        ),
    )

    assert is_dataclass(digest)
    assert POST_SETTLEMENT_CALIBRATION_QUEUE_STATUSES == ("pass", "watch", "block")
    assert digest.generated_at == GENERATED_AT
    assert (
        digest.config_version
        == "research-strategy-post-settlement-calibration-queue-report-v1"
    )
    assert digest.input_count == d("3.000000")
    assert digest.calibration_queue_task_count == d("2.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.block_count == d("1.000000")
    assert digest.task_ratio == d("0.666667")
    assert digest.min_resolved_event_count == d("1.000000")
    assert digest.average_feedback_ready_ratio == d("0.623333")
    assert digest.max_calibration_error == d("0.220000")
    assert digest.min_source_provenance_quality == d("0.300000")
    assert digest.max_team_feedback_age_seconds == d("900000.000000")
    assert digest.status == "block"
    assert digest.queue_mode == "paper_calibration_queue_block"
    assert digest.reason_codes == (
        "post_settlement_calibration_queue_block",
        "resolved_event_feedback_thin_block",
        "feedback_readiness_low_block",
        "calibration_error_pressure_high_block",
        "source_provenance_quality_low_block",
        "domain_team_feedback_stale_block",
        "resolved_event_feedback_thin_watch",
        "feedback_readiness_thin_watch",
        "calibration_error_pressure_elevated_watch",
        "source_provenance_quality_thin_watch",
        "domain_team_feedback_stale_watch",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True
    assert len(digest.derived_validation_digest) == 64

    blocked, watched, passed = digest.rows
    assert tuple(row.queue_status for row in digest.rows) == ("block", "watch", "pass")
    assert blocked.domain_team == "crypto"
    assert blocked.feedback_bucket == "source_trace"
    assert blocked.reason_codes == (
        "resolved_event_feedback_thin_block",
        "feedback_readiness_low_block",
        "calibration_error_pressure_high_block",
        "source_provenance_quality_low_block",
        "domain_team_feedback_stale_block",
    )
    assert watched.reason_codes == (
        "resolved_event_feedback_thin_watch",
        "feedback_readiness_thin_watch",
        "calibration_error_pressure_elevated_watch",
        "source_provenance_quality_thin_watch",
        "domain_team_feedback_stale_watch",
    )
    assert passed.reason_codes == ("post_settlement_calibration_queue_clear",)
    assert ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount(
        reason_code="calibration_error_pressure_high_block",
        count=d("1.000000"),
        row_ratio=d("0.333333"),
    ) in digest.reason_code_counts


def test_empty_queue_is_pass_with_decimal_counts_and_hard_flags() -> None:
    digest = report()

    assert digest.input_count == ZERO
    assert digest.calibration_queue_task_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.block_count == ZERO
    assert digest.task_ratio == ZERO
    assert digest.min_resolved_event_count == ZERO
    assert digest.average_feedback_ready_ratio == ZERO
    assert digest.max_calibration_error == ZERO
    assert digest.min_source_provenance_quality == ZERO
    assert digest.max_team_feedback_age_seconds == ZERO
    assert digest.status == "pass"
    assert digest.queue_mode == "paper_calibration_monitor_only"
    assert digest.reason_codes == ("post_settlement_calibration_queue_empty",)
    assert digest.reason_code_counts == ()
    assert digest.rows == ()

    populated = report(input_row())
    for value in (digest, populated, *populated.rows, *populated.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            if item.name.endswith(("_count", "_ratio", "_error", "_quality", "_seconds")):
                assert type(item_value) is Decimal


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    first = report(
        input_row(
            "sports",
            "late_resolution",
            resolved_event_count=d("5.000000"),
            feedback_ready_ratio=d("0.650000"),
            calibration_error=d("0.100000"),
            source_provenance_quality=d("0.620000"),
            team_feedback_age_seconds=d("172800.000000"),
            observed_at=datetime(
                2026,
                7,
                8,
                5,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        input_row("macro", "settled_accuracy"),
        generated_at=datetime(
            2026,
            7,
            8,
            6,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = report(
        input_row("macro", "settled_accuracy"),
        input_row(
            "sports",
            "late_resolution",
            resolved_event_count=d("5.000000"),
            feedback_ready_ratio=d("0.650000"),
            calibration_error=d("0.100000"),
            source_provenance_quality=d("0.620000"),
            team_feedback_age_seconds=d("172800.000000"),
            observed_at=datetime(
                2026,
                7,
                8,
                5,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        generated_at=datetime(
            2026,
            7,
            8,
            6,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )

    payload = research_strategy_post_settlement_calibration_queue_report_payload(first)
    repeat_payload = research_strategy_post_settlement_calibration_queue_report_payload(
        second,
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload["generated_at"] == "2026-07-08T13:00:00+00:00"
    assert payload["input_count"] == "2.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T12:30:00+00:00"
    assert payload["rows"][0]["calibration_error"] == "0.100000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert_no_public_numeric_values(payload)
    json.dumps(payload, sort_keys=True)

    forbidden_public_fragments = (
        "candidate",
        "market",
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
    )
    assert not any(
        fragment in key.lower()
        for key in payload_keys(payload)
        for fragment in forbidden_public_fragments
    )
    rendered = json.dumps(payload, sort_keys=True).lower()
    for forbidden in forbidden_public_fragments:
        assert forbidden not in rendered
    assert "blocked" not in rendered

    tampered = dict(payload)
    tampered["pass_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_post_settlement_calibration_queue_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("2.000000"))


def test_public_payload_rejects_raw_identifiers_unsafe_flags_and_numbers() -> None:
    payload = research_strategy_post_settlement_calibration_queue_report_payload(
        report(input_row()),
    )

    for key in (
        "candidate_id",
        "market_slug",
        "raw_question",
        "source_text",
        "source_url",
        "database_dsn",
        "table_name",
        "auth_token",
        "wallet_route",
        "order_route",
        "trade_mode",
        "live_execution",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            research_strategy_post_settlement_calibration_queue_report_payload(unsafe)

    numeric = dict(payload)
    numeric["input_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        research_strategy_post_settlement_calibration_queue_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["report_only"] = False
    with pytest.raises(ValueError, match="report_only"):
        research_strategy_post_settlement_calibration_queue_report_payload(downgraded)


def test_validation_rejects_non_decimals_duplicates_bad_labels_and_time_boundaries() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        input_row(resolved_event_count=8)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        input_row(calibration_error=_DecimalSubclass("0.100000"))

    with pytest.raises(ValueError, match="generated_at"):
        report(input_row(), generated_at=datetime(2026, 7, 8, 13, 0))

    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=datetime(2026, 7, 8, 11, 0))

    with pytest.raises(ValueError, match="observed_at"):
        input_row(observed_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC))

    with pytest.raises(ValueError, match="future"):
        report(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="unique"):
        report(input_row(), input_row())

    with pytest.raises(ValueError, match="domain_team"):
        input_row("weather", "settled_accuracy")

    with pytest.raises(ValueError, match="feedback_bucket"):
        input_row("macro", "raw-source-text")

    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)

    with pytest.raises(ValueError, match="subclass"):
        type(
            "ConfigSubclass",
            (ResearchStrategyPostSettlementCalibrationQueueConfig,),
            {},
        )

    frozen = input_row()
    with pytest.raises(FrozenInstanceError):
        frozen.domain_team = "crypto"  # type: ignore[misc]


def test_materialized_row_and_report_fields_are_revalidated() -> None:
    digest = report(input_row())
    row = digest.rows[0]

    with pytest.raises(ValueError, match="queue_status"):
        ResearchStrategyPostSettlementCalibrationQueueRow(
            **{
                **row.__dict__,
                "queue_status": "block",
            },
        )

    with pytest.raises(ValueError, match="status"):
        ResearchStrategyPostSettlementCalibrationQueueReport(
            **{
                **digest.__dict__,
                "status": "block",
                "queue_mode": "paper_calibration_queue_block",
                "derived_validation_digest": "",
            },
        )


def test_module_exposes_no_db_network_wallet_auth_order_trade_live_or_sizing_surface() -> None:
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_post_settlement_calibration_queue_report.py"
    )
    tree = ast.parse(module_path.read_text())
    module_text = module_path.read_text().lower()
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }

    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_text",
        "database",
        "dsn",
        "table_name",
        "wallet",
        "auth",
        "order",
        "trade",
        "recommendation",
        "sizing",
        "buy",
        "sell",
        "live trading",
    ):
        assert forbidden not in module_text

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
