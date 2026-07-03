from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import get_args, get_origin

import pytest

from polymarket_alpha_lab.team_memory_source_recheck_cadence_queue_report import (
    DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_QUEUE_CONFIG_VERSION,
    TeamMemorySourceRecheckCadenceCandidate,
    TeamMemorySourceRecheckCadenceQueueConfig,
    TeamMemorySourceRecheckCadenceQueueFamilyRow,
    TeamMemorySourceRecheckCadenceQueueReasonCodeCount,
    TeamMemorySourceRecheckCadenceQueueReport,
    TeamMemorySourceRecheckCadenceQueueRow,
    build_team_memory_source_recheck_cadence_queue_report,
    team_memory_source_recheck_cadence_queue_report_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> TeamMemorySourceRecheckCadenceQueueConfig:
    values = {
        "config_version": DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_QUEUE_CONFIG_VERSION,
        "min_overdue_age_seconds": d("0.000000"),
        "max_reviewer_ack_lag_seconds": d("3600.000000"),
        "repeated_miss_threshold_count": d("2.000000"),
        "source_family_concentration_ratio": d("0.500000"),
        "source_family_concentration_min_count": d("2.000000"),
    }
    values.update(overrides)
    return TeamMemorySourceRecheckCadenceQueueConfig(**values)


def _candidate(
    source_id: str,
    source_family: str,
    *,
    team_id: str = "politics",
    recheck_due_at: datetime = GENERATED_AT,
    owner_id: str | None = "owner_alpha",
    consecutive_miss_count: Decimal = d("0.000000"),
    reviewer_ack_requested_at: datetime | None = None,
    reviewer_acknowledged_at: datetime | None = None,
    source_config_version: str = "memory-source-v0",
) -> TeamMemorySourceRecheckCadenceCandidate:
    return TeamMemorySourceRecheckCadenceCandidate(
        team_id=team_id,
        source_id=source_id,
        source_family=source_family,
        recheck_due_at=recheck_due_at,
        owner_id=owner_id,
        consecutive_miss_count=consecutive_miss_count,
        reviewer_ack_requested_at=reviewer_ack_requested_at,
        reviewer_acknowledged_at=reviewer_acknowledged_at,
        source_config_version=source_config_version,
    )


def _field_allows_decimal(annotation: object) -> bool:
    if annotation is Decimal:
        return True
    origin = get_origin(annotation)
    if origin in (tuple, list):
        return any(_field_allows_decimal(arg) for arg in get_args(annotation))
    if origin is None:
        return False
    return any(arg is type(None) or _field_allows_decimal(arg) for arg in get_args(annotation))


def test_recheck_cadence_queue_prioritizes_overdue_owner_family_misses_and_ack_lag() -> None:
    report = build_team_memory_source_recheck_cadence_queue_report(
        (
            _candidate(
                "politics_oldest",
                "polling",
                recheck_due_at=GENERATED_AT - timedelta(seconds=7200),
            ),
            _candidate(
                "politics_missing_owner",
                "polling",
                recheck_due_at=GENERATED_AT - timedelta(seconds=300),
                owner_id=None,
            ),
            _candidate(
                "politics_repeated_miss",
                "model",
                recheck_due_at=GENERATED_AT + timedelta(seconds=600),
                consecutive_miss_count=d("3.000000"),
            ),
            _candidate(
                "politics_ack_lag",
                "polling",
                recheck_due_at=GENERATED_AT + timedelta(seconds=900),
                reviewer_ack_requested_at=GENERATED_AT - timedelta(seconds=5400),
            ),
            _candidate(
                "politics_clear_future",
                "model",
                recheck_due_at=GENERATED_AT + timedelta(seconds=3600),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, TeamMemorySourceRecheckCadenceQueueReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_QUEUE_CONFIG_VERSION
    assert report.queue_status == "blocked"
    assert report.candidate_count == d("5.000000")
    assert report.queued_source_count == d("4.000000")
    assert report.blocked_source_count == d("3.000000")
    assert report.watch_source_count == d("1.000000")
    assert report.overdue_source_count == d("2.000000")
    assert report.missing_owner_count == d("1.000000")
    assert report.concentrated_family_count == d("1.000000")
    assert report.repeated_miss_count == d("1.000000")
    assert report.reviewer_ack_lag_count == d("1.000000")
    assert report.max_overdue_age_seconds == d("7200.000000")
    assert report.max_reviewer_ack_lag_seconds == d("5400.000000")
    assert report.reason_codes == (
        "team_memory_source_recheck_cadence_overdue",
        "team_memory_source_recheck_missing_owner",
        "team_memory_source_recheck_family_concentration",
        "team_memory_source_recheck_repeated_misses",
        "team_memory_source_recheck_reviewer_ack_lag",
    )
    assert report.reason_code_counts == (
        TeamMemorySourceRecheckCadenceQueueReasonCodeCount(
            reason_code="team_memory_source_recheck_cadence_overdue",
            queue_row_count=d("2.000000"),
        ),
        TeamMemorySourceRecheckCadenceQueueReasonCodeCount(
            reason_code="team_memory_source_recheck_family_concentration",
            queue_row_count=d("3.000000"),
        ),
        TeamMemorySourceRecheckCadenceQueueReasonCodeCount(
            reason_code="team_memory_source_recheck_missing_owner",
            queue_row_count=d("1.000000"),
        ),
        TeamMemorySourceRecheckCadenceQueueReasonCodeCount(
            reason_code="team_memory_source_recheck_repeated_misses",
            queue_row_count=d("1.000000"),
        ),
        TeamMemorySourceRecheckCadenceQueueReasonCodeCount(
            reason_code="team_memory_source_recheck_reviewer_ack_lag",
            queue_row_count=d("1.000000"),
        ),
    )
    assert tuple(row.source_id for row in report.queue_rows) == (
        "politics_oldest",
        "politics_missing_owner",
        "politics_ack_lag",
        "politics_repeated_miss",
    )
    assert tuple(row.priority_rank for row in report.queue_rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
        d("4.000000"),
    )
    assert report.queue_rows[0] == TeamMemorySourceRecheckCadenceQueueRow(
        team_id="politics",
        source_id="politics_oldest",
        source_family="polling",
        owner_id="owner_alpha",
        queue_status="watch",
        priority_rank=d("1.000000"),
        recheck_due_at=GENERATED_AT - timedelta(seconds=7200),
        overdue_age_seconds=d("7200.000000"),
        consecutive_miss_count=d("0.000000"),
        reviewer_ack_lag_seconds=None,
        source_family_queue_ratio=d("0.750000"),
        reason_codes=(
            "team_memory_source_recheck_cadence_overdue",
            "team_memory_source_recheck_family_concentration",
        ),
    )
    assert report.queue_rows[1].queue_status == "blocked"
    assert report.queue_rows[1].owner_id is None
    assert report.queue_rows[1].reason_codes == (
        "team_memory_source_recheck_cadence_overdue",
        "team_memory_source_recheck_missing_owner",
        "team_memory_source_recheck_family_concentration",
    )
    assert report.queue_rows[2].reviewer_ack_lag_seconds == d("5400.000000")
    assert report.queue_rows[3].reason_codes == (
        "team_memory_source_recheck_repeated_misses",
    )
    assert report.source_family_rows == (
        TeamMemorySourceRecheckCadenceQueueFamilyRow(
            source_family="model",
            queued_source_count=d("1.000000"),
            queued_source_ratio=d("0.250000"),
            team_count=d("1.000000"),
            family_status="ready",
            reason_codes=("team_memory_source_recheck_cadence_clear",),
        ),
        TeamMemorySourceRecheckCadenceQueueFamilyRow(
            source_family="polling",
            queued_source_count=d("3.000000"),
            queued_source_ratio=d("0.750000"),
            team_count=d("1.000000"),
            family_status="watch",
            reason_codes=("team_memory_source_recheck_family_concentration",),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_recheck_cadence_queue_returns_ready_empty_report() -> None:
    report = build_team_memory_source_recheck_cadence_queue_report(
        (
            _candidate(
                "clear_future",
                "model",
                recheck_due_at=GENERATED_AT + timedelta(seconds=3600),
                reviewer_ack_requested_at=GENERATED_AT - timedelta(seconds=60),
                reviewer_acknowledged_at=GENERATED_AT - timedelta(seconds=30),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.queue_status == "ready"
    assert report.candidate_count == d("1.000000")
    assert report.queued_source_count == d("0.000000")
    assert report.blocked_source_count == d("0.000000")
    assert report.watch_source_count == d("0.000000")
    assert report.overdue_source_count == d("0.000000")
    assert report.max_overdue_age_seconds is None
    assert report.max_reviewer_ack_lag_seconds is None
    assert report.queue_rows == ()
    assert report.source_family_rows == ()
    assert report.reason_code_counts == (
        TeamMemorySourceRecheckCadenceQueueReasonCodeCount(
            reason_code="team_memory_source_recheck_cadence_clear",
            queue_row_count=d("0.000000"),
        ),
    )
    assert report.reason_codes == ("team_memory_source_recheck_cadence_clear",)


def test_recheck_cadence_queue_normalizes_utc_offsets_and_acknowledged_lag() -> None:
    generated_at = datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    due_at = datetime(2026, 7, 2, 14, 30, tzinfo=timezone(timedelta(hours=2)))
    requested_at = datetime(2026, 7, 2, 12, 15, tzinfo=timezone(timedelta(hours=1)))
    acknowledged_at = datetime(2026, 7, 2, 12, 50, tzinfo=timezone(timedelta(hours=1)))

    report = build_team_memory_source_recheck_cadence_queue_report(
        (
            _candidate(
                "offset_source",
                "calendar",
                team_id="macro_rates",
                recheck_due_at=due_at,
                reviewer_ack_requested_at=requested_at,
                reviewer_acknowledged_at=acknowledged_at,
            ),
        ),
        config=_config(max_reviewer_ack_lag_seconds=d("1200.000000")),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.queue_rows[0].recheck_due_at == datetime(2026, 7, 2, 12, 30, tzinfo=UTC)
    assert report.queue_rows[0].overdue_age_seconds == d("0.000000")
    assert report.queue_rows[0].reviewer_ack_lag_seconds == d("2100.000000")
    assert report.queue_rows[0].reason_codes == (
        "team_memory_source_recheck_reviewer_ack_lag",
    )


def test_recheck_cadence_queue_payload_is_json_ready_and_has_no_floats() -> None:
    report = build_team_memory_source_recheck_cadence_queue_report(
        (
            _candidate(
                "source_alpha",
                "polling",
                recheck_due_at=GENERATED_AT - timedelta(seconds=90),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = team_memory_source_recheck_cadence_queue_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["candidate_count"] == "1.000000"
    assert payload["queue_rows"][0]["overdue_age_seconds"] == "90.000000"
    assert payload["queue_rows"][0]["source_family_queue_ratio"] == "1.000000"
    json.dumps(payload, sort_keys=True)

    def assert_no_float(value: object) -> None:
        if isinstance(value, float):
            raise AssertionError("payload contains a float")
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float(item)
        if isinstance(value, list):
            for item in value:
                assert_no_float(item)

    assert_no_float(payload)


def test_recheck_cadence_queue_validates_types_flags_and_temporal_shape() -> None:
    with pytest.raises(ValueError, match="config_version"):
        TeamMemorySourceRecheckCadenceQueueConfig(
            config_version=_StringSubclass(
                DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_QUEUE_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="min_overdue_age_seconds"):
        TeamMemorySourceRecheckCadenceQueueConfig(min_overdue_age_seconds=0)
    with pytest.raises(ValueError, match="source_family_concentration_ratio"):
        TeamMemorySourceRecheckCadenceQueueConfig(
            source_family_concentration_ratio=d("1.500000"),
        )
    with pytest.raises(ValueError, match="repeated_miss_threshold_count"):
        TeamMemorySourceRecheckCadenceQueueConfig(
            repeated_miss_threshold_count=_DecimalSubclass("2.000000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_team_memory_source_recheck_cadence_queue_report(
            (_candidate("source_alpha", "polling"),),
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="recheck_due_at"):
        _candidate("source_alpha", "polling", recheck_due_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="team_id"):
        _candidate("source_alpha", "polling", team_id="unknown")
    with pytest.raises(ValueError, match="source_id"):
        _candidate("wallet_source", "polling")
    with pytest.raises(ValueError, match="owner_id"):
        _candidate("source_alpha", "polling", owner_id="")
    with pytest.raises(ValueError, match="acknowledged"):
        _candidate(
            "source_alpha",
            "polling",
            reviewer_acknowledged_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="acknowledged"):
        _candidate(
            "source_alpha",
            "polling",
            reviewer_ack_requested_at=GENERATED_AT,
            reviewer_acknowledged_at=GENERATED_AT - timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="future"):
        build_team_memory_source_recheck_cadence_queue_report(
            (
                _candidate(
                    "source_alpha",
                    "polling",
                    reviewer_ack_requested_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        build_team_memory_source_recheck_cadence_queue_report(
            (
                _candidate("source_alpha", "polling"),
                _candidate("source_alpha", "model"),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_candidate("source_alpha", "polling"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_candidate("source_alpha", "polling"), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_candidate("source_alpha", "polling"), readonly=False)
    with pytest.raises(ValueError, match="candidates"):
        build_team_memory_source_recheck_cadence_queue_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_recheck_cadence_queue_rejects_bad_manual_report_consistency() -> None:
    row = TeamMemorySourceRecheckCadenceQueueRow(
        team_id="politics",
        source_id="source_alpha",
        source_family="polling",
        owner_id="owner_alpha",
        queue_status="watch",
        priority_rank=d("1.000000"),
        recheck_due_at=GENERATED_AT - timedelta(seconds=60),
        overdue_age_seconds=d("60.000000"),
        consecutive_miss_count=d("0.000000"),
        reviewer_ack_lag_seconds=None,
        source_family_queue_ratio=d("1.000000"),
        reason_codes=("team_memory_source_recheck_cadence_overdue",),
    )
    family_row = TeamMemorySourceRecheckCadenceQueueFamilyRow(
        source_family="polling",
        queued_source_count=d("1.000000"),
        queued_source_ratio=d("1.000000"),
        team_count=d("1.000000"),
        family_status="ready",
        reason_codes=("team_memory_source_recheck_cadence_clear",),
    )
    reason_count = TeamMemorySourceRecheckCadenceQueueReasonCodeCount(
        reason_code="team_memory_source_recheck_cadence_overdue",
        queue_row_count=d("1.000000"),
    )
    kwargs = dict(
        generated_at=GENERATED_AT,
        config_version=DEFAULT_TEAM_MEMORY_SOURCE_RECHECK_CADENCE_QUEUE_CONFIG_VERSION,
        queue_status="watch",
        candidate_count=d("1.000000"),
        queued_source_count=d("1.000000"),
        blocked_source_count=d("0.000000"),
        watch_source_count=d("1.000000"),
        overdue_source_count=d("1.000000"),
        missing_owner_count=d("0.000000"),
        concentrated_family_count=d("0.000000"),
        repeated_miss_count=d("0.000000"),
        reviewer_ack_lag_count=d("0.000000"),
        max_overdue_age_seconds=d("60.000000"),
        max_reviewer_ack_lag_seconds=None,
        queue_rows=(row,),
        source_family_rows=(family_row,),
        reason_code_counts=(reason_count,),
        reason_codes=("team_memory_source_recheck_cadence_overdue",),
    )

    assert TeamMemorySourceRecheckCadenceQueueReport(**kwargs).queue_status == "watch"

    with pytest.raises(ValueError, match="queued_source_count"):
        TeamMemorySourceRecheckCadenceQueueReport(
            **{**kwargs, "queued_source_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="queue_status"):
        TeamMemorySourceRecheckCadenceQueueReport(
            **{**kwargs, "queue_status": "ready"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        TeamMemorySourceRecheckCadenceQueueReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    TeamMemorySourceRecheckCadenceQueueReasonCodeCount(
                        reason_code="team_memory_source_recheck_cadence_overdue",
                        queue_row_count=d("2.000000"),
                    ),
                ),
            },
        )


def test_recheck_cadence_queue_dataclasses_are_frozen_and_decimal_only_metrics() -> None:
    report = build_team_memory_source_recheck_cadence_queue_report(
        (
            _candidate(
                "source_alpha",
                "polling",
                recheck_due_at=GENERATED_AT - timedelta(seconds=60),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    values = (
        _config(),
        _candidate("source_beta", "model"),
        report.queue_rows[0],
        report.source_family_rows[0],
        report.reason_code_counts[0],
        report,
    )

    for value in values:
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False

    public_values = repr(asdict(report))
    assert "60.000000" in public_values
    for dataclass_type in (
        TeamMemorySourceRecheckCadenceQueueConfig,
        TeamMemorySourceRecheckCadenceCandidate,
        TeamMemorySourceRecheckCadenceQueueRow,
        TeamMemorySourceRecheckCadenceQueueFamilyRow,
        TeamMemorySourceRecheckCadenceQueueReasonCodeCount,
        TeamMemorySourceRecheckCadenceQueueReport,
    ):
        for field in fields(dataclass_type):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_age_seconds")
                or field.name.endswith("_seconds")
                or field.name == "priority_rank"
            ):
                assert _field_allows_decimal(field.type), (dataclass_type, field.name, field.type)


def test_recheck_cadence_queue_scope_excludes_io_and_execution_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.team_memory_source_recheck_cadence_queue_report",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    lowered_source = source.lower()
    forbidden_tokens = (
        "account",
        "advice",
        "auth",
        "broker",
        "cancel",
        "exchange",
        "live",
        "network",
        "order",
        "signing",
        "submit",
        "wallet",
    )
    assert not any(token in lowered_source for token in forbidden_tokens)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
