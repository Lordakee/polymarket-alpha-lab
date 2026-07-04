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


MODULE_NAME = "polymarket_alpha_lab.market_source_family_divergence_queue_report"
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
    observed_value: str,
    *,
    source_updated_at: datetime,
) -> object:
    return _api().MarketSourceFamilyDivergenceQueueInputRow(
        market_id=market_id,
        category_id=category_id,
        source_family=source_family,
        observed_value=observed_value,
        source_updated_at=source_updated_at,
    )


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_QUEUE_REPORT_CONFIG_VERSION
        ),
        "stale_source_family_seconds": d("3600.000000"),
        "team_acknowledgement_required_after_seconds": d("600.000000"),
        "repeated_category_miss_threshold": d("2.000000"),
    }
    values.update(overrides)
    return api.MarketSourceFamilyDivergenceQueueConfig(**values)


def _report(*rows: object, **config_overrides: object) -> object:
    return _api().build_market_source_family_divergence_queue_report(
        rows,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_module_import_surface_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_build_report_queues_source_family_divergence_cases() -> None:
    api = _api()

    report = _report(
        _input_row(
            "market-conflict",
            "politics",
            "official",
            "resolved_yes",
            source_updated_at=_at(hours=2),
        ),
        _input_row(
            "market-conflict",
            "politics",
            "primary",
            "resolved_yes",
            source_updated_at=_at(minutes=30),
        ),
        _input_row(
            "market-conflict",
            "politics",
            "proxy",
            "resolved_no",
            source_updated_at=_at(minutes=20),
        ),
        _input_row(
            "market-repeat",
            "politics",
            "official",
            "open",
            source_updated_at=_at(hours=2),
        ),
        _input_row(
            "market-repeat",
            "politics",
            "proxy",
            "open",
            source_updated_at=_at(minutes=20),
        ),
        _input_row(
            "market-stale-acknowledged",
            "sports",
            "official",
            "open",
            source_updated_at=_at(hours=2),
        ),
        _input_row(
            "market-stale-acknowledged",
            "sports",
            "proxy",
            "open",
            source_updated_at=_at(minutes=20),
        ),
        _input_row(
            "market-stale-acknowledged",
            "sports",
            "team_acknowledged",
            "open",
            source_updated_at=_at(minutes=10),
        ),
        _input_row(
            "market-clear",
            "weather",
            "official",
            "open",
            source_updated_at=_at(minutes=30),
        ),
        _input_row(
            "market-clear",
            "weather",
            "primary",
            "open",
            source_updated_at=_at(minutes=25),
        ),
        _input_row(
            "market-clear",
            "weather",
            "proxy",
            "open",
            source_updated_at=_at(minutes=20),
        ),
        _input_row(
            "market-clear",
            "weather",
            "team_acknowledged",
            "open",
            source_updated_at=_at(minutes=15),
        ),
    )

    assert type(report) is api.MarketSourceFamilyDivergenceQueueReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        api.DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_QUEUE_REPORT_CONFIG_VERSION
    )
    assert report.report_status == "blocked"
    assert report.reason_codes == (
        "market_source_family_divergence_queue_official_proxy_conflict",
        "market_source_family_divergence_queue_stale_source_family",
        "market_source_family_divergence_queue_missing_team_acknowledgement",
        "market_source_family_divergence_queue_repeated_category_miss",
    )
    assert report.market_count == d("4.000000")
    assert report.source_family_count == d("12.000000")
    assert report.clear_market_count == d("1.000000")
    assert report.watch_market_count == d("1.000000")
    assert report.blocked_market_count == d("2.000000")
    assert report.queued_market_count == d("3.000000")
    assert report.official_proxy_conflict_market_count == d("1.000000")
    assert report.stale_source_family_market_count == d("3.000000")
    assert report.missing_team_acknowledgement_market_count == d("2.000000")
    assert report.repeated_category_miss_market_count == d("2.000000")
    assert report.queued_market_ratio == d("0.750000")
    assert report.official_proxy_conflict_ratio == d("0.250000")
    assert report.stale_source_family_ratio == d("0.750000")
    assert report.missing_team_acknowledgement_ratio == d("0.500000")
    assert report.repeated_category_miss_ratio == d("0.500000")
    assert report.max_source_age_seconds == d("7200.000000")
    assert tuple(row.market_id for row in report.rows) == (
        "market-conflict",
        "market-repeat",
        "market-stale-acknowledged",
        "market-clear",
    )

    conflict = report.rows[0]
    assert conflict.queue_status == "blocked"
    assert conflict.queue_required is True
    assert conflict.category_id == "politics"
    assert conflict.official_value == "resolved_yes"
    assert conflict.primary_value == "resolved_yes"
    assert conflict.proxy_value == "resolved_no"
    assert conflict.team_acknowledged_value is None
    assert conflict.source_family_count == d("3.000000")
    assert conflict.official_proxy_conflict_count == d("1.000000")
    assert conflict.stale_source_family_count == d("1.000000")
    assert conflict.missing_team_acknowledgement_count == d("1.000000")
    assert conflict.repeated_category_miss_count == d("1.000000")
    assert conflict.category_miss_count == d("2.000000")
    assert conflict.max_source_age_seconds == d("7200.000000")
    assert conflict.reason_codes == (
        "market_source_family_divergence_queue_official_proxy_conflict",
        "market_source_family_divergence_queue_stale_source_family",
        "market_source_family_divergence_queue_missing_team_acknowledgement",
        "market_source_family_divergence_queue_repeated_category_miss",
    )

    repeated = report.rows[1]
    assert repeated.queue_status == "blocked"
    assert repeated.reason_codes == (
        "market_source_family_divergence_queue_stale_source_family",
        "market_source_family_divergence_queue_missing_team_acknowledgement",
        "market_source_family_divergence_queue_repeated_category_miss",
    )

    stale = report.rows[2]
    assert stale.queue_status == "watch"
    assert stale.queue_required is True
    assert stale.missing_team_acknowledgement_count == d("0.000000")
    assert stale.repeated_category_miss_count == d("0.000000")
    assert stale.reason_codes == (
        "market_source_family_divergence_queue_stale_source_family",
    )

    clear = report.rows[3]
    assert clear.queue_status == "clear"
    assert clear.queue_required is False
    assert clear.reason_codes == (
        "market_source_family_divergence_queue_clear",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_is_clear_decimal_only_and_deterministic() -> None:
    report = _report()

    assert report.report_status == "clear"
    assert report.reason_codes == ("market_source_family_divergence_queue_clear",)
    assert report.market_count == d("0.000000")
    assert report.source_family_count == d("0.000000")
    assert report.queued_market_count == d("0.000000")
    assert report.queued_market_ratio == d("0.000000")
    assert report.max_source_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_helper_is_json_ready_without_float_values_and_uses_utc_strings() -> None:
    offset = timezone(timedelta(hours=-4))
    api = _api()
    report = api.build_market_source_family_divergence_queue_report(
        (
            api.MarketSourceFamilyDivergenceQueueInputRow(
                market_id="market-offset",
                category_id="weather",
                source_family="official",
                observed_value="open",
                source_updated_at=datetime(2026, 7, 2, 7, 30, tzinfo=offset),
            ),
            api.MarketSourceFamilyDivergenceQueueInputRow(
                market_id="market-offset",
                category_id="weather",
                source_family="proxy",
                observed_value="open",
                source_updated_at=datetime(2026, 7, 2, 7, 45, tzinfo=offset),
            ),
            api.MarketSourceFamilyDivergenceQueueInputRow(
                market_id="market-offset",
                category_id="weather",
                source_family="team_acknowledged",
                observed_value="open",
                source_updated_at=datetime(2026, 7, 2, 7, 50, tzinfo=offset),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=offset),
    )

    payload = api.market_source_family_divergence_queue_report_to_payload(report)

    json.dumps(payload, sort_keys=True)
    assert _float_paths(payload) == ()
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["queued_market_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["market_id"] == "market-offset"
    assert payload["rows"][0]["max_source_age_seconds"] == "1800.000000"

    with pytest.raises(ValueError, match="report must be"):
        api.market_source_family_divergence_queue_report_to_payload(object())


def test_public_dataclasses_are_frozen_decimal_only_and_validate_times_and_flags() -> None:
    api = _api()
    contract_classes = (
        api.MarketSourceFamilyDivergenceQueueConfig,
        api.MarketSourceFamilyDivergenceQueueInputRow,
        api.MarketSourceFamilyDivergenceQueueRow,
        api.MarketSourceFamilyDivergenceQueueReport,
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
            if (
                field_name.endswith("_count")
                or field_name.endswith("_ratio")
                or field_name.endswith("_seconds")
            ):
                assert hint is Decimal

    row = _input_row(
        "market-frozen",
        "weather",
        "official",
        "open",
        source_updated_at=_at(minutes=5),
    )
    with pytest.raises(FrozenInstanceError):
        row.observed_value = "closed"  # type: ignore[misc]

    with pytest.raises(ValueError, match="stale_source_family_seconds"):
        api.MarketSourceFamilyDivergenceQueueConfig(
            stale_source_family_seconds=3600,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        api.MarketSourceFamilyDivergenceQueueInputRow(
            market_id="market-naive",
            category_id="weather",
            source_family="official",
            observed_value="open",
            source_updated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_market_source_family_divergence_queue_report(
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
                "open",
                source_updated_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="source_family"):
        _input_row(
            "market-family",
            "weather",
            "community",
            "open",
            source_updated_at=_at(minutes=5),
        )
    with pytest.raises(ValueError, match="market_id"):
        _input_row(
            _join_parts("wal", "let"),
            "weather",
            "official",
            "open",
            source_updated_at=_at(minutes=5),
        )
    with pytest.raises(ValueError, match="unique"):
        _report(
            _input_row(
                "market-duplicate",
                "weather",
                "official",
                "open",
                source_updated_at=_at(minutes=5),
            ),
            _input_row(
                "market-duplicate",
                "weather",
                "official",
                "closed",
                source_updated_at=_at(minutes=4),
            ),
        )
    with pytest.raises(ValueError, match="category_id"):
        _report(
            _input_row(
                "market-category-a",
                "weather",
                "official",
                "open",
                source_updated_at=_at(minutes=5),
            ),
            _input_row(
                "market-category-a",
                "politics",
                "proxy",
                "open",
                source_updated_at=_at(minutes=4),
            ),
        )
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)


def test_module_is_pure_in_memory_report_only_surface() -> None:
    api = _api()
    public_names = tuple(api.__all__)
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert api.__all__ == (
        "DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_QUEUE_REPORT_CONFIG_VERSION",
        "MarketSourceFamilyDivergenceQueueConfig",
        "MarketSourceFamilyDivergenceQueueInputRow",
        "MarketSourceFamilyDivergenceQueueReport",
        "MarketSourceFamilyDivergenceQueueRow",
        "build_market_source_family_divergence_queue_report",
        "market_source_family_divergence_queue_report_to_payload",
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
