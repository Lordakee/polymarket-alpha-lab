from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_revision_quality_gate import (
    DEFAULT_FORECAST_REVISION_QUALITY_GATE_CONFIG_VERSION,
    ForecastRevisionQualityGateConfig,
    ForecastRevisionQualityGateReport,
    ForecastRevisionQualityGateRow,
    ForecastRevisionRow,
    build_forecast_revision_quality_gate,
    forecast_revision_quality_gate_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def test_builds_readonly_report_with_decimal_counts_digest_and_payload_strings() -> None:
    report = build_forecast_revision_quality_gate(
        (
            _revision("forecast-b", revision_age_hours=Decimal("30.000000")),
            _revision("forecast-a"),
        ),
        config=ForecastRevisionQualityGateConfig(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, ForecastRevisionQualityGateReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == DEFAULT_FORECAST_REVISION_QUALITY_GATE_CONFIG_VERSION
    assert report.gate_status == "watch"
    assert report.gate_next_step == "review_forecast_revision_cadence"
    assert report.forecast_count == Decimal("2.000000")
    assert report.revision_count == Decimal("2.000000")
    assert report.passing_revision_count == Decimal("1.000000")
    assert report.watch_revision_count == Decimal("1.000000")
    assert report.blocked_revision_count == Decimal("0.000000")
    assert report.passing_revision_ratio == Decimal("0.500000")
    assert report.watch_revision_ratio == Decimal("0.500000")
    assert report.blocked_revision_ratio == Decimal("0.000000")
    assert report.reason_codes == (
        "forecast_revision_quality_gate_stale_revision_present",
    )
    assert tuple(row.forecast_id for row in report.rows) == ("forecast-b", "forecast-a")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    payload = forecast_revision_quality_gate_payload(report)
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["forecast_count"] == "2.000000"
    assert payload["passing_revision_ratio"] == "0.500000"
    assert payload["rows"][0]["revision_age_hours"] == "30.000000"
    assert payload["rows"][1]["probability_delta"] == "0.020000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _decimal_values_are_strings(payload)


def test_blocks_missing_rationale_delta_and_stale_unchanged_failures() -> None:
    report = build_forecast_revision_quality_gate(
        (
            _revision(
                "forecast-stale",
                prior_probability=Decimal("0.400000"),
                revised_probability=Decimal("0.400000"),
                probability_delta=Decimal("0.000000"),
                revision_age_hours=Decimal("50.000000"),
            ),
            _revision("forecast-missing", revision_rationale="   "),
            _revision(
                "forecast-large-delta",
                prior_probability=Decimal("0.100000"),
                revised_probability=Decimal("0.550000"),
                probability_delta=Decimal("0.450000"),
            ),
        ),
        config=ForecastRevisionQualityGateConfig(
            max_revision_age_hours=Decimal("24.000000"),
            stale_unchanged_age_hours=Decimal("36.000000"),
            max_abs_probability_delta=Decimal("0.300000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.gate_next_step == "block_forecast_revision_until_remediated"
    assert report.revision_count == Decimal("3.000000")
    assert report.blocked_revision_count == Decimal("3.000000")
    assert report.blocked_revision_ratio == Decimal("1.000000")
    assert report.reason_codes == (
        "forecast_revision_quality_gate_stale_revision_present",
        "forecast_revision_quality_gate_missing_rationale_present",
        "forecast_revision_quality_gate_probability_delta_out_of_bounds_present",
        "forecast_revision_quality_gate_stale_unchanged_forecast_present",
    )
    assert tuple(row.forecast_id for row in report.rows) == (
        "forecast-large-delta",
        "forecast-missing",
        "forecast-stale",
    )
    assert report.rows[0].reason_codes == (
        "forecast_revision_quality_gate_probability_delta_out_of_bounds",
    )
    assert report.rows[1].reason_codes == (
        "forecast_revision_quality_gate_missing_rationale",
    )
    assert report.rows[2].reason_codes == (
        "forecast_revision_quality_gate_stale_revision",
        "forecast_revision_quality_gate_stale_unchanged_forecast",
    )


def test_empty_revision_rows_are_readonly_blocked_report() -> None:
    report = build_forecast_revision_quality_gate(
        (),
        config=ForecastRevisionQualityGateConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.reason_codes == ("forecast_revision_quality_gate_empty_rows",)
    assert report.forecast_count == Decimal("0.000000")
    assert report.revision_count == Decimal("0.000000")
    assert report.passing_revision_ratio is None
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_dataclasses_are_frozen_decimal_only_and_hard_flags_are_enforced() -> None:
    with pytest.raises(ValueError, match="config_version"):
        ForecastRevisionQualityGateConfig(config_version=_StringSubclass("v1"))
    with pytest.raises(ValueError, match="max_revision_age_hours"):
        ForecastRevisionQualityGateConfig(max_revision_age_hours=24)
    with pytest.raises(ValueError, match="max_revision_age_hours"):
        ForecastRevisionQualityGateConfig(max_revision_age_hours=_DecimalSubclass("24"))
    with pytest.raises(ValueError, match="min_rationale_character_count"):
        ForecastRevisionQualityGateConfig(min_rationale_character_count=1)
    with pytest.raises(ValueError, match="probability_delta"):
        _revision("forecast-a", probability_delta="0.020000")
    with pytest.raises(ValueError, match="probability_delta"):
        _revision("forecast-a", probability_delta=Decimal("NaN"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_revision("forecast-a"), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        ForecastRevisionQualityGateConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        ForecastRevisionQualityGateConfig(readonly=False)

    report = build_forecast_revision_quality_gate(
        (_revision("forecast-a"),),
        config=ForecastRevisionQualityGateConfig(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.paper_only = False
    with pytest.raises(FrozenInstanceError):
        report.rows[0].gate_status = "blocked"


def test_derived_validation_digest_is_tamper_evident() -> None:
    report = build_forecast_revision_quality_gate(
        (_revision("forecast-a"),),
        config=ForecastRevisionQualityGateConfig(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="forecast_count"):
        replace(report, forecast_count=Decimal("2.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=())


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("forecast_id", "live-surface"),
        ("forecast_id", "auth-surface"),
        ("forecast_id", "wallet-surface"),
        ("forecast_id", "order-surface"),
        ("forecast_id", "network-surface"),
        ("forecast_id", "database-surface"),
        ("forecast_id", "persist-surface"),
        ("revision_rationale", "connect wallet before review"),
    ),
)
def test_unsafe_public_surface_values_are_rejected(
    field_name: str,
    field_value: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe surface"):
        if field_name == "forecast_id":
            _revision(field_value)
        else:
            _revision("forecast-a", **{field_name: field_value})


def test_payload_rejects_unsafe_public_payload_keys() -> None:
    module = importlib.import_module("polymarket_alpha_lab.forecast_revision_quality_gate")
    report = build_forecast_revision_quality_gate(
        (_revision("forecast-a"),),
        config=ForecastRevisionQualityGateConfig(),
        generated_at=GENERATED_AT,
    )

    payload = forecast_revision_quality_gate_payload(report)
    with pytest.raises(ValueError, match="unsafe surface"):
        module._reject_unsafe_public_payload("payload", {"wallet": payload})
    with pytest.raises(ValueError, match="unsafe surface"):
        module._reject_unsafe_public_payload("payload", {"safe": {"order": "x"}})

    rendered = repr(payload).lower()
    for token in (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "buy",
        "sell",
    ):
        assert token not in rendered


def test_module_scope_excludes_execution_and_storage_surfaces() -> None:
    module = importlib.import_module("polymarket_alpha_lab.forecast_revision_quality_gate")
    assert module.__all__ == (
        "DEFAULT_FORECAST_REVISION_QUALITY_GATE_CONFIG_VERSION",
        "ForecastRevisionQualityGateConfig",
        "ForecastRevisionQualityGateReport",
        "ForecastRevisionQualityGateRow",
        "ForecastRevisionRow",
        "build_forecast_revision_quality_gate",
        "forecast_revision_quality_gate_payload",
    )

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "supabase",
        "subprocess",
        "pathlib",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _revision(forecast_id: str, **overrides: object) -> ForecastRevisionRow:
    values = {
        "forecast_id": forecast_id,
        "revision_sequence": Decimal("1.000000"),
        "prior_probability": Decimal("0.480000"),
        "revised_probability": Decimal("0.500000"),
        "probability_delta": Decimal("0.020000"),
        "revision_age_hours": Decimal("6.000000"),
        "revision_rationale": "new evidence changed the forecast",
    }
    values.update(overrides)
    return ForecastRevisionRow(**values)


def _decimal_values_are_strings(value: object) -> bool:
    if isinstance(value, Decimal):
        return False
    if isinstance(value, dict):
        return all(_decimal_values_are_strings(item) for item in value.values())
    if isinstance(value, list):
        return all(_decimal_values_are_strings(item) for item in value)
    return True
