from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _api():
    return import_module("polymarket_alpha_lab.research_strategy_backtest_readiness_plan")


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    api = _api()
    values: dict[str, object] = {
        "config_version": "research-strategy-backtest-readiness-plan-v0",
        "min_historical_sample_count": d("100.000000"),
        "min_settlement_label_coverage_ratio": d("0.950000"),
        "min_fee_assumption_count": d("2.000000"),
        "min_calibration_bucket_count": d("5.000000"),
        "max_probability_calibration_error": d("0.030000"),
        "min_team_memory_reference_count": d("3.000000"),
        "min_team_memory_coverage_ratio": d("0.800000"),
    }
    values.update(overrides)
    return api.ResearchStrategyBacktestReadinessPlanConfig(**values)


def _readiness_input(**overrides: object):
    api = _api()
    values: dict[str, object] = {
        "strategy_family": "probability_calibration_research",
        "historical_sample_count": d("120.000000"),
        "settled_label_count": d("120.000000"),
        "unresolved_label_count": d("0.000000"),
        "ambiguous_label_count": d("0.000000"),
        "fee_assumption_count": d("3.000000"),
        "fee_model_documented": True,
        "calibration_bucket_count": d("6.000000"),
        "mean_absolute_calibration_error": d("0.020000"),
        "team_memory_reference_count": d("4.000000"),
        "team_memory_coverage_ratio": d("0.900000"),
        "local_supabase_postgres_plan": (
            "load_closed_prediction_snapshots",
            "collect_final_resolution_labels",
            "snapshot_fee_schedule_assumptions",
            "bucket_forecast_probabilities",
            "snapshot_team_memory_references",
        ),
    }
    values.update(overrides)
    return api.ResearchStrategyBacktestReadinessPlanInput(**values)


def _report(readiness_input: object | None = None, *, cfg=None, generated_at=GENERATED_AT):
    api = _api()
    return api.build_research_strategy_backtest_readiness_plan(
        readiness_input or _readiness_input(),
        config=cfg or _config(),
        generated_at=generated_at,
    )


def test_plan_marks_pass_watch_and_block_areas_for_backtest_preparation() -> None:
    api = _api()
    report = _report(
        _readiness_input(
            historical_sample_count=d("80.000000"),
            settled_label_count=d("95.000000"),
            unresolved_label_count=d("5.000000"),
            fee_assumption_count=d("0.000000"),
            fee_model_documented=False,
            calibration_bucket_count=d("4.000000"),
            team_memory_coverage_ratio=d("0.700000"),
        ),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is api.ResearchStrategyBacktestReadinessPlanReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-strategy-backtest-readiness-plan-v0"
    assert report.area_count == d("5.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("3.000000")
    assert report.block_count == d("1.000000")
    assert report.status == "block"
    assert report.reason_codes == (
        "blocked_backtest_readiness_area",
        "watch_backtest_readiness_area",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.area, row.status) for row in report.rows) == (
        ("historical_samples", "watch"),
        ("settlement_labels", "pass"),
        ("fee_assumptions", "block"),
        ("probability_calibration", "watch"),
        ("team_memory", "watch"),
    )
    assert report.rows[0].observed_value == d("80.000000")
    assert report.rows[0].required_value == d("100.000000")
    assert report.rows[0].coverage_ratio == d("0.800000")
    assert report.rows[0].reason_codes == ("historical_sample_count_watch",)
    assert report.rows[2].reason_codes == (
        "fee_assumption_count_block",
        "fee_model_not_documented",
    )
    assert report.rows[3].reason_codes == ("calibration_bucket_count_watch",)
    assert report.rows[4].reason_codes == ("team_memory_coverage_watch",)


def test_pass_plan_is_json_ready_decimal_only_and_contains_local_data_requirements() -> None:
    api = _api()
    report = _report()
    payload = api.research_strategy_backtest_readiness_plan_payload(report)

    assert report.status == "pass"
    assert report.reason_codes == ("research_strategy_backtest_readiness_plan_pass",)
    assert tuple(row.status for row in report.rows) == (
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
    )
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["area_count"] == "5.000000"
    assert payload["pass_count"] == "5.000000"
    assert payload["rows"][0]["observed_value"] == "120.000000"
    assert payload["rows"][1]["coverage_ratio"] == "1.000000"
    assert payload["local_supabase_postgres_requirements"] == [
        "load_closed_prediction_snapshots",
        "collect_final_resolution_labels",
        "snapshot_fee_schedule_assumptions",
        "bucket_forecast_probabilities",
        "snapshot_team_memory_references",
        "compute_readiness_gaps_locally",
    ]
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_floats(payload)
    _assert_no_forbidden_public_identifiers(payload)
    _assert_no_trading_advice(payload)


def test_plan_blocks_empty_history_labels_calibration_and_team_memory() -> None:
    report = _report(
        _readiness_input(
            historical_sample_count=d("0.000000"),
            settled_label_count=d("0.000000"),
            unresolved_label_count=d("8.000000"),
            ambiguous_label_count=d("1.000000"),
            calibration_bucket_count=d("0.000000"),
            team_memory_reference_count=d("0.000000"),
            team_memory_coverage_ratio=d("0.000000"),
        ),
    )

    assert report.status == "block"
    assert report.block_count == d("4.000000")
    assert report.watch_count == d("0.000000")
    assert tuple(row.status for row in report.rows) == (
        "block",
        "block",
        "pass",
        "block",
        "block",
    )
    assert report.rows[1].reason_codes == (
        "ambiguous_settlement_labels_present",
        "settlement_label_count_block",
        "settlement_label_coverage_watch",
    )
    assert report.rows[3].reason_codes == ("calibration_bucket_count_block",)
    assert report.rows[4].reason_codes == ("team_memory_reference_count_block",)


def test_payload_rejects_public_identifiers_and_trading_advice_surfaces() -> None:
    api = _api()
    report = _report()

    bad_identifier = _bypassed_row(
        report,
        local_supabase_postgres_requirements=("market_slug",),
    )
    with pytest.raises(ValueError, match="public identifier"):
        api.research_strategy_backtest_readiness_plan_payload(bad_identifier)

    bad_advice = _bypassed_row(report.rows[0], reason_codes=("buy_yes_contracts",))
    bad_report = _bypassed_row(report, rows=(bad_advice, *report.rows[1:]))
    with pytest.raises(ValueError, match="trading advice"):
        api.research_strategy_backtest_readiness_plan_payload(bad_report)


def test_dataclasses_are_frozen_strict_decimal_utc_and_flag_guarded() -> None:
    api = _api()
    report = _report()

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        _config(min_historical_sample_count=100)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        _config(min_historical_sample_count=_DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="historical_sample_count"):
        _readiness_input(historical_sample_count=120)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fee_model_documented"):
        _readiness_input(fee_model_documented=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        _report(generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="UTC offset"):
        _report(generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at"):
        _report(generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="config"):
        api.build_research_strategy_backtest_readiness_plan(
            _readiness_input(),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        _config(paper_only=False)

    for field_name in (
        "area_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        assert type(getattr(report, field_name)) is Decimal
    for field_name in ("observed_value", "required_value", "coverage_ratio"):
        assert type(getattr(report.rows[0], field_name)) is Decimal


def test_report_rejects_inconsistent_counts_and_nonpublic_plan_terms() -> None:
    from dataclasses import replace

    report = _report()

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("4.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="local_supabase_postgres_plan"):
        _readiness_input(local_supabase_postgres_plan=("raw_source_archive",))
    with pytest.raises(ValueError, match="settlement label counts"):
        _readiness_input(
            settled_label_count=d("1.000000"),
            unresolved_label_count=d("-1.000000"),
        )


def test_module_scope_is_pure_report_only_without_database_connections() -> None:
    module = _api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name is not None:
                called_names.add(call_name.rsplit(".", maxsplit=1)[-1])

    assert imported_modules == {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
        "polymarket_alpha_lab.team_paper_guard",
    }
    assert {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "open",
        "print",
        "read_text",
        "request",
        "send",
        "write_text",
    }.isdisjoint(called_names)

    report = _report()
    field_names = {field.name for field in fields(report)}
    row_field_names = {field.name for field in fields(report.rows[0])}
    for forbidden in module.PUBLIC_IDENTIFIER_FRAGMENTS:
        assert all(forbidden not in name for name in field_names | row_field_names)
    assert "local_supabase_postgres_requirements" in field_names


def _bypassed_row(row: object, **overrides: Any) -> object:
    malformed = object.__new__(type(row))
    for key, value in row.__dict__.items():
        object.__setattr__(malformed, key, value)
    for key, value in overrides.items():
        object.__setattr__(malformed, key, value)
    return malformed


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, list | tuple):
        for item in value:
            _assert_no_floats(item)


def _assert_no_forbidden_public_identifiers(value: object) -> None:
    forbidden = ("dsn", "table", "token", "source", "market")
    if isinstance(value, dict):
        for key, item in value.items():
            assert all(fragment not in key.lower() for fragment in forbidden)
            _assert_no_forbidden_public_identifiers(item)
    elif isinstance(value, str):
        assert all(fragment not in value.lower() for fragment in forbidden)
    elif isinstance(value, list | tuple):
        for item in value:
            _assert_no_forbidden_public_identifiers(item)


def _assert_no_trading_advice(value: object) -> None:
    forbidden = ("buy", "sell", "bet", "stake", "position", "entry", "exit")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_trading_advice(item)
    elif isinstance(value, str):
        assert all(fragment not in value.lower() for fragment in forbidden)
    elif isinstance(value, list | tuple):
        for item in value:
            _assert_no_trading_advice(item)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None
