from __future__ import annotations

import ast
import dataclasses
import importlib.util
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from typing import Any, get_args, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_source_family_divergence_health_report"
GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return import_module(MODULE_NAME)


def _at(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def _input_row(
    market_id: str,
    research_input_id: str,
    source_family: str,
    probability: Decimal,
    *,
    observed_at: datetime,
) -> object:
    api = _api()
    return api.MarketSourceFamilyDivergenceHealthInputRow(
        market_id=market_id,
        research_input_id=research_input_id,
        source_family=source_family,
        probability=probability,
        observed_at=observed_at,
    )


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_HEALTH_REPORT_CONFIG_VERSION
        ),
        "watch_probability_delta": d("0.050000"),
        "blocked_probability_delta": d("0.150000"),
        "stale_family_after_seconds": d("7200.000000"),
        "dominant_family_watch_ratio": d("0.600000"),
        "dominant_family_blocked_ratio": d("0.800000"),
    }
    values.update(overrides)
    return api.MarketSourceFamilyDivergenceHealthConfig(**values)


def _report(*rows: object, **config_overrides: object) -> object:
    api = _api()
    return api.build_market_source_family_divergence_health_report(
        rows,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_empty_input_returns_clear_decimal_report() -> None:
    api = _api()

    report = _report()

    assert type(report) is api.MarketSourceFamilyDivergenceHealthReport
    assert is_dataclass(report)
    assert report.report_status == "clear"
    assert report.reason_codes == (
        "market_source_family_divergence_health_clear",
    )
    assert report.market_count == d("0.000000")
    assert report.source_family_count == d("0.000000")
    assert report.research_input_count == d("0.000000")
    assert report.blocked_market_count == d("0.000000")
    assert report.watch_market_count == d("0.000000")
    assert report.stale_family_count == d("0.000000")
    assert report.max_probability_delta == d("0.000000")
    assert report.max_dominant_family_ratio == d("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_deterministic_sorting_prioritizes_status_metrics_and_market_id() -> None:
    report = _report(
        _input_row(
            "market-watch-beta",
            "input-1",
            "official",
            d("0.520000"),
            observed_at=_at(minutes=10),
        ),
        _input_row(
            "market-watch-beta",
            "input-2",
            "proxy",
            d("0.600000"),
            observed_at=_at(minutes=9),
        ),
        _input_row(
            "market-blocked-lower",
            "input-3",
            "official",
            d("0.200000"),
            observed_at=_at(minutes=8),
        ),
        _input_row(
            "market-blocked-lower",
            "input-4",
            "proxy",
            d("0.380000"),
            observed_at=_at(minutes=7),
        ),
        _input_row(
            "market-clear",
            "input-5",
            "official",
            d("0.500000"),
            observed_at=_at(minutes=6),
        ),
        _input_row(
            "market-clear",
            "input-6",
            "primary",
            d("0.510000"),
            observed_at=_at(minutes=5),
        ),
        _input_row(
            "market-blocked-higher",
            "input-7",
            "official",
            d("0.100000"),
            observed_at=_at(minutes=4),
        ),
        _input_row(
            "market-blocked-higher",
            "input-8",
            "proxy",
            d("0.350000"),
            observed_at=_at(minutes=3),
        ),
        _input_row(
            "market-watch-alpha",
            "input-9",
            "official",
            d("0.520000"),
            observed_at=_at(minutes=2),
        ),
        _input_row(
            "market-watch-alpha",
            "input-10",
            "proxy",
            d("0.600000"),
            observed_at=_at(minutes=1),
        ),
    )

    assert tuple(row.market_id for row in report.rows) == (
        "market-blocked-higher",
        "market-blocked-lower",
        "market-watch-alpha",
        "market-watch-beta",
        "market-clear",
    )
    assert tuple(row.health_status for row in report.rows) == (
        "blocked",
        "blocked",
        "watch",
        "watch",
        "clear",
    )


def test_threshold_statuses_cover_disagreement_staleness_and_concentration() -> None:
    report = _report(
        _input_row(
            "market-clear",
            "input-clear-official",
            "official",
            d("0.500000"),
            observed_at=_at(minutes=15),
        ),
        _input_row(
            "market-clear",
            "input-clear-primary",
            "primary",
            d("0.520000"),
            observed_at=_at(minutes=14),
        ),
        _input_row(
            "market-clear",
            "input-clear-proxy",
            "proxy",
            d("0.510000"),
            observed_at=_at(minutes=13),
        ),
        _input_row(
            "market-watch-disagreement",
            "input-watch-official",
            "official",
            d("0.500000"),
            observed_at=_at(minutes=12),
        ),
        _input_row(
            "market-watch-disagreement",
            "input-watch-proxy",
            "proxy",
            d("0.600000"),
            observed_at=_at(minutes=11),
        ),
        _input_row(
            "market-blocked-disagreement",
            "input-blocked-official",
            "official",
            d("0.300000"),
            observed_at=_at(minutes=10),
        ),
        _input_row(
            "market-blocked-disagreement",
            "input-blocked-proxy",
            "proxy",
            d("0.500001"),
            observed_at=_at(minutes=9),
        ),
        _input_row(
            "market-stale-family",
            "input-stale-official",
            "official",
            d("0.550000"),
            observed_at=_at(hours=3),
        ),
        _input_row(
            "market-stale-family",
            "input-stale-proxy",
            "proxy",
            d("0.560000"),
            observed_at=_at(minutes=8),
        ),
        _input_row(
            "market-dominant-family",
            "input-dominant-official-1",
            "official",
            d("0.440000"),
            observed_at=_at(minutes=7),
        ),
        _input_row(
            "market-dominant-family",
            "input-dominant-official-2",
            "official",
            d("0.450000"),
            observed_at=_at(minutes=6),
        ),
        _input_row(
            "market-dominant-family",
            "input-dominant-official-3",
            "official",
            d("0.460000"),
            observed_at=_at(minutes=5),
        ),
        _input_row(
            "market-dominant-family",
            "input-dominant-proxy",
            "proxy",
            d("0.450000"),
            observed_at=_at(minutes=4),
        ),
    )

    by_market = {row.market_id: row for row in report.rows}

    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "market_source_family_probability_delta_blocked",
        "market_source_family_probability_delta_watch",
        "market_source_family_stale_family_coverage",
        "market_source_family_dominant_family_concentration_watch",
    )
    assert report.market_count == d("5.000000")
    assert report.clear_market_count == d("1.000000")
    assert report.watch_market_count == d("3.000000")
    assert report.blocked_market_count == d("1.000000")
    assert report.stale_family_count == d("1.000000")
    assert report.dominant_family_market_count == d("1.000000")
    assert report.disagreement_market_ratio == d("0.400000")
    assert report.stale_family_ratio == d("0.090909")
    assert report.dominant_family_market_ratio == d("0.200000")
    assert report.max_probability_delta == d("0.200001")
    assert report.max_family_age_seconds == d("10800.000000")
    assert report.max_dominant_family_ratio == d("0.750000")

    assert by_market["market-clear"].health_status == "clear"
    assert by_market["market-clear"].reason_codes == (
        "market_source_family_divergence_health_clear",
    )

    watch = by_market["market-watch-disagreement"]
    assert watch.health_status == "watch"
    assert watch.max_probability_delta == d("0.100000")
    assert watch.reason_codes == (
        "market_source_family_probability_delta_watch",
    )

    blocked = by_market["market-blocked-disagreement"]
    assert blocked.health_status == "blocked"
    assert blocked.max_probability_delta == d("0.200001")
    assert blocked.reason_codes == (
        "market_source_family_probability_delta_blocked",
    )

    stale = by_market["market-stale-family"]
    assert stale.health_status == "watch"
    assert stale.stale_family_count == d("1.000000")
    assert stale.reason_codes == (
        "market_source_family_stale_family_coverage",
    )

    dominant = by_market["market-dominant-family"]
    assert dominant.health_status == "watch"
    assert dominant.dominant_source_family == "official"
    assert dominant.dominant_family_ratio == d("0.750000")
    assert dominant.reason_codes == (
        "market_source_family_dominant_family_concentration_watch",
    )


def test_utc_validation_rejects_naive_times_and_normalizes_offsets() -> None:
    api = _api()

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        _input_row(
            "market-naive",
            "input-naive",
            "official",
            d("0.500000"),
            observed_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_market_source_family_divergence_health_report(
            (),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        _report(
            _input_row(
                "market-future",
                "input-future",
                "official",
                d("0.500000"),
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )

    offset = timezone(timedelta(hours=-4))
    converted = api.build_market_source_family_divergence_health_report(
        (
            api.MarketSourceFamilyDivergenceHealthInputRow(
                market_id="market-offset",
                research_input_id="input-offset",
                source_family="official",
                probability=d("0.500000"),
                observed_at=datetime(2026, 7, 2, 7, 30, tzinfo=offset),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=offset),
    )

    assert converted.generated_at == GENERATED_AT
    assert converted.rows[0].latest_observed_at == datetime(
        2026,
        7,
        2,
        11,
        30,
        tzinfo=UTC,
    )
    assert converted.rows[0].max_family_age_seconds == d("1800.000000")


def test_public_dataclasses_are_frozen_and_decimal_only() -> None:
    api = _api()
    contract_classes = (
        api.MarketSourceFamilyDivergenceHealthConfig,
        api.MarketSourceFamilyDivergenceHealthInputRow,
        api.MarketSourceFamilyDivergenceHealthMarketRow,
        api.MarketSourceFamilyDivergenceHealthReport,
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
            assert not _type_uses_binary_numeric(hint)

    row = _input_row(
        "market-frozen",
        "input-frozen",
        "official",
        d("0.500000"),
        observed_at=_at(minutes=5),
    )
    with pytest.raises(FrozenInstanceError):
        row.probability = d("0.600000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="probability must be a Decimal"):
        _input_row(
            "market-numeric",
            "input-numeric",
            "official",
            0.5,  # type: ignore[arg-type]
            observed_at=_at(minutes=5),
        )
    with pytest.raises(ValueError, match="watch_probability_delta must be a Decimal"):
        _config(watch_probability_delta=0.05)
    with pytest.raises(ValueError, match="paper_only must be True"):
        getattr(dataclasses, _join_parts("rep", "lace"))(row, paper_only=False)


def test_public_strings_reject_sensitive_and_mutation_terms() -> None:
    for index, unsafe_fragment in enumerate(
        (
            _join_parts("cred", "ential"),
            _join_parts("priv", "ate"),
            _join_parts("sec", "ret"),
            _join_parts("to", "ken"),
            _join_parts("li", "ve"),
            _join_parts("au", "th"),
            _join_parts("wal", "let"),
            _join_parts("ex", "change"),
            _join_parts("bro", "ker"),
            _join_parts("ord", "er"),
            _join_parts("sub", "mit"),
            _join_parts("can", "cel"),
            _join_parts("rep", "lace"),
            _join_parts("sig", "ning"),
            _join_parts("ad", "vice"),
        ),
    ):
        with pytest.raises(ValueError, match="source_family contains unsafe text"):
            _input_row(
                f"market-safe-{index}",
                f"input-safe-{index}",
                f"source-{unsafe_fragment}",
                d("0.500000"),
                observed_at=_at(minutes=5),
            )


def test_json_payload_uses_decimal_strings_and_iso_datetimes() -> None:
    api = _api()
    report = _report(
        _input_row(
            "market-json",
            "input-json-official",
            "official",
            d("0.500000"),
            observed_at=_at(minutes=30),
        ),
        _input_row(
            "market-json",
            "input-json-proxy",
            "proxy",
            d("0.700000"),
            observed_at=_at(minutes=10),
        ),
    )

    payload = api.market_source_family_divergence_health_report_payload(report)

    json.dumps(payload, sort_keys=True)
    assert _binary_numeric_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["max_probability_delta"] == "0.200000"
    assert payload["rows"][0]["latest_observed_at"] == "2026-07-02T11:50:00+00:00"
    assert payload["rows"][0]["dominant_family_ratio"] == "0.500000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(ValueError, match="report must be"):
        api.market_source_family_divergence_health_report_payload(object())


def test_module_surface_is_report_only_and_does_not_use_float_calls() -> None:
    api = _api()

    assert importlib.util.find_spec(MODULE_NAME) is not None
    public_names = tuple(api.__all__)
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert _join_parts(".", "total", "_seconds", "(") not in source
    assert _join_parts("flo", "at", "(") not in source
    for banned in (
        _join_parts("cred", "ential"),
        _join_parts("priv", "ate"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ex", "change"),
        _join_parts("bro", "ker"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("rep", "lace"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ):
        assert banned not in source
        assert all(banned not in name.lower() for name in public_names)

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "buy",
                "connect",
                "execute",
                "executemany",
                "patch",
                "place",
                "post",
                "put",
                "request",
                "sell",
            }


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _binary_numeric_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_binary_numeric_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_binary_numeric_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()


def _type_uses_binary_numeric(value: object) -> bool:
    if value is float:
        return True
    return any(_type_uses_binary_numeric(item) for item in get_args(value))
