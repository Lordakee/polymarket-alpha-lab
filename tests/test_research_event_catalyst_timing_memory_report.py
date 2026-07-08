from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_catalyst_timing_memory_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return importlib.import_module(MODULE_NAME)


def timing_input(
    aggregate_label: str = "policy-aggregate",
    *,
    catalyst_freshness_hours: Decimal = d("12.000000"),
    evidence_lead_time_hours: Decimal = d("48.000000"),
    stale_thesis_risk_score: Decimal = d("0.100000"),
    recheck_urgency_score: Decimal = d("0.100000"),
):
    module = api()
    return module.ResearchEventCatalystTimingMemoryInput(
        aggregate_label=aggregate_label,
        catalyst_freshness_hours=catalyst_freshness_hours,
        evidence_lead_time_hours=evidence_lead_time_hours,
        stale_thesis_risk_score=stale_thesis_risk_score,
        recheck_urgency_score=recheck_urgency_score,
    )


def build(*inputs: object, generated_at: datetime = GENERATED_AT, cfg: object | None = None):
    module = api()
    return module.build_research_event_catalyst_timing_memory_report(
        inputs,
        config=cfg if cfg is not None else module.ResearchEventCatalystTimingMemoryConfig(),
        generated_at=generated_at,
    )


def assert_payload_has_no_numeric_values(value: Any) -> None:
    if type(value) in (Decimal, int, float):
        raise AssertionError(f"unexpected numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_numeric_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_payload_has_no_numeric_values(item)


def test_timing_memory_report_scores_aggregate_catalyst_risks_deterministically() -> None:
    module = api()
    block = timing_input(
        "macro-aggregate",
        catalyst_freshness_hours=d("96.000000"),
        evidence_lead_time_hours=d("2.000000"),
        stale_thesis_risk_score=d("0.750000"),
        recheck_urgency_score=d("0.900000"),
    )
    watch = timing_input(
        "sports-aggregate",
        catalyst_freshness_hours=d("48.000000"),
        evidence_lead_time_hours=d("18.000000"),
        stale_thesis_risk_score=d("0.300000"),
        recheck_urgency_score=d("0.500000"),
    )
    passed = timing_input("crypto-aggregate")

    report = build(watch, passed, block)
    repeated = build(block, passed, watch)

    assert module.TIMING_MEMORY_STATUSES == ("pass", "watch", "block")
    assert report.status == "block"
    assert report.recommended_next_step == "rebuild_timing_memory_before_paper_report"
    assert report.aggregate_count == d("3.000000")
    assert report.pass_aggregate_count == d("1.000000")
    assert report.watch_aggregate_count == d("1.000000")
    assert report.block_aggregate_count == d("1.000000")
    assert report.flagged_aggregate_count == d("2.000000")
    assert report.flagged_aggregate_ratio == d("0.666667")
    assert report.catalyst_freshness_risk_count == d("2.000000")
    assert report.weak_evidence_lead_time_count == d("2.000000")
    assert report.stale_thesis_risk_count == d("2.000000")
    assert report.recheck_urgency_count == d("2.000000")
    assert report.highest_timing_memory_risk_score == d("1.000000")
    assert report.max_catalyst_freshness_hours == d("96.000000")
    assert report.min_evidence_lead_time_hours == d("2.000000")
    assert report.max_stale_thesis_risk_score == d("0.750000")
    assert report.max_recheck_urgency_score == d("0.900000")
    assert report.reason_codes == (
        "catalyst_freshness_block",
        "catalyst_freshness_watch",
        "recheck_urgency_block",
        "recheck_urgency_watch",
        "stale_thesis_risk_block",
        "stale_thesis_risk_watch",
        "weak_evidence_lead_time_block",
        "weak_evidence_lead_time_watch",
    )
    assert report.rows == repeated.rows
    assert report.derived_validation_digest == repeated.derived_validation_digest
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.aggregate_label for row in report.rows) == (
        "macro-aggregate",
        "sports-aggregate",
        "crypto-aggregate",
    )
    block_row, watch_row, pass_row = report.rows
    assert block_row.status == "block"
    assert block_row.timing_memory_risk_score == d("1.000000")
    assert block_row.needs_fresh_catalyst is True
    assert block_row.weak_evidence_lead_time is True
    assert block_row.stale_thesis_risk is True
    assert block_row.recheck_urgency is True
    assert block_row.reason_codes == (
        "catalyst_freshness_block",
        "recheck_urgency_block",
        "stale_thesis_risk_block",
        "weak_evidence_lead_time_block",
    )
    assert watch_row.status == "watch"
    assert watch_row.timing_memory_risk_score == d("0.500000")
    assert watch_row.reason_codes == (
        "catalyst_freshness_watch",
        "recheck_urgency_watch",
        "stale_thesis_risk_watch",
        "weak_evidence_lead_time_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("timing_memory_pass",)

    payload = module.research_event_catalyst_timing_memory_report_to_payload(report)
    assert json.dumps(payload, sort_keys=True)
    assert payload == module.research_event_catalyst_timing_memory_report_to_payload(
        repeated,
    )
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["aggregate_count"] == "3.000000"
    assert payload["flagged_aggregate_ratio"] == "0.666667"
    assert payload["rows"][0]["timing_memory_risk_score"] == "1.000000"
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])
    assert_payload_has_no_numeric_values(payload)


def test_empty_report_passes_with_decimal_zeroes_and_stable_digest() -> None:
    report = build()
    repeated = build()

    assert report.status == "pass"
    assert report.recommended_next_step == "keep_timing_memory_on_regular_paper_review"
    assert report.reason_codes == ("timing_memory_pass",)
    assert report.aggregate_count == ZERO
    assert report.flagged_aggregate_count == ZERO
    assert report.flagged_aggregate_ratio == ZERO
    assert report.highest_timing_memory_risk_score == ZERO
    assert report.max_catalyst_freshness_hours == ZERO
    assert report.min_evidence_lead_time_hours == ZERO
    assert report.max_stale_thesis_risk_score == ZERO
    assert report.max_recheck_urgency_score == ZERO
    assert report.rows == ()
    assert report.derived_validation_digest == repeated.derived_validation_digest


def test_contracts_are_frozen_decimal_only_hard_flagged_and_public_safe() -> None:
    module = api()
    contract_classes = (
        module.ResearchEventCatalystTimingMemoryConfig,
        module.ResearchEventCatalystTimingMemoryInput,
        module.ResearchEventCatalystTimingMemoryRow,
        module.ResearchEventCatalystTimingMemoryReport,
    )
    for contract_class in contract_classes:
        assert is_dataclass(contract_class)
        assert contract_class.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract_class)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        for field_name, hint in get_type_hints(contract_class).items():
            if field_name in {"paper_only", "report_only", "readonly"}:
                continue
            assert not _type_uses_float(hint)

    input_row = timing_input("safe-aggregate")
    report = build(input_row)
    with pytest.raises(FrozenInstanceError):
        input_row.aggregate_label = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="catalyst_freshness_hours"):
        timing_input(catalyst_freshness_hours=12)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_lead_time_hours"):
        timing_input(evidence_lead_time_hours=d("-1.000000"))
    with pytest.raises(ValueError, match="stale_thesis_risk_score"):
        timing_input(stale_thesis_risk_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="recheck_urgency_score"):
        timing_input(recheck_urgency_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        build(input_row, generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="report_only"):
        replace(input_row, report_only=False)
    with pytest.raises(ValueError, match="config"):
        build(input_row, cfg=object())
    with pytest.raises(ValueError, match="inputs"):
        module.build_research_event_catalyst_timing_memory_report(
            object(),
            config=module.ResearchEventCatalystTimingMemoryConfig(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report"):
        module.research_event_catalyst_timing_memory_report_to_payload(object())


def test_public_surface_rejects_raw_identifiers_urls_source_text_and_tampering() -> None:
    module = api()

    for unsafe_label in (
        "event_id:123",
        "market-id-abc",
        "source_id:alpha",
        "https://example.test/path",
        "www.example.test",
        "raw source text",
        "wallet-review",
        "trade-signal",
    ):
        with pytest.raises(ValueError, match="aggregate_label"):
            timing_input(unsafe_label)

    report = build(timing_input("digest-aggregate"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchEventCatalystTimingMemoryReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            status=report.status,
            recommended_next_step=report.recommended_next_step,
            aggregate_count=report.aggregate_count,
            pass_aggregate_count=report.pass_aggregate_count,
            watch_aggregate_count=report.watch_aggregate_count,
            block_aggregate_count=report.block_aggregate_count,
            flagged_aggregate_count=report.flagged_aggregate_count,
            flagged_aggregate_ratio=report.flagged_aggregate_ratio,
            catalyst_freshness_risk_count=report.catalyst_freshness_risk_count,
            weak_evidence_lead_time_count=report.weak_evidence_lead_time_count,
            stale_thesis_risk_count=report.stale_thesis_risk_count,
            recheck_urgency_count=report.recheck_urgency_count,
            highest_timing_memory_risk_score=report.highest_timing_memory_risk_score,
            max_catalyst_freshness_hours=report.max_catalyst_freshness_hours,
            min_evidence_lead_time_hours=report.min_evidence_lead_time_hours,
            max_stale_thesis_risk_score=report.max_stale_thesis_risk_score,
            max_recheck_urgency_score=report.max_recheck_urgency_score,
            rows=report.rows,
            reason_codes=report.reason_codes,
            derived_validation_digest="0" * 64,
        )


def test_module_has_no_runtime_or_trading_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_CATALYST_TIMING_MEMORY_REPORT_CONFIG_VERSION",
        "REASON_CODES",
        "ResearchEventCatalystTimingMemoryConfig",
        "ResearchEventCatalystTimingMemoryInput",
        "ResearchEventCatalystTimingMemoryReport",
        "ResearchEventCatalystTimingMemoryRow",
        "TIMING_MEMORY_STATUSES",
        "build_research_event_catalyst_timing_memory_report",
        "research_event_catalyst_timing_memory_report_to_payload",
    )

    forbidden_import_roots = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "supabase",
    )
    forbidden_call_names = {
        "authenticate",
        "cancel_order",
        "create_order",
        "open",
        "place_order",
        "read_text",
        "submit_order",
        "write_text",
    }
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", *forbidden_call_names}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    assert not any(
        imported_module.split(".")[0] in forbidden_import_roots
        for imported_module in imported_modules
    )


def _type_uses_float(hint: object) -> bool:
    if hint is float:
        return True
    return any(_type_uses_float(arg) for arg in getattr(hint, "__args__", ()))
