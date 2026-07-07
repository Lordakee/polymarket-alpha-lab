from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_dependency_graph_report"
MODULE_PATH = Path("src/polymarket_alpha_lab/research_event_dependency_graph_report.py")
GENERATED_AT = datetime(2026, 7, 2, 14, 30, tzinfo=timezone(timedelta(hours=-4)))


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def node(**overrides: Any):
    module = api()
    values: dict[str, Any] = {
        "redacted_event_ref": "redacted-event-alpha",
        "dependency_edge_count": d("1"),
        "unresolved_dependency_count": d("0"),
        "external_shock_sensitivity": d("0.100000"),
        "timeline_quality_score": d("0.950000"),
        "evidence_support_score": d("0.900000"),
        "reason_codes": ("sanitized_event_dependency_input",),
    }
    values.update(overrides)
    return module.ResearchEventDependencyGraphInput(**values)


def report(*rows: object, config: object | None = None):
    module = api()
    return module.build_research_event_dependency_graph_report(
        rows,
        config=(
            module.ResearchEventDependencyGraphReportConfig()
            if config is None
            else config
        ),
        generated_at=GENERATED_AT,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float) or type(value) is int:
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def public_field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def test_report_passes_for_sanitized_low_risk_graph() -> None:
    module = api()

    graph_report = report(
        node(redacted_event_ref="redacted-event-beta"),
        node(redacted_event_ref="redacted-event-alpha", dependency_edge_count=d("0")),
    )

    assert is_dataclass(graph_report)
    assert graph_report.generated_at == datetime(2026, 7, 2, 18, 30, tzinfo=UTC)
    assert graph_report.node_count == d("2")
    assert graph_report.pass_count == d("2")
    assert graph_report.watch_count == d("0")
    assert graph_report.block_count == d("0")
    assert graph_report.max_dependency_pressure_score == d("0.081667")
    assert graph_report.average_external_shock_sensitivity == d("0.100000")
    assert graph_report.min_timeline_quality_score == d("0.950000")
    assert graph_report.status == "pass"
    assert graph_report.reason_codes == (
        "research_event_dependency_graph_report_pass",
        "event_dependency_pass_present",
    )
    assert tuple(row.redacted_event_ref for row in graph_report.rows) == (
        "redacted-event-alpha",
        "redacted-event-beta",
    )
    assert graph_report.paper_only is True
    assert graph_report.report_only is True
    assert graph_report.readonly is True
    assert graph_report.safety_flags == module.SAFETY_FLAGS


def test_report_watches_external_shock_and_timeline_quality() -> None:
    graph_report = report(
        node(
            redacted_event_ref="redacted-event-watch",
            dependency_edge_count=d("2"),
            unresolved_dependency_count=d("0"),
            external_shock_sensitivity=d("0.650000"),
            timeline_quality_score=d("0.450000"),
            evidence_support_score=d("0.800000"),
            reason_codes=(),
        ),
    )

    row = graph_report.rows[0]
    assert row.dependency_pressure_score == d("0.343333")
    assert row.status == "watch"
    assert row.reason_codes == (
        "research_event_dependency_graph_row",
        "event_dependency_watch",
        "dependency_edges_present",
        "unresolved_dependencies_clear",
        "external_shock_watch",
        "timeline_quality_watch",
        "evidence_support_strong",
        "dependency_pressure_watch",
    )
    assert graph_report.status == "watch"
    assert graph_report.reason_codes == (
        "research_event_dependency_graph_report_watch",
        "event_dependency_watch_present",
    )


def test_report_blocks_unresolved_dependencies_and_low_timeline_quality() -> None:
    graph_report = report(
        node(
            redacted_event_ref="redacted-event-block",
            dependency_edge_count=d("4"),
            unresolved_dependency_count=d("2"),
            external_shock_sensitivity=d("0.900000"),
            timeline_quality_score=d("0.150000"),
            evidence_support_score=d("0.100000"),
            reason_codes=(),
        ),
    )

    row = graph_report.rows[0]
    assert row.dependency_pressure_score == d("0.773333")
    assert row.status == "block"
    assert row.hard_flag_codes == (
        "unresolved_dependency_count_block",
        "external_shock_sensitivity_block",
        "timeline_quality_score_block",
        "evidence_support_score_block",
    )
    assert "event_dependency_block" in row.reason_codes
    assert graph_report.status == "block"
    assert graph_report.block_count == d("1")
    assert graph_report.reason_codes == (
        "research_event_dependency_graph_report_block",
        "event_dependency_block_present",
    )


def test_rejects_bad_types_datetimes_statuses_and_mutation() -> None:
    module = api()

    with pytest.raises(ValueError, match="dependency_edge_count must be a Decimal"):
        node(dependency_edge_count=1)
    with pytest.raises(ValueError, match="external_shock_sensitivity must be a Decimal"):
        node(external_shock_sensitivity=0.2)
    with pytest.raises(ValueError, match="timeline_quality_score must be finite"):
        node(timeline_quality_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="unresolved_dependency_count must be integral"):
        node(unresolved_dependency_count=d("1.5"))
    with pytest.raises(ValueError, match="unresolved_dependency_count must not exceed"):
        node(dependency_edge_count=d("1"), unresolved_dependency_count=d("2"))

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_event_dependency_graph_report(
            (),
            config=module.ResearchEventDependencyGraphReportConfig(),
            generated_at=DatetimeSubclass(2026, 7, 2, 14, 30, tzinfo=UTC),
        )

    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, dt: datetime | None) -> None:
            return None

        def dst(self, dt: datetime | None) -> None:
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_dependency_graph_report(
            (),
            config=module.ResearchEventDependencyGraphReportConfig(),
            generated_at=datetime(2026, 7, 2, 14, 30, tzinfo=NoneOffsetTimezone()),
        )

    row = node()
    with pytest.raises(FrozenInstanceError):
        row.redacted_event_ref = "redacted-event-other"  # type: ignore[misc]

    scored = graph_report = report(row)
    with pytest.raises(FrozenInstanceError):
        graph_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status must be one of"):
        replace(scored.rows[0], status="blocked")
    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "DerivedResearchEventDependencyGraphInput",
            (module.ResearchEventDependencyGraphInput,),
            {},
        )


def test_rejects_leaky_public_payload_terms_everywhere() -> None:
    module = api()
    unsafe_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position_sizing",
        "buy",
        "sell",
        "recommendation",
        "https://example.test/source",
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public payload entry"):
            node(redacted_event_ref=f"redacted-event-{term}")
        with pytest.raises(ValueError, match="unsafe public payload entry"):
            node(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe public payload entry"):
            module.reject_research_event_dependency_graph_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "research_report"},
            )
        with pytest.raises(ValueError, match="unsafe public payload entry"):
            module.reject_research_event_dependency_graph_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_hard_flags_payload_and_deterministic_digest_are_enforced() -> None:
    module = api()
    config = module.ResearchEventDependencyGraphReportConfig()
    subject = node()
    graph_report = report(subject)
    row = graph_report.rows[0]

    assert module.ResearchEventDependencyGraphReportConfig.__dataclass_params__.frozen
    assert module.ResearchEventDependencyGraphInput.__dataclass_params__.frozen
    assert module.ResearchEventDependencyGraphRow.__dataclass_params__.frozen
    assert module.ResearchEventDependencyGraphReport.__dataclass_params__.frozen

    for instance in (config, subject, row, graph_report):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field_name, value in public_field_values(instance).items():
            if type(value) is bool or field_name == "derived_validation_digest":
                continue
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="paper_only must be True"):
        node(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        module.ResearchEventDependencyGraphReportConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(row, readonly=False)

    payload = module.research_event_dependency_graph_report_payload(graph_report)
    assert payload == graph_report.payload
    assert payload["generated_at"] == "2026-07-02T18:30:00+00:00"
    assert payload["node_count"] == "1"
    assert payload["status"] == "pass"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["redacted_event_ref"] == "redacted-event-alpha"
    assert "candidate_id" not in payload
    assert "market_id" not in payload
    assert "source_ref" not in payload
    assert_no_float_or_int_values(payload)
    assert module.research_event_dependency_graph_report_payload(graph_report) == payload

    object.__setattr__(graph_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_dependency_graph_report_payload(graph_report)

    shuffled = (
        node(redacted_event_ref="redacted-event-z"),
        node(redacted_event_ref="redacted-event-a"),
        node(
            redacted_event_ref="redacted-event-block",
            dependency_edge_count=d("4"),
            unresolved_dependency_count=d("2"),
            external_shock_sensitivity=d("0.900000"),
            timeline_quality_score=d("0.150000"),
            evidence_support_score=d("0.100000"),
            reason_codes=(),
        ),
    )
    with localcontext() as context:
        context.prec = 2
        context.rounding = "ROUND_UP"
        first = report(*shuffled).payload
    second = report(*reversed(shuffled)).payload
    assert first == second
    assert [item["redacted_event_ref"] for item in first["rows"]] == [
        "redacted-event-block",
        "redacted-event-a",
        "redacted-event-z",
    ]


def test_module_has_no_runtime_io_or_float_literals() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "subprocess",
        "getenv",
        "environ",
        "open(",
        "Path(",
        "connect(",
        "execute(",
        "commit(",
        "rollback(",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for item in ast.walk(tree):
        if isinstance(item, ast.Import):
            imported_modules.extend(alias.name for alias in item.names)
        elif isinstance(item, ast.ImportFrom):
            imported_modules.append(item.module or "")
        if isinstance(item, ast.Constant):
            assert type(item.value) is not float
        if isinstance(item, ast.Call) and isinstance(item.func, ast.Name):
            assert item.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.STATUS_VALUES == ("pass", "watch", "block")
    assert "blocked" not in module.STATUS_VALUES
    assert module.__all__ == (
        "STATUS_VALUES",
        "SAFETY_FLAGS",
        "ResearchEventDependencyGraphReportConfig",
        "ResearchEventDependencyGraphInput",
        "ResearchEventDependencyGraphRow",
        "ResearchEventDependencyGraphReport",
        "build_research_event_dependency_graph_report",
        "research_event_dependency_graph_report_payload",
        "reject_research_event_dependency_graph_unsafe_payload",
    )
