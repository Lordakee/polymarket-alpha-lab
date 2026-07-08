from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_event_resolution_delay_forecast_report import (
    DEFAULT_RESEARCH_EVENT_RESOLUTION_DELAY_FORECAST_CONFIG_VERSION,
    ResearchEventResolutionDelayForecastConfig,
    ResearchEventResolutionDelayForecastInput,
    ResearchEventResolutionDelayForecastReasonCount,
    ResearchEventResolutionDelayForecastReport,
    ResearchEventResolutionDelayForecastRow,
    build_research_event_resolution_delay_forecast_report,
    research_event_resolution_delay_forecast_report_digest,
    research_event_resolution_delay_forecast_report_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_event_resolution_delay_forecast_report.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventResolutionDelayForecastConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_RESOLUTION_DELAY_FORECAST_CONFIG_VERSION
        ),
        "oracle_lag_watch_seconds": d("3600"),
        "oracle_lag_block_seconds": d("14400"),
        "evidence_conflict_watch_score": d("0.300000"),
        "evidence_conflict_block_score": d("0.700000"),
        "deadline_clarity_watch_score": d("0.600000"),
        "deadline_clarity_block_score": d("0.300000"),
        "dispute_pressure_watch_score": d("0.250000"),
        "dispute_pressure_block_score": d("0.650000"),
        "historical_delay_memory_watch_score": d("0.300000"),
        "historical_delay_memory_block_score": d("0.700000"),
        "aggregate_watch_threshold": d("0.300000"),
        "aggregate_block_threshold": d("0.650000"),
    }
    values.update(overrides)
    return ResearchEventResolutionDelayForecastConfig(**values)


def input_row(
    domain: str = "macro_data",
    *,
    public_event_label: str = "public macro data release",
    oracle_expected_at: datetime | None = None,
    oracle_observed_at: datetime | None = None,
    evidence_conflict_score: Decimal = d("0.100000"),
    deadline_clarity_score: Decimal = d("0.900000"),
    dispute_pressure_score: Decimal = d("0.100000"),
    historical_delay_memory_score: Decimal = d("0.100000"),
    public_resolution_rule_ref: str = "public-resolution-bulletin",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventResolutionDelayForecastInput:
    return ResearchEventResolutionDelayForecastInput(
        domain=domain,
        public_event_label=public_event_label,
        oracle_expected_at=oracle_expected_at or GENERATED_AT - timedelta(minutes=30),
        oracle_observed_at=oracle_observed_at,
        evidence_conflict_score=evidence_conflict_score,
        deadline_clarity_score=deadline_clarity_score,
        dispute_pressure_score=dispute_pressure_score,
        historical_delay_memory_score=historical_delay_memory_score,
        public_resolution_rule_ref=public_resolution_rule_ref,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchEventResolutionDelayForecastConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventResolutionDelayForecastReport:
    return build_research_event_resolution_delay_forecast_report(
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
        if field.name.endswith(("_count", "_ratio", "_score", "_seconds")):
            assert type(item) is Decimal


def test_resolution_delay_forecast_reduces_domains_redacts_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "macro_data",
                public_event_label="public macro release",
                oracle_expected_at=GENERATED_AT - timedelta(hours=1),
                oracle_observed_at=GENERATED_AT - timedelta(minutes=20),
                evidence_conflict_score=d("0.200000"),
                deadline_clarity_score=d("0.800000"),
                dispute_pressure_score=d("0.150000"),
                historical_delay_memory_score=d("0.100000"),
                public_resolution_rule_ref="public-resolution-bulletin",
            ),
            input_row(
                "sports_results",
                public_event_label="public sports final",
                oracle_expected_at=GENERATED_AT - timedelta(hours=2),
                oracle_observed_at=GENERATED_AT - timedelta(minutes=10),
                evidence_conflict_score=d("0.550000"),
                deadline_clarity_score=d("0.500000"),
                dispute_pressure_score=d("0.300000"),
                historical_delay_memory_score=d("0.350000"),
                public_resolution_rule_ref="league-box-score-with-internal-case",
            ),
            input_row(
                "policy_deadlines",
                public_event_label="public policy deadline",
                oracle_expected_at=GENERATED_AT - timedelta(hours=6),
                oracle_observed_at=None,
                evidence_conflict_score=d("0.800000"),
                deadline_clarity_score=d("0.250000"),
                dispute_pressure_score=d("0.700000"),
                historical_delay_memory_score=d("0.750000"),
                public_resolution_rule_ref="https://vendor.example/rule?token=hidden",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_DELAY_FORECAST_CONFIG_VERSION
    )
    assert summary.forecast_status == "block"
    assert summary.next_step == "block_report_only_resolution_delay_review"
    assert summary.domain_count == d("3.000000")
    assert summary.pass_domain_count == d("1.000000")
    assert summary.watch_domain_count == d("1.000000")
    assert summary.block_domain_count == d("1.000000")
    assert summary.max_resolution_delay_risk_score == d("0.800000")
    assert summary.average_resolution_delay_risk_score == d("0.465000")
    assert summary.max_oracle_lag_seconds == d("21600.000000")
    assert summary.average_oracle_lag_seconds == d("10200.000000")
    assert summary.oracle_lag_pressure_count == d("2.000000")
    assert summary.evidence_conflict_count == d("2.000000")
    assert summary.deadline_clarity_count == d("2.000000")
    assert summary.dispute_pressure_count == d("2.000000")
    assert summary.historical_delay_memory_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.domain_status, row.domain) for row in summary.rows) == (
        ("block", "policy_deadlines"),
        ("watch", "sports_results"),
        ("pass", "macro_data"),
    )

    blocked = summary.rows[0]
    assert blocked.oracle_lag_seconds == d("21600.000000")
    assert blocked.resolution_delay_risk_score == d("0.800000")
    assert blocked.redacted_resolution_rule_ref == "sha256:ccd33ab29588"
    assert blocked.reason_codes == (
        "resolution_delay_forecast_deadline_clarity_block",
        "resolution_delay_forecast_dispute_pressure_block",
        "resolution_delay_forecast_evidence_conflict_block",
        "resolution_delay_forecast_historical_delay_memory_block",
        "resolution_delay_forecast_oracle_lag_block",
    )

    watched = summary.rows[1]
    assert watched.oracle_lag_seconds == d("6600.000000")
    assert watched.resolution_delay_risk_score == d("0.431667")
    assert watched.redacted_resolution_rule_ref == "sha256:2093f1b90208"
    assert watched.reason_codes == (
        "resolution_delay_forecast_deadline_clarity_watch",
        "resolution_delay_forecast_dispute_pressure_watch",
        "resolution_delay_forecast_evidence_conflict_watch",
        "resolution_delay_forecast_historical_delay_memory_watch",
        "resolution_delay_forecast_oracle_lag_watch",
    )

    passed = summary.rows[2]
    assert passed.oracle_lag_seconds == d("2400.000000")
    assert passed.resolution_delay_risk_score == d("0.163333")
    assert passed.redacted_resolution_rule_ref == "public-resolution-bulletin"
    assert passed.reason_codes == ("resolution_delay_forecast_pass",)

    public = repr(asdict(summary)).lower()
    for value in (
        "hidden",
        "vendor.example",
        "https://",
        "league-box-score-with-internal-case",
        "token",
    ):
        assert value not in public


def test_empty_resolution_delay_forecast_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.forecast_status == "block"
    assert summary.next_step == "block_report_only_resolution_delay_review"
    assert summary.domain_count == ZERO
    assert summary.pass_domain_count == ZERO
    assert summary.watch_domain_count == ZERO
    assert summary.block_domain_count == ZERO
    assert summary.max_resolution_delay_risk_score == ZERO
    assert summary.average_resolution_delay_risk_score == ZERO
    assert summary.max_oracle_lag_seconds == ZERO
    assert summary.average_oracle_lag_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchEventResolutionDelayForecastReasonCount(
            reason_code="resolution_delay_forecast_no_inputs",
            count=d("1.000000"),
            domain_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == ("resolution_delay_forecast_no_inputs",)
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_resolution_delay_forecast_honors_custom_threshold_config() -> None:
    summary = report(
        (
            input_row(
                oracle_expected_at=GENERATED_AT - timedelta(hours=1),
                evidence_conflict_score=d("0.100000"),
                deadline_clarity_score=d("0.900000"),
                dispute_pressure_score=d("0.100000"),
                historical_delay_memory_score=d("0.100000"),
            ),
        ),
        cfg=config(
            oracle_lag_watch_seconds=d("1800"),
            oracle_lag_block_seconds=d("7200"),
            aggregate_watch_threshold=d("0.050000"),
            aggregate_block_threshold=d("0.900000"),
        ),
    )

    assert summary.forecast_status == "watch"
    assert summary.watch_domain_count == d("1.000000")
    assert summary.rows[0].domain_status == "watch"
    assert summary.rows[0].reason_codes == (
        "resolution_delay_forecast_oracle_lag_watch",
    )


def test_resolution_delay_forecast_payload_uses_decimal_strings_and_digest() -> None:
    first = report((input_row(),))
    second = report((input_row(),))
    payload = research_event_resolution_delay_forecast_report_payload(first)
    json.dumps(payload, sort_keys=True)

    assert payload["domain_count"] == "1.000000"
    assert payload["average_resolution_delay_risk_score"] == "0.105000"
    assert payload["rows"][0]["oracle_lag_seconds"] == "1800.000000"
    assert payload["report_digest"] == research_event_resolution_delay_forecast_report_digest(
        first,
    )
    assert research_event_resolution_delay_forecast_report_digest(first) == (
        research_event_resolution_delay_forecast_report_digest(second)
    )
    assert payload == research_event_resolution_delay_forecast_report_payload(second)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "public_resolution_rule_ref" not in repr(payload)


def test_resolution_delay_forecast_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(ResearchEventResolutionDelayForecastConfig)
    assert is_dataclass(ResearchEventResolutionDelayForecastInput)
    assert is_dataclass(ResearchEventResolutionDelayForecastRow)
    assert is_dataclass(ResearchEventResolutionDelayForecastReasonCount)
    assert is_dataclass(ResearchEventResolutionDelayForecastReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.evidence_conflict_score = d("0.2")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].resolution_delay_risk_score = d("0.2")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.domain_count = d("2")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("resolution-delay-v0"))
    with pytest.raises(ValueError, match="oracle_lag_watch_seconds"):
        config(oracle_lag_watch_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="oracle_lag_block_seconds"):
        config(oracle_lag_watch_seconds=d("7200"), oracle_lag_block_seconds=d("3600"))
    with pytest.raises(ValueError, match="evidence_conflict_watch_score"):
        config(evidence_conflict_watch_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="deadline_clarity_block_score"):
        config(
            deadline_clarity_watch_score=d("0.300000"),
            deadline_clarity_block_score=d("0.600000"),
        )
    with pytest.raises(ValueError, match="aggregate_block_threshold"):
        config(aggregate_watch_threshold=d("0.700000"), aggregate_block_threshold=d("0.6"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="domain"):
        input_row("bad domain")
    with pytest.raises(ValueError, match="public_event_label"):
        input_row(public_event_label="event with account detail")
    with pytest.raises(ValueError, match="oracle_expected_at"):
        input_row(oracle_expected_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="oracle_observed_at"):
        input_row(oracle_observed_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="evidence_conflict_score"):
        input_row(evidence_conflict_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="deadline_clarity_score"):
        input_row(deadline_clarity_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="dispute_pressure_score"):
        input_row(dispute_pressure_score=d("1.000001"))
    with pytest.raises(ValueError, match="historical_delay_memory_score"):
        input_row(historical_delay_memory_score=d("-0.000001"))
    with pytest.raises(ValueError, match="public_resolution_rule_ref"):
        input_row(public_resolution_rule_ref="")
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_event_resolution_delay_forecast_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_event_resolution_delay_forecast_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_resolution_delay_forecast_consistency_rejects_manual_drift() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "resolution_delay_forecast_pass",
                "resolution_delay_forecast_oracle_lag_watch",
            ),
        )
    with pytest.raises(ValueError, match="domain_status"):
        replace(ready, domain_status="block")
    with pytest.raises(ValueError, match="resolution_delay_risk_score"):
        replace(ready, resolution_delay_risk_score=d("0.999999"))
    with pytest.raises(ValueError, match="redacted_resolution_rule_ref"):
        replace(ready, redacted_resolution_rule_ref="https://host?token=hidden")

    with pytest.raises(ValueError, match="pass_domain_count"):
        replace(report((input_row(),)), pass_domain_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report((input_row(),)), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report((input_row(),)), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report((input_row(),)), readonly=False)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("weather", public_event_label="public weather event"),
                input_row(),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="report_digest"):
        replace(report((input_row(),)), report_digest="0" * 64)


def test_resolution_delay_forecast_public_numeric_fields_are_decimals() -> None:
    source_row = input_row()
    summary = report((source_row,))

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_resolution_delay_forecast_module_has_no_io_or_execution_surfaces() -> None:
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
        "live",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "recommend",
        "sizing",
        "market_slug",
        "source_id",
        "condition_id",
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
        "write",
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
