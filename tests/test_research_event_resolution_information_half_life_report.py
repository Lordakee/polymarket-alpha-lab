from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
BASE_LATEST_AT = datetime(2026, 7, 9, 11, 0, tzinfo=UTC)
BASE_DEADLINE_AT = datetime(2026, 7, 10, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_resolution_information_half_life_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    module = api()
    values = {
        "watch_age_to_half_life_ratio": d("0.500000"),
        "block_age_to_half_life_ratio": d("1.000000"),
        "minimum_independent_signal_count": d("2"),
        "contradiction_watch_threshold": d("0.300000"),
        "contradiction_block_threshold": d("0.700000"),
        "unresolved_claim_watch_threshold": d("2"),
        "unresolved_claim_block_threshold": d("4"),
        "deadline_watch_seconds": d("7200.000000"),
        "deadline_block_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionInformationHalfLifeConfig(**values)


def _observation(
    public_event_key: str,
    *,
    latest_information_at: datetime = BASE_LATEST_AT,
    resolution_deadline_at: datetime = BASE_DEADLINE_AT,
    information_half_life_seconds: Decimal = d("7200.000000"),
    independent_signal_count: Decimal = d("3"),
    contradiction_pressure: Decimal = d("0.050000"),
    unresolved_claim_count: Decimal = d("0"),
):
    module = api()
    return module.ResearchEventResolutionInformationHalfLifeObservation(
        public_event_key=public_event_key,
        latest_information_at=latest_information_at,
        resolution_deadline_at=resolution_deadline_at,
        information_half_life_seconds=information_half_life_seconds,
        independent_signal_count=independent_signal_count,
        contradiction_pressure=contradiction_pressure,
        unresolved_claim_count=unresolved_claim_count,
    )


def _build_report(*observations, config=None):
    module = api()
    return module.build_research_event_resolution_information_half_life_report(
        observations,
        config=_config() if config is None else config,
        generated_at=GENERATED_AT,
    )


def _scenario_report():
    return _build_report(
        _observation(
            "event-blocked",
            latest_information_at=GENERATED_AT - timedelta(hours=2),
            resolution_deadline_at=GENERATED_AT + timedelta(minutes=20),
            information_half_life_seconds=d("3600.000000"),
            independent_signal_count=d("1"),
            contradiction_pressure=d("0.800000"),
            unresolved_claim_count=d("4"),
        ),
        _observation(
            "event-watch",
            latest_information_at=GENERATED_AT - timedelta(minutes=50),
            resolution_deadline_at=GENERATED_AT + timedelta(hours=3),
            information_half_life_seconds=d("6000.000000"),
            independent_signal_count=d("2"),
            contradiction_pressure=d("0.400000"),
            unresolved_claim_count=d("0"),
        ),
        _observation(
            "event-pass",
            latest_information_at=GENERATED_AT - timedelta(minutes=10),
            resolution_deadline_at=GENERATED_AT + timedelta(days=1),
            information_half_life_seconds=d("7200.000000"),
            independent_signal_count=d("3"),
            contradiction_pressure=d("0.050000"),
            unresolved_claim_count=d("0"),
        ),
    )


def test_report_triages_expired_near_expiry_independence_conflict_and_deadline():
    report = _scenario_report()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.reason_codes == (
        "information_half_life_expired",
        "information_half_life_near_expiry",
        "information_half_life_low_independence",
        "information_half_life_contradiction_pressure",
        "information_half_life_unresolved_claim_pressure",
        "information_half_life_deadline_pressure",
    )
    assert report.event_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.half_life_pressure_count == d("2")
    assert report.low_independence_count == d("1")
    assert report.contradiction_pressure_count == d("2")
    assert report.unresolved_claim_pressure_count == d("1")
    assert report.deadline_pressure_count == d("1")
    assert report.min_half_life_remaining_seconds == d("0.000000")
    assert report.max_age_to_half_life_ratio == d("2.000000")
    assert report.average_half_life_remaining_seconds == d("3200.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    rows = {row.public_event_key: row for row in report.rows}
    blocked = rows["event-blocked"]
    assert blocked.status == "block"
    assert blocked.information_age_seconds == d("7200.000000")
    assert blocked.information_half_life_seconds == d("3600.000000")
    assert blocked.half_life_remaining_seconds == d("0.000000")
    assert blocked.age_to_half_life_ratio == d("2.000000")
    assert blocked.deadline_proximity_seconds == d("1200.000000")
    assert blocked.reason_codes == (
        "information_half_life_expired",
        "information_half_life_low_independence",
        "information_half_life_contradiction_pressure",
        "information_half_life_unresolved_claim_pressure",
        "information_half_life_deadline_pressure",
    )

    watched = rows["event-watch"]
    assert watched.status == "watch"
    assert watched.information_age_seconds == d("3000.000000")
    assert watched.half_life_remaining_seconds == d("3000.000000")
    assert watched.age_to_half_life_ratio == d("0.500000")
    assert watched.reason_codes == (
        "information_half_life_near_expiry",
        "information_half_life_contradiction_pressure",
    )

    passed = rows["event-pass"]
    assert passed.status == "pass"
    assert passed.information_age_seconds == d("600.000000")
    assert passed.half_life_remaining_seconds == d("6600.000000")
    assert passed.age_to_half_life_ratio == d("0.083333")
    assert passed.reason_codes == ("information_half_life_clear",)


def test_empty_report_and_payload_are_decimal_json_ready_and_digest_validated():
    module = api()

    report = _build_report()
    payload = module.research_event_resolution_information_half_life_report_to_payload(
        report,
    )

    assert report.status == "pass"
    assert report.reason_codes == ("information_half_life_empty",)
    assert report.event_count == d("0")
    assert report.min_half_life_remaining_seconds == d("0.000000")
    assert report.max_age_to_half_life_ratio == d("0.000000")
    assert report.average_half_life_remaining_seconds == d("0.000000")
    assert report.rows == ()
    assert len(report.derived_validation_digest) == 64
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["event_count"] == "0"
    assert payload["max_age_to_half_life_ratio"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert _float_paths(payload) == ()
    assert _int_paths(payload) == ()
    json.dumps(payload, sort_keys=True)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        bad_payload = {**payload, "event_count": "1"}
        module.validate_research_event_resolution_information_half_life_public_payload(
            bad_payload,
        )


def test_input_order_does_not_change_rows_or_digest():
    module = api()
    event_a = _observation(
        "event-a",
        latest_information_at=GENERATED_AT - timedelta(minutes=20),
        resolution_deadline_at=GENERATED_AT + timedelta(hours=6),
    )
    event_b = _observation(
        "event-b",
        latest_information_at=GENERATED_AT - timedelta(hours=2),
        resolution_deadline_at=GENERATED_AT + timedelta(minutes=10),
        information_half_life_seconds=d("3600.000000"),
        independent_signal_count=d("1"),
        contradiction_pressure=d("0.750000"),
        unresolved_claim_count=d("4"),
    )

    first = module.build_research_event_resolution_information_half_life_report(
        (event_a, event_b),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    second = module.build_research_event_resolution_information_half_life_report(
        (event_b, event_a),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert first == second
    assert first.derived_validation_digest == second.derived_validation_digest
    assert tuple(row.public_event_key for row in first.rows) == ("event-b", "event-a")


def test_dataclasses_flags_datetimes_and_decimal_only_inputs_are_enforced():
    module = api()
    report = _scenario_report()

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="information_half_life_seconds must be a Decimal"):
        _observation("event-int", information_half_life_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_pressure must be a Decimal"):
        _observation(
            "event-decimal-subclass",
            contradiction_pressure=_DecimalSubclass("0.5"),
        )
    with pytest.raises(ValueError, match="latest_information_at must be timezone-aware"):
        _observation(
            "event-naive",
            latest_information_at=datetime(2026, 7, 9, 10, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_resolution_information_half_life_report(
            (_observation("event-valid"),),
            config=_config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="latest_information_at must be <= generated_at"):
        _build_report(
            _observation(
                "event-future-update",
                latest_information_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="public_event_key values must be unique"):
        _build_report(
            _observation("event-dup"),
            _observation("event-dup", resolution_deadline_at=GENERATED_AT + timedelta(hours=4)),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation("event-flag"), paper_only=False)
    with pytest.raises(ValueError, match="deterministic sorting"):
        replace(report, rows=tuple(reversed(report.rows)))


def test_public_payload_hides_raw_surfaces_and_module_stays_report_only():
    module = api()
    payload = module.research_event_resolution_information_half_life_report_to_payload(
        _scenario_report(),
    )
    payload_text = json.dumps(payload, sort_keys=True)

    for forbidden in (
        "raw",
        "raw_id",
        "condition_id",
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

    with pytest.raises(ValueError, match="unsafe"):
        module.ResearchEventResolutionInformationHalfLifeObservation(
            public_event_key="market-slug-leak",
            latest_information_at=BASE_LATEST_AT,
            resolution_deadline_at=BASE_DEADLINE_AT,
            information_half_life_seconds=d("7200.000000"),
            independent_signal_count=d("3"),
            contradiction_pressure=d("0.050000"),
            unresolved_claim_count=d("0"),
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.ResearchEventResolutionInformationHalfLifeObservation(
            public_event_key="raw_id_leak",
            latest_information_at=BASE_LATEST_AT,
            resolution_deadline_at=BASE_DEADLINE_AT,
            information_half_life_seconds=d("7200.000000"),
            independent_signal_count=d("3"),
            contradiction_pressure=d("0.050000"),
            unresolved_claim_count=d("0"),
        )
    with pytest.raises(ValueError, match="public readonly schema"):
        module.validate_research_event_resolution_information_half_life_public_payload(
            {**payload, "source_url": "redacted"},
        )

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_INFORMATION_HALF_LIFE_REPORT_CONFIG_VERSION",
        "ResearchEventResolutionInformationHalfLifeConfig",
        "ResearchEventResolutionInformationHalfLifeObservation",
        "ResearchEventResolutionInformationHalfLifeReport",
        "ResearchEventResolutionInformationHalfLifeRow",
        "build_research_event_resolution_information_half_life_report",
        "research_event_resolution_information_half_life_report_to_payload",
        "validate_research_event_resolution_information_half_life_public_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    for cls in (
        module.ResearchEventResolutionInformationHalfLifeConfig,
        module.ResearchEventResolutionInformationHalfLifeObservation,
        module.ResearchEventResolutionInformationHalfLifeReport,
        module.ResearchEventResolutionInformationHalfLifeRow,
    ):
        for field in fields(cls):
            assert field.name not in {
                "candidate_id",
                "market_id",
                "market_slug",
                "question",
                "source_url",
                "source_text",
                "dsn",
                "table_name",
                "token",
                "wallet",
                "order",
                "trade",
                "size",
                "recommendation",
            }

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
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
