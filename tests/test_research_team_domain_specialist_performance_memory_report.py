from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, get_type_hints

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_domain_specialist_performance_memory_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_specialist_performance_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-domain-specialist-performance-memory-report-test",
        "min_memory_sample_count": d("10"),
        "calibration_error_watch_threshold": d("0.075000"),
        "calibration_error_block_threshold": d("0.150000"),
        "stale_feedback_rate_watch_threshold": d("0.300000"),
        "stale_feedback_rate_block_threshold": d("0.600000"),
        "unresolved_conflict_count_watch_threshold": d("2"),
        "unresolved_conflict_count_block_threshold": d("10"),
        "review_latency_hours_watch_threshold": d("25.000000"),
        "review_latency_hours_block_threshold": d("100.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSpecialistPerformanceMemoryConfig(**values)


def fact(**overrides: object):
    module = api()
    values = {
        "domain": "macro-rates",
        "memory_sample_count": d("10"),
        "calibration_error": d("0.000000"),
        "stale_feedback_rate": d("0.000000"),
        "unresolved_conflict_count": d("0"),
        "average_review_latency_hours": d("0.000000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSpecialistPerformanceMemoryFact(**values)


def build_report(*facts: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_specialist_performance_memory_report(
        facts,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected primitive numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
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


def test_builds_deterministic_domain_performance_memory_report() -> None:
    report = build_report(
        fact(
            domain="sports",
            memory_sample_count=d("10"),
            calibration_error=d("0.000000"),
            stale_feedback_rate=d("0.000000"),
            unresolved_conflict_count=d("0"),
            average_review_latency_hours=d("0.000000"),
        ),
        fact(
            domain="macro-rates",
            memory_sample_count=d("10"),
            calibration_error=d("0.100000"),
            stale_feedback_rate=d("0.300000"),
            unresolved_conflict_count=d("2"),
            average_review_latency_hours=d("25.000000"),
        ),
        fact(
            domain="crypto",
            memory_sample_count=d("5"),
            calibration_error=d("0.200000"),
            stale_feedback_rate=d("0.800000"),
            unresolved_conflict_count=d("10"),
            average_review_latency_hours=d("100.000000"),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.domain_count == d("3")
    assert report.memory_sample_count == d("25")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_calibration_error == d("0.080000")
    assert report.average_stale_feedback_rate == d("0.280000")
    assert report.total_unresolved_conflict_count == d("12")
    assert report.max_review_latency_hours == d("100.000000")
    assert report.average_performance_memory_quality_score == d("0.786000")
    assert tuple(row.domain for row in report.rows) == (
        "sports",
        "macro-rates",
        "crypto",
    )
    assert tuple(row.status for row in report.rows) == ("pass", "watch", "block")
    assert tuple(row.performance_memory_quality_score for row in report.rows) == (
        d("1.000000"),
        d("0.800000"),
        d("0.330000"),
    )
    assert report.rows[0].reason_codes == (
        "domain_specialist_performance_memory_pass",
    )
    assert report.rows[1].reason_codes == (
        "calibration_error_watch",
        "stale_feedback_rate_watch",
        "unresolved_conflict_count_watch",
        "review_latency_hours_watch",
        "domain_specialist_performance_memory_watch",
    )
    assert report.rows[2].reason_codes == (
        "insufficient_memory_sample_count",
        "calibration_error_block",
        "stale_feedback_rate_block",
        "unresolved_conflict_count_block",
        "review_latency_hours_block",
        "domain_specialist_performance_memory_block",
    )
    assert report.reason_codes == (
        "insufficient_memory_sample_count",
        "calibration_error_block",
        "stale_feedback_rate_block",
        "unresolved_conflict_count_block",
        "review_latency_hours_block",
        "calibration_error_watch",
        "stale_feedback_rate_watch",
        "unresolved_conflict_count_watch",
        "review_latency_hours_watch",
        "domain_specialist_performance_memory_block",
        "domain_specialist_performance_memory_watch",
    )


def test_aggregates_multiple_sanitized_facts_by_domain_before_scoring() -> None:
    report = build_report(
        fact(domain="macro-rates", memory_sample_count=d("4"), calibration_error=d("0.000000")),
        fact(
            domain="macro-rates",
            memory_sample_count=d("6"),
            calibration_error=d("0.100000"),
            stale_feedback_rate=d("0.500000"),
            unresolved_conflict_count=d("3"),
            average_review_latency_hours=d("50.000000"),
        ),
    )

    assert report.domain_count == d("1")
    assert report.memory_sample_count == d("10")
    assert report.rows[0].domain == "macro-rates"
    assert report.rows[0].calibration_error == d("0.060000")
    assert report.rows[0].stale_feedback_rate == d("0.300000")
    assert report.rows[0].unresolved_conflict_count == d("3")
    assert report.rows[0].average_review_latency_hours == d("30.000000")
    assert report.rows[0].status == "watch"


def test_empty_fact_set_blocks_report_only_summary() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.domain_count == d("0")
    assert report.memory_sample_count == d("0")
    assert report.average_calibration_error is None
    assert report.average_stale_feedback_rate is None
    assert report.total_unresolved_conflict_count == d("0")
    assert report.max_review_latency_hours is None
    assert report.average_performance_memory_quality_score is None
    assert report.rows == ()
    assert report.reason_codes == ("no_domain_specialist_performance_memory_facts",)
    assert report.reason_code_counts[0].reason_code == (
        "no_domain_specialist_performance_memory_facts"
    )
    assert report.reason_code_counts[0].count == d("1")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_canonical_digest_bound_and_public_safe() -> None:
    module = api()
    report = build_report(fact())

    payload = module.research_team_domain_specialist_performance_memory_report_payload(
        report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["status"] == "pass"
    assert payload["memory_sample_count"] == "10"
    assert payload["average_calibration_error"] == "0.000000"
    assert payload["rows"][0]["domain"] == "macro-rates"
    assert payload["rows"][0]["performance_memory_quality_score"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "private",
        "wallet",
        "order",
        "trade",
        "recommendation",
        "sizing",
        "http://",
        "https://",
    )
    assert all(fragment not in encoded.lower() for fragment in forbidden_fragments)

    tampered = dict(payload)
    tampered["average_calibration_error"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_specialist_performance_memory_report_payload(tampered)

    unsafe = dict(payload)
    unsafe["source_url"] = "https://private.example/source"
    unsafe["derived_validation_digest"] = canonical_digest(unsafe)
    with pytest.raises(ValueError, match="unsafe"):
        module.research_team_domain_specialist_performance_memory_report_payload(unsafe)


def test_validation_rejects_non_decimal_bad_statuses_unsafe_values_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at"):
        build_report(fact(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            fact(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_research_team_domain_specialist_performance_memory_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="domain"):
        fact(domain="https://private.example/team")
    with pytest.raises(ValueError, match="memory_sample_count"):
        fact(memory_sample_count=10)
    with pytest.raises(ValueError, match="calibration_error"):
        fact(calibration_error=0.1)
    with pytest.raises(ValueError, match="stale_feedback_rate"):
        fact(stale_feedback_rate=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="unresolved_conflict_count"):
        fact(unresolved_conflict_count=d("1.5"))
    with pytest.raises(ValueError, match="average_review_latency_hours"):
        fact(average_review_latency_hours=Decimal("NaN"))
    with pytest.raises(ValueError, match="block threshold"):
        config(calibration_error_watch_threshold=d("0.200000"))
    with pytest.raises(ValueError, match="facts"):
        build_report(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(fact(), paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(build_report(fact()), status="blocked")
    with pytest.raises(TypeError):
        type("FactSubclass", (module.ResearchTeamDomainSpecialistPerformanceMemoryFact,), {})


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    report = build_report(fact())
    items = (
        config(),
        fact(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )

    for item in items:
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    decimal_fields = {
        "min_memory_sample_count",
        "calibration_error_watch_threshold",
        "calibration_error_block_threshold",
        "stale_feedback_rate_watch_threshold",
        "stale_feedback_rate_block_threshold",
        "unresolved_conflict_count_watch_threshold",
        "unresolved_conflict_count_block_threshold",
        "review_latency_hours_watch_threshold",
        "review_latency_hours_block_threshold",
        "memory_sample_count",
        "calibration_error",
        "stale_feedback_rate",
        "unresolved_conflict_count",
        "average_review_latency_hours",
        "performance_memory_quality_score",
        "domain_count",
        "pass_count",
        "watch_count",
        "block_count",
        "total_unresolved_conflict_count",
        "count",
    }
    optional_decimal_fields = {
        "average_calibration_error",
        "average_stale_feedback_rate",
        "average_performance_memory_quality_score",
        "max_review_latency_hours",
    }
    for cls in (
        module.ResearchTeamDomainSpecialistPerformanceMemoryConfig,
        module.ResearchTeamDomainSpecialistPerformanceMemoryFact,
        module.ResearchTeamDomainSpecialistPerformanceMemoryRow,
        module.ResearchTeamDomainSpecialistPerformanceMemoryReasonCodeCount,
        module.ResearchTeamDomainSpecialistPerformanceMemoryReport,
    ):
        hints = get_type_hints(cls)
        for item in fields(cls):
            if item.name in decimal_fields:
                assert hints[item.name] is Decimal
            if item.name in optional_decimal_fields:
                assert hints[item.name] == Decimal | None

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    assert module.research_team_domain_specialist_performance_memory_report_digest(
        report,
    ) == report.derived_validation_digest


def test_owned_module_has_no_db_network_wallet_order_trade_sizing_or_recommendation_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "private",
        "wallet",
        "order",
        "trade",
        "database",
        "network",
        "requests",
        "urllib",
        "socket",
        "sqlite",
        "recommend",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    field_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            field_names.append(node.target.id)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "os",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "persist",
        "rollback",
        "send",
        "write",
    }
    forbidden_field_names = {
        "account_id",
        "auth_token",
        "candidate_id",
        "condition_id",
        "market_id",
        "market_slug",
        "order_id",
        "private_token",
        "raw_candidate_id",
        "raw_market_id",
        "source_text",
        "source_url",
        "trade_id",
        "wallet_address",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert not any(name in forbidden_field_names for name in field_names)
    assert_no_float_or_int_values([imports, call_names, attribute_names, field_names])
