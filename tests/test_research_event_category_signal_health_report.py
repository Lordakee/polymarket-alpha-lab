from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_category_signal_health_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


@dataclass(frozen=True)
class SuppliedSignalShape:
    category: str
    source_freshness_ratio: Decimal
    freshest_source_age_seconds: Decimal
    corroborating_source_count: Decimal
    mechanics_health_ratio: Decimal
    team_memory_coverage_ratio: Decimal
    resolution_clarity_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_category_signal_health_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object):
    module = api()
    values = {
        "config_version": "research-event-category-signal-health-report-test",
        "target_categories": (
            "basketball",
            "commodities",
            "crypto",
            "equities",
            "football",
            "politics",
        ),
        "pass_min_signal_health_score": d("0.800000"),
        "watch_min_signal_health_score": d("0.550000"),
        "pass_max_source_age_seconds": d("86400.000000"),
        "block_min_source_age_seconds": d("604800.000000"),
        "min_source_count": d("2.000000"),
        "block_below_dimension_ratio": d("0.400000"),
        "source_weight": d("0.250000"),
        "mechanics_weight": d("0.250000"),
        "memory_weight": d("0.250000"),
        "resolution_weight": d("0.250000"),
    }
    values.update(overrides)
    return module.ResearchEventCategorySignalHealthConfig(**values)


def signal_input(**overrides: object):
    module = api()
    values = {
        "category": "politics",
        "source_freshness_ratio": d("1.000000"),
        "freshest_source_age_seconds": d("3600.000000"),
        "corroborating_source_count": d("3.000000"),
        "mechanics_health_ratio": d("0.950000"),
        "team_memory_coverage_ratio": d("0.900000"),
        "resolution_clarity_ratio": d("0.950000"),
        "reason_codes": (),
    }
    values.update(overrides)
    return module.ResearchEventCategorySignalHealthInput(**values)


def build_report(*rows: object, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_event_category_signal_health_report(
        rows,
        config=config or cfg(),
        generated_at=generated_at,
    )


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (str, datetime):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def assert_payload_public_safe(value: object) -> None:
    unsafe_terms = (
        _join_parts("raw_", "candidate"),
        _join_parts("candidate", "_id"),
        _join_parts("market", "_id"),
        _join_parts("market", "_slug"),
        "slug",
        "question",
        _join_parts("source", "_text"),
        _join_parts("source", "_url"),
        "https://",
        "dsn",
        "table",
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("liv", "e"),
        _join_parts("siz", "ing"),
        _join_parts("pos", "ition"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("rec", "ommend"),
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(term in lowered for term in unsafe_terms), key
            assert_payload_public_safe(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_public_safe(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(term in lowered for term in unsafe_terms), value


def test_report_scores_category_signal_health_across_required_categories() -> None:
    module = api()
    report = build_report(
        signal_input(category="politics"),
        SuppliedSignalShape(
            category="crypto",
            source_freshness_ratio=d("0.750000"),
            freshest_source_age_seconds=d("172800.000000"),
            corroborating_source_count=d("2.000000"),
            mechanics_health_ratio=d("0.700000"),
            team_memory_coverage_ratio=d("0.650000"),
            resolution_clarity_ratio=d("0.750000"),
            reason_codes=("manual_reviewed",),
        ),
        signal_input(
            category="football",
            source_freshness_ratio=d("0.300000"),
            freshest_source_age_seconds=d("700000.000000"),
            corroborating_source_count=d("1.000000"),
            mechanics_health_ratio=d("0.500000"),
            team_memory_coverage_ratio=d("0.200000"),
            resolution_clarity_ratio=d("0.400000"),
        ),
    )

    assert isinstance(report, module.ResearchEventCategorySignalHealthReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "research-event-category-signal-health-report-test"
    assert report.report_status == "block"
    assert report.category_count == d("6.000000")
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("4.000000")
    assert report.stale_source_count == d("2.000000")
    assert report.mechanics_gap_count == d("5.000000")
    assert report.memory_gap_count == d("5.000000")
    assert report.resolution_gap_count == d("5.000000")
    assert report.average_signal_health_score == d("0.338658")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.category for row in report.rows) == (
        "basketball",
        "commodities",
        "crypto",
        "equities",
        "football",
        "politics",
    )

    crypto = report.rows[2]
    assert crypto.public_status == "watch"
    assert crypto.source_freshness_ratio == d("0.750000")
    assert crypto.source_age_health_ratio == d("0.833333")
    assert crypto.source_count_health_ratio == d("1.000000")
    assert crypto.source_health_ratio == d("0.861111")
    assert crypto.signal_health_score == d("0.740278")
    assert crypto.reason_codes == (
        "input_manual_reviewed",
        "mechanics_health_watch",
        "research_event_category_signal_health_watch",
        "resolution_clarity_watch",
        "source_age_watch",
        "source_count_pass",
        "source_freshness_watch",
        "team_memory_watch",
    )

    football = report.rows[4]
    assert football.public_status == "block"
    assert football.source_age_health_ratio == d("0.000000")
    assert football.source_count_health_ratio == d("0.500000")
    assert football.source_health_ratio == d("0.266667")
    assert football.signal_health_score == d("0.341667")
    assert football.reason_codes == (
        "mechanics_health_watch",
        "research_event_category_signal_health_block",
        "resolution_clarity_watch",
        "source_age_block",
        "source_count_watch",
        "source_freshness_block",
        "team_memory_block",
    )

    politics = report.rows[5]
    assert politics.public_status == "pass"
    assert politics.signal_health_score == d("0.950000")
    assert politics.reason_codes == (
        "mechanics_health_pass",
        "research_event_category_signal_health_pass",
        "resolution_clarity_pass",
        "source_age_pass",
        "source_count_pass",
        "source_freshness_pass",
        "team_memory_pass",
    )


def test_empty_report_blocks_all_categories_without_private_identifiers() -> None:
    module = api()
    report = build_report()

    assert report.report_status == "block"
    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("6.000000")
    assert report.average_signal_health_score == d("0.000000")
    assert all(row.public_status == "block" for row in report.rows)
    assert all(row.reason_codes[0] == "mechanics_health_block" for row in report.rows)
    assert any(
        item.reason_code == "research_event_category_signal_health_block_missing_category"
        and item.count == d("6.000000")
        for item in report.reason_code_counts
    )
    assert report.reason_codes == tuple(item.reason_code for item in report.reason_code_counts)
    assert isinstance(report.payload, dict)
    assert_payload_public_safe(module.research_event_category_signal_health_report_payload(report))


def test_payload_is_deterministic_decimal_string_only_and_digest_validated() -> None:
    module = api()
    first = build_report(
        signal_input(category="politics"),
        signal_input(
            category="crypto",
            source_freshness_ratio=d("0.750000"),
            freshest_source_age_seconds=d("172800.000000"),
            corroborating_source_count=d("2.000000"),
            mechanics_health_ratio=d("0.700000"),
            team_memory_coverage_ratio=d("0.650000"),
            resolution_clarity_ratio=d("0.750000"),
            reason_codes=("manual_reviewed",),
        ),
    )
    second = build_report(
        signal_input(
            category="crypto",
            source_freshness_ratio=d("0.750000"),
            freshest_source_age_seconds=d("172800.000000"),
            corroborating_source_count=d("2.000000"),
            mechanics_health_ratio=d("0.700000"),
            team_memory_coverage_ratio=d("0.650000"),
            resolution_clarity_ratio=d("0.750000"),
            reason_codes=("manual_reviewed",),
        ),
        signal_input(category="politics"),
    )

    assert first.derived_validation_digest == second.derived_validation_digest

    payload = module.research_event_category_signal_health_report_payload(first)
    assert payload == module.research_event_category_signal_health_report_payload(second)
    assert payload["generated_at"] == "2026-07-08T12:00:00Z"
    assert payload["category_count"] == "6.000000"
    assert payload["input_count"] == "2.000000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_int_or_float_values(payload)
    assert_payload_public_safe(payload)

    digest = module.research_event_category_signal_health_report_digest(first)
    assert digest == {
        "generated_at": "2026-07-08T12:00:00Z",
        "config_version": "research-event-category-signal-health-report-test",
        "report_status": "block",
        "category_count": "6.000000",
        "input_count": "2.000000",
        "pass_count": "1.000000",
        "watch_count": "1.000000",
        "block_count": "4.000000",
        "reason_codes": payload["reason_codes"],
        "derived_validation_digest": first.derived_validation_digest,
    }

    tampered = dict(payload)
    tampered["average_signal_health_score"] = "0.910000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_category_signal_health_report_payload(tampered)

    with pytest.raises(ValueError, match="public"):
        module.research_event_category_signal_health_report_payload(
            {**payload, "candidate_id": "abc"},
        )


def test_validates_frozen_dataclasses_decimal_only_statuses_and_hard_flags() -> None:
    module = api()
    sample_config = cfg()
    sample_input = signal_input()
    sample_report = build_report(sample_input)

    for cls in (
        module.ResearchEventCategorySignalHealthConfig,
        module.ResearchEventCategorySignalHealthInput,
        module.ResearchEventCategorySignalHealthReasonCodeCount,
        module.ResearchEventCategorySignalHealthReport,
        module.ResearchEventCategorySignalHealthRow,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    for item in (sample_config, sample_input, sample_report, *sample_report.rows):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    with pytest.raises(TypeError, match="Decimal"):
        signal_input(source_freshness_ratio=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="exactly str"):
        signal_input(category=_StringSubclass("politics"))
    with pytest.raises(TypeError, match="exactly Decimal"):
        signal_input(mechanics_health_ratio=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        signal_input(resolution_clarity_ratio=d("1.100000"))
    with pytest.raises(ValueError, match="pass_min_signal_health_score"):
        cfg(
            pass_min_signal_health_score=d("0.500000"),
            watch_min_signal_health_score=d("0.600000"),
        )
    with pytest.raises(ValueError, match="dimension weights"):
        cfg(source_weight=d("0.300000"))
    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal_input(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        signal_input(readonly=False)
    with pytest.raises(ValueError, match="public_status must be pass, watch, or block"):
        replace(sample_report.rows[0], public_status="blocked")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(sample_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="target_categories"):
        cfg(target_categories=("politics", "crypto"))
    with pytest.raises(ValueError, match="input category"):
        build_report(signal_input(category="baseball"))


def test_public_inputs_reject_private_or_actionable_leaks() -> None:
    module = api()
    leak_values = (
        _join_parts("raw_", "candidate", "_17"),
        _join_parts("market", "_id"),
        _join_parts("market", "_slug"),
        "event_slug",
        "question_text",
        _join_parts("source", "_text"),
        _join_parts("source", "_url"),
        "https://example.test/path",
        "analytics_dsn",
        "memory_table",
        _join_parts("to", "ken", "_abc"),
        _join_parts("wal", "let", "_field"),
        _join_parts("au", "th", "_scope"),
        _join_parts("ord", "er", "_ticket"),
        _join_parts("tra", "de", "_ticket"),
        _join_parts("b", "uy", "_signal"),
        _join_parts("s", "ell", "_signal"),
        _join_parts("rec", "ommend", "_path"),
        _join_parts("pos", "ition", "_size"),
        _join_parts("siz", "ing", "_path"),
    )

    for value in leak_values:
        with pytest.raises(ValueError, match="public"):
            signal_input(reason_codes=(value,))

    payload = module.research_event_category_signal_health_report_payload(
        build_report(signal_input()),
    )
    public = repr((payload, asdict(build_report(signal_input())))).lower()
    assert_payload_public_safe(payload)
    for value in leak_values:
        assert value.lower() not in public


def test_module_is_pure_report_only_without_io_or_action_surfaces() -> None:
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(module_source)

    forbidden_import_roots = {
        "asyncio",
        "builtins",
        "httpx",
        "io",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "cancel",
        "connect",
        "cursor",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }
    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)

    forbidden_source_terms = (
        "private_key",
        _join_parts("candidate", "_id"),
        _join_parts("market", "_id"),
        _join_parts("market", "_slug"),
        "place_order",
        "cancel_order",
        "order_book",
        "trade_client",
        _join_parts("source", "_url"),
        _join_parts("source", "_text"),
        "raw_identifier",
        "position_size",
    )
    lowered = module_source.lower()
    assert not any(term in lowered for term in forbidden_source_terms)
