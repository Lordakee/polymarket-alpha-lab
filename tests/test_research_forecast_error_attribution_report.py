from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_forecast_error_attribution_report import (
    DEFAULT_RESEARCH_FORECAST_ERROR_ATTRIBUTION_CONFIG_VERSION,
    ResearchForecastErrorAttributionConfig,
    ResearchForecastErrorAttributionInputRow,
    ResearchForecastErrorAttributionReasonCodeCount,
    ResearchForecastErrorAttributionReport,
    ResearchForecastErrorAttributionRow,
    build_research_forecast_error_attribution_report,
    research_forecast_error_attribution_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_forecast_error_attribution_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchForecastErrorAttributionConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_FORECAST_ERROR_ATTRIBUTION_CONFIG_VERSION,
        "material_error_watch_threshold": d("0.100000"),
        "material_error_block_threshold": d("0.350000"),
        "component_watch_threshold": d("0.200000"),
        "component_block_threshold": d("0.600000"),
    }
    values.update(overrides)
    return ResearchForecastErrorAttributionConfig(**values)


def input_row(
    review_key: str = "forecast.energy.reserve.pass",
    *,
    condition_id: str = "condition_energy_reserve_pass",
    forecast_group: str = "energy_reserve",
    public_resolution_reference: str = "public-resolution-memo",
    forecast_made_at: datetime | None = None,
    resolved_at: datetime | None = None,
    forecast_probability: Decimal = d("0.520000"),
    resolved_probability: Decimal = d("0.560000"),
    information_gap_score: Decimal = d("0.050000"),
    model_disagreement_score: Decimal = d("0.050000"),
    settlement_ambiguity_score: Decimal = d("0.050000"),
    cost_friction_score: Decimal = d("0.050000"),
    team_memory_gap_score: Decimal = d("0.050000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchForecastErrorAttributionInputRow:
    return ResearchForecastErrorAttributionInputRow(
        review_key=review_key,
        condition_id=condition_id,
        forecast_group=forecast_group,
        public_resolution_reference=public_resolution_reference,
        forecast_made_at=forecast_made_at or GENERATED_AT - timedelta(days=2),
        resolved_at=resolved_at or GENERATED_AT - timedelta(hours=2),
        forecast_probability=forecast_probability,
        resolved_probability=resolved_probability,
        information_gap_score=information_gap_score,
        model_disagreement_score=model_disagreement_score,
        settlement_ambiguity_score=settlement_ambiguity_score,
        cost_friction_score=cost_friction_score,
        team_memory_gap_score=team_memory_gap_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchForecastErrorAttributionConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchForecastErrorAttributionReport:
    return build_research_forecast_error_attribution_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if (
            field.name.endswith(
                (
                    "_count",
                    "_error",
                    "_probability",
                    "_ratio",
                    "_score",
                    "_seconds",
                    "_threshold",
                ),
            )
            or "probability" in field.name
        ):
            assert type(item) is Decimal


def test_forecast_error_attribution_reduces_rows_redacts_refs_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "forecast.energy.reserve.watch",
                condition_id="condition_energy_reserve_watch",
                forecast_group="energy_reserve",
                public_resolution_reference="public-resolution-bulletin",
                forecast_probability=d("0.600000"),
                resolved_probability=d("0.450000"),
                information_gap_score=d("0.320000"),
                model_disagreement_score=d("0.250000"),
                settlement_ambiguity_score=d("0.100000"),
                cost_friction_score=d("0.300000"),
                team_memory_gap_score=d("0.050000"),
            ),
            input_row(
                "forecast.energy.reserve.block",
                condition_id="condition_energy_reserve_block",
                forecast_group="energy_reserve",
                public_resolution_reference=(
                    "https://vendor.example/resolution?credential=hidden"
                ),
                forecast_probability=d("0.200000"),
                resolved_probability=d("0.900000"),
                information_gap_score=d("0.100000"),
                model_disagreement_score=d("0.150000"),
                settlement_ambiguity_score=d("0.720000"),
                cost_friction_score=d("0.050000"),
                team_memory_gap_score=d("0.610000"),
            ),
            input_row(),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_FORECAST_ERROR_ATTRIBUTION_CONFIG_VERSION
    )
    assert summary.attribution_status == "block"
    assert summary.next_step == "block_report_only_forecast_error_attribution_review"
    assert summary.forecast_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.material_error_count == d("2.000000")
    assert summary.information_gap_count == d("1.000000")
    assert summary.model_disagreement_count == d("1.000000")
    assert summary.settlement_ambiguity_count == d("1.000000")
    assert summary.cost_friction_count == d("1.000000")
    assert summary.team_memory_missing_count == d("1.000000")
    assert summary.average_forecast_error == d("0.296667")
    assert summary.max_forecast_error == d("0.700000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.attribution_status, row.review_key) for row in summary.rows) == (
        ("block", "forecast.energy.reserve.block"),
        ("watch", "forecast.energy.reserve.watch"),
        ("pass", "forecast.energy.reserve.pass"),
    )

    blocked = summary.rows[0]
    assert blocked.forecast_error == d("0.700000")
    assert blocked.resolution_lag_seconds == d("165600.000000")
    assert blocked.redacted_resolution_reference == "sha256:63d3e5245be7"
    assert blocked.reason_codes == (
        "research_forecast_error_attribution_report_material_forecast_error",
        "research_forecast_error_attribution_report_settlement_ambiguity",
        "research_forecast_error_attribution_report_team_memory_missing",
    )

    watched = summary.rows[1]
    assert watched.forecast_error == d("0.150000")
    assert watched.redacted_resolution_reference == "public-resolution-bulletin"
    assert watched.reason_codes == (
        "research_forecast_error_attribution_report_material_forecast_error",
        "research_forecast_error_attribution_report_information_gap",
        "research_forecast_error_attribution_report_model_disagreement",
        "research_forecast_error_attribution_report_cost_friction",
    )

    passed = summary.rows[2]
    assert passed.forecast_error == d("0.040000")
    assert passed.redacted_resolution_reference == "public-resolution-memo"
    assert passed.reason_codes == (
        "research_forecast_error_attribution_report_pass",
    )

    assert summary.reason_code_counts == (
        ResearchForecastErrorAttributionReasonCodeCount(
            reason_code=(
                "research_forecast_error_attribution_report_material_forecast_error"
            ),
            count=d("2.000000"),
            forecast_ratio=d("0.666667"),
        ),
        ResearchForecastErrorAttributionReasonCodeCount(
            reason_code="research_forecast_error_attribution_report_information_gap",
            count=d("1.000000"),
            forecast_ratio=d("0.333333"),
        ),
        ResearchForecastErrorAttributionReasonCodeCount(
            reason_code="research_forecast_error_attribution_report_model_disagreement",
            count=d("1.000000"),
            forecast_ratio=d("0.333333"),
        ),
        ResearchForecastErrorAttributionReasonCodeCount(
            reason_code="research_forecast_error_attribution_report_settlement_ambiguity",
            count=d("1.000000"),
            forecast_ratio=d("0.333333"),
        ),
        ResearchForecastErrorAttributionReasonCodeCount(
            reason_code="research_forecast_error_attribution_report_cost_friction",
            count=d("1.000000"),
            forecast_ratio=d("0.333333"),
        ),
        ResearchForecastErrorAttributionReasonCodeCount(
            reason_code="research_forecast_error_attribution_report_team_memory_missing",
            count=d("1.000000"),
            forecast_ratio=d("0.333333"),
        ),
        ResearchForecastErrorAttributionReasonCodeCount(
            reason_code="research_forecast_error_attribution_report_pass",
            count=d("1.000000"),
            forecast_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for value in (
        "hidden",
        "vendor.example",
        "https://",
        "credential",
    ):
        assert value not in public


def test_empty_forecast_error_attribution_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.attribution_status == "block"
    assert summary.next_step == "block_report_only_forecast_error_attribution_review"
    assert summary.forecast_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_forecast_error == ZERO
    assert summary.max_forecast_error == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchForecastErrorAttributionReasonCodeCount(
            reason_code="research_forecast_error_attribution_report_no_inputs",
            count=d("1.000000"),
            forecast_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "research_forecast_error_attribution_report_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_forecast_error_attribution_honors_custom_threshold_config() -> None:
    summary = report(
        (
            input_row(
                forecast_probability=d("0.520000"),
                resolved_probability=d("0.560000"),
                information_gap_score=d("0.120000"),
            ),
        ),
        cfg=config(
            material_error_watch_threshold=d("0.900000"),
            material_error_block_threshold=d("1.000000"),
            component_watch_threshold=d("0.100000"),
            component_block_threshold=d("0.900000"),
        ),
    )

    assert summary.attribution_status == "watch"
    assert summary.watch_count == d("1.000000")
    assert summary.rows[0].attribution_status == "watch"
    assert summary.rows[0].reason_codes == (
        "research_forecast_error_attribution_report_information_gap",
    )


def test_forecast_error_attribution_payload_uses_decimal_strings_and_redacts() -> None:
    summary = report((input_row(),))
    payload = research_forecast_error_attribution_report_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["forecast_count"] == "1.000000"
    assert payload["average_forecast_error"] == "0.040000"
    assert payload["rows"][0]["forecast_probability"] == "0.520000"
    assert payload["rows"][0]["forecast_error"] == "0.040000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_resolution_reference':" not in repr(payload)
    assert "credential" not in repr(payload).lower()


def test_forecast_error_attribution_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(ResearchForecastErrorAttributionConfig)
    assert is_dataclass(ResearchForecastErrorAttributionInputRow)
    assert is_dataclass(ResearchForecastErrorAttributionRow)
    assert is_dataclass(ResearchForecastErrorAttributionReasonCodeCount)
    assert is_dataclass(ResearchForecastErrorAttributionReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.forecast_probability = d("0.400000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].forecast_error = d("0.400000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.forecast_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("forecast-error-v0"))
    with pytest.raises(ValueError, match="material_error_watch_threshold"):
        config(material_error_watch_threshold=Decimal("NaN"))
    with pytest.raises(ValueError, match="material_error_block_threshold"):
        config(
            material_error_watch_threshold=d("0.800000"),
            material_error_block_threshold=d("0.700000"),
        )
    with pytest.raises(ValueError, match="component_watch_threshold"):
        config(component_watch_threshold=d("-0.000001"))
    with pytest.raises(ValueError, match="component_block_threshold"):
        config(
            component_watch_threshold=d("0.700000"),
            component_block_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="review_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id="condition_live_surface")
    with pytest.raises(ValueError, match="forecast_made_at"):
        input_row(forecast_made_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="resolved_at"):
        input_row(resolved_at=_DateTimeSubclass(2026, 7, 6, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="forecast_probability"):
        input_row(forecast_probability=0.520000)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolved_probability"):
        input_row(resolved_probability=d("1.000001"))
    with pytest.raises(ValueError, match="information_gap_score"):
        input_row(information_gap_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="model_disagreement_score"):
        input_row(model_disagreement_score=Decimal("Infinity"))
    with pytest.raises(ValueError, match="settlement_ambiguity_score"):
        input_row(settlement_ambiguity_score=d("-0.000001"))
    with pytest.raises(ValueError, match="cost_friction_score"):
        input_row(cost_friction_score=d("1.000001"))
    with pytest.raises(ValueError, match="team_memory_gap_score"):
        input_row(team_memory_gap_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_forecast_error_attribution_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_forecast_error_attribution_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 6, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    passed = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            passed,
            reason_codes=(
                "research_forecast_error_attribution_report_pass",
                "research_forecast_error_attribution_report_information_gap",
            ),
        )
    with pytest.raises(ValueError, match="attribution_status"):
        replace(passed, attribution_status="block")
    with pytest.raises(ValueError, match="forecast_error"):
        replace(passed, forecast_error=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_resolution_reference"):
        replace(passed, redacted_resolution_reference="https://host?credential=hidden")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report((input_row(),)), pass_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report((input_row(),)), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report((input_row(),)), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report((input_row(),)), readonly=False)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("forecast.energy.reserve.z", forecast_group="zeta_rules"),
                input_row(),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    source_row = input_row()
    summary = report((source_row,))

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_store_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "advice",
        "market_slug",
        "question",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "network",
        "database",
        "durable",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered
