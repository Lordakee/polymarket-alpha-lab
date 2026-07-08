from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
BASE_VERIFIED_AT = datetime(2026, 7, 7, 10, 0, tzinfo=UTC)
BASE_DEADLINE_AT = datetime(2026, 7, 7, 13, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_resolution_update_latency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    values = {
        "expected_cadence_seconds": d("1800.000000"),
        "watch_latency_multiplier": d("1.500000"),
        "block_latency_multiplier": d("3.000000"),
        "authoritative_source_threshold": d("0.700000"),
        "contradiction_watch_threshold": d("0.300000"),
        "contradiction_block_threshold": d("0.700000"),
        "ambiguity_watch_threshold": d("0.300000"),
        "ambiguity_block_threshold": d("0.700000"),
        "deadline_watch_seconds": d("7200.000000"),
        "deadline_block_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionUpdateLatencyConfig(**values)


def _observation(
    public_event_key: str,
    *,
    last_verified_update_at: datetime = BASE_VERIFIED_AT,
    deadline_at: datetime = BASE_DEADLINE_AT,
    expected_cadence_seconds: Decimal | None = None,
    source_authority_score: Decimal = d("0.900000"),
    contradiction_pressure: Decimal = d("0.100000"),
    ambiguity_risk: Decimal = d("0.100000"),
):
    module = api()
    return module.ResearchEventResolutionUpdateLatencyObservation(
        public_event_key=public_event_key,
        last_verified_update_at=last_verified_update_at,
        deadline_at=deadline_at,
        expected_cadence_seconds=expected_cadence_seconds,
        source_authority_score=source_authority_score,
        contradiction_pressure=contradiction_pressure,
        ambiguity_risk=ambiguity_risk,
    )


def _build_report(*observations, config=None):
    module = api()
    return module.build_research_event_resolution_update_latency_report(
        observations,
        config=_config() if config is None else config,
        generated_at=GENERATED_AT,
    )


def _scenario_report():
    return _build_report(
        _observation(
            "event-blocked",
            last_verified_update_at=GENERATED_AT - timedelta(hours=2),
            deadline_at=GENERATED_AT + timedelta(minutes=20),
            source_authority_score=d("0.600000"),
            contradiction_pressure=d("0.800000"),
            ambiguity_risk=d("0.750000"),
        ),
        _observation(
            "event-watch",
            last_verified_update_at=GENERATED_AT - timedelta(minutes=50),
            deadline_at=GENERATED_AT + timedelta(hours=3),
            source_authority_score=d("0.800000"),
            contradiction_pressure=d("0.400000"),
            ambiguity_risk=d("0.200000"),
        ),
        _observation(
            "event-pass",
            last_verified_update_at=GENERATED_AT - timedelta(minutes=10),
            deadline_at=GENERATED_AT + timedelta(days=1),
            source_authority_score=d("0.950000"),
            contradiction_pressure=d("0.050000"),
            ambiguity_risk=d("0.050000"),
        ),
    )


def test_report_triages_latency_authority_contradiction_ambiguity_and_deadline() -> None:
    report = _scenario_report()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.reason_codes == (
        "resolution_update_stale",
        "resolution_update_low_authority",
        "resolution_update_contradiction_pressure",
        "resolution_update_ambiguity_risk",
        "resolution_update_deadline_near",
    )
    assert report.event_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.stale_count == d("2")
    assert report.low_authority_count == d("1")
    assert report.contradiction_pressure_count == d("2")
    assert report.ambiguity_risk_count == d("1")
    assert report.deadline_pressure_count == d("1")
    assert report.max_last_verified_update_age_seconds == d("7200.000000")
    assert report.average_last_verified_update_age_seconds == d("3600.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    rows = {row.public_event_key: row for row in report.rows}
    blocked = rows["event-blocked"]
    assert blocked.status == "block"
    assert blocked.expected_cadence_seconds == d("1800.000000")
    assert blocked.last_verified_update_age_seconds == d("7200.000000")
    assert blocked.deadline_proximity_seconds == d("1200.000000")
    assert blocked.source_authority_score == d("0.600000")
    assert blocked.contradiction_pressure == d("0.800000")
    assert blocked.ambiguity_risk == d("0.750000")
    assert blocked.reason_codes == (
        "resolution_update_stale",
        "resolution_update_low_authority",
        "resolution_update_contradiction_pressure",
        "resolution_update_ambiguity_risk",
        "resolution_update_deadline_near",
    )

    watch = rows["event-watch"]
    assert watch.status == "watch"
    assert watch.last_verified_update_age_seconds == d("3000.000000")
    assert watch.deadline_proximity_seconds == d("10800.000000")
    assert watch.reason_codes == (
        "resolution_update_stale",
        "resolution_update_contradiction_pressure",
    )

    passed = rows["event-pass"]
    assert passed.status == "pass"
    assert passed.last_verified_update_age_seconds == d("600.000000")
    assert passed.deadline_proximity_seconds == d("86400.000000")
    assert passed.reason_codes == ("resolution_update_latency_clear",)


def test_empty_report_and_payload_are_decimal_json_ready_and_digest_validated() -> None:
    module = api()

    report = _build_report()
    payload = module.research_event_resolution_update_latency_report_to_payload(report)

    assert report.status == "pass"
    assert report.reason_codes == ("resolution_update_latency_empty",)
    assert report.event_count == d("0")
    assert report.max_last_verified_update_age_seconds == d("0.000000")
    assert report.average_last_verified_update_age_seconds == d("0.000000")
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["event_count"] == "0"
    assert payload["max_last_verified_update_age_seconds"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert _float_paths(payload) == ()
    assert _int_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_input_order_does_not_change_rows_or_digest() -> None:
    module = api()
    event_a = _observation(
        "event-a",
        last_verified_update_at=GENERATED_AT - timedelta(minutes=20),
        deadline_at=GENERATED_AT + timedelta(hours=6),
    )
    event_b = _observation(
        "event-b",
        last_verified_update_at=GENERATED_AT - timedelta(hours=2),
        deadline_at=GENERATED_AT + timedelta(minutes=10),
        source_authority_score=d("0.500000"),
        contradiction_pressure=d("0.750000"),
        ambiguity_risk=d("0.200000"),
    )

    first = module.build_research_event_resolution_update_latency_report(
        (event_a, event_b),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    second = module.build_research_event_resolution_update_latency_report(
        (event_b, event_a),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert tuple(row.public_event_key for row in first.rows) == ("event-b", "event-a")


def test_dataclasses_flags_datetimes_and_decimal_only_inputs_are_enforced() -> None:
    module = api()
    report = _scenario_report()

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="expected_cadence_seconds must be a Decimal"):
        module.ResearchEventResolutionUpdateLatencyConfig(
            expected_cadence_seconds=1800,
        )
    with pytest.raises(ValueError, match="source_authority_score must be a Decimal"):
        _observation("event-decimal-subclass", source_authority_score=_DecimalSubclass("0.5"))
    with pytest.raises(ValueError, match="last_verified_update_at must be timezone-aware"):
        _observation(
            "event-naive",
            last_verified_update_at=datetime(2026, 7, 7, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_resolution_update_latency_report(
            (_observation("event-valid"),),
            config=_config(),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="last_verified_update_at must be <= generated_at"):
        _build_report(
            _observation(
                "event-future-update",
                last_verified_update_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="public_event_key values must be unique"):
        _build_report(
            _observation("event-dup"),
            _observation("event-dup", deadline_at=GENERATED_AT + timedelta(hours=4)),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation("event-flag"), paper_only=False)


def test_tampered_digest_and_nondeterministic_rows_are_rejected() -> None:
    report = _scenario_report()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="deterministic sorting"):
        replace(report, rows=tuple(reversed(report.rows)))


def test_public_payload_hides_raw_surfaces_and_module_stays_report_only() -> None:
    module = api()
    payload = module.research_event_resolution_update_latency_report_to_payload(
        _scenario_report(),
    )
    payload_text = json.dumps(payload, sort_keys=True)

    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert forbidden not in payload_text.lower()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_UPDATE_LATENCY_REPORT_CONFIG_VERSION",
        "ResearchEventResolutionUpdateLatencyConfig",
        "ResearchEventResolutionUpdateLatencyObservation",
        "ResearchEventResolutionUpdateLatencyReport",
        "ResearchEventResolutionUpdateLatencyRow",
        "build_research_event_resolution_update_latency_report",
        "research_event_resolution_update_latency_report_to_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    for cls in (
        module.ResearchEventResolutionUpdateLatencyConfig,
        module.ResearchEventResolutionUpdateLatencyObservation,
        module.ResearchEventResolutionUpdateLatencyReport,
        module.ResearchEventResolutionUpdateLatencyRow,
    ):
        for field in fields(cls):
            assert field.name not in {
                "candidate_id",
                "market_id",
                "market_slug",
                "question",
                "url",
                "text",
                "dsn",
                "table_name",
                "token",
                "wallet",
                "order",
                "trade",
            }

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "wallet",
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
