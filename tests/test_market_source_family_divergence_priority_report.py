from __future__ import annotations

import ast
import importlib.util
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from typing import Any, get_args, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_source_family_divergence_priority_report"
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
    market_id: str,
    category_id: str,
    source_family: str,
    probability: Decimal,
    *,
    source_updated_at: datetime,
) -> object:
    return _api().MarketSourceFamilyDivergencePriorityInputRow(
        market_id=market_id,
        category_id=category_id,
        source_family=source_family,
        probability=probability,
        source_updated_at=source_updated_at,
    )


def _market_rows(
    market_id: str,
    category_id: str,
    probabilities: dict[str, str],
    *,
    age_seconds: dict[str, int] | None = None,
) -> tuple[object, ...]:
    ages = age_seconds or {}
    return tuple(
        _input_row(
            market_id,
            category_id,
            source_family,
            d(probability),
            source_updated_at=GENERATED_AT
            - timedelta(seconds=ages.get(source_family, 600)),
        )
        for source_family, probability in probabilities.items()
    )


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_PRIORITY_REPORT_CONFIG_VERSION
        ),
        "watch_probability_delta": d("0.050000"),
        "blocked_probability_delta": d("0.150000"),
        "stale_source_family_seconds": d("3600.000000"),
        "concentration_watch_ratio": d("0.500000"),
        "concentration_blocked_ratio": d("0.750000"),
        "expected_source_family_count": d("4.000000"),
    }
    values.update(overrides)
    return api.MarketSourceFamilyDivergencePriorityConfig(**values)


def _report(*rows: object, **config_overrides: object) -> object:
    return _api().build_market_source_family_divergence_priority_report(
        rows,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_module_import_surface_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_empty_input_report_is_clear_decimal_only_and_deterministic() -> None:
    api = _api()

    report = _report()

    assert type(report) is api.MarketSourceFamilyDivergencePriorityReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_PRIORITY_REPORT_CONFIG_VERSION
    )
    assert report.report_status == "clear"
    assert report.reason_codes == (
        "market_source_family_divergence_priority_clear",
    )
    assert report.market_count == d("0.000000")
    assert report.source_family_count == d("0.000000")
    assert report.priority_market_count == d("0.000000")
    assert report.priority_market_ratio == d("0.000000")
    assert report.max_probability_delta == d("0.000000")
    assert report.max_source_age_seconds == d("0.000000")
    assert report.max_category_pressure_ratio == d("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = api.market_source_family_divergence_priority_report_to_payload(report)
    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["market_count"] == "0.000000"
    assert payload["max_probability_delta"] == "0.000000"
    assert payload["rows"] == []


def test_priority_report_ranks_rows_by_delta_age_concentration_missing_and_ties() -> None:
    report = _report(
        *_market_rows(
            "market-beta",
            "politics",
            {
                "official": "0.700000",
                "primary": "0.500000",
                "proxy": "0.510000",
                "team_acknowledged": "0.690000",
            },
            age_seconds={"official": 7200, "primary": 1800, "proxy": 600},
        ),
        *_market_rows(
            "market-alpha",
            "politics",
            {
                "official": "0.700000",
                "primary": "0.500000",
                "proxy": "0.510000",
                "team_acknowledged": "0.690000",
            },
            age_seconds={"official": 14400, "primary": 1800, "proxy": 600},
        ),
        *_market_rows(
            "market-gamma",
            "politics",
            {
                "official": "0.600000",
                "primary": "0.500000",
                "proxy": "0.510000",
            },
            age_seconds={"official": 7200, "primary": 1800, "proxy": 600},
        ),
        *_market_rows(
            "market-delta",
            "weather",
            {
                "official": "0.600000",
                "primary": "0.500000",
                "proxy": "0.510000",
            },
            age_seconds={"official": 7200, "primary": 1800, "proxy": 600},
        ),
        *_market_rows(
            "market-clear",
            "weather",
            {
                "official": "0.520000",
                "primary": "0.510000",
                "proxy": "0.500000",
                "team_acknowledged": "0.515000",
            },
            age_seconds={"official": 1200, "primary": 900, "proxy": 600},
        ),
    )

    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "market_source_family_divergence_priority_delta_blocked",
        "market_source_family_divergence_priority_delta_watch",
        "market_source_family_divergence_priority_stale_source_age",
        "market_source_family_divergence_priority_concentration_blocked",
        "market_source_family_divergence_priority_missing_family_coverage",
    )
    assert report.market_count == d("5.000000")
    assert report.priority_market_count == d("4.000000")
    assert report.divergent_market_count == d("4.000000")
    assert report.stale_market_count == d("4.000000")
    assert report.concentrated_market_count == d("3.000000")
    assert report.missing_family_market_count == d("2.000000")
    assert report.priority_market_ratio == d("0.800000")
    assert report.max_probability_delta == d("0.200000")
    assert report.max_source_age_seconds == d("14400.000000")
    assert report.max_category_pressure_ratio == d("0.750000")

    assert tuple(row.market_id for row in report.rows) == (
        "market-alpha",
        "market-beta",
        "market-gamma",
        "market-delta",
        "market-clear",
    )
    assert tuple(row.priority_rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
        d("4.000000"),
        d("5.000000"),
    )

    top = report.rows[0]
    assert top.priority_status == "blocked"
    assert top.max_probability_delta == d("0.200000")
    assert top.max_source_age_seconds == d("14400.000000")
    assert top.category_pressure_count == d("3.000000")
    assert top.category_pressure_ratio == d("0.750000")
    assert top.missing_source_family_count == d("0.000000")
    assert top.reason_codes == (
        "market_source_family_divergence_priority_delta_blocked",
        "market_source_family_divergence_priority_stale_source_age",
        "market_source_family_divergence_priority_concentration_blocked",
    )

    concentrated_missing = report.rows[2]
    assert concentrated_missing.market_id == "market-gamma"
    assert concentrated_missing.priority_status == "blocked"
    assert concentrated_missing.max_probability_delta == d("0.100000")
    assert concentrated_missing.category_pressure_ratio == d("0.750000")
    assert concentrated_missing.missing_source_family_count == d("1.000000")
    assert concentrated_missing.reason_codes == (
        "market_source_family_divergence_priority_delta_watch",
        "market_source_family_divergence_priority_stale_source_age",
        "market_source_family_divergence_priority_concentration_blocked",
        "market_source_family_divergence_priority_missing_family_coverage",
    )

    tie_broken_after_concentration = report.rows[3]
    assert tie_broken_after_concentration.market_id == "market-delta"
    assert tie_broken_after_concentration.priority_status == "watch"
    assert tie_broken_after_concentration.category_pressure_ratio == d("0.250000")

    clear = report.rows[-1]
    assert clear.priority_status == "clear"
    assert clear.reason_codes == (
        "market_source_family_divergence_priority_clear",
    )


def test_threshold_statuses_and_reason_codes_are_deterministic() -> None:
    report = _report(
        *_market_rows(
            "market-block-threshold",
            "politics",
            {
                "official": "0.650000",
                "primary": "0.500000",
                "proxy": "0.500000",
                "team_acknowledged": "0.500000",
            },
            age_seconds={"official": 3600, "primary": 600, "proxy": 600},
        ),
        *_market_rows(
            "market-watch-threshold",
            "sports",
            {
                "official": "0.550000",
                "primary": "0.500000",
                "proxy": "0.500000",
                "team_acknowledged": "0.500000",
            },
            age_seconds={"official": 3600, "primary": 600, "proxy": 600},
        ),
        *_market_rows(
            "market-stale",
            "weather",
            {
                "official": "0.520000",
                "primary": "0.500000",
                "proxy": "0.510000",
                "team_acknowledged": "0.515000",
            },
            age_seconds={"official": 3601, "primary": 600, "proxy": 600},
        ),
        *_market_rows(
            "market-missing",
            "macro",
            {
                "official": "0.520000",
                "primary": "0.500000",
                "proxy": "0.510000",
            },
            age_seconds={"official": 600, "primary": 600, "proxy": 600},
        ),
        concentration_watch_ratio=d("0.900000"),
        concentration_blocked_ratio=d("1.000000"),
    )

    by_market = {row.market_id: row for row in report.rows}
    assert by_market["market-block-threshold"].priority_status == "blocked"
    assert by_market["market-block-threshold"].reason_codes == (
        "market_source_family_divergence_priority_delta_blocked",
    )
    assert by_market["market-watch-threshold"].priority_status == "watch"
    assert by_market["market-watch-threshold"].reason_codes == (
        "market_source_family_divergence_priority_delta_watch",
    )
    assert by_market["market-stale"].priority_status == "watch"
    assert by_market["market-stale"].reason_codes == (
        "market_source_family_divergence_priority_stale_source_age",
    )
    assert by_market["market-missing"].priority_status == "watch"
    assert by_market["market-missing"].reason_codes == (
        "market_source_family_divergence_priority_missing_family_coverage",
    )
    assert report.reason_codes == (
        "market_source_family_divergence_priority_delta_blocked",
        "market_source_family_divergence_priority_delta_watch",
        "market_source_family_divergence_priority_stale_source_age",
        "market_source_family_divergence_priority_missing_family_coverage",
    )


def test_utc_decimal_and_frozen_contracts_are_enforced() -> None:
    api = _api()
    contract_classes = (
        api.MarketSourceFamilyDivergencePriorityConfig,
        api.MarketSourceFamilyDivergencePriorityInputRow,
        api.MarketSourceFamilyDivergencePriorityRow,
        api.MarketSourceFamilyDivergencePriorityReport,
    )
    for contract_class in contract_classes:
        assert is_dataclass(contract_class)
        assert contract_class.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        hints = get_type_hints(contract_class)
        for field_name, hint in hints.items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            assert not _type_uses_float(hint)
            if _is_public_numeric_field(field_name):
                assert hint is Decimal or hint == Decimal | None

    row = _input_row(
        "market-frozen",
        "weather",
        "official",
        d("0.500000"),
        source_updated_at=_at(minutes=5),
    )
    with pytest.raises(FrozenInstanceError):
        row.probability = d("0.600000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="watch_probability_delta"):
        api.MarketSourceFamilyDivergencePriorityConfig(
            watch_probability_delta=0.05,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        api.MarketSourceFamilyDivergencePriorityInputRow(
            market_id="market-naive",
            category_id="weather",
            source_family="official",
            probability=d("0.500000"),
            source_updated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_market_source_family_divergence_priority_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="source_updated_at"):
        _report(
            _input_row(
                "market-future",
                "weather",
                "official",
                d("0.500000"),
                source_updated_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="probability"):
        _input_row(
            "market-float",
            "weather",
            "official",
            0.5,  # type: ignore[arg-type]
            source_updated_at=_at(minutes=5),
        )
    with pytest.raises(ValueError, match="probability"):
        _input_row(
            "market-negative-rounds-to-zero",
            "weather",
            "official",
            d("-0.0000001"),
            source_updated_at=_at(minutes=5),
        )
    with pytest.raises(ValueError, match="source_family"):
        _input_row(
            "market-family",
            "weather",
            "community",
            d("0.500000"),
            source_updated_at=_at(minutes=5),
        )
    with pytest.raises(ValueError, match="market_id"):
        _input_row(
            _join_parts("wal", "let"),
            "weather",
            "official",
            d("0.500000"),
            source_updated_at=_at(minutes=5),
        )
    with pytest.raises(ValueError, match="unique"):
        _report(
            _input_row(
                "market-duplicate",
                "weather",
                "official",
                d("0.500000"),
                source_updated_at=_at(minutes=5),
            ),
            _input_row(
                "market-duplicate",
                "weather",
                "official",
                d("0.600000"),
                source_updated_at=_at(minutes=4),
            ),
        )
    with pytest.raises(ValueError, match="category_id"):
        _report(
            _input_row(
                "market-category-a",
                "weather",
                "official",
                d("0.500000"),
                source_updated_at=_at(minutes=5),
            ),
            _input_row(
                "market-category-a",
                "politics",
                "proxy",
                d("0.500000"),
                source_updated_at=_at(minutes=4),
            ),
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)


def test_payload_helper_uses_decimal_strings_and_utc_iso_datetimes() -> None:
    offset = timezone(timedelta(hours=-4))
    api = _api()

    report = api.build_market_source_family_divergence_priority_report(
        (
            api.MarketSourceFamilyDivergencePriorityInputRow(
                market_id="market-offset",
                category_id="weather",
                source_family="official",
                probability=d("0.580000"),
                source_updated_at=datetime(2026, 7, 2, 7, 30, tzinfo=offset),
            ),
            api.MarketSourceFamilyDivergencePriorityInputRow(
                market_id="market-offset",
                category_id="weather",
                source_family="primary",
                probability=d("0.500000"),
                source_updated_at=datetime(2026, 7, 2, 7, 40, tzinfo=offset),
            ),
            api.MarketSourceFamilyDivergencePriorityInputRow(
                market_id="market-offset",
                category_id="weather",
                source_family="proxy",
                probability=d("0.510000"),
                source_updated_at=datetime(2026, 7, 2, 7, 45, tzinfo=offset),
            ),
            api.MarketSourceFamilyDivergencePriorityInputRow(
                market_id="market-offset",
                category_id="weather",
                source_family="team_acknowledged",
                probability=d("0.515000"),
                source_updated_at=datetime(2026, 7, 2, 7, 50, tzinfo=offset),
            ),
        ),
        config=_config(
            concentration_watch_ratio=d("0.900000"),
            concentration_blocked_ratio=d("1.000000"),
        ),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=offset),
    )

    payload = api.market_source_family_divergence_priority_report_to_payload(report)

    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["max_probability_delta"] == "0.080000"
    assert payload["priority_market_ratio"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["market_id"] == "market-offset"
    assert payload["rows"][0]["priority_rank"] == "1.000000"
    assert payload["rows"][0]["official_probability"] == "0.580000"
    assert payload["rows"][0]["max_source_age_seconds"] == "1800.000000"

    with pytest.raises(ValueError, match="report must be"):
        api.market_source_family_divergence_priority_report_to_payload(object())


def test_module_is_pure_in_memory_report_only_surface() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert api.__all__ == (
        "DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_PRIORITY_REPORT_CONFIG_VERSION",
        "MarketSourceFamilyDivergencePriorityConfig",
        "MarketSourceFamilyDivergencePriorityInputRow",
        "MarketSourceFamilyDivergencePriorityReport",
        "MarketSourceFamilyDivergencePriorityRow",
        "build_market_source_family_divergence_priority_report",
        "market_source_family_divergence_priority_report_to_payload",
    )
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
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
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


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name == "probability"
        or field_name.endswith("_count")
        or field_name.endswith("_ratio")
        or field_name.endswith("_seconds")
        or field_name.endswith("_delta")
        or field_name.endswith("_probability")
        or field_name == "priority_rank"
    )
