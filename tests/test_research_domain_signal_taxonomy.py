from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_domain_signal_taxonomy import (
    DEFAULT_RESEARCH_DOMAIN_SIGNAL_TAXONOMY_CONFIG_VERSION,
    ResearchDomainSignalTaxonomyCoverageCount,
    ResearchDomainSignalTaxonomyFilter,
    ResearchDomainSignalTaxonomyReport,
    ResearchDomainSignalTaxonomyRow,
    build_research_domain_signal_taxonomy_report,
    research_domain_signal_taxonomy_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
MODULE_PATH = Path("src/polymarket_alpha_lab/research_domain_signal_taxonomy.py")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def taxonomy_filter(**overrides: object) -> ResearchDomainSignalTaxonomyFilter:
    values = {
        "config_version": DEFAULT_RESEARCH_DOMAIN_SIGNAL_TAXONOMY_CONFIG_VERSION,
        "domain_filters": (),
        "coverage_status_filters": (),
        "max_risk_score": None,
    }
    values.update(overrides)
    return ResearchDomainSignalTaxonomyFilter(**values)


def report(
    *,
    filters: ResearchDomainSignalTaxonomyFilter | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchDomainSignalTaxonomyReport:
    return build_research_domain_signal_taxonomy_report(
        filters=filters or taxonomy_filter(),
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
            field.name.endswith(("_count", "_ratio", "_score"))
            or field.name.startswith(("pass_", "watch_", "block_"))
            or field.name == "domain_count"
        ):
            assert type(item) is Decimal


def test_domain_signal_taxonomy_reports_required_domains_and_status_coverage() -> None:
    summary = report(generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))))

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == DEFAULT_RESEARCH_DOMAIN_SIGNAL_TAXONOMY_CONFIG_VERSION
    assert summary.status == "block"
    assert summary.next_step == "block_report_only_research_domain_signal_taxonomy"
    assert summary.signal_count == d("12.000000")
    assert summary.domain_count == d("6.000000")
    assert summary.pass_count == d("5.000000")
    assert summary.watch_count == d("4.000000")
    assert summary.block_count == d("3.000000")
    assert summary.max_risk_score == d("0.910000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.domain, row.signal_class, row.coverage_status) for row in summary.rows) == (
        ("basketball", "injury_rotation", "block"),
        ("btc", "venue_liquidity_context", "block"),
        ("politics", "election_integrity", "block"),
        ("basketball", "schedule_density", "watch"),
        ("btc", "chain_flow_context", "watch"),
        ("equity_index", "macro_release_calendar", "watch"),
        ("soccer", "fixture_congestion", "watch"),
        ("equity_index", "breadth_and_volatility", "pass"),
        ("gold", "official_sector_flow", "pass"),
        ("gold", "real_rate_context", "pass"),
        ("politics", "policy_calendar", "pass"),
        ("soccer", "lineup_availability", "pass"),
    )

    assert summary.coverage_counts == (
        ResearchDomainSignalTaxonomyCoverageCount(
            coverage_status="block",
            count=d("3.000000"),
            coverage_ratio=d("0.250000"),
        ),
        ResearchDomainSignalTaxonomyCoverageCount(
            coverage_status="watch",
            count=d("4.000000"),
            coverage_ratio=d("0.333333"),
        ),
        ResearchDomainSignalTaxonomyCoverageCount(
            coverage_status="pass",
            count=d("5.000000"),
            coverage_ratio=d("0.416667"),
        ),
    )
    assert summary.reason_codes == (
        "research_domain_signal_taxonomy_block",
        "research_domain_signal_taxonomy_required_domains_present",
        "research_domain_signal_taxonomy_watch",
    )

    blocked = summary.rows[0]
    assert blocked.applicable_scope == (
        "public_injury_reports",
        "rotation_context",
        "availability_uncertainty",
    )
    assert blocked.refresh_requirement == "refresh_before_each_slate"
    assert blocked.risk_notes == (
        "late_scratch_updates_can_change_context",
        "single_source_availability_can_be_fragile",
    )
    assert blocked.risk_score == d("0.910000")
    assert blocked.reason_codes == (
        "coverage_block",
        "high_update_cadence",
        "single_source_fragility",
    )


def test_domain_signal_taxonomy_safe_filters_are_allowlisted_and_deterministic() -> None:
    summary = report(
        filters=taxonomy_filter(
            domain_filters=("gold", "btc"),
            coverage_status_filters=("pass", "watch"),
            max_risk_score=d("0.600000"),
        ),
    )

    assert summary.status == "watch"
    assert summary.signal_count == d("3.000000")
    assert summary.domain_count == d("2.000000")
    assert summary.pass_count == d("2.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == ZERO
    assert summary.max_risk_score == d("0.560000")
    assert tuple((row.domain, row.signal_class, row.coverage_status) for row in summary.rows) == (
        ("btc", "chain_flow_context", "watch"),
        ("gold", "official_sector_flow", "pass"),
        ("gold", "real_rate_context", "pass"),
    )
    assert summary.reason_codes == (
        "research_domain_signal_taxonomy_filters_active",
        "research_domain_signal_taxonomy_watch",
    )

    repeat = report(
        filters=taxonomy_filter(
            domain_filters=("btc", "gold"),
            coverage_status_filters=("watch", "pass"),
            max_risk_score=d("0.600000"),
        ),
    )
    assert asdict(summary) == asdict(repeat)


def test_empty_domain_signal_taxonomy_filter_is_blocked_and_report_only() -> None:
    summary = report(filters=taxonomy_filter(domain_filters=("soccer",), max_risk_score=d("0.1")))

    assert summary.status == "block"
    assert summary.next_step == "block_report_only_research_domain_signal_taxonomy"
    assert summary.signal_count == ZERO
    assert summary.domain_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.max_risk_score is None
    assert summary.rows == ()
    assert summary.coverage_counts == (
        ResearchDomainSignalTaxonomyCoverageCount(
            coverage_status="block",
            count=d("1.000000"),
            coverage_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "research_domain_signal_taxonomy_no_signals",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_domain_signal_taxonomy_payload_uses_decimal_strings_and_public_fields() -> None:
    summary = report()
    payload = research_domain_signal_taxonomy_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["signal_count"] == "12.000000"
    assert payload["max_risk_score"] == "0.910000"
    assert payload["rows"][0]["risk_score"] == "0.910000"
    assert payload["coverage_counts"][0]["coverage_ratio"] == "0.250000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "credential" not in repr(payload).lower()
    assert "secret" not in repr(payload).lower()


def test_domain_signal_taxonomy_validates_contracts_and_flags() -> None:
    assert is_dataclass(ResearchDomainSignalTaxonomyFilter)
    assert is_dataclass(ResearchDomainSignalTaxonomyRow)
    assert is_dataclass(ResearchDomainSignalTaxonomyCoverageCount)
    assert is_dataclass(ResearchDomainSignalTaxonomyReport)

    cfg = taxonomy_filter()
    summary = report(filters=cfg)
    row = summary.rows[0]
    count = summary.coverage_counts[0]

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.risk_score = d("0.1")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        count.count = d("2")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.signal_count = d("1")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        taxonomy_filter(config_version=_StringSubclass("research-domain-signal-v0"))
    with pytest.raises(ValueError, match="domain_filters"):
        taxonomy_filter(domain_filters=("btc", "gold", "btc"))
    with pytest.raises(ValueError, match="domain_filters"):
        taxonomy_filter(domain_filters=("private_key",))
    with pytest.raises(ValueError, match="coverage_status_filters"):
        taxonomy_filter(coverage_status_filters=("ready",))
    with pytest.raises(ValueError, match="max_risk_score"):
        taxonomy_filter(max_risk_score=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="max_risk_score"):
        taxonomy_filter(max_risk_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="max_risk_score"):
        taxonomy_filter(max_risk_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        taxonomy_filter(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        taxonomy_filter(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        taxonomy_filter(readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_research_domain_signal_taxonomy_report(
            filters=taxonomy_filter(),
            generated_at=_DateTimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="filters"):
        build_research_domain_signal_taxonomy_report(
            filters=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    summary = report()
    ready = summary.rows[-1]

    with pytest.raises(ValueError, match="coverage_status"):
        replace(ready, coverage_status="ready")
    with pytest.raises(ValueError, match="risk_score"):
        replace(ready, risk_score=d("9.999999"))
    with pytest.raises(ValueError, match="applicable_scope"):
        replace(ready, applicable_scope=("public_scope", "public_scope"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(ready, reason_codes=("coverage_pass", "coverage_block"))
    with pytest.raises(ValueError, match="signal_count"):
        replace(summary, signal_count=ZERO)
    with pytest.raises(ValueError, match="pass_count"):
        replace(summary, pass_count=ZERO)
    with pytest.raises(ValueError, match="max_risk_score"):
        replace(summary, max_risk_score=d("0.100000"))
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)


def test_public_numeric_fields_are_decimals() -> None:
    cfg = taxonomy_filter(max_risk_score=d("0.700000"))
    summary = report(filters=cfg)

    assert_decimal_numeric_fields(cfg)
    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.coverage_counts[0])


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
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "advice",
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
