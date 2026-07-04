from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
EXPECTED_EXPORTS = (
    "DEFAULT_MARKET_CATEGORY_VOLATILITY_PROFILE_CONFIG_VERSION",
    "MarketCategoryProbabilitySnapshot",
    "MarketCategoryVolatilityProfileConfig",
    "MarketCategoryVolatilityProfileReport",
    "MarketCategoryVolatilityProfileRow",
    "build_market_category_volatility_profile_report",
    "market_category_volatility_profile_payload",
)
FORBIDDEN_IMPORT_PREFIXES = {
    "argparse",
    "httpx",
    "json",
    "os",
    "pathlib",
    "psycopg",
    "requests",
    "socket",
    "sqlite3",
    "sqlalchemy",
    "subprocess",
    "supabase",
    "redis",
    "pymongo",
    "web3",
    "eth_account",
    "py_clob_client",
}
FORBIDDEN_IO_CALL_NAMES = {
    "open",
    "connect",
    "create_connection",
    "request",
    "urlopen",
    "Popen",
    "run",
    "call",
    "check_call",
    "check_output",
}
FORBIDDEN_OUTPUT_FIELDS = {
    "market_slug",
    "question",
    "payload",
    "payload_json",
    "auth",
    "wallet",
    "account",
    "order",
}


def _module() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.market_category_volatility_profile",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _snapshot(
    snapshot_id: str,
    *,
    category_id: str = "finance.crypto.btc",
    team_id: str = "crypto_btc",
    probability: Decimal = d("0.500000"),
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = _module()
    return module.MarketCategoryProbabilitySnapshot(
        snapshot_id=snapshot_id,
        category_id=category_id,
        team_id=team_id,
        forecast_probability=probability,
        generated_at=generated_at,
    )


def _bypassed_snapshot(snapshot: object, **overrides: Any) -> object:
    malformed = object.__new__(type(snapshot))
    for key, value in snapshot.__dict__.items():
        object.__setattr__(malformed, key, value)
    for key, value in overrides.items():
        object.__setattr__(malformed, key, value)
    return malformed


def _bypassed_report(report: object, **overrides: Any) -> object:
    malformed = object.__new__(type(report))
    for key, value in report.__dict__.items():
        object.__setattr__(malformed, key, value)
    for key, value in overrides.items():
        object.__setattr__(malformed, key, value)
    return malformed


def _assert_no_float_values(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("market category volatility profile must not expose float values")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_no_float_values(getattr(value, field.name))
    elif isinstance(value, dict):
        for key, item in value.items():
            _assert_no_float_values(key)
            _assert_no_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_float_values(item)


def _assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) in {int, float}:
        pytest.fail(
            "market category volatility profile public numerics must be Decimal values",
        )
    if isinstance(value, Decimal) or isinstance(value, (str, bool, datetime, type(None))):
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _assert_public_numeric_values_are_decimal(getattr(value, field.name))
    elif isinstance(value, dict):
        for key, item in value.items():
            _assert_public_numeric_values_are_decimal(key)
            _assert_public_numeric_values_are_decimal(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_numeric_values_are_decimal(item)


def test_public_exports_are_exact_and_dataclasses_are_frozen() -> None:
    module = _module()

    assert module.__all__ == EXPECTED_EXPORTS

    config = module.MarketCategoryVolatilityProfileConfig()
    snapshot = _snapshot("snapshot-1", probability=d("0.250000"))
    row = module.MarketCategoryVolatilityProfileRow(
        category_id="finance.crypto.btc",
        snapshot_count=d("2.000000"),
        team_count=d("1.000000"),
        first_snapshot_at=GENERATED_AT,
        latest_snapshot_at=GENERATED_AT + timedelta(minutes=1),
        min_probability=d("0.250000"),
        max_probability=d("0.300000"),
        average_probability=d("0.275000"),
        category_volatility=d("0.050000"),
        first_probability_range=d("0.000000"),
        latest_probability_range=d("0.000000"),
        range_expansion=d("0.000000"),
        stability_bucket="stable",
        reason_codes=("category_stable",),
    )
    report = module.MarketCategoryVolatilityProfileReport(
        generated_at=GENERATED_AT,
        config_version=config.config_version,
        snapshot_count=d("2.000000"),
        category_count=d("1.000000"),
        volatile_category_count=d("0.000000"),
        watch_category_count=d("0.000000"),
        stable_category_count=d("1.000000"),
        insufficient_history_category_count=d("0.000000"),
        max_category_volatility=d("0.050000"),
        max_range_expansion=d("0.000000"),
        status="stable",
        rows=(row,),
    )

    assert config.paper_only is True
    assert snapshot.report_only is True
    assert row.readonly is True
    assert report.paper_only is True
    _assert_public_numeric_values_are_decimal(config)
    _assert_public_numeric_values_are_decimal(snapshot)
    _assert_public_numeric_values_are_decimal(row)
    _assert_public_numeric_values_are_decimal(report)

    with pytest.raises(FrozenInstanceError):
        config.config_version = "mutated"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        snapshot.forecast_probability = d("0")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.snapshot_count = 0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.category_count = 0  # type: ignore[misc]


def test_build_report_profiles_category_volatility_and_range_expansion() -> None:
    module = _module()
    config = module.MarketCategoryVolatilityProfileConfig(
        config_version="market-category-volatility-profile-test-v0",
        min_snapshot_count=d("3.000000"),
        min_team_count=d("1.000000"),
        stable_volatility_threshold=d("0.050000"),
        high_volatility_threshold=d("0.250000"),
        range_expansion_threshold=d("0.100000"),
    )
    first_at = GENERATED_AT
    latest_at = GENERATED_AT + timedelta(minutes=10)

    report = module.build_market_category_volatility_profile_report(
        (
            _snapshot(
                "btc-first-a",
                probability=d("0.400000"),
                generated_at=first_at,
            ),
            _snapshot(
                "btc-first-b",
                probability=d("0.450000"),
                generated_at=first_at,
            ),
            _snapshot(
                "btc-latest-a",
                probability=d("0.200000"),
                generated_at=latest_at,
            ),
            _snapshot(
                "btc-latest-b",
                probability=d("0.850000"),
                generated_at=latest_at,
            ),
            _snapshot(
                "rates-one",
                category_id="finance.macro.rates",
                team_id="macro_rates",
                probability=d("0.510000"),
                generated_at=first_at,
            ),
            _snapshot(
                "rates-two",
                category_id="finance.macro.rates",
                team_id="macro_rates",
                probability=d("0.530000"),
                generated_at=latest_at,
            ),
            _snapshot(
                "gold-only",
                category_id="finance.commodities.gold",
                team_id="commodities_gold",
                probability=d("0.650000"),
                generated_at=latest_at,
            ),
        ),
        config=config,
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is module.MarketCategoryVolatilityProfileReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-category-volatility-profile-test-v0"
    assert report.snapshot_count == d("7.000000")
    assert report.category_count == d("3.000000")
    assert report.volatile_category_count == d("1.000000")
    assert report.watch_category_count == d("0.000000")
    assert report.stable_category_count == d("0.000000")
    assert report.insufficient_history_category_count == d("2.000000")
    assert report.max_category_volatility == d("0.650000")
    assert report.max_range_expansion == d("0.600000")
    assert report.status == "volatile"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    rows_by_category = {row.category_id: row for row in report.rows}
    btc = rows_by_category["finance.crypto.btc"]
    gold = rows_by_category["finance.commodities.gold"]
    rates = rows_by_category["finance.macro.rates"]

    assert btc.category_id == "finance.crypto.btc"
    assert btc.snapshot_count == d("4.000000")
    assert btc.team_count == d("1.000000")
    assert btc.first_snapshot_at == first_at
    assert btc.latest_snapshot_at == latest_at
    assert btc.min_probability == d("0.200000")
    assert btc.max_probability == d("0.850000")
    assert btc.average_probability == d("0.475000")
    assert btc.category_volatility == d("0.650000")
    assert btc.first_probability_range == d("0.050000")
    assert btc.latest_probability_range == d("0.650000")
    assert btc.range_expansion == d("0.600000")
    assert btc.stability_bucket == "volatile"
    assert btc.reason_codes == (
        "category_volatility_high",
        "range_expansion_high",
    )

    assert gold.category_id == "finance.commodities.gold"
    assert gold.stability_bucket == "insufficient_history"
    assert gold.reason_codes == ("missing_snapshot_history",)

    assert rates.category_id == "finance.macro.rates"
    assert rates.category_volatility == d("0.020000")
    assert rates.stability_bucket == "insufficient_history"
    assert rates.reason_codes == ("missing_snapshot_history",)
    _assert_no_float_values(report)
    _assert_public_numeric_values_are_decimal(report)


def test_build_report_marks_stable_and_watch_buckets() -> None:
    module = _module()

    stable_report = module.build_market_category_volatility_profile_report(
        (
            _snapshot("stable-one", probability=d("0.510000")),
            _snapshot(
                "stable-two",
                probability=d("0.530000"),
                generated_at=GENERATED_AT + timedelta(minutes=1),
            ),
        ),
        config=module.MarketCategoryVolatilityProfileConfig(
            config_version="market-category-volatility-profile-test-v0",
            min_snapshot_count=d("2.000000"),
            stable_volatility_threshold=d("0.050000"),
            high_volatility_threshold=d("0.250000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert stable_report.status == "stable"
    assert stable_report.stable_category_count == 1
    assert stable_report.rows[0].category_volatility == d("0.020000")
    assert stable_report.rows[0].stability_bucket == "stable"
    assert stable_report.rows[0].reason_codes == ("category_stable",)

    watch_report = module.build_market_category_volatility_profile_report(
        (
            _snapshot("watch-one", probability=d("0.400000")),
            _snapshot(
                "watch-two",
                probability=d("0.520000"),
                generated_at=GENERATED_AT + timedelta(minutes=1),
            ),
        ),
        config=module.MarketCategoryVolatilityProfileConfig(
            config_version="market-category-volatility-profile-test-v0",
            min_snapshot_count=d("2.000000"),
            stable_volatility_threshold=d("0.050000"),
            high_volatility_threshold=d("0.250000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert watch_report.status == "watch"
    assert watch_report.watch_category_count == 1
    assert watch_report.rows[0].category_volatility == d("0.120000")
    assert watch_report.rows[0].stability_bucket == "watch"
    assert watch_report.rows[0].reason_codes == ("category_volatility_watch",)


def test_build_report_handles_empty_inputs_without_identifying_markets() -> None:
    module = _module()

    report = module.build_market_category_volatility_profile_report(
        [],
        config=module.MarketCategoryVolatilityProfileConfig(
            config_version="market-category-volatility-profile-test-v0",
        ),
        generated_at=GENERATED_AT,
    )

    assert report.snapshot_count == 0
    assert report.snapshot_count == d("0.000000")
    assert report.category_count == d("0.000000")
    assert report.volatile_category_count == d("0.000000")
    assert report.watch_category_count == d("0.000000")
    assert report.stable_category_count == d("0.000000")
    assert report.insufficient_history_category_count == d("0.000000")
    assert report.max_category_volatility is None
    assert report.max_range_expansion is None
    assert report.status == "empty_snapshot_set"
    assert report.rows == ()

    exposed_field_names = {
        field.name
        for dataclass_type in (
            module.MarketCategoryProbabilitySnapshot,
            module.MarketCategoryVolatilityProfileRow,
            module.MarketCategoryVolatilityProfileReport,
        )
        for field in fields(dataclass_type)
    }
    assert not (exposed_field_names & FORBIDDEN_OUTPUT_FIELDS)


def test_dataclasses_validate_decimal_only_counts_metadata_and_flags() -> None:
    module = _module()

    with pytest.raises(ValueError, match="config_version"):
        module.MarketCategoryVolatilityProfileConfig(config_version=" ")
    with pytest.raises(ValueError, match="min_snapshot_count"):
        module.MarketCategoryVolatilityProfileConfig(min_snapshot_count=0)
    with pytest.raises(ValueError, match="min_snapshot_count"):
        module.MarketCategoryVolatilityProfileConfig(
            min_snapshot_count=d("1.500000"),
        )
    with pytest.raises(ValueError, match="min_team_count"):
        module.MarketCategoryVolatilityProfileConfig(min_team_count=True)
    with pytest.raises(ValueError, match="high_volatility_threshold"):
        module.MarketCategoryVolatilityProfileConfig(
            stable_volatility_threshold=d("0.250000"),
            high_volatility_threshold=d("0.250000"),
        )
    with pytest.raises(ValueError, match="range_expansion_threshold"):
        module.MarketCategoryVolatilityProfileConfig(range_expansion_threshold=0.1)
    with pytest.raises(ValueError, match="paper_only"):
        module.MarketCategoryVolatilityProfileConfig(paper_only=False)
    with pytest.raises(ValueError, match="category_id"):
        _snapshot(
            "bad-category",
            category_id="finance.crypto.eth",
            team_id="crypto_btc",
            probability=d("0.500000"),
        )
    with pytest.raises(ValueError, match="forecast_probability"):
        module.MarketCategoryProbabilitySnapshot(
            snapshot_id="bad-probability",
            category_id="finance.crypto.btc",
            team_id="crypto_btc",
            forecast_probability=0.5,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="forecast_probability"):
        module.MarketCategoryProbabilitySnapshot(
            snapshot_id="bad-decimal-subclass",
            category_id="finance.crypto.btc",
            team_id="crypto_btc",
            forecast_probability=_DecimalSubclass("0.500000"),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="reason_codes"):
        module.MarketCategoryVolatilityProfileRow(
            category_id="finance.crypto.btc",
            snapshot_count=d("2.000000"),
            team_count=d("1.000000"),
            first_snapshot_at=GENERATED_AT,
            latest_snapshot_at=GENERATED_AT,
            min_probability=d("0.250000"),
            max_probability=d("0.300000"),
            average_probability=d("0.275000"),
            category_volatility=d("0.050000"),
            first_probability_range=d("0.000000"),
            latest_probability_range=d("0.000000"),
            range_expansion=d("0.000000"),
            stability_bucket="stable",
            reason_codes=("category_stable", "category_stable"),
        )
    with pytest.raises(ValueError, match="rows"):
        module.MarketCategoryVolatilityProfileReport(
            generated_at=GENERATED_AT,
            config_version="market-category-volatility-profile-test-v0",
            snapshot_count=d("0.000000"),
            category_count=d("1.000000"),
            volatile_category_count=d("0.000000"),
            watch_category_count=d("0.000000"),
            stable_category_count=d("0.000000"),
            insufficient_history_category_count=d("0.000000"),
            max_category_volatility=None,
            max_range_expansion=None,
            status="empty_snapshot_set",
            rows=(),
        )


def test_payload_serializes_decimal_counts_as_strings_and_rejects_public_ints() -> None:
    module = _module()
    report = module.build_market_category_volatility_profile_report(
        (
            _snapshot("stable-one", probability=d("0.510000")),
            _snapshot(
                "stable-two",
                probability=d("0.530000"),
                generated_at=GENERATED_AT + timedelta(minutes=1),
            ),
        ),
        config=module.MarketCategoryVolatilityProfileConfig(
            config_version="market-category-volatility-profile-test-v0",
            min_snapshot_count=d("2.000000"),
        ),
        generated_at=GENERATED_AT,
    )

    payload = module.market_category_volatility_profile_payload(report)

    json.dumps(payload, sort_keys=True)
    assert payload["snapshot_count"] == "2.000000"
    assert payload["category_count"] == "1.000000"
    assert payload["stable_category_count"] == "1.000000"
    assert payload["max_category_volatility"] == "0.020000"
    assert payload["rows"][0]["snapshot_count"] == "2.000000"
    assert payload["rows"][0]["team_count"] == "1.000000"
    assert payload["rows"][0]["category_volatility"] == "0.020000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_values(payload)

    with pytest.raises(ValueError, match="snapshot_count.*Decimal"):
        module.market_category_volatility_profile_payload(
            _bypassed_report(report, snapshot_count=2),
        )


def test_datetime_inputs_must_be_exact_timezone_aware_datetimes() -> None:
    module = _module()
    config = module.MarketCategoryVolatilityProfileConfig()

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        _snapshot("naive-snapshot", generated_at=datetime(2026, 7, 2, 12, 0))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        _snapshot(
            "subclass-snapshot",
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        _snapshot(
            "none-offset-snapshot",
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_market_category_volatility_profile_report(
            [],
            config=config,
            generated_at=datetime(2026, 7, 2, 12, 0),
        )


def test_build_report_rejects_bad_inputs_duplicate_ids_and_non_paper_snapshots() -> None:
    module = _module()
    config = module.MarketCategoryVolatilityProfileConfig()

    with pytest.raises(ValueError, match="snapshots"):
        module.build_market_category_volatility_profile_report(
            "not-snapshots",
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="MarketCategoryProbabilitySnapshot"):
        module.build_market_category_volatility_profile_report(
            [object()],
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique snapshot_id"):
        module.build_market_category_volatility_profile_report(
            (
                _snapshot("duplicate"),
                _snapshot("duplicate", probability=d("0.550000")),
            ),
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper-only"):
        module.build_market_category_volatility_profile_report(
            [_bypassed_snapshot(_snapshot("non-paper"), paper_only=False)],
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_market_category_volatility_profile_report(
            [],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_market_category_volatility_profile_report(
            [],
            config=config,
            generated_at=None,
        )


def test_forbidden_imports_and_output_fields_are_not_used_by_profile_module() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_category_volatility_profile.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    imported: list[str] = []
    call_names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)

    assert not {
        module_name
        for module_name in imported
        for prefix in FORBIDDEN_IMPORT_PREFIXES
        if module_name == prefix or module_name.startswith(f"{prefix}.")
    }
    assert not (set(call_names) & FORBIDDEN_IO_CALL_NAMES)

    dataclass_field_names = {
        field.name
        for dataclass_type in (
            _module().MarketCategoryProbabilitySnapshot,
            _module().MarketCategoryVolatilityProfileConfig,
            _module().MarketCategoryVolatilityProfileRow,
            _module().MarketCategoryVolatilityProfileReport,
        )
        for field in fields(dataclass_type)
    }
    assert not (dataclass_field_names & FORBIDDEN_OUTPUT_FIELDS)
