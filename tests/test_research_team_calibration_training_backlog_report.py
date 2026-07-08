from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_calibration_training_backlog_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_calibration_training_backlog_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    report = api()
    values = {
        "config_version": "research-team-calibration-training-backlog-v0",
        "watch_calibration_drift": d("0.050000"),
        "block_calibration_drift": d("0.120000"),
        "watch_min_sample_count": d("30"),
        "block_min_sample_count": d("10"),
        "watch_evidence_miss_rate": d("0.100000"),
        "block_evidence_miss_rate": d("0.250000"),
        "watch_stale_memory_hours": d("48.000000"),
        "block_stale_memory_hours": d("168.000000"),
        "watch_min_review_capacity_hours": d("6.000000"),
        "block_min_review_capacity_hours": d("2.000000"),
    }
    values.update(overrides)
    return report.ResearchTeamCalibrationTrainingBacklogConfig(**values)


def input_row(**overrides: object):
    report = api()
    values = {
        "team_key": "macro_rates",
        "aggregate_calibration_drift": d("0.040000"),
        "sample_count": d("36"),
        "evidence_miss_rate": d("0.020000"),
        "stale_memory_hours": d("12.000000"),
        "review_capacity_hours": d("8.000000"),
    }
    values.update(overrides)
    return report.ResearchTeamCalibrationTrainingBacklogInput(**values)


def build_report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_team_calibration_training_backlog_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float(item)
    else:
        assert type(value) is not float


def test_backlog_blocks_and_watches_aggregate_training_needs() -> None:
    backlog_report = build_report(
        input_row(
            team_key="sports_soccer",
            aggregate_calibration_drift=d("-0.130000"),
            sample_count=d("8"),
            evidence_miss_rate=d("0.270000"),
            stale_memory_hours=d("170.000000"),
            review_capacity_hours=d("1.500000"),
        ),
        input_row(
            team_key="crypto_btc",
            aggregate_calibration_drift=d("0.060000"),
            sample_count=d("28"),
            evidence_miss_rate=d("0.120000"),
            stale_memory_hours=d("60.000000"),
            review_capacity_hours=d("5.000000"),
        ),
        input_row(team_key="macro_rates"),
    )

    assert is_dataclass(backlog_report)
    assert backlog_report.generated_at == GENERATED_AT
    assert backlog_report.generated_at.tzinfo is UTC
    assert backlog_report.config_version == (
        "research-team-calibration-training-backlog-v0"
    )
    assert backlog_report.status == "block"
    assert backlog_report.reason_codes == (
        "calibration_drift_block",
        "sample_count_block",
        "evidence_miss_rate_block",
        "stale_memory_block",
        "review_capacity_block",
        "calibration_drift_watch",
        "sample_count_watch",
        "evidence_miss_rate_watch",
        "stale_memory_watch",
        "review_capacity_watch",
    )
    assert backlog_report.team_count == d("3")
    assert backlog_report.backlog_item_count == d("2")
    assert backlog_report.block_count == d("1")
    assert backlog_report.watch_count == d("1")
    assert backlog_report.pass_count == d("1")
    assert backlog_report.paper_only is True
    assert backlog_report.report_only is True
    assert backlog_report.readonly is True

    blocked, watched = backlog_report.backlog_items
    assert blocked.team_key == "sports_soccer"
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "calibration_drift_block",
        "sample_count_block",
        "evidence_miss_rate_block",
        "stale_memory_block",
        "review_capacity_block",
    )
    assert blocked.priority_score == d("1.000000")
    assert blocked.paper_only is True
    assert blocked.report_only is True
    assert blocked.readonly is True

    assert watched.team_key == "crypto_btc"
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "calibration_drift_watch",
        "sample_count_watch",
        "evidence_miss_rate_watch",
        "stale_memory_watch",
        "review_capacity_watch",
    )
    assert watched.priority_score == d("0.500000")


def test_report_passes_when_no_training_backlog_items_are_needed() -> None:
    backlog_report = build_report(input_row(team_key="commodities_gold"))

    assert backlog_report.status == "pass"
    assert backlog_report.reason_codes == ("training_backlog_clear",)
    assert backlog_report.backlog_items == ()
    assert backlog_report.backlog_item_count == d("0")
    assert backlog_report.pass_count == d("1")
    assert backlog_report.watch_count == d("0")
    assert backlog_report.block_count == d("0")


def test_custom_config_drives_status_reason_codes_and_digest() -> None:
    custom = config(
        watch_calibration_drift=d("0.010000"),
        block_calibration_drift=d("0.200000"),
        watch_min_sample_count=d("50"),
        block_min_sample_count=d("5"),
        watch_evidence_miss_rate=d("0.050000"),
        block_evidence_miss_rate=d("0.500000"),
        watch_stale_memory_hours=d("10.000000"),
        block_stale_memory_hours=d("500.000000"),
        watch_min_review_capacity_hours=d("12.000000"),
        block_min_review_capacity_hours=d("1.000000"),
    )

    backlog_report = build_report(input_row(), cfg=custom)

    assert backlog_report.status == "watch"
    assert backlog_report.reason_codes == (
        "calibration_drift_watch",
        "sample_count_watch",
        "stale_memory_watch",
        "review_capacity_watch",
    )
    assert backlog_report.backlog_items[0].reason_codes == backlog_report.reason_codes


def test_payload_and_digest_are_deterministic_and_public_safe() -> None:
    report = api()
    rows = (
        input_row(
            team_key="sports_soccer",
            aggregate_calibration_drift=d("-0.130000"),
            sample_count=d("8"),
            evidence_miss_rate=d("0.270000"),
            stale_memory_hours=d("170.000000"),
            review_capacity_hours=d("1.500000"),
        ),
        input_row(
            team_key="crypto_btc",
            aggregate_calibration_drift=d("0.060000"),
            sample_count=d("28"),
            evidence_miss_rate=d("0.120000"),
            stale_memory_hours=d("60.000000"),
            review_capacity_hours=d("5.000000"),
        ),
    )
    first = build_report(
        *rows,
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )
    second = build_report(*reversed(rows))

    first_payload = report.research_team_calibration_training_backlog_report_payload(
        first,
    )
    second_payload = report.research_team_calibration_training_backlog_report_payload(
        second,
    )
    payload_text = repr(first_payload).lower()

    assert first.generated_at == GENERATED_AT
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["team_count"] == "2"
    assert first_payload["backlog_items"][0]["priority_score"] == "1.000000"
    assert len(first_payload["derived_validation_digest"]) == 64
    assert "Decimal(" not in repr(first_payload)
    assert "datetime" not in payload_text
    for unsafe in (
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
    ):
        assert unsafe not in payload_text
    assert_no_float(first_payload)


def test_public_payload_validator_rejects_raw_identifiers_and_numeric_values() -> None:
    report = api()
    payload = report.research_team_calibration_training_backlog_report_payload(
        build_report(input_row(team_key="crypto_eth", evidence_miss_rate=d("0.120000"))),
    )

    report.validate_research_team_calibration_training_backlog_public_payload(payload)
    for unsafe_payload in (
        {**payload, "event_id": "abc"},
        {**payload, "market_slug": "abc"},
        {**payload, "source_url": "abc"},
        {**payload, "team_key": "live_trade"},
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            report.validate_research_team_calibration_training_backlog_public_payload(
                unsafe_payload,
            )
    with pytest.raises(ValueError, match="Decimal-derived"):
        report.validate_research_team_calibration_training_backlog_public_payload(
            {**payload, "team_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        report.validate_research_team_calibration_training_backlog_public_payload(
            {**payload, "readonly": False},
        )


def test_dataclasses_are_frozen_and_enforce_exact_decimal_inputs() -> None:
    report = api()
    row = input_row()

    with pytest.raises(FrozenInstanceError):
        row.sample_count = d("40")  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        input_row(sample_count=30)
    with pytest.raises(ValueError, match="Decimal"):
        input_row(evidence_miss_rate=0.12)
    with pytest.raises(ValueError, match="Decimal"):
        input_row(aggregate_calibration_drift=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="integral"):
        input_row(sample_count=d("30.500000"))
    with pytest.raises(ValueError, match="timezone-aware"):
        build_report(input_row(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="datetime"):
        build_report(input_row(), generated_at=_DatetimeSubclass(2026, 7, 8, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        report.ResearchTeamCalibrationTrainingBacklogInput(
            team_key="crypto_eth",
            aggregate_calibration_drift=d("0.010000"),
            sample_count=d("30"),
            evidence_miss_rate=d("0.010000"),
            stale_memory_hours=d("1.000000"),
            review_capacity_hours=d("8.000000"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="config"):
        build_report(input_row(), cfg=object())


def test_digest_is_tamper_evident_and_statuses_are_exact() -> None:
    report = api()
    backlog_report = build_report(
        input_row(
            team_key="sports_soccer",
            aggregate_calibration_drift=d("0.130000"),
            sample_count=d("8"),
            evidence_miss_rate=d("0.270000"),
            stale_memory_hours=d("170.000000"),
            review_capacity_hours=d("1.500000"),
        ),
    )

    assert report.STATUSES == ("pass", "watch", "block")
    assert "blocked" not in report.STATUSES
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(backlog_report, derived_validation_digest="0" * 64)

    object.__setattr__(
        backlog_report.backlog_items[0],
        "priority_score",
        d("0.000000"),
    )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        report.research_team_calibration_training_backlog_report_payload(backlog_report)


def test_module_is_report_only_without_external_write_surfaces() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    calls: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

    assert not (
        imported_roots
        & {
            "requests",
            "socket",
            "subprocess",
            "psycopg",
            "psycopg2",
            "sqlalchemy",
            "sqlite3",
        }
    )
    assert not (
        calls
        & {
            "open",
            "connect",
            "request",
            "post",
            "put",
            "patch",
            "delete",
            "send",
            "run",
            "Popen",
        }
    )
