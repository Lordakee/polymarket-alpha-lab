from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, get_type_hints

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_weather_heat_index_alert_escalation_digest"
)
GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def _module() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"{MODULE_NAME} is missing: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_WEATHER_HEAT_INDEX_ALERT_ESCALATION_DIGEST_CONFIG_VERSION
        ),
        "fresh_snapshot_max_age_seconds": d("21600.000000"),
        "watch_heat_index_f": d("100.000000"),
        "block_heat_index_f": d("108.000000"),
        "rapid_heat_rise_f": d("8.000000"),
        "near_term_peak_hours": d("24.000000"),
        "high_exposure_population_millions": d("1.000000"),
        "min_public_source_count": d("2.000000"),
    }
    values.update(overrides)
    return module.MarketResearchWeatherHeatIndexAlertEscalationDigestConfig(**values)


def _row(
    module: Any,
    region_id: str = "boston",
    market_slug: str = "will-boston-issue-heat-alert",
    *,
    condition_id: str = "condition_boston_heat_index_alert",
    source_id: str = "noaa_public_heat_snapshot",
    snapshot_at: datetime | None = None,
    current_alert_level: str = "none",
    forecast_heat_index_f: Decimal = d("88.000000"),
    prior_heat_index_f: Decimal = d("86.000000"),
    forecast_hours_until_peak: Decimal = d("36.000000"),
    exposed_population_millions: Decimal = d("0.400000"),
    public_source_count: Decimal = d("3.000000"),
    market_probability_before: Decimal = d("0.220000"),
    market_probability_after: Decimal = d("0.240000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.MarketResearchWeatherHeatIndexAlertEscalationInputRow(
        region_id=region_id,
        market_slug=market_slug,
        condition_id=condition_id,
        source_id=source_id,
        snapshot_at=snapshot_at or GENERATED_AT - timedelta(minutes=30),
        current_alert_level=current_alert_level,
        forecast_heat_index_f=forecast_heat_index_f,
        prior_heat_index_f=prior_heat_index_f,
        forecast_hours_until_peak=forecast_hours_until_peak,
        exposed_population_millions=exposed_population_millions,
        public_source_count=public_source_count,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _digest(
    module: Any,
    rows: tuple[object, ...] = (),
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_market_research_weather_heat_index_alert_escalation_digest(
        rows,
        config=cfg or _config(module),
        generated_at=generated_at,
    )


def test_heat_index_alert_escalation_digest_reduces_rows_and_sorts_reasons() -> None:
    module = _module()

    report = _digest(
        module,
        (
            _row(
                module,
                "st_louis",
                "will-st-louis-heat-advisory-escalate",
                condition_id="condition_st_louis_heat_alert",
                source_id="nws_public_heat_advisory",
                snapshot_at=GENERATED_AT - timedelta(hours=8),
                current_alert_level="heat_advisory",
                forecast_heat_index_f=d("101.500000"),
                prior_heat_index_f=d("97.000000"),
                forecast_hours_until_peak=d("18.000000"),
                exposed_population_millions=d("0.800000"),
                public_source_count=d("1.000000"),
                market_probability_before=d("0.300000"),
                market_probability_after=d("0.340000"),
            ),
            _row(
                module,
                "phoenix",
                "will-phoenix-excessive-heat-warning-expand",
                condition_id="condition_phoenix_excessive_heat",
                source_id="nws_public_excessive_heat_warning",
                snapshot_at=datetime(
                    2026,
                    7,
                    4,
                    8,
                    45,
                    tzinfo=timezone(timedelta(hours=-7)),
                ),
                current_alert_level="excessive_heat_warning",
                forecast_heat_index_f=d("112.000000"),
                prior_heat_index_f=d("99.000000"),
                forecast_hours_until_peak=d("6.000000"),
                exposed_population_millions=d("4.600000"),
                public_source_count=d("3.000000"),
                market_probability_before=d("0.480000"),
                market_probability_after=d("0.610000"),
            ),
            _row(module),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=9))),
    )

    assert is_dataclass(report)
    assert type(report) is module.MarketResearchWeatherHeatIndexAlertEscalationDigestReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_MARKET_RESEARCH_WEATHER_HEAT_INDEX_ALERT_ESCALATION_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.next_step == (
        "block_report_only_market_research_weather_heat_index_alert_escalation_digest"
    )
    assert report.region_count == d("3.000000")
    assert report.clear_region_count == d("1.000000")
    assert report.watch_region_count == d("1.000000")
    assert report.blocked_region_count == d("1.000000")
    assert report.fresh_snapshot_count == d("2.000000")
    assert report.stale_snapshot_count == d("1.000000")
    assert report.thin_source_count == d("1.000000")
    assert report.active_alert_count == d("2.000000")
    assert report.high_heat_index_count == d("2.000000")
    assert report.rapid_heat_rise_count == d("1.000000")
    assert report.near_term_peak_count == d("2.000000")
    assert report.high_exposure_count == d("1.000000")
    assert report.probability_shift_count == d("1.000000")
    assert report.max_forecast_heat_index_f == d("112.000000")
    assert report.max_heat_index_rise_f == d("13.000000")
    assert report.min_forecast_hours_until_peak == d("6.000000")
    assert report.max_exposed_population_millions == d("4.600000")
    assert report.max_snapshot_age_seconds == d("28800.000000")
    assert report.average_public_source_count == d("2.333333")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(
        (row.escalation_status, row.region_id, row.market_slug)
        for row in report.rows
    ) == (
        ("blocked", "phoenix", "will-phoenix-excessive-heat-warning-expand"),
        ("watch", "st_louis", "will-st-louis-heat-advisory-escalate"),
        ("clear", "boston", "will-boston-issue-heat-alert"),
    )

    blocked = report.rows[0]
    assert type(blocked) is module.MarketResearchWeatherHeatIndexAlertEscalationDigestRow
    assert blocked.snapshot_at == datetime(2026, 7, 4, 15, 45, tzinfo=UTC)
    assert blocked.snapshot_age_seconds == d("900.000000")
    assert blocked.heat_index_rise_f == d("13.000000")
    assert blocked.probability_change == d("0.130000")
    assert blocked.reason_codes == (
        "market_research_weather_heat_index_alert_escalation_digest_heat_index_block",
        "market_research_weather_heat_index_alert_escalation_digest_alert_level_warning",
        "market_research_weather_heat_index_alert_escalation_digest_rapid_heat_rise",
        "market_research_weather_heat_index_alert_escalation_digest_near_term_peak",
        "market_research_weather_heat_index_alert_escalation_digest_high_exposure",
        "market_research_weather_heat_index_alert_escalation_digest_probability_shift",
    )

    watch = report.rows[1]
    assert watch.snapshot_age_seconds == d("28800.000000")
    assert watch.heat_index_rise_f == d("4.500000")
    assert watch.reason_codes == (
        "market_research_weather_heat_index_alert_escalation_digest_heat_index_watch",
        "market_research_weather_heat_index_alert_escalation_digest_alert_level_watch",
        "market_research_weather_heat_index_alert_escalation_digest_near_term_peak",
        "market_research_weather_heat_index_alert_escalation_digest_stale_snapshot",
        "market_research_weather_heat_index_alert_escalation_digest_thin_sources",
    )

    clear = report.rows[2]
    assert clear.escalation_status == "clear"
    assert clear.snapshot_age_seconds == d("1800.000000")
    assert clear.probability_change == d("0.020000")
    assert clear.reason_codes == (
        "market_research_weather_heat_index_alert_escalation_digest_clear",
    )

    assert report.reason_code_counts == (
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_heat_index_block"
            ),
            count=d("1.000000"),
            region_ratio=d("0.333333"),
        ),
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_alert_level_warning"
            ),
            count=d("1.000000"),
            region_ratio=d("0.333333"),
        ),
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_heat_index_watch"
            ),
            count=d("1.000000"),
            region_ratio=d("0.333333"),
        ),
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_alert_level_watch"
            ),
            count=d("1.000000"),
            region_ratio=d("0.333333"),
        ),
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_rapid_heat_rise"
            ),
            count=d("1.000000"),
            region_ratio=d("0.333333"),
        ),
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_near_term_peak"
            ),
            count=d("2.000000"),
            region_ratio=d("0.666667"),
        ),
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_stale_snapshot"
            ),
            count=d("1.000000"),
            region_ratio=d("0.333333"),
        ),
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_thin_sources"
            ),
            count=d("1.000000"),
            region_ratio=d("0.333333"),
        ),
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_high_exposure"
            ),
            count=d("1.000000"),
            region_ratio=d("0.333333"),
        ),
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_probability_shift"
            ),
            count=d("1.000000"),
            region_ratio=d("0.333333"),
        ),
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_clear"
            ),
            count=d("1.000000"),
            region_ratio=d("0.333333"),
        ),
    )
    assert report.reason_codes == tuple(item.reason_code for item in report.reason_code_counts)


def test_empty_heat_index_alert_escalation_digest_is_blocked_report_only_payload() -> None:
    module = _module()

    report = _digest(module)
    data = module.market_research_weather_heat_index_alert_escalation_digest_payload(
        report,
    )

    json.dumps(data, allow_nan=False, sort_keys=True)
    assert data == module.market_research_weather_heat_index_alert_escalation_digest_json(
        report,
    )
    assert report.digest_status == "blocked"
    assert report.next_step == (
        "block_report_only_market_research_weather_heat_index_alert_escalation_digest"
    )
    assert report.region_count == ZERO
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_weather_heat_index_alert_escalation_digest_no_inputs",
    )
    assert report.reason_code_counts == (
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount(
            reason_code=(
                "market_research_weather_heat_index_alert_escalation_digest_no_inputs"
            ),
            count=d("1.000000"),
            region_ratio=d("1.000000"),
        ),
    )
    assert data["generated_at"] == "2026-07-04T16:00:00+00:00"
    assert data["region_count"] == "0.000000"
    assert data["reason_code_counts"][0]["count"] == "1.000000"
    assert data["paper_only"] is True
    assert data["report_only"] is True
    assert data["readonly"] is True
    assert _float_paths(data) == ()
    assert not any(isinstance(value, Decimal) for value in _walk_values(data))


def test_cooling_rows_keep_signed_row_change_but_nonnegative_report_max_rise() -> None:
    module = _module()

    report = _digest(
        module,
        (
            _row(
                module,
                forecast_heat_index_f=d("88.000000"),
                prior_heat_index_f=d("90.000000"),
            ),
        ),
    )

    assert report.digest_status == "clear"
    assert report.max_heat_index_rise_f == ZERO
    assert report.rows[0].heat_index_rise_f == d("-2.000000")
    assert report.rows[0].reason_codes == (
        "market_research_weather_heat_index_alert_escalation_digest_clear",
    )


def test_heat_index_alert_escalation_validates_contracts_flags_and_duplicates() -> None:
    module = _module()

    cfg = _config(module)
    row = _row(module)
    report = _digest(module, (row,))

    for value in (cfg, row, report, report.rows[0], report.reason_code_counts[0]):
        assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        row.region_id = "phoenix"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].forecast_heat_index_f = d("100.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        _config(module, config_version=_StringSubclass("heat-index-alert-escalation-v0"))
    with pytest.raises(ValueError, match="fresh_snapshot_max_age_seconds"):
        _config(module, fresh_snapshot_max_age_seconds=21600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_heat_index_f"):
        _config(
            module,
            watch_heat_index_f=d("109.000000"),
            block_heat_index_f=d("108.000000"),
        )
    with pytest.raises(ValueError, match="min_public_source_count"):
        _config(module, min_public_source_count=d("1.5"))
    with pytest.raises(ValueError, match="region_id"):
        _row(module, region_id="Phoenix")
    with pytest.raises(ValueError, match="source_id"):
        _row(module, source_id="bad id")
    with pytest.raises(ValueError, match="current_alert_level"):
        _row(module, current_alert_level="warning")
    with pytest.raises(ValueError, match="snapshot_at"):
        _row(module, snapshot_at=datetime(2026, 7, 4, 16, 0))
    with pytest.raises(ValueError, match="snapshot_at"):
        _row(module, snapshot_at=_DateTimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="forecast_heat_index_f"):
        _row(module, forecast_heat_index_f=_DecimalSubclass("101.000000"))
    with pytest.raises(ValueError, match="forecast_hours_until_peak"):
        _row(module, forecast_hours_until_peak=d("-1.000000"))
    with pytest.raises(ValueError, match="market_probability_after"):
        _row(module, market_probability_after=d("1.000001"))
    with pytest.raises(ValueError, match="public_source_count"):
        _row(module, public_source_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="report_only"):
        _row(module, report_only=False)
    with pytest.raises(ValueError, match="config"):
        module.build_market_research_weather_heat_index_alert_escalation_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_market_research_weather_heat_index_alert_escalation_digest(
            (),
            config=cfg,
            generated_at=datetime(2026, 7, 4, 16, 0),
        )
    with pytest.raises(ValueError, match="after generated_at"):
        _digest(module, (_row(module, snapshot_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="unique"):
        _digest(
            module,
            (
                _row(module, "phoenix", "will-phoenix-heat-alert", source_id="source_one"),
                _row(module, "phoenix", "will-phoenix-heat-alert", source_id="source_two"),
            ),
        )
    with pytest.raises(ValueError, match="escalation_status"):
        replace(report.rows[0], escalation_status="blocked")

    unsafe_report = replace(report)
    object.__setattr__(unsafe_report, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.market_research_weather_heat_index_alert_escalation_digest_payload(
            unsafe_report,
        )


def test_dataclasses_are_frozen_and_public_numeric_hints_are_decimal_only() -> None:
    module = _module()

    for cls in (
        module.MarketResearchWeatherHeatIndexAlertEscalationDigestConfig,
        module.MarketResearchWeatherHeatIndexAlertEscalationInputRow,
        module.MarketResearchWeatherHeatIndexAlertEscalationDigestRow,
        module.MarketResearchWeatherHeatIndexAlertEscalationReasonCodeCount,
        module.MarketResearchWeatherHeatIndexAlertEscalationDigestReport,
    ):
        assert cls.__dataclass_params__.frozen is True
        for hint in get_type_hints(cls).values():
            assert not _type_uses_float(hint)
        for field in fields(cls):
            if _is_public_numeric(field.name):
                assert field.type in (Decimal, "Decimal")


def test_static_source_excludes_io_sensitive_surfaces_and_float_literals() -> None:
    module = _module()

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    tree = ast.parse(source)

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )
    for term in (
        "auth",
        "wallet",
        "account",
        "order",
        "cancel",
        "replace",
        "exchange",
        "secret",
        "token",
        "trading",
        "requests",
        "socket",
        "subprocess",
        "open(",
        "sqlite",
        "postgres",
        "redis",
        "httpx",
        "urllib",
    ):
        assert term not in lowered

    forbidden_import_roots = {
        "pathlib",
        "requests",
        "socket",
        "subprocess",
        "supabase",
        "httpx",
        "urllib",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
        "request",
        "post",
        "put",
        "patch",
        "delete",
        "send",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names

    assert inspect.signature(
        module.build_market_research_weather_heat_index_alert_escalation_digest,
    ).parameters["config"].kind is inspect.Parameter.KEYWORD_ONLY


def _is_public_numeric(field_name: str) -> bool:
    if field_name == "reason_code_counts":
        return False
    return any(
        part in field_name
        for part in (
            "count",
            "ratio",
            "seconds",
            "heat_index",
            "_f",
            "hours",
            "population",
            "probability",
            "change",
        )
    )


def _type_uses_float(hint: object) -> bool:
    if hint is float:
        return True
    return any(_type_uses_float(item) for item in getattr(hint, "__args__", ()))


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if type(value) is float:
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


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in _walk_values(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in _walk_values(nested))
    return (value,)
