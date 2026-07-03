from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 2, 16, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_source_ack_recheck_health_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    values = {
        "ack_latency_watch_seconds": d("300.000000"),
        "ack_latency_block_seconds": d("600.000000"),
        "missing_acknowledgement_watch_count": d("1"),
        "missing_acknowledgement_block_count": d("2"),
        "recheck_freshness_watch_seconds": d("1800.000000"),
        "recheck_freshness_block_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return module.ResearchPacketSourceAckRecheckHealthConfig(**values)


def _observation(
    observation_id: str,
    *,
    packet_id: str | None = None,
    source_id: str | None = None,
    source_family: str = "official",
    team_id: str = "politics",
    category_id: str = "politics",
    source_observed_at: datetime = datetime(2026, 7, 2, 15, 40, tzinfo=UTC),
    acknowledged_at: datetime | None = datetime(2026, 7, 2, 15, 43, tzinfo=UTC),
    rechecked_at: datetime | None = datetime(2026, 7, 2, 15, 50, tzinfo=UTC),
):
    module = api()
    suffix = observation_id.replace("obs-", "")
    return module.ResearchPacketSourceAckRecheckHealthObservation(
        observation_id=observation_id,
        packet_id=packet_id or f"packet-{suffix}",
        source_id=source_id or f"source-{suffix}",
        source_family=source_family,
        team_id=team_id,
        category_id=category_id,
        source_observed_at=source_observed_at,
        acknowledged_at=acknowledged_at,
        rechecked_at=rechecked_at,
    )


def _build_report(*observations, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_packet_source_ack_recheck_health_report(
        observations,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_empty_health_report_is_report_only_and_decimal_safe_payload() -> None:
    module = api()
    report = _build_report()

    assert is_dataclass(report)
    assert report.status == "empty"
    assert report.reason_codes == ("source_ack_recheck_health_empty",)
    assert report.observation_count == d("0")
    assert report.summary_row_count == d("0")
    assert report.pass_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.missing_acknowledgement_count == d("0")
    assert report.ack_latency_watch_count == d("0")
    assert report.ack_latency_blocked_count == d("0")
    assert report.missing_acknowledgement_pressure_count == d("0")
    assert report.recheck_freshness_watch_count == d("0")
    assert report.recheck_freshness_blocked_count == d("0")
    assert report.issue_ratio == d("0.000000")
    assert report.max_ack_latency_seconds == d("0.000000")
    assert report.max_missing_acknowledgement_age_seconds == d("0.000000")
    assert report.max_recheck_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.summary_rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.research_packet_source_ack_recheck_health_report_to_payload(report)
    assert payload["generated_at"] == "2026-07-02T16:00:00+00:00"
    assert payload["observation_count"] == "0"
    assert payload["issue_ratio"] == "0.000000"
    assert payload["rows"] == []
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_health_report_classifies_latency_missing_pressure_and_recheck_freshness() -> None:
    report = _build_report(
        _observation(
            "obs-clear",
            source_family="proxy",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            source_observed_at=datetime(2026, 7, 2, 15, 40, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 15, 43, tzinfo=UTC),
            rechecked_at=datetime(2026, 7, 2, 15, 55, tzinfo=UTC),
        ),
        _observation(
            "obs-latency-watch",
            source_observed_at=datetime(2026, 7, 2, 15, 35, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 15, 41, tzinfo=UTC),
            rechecked_at=datetime(2026, 7, 2, 15, 50, tzinfo=UTC),
        ),
        _observation(
            "obs-recheck-blocked",
            source_observed_at=datetime(2026, 7, 2, 14, 0, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 14, 20, tzinfo=UTC),
            rechecked_at=datetime(2026, 7, 2, 14, 30, tzinfo=UTC),
        ),
        _observation(
            "obs-missing-alpha",
            source_observed_at=datetime(2026, 7, 2, 15, 0, tzinfo=UTC),
            acknowledged_at=None,
            rechecked_at=None,
        ),
        _observation(
            "obs-missing-beta",
            source_observed_at=datetime(2026, 7, 2, 15, 10, tzinfo=UTC),
            acknowledged_at=None,
            rechecked_at=None,
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.status == "blocked"
    assert report.observation_count == d("5")
    assert report.summary_row_count == d("2")
    assert report.pass_count == d("1")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("4")
    assert report.missing_acknowledgement_count == d("2")
    assert report.ack_latency_watch_count == d("1")
    assert report.ack_latency_blocked_count == d("3")
    assert report.missing_acknowledgement_pressure_count == d("4")
    assert report.recheck_freshness_watch_count == d("1")
    assert report.recheck_freshness_blocked_count == d("2")
    assert report.issue_ratio == d("0.800000")
    assert report.max_ack_latency_seconds == d("3600.000000")
    assert report.max_missing_acknowledgement_age_seconds == d("3600.000000")
    assert report.max_recheck_age_seconds == d("5400.000000")
    assert report.reason_codes == (
        "source_ack_latency_watch",
        "source_ack_latency_blocked",
        "source_ack_missing_acknowledgement",
        "source_ack_missing_pressure_blocked",
        "source_ack_recheck_freshness_blocked",
    )

    assert tuple(row.observation_id for row in report.rows) == (
        "obs-missing-alpha",
        "obs-recheck-blocked",
        "obs-missing-beta",
        "obs-latency-watch",
        "obs-clear",
    )
    missing = report.rows[0]
    assert missing.status == "blocked"
    assert missing.ack_latency_status == "blocked"
    assert missing.missing_acknowledgement_pressure_status == "blocked"
    assert missing.recheck_freshness_status == "blocked"
    assert missing.ack_latency_seconds == d("3600.000000")
    assert missing.missing_acknowledgement_age_seconds == d("3600.000000")
    assert missing.recheck_age_seconds == d("3600.000000")
    assert missing.group_missing_acknowledgement_count == d("2")
    assert missing.group_observation_count == d("4")
    assert missing.group_missing_acknowledgement_ratio == d("0.500000")
    assert missing.reason_codes == (
        "source_ack_latency_blocked",
        "source_ack_missing_acknowledgement",
        "source_ack_missing_pressure_blocked",
    )

    recheck_blocked = report.rows[1]
    assert recheck_blocked.ack_latency_status == "blocked"
    assert recheck_blocked.recheck_freshness_status == "blocked"
    assert recheck_blocked.ack_latency_seconds == d("1200.000000")
    assert recheck_blocked.recheck_age_seconds == d("5400.000000")
    assert recheck_blocked.reason_codes == (
        "source_ack_latency_blocked",
        "source_ack_missing_pressure_blocked",
        "source_ack_recheck_freshness_blocked",
    )

    latency_watch = report.rows[3]
    assert latency_watch.status == "blocked"
    assert latency_watch.ack_latency_status == "watch"
    assert latency_watch.missing_acknowledgement_pressure_status == "blocked"
    assert latency_watch.recheck_freshness_status == "pass"

    clear = report.rows[4]
    assert clear.status == "pass"
    assert clear.reason_codes == ("source_ack_recheck_health_clear",)

    assert report.summary_rows == (
        api().ResearchPacketSourceAckRecheckHealthSummaryRow(
            team_id="politics",
            category_id="politics",
            source_family="official",
            status="blocked",
            observation_count=d("4"),
            missing_acknowledgement_count=d("2"),
            missing_acknowledgement_ratio=d("0.500000"),
            max_ack_latency_seconds=d("3600.000000"),
            max_recheck_age_seconds=d("5400.000000"),
            reason_codes=(
                "source_ack_latency_watch",
                "source_ack_latency_blocked",
                "source_ack_missing_acknowledgement",
                "source_ack_missing_pressure_blocked",
                "source_ack_recheck_freshness_blocked",
            ),
        ),
        api().ResearchPacketSourceAckRecheckHealthSummaryRow(
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            source_family="proxy",
            status="pass",
            observation_count=d("1"),
            missing_acknowledgement_count=d("0"),
            missing_acknowledgement_ratio=d("0.000000"),
            max_ack_latency_seconds=d("180.000000"),
            max_recheck_age_seconds=d("300.000000"),
            reason_codes=("source_ack_recheck_health_clear",),
        ),
    )


def test_health_report_sorting_is_deterministic_for_observations_and_summaries() -> None:
    observations = (
        _observation(
            "obs-pass",
            source_family="proxy",
            team_id="sports_other",
            category_id="sports.other",
            source_observed_at=datetime(2026, 7, 2, 15, 50, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 15, 52, tzinfo=UTC),
            rechecked_at=datetime(2026, 7, 2, 15, 55, tzinfo=UTC),
        ),
        _observation(
            "obs-watch",
            source_family="official",
            team_id="crypto_btc",
            category_id="finance.crypto.btc",
            source_observed_at=datetime(2026, 7, 2, 15, 40, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 15, 46, tzinfo=UTC),
            rechecked_at=datetime(2026, 7, 2, 15, 55, tzinfo=UTC),
        ),
        _observation(
            "obs-blocked",
            source_family="official",
            team_id="politics",
            category_id="politics",
            source_observed_at=datetime(2026, 7, 2, 15, 0, tzinfo=UTC),
            acknowledged_at=None,
            rechecked_at=None,
        ),
    )

    first = _build_report(*observations)
    second = _build_report(*reversed(observations))

    assert first == second
    assert tuple(row.observation_id for row in first.rows) == (
        "obs-blocked",
        "obs-watch",
        "obs-pass",
    )
    assert tuple(
        (row.team_id, row.category_id, row.source_family)
        for row in first.summary_rows
    ) == (
        ("politics", "politics", "official"),
        ("crypto_btc", "finance.crypto.btc", "official"),
        ("sports_other", "sports.other", "proxy"),
    )


def test_threshold_boundaries_drive_dimension_statuses() -> None:
    config = _config(
        ack_latency_watch_seconds=d("60.000000"),
        ack_latency_block_seconds=d("120.000000"),
        missing_acknowledgement_watch_count=d("1"),
        missing_acknowledgement_block_count=d("2"),
        recheck_freshness_watch_seconds=d("300.000000"),
        recheck_freshness_block_seconds=d("600.000000"),
    )

    report = _build_report(
        _observation(
            "obs-boundary-pass",
            source_observed_at=datetime(2026, 7, 2, 15, 40, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 15, 41, tzinfo=UTC),
            rechecked_at=GENERATED_AT - timedelta(seconds=300),
        ),
        _observation(
            "obs-watch",
            source_observed_at=datetime(2026, 7, 2, 15, 30, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 15, 31, 1, tzinfo=UTC),
            rechecked_at=GENERATED_AT - timedelta(seconds=301),
        ),
        _observation(
            "obs-blocked",
            source_observed_at=datetime(2026, 7, 2, 15, 20, tzinfo=UTC),
            acknowledged_at=datetime(2026, 7, 2, 15, 22, 1, tzinfo=UTC),
            rechecked_at=GENERATED_AT - timedelta(seconds=601),
        ),
        config=config,
    )

    rows = {row.observation_id: row for row in report.rows}
    assert rows["obs-boundary-pass"].ack_latency_status == "pass"
    assert rows["obs-boundary-pass"].recheck_freshness_status == "pass"
    assert rows["obs-watch"].ack_latency_status == "watch"
    assert rows["obs-watch"].recheck_freshness_status == "watch"
    assert rows["obs-blocked"].ack_latency_status == "blocked"
    assert rows["obs-blocked"].recheck_freshness_status == "blocked"


def test_datetime_decimal_flag_and_uniqueness_validation() -> None:
    module = api()
    local_observed_at = datetime(2026, 7, 2, 11, 40, tzinfo=timezone(timedelta(hours=-4)))
    local_acknowledged_at = datetime(2026, 7, 2, 11, 43, tzinfo=timezone(timedelta(hours=-4)))
    report = _build_report(
        _observation(
            "obs-tz",
            source_observed_at=local_observed_at,
            acknowledged_at=local_acknowledged_at,
            rechecked_at=datetime(2026, 7, 2, 15, 50, tzinfo=UTC),
        ),
    )

    assert report.rows[0].source_observed_at == datetime(2026, 7, 2, 15, 40, tzinfo=UTC)
    assert report.rows[0].acknowledged_at == datetime(2026, 7, 2, 15, 43, tzinfo=UTC)
    assert type(report.observation_count) is Decimal
    assert type(report.issue_ratio) is Decimal
    assert type(report.rows[0].ack_latency_seconds) is Decimal
    assert type(report.rows[0].group_missing_acknowledgement_ratio) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="ack_latency_watch_seconds must be a Decimal"):
        module.ResearchPacketSourceAckRecheckHealthConfig(
            ack_latency_watch_seconds=_DecimalSubclass("60.000000"),
        )
    with pytest.raises(ValueError, match="source_observed_at must be timezone-aware"):
        _observation(
            "obs-naive-observed",
            source_observed_at=datetime(2026, 7, 2, 15, 40),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_packet_source_ack_recheck_health_report(
            (_observation("obs-valid"),),
            config=module.ResearchPacketSourceAckRecheckHealthConfig(),
            generated_at=datetime(2026, 7, 2, 16, 0),
        )
    with pytest.raises(ValueError, match="source_observed_at must be <= generated_at"):
        _build_report(
            _observation(
                "obs-future",
                source_observed_at=GENERATED_AT + timedelta(seconds=1),
                acknowledged_at=None,
                rechecked_at=None,
            ),
        )
    with pytest.raises(ValueError, match="observation_id values must be unique"):
        _build_report(
            _observation("obs-dup"),
            _observation("obs-dup", packet_id="packet-other"),
        )
    with pytest.raises(ValueError, match="category_id must match team_id"):
        _observation(
            "obs-category",
            team_id="crypto_btc",
            category_id="politics",
        )
    with pytest.raises(ValueError, match="observation_id must be a canonical"):
        _observation("obs-control\nchar")
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation("obs-flag"), paper_only=False)


def test_payload_helper_json_decimal_safety_and_public_api_scope() -> None:
    module = api()
    report = _build_report(
        _observation(
            "obs-json",
            source_observed_at=datetime(2026, 7, 2, 15, 0, tzinfo=UTC),
            acknowledged_at=None,
            rechecked_at=None,
        ),
    )

    payload = module.research_packet_source_ack_recheck_health_report_to_payload(report)

    assert payload["generated_at"] == "2026-07-02T16:00:00+00:00"
    assert payload["observation_count"] == "1"
    assert payload["issue_ratio"] == "1.000000"
    assert payload["max_ack_latency_seconds"] == "3600.000000"
    assert payload["rows"][0]["ack_latency_seconds"] == "3600.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_SOURCE_ACK_RECHECK_HEALTH_CONFIG_VERSION",
        "ResearchPacketSourceAckRecheckHealthConfig",
        "ResearchPacketSourceAckRecheckHealthObservation",
        "ResearchPacketSourceAckRecheckHealthReport",
        "ResearchPacketSourceAckRecheckHealthRow",
        "ResearchPacketSourceAckRecheckHealthSummaryRow",
        "build_research_packet_source_ack_recheck_health_report",
        "research_packet_source_ack_recheck_health_report_to_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(ValueError, match="report must be"):
        module.research_packet_source_ack_recheck_health_report_to_payload(object())

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
