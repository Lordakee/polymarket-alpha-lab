from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 16, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_source_ack_recheck_status_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    values = {}
    values.update(overrides)
    return module.ResearchPacketSourceAckRecheckStatusConfig(**values)


def _recheck(
    recheck_id: str,
    *,
    acknowledgement_id: str | None = None,
    packet_id: str | None = None,
    source_id: str | None = None,
    source_family: str = "official",
    team_id: str = "politics",
    category_id: str = "politics",
    requested_at: datetime = datetime(2026, 7, 2, 13, 0, tzinfo=UTC),
    due_at: datetime = datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
    started_at: datetime | None = None,
    cleared_at: datetime | None = None,
    blocked_at: datetime | None = None,
    blocked_reason_code: str | None = None,
):
    module = api()
    suffix = recheck_id.replace("recheck-", "")
    return module.ResearchPacketSourceAckRecheckStatusInput(
        recheck_id=recheck_id,
        acknowledgement_id=acknowledgement_id or f"ack-{suffix}",
        packet_id=packet_id or f"packet-{suffix}",
        source_id=source_id or f"source-{suffix}",
        source_family=source_family,
        team_id=team_id,
        category_id=category_id,
        requested_at=requested_at,
        due_at=due_at,
        started_at=started_at,
        cleared_at=cleared_at,
        blocked_at=blocked_at,
        blocked_reason_code=blocked_reason_code,
    )


def _build_report(*rechecks, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_packet_source_ack_recheck_status_report(
        rechecks,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_status_report_rolls_up_rechecks_by_team_category_and_source_family() -> None:
    report = _build_report(
        _recheck(
            "recheck-clear",
            source_family="proxy",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            requested_at=datetime(2026, 7, 2, 13, 30, tzinfo=UTC),
            due_at=datetime(2026, 7, 2, 15, 30, tzinfo=UTC),
            started_at=datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
            cleared_at=datetime(2026, 7, 2, 15, 20, tzinfo=UTC),
        ),
        _recheck(
            "recheck-in-progress",
            source_family="proxy",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            requested_at=datetime(2026, 7, 2, 15, 0, tzinfo=UTC),
            due_at=datetime(2026, 7, 2, 17, 0, tzinfo=UTC),
            started_at=datetime(2026, 7, 2, 15, 10, tzinfo=UTC),
        ),
        _recheck(
            "recheck-overdue",
            requested_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            due_at=datetime(2026, 7, 2, 14, 30, tzinfo=UTC),
        ),
        _recheck(
            "recheck-blocked",
            requested_at=datetime(2026, 7, 2, 13, 0, tzinfo=UTC),
            due_at=datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
            started_at=datetime(2026, 7, 2, 13, 5, tzinfo=UTC),
            blocked_at=datetime(2026, 7, 2, 15, 0, tzinfo=UTC),
            blocked_reason_code="source_ack_recheck_blocked_owner_missing",
        ),
    )

    assert is_dataclass(report)
    assert report.status == "blocked"
    assert report.reason_codes == (
        "source_ack_recheck_status_blocked",
        "source_ack_recheck_status_overdue",
        "source_ack_recheck_status_in_progress",
        "source_ack_recheck_blocked_owner_missing",
    )
    assert report.recheck_count == d("4")
    assert report.summary_row_count == d("2")
    assert report.overdue_count == d("1")
    assert report.in_progress_count == d("1")
    assert report.blocked_count == d("1")
    assert report.cleared_count == d("1")
    assert report.overdue_ratio == d("0.250000")
    assert report.blocked_ratio == d("0.250000")
    assert report.cleared_ratio == d("0.250000")
    assert report.max_recheck_age_seconds == d("14400.000000")
    assert report.max_overdue_age_seconds == d("7200.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.recheck_id for row in report.rows) == (
        "recheck-blocked",
        "recheck-overdue",
        "recheck-in-progress",
        "recheck-clear",
    )
    blocked = report.rows[0]
    assert blocked.status == "blocked"
    assert blocked.recheck_age_seconds == d("10800.000000")
    assert blocked.overdue_age_seconds == d("7200.000000")
    assert blocked.reason_codes == (
        "source_ack_recheck_status_blocked",
        "source_ack_recheck_blocked_owner_missing",
    )

    overdue = report.rows[1]
    assert overdue.status == "overdue"
    assert overdue.recheck_age_seconds == d("14400.000000")
    assert overdue.overdue_age_seconds == d("5400.000000")
    assert overdue.reason_codes == ("source_ack_recheck_status_overdue",)

    in_progress = report.rows[2]
    assert in_progress.status == "in_progress"
    assert in_progress.overdue_age_seconds == d("0.000000")
    assert in_progress.reason_codes == ("source_ack_recheck_status_in_progress",)

    cleared = report.rows[3]
    assert cleared.status == "cleared"
    assert cleared.reason_codes == ("source_ack_recheck_status_cleared",)

    assert report.summary_rows == (
        api().ResearchPacketSourceAckRecheckStatusSummaryRow(
            team_id="politics",
            category_id="politics",
            source_family="official",
            status="blocked",
            recheck_count=d("2"),
            overdue_count=d("1"),
            in_progress_count=d("0"),
            blocked_count=d("1"),
            cleared_count=d("0"),
            overdue_ratio=d("0.500000"),
            blocked_ratio=d("0.500000"),
            cleared_ratio=d("0.000000"),
            max_recheck_age_seconds=d("14400.000000"),
            max_overdue_age_seconds=d("7200.000000"),
            reason_codes=(
                "source_ack_recheck_status_blocked",
                "source_ack_recheck_status_overdue",
                "source_ack_recheck_blocked_owner_missing",
            ),
        ),
        api().ResearchPacketSourceAckRecheckStatusSummaryRow(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            source_family="proxy",
            status="in_progress",
            recheck_count=d("2"),
            overdue_count=d("0"),
            in_progress_count=d("1"),
            blocked_count=d("0"),
            cleared_count=d("1"),
            overdue_ratio=d("0.000000"),
            blocked_ratio=d("0.000000"),
            cleared_ratio=d("0.500000"),
            max_recheck_age_seconds=d("9000.000000"),
            max_overdue_age_seconds=d("0.000000"),
            reason_codes=(
                "source_ack_recheck_status_in_progress",
                "source_ack_recheck_status_cleared",
            ),
        ),
    )


def test_empty_status_report_is_decimal_report_only_and_json_ready() -> None:
    module = api()
    report = _build_report()

    assert report.status == "empty"
    assert report.reason_codes == ("source_ack_recheck_status_empty",)
    assert report.recheck_count == d("0")
    assert report.summary_row_count == d("0")
    assert report.overdue_count == d("0")
    assert report.in_progress_count == d("0")
    assert report.blocked_count == d("0")
    assert report.cleared_count == d("0")
    assert report.overdue_ratio == d("0.000000")
    assert report.blocked_ratio == d("0.000000")
    assert report.cleared_ratio == d("0.000000")
    assert report.max_recheck_age_seconds == d("0.000000")
    assert report.max_overdue_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.summary_rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.research_packet_source_ack_recheck_status_report_to_payload(report)
    assert payload["generated_at"] == "2026-07-02T16:00:00+00:00"
    assert payload["recheck_count"] == "0"
    assert payload["max_recheck_age_seconds"] == "0.000000"
    assert payload["rows"] == []
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_datetimes_flags_decimal_public_fields_and_uniqueness_are_validated() -> None:
    module = api()
    local_generated_at = datetime(2026, 7, 2, 12, 0, tzinfo=timezone(timedelta(hours=-4)))
    local_requested_at = datetime(2026, 7, 2, 9, 0, tzinfo=timezone(timedelta(hours=-4)))
    report = _build_report(
        _recheck(
            "recheck-tz",
            requested_at=local_requested_at,
            due_at=datetime(2026, 7, 2, 15, 30, tzinfo=UTC),
        ),
        generated_at=local_generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].requested_at == datetime(2026, 7, 2, 13, 0, tzinfo=UTC)
    assert type(report.recheck_count) is Decimal
    assert type(report.overdue_ratio) is Decimal
    assert type(report.rows[0].recheck_age_seconds) is Decimal
    assert type(report.rows[0].overdue_age_seconds) is Decimal
    assert type(report.summary_rows[0].recheck_count) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="recheck_count must be a Decimal"):
        replace(report, recheck_count=1)
    with pytest.raises(ValueError, match="requested_at must be timezone-aware"):
        _recheck("recheck-naive", requested_at=datetime(2026, 7, 2, 13, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_packet_source_ack_recheck_status_report(
            (_recheck("recheck-valid"),),
            config=module.ResearchPacketSourceAckRecheckStatusConfig(),
            generated_at=datetime(2026, 7, 2, 16, 0),
        )
    with pytest.raises(ValueError, match="requested_at must be <= generated_at"):
        _build_report(
            _recheck(
                "recheck-future",
                requested_at=GENERATED_AT + timedelta(seconds=1),
                due_at=GENERATED_AT + timedelta(minutes=1),
            ),
        )
    with pytest.raises(ValueError, match="recheck_id values must be unique"):
        _build_report(_recheck("recheck-dup"), _recheck("recheck-dup"))
    with pytest.raises(ValueError, match="category_id must match team_id"):
        _recheck(
            "recheck-category",
            team_id="crypto_btc",
            category_id="politics",
        )
    with pytest.raises(ValueError, match="cleared_at and blocked_at"):
        _recheck(
            "recheck-terminal",
            cleared_at=datetime(2026, 7, 2, 15, 0, tzinfo=UTC),
            blocked_at=datetime(2026, 7, 2, 15, 5, tzinfo=UTC),
            blocked_reason_code="source_ack_recheck_blocked_source_unavailable",
        )
    with pytest.raises(ValueError, match="blocked_reason_code is required"):
        _recheck(
            "recheck-blocked-no-reason",
            blocked_at=datetime(2026, 7, 2, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_recheck("recheck-flag"), paper_only=False)


def test_payload_helper_and_public_api_stay_pure_in_memory_report_only() -> None:
    module = api()
    report = _build_report(
        _recheck(
            "recheck-json",
            blocked_at=datetime(2026, 7, 2, 15, 0, tzinfo=UTC),
            blocked_reason_code="source_ack_recheck_blocked_dependency",
        ),
    )

    payload = module.research_packet_source_ack_recheck_status_report_to_payload(report)

    assert payload["generated_at"] == "2026-07-02T16:00:00+00:00"
    assert payload["recheck_count"] == "1"
    assert payload["blocked_ratio"] == "1.000000"
    assert payload["rows"][0]["recheck_age_seconds"] == "10800.000000"
    assert payload["summary_rows"][0]["blocked_count"] == "1"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_STATUS_CONFIG_VERSION",
        "ResearchPacketSourceAckRecheckStatusConfig",
        "ResearchPacketSourceAckRecheckStatusInput",
        "ResearchPacketSourceAckRecheckStatusReport",
        "ResearchPacketSourceAckRecheckStatusRow",
        "ResearchPacketSourceAckRecheckStatusSummaryRow",
        "build_research_packet_source_ack_recheck_status_report",
        "research_packet_source_ack_recheck_status_report_to_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(ValueError, match="report must be"):
        module.research_packet_source_ack_recheck_status_report_to_payload(object())

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "market_slug",
        "question",
        "wallet",
        "account",
        "broker",
        "order",
        "submit",
        "cancel",
        "signing",
        "advice",
        "private_key",
        "credential",
        "payload_json",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
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


def _float_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, float):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    return ()
