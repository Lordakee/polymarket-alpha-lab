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
        "polymarket_alpha_lab.research_packet_source_ack_recheck_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    return module.ResearchPacketSourceAckRecheckPriorityConfig(**overrides)


def _packet(
    packet_id: str,
    *,
    team_id: str = "politics",
    category_id: str = "politics",
    source_family: str = "official",
    requested_at: datetime = datetime(2026, 7, 1, 16, 0, tzinfo=UTC),
    last_rechecked_at: datetime | None = datetime(2026, 7, 2, 8, 0, tzinfo=UTC),
    required_ack_count: Decimal = d("4"),
    acknowledged_ack_count: Decimal = d("4"),
    source_reliability_score: Decimal = d("0.900000"),
):
    module = api()
    return module.ResearchPacketSourceAckRecheckPriorityInput(
        packet_id=packet_id,
        team_id=team_id,
        category_id=category_id,
        source_family=source_family,
        requested_at=requested_at,
        last_rechecked_at=last_rechecked_at,
        required_ack_count=required_ack_count,
        acknowledged_ack_count=acknowledged_ack_count,
        source_reliability_score=source_reliability_score,
    )


def _build_report(*packets, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_packet_source_ack_recheck_priority_report(
        packets,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_empty_priority_report_is_decimal_safe_and_json_ready() -> None:
    module = api()
    report = _build_report()

    assert is_dataclass(report)
    assert report.status == "empty"
    assert report.reason_codes == ("source_ack_priority_empty",)
    assert report.packet_count == d("0")
    assert report.critical_packet_count == d("0")
    assert report.watch_packet_count == d("0")
    assert report.clear_packet_count == d("0")
    assert report.missing_ack_packet_count == d("0")
    assert report.stale_recheck_packet_count == d("0")
    assert report.reliability_gap_packet_count == d("0")
    assert report.max_missing_ack_pressure_ratio == d("0.000000")
    assert report.max_stale_recheck_age_seconds == d("0.000000")
    assert report.max_source_reliability_gap == d("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.research_packet_source_ack_recheck_priority_report_to_payload(report)
    assert payload["generated_at"] == "2026-07-02T16:00:00+00:00"
    assert payload["packet_count"] == "0"
    assert payload["max_stale_recheck_age_seconds"] == "0.000000"
    assert payload["rows"] == []
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_priority_report_ranks_by_pressure_age_gap_reason_codes_then_packet_id() -> None:
    report = _build_report(
        _packet(
            "packet-tie-never",
            requested_at=datetime(2026, 7, 1, 16, 0, tzinfo=UTC),
            last_rechecked_at=None,
            acknowledged_ack_count=d("3"),
            source_reliability_score=d("0.700000"),
        ),
        _packet(
            "packet-high-pressure",
            requested_at=datetime(2026, 7, 2, 4, 0, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 7, 2, 4, 0, tzinfo=UTC),
            acknowledged_ack_count=d("1"),
            source_reliability_score=d("0.800000"),
        ),
        _packet(
            "packet-tie-checked",
            requested_at=datetime(2026, 7, 1, 8, 0, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 7, 1, 16, 0, tzinfo=UTC),
            acknowledged_ack_count=d("3"),
            source_reliability_score=d("0.700000"),
        ),
        _packet(
            "packet-clear",
            requested_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 7, 2, 15, 0, tzinfo=UTC),
        ),
        _packet(
            "packet-age-wins-after-pressure",
            requested_at=datetime(2026, 6, 30, 16, 0, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 6, 30, 16, 0, tzinfo=UTC),
            acknowledged_ack_count=d("2"),
            source_reliability_score=d("0.550000"),
        ),
    )

    assert tuple(row.packet_id for row in report.rows) == (
        "packet-high-pressure",
        "packet-age-wins-after-pressure",
        "packet-tie-checked",
        "packet-tie-never",
        "packet-clear",
    )
    assert tuple(row.priority_rank for row in report.rows) == (
        d("1"),
        d("2"),
        d("3"),
        d("4"),
        d("5"),
    )
    assert report.rows[0].missing_ack_pressure_ratio == d("0.750000")
    assert report.rows[1].missing_ack_pressure_ratio == d("0.500000")
    assert report.rows[1].stale_recheck_age_seconds == d("172800.000000")
    assert report.rows[2].reason_codes == (
        "source_ack_priority_missing_ack_pressure_watch",
        "source_ack_priority_stale_recheck_age_watch",
        "source_ack_priority_reliability_gap_watch",
    )
    assert report.rows[3].reason_codes == (
        "source_ack_priority_missing_ack_pressure_watch",
        "source_ack_priority_stale_recheck_age_watch",
        "source_ack_priority_reliability_gap_watch",
        "source_ack_priority_never_rechecked",
    )


def test_threshold_statuses_and_reason_codes_are_deterministic() -> None:
    config = _config(
        missing_ack_watch_ratio=d("0.250000"),
        missing_ack_critical_ratio=d("0.500000"),
        stale_recheck_watch_seconds=d("86400.000000"),
        stale_recheck_critical_seconds=d("172800.000000"),
        reliability_gap_watch=d("0.100000"),
        reliability_gap_critical=d("0.250000"),
        min_source_reliability_score=d("0.800000"),
    )

    report = _build_report(
        _packet(
            "packet-critical",
            requested_at=datetime(2026, 6, 30, 16, 0, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 6, 30, 16, 0, tzinfo=UTC),
            acknowledged_ack_count=d("2"),
            source_reliability_score=d("0.550000"),
        ),
        _packet(
            "packet-watch",
            requested_at=datetime(2026, 7, 1, 16, 0, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 7, 1, 16, 0, tzinfo=UTC),
            acknowledged_ack_count=d("3"),
            source_reliability_score=d("0.700000"),
        ),
        _packet(
            "packet-clear",
            requested_at=datetime(2026, 7, 2, 12, 0, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 7, 2, 15, 0, tzinfo=UTC),
            acknowledged_ack_count=d("4"),
            source_reliability_score=d("0.900000"),
        ),
        config=config,
    )

    assert report.status == "critical"
    assert report.reason_codes == (
        "source_ack_priority_missing_ack_pressure_critical",
        "source_ack_priority_missing_ack_pressure_watch",
        "source_ack_priority_stale_recheck_age_critical",
        "source_ack_priority_stale_recheck_age_watch",
        "source_ack_priority_reliability_gap_critical",
        "source_ack_priority_reliability_gap_watch",
    )
    assert report.packet_count == d("3")
    assert report.critical_packet_count == d("1")
    assert report.watch_packet_count == d("1")
    assert report.clear_packet_count == d("1")
    assert report.missing_ack_packet_count == d("2")
    assert report.stale_recheck_packet_count == d("2")
    assert report.reliability_gap_packet_count == d("2")
    assert report.max_missing_ack_pressure_ratio == d("0.500000")
    assert report.max_stale_recheck_age_seconds == d("172800.000000")
    assert report.max_source_reliability_gap == d("0.250000")

    critical = report.rows[0]
    assert critical.priority_status == "critical"
    assert critical.missing_ack_count == d("2")
    assert critical.reason_codes == (
        "source_ack_priority_missing_ack_pressure_critical",
        "source_ack_priority_stale_recheck_age_critical",
        "source_ack_priority_reliability_gap_critical",
    )

    watch = report.rows[1]
    assert watch.priority_status == "watch"
    assert watch.missing_ack_pressure_ratio == d("0.250000")
    assert watch.stale_recheck_age_seconds == d("86400.000000")
    assert watch.source_reliability_gap == d("0.100000")
    assert watch.reason_codes == (
        "source_ack_priority_missing_ack_pressure_watch",
        "source_ack_priority_stale_recheck_age_watch",
        "source_ack_priority_reliability_gap_watch",
    )

    clear = report.rows[2]
    assert clear.priority_status == "clear"
    assert clear.reason_codes == ("source_ack_priority_clear",)


def test_utc_datetimes_decimal_values_and_flags_are_validated() -> None:
    module = api()

    with pytest.raises(ValueError, match="requested_at must be UTC-aware"):
        _packet("packet-naive-request", requested_at=datetime(2026, 7, 1, 16, 0))
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        _build_report(
            _packet("packet-valid"),
            generated_at=datetime(
                2026,
                7,
                2,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="required_ack_count must be a Decimal"):
        _packet("packet-float-count", required_ack_count=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_reliability_score must be a Decimal"):
        _packet(
            "packet-float-score",
            source_reliability_score=0.5,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="acknowledged_ack_count must not exceed"):
        _packet(
            "packet-too-many-acks",
            required_ack_count=d("2"),
            acknowledged_ack_count=d("3"),
        )
    with pytest.raises(ValueError, match="packet_id values must be unique"):
        _build_report(_packet("packet-dup"), _packet("packet-dup"))
    with pytest.raises(ValueError, match="category_id must match team_id"):
        _packet(
            "packet-category",
            team_id="crypto_btc",
            category_id="politics",
        )
    with pytest.raises(ValueError, match="last_rechecked_at must be <= generated_at"):
        _build_report(
            _packet(
                "packet-future-recheck",
                last_rechecked_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_packet("packet-flag"), paper_only=False)

    report = module.ResearchPacketSourceAckRecheckPriorityReport(
        generated_at=GENERATED_AT,
        config_version=module.DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_PRIORITY_CONFIG_VERSION,
        status="empty",
        packet_count=d("0"),
        critical_packet_count=d("0"),
        watch_packet_count=d("0"),
        clear_packet_count=d("0"),
        missing_ack_packet_count=d("0"),
        stale_recheck_packet_count=d("0"),
        reliability_gap_packet_count=d("0"),
        max_missing_ack_pressure_ratio=d("0.000000"),
        max_stale_recheck_age_seconds=d("0.000000"),
        max_source_reliability_gap=d("0.000000"),
        rows=(),
        reason_codes=("source_ack_priority_empty",),
    )
    with pytest.raises(ValueError, match="packet_count must be a Decimal"):
        replace(report, packet_count=0)


def test_manual_reason_codes_must_be_row_scoped_unique_and_deterministic() -> None:
    critical = _build_report(
        _packet(
            "packet-critical",
            requested_at=datetime(2026, 6, 30, 16, 0, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 6, 30, 16, 0, tzinfo=UTC),
            acknowledged_ack_count=d("2"),
            source_reliability_score=d("0.550000"),
        ),
    ).rows[0]

    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(
            critical,
            reason_codes=(
                "source_ack_priority_missing_ack_pressure_critical",
                "source_ack_priority_missing_ack_pressure_critical",
            ),
        )
    with pytest.raises(ValueError, match="reason_codes must be deterministic"):
        replace(
            critical,
            reason_codes=(
                "source_ack_priority_reliability_gap_critical",
                "source_ack_priority_missing_ack_pressure_critical",
                "source_ack_priority_stale_recheck_age_critical",
            ),
        )
    with pytest.raises(ValueError, match="source_ack_priority_clear must be exclusive"):
        replace(
            critical,
            reason_codes=(
                "source_ack_priority_missing_ack_pressure_critical",
                "source_ack_priority_clear",
            ),
        )
    with pytest.raises(ValueError, match="reason_codes must contain known row reason codes"):
        replace(critical, reason_codes=("source_ack_priority_empty",))


def test_public_dataclasses_are_frozen_and_payload_helper_stays_pure() -> None:
    module = api()
    report = _build_report(
        _packet(
            "packet-json",
            requested_at=datetime(2026, 6, 30, 16, 0, tzinfo=UTC),
            last_rechecked_at=None,
            acknowledged_ack_count=d("1"),
            source_reliability_score=d("0.500000"),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_status = "clear"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    payload = module.research_packet_source_ack_recheck_priority_report_to_payload(report)
    assert payload["packet_count"] == "1"
    assert payload["rows"][0]["priority_rank"] == "1"
    assert payload["rows"][0]["missing_ack_pressure_ratio"] == "0.750000"
    assert payload["rows"][0]["last_rechecked_at"] is None
    assert payload["rows"][0]["requested_at"] == "2026-06-30T16:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_PRIORITY_CONFIG_VERSION",
        "ResearchPacketSourceAckRecheckPriorityConfig",
        "ResearchPacketSourceAckRecheckPriorityInput",
        "ResearchPacketSourceAckRecheckPriorityReport",
        "ResearchPacketSourceAckRecheckPriorityRow",
        "build_research_packet_source_ack_recheck_priority_report",
        "research_packet_source_ack_recheck_priority_report_to_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(ValueError, match="report must be"):
        module.research_packet_source_ack_recheck_priority_report_to_payload(object())

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
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
