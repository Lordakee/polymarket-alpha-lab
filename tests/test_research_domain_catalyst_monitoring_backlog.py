from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_domain_catalyst_monitoring_backlog import (
    DEFAULT_RESEARCH_DOMAIN_CATALYST_MONITORING_BACKLOG_CONFIG_VERSION,
    DOMAIN_SEQUENCE,
    STATUS_VALUES,
    ResearchDomainCatalystMonitoringBacklogConfig,
    ResearchDomainCatalystMonitoringBacklogInputRow,
    ResearchDomainCatalystMonitoringBacklogReasonCodeCount,
    ResearchDomainCatalystMonitoringBacklogReport,
    ResearchDomainCatalystMonitoringBacklogRow,
    build_research_domain_catalyst_monitoring_backlog,
    research_domain_catalyst_monitoring_backlog_digest,
    research_domain_catalyst_monitoring_backlog_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_domain_catalyst_monitoring_backlog.py",
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
) -> ResearchDomainCatalystMonitoringBacklogConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_DOMAIN_CATALYST_MONITORING_BACKLOG_CONFIG_VERSION
        ),
        "fresh_metric_max_age_seconds": d("86400.000000"),
        "min_freshness_score": d("0.700000"),
        "min_coverage_score": d("0.600000"),
        "min_public_evidence_count": d("2"),
        "impact_watch_threshold": d("0.650000"),
        "impact_block_threshold": d("0.850000"),
    }
    values.update(overrides)
    return ResearchDomainCatalystMonitoringBacklogConfig(**values)


def input_row(
    domain: str = "politics",
    *,
    catalyst_theme: str = "election-calendar",
    metrics_updated_at: datetime | None = None,
    freshness_score: Decimal = d("0.920000"),
    impact_score: Decimal = d("0.200000"),
    coverage_score: Decimal = d("0.880000"),
    public_evidence_count: Decimal = d("4"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchDomainCatalystMonitoringBacklogInputRow:
    return ResearchDomainCatalystMonitoringBacklogInputRow(
        domain=domain,
        catalyst_theme=catalyst_theme,
        metrics_updated_at=metrics_updated_at or GENERATED_AT - timedelta(hours=1),
        freshness_score=freshness_score,
        impact_score=impact_score,
        coverage_score=coverage_score,
        public_evidence_count=public_evidence_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchDomainCatalystMonitoringBacklogConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchDomainCatalystMonitoringBacklogReport:
    return build_research_domain_catalyst_monitoring_backlog(
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
        if field.name.endswith(("_count", "_score", "_seconds", "_ratio")):
            assert type(item) is Decimal


def test_domain_catalyst_backlog_reduces_rows_and_sorts_statuses() -> None:
    summary = report(
        (
            input_row("politics", catalyst_theme="election-calendar"),
            input_row(
                "crypto",
                catalyst_theme="protocol-upgrade",
                metrics_updated_at=GENERATED_AT - timedelta(hours=2),
                freshness_score=d("0.850000"),
                impact_score=d("0.900000"),
                coverage_score=d("0.900000"),
                public_evidence_count=d("5"),
            ),
            input_row(
                "equities",
                catalyst_theme="earnings-window",
                metrics_updated_at=GENERATED_AT - timedelta(hours=3),
                freshness_score=d("0.750000"),
                impact_score=d("0.700000"),
                coverage_score=d("0.650000"),
                public_evidence_count=d("3"),
            ),
            input_row(
                "gold",
                catalyst_theme="central-bank-flows",
                metrics_updated_at=GENERATED_AT - timedelta(hours=12),
                freshness_score=d("0.880000"),
                impact_score=d("0.250000"),
                coverage_score=d("0.800000"),
                public_evidence_count=d("3"),
            ),
            input_row(
                "soccer",
                catalyst_theme="fixture-density",
                metrics_updated_at=GENERATED_AT - timedelta(hours=4),
                freshness_score=d("0.800000"),
                impact_score=d("0.300000"),
                coverage_score=d("0.400000"),
                public_evidence_count=d("1"),
            ),
            input_row(
                "basketball",
                catalyst_theme="rotation-depth",
                metrics_updated_at=GENERATED_AT - timedelta(minutes=30),
                freshness_score=d("0.910000"),
                impact_score=d("0.400000"),
                coverage_score=d("0.780000"),
                public_evidence_count=d("2"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_DOMAIN_CATALYST_MONITORING_BACKLOG_CONFIG_VERSION
    )
    assert STATUS_VALUES == ("pass", "watch", "block")
    assert summary.backlog_status == "block"
    assert summary.next_step == "block_report_only_domain_catalyst_backlog"
    assert summary.catalyst_count == d("6.000000")
    assert summary.domain_count == d("6.000000")
    assert summary.pass_count == d("3.000000")
    assert summary.watch_count == d("2.000000")
    assert summary.block_count == d("1.000000")
    assert summary.missing_domain_count == ZERO
    assert summary.high_impact_count == d("2.000000")
    assert summary.low_coverage_count == d("1.000000")
    assert summary.low_freshness_count == ZERO
    assert summary.stale_metric_count == ZERO
    assert summary.average_freshness_score == d("0.851667")
    assert summary.average_impact_score == d("0.458333")
    assert summary.average_coverage_score == d("0.735000")
    assert summary.average_public_evidence_count == d("3.000000")
    assert summary.max_metric_age_seconds == d("43200.000000")
    assert summary.missing_domains == ()
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.catalyst_status, row.domain) for row in summary.rows) == (
        ("block", "crypto"),
        ("watch", "equities"),
        ("watch", "soccer"),
        ("pass", "basketball"),
        ("pass", "gold"),
        ("pass", "politics"),
    )

    blocked = summary.rows[0]
    assert blocked.metric_age_seconds == d("7200.000000")
    assert blocked.reason_codes == (
        "research_domain_catalyst_monitoring_backlog_impact_block",
    )

    watched = summary.rows[1]
    assert watched.reason_codes == (
        "research_domain_catalyst_monitoring_backlog_impact_watch",
    )

    thin = summary.rows[2]
    assert thin.reason_codes == (
        "research_domain_catalyst_monitoring_backlog_low_coverage",
    )

    passed = summary.rows[3]
    assert passed.reason_codes == (
        "research_domain_catalyst_monitoring_backlog_pass",
    )

    assert summary.reason_code_counts == (
        ResearchDomainCatalystMonitoringBacklogReasonCodeCount(
            reason_code="research_domain_catalyst_monitoring_backlog_impact_block",
            count=d("1.000000"),
            catalyst_ratio=d("0.166667"),
        ),
        ResearchDomainCatalystMonitoringBacklogReasonCodeCount(
            reason_code="research_domain_catalyst_monitoring_backlog_impact_watch",
            count=d("1.000000"),
            catalyst_ratio=d("0.166667"),
        ),
        ResearchDomainCatalystMonitoringBacklogReasonCodeCount(
            reason_code="research_domain_catalyst_monitoring_backlog_low_coverage",
            count=d("1.000000"),
            catalyst_ratio=d("0.166667"),
        ),
        ResearchDomainCatalystMonitoringBacklogReasonCodeCount(
            reason_code="research_domain_catalyst_monitoring_backlog_pass",
            count=d("3.000000"),
            catalyst_ratio=d("0.500000"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )


def test_empty_domain_catalyst_backlog_is_blocked_and_public_safe() -> None:
    summary = report(())

    assert summary.backlog_status == "block"
    assert summary.next_step == "block_report_only_domain_catalyst_backlog"
    assert summary.catalyst_count == ZERO
    assert summary.domain_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.missing_domain_count == d("6.000000")
    assert summary.missing_domains == DOMAIN_SEQUENCE
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        ResearchDomainCatalystMonitoringBacklogReasonCodeCount(
            reason_code="research_domain_catalyst_monitoring_backlog_no_inputs",
            count=d("1.000000"),
            catalyst_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "research_domain_catalyst_monitoring_backlog_no_inputs",
        "research_domain_catalyst_monitoring_backlog_missing_domain_coverage",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_domain_catalyst_backlog_payload_and_digest_are_deterministic() -> None:
    summary = report(
        (
            input_row("politics", catalyst_theme="election-calendar"),
            input_row("crypto", catalyst_theme="protocol-upgrade"),
        ),
    )
    payload = research_domain_catalyst_monitoring_backlog_payload(summary)
    digest = research_domain_catalyst_monitoring_backlog_digest(summary)

    assert payload == research_domain_catalyst_monitoring_backlog_payload(summary)
    assert digest == research_domain_catalyst_monitoring_backlog_digest(summary)
    assert len(digest) == 64
    int(digest, 16)
    json.dumps(payload, sort_keys=True)
    assert payload["catalyst_count"] == "2.000000"
    assert payload["rows"][0]["freshness_score"] == "0.920000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))

    public = repr(payload).lower()
    for value in (
        "event_id",
        "market_id",
        "source_id",
        "wallet",
        "private_key",
        "api_key",
        "secret",
        "buy",
        "sell",
        "recommend",
    ):
        assert value not in public


def test_domain_catalyst_backlog_validates_contracts_and_flags() -> None:
    assert is_dataclass(ResearchDomainCatalystMonitoringBacklogConfig)
    assert is_dataclass(ResearchDomainCatalystMonitoringBacklogInputRow)
    assert is_dataclass(ResearchDomainCatalystMonitoringBacklogRow)
    assert is_dataclass(ResearchDomainCatalystMonitoringBacklogReasonCodeCount)
    assert is_dataclass(ResearchDomainCatalystMonitoringBacklogReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.coverage_score = d("0.900000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].impact_score = d("0.900000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.catalyst_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("catalyst-v0"))
    with pytest.raises(ValueError, match="fresh_metric_max_age_seconds"):
        config(fresh_metric_max_age_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_public_evidence_count"):
        config(min_public_evidence_count=d("1.5"))
    with pytest.raises(ValueError, match="min_freshness_score"):
        config(min_freshness_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="min_coverage_score"):
        config(min_coverage_score=d("-0.000001"))
    with pytest.raises(ValueError, match="impact_block_threshold"):
        config(impact_watch_threshold=d("0.900000"), impact_block_threshold=d("0.850000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="domain"):
        input_row("tennis")
    with pytest.raises(ValueError, match="catalyst_theme"):
        input_row(catalyst_theme="raw-event-id")
    with pytest.raises(ValueError, match="metrics_updated_at"):
        input_row(metrics_updated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="metrics_updated_at"):
        input_row(metrics_updated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="freshness_score"):
        input_row(freshness_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="impact_score"):
        input_row(impact_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="coverage_score"):
        input_row(coverage_score=Decimal("Infinity"))
    with pytest.raises(ValueError, match="public_evidence_count"):
        input_row(public_evidence_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_research_domain_catalyst_monitoring_backlog(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_domain_catalyst_monitoring_backlog(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_domain_catalyst_row_and_report_reject_manual_drift() -> None:
    passing = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            passing,
            reason_codes=(
                "research_domain_catalyst_monitoring_backlog_pass",
                "research_domain_catalyst_monitoring_backlog_low_coverage",
            ),
        )
    with pytest.raises(ValueError, match="catalyst_status"):
        replace(passing, catalyst_status="watch")
    with pytest.raises(ValueError, match="metric_age_seconds"):
        replace(passing, metric_age_seconds=d("9.000000"))

    full = report(
        (
            input_row("politics", catalyst_theme="election-calendar"),
            input_row("crypto", catalyst_theme="protocol-upgrade"),
            input_row("equities", catalyst_theme="earnings-window"),
            input_row("gold", catalyst_theme="central-bank-flows"),
            input_row("soccer", catalyst_theme="fixture-density"),
            input_row("basketball", catalyst_theme="rotation-depth"),
        ),
    )
    with pytest.raises(ValueError, match="rows"):
        replace(full, rows=tuple(reversed(full.rows)))
    with pytest.raises(ValueError, match="pass_count"):
        replace(full, pass_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(full, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(full, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(full, readonly=False)


def test_domain_catalyst_public_numeric_fields_are_decimals() -> None:
    source_row = input_row()
    summary = report((source_row,))

    assert_decimal_numeric_fields(source_row)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_domain_catalyst_module_has_no_io_store_or_action_surfaces() -> None:
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
        "event_id",
        "market_id",
        "source_id",
        "wallet",
        "auth",
        "order",
        "trade",
        "private-key",
        "private_key",
        "live execution",
        "database",
        "network",
        "buy",
        "sell",
        "recommend",
        "advice",
        "api_key",
        "secret",
        "position",
        "stake",
        "client",
        "http",
        "socket",
        "subprocess",
        "open(",
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
