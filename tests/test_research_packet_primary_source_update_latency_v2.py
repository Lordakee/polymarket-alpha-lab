from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
BASE_DETECTED_AT = datetime(2026, 7, 7, 10, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_packet_primary_source_update_latency_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    values = {
        "routine_sla_seconds": d("3600.000000"),
        "elevated_sla_seconds": d("1800.000000"),
        "critical_sla_seconds": d("600.000000"),
        "elevated_probability_delta": d("0.050000"),
        "critical_probability_delta": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchPacketPrimarySourceUpdateLatencyConfig(**values)


def _movement(
    movement_id: str,
    *,
    market_id: str,
    detected_at: datetime = BASE_DETECTED_AT,
    probability_before: Decimal = d("0.400000"),
    probability_after: Decimal = d("0.430000"),
    team_id: str = "politics",
    category_id: str = "politics",
):
    module = api()
    return module.ResearchPacketMarketProbabilityMovement(
        movement_id=movement_id,
        market_id=market_id,
        team_id=team_id,
        category_id=category_id,
        detected_at=detected_at,
        probability_before=probability_before,
        probability_after=probability_after,
    )


def _update(
    update_id: str,
    *,
    market_id: str,
    source_family: str,
    collected_at: datetime,
    source_id: str | None = None,
):
    module = api()
    return module.ResearchPacketPrimarySourceUpdate(
        update_id=update_id,
        market_id=market_id,
        source_id=f"source-{update_id}" if source_id is None else source_id,
        source_family=source_family,
        collected_at=collected_at,
    )


def _build_report(*movements, updates=(), config=None):
    module = api()
    return module.build_research_packet_primary_source_update_latency_v2_report(
        movements,
        updates,
        config=_config() if config is None else config,
        generated_at=GENERATED_AT,
    )


def _scenario_report():
    return _build_report(
        _movement(
            "move-critical",
            market_id="market-critical",
            probability_before=d("0.300000"),
            probability_after=d("0.520000"),
        ),
        _movement(
            "move-elevated",
            market_id="market-elevated",
            detected_at=BASE_DETECTED_AT + timedelta(minutes=10),
            probability_before=d("0.500000"),
            probability_after=d("0.610000"),
        ),
        _movement(
            "move-routine",
            market_id="market-routine",
            detected_at=BASE_DETECTED_AT + timedelta(hours=1),
            probability_before=d("0.400000"),
            probability_after=d("0.420000"),
        ),
        updates=(
            _update(
                "update-elevated-proxy",
                market_id="market-elevated",
                source_family="proxy",
                collected_at=BASE_DETECTED_AT + timedelta(minutes=50),
            ),
            _update(
                "update-routine-before",
                market_id="market-routine",
                source_family="official",
                collected_at=BASE_DETECTED_AT + timedelta(minutes=55),
            ),
            _update(
                "update-critical-official",
                market_id="market-critical",
                source_family="official",
                collected_at=BASE_DETECTED_AT + timedelta(minutes=8),
            ),
        ),
    )


def test_latency_report_measures_sla_tiers_official_presence_and_stale_reasons() -> None:
    report = _scenario_report()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "blocked"
    assert report.reason_codes == (
        "primary_source_update_missing",
        "primary_source_update_before_movement_only",
        "primary_source_update_sla_miss",
        "primary_source_update_missing_official_source",
    )
    assert report.movement_count == d("3")
    assert report.update_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.blocked_count == d("1")
    assert report.routine_count == d("1")
    assert report.elevated_count == d("1")
    assert report.critical_count == d("1")
    assert report.official_source_present_count == d("1")
    assert report.missing_official_source_count == d("2")
    assert report.sla_miss_count == d("1")
    assert report.no_update_count == d("1")
    assert report.before_movement_only_count == d("1")
    assert report.max_collection_latency_seconds == d("2400.000000")
    assert report.average_collection_latency_seconds == d("1440.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    rows = {row.movement_id: row for row in report.rows}
    critical = rows["move-critical"]
    assert critical.status == "pass"
    assert critical.urgency == "critical"
    assert critical.sla_tier == "critical"
    assert critical.sla_seconds == d("600.000000")
    assert critical.collection_latency_seconds == d("480.000000")
    assert critical.collected_update_id == "update-critical-official"
    assert critical.collected_source_family == "official"
    assert critical.official_source_present is True
    assert critical.stale_source_reasons == ()
    assert critical.reason_codes == ("primary_source_update_latency_clear",)

    elevated = rows["move-elevated"]
    assert elevated.status == "watch"
    assert elevated.urgency == "elevated"
    assert elevated.sla_tier == "elevated"
    assert elevated.sla_seconds == d("1800.000000")
    assert elevated.collection_latency_seconds == d("2400.000000")
    assert elevated.collected_source_family == "proxy"
    assert elevated.official_source_present is False
    assert elevated.stale_source_reasons == (
        "collection_sla_miss",
        "missing_official_source",
    )
    assert elevated.reason_codes == (
        "primary_source_update_sla_miss",
        "primary_source_update_missing_official_source",
    )

    routine = rows["move-routine"]
    assert routine.status == "blocked"
    assert routine.urgency == "routine"
    assert routine.sla_tier == "routine"
    assert routine.collection_latency_seconds is None
    assert routine.collected_update_id is None
    assert routine.collected_source_family == "none"
    assert routine.official_source_present is False
    assert routine.stale_source_reasons == (
        "no_primary_source_update",
        "source_update_before_movement_only",
        "missing_official_source",
    )

    assert report.source_family_rollups == (
        api().ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup(
            source_family="none",
            movement_count=d("1"),
            stale_source_count=d("1"),
            official_source_present_count=d("0"),
            max_collection_latency_seconds=d("0.000000"),
        ),
        api().ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup(
            source_family="official",
            movement_count=d("1"),
            stale_source_count=d("0"),
            official_source_present_count=d("1"),
            max_collection_latency_seconds=d("480.000000"),
        ),
        api().ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup(
            source_family="proxy",
            movement_count=d("1"),
            stale_source_count=d("1"),
            official_source_present_count=d("0"),
            max_collection_latency_seconds=d("2400.000000"),
        ),
    )
    assert report.stale_source_reason_rollups == (
        api().ResearchPacketPrimarySourceUpdateLatencyReasonRollup(
            stale_source_reason="no_primary_source_update",
            movement_count=d("1"),
        ),
        api().ResearchPacketPrimarySourceUpdateLatencyReasonRollup(
            stale_source_reason="source_update_before_movement_only",
            movement_count=d("1"),
        ),
        api().ResearchPacketPrimarySourceUpdateLatencyReasonRollup(
            stale_source_reason="collection_sla_miss",
            movement_count=d("1"),
        ),
        api().ResearchPacketPrimarySourceUpdateLatencyReasonRollup(
            stale_source_reason="missing_official_source",
            movement_count=d("2"),
        ),
    )


def test_empty_report_and_payload_digest_are_decimal_json_ready() -> None:
    module = api()

    report = _build_report()
    payload = module.research_packet_primary_source_update_latency_v2_report_to_payload(
        report,
    )

    assert report.status == "empty"
    assert report.reason_codes == ("primary_source_update_latency_empty",)
    assert report.movement_count == d("0")
    assert report.update_count == d("0")
    assert report.max_collection_latency_seconds == d("0.000000")
    assert report.average_collection_latency_seconds == d("0.000000")
    assert report.rows == ()
    assert report.source_family_rollups == ()
    assert report.stale_source_reason_rollups == ()
    assert len(report.derived_validation_digest) == 64
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["movement_count"] == "0"
    assert payload["max_collection_latency_seconds"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert _float_paths(payload) == ()
    assert _int_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_input_order_does_not_change_rows_rollups_or_digest() -> None:
    module = api()
    movement_a = _movement(
        "move-a",
        market_id="market-a",
        detected_at=BASE_DETECTED_AT,
        probability_before=d("0.200000"),
        probability_after=d("0.410000"),
    )
    movement_b = _movement(
        "move-b",
        market_id="market-b",
        detected_at=BASE_DETECTED_AT + timedelta(minutes=5),
        probability_before=d("0.400000"),
        probability_after=d("0.470000"),
    )
    update_a = _update(
        "update-a",
        market_id="market-a",
        source_family="official",
        collected_at=BASE_DETECTED_AT + timedelta(minutes=5),
    )
    update_b = _update(
        "update-b",
        market_id="market-b",
        source_family="primary",
        collected_at=BASE_DETECTED_AT + timedelta(minutes=20),
    )

    first = module.build_research_packet_primary_source_update_latency_v2_report(
        (movement_a, movement_b),
        (update_b, update_a),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    second = module.build_research_packet_primary_source_update_latency_v2_report(
        (movement_b, movement_a),
        (update_a, update_b),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert tuple(row.movement_id for row in first.rows) == ("move-b", "move-a")
    assert first.reason_codes == ("primary_source_update_missing_official_source",)


def test_dataclasses_are_frozen_flags_datetimes_and_decimals_are_enforced() -> None:
    module = api()
    report = _scenario_report()

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="routine_sla_seconds must be a Decimal"):
        module.ResearchPacketPrimarySourceUpdateLatencyConfig(
            routine_sla_seconds=3600,
        )
    with pytest.raises(ValueError, match="elevated_probability_delta must be a Decimal"):
        module.ResearchPacketPrimarySourceUpdateLatencyConfig(
            elevated_probability_delta=_DecimalSubclass("0.050000"),
        )
    with pytest.raises(ValueError, match="probability_before must be a Decimal"):
        _movement("move-float", market_id="market-float", probability_before=0.4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="detected_at must be timezone-aware"):
        _movement(
            "move-naive",
            market_id="market-naive",
            detected_at=datetime(2026, 7, 7, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_packet_primary_source_update_latency_v2_report(
            (_movement("move-valid", market_id="market-valid"),),
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="detected_at must be <= generated_at"):
        _build_report(
            _movement(
                "move-future",
                market_id="market-future",
                detected_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="movement_id values must be unique"):
        _build_report(
            _movement("move-dup", market_id="market-dup-a"),
            _movement("move-dup", market_id="market-dup-b"),
        )
    with pytest.raises(ValueError, match="update_id values must be unique"):
        _build_report(
            _movement("move-update-dup", market_id="market-update-dup"),
            updates=(
                _update(
                    "update-dup",
                    market_id="market-update-dup",
                    source_family="official",
                    collected_at=BASE_DETECTED_AT + timedelta(minutes=1),
                ),
                _update(
                    "update-dup",
                    market_id="market-update-dup",
                    source_family="primary",
                    collected_at=BASE_DETECTED_AT + timedelta(minutes=2),
                ),
            ),
        )
    with pytest.raises(ValueError, match="category_id must match team_id"):
        _movement(
            "move-category",
            market_id="market-category",
            team_id="crypto_btc",
            category_id="politics",
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_update("update-flag", market_id="market-flag", source_family="official", collected_at=BASE_DETECTED_AT), paper_only=False)


def test_tampered_digest_and_nondeterministic_rollups_are_rejected() -> None:
    report = _scenario_report()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="deterministic sorting"):
        replace(
            report,
            stale_source_reason_rollups=tuple(
                reversed(report.stale_source_reason_rollups),
            ),
        )
    with pytest.raises(ValueError, match="deterministic sorting"):
        replace(
            report,
            source_family_rollups=tuple(reversed(report.source_family_rollups)),
        )


def test_public_api_and_module_scope_stay_pure_phase_one_report_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_PACKET_PRIMARY_SOURCE_UPDATE_LATENCY_V2_CONFIG_VERSION",
        "ResearchPacketMarketProbabilityMovement",
        "ResearchPacketPrimarySourceUpdate",
        "ResearchPacketPrimarySourceUpdateLatencyConfig",
        "ResearchPacketPrimarySourceUpdateLatencyReasonRollup",
        "ResearchPacketPrimarySourceUpdateLatencyReport",
        "ResearchPacketPrimarySourceUpdateLatencyRow",
        "ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup",
        "build_research_packet_primary_source_update_latency_v2_report",
        "research_packet_primary_source_update_latency_v2_report_to_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    for cls in (
        module.ResearchPacketMarketProbabilityMovement,
        module.ResearchPacketPrimarySourceUpdate,
        module.ResearchPacketPrimarySourceUpdateLatencyConfig,
        module.ResearchPacketPrimarySourceUpdateLatencyReasonRollup,
        module.ResearchPacketPrimarySourceUpdateLatencyReport,
        module.ResearchPacketPrimarySourceUpdateLatencyRow,
        module.ResearchPacketPrimarySourceUpdateLatencySourceFamilyRollup,
    ):
        for field in fields(cls):
            assert field.name not in {"auth", "wallet", "account", "order"}

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "wallet",
        "account",
        "broker",
        "submit",
        "cancel",
        "private_key",
        "credential",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
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


def _int_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if type(value) is int:
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_int_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_int_paths(nested, child))
        return tuple(paths)
    return ()
