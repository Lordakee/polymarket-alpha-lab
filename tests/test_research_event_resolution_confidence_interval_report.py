from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_event_resolution_confidence_interval_report import (
    DEFAULT_RESEARCH_EVENT_RESOLUTION_CONFIDENCE_INTERVAL_CONFIG_VERSION,
    ResearchEventResolutionConfidenceIntervalConfig,
    ResearchEventResolutionConfidenceIntervalObservation,
    ResearchEventResolutionConfidenceIntervalReasonCodeCount,
    ResearchEventResolutionConfidenceIntervalReport,
    ResearchEventResolutionConfidenceIntervalRow,
    build_research_event_resolution_confidence_interval_report,
    research_event_resolution_confidence_interval_report_digest,
    research_event_resolution_confidence_interval_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_event_resolution_confidence_interval_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchEventResolutionConfidenceIntervalConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_RESOLUTION_CONFIDENCE_INTERVAL_CONFIG_VERSION
        ),
        "pass_quality_threshold": d("0.750000"),
        "watch_quality_threshold": d("0.500000"),
        "max_pass_interval_width": d("0.250000"),
        "max_watch_interval_width": d("0.500000"),
        "min_pass_evidence_quality": d("0.700000"),
        "min_watch_evidence_quality": d("0.450000"),
        "max_pass_contradiction_pressure": d("0.200000"),
        "max_watch_contradiction_pressure": d("0.500000"),
        "min_pass_source_reliability": d("0.700000"),
        "min_watch_source_reliability": d("0.450000"),
        "min_pass_rule_clarity": d("0.700000"),
        "min_watch_rule_clarity": d("0.450000"),
        "min_pass_historical_calibration": d("0.700000"),
        "min_watch_historical_calibration": d("0.450000"),
        "evidence_quality_weight": d("0.250000"),
        "contradiction_pressure_weight": d("0.150000"),
        "source_reliability_weight": d("0.200000"),
        "rule_clarity_weight": d("0.200000"),
        "historical_calibration_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchEventResolutionConfidenceIntervalConfig(**values)


def observation(
    resolution_scope: str = "macro_policy",
    *,
    observed_at: datetime | None = None,
    aggregate_evidence_quality: Decimal = d("0.840000"),
    contradiction_pressure: Decimal = d("0.120000"),
    source_reliability: Decimal = d("0.780000"),
    rule_clarity: Decimal = d("0.800000"),
    historical_calibration: Decimal = d("0.760000"),
    confidence_interval_width: Decimal = d("0.180000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventResolutionConfidenceIntervalObservation:
    return ResearchEventResolutionConfidenceIntervalObservation(
        resolution_scope=resolution_scope,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
        aggregate_evidence_quality=aggregate_evidence_quality,
        contradiction_pressure=contradiction_pressure,
        source_reliability=source_reliability,
        rule_clarity=rule_clarity,
        historical_calibration=historical_calibration,
        confidence_interval_width=confidence_interval_width,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchEventResolutionConfidenceIntervalConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventResolutionConfidenceIntervalReport:
    return build_research_event_resolution_confidence_interval_report(
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
        if field.name in {
            "paper_only",
            "report_only",
            "readonly",
            "reason_code_counts",
            "reason_codes",
            "rows",
        }:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if any(
            token in field.name
            for token in (
                "calibration",
                "count",
                "pressure",
                "quality",
                "ratio",
                "reliability",
                "score",
                "width",
            )
        ):
            assert type(item) is Decimal


def test_confidence_interval_report_scores_sorts_and_summarizes_quality() -> None:
    summary = report(
        (
            observation(
                "macro_policy",
                observed_at=GENERATED_AT - timedelta(hours=1),
                aggregate_evidence_quality=d("0.840000"),
                contradiction_pressure=d("0.120000"),
                source_reliability=d("0.780000"),
                rule_clarity=d("0.800000"),
                historical_calibration=d("0.760000"),
                confidence_interval_width=d("0.180000"),
            ),
            observation(
                "weather_resolution",
                observed_at=GENERATED_AT - timedelta(hours=3),
                aggregate_evidence_quality=d("0.620000"),
                contradiction_pressure=d("0.300000"),
                source_reliability=d("0.680000"),
                rule_clarity=d("0.600000"),
                historical_calibration=d("0.640000"),
                confidence_interval_width=d("0.340000"),
            ),
            observation(
                "ambiguous_rules",
                observed_at=GENERATED_AT - timedelta(hours=6),
                aggregate_evidence_quality=d("0.400000"),
                contradiction_pressure=d("0.620000"),
                source_reliability=d("0.410000"),
                rule_clarity=d("0.300000"),
                historical_calibration=d("0.420000"),
                confidence_interval_width=d("0.620000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_CONFIDENCE_INTERVAL_CONFIG_VERSION
    )
    assert summary.status == "block"
    assert summary.next_step == "block_report_only_event_resolution_confidence_interval"
    assert summary.observation_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_quality_score == d("0.612333")
    assert summary.average_interval_width == d("0.380000")
    assert summary.average_contradiction_pressure == d("0.346667")
    assert summary.min_rule_clarity == d("0.300000")
    assert summary.min_historical_calibration == d("0.420000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.status, row.resolution_scope) for row in summary.rows) == (
        ("block", "ambiguous_rules"),
        ("watch", "weather_resolution"),
        ("pass", "macro_policy"),
    )

    blocked = summary.rows[0]
    assert blocked.quality_score == d("0.383000")
    assert blocked.observation_age_seconds == d("21600.000000")
    assert blocked.reason_codes == (
        "event_resolution_ci_quality_below_watch",
        "event_resolution_ci_contradiction_pressure_high",
        "event_resolution_ci_source_reliability_low",
        "event_resolution_ci_rule_clarity_low",
        "event_resolution_ci_historical_calibration_low",
        "event_resolution_ci_interval_too_wide",
    )

    watch = summary.rows[1]
    assert watch.quality_score == d("0.644000")
    assert watch.reason_codes == (
        "event_resolution_ci_quality_between_watch_and_pass",
        "event_resolution_ci_contradiction_pressure_elevated",
        "event_resolution_ci_interval_watch",
    )

    passed = summary.rows[2]
    assert passed.quality_score == d("0.810000")
    assert passed.reason_codes == ("event_resolution_ci_pass",)

    assert summary.reason_code_counts == (
        ResearchEventResolutionConfidenceIntervalReasonCodeCount(
            reason_code="event_resolution_ci_quality_below_watch",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        ResearchEventResolutionConfidenceIntervalReasonCodeCount(
            reason_code="event_resolution_ci_contradiction_pressure_high",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        ResearchEventResolutionConfidenceIntervalReasonCodeCount(
            reason_code="event_resolution_ci_source_reliability_low",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        ResearchEventResolutionConfidenceIntervalReasonCodeCount(
            reason_code="event_resolution_ci_rule_clarity_low",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        ResearchEventResolutionConfidenceIntervalReasonCodeCount(
            reason_code="event_resolution_ci_historical_calibration_low",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        ResearchEventResolutionConfidenceIntervalReasonCodeCount(
            reason_code="event_resolution_ci_interval_too_wide",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        ResearchEventResolutionConfidenceIntervalReasonCodeCount(
            reason_code="event_resolution_ci_quality_between_watch_and_pass",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        ResearchEventResolutionConfidenceIntervalReasonCodeCount(
            reason_code="event_resolution_ci_contradiction_pressure_elevated",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        ResearchEventResolutionConfidenceIntervalReasonCodeCount(
            reason_code="event_resolution_ci_interval_watch",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
        ResearchEventResolutionConfidenceIntervalReasonCodeCount(
            reason_code="event_resolution_ci_pass",
            count=d("1.000000"),
            observation_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for value in (
        "event_id",
        "market_id",
        "source_id",
        "condition_id",
        "wallet",
        "order",
        "trade",
        "position",
        "stake",
    ):
        assert value not in public


def test_empty_confidence_interval_report_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.status == "block"
    assert summary.next_step == "block_report_only_event_resolution_confidence_interval"
    assert summary.observation_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_quality_score is None
    assert summary.average_interval_width is None
    assert summary.average_contradiction_pressure is None
    assert summary.min_rule_clarity is None
    assert summary.min_historical_calibration is None
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchEventResolutionConfidenceIntervalReasonCodeCount(
            reason_code="event_resolution_ci_no_inputs",
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == ("event_resolution_ci_no_inputs",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_confidence_interval_payload_and_digest_are_deterministic_public_safe() -> None:
    rows = (
        observation("macro_policy"),
        observation(
            "weather_resolution",
            contradiction_pressure=d("0.300000"),
            confidence_interval_width=d("0.340000"),
        ),
    )
    summary_a = report(tuple(reversed(rows)))
    summary_b = report(rows)
    payload_a = research_event_resolution_confidence_interval_report_payload(summary_a)
    payload_b = research_event_resolution_confidence_interval_report_payload(summary_b)
    digest_a = research_event_resolution_confidence_interval_report_digest(summary_a)
    digest_b = research_event_resolution_confidence_interval_report_digest(summary_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert len(digest_a) == 64
    int(digest_a, 16)
    json.dumps(payload_a, sort_keys=True)
    assert payload_a["observation_count"] == "2.000000"
    assert payload_a["average_quality_score"] == "0.796500"
    assert payload_a["rows"][0]["quality_score"] == "0.783000"
    assert payload_a["paper_only"] is True
    assert payload_a["report_only"] is True
    assert payload_a["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload_a))

    lowered = repr(payload_a).lower()
    for value in (
        "event_id",
        "market_id",
        "source_id",
        "condition_id",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    ):
        assert value not in lowered


def test_confidence_interval_contracts_validate_decimal_inputs_and_flags() -> None:
    assert is_dataclass(ResearchEventResolutionConfidenceIntervalConfig)
    assert is_dataclass(ResearchEventResolutionConfidenceIntervalObservation)
    assert is_dataclass(ResearchEventResolutionConfidenceIntervalRow)
    assert is_dataclass(ResearchEventResolutionConfidenceIntervalReasonCodeCount)
    assert is_dataclass(ResearchEventResolutionConfidenceIntervalReport)

    cfg = config()
    source_row = observation()
    summary = report((source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.aggregate_evidence_quality = d("0.700000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].quality_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.observation_count = d("2.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("config-v0"))
    with pytest.raises(ValueError, match="pass_quality_threshold"):
        config(pass_quality_threshold=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_quality_threshold"):
        config(watch_quality_threshold=d("-0.000001"))
    with pytest.raises(ValueError, match="pass_quality_threshold"):
        config(pass_quality_threshold=d("0.400000"))
    with pytest.raises(ValueError, match="max_pass_interval_width"):
        config(max_pass_interval_width=d("0.600000"))
    with pytest.raises(ValueError, match="min_pass_rule_clarity"):
        config(min_pass_rule_clarity=d("0.300000"))
    with pytest.raises(ValueError, match="weights"):
        config(evidence_quality_weight=d("0.300000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)

    with pytest.raises(ValueError, match="resolution_scope"):
        observation("market:123")
    with pytest.raises(ValueError, match="resolution_scope"):
        observation(_StringSubclass("macro_policy"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="aggregate_evidence_quality"):
        observation(aggregate_evidence_quality=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_pressure"):
        observation(contradiction_pressure=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="source_reliability"):
        observation(source_reliability=d("1.000001"))
    with pytest.raises(ValueError, match="rule_clarity"):
        observation(rule_clarity=Decimal("NaN"))
    with pytest.raises(ValueError, match="historical_calibration"):
        observation(historical_calibration=d("-0.000001"))
    with pytest.raises(ValueError, match="confidence_interval_width"):
        observation(confidence_interval_width=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_event_resolution_confidence_interval_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_event_resolution_confidence_interval_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations"):
        report((object(),))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(observed_at=GENERATED_AT + timedelta(seconds=1)),))


def test_confidence_interval_report_rejects_manual_drift() -> None:
    passed = report((observation(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(passed, reason_codes=("event_resolution_ci_interval_watch",))
    with pytest.raises(ValueError, match="status"):
        replace(passed, status="block")
    with pytest.raises(ValueError, match="quality_score"):
        replace(passed, quality_score=d("0.100000"))

    summary = report((observation(),))
    with pytest.raises(ValueError, match="pass_count"):
        replace(summary, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                observation("weather_resolution", contradiction_pressure=d("0.300000")),
                observation("macro_policy"),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)


def test_public_numeric_fields_are_decimals() -> None:
    source_row = observation()
    summary = report((source_row,))

    assert_decimal_numeric_fields(config())
    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_store_identifier_or_execution_surfaces() -> None:
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
        "private_key",
        "api_key",
        "secret",
        "order",
        "trade",
        "position",
        "stake",
        "sizing",
        "recommendation",
        "event_id",
        "market_id",
        "source_id",
        "condition_id",
        "clob",
        "http",
        "socket",
        "subprocess",
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

    exported = set(
        importlib.import_module(
            "polymarket_alpha_lab."
            "research_event_resolution_confidence_interval_report",
        ).__all__,
    )
    assert exported == {
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_CONFIDENCE_INTERVAL_CONFIG_VERSION",
        "ResearchEventResolutionConfidenceIntervalConfig",
        "ResearchEventResolutionConfidenceIntervalObservation",
        "ResearchEventResolutionConfidenceIntervalReasonCodeCount",
        "ResearchEventResolutionConfidenceIntervalReport",
        "ResearchEventResolutionConfidenceIntervalRow",
        "build_research_event_resolution_confidence_interval_report",
        "research_event_resolution_confidence_interval_report_digest",
        "research_event_resolution_confidence_interval_report_payload",
    }
