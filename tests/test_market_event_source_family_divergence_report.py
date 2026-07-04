from __future__ import annotations

import ast
import importlib.util
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
from typing import Any, get_args, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_event_source_family_divergence_report"
GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _api() -> Any:
    return import_module(MODULE_NAME)


def _at(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def _input_row(
    event_id: str,
    source_family: str,
    event_state: str,
    *,
    source_observed_at: datetime,
) -> object:
    return _api().MarketEventSourceFamilyDivergenceInputRow(
        event_id=event_id,
        source_family=source_family,
        event_state=event_state,
        source_observed_at=source_observed_at,
    )


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_MARKET_EVENT_SOURCE_FAMILY_DIVERGENCE_REPORT_CONFIG_VERSION
        ),
        "stale_source_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return api.MarketEventSourceFamilyDivergenceConfig(**values)


def _report(*rows: object, **config_overrides: object) -> object:
    return _api().build_market_event_source_family_divergence_report(
        rows,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_module_import_surface_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_build_report_flags_divergence_stale_sources_and_missing_acknowledgement() -> None:
    api = _api()

    report = _report(
        _input_row(
            "event-clear",
            "official",
            "open",
            source_observed_at=_at(minutes=40),
        ),
        _input_row(
            "event-clear",
            "primary",
            "open",
            source_observed_at=_at(minutes=35),
        ),
        _input_row(
            "event-clear",
            "proxy",
            "open",
            source_observed_at=_at(minutes=30),
        ),
        _input_row(
            "event-clear",
            "team_acknowledged",
            "open",
            source_observed_at=_at(minutes=20),
        ),
        _input_row(
            "event-ack-divergent",
            "official",
            "open",
            source_observed_at=_at(minutes=20),
        ),
        _input_row(
            "event-ack-divergent",
            "primary",
            "closed",
            source_observed_at=_at(minutes=15),
        ),
        _input_row(
            "event-ack-divergent",
            "proxy",
            "open",
            source_observed_at=_at(minutes=10),
        ),
        _input_row(
            "event-ack-divergent",
            "team_acknowledged",
            "open",
            source_observed_at=_at(minutes=5),
        ),
        _input_row(
            "event-missing-ack",
            "official",
            "resolved_yes",
            source_observed_at=_at(hours=4),
        ),
        _input_row(
            "event-missing-ack",
            "primary",
            "resolved_yes",
            source_observed_at=_at(hours=2),
        ),
        _input_row(
            "event-missing-ack",
            "proxy",
            "resolved_no",
            source_observed_at=_at(hours=1),
        ),
    )

    assert type(report) is api.MarketEventSourceFamilyDivergenceReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_MARKET_EVENT_SOURCE_FAMILY_DIVERGENCE_REPORT_CONFIG_VERSION
    )
    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "market_event_source_family_state_divergence",
        "market_event_source_family_stale",
        "market_event_source_family_acknowledgement_missing",
    )
    assert report.event_count == d("3.000000")
    assert report.source_family_count == d("11.000000")
    assert report.clear_event_count == d("1.000000")
    assert report.watch_event_count == d("1.000000")
    assert report.blocked_event_count == d("1.000000")
    assert report.pressure_event_count == d("2.000000")
    assert report.divergent_event_count == d("2.000000")
    assert report.stale_event_count == d("1.000000")
    assert report.missing_acknowledgement_event_count == d("1.000000")
    assert report.stale_source_family_count == d("2.000000")
    assert report.divergence_ratio == d("0.666667")
    assert report.stale_source_ratio == d("0.181818")
    assert report.max_source_age_seconds == d("14400.000000")
    assert tuple(row.event_id for row in report.rows) == (
        "event-missing-ack",
        "event-ack-divergent",
        "event-clear",
    )

    missing_ack = report.rows[0]
    assert missing_ack.pressure_status == "blocked"
    assert missing_ack.official_state == "resolved_yes"
    assert missing_ack.primary_state == "resolved_yes"
    assert missing_ack.proxy_state == "resolved_no"
    assert missing_ack.team_acknowledged_state is None
    assert missing_ack.source_family_count == d("3.000000")
    assert missing_ack.divergent_source_family_count == d("1.000000")
    assert missing_ack.stale_source_family_count == d("2.000000")
    assert missing_ack.missing_acknowledgement_count == d("1.000000")
    assert missing_ack.divergence_ratio == d("0.333333")
    assert missing_ack.max_source_age_seconds == d("14400.000000")
    assert missing_ack.reason_codes == (
        "market_event_source_family_state_divergence",
        "market_event_source_family_stale",
        "market_event_source_family_acknowledgement_missing",
    )

    acknowledged = report.rows[1]
    assert acknowledged.pressure_status == "watch"
    assert acknowledged.divergent_source_family_count == d("1.000000")
    assert acknowledged.missing_acknowledgement_count == d("0.000000")
    assert acknowledged.reason_codes == (
        "market_event_source_family_state_divergence",
    )

    clear = report.rows[2]
    assert clear.pressure_status == "clear"
    assert clear.reason_codes == ("market_event_source_family_divergence_clear",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_is_clear_and_deterministic() -> None:
    report = _report()

    assert report.report_status == "clear"
    assert report.reason_codes == ("market_event_source_family_divergence_clear",)
    assert report.event_count == d("0.000000")
    assert report.source_family_count == d("0.000000")
    assert report.pressure_event_count == d("0.000000")
    assert report.divergence_ratio == d("0.000000")
    assert report.stale_source_ratio == d("0.000000")
    assert report.max_source_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_helper_is_json_ready_without_float_values_and_uses_utc_strings() -> None:
    offset = timezone(timedelta(hours=-4))
    api = _api()
    report = api.build_market_event_source_family_divergence_report(
        (
            api.MarketEventSourceFamilyDivergenceInputRow(
                event_id="event-offset",
                source_family="official",
                event_state="open",
                source_observed_at=datetime(2026, 7, 2, 7, 30, tzinfo=offset),
            ),
            api.MarketEventSourceFamilyDivergenceInputRow(
                event_id="event-offset",
                source_family="primary",
                event_state="open",
                source_observed_at=datetime(2026, 7, 2, 7, 40, tzinfo=offset),
            ),
            api.MarketEventSourceFamilyDivergenceInputRow(
                event_id="event-offset",
                source_family="proxy",
                event_state="open",
                source_observed_at=datetime(2026, 7, 2, 7, 45, tzinfo=offset),
            ),
            api.MarketEventSourceFamilyDivergenceInputRow(
                event_id="event-offset",
                source_family="team_acknowledged",
                event_state="open",
                source_observed_at=datetime(2026, 7, 2, 7, 50, tzinfo=offset),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=offset),
    )

    payload = api.market_event_source_family_divergence_report_to_payload(report)

    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["event_count"] == "1.000000"
    assert payload["divergence_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["event_id"] == "event-offset"
    assert payload["rows"][0]["max_source_age_seconds"] == "1800.000000"

    with pytest.raises(ValueError, match="report must be"):
        api.market_event_source_family_divergence_report_to_payload(object())


def test_public_dataclasses_are_frozen_decimal_only_and_validate_times_and_flags() -> None:
    api = _api()
    contract_classes = (
        api.MarketEventSourceFamilyDivergenceConfig,
        api.MarketEventSourceFamilyDivergenceInputRow,
        api.MarketEventSourceFamilyDivergenceRow,
        api.MarketEventSourceFamilyDivergenceReport,
    )
    for contract_class in contract_classes:
        assert is_dataclass(contract_class)
        assert contract_class.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        for field_name, hint in get_type_hints(contract_class).items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            assert not _type_uses_float(hint)

    row = _input_row(
        "event-frozen",
        "official",
        "open",
        source_observed_at=_at(minutes=5),
    )
    with pytest.raises(FrozenInstanceError):
        row.event_state = "closed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="stale_source_seconds"):
        api.MarketEventSourceFamilyDivergenceConfig(
            stale_source_seconds=3600,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        api.MarketEventSourceFamilyDivergenceInputRow(
            event_id="event-naive",
            source_family="official",
            event_state="open",
            source_observed_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="concrete UTC offset"):
        api.MarketEventSourceFamilyDivergenceInputRow(
            event_id="event-none-offset",
            source_family="official",
            event_state="open",
            source_observed_at=datetime(
                2026,
                7,
                2,
                12,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_market_event_source_family_divergence_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="source_observed_at"):
        _report(
            _input_row(
                "event-future",
                "official",
                "open",
                source_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="source_family"):
        _input_row(
            "event-family",
            "community",
            "open",
            source_observed_at=_at(minutes=5),
        )
    with pytest.raises(ValueError, match="event_id"):
        _input_row(
            _join_parts("wal", "let"),
            "official",
            "open",
            source_observed_at=_at(minutes=5),
        )
    with pytest.raises(ValueError, match="unique"):
        _report(
            _input_row(
                "event-duplicate",
                "official",
                "open",
                source_observed_at=_at(minutes=5),
            ),
            _input_row(
                "event-duplicate",
                "official",
                "closed",
                source_observed_at=_at(minutes=4),
            ),
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)


def test_module_is_pure_in_memory_report_only_surface() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert ".total_seconds(" not in source
    assert "float(" not in source
    for banned in (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ):
        assert banned not in source
        assert all(banned not in name.lower() for name in public_names)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "buy",
                "connect",
                "execute",
                "executemany",
                "open",
                "patch",
                "place",
                "post",
                "put",
                "request",
                "sell",
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


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _type_uses_float(value: object) -> bool:
    if value is float:
        return True
    return any(_type_uses_float(item) for item in get_args(value))


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, value: datetime | None) -> None:
        return None

    def dst(self, value: datetime | None) -> None:
        return None
