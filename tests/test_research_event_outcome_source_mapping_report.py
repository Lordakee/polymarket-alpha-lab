from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.research_event_outcome_source_mapping_report"


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "watch_coverage_ratio": d("0.950000"),
        "block_coverage_ratio": d("0.750000"),
        "watch_agreement_ratio": d("0.900000"),
        "block_agreement_ratio": d("0.750000"),
        "watch_stale_mapping_ratio": d("0.150000"),
        "block_stale_mapping_ratio": d("0.300000"),
        "watch_ambiguity_ratio": d("0.100000"),
        "block_ambiguity_ratio": d("0.250000"),
        "watch_recheck_urgency_ratio": d("0.200000"),
        "block_recheck_urgency_ratio": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchEventOutcomeSourceMappingReportConfig(**values)


def aggregate(source_class: str, **overrides: object) -> Any:
    module = api()
    values = {
        "source_class": source_class,
        "outcome_count": d("10.000000"),
        "mapped_outcome_count": d("10.000000"),
        "agreeing_mapping_count": d("10.000000"),
        "stale_mapping_count": d("0.000000"),
        "ambiguous_mapping_count": d("0.000000"),
        "recheck_due_count": d("0.000000"),
        "max_mapping_age_seconds": d("600.000000"),
    }
    values.update(overrides)
    return module.ResearchEventOutcomeSourceMappingAggregate(**values)


def build_report(*values: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_event_outcome_source_mapping_report(
        values,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def payload(report_value: Any | None = None) -> dict[str, object]:
    module = api()
    return module.research_event_outcome_source_mapping_report_payload(
        report_value if report_value is not None else build_report(),
    )


def test_report_rolls_up_source_class_coverage_agreement_pressure_and_urgency() -> None:
    module = api()
    report = build_report(
        aggregate("official_statistics"),
        aggregate(
            "league_result",
            outcome_count=d("8.000000"),
            mapped_outcome_count=d("7.000000"),
            agreeing_mapping_count=d("6.000000"),
            stale_mapping_count=d("2.000000"),
            ambiguous_mapping_count=d("1.000000"),
            recheck_due_count=d("2.000000"),
            max_mapping_age_seconds=d("7200.000000"),
        ),
        aggregate(
            "regulatory_filing",
            outcome_count=d("5.000000"),
            mapped_outcome_count=d("3.000000"),
            agreeing_mapping_count=d("2.000000"),
            stale_mapping_count=d("2.000000"),
            ambiguous_mapping_count=d("2.000000"),
            recheck_due_count=d("2.000000"),
            max_mapping_age_seconds=d("14400.000000"),
        ),
    )

    assert type(report) is module.ResearchEventOutcomeSourceMappingReport
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.source_class_count == d("3.000000")
    assert report.outcome_count == d("23.000000")
    assert report.mapped_outcome_count == d("20.000000")
    assert report.unmapped_outcome_count == d("3.000000")
    assert report.agreeing_mapping_count == d("18.000000")
    assert report.stale_mapping_count == d("4.000000")
    assert report.ambiguous_mapping_count == d("3.000000")
    assert report.recheck_due_count == d("4.000000")
    assert report.coverage_ratio == d("0.869565")
    assert report.agreement_ratio == d("0.900000")
    assert report.stale_mapping_ratio == d("0.200000")
    assert report.ambiguity_ratio == d("0.150000")
    assert report.recheck_urgency_ratio == d("0.200000")
    assert report.max_mapping_age_seconds == d("14400.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.source_class for row in report.rows) == (
        "regulatory_filing",
        "league_result",
        "official_statistics",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert report.rows[0].reason_codes == (
        "source_mapping_block",
        "coverage_gap_block",
        "agreement_gap_block",
        "stale_mapping_pressure_block",
        "ambiguity_pressure_block",
        "recheck_urgency_block",
    )
    assert report.rows[1].reason_codes == (
        "source_mapping_watch",
        "coverage_gap_watch",
        "agreement_gap_watch",
        "stale_mapping_pressure_watch",
        "ambiguity_pressure_watch",
        "recheck_urgency_watch",
    )
    assert report.rows[2].reason_codes == ("source_mapping_pass",)
    assert report.reason_codes == (
        "source_mapping_report_block",
        "coverage_gap_block",
        "agreement_gap_block",
        "stale_mapping_pressure_block",
        "ambiguity_pressure_block",
        "recheck_urgency_block",
        "coverage_gap_watch",
        "agreement_gap_watch",
        "stale_mapping_pressure_watch",
        "ambiguity_pressure_watch",
        "recheck_urgency_watch",
    )

    public_payload = module.research_event_outcome_source_mapping_report_payload(report)
    assert public_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert public_payload["coverage_ratio"] == "0.869565"
    assert public_payload["rows"][0]["source_class"] == "regulatory_filing"  # type: ignore[index]
    assert public_payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    json.dumps(public_payload, sort_keys=True)
    _assert_no_public_numeric_scalars(public_payload)
    _assert_no_raw_event_or_source_surface(public_payload)


def test_report_contract_is_frozen_decimal_only_deterministic_and_tamper_checked() -> None:
    module = api()
    values = (
        aggregate("official_statistics"),
        aggregate(
            "league_result",
            outcome_count=d("8.000000"),
            mapped_outcome_count=d("7.000000"),
            agreeing_mapping_count=d("6.000000"),
            stale_mapping_count=d("2.000000"),
            ambiguous_mapping_count=d("1.000000"),
            recheck_due_count=d("2.000000"),
            max_mapping_age_seconds=d("7200.000000"),
        ),
    )
    first = build_report(*values)
    second = build_report(*reversed(values))

    assert first == second
    assert payload(first) == payload(second)
    assert module.MAPPING_STATUSES == ("pass", "watch", "block")
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)
    for cls in (
        module.ResearchEventOutcomeSourceMappingReportConfig,
        module.ResearchEventOutcomeSourceMappingAggregate,
        module.ResearchEventOutcomeSourceMappingRow,
        module.ResearchEventOutcomeSourceMappingReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        first.status = "pass"  # type: ignore[misc]
    _assert_decimal_public_fields(first)
    for row in first.rows:
        _assert_decimal_public_fields(row)

    with pytest.raises(ValueError, match="watch_coverage_ratio"):
        config(watch_coverage_ratio=1)
    with pytest.raises(ValueError, match="block_coverage_ratio"):
        config(block_coverage_ratio=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="source_class"):
        aggregate("https://example.invalid/result")
    with pytest.raises(ValueError, match="outcome_count"):
        aggregate("bad_count", outcome_count=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="mapped_outcome_count"):
        aggregate("bad_mapping", mapped_outcome_count=d("11.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(aggregate("bad_flag"), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(first, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(first.rows[0], status="ready")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_event_outcome_source_mapping_report_payload(object())


def test_empty_report_is_pass_and_public_safe() -> None:
    module = api()
    report = build_report()

    assert report.status == "pass"
    assert report.source_class_count == d("0.000000")
    assert report.outcome_count == d("0.000000")
    assert report.coverage_ratio == d("1.000000")
    assert report.agreement_ratio == d("1.000000")
    assert report.reason_codes == ("source_mapping_report_pass",)
    assert report.rows == ()
    public_payload = module.research_event_outcome_source_mapping_report_payload(report)
    module.validate_research_event_outcome_source_mapping_report_payload(public_payload)
    _assert_no_public_numeric_scalars(public_payload)
    _assert_no_raw_event_or_source_surface(public_payload)


def test_module_has_no_external_io_or_action_surface() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
        "io",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "buy",
        "sell",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")

    lowered_source = source.lower()
    forbidden_text = (
        "wallet",
        "private_key",
        "live execution",
        "position sizing",
        "market_id",
        "market_slug",
        "source_url",
        "source_text",
    )
    assert not any(token in lowered_source for token in forbidden_text)


def _assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (float, int, Decimal):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_numeric_scalars(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_public_numeric_scalars(item)


def _assert_no_raw_event_or_source_surface(value: Any) -> None:
    raw_keys = {
        "event_id",
        "event_slug",
        "market_id",
        "market_slug",
        "question",
        "source_id",
        "source_url",
        "source_text",
        "text",
        "url",
    }
    if isinstance(value, dict):
        assert set(value).isdisjoint(raw_keys)
        for item in value.values():
            _assert_no_raw_event_or_source_surface(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_raw_event_or_source_surface(item)


def _assert_decimal_public_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if field.name.endswith("_count") or field.name.endswith("_ratio") or field.name.endswith(
            "_seconds",
        ):
            assert type(item) is Decimal
