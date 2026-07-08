from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from typing import Any

import pytest


MODULE_UNDER_TEST = (
    "polymarket_alpha_lab.research_resolution_rule_memory_health_report"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _module_under_test() -> Any:
    try:
        return importlib.import_module(MODULE_UNDER_TEST)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_UNDER_TEST:
            pytest.fail(f"{MODULE_UNDER_TEST} does not exist")
        raise


def _types() -> tuple[Any, Any, Any]:
    module = _module_under_test()
    return (
        module.ResearchResolutionRuleMemoryHealthConfig,
        module.ResearchResolutionRuleMemoryHealthObservation,
        module.ResearchResolutionRuleMemoryHealthReport,
    )


def _config(**overrides: object) -> Any:
    Config, _Observation, _Report = _types()
    values: dict[str, object] = {
        "config_version": "research-resolution-rule-memory-health-report-v0",
        "min_pattern_memory_confidence_watch": Decimal("0.700000"),
        "min_pattern_memory_confidence_block": Decimal("0.400000"),
        "rule_change_risk_watch_score": Decimal("0.300000"),
        "rule_change_risk_block_score": Decimal("0.750000"),
        "ambiguity_backlog_watch_count": Decimal("2"),
        "ambiguity_backlog_block_count": Decimal("5"),
        "recheck_watch_age_seconds": Decimal("604800"),
        "recheck_block_age_seconds": Decimal("2592000"),
    }
    values.update(overrides)
    return Config(**values)


def _observation(
    rule_pattern: str = "weather-settlement-rules",
    *,
    pattern_observation_count: Decimal = Decimal("10"),
    confirmed_resolution_count: Decimal = Decimal("9"),
    rule_change_risk_score: Decimal = Decimal("0.100000"),
    ambiguity_backlog_count: Decimal = Decimal("0"),
    last_rechecked_at: datetime | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    _Config, Observation, _Report = _types()
    return Observation(
        rule_pattern=rule_pattern,
        pattern_observation_count=pattern_observation_count,
        confirmed_resolution_count=confirmed_resolution_count,
        rule_change_risk_score=rule_change_risk_score,
        ambiguity_backlog_count=ambiguity_backlog_count,
        last_rechecked_at=(
            last_rechecked_at
            if last_rechecked_at is not None
            else GENERATED_AT - timedelta(days=1)
        ),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _build(observations: tuple[Any, ...], **config_overrides: object) -> Any:
    module = _module_under_test()
    return module.build_research_resolution_rule_memory_health_report(
        observations,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _payload(report: Any) -> dict[str, Any]:
    module = _module_under_test()
    return module.research_resolution_rule_memory_health_report_payload(report)


def _assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (Decimal, float, int):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_numeric_scalars(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_public_numeric_scalars(item)


def test_report_aggregates_rule_memory_risk_backlog_and_recheck_urgency() -> None:
    blocked = _observation(
        "election-certification-rules",
        pattern_observation_count=Decimal("4"),
        confirmed_resolution_count=Decimal("1"),
        rule_change_risk_score=Decimal("0.800000"),
        ambiguity_backlog_count=Decimal("6"),
        last_rechecked_at=GENERATED_AT - timedelta(days=45),
    )
    watched = _observation(
        "sports-stat-correction-rules",
        pattern_observation_count=Decimal("6"),
        confirmed_resolution_count=Decimal("4"),
        rule_change_risk_score=Decimal("0.350000"),
        ambiguity_backlog_count=Decimal("3"),
        last_rechecked_at=GENERATED_AT - timedelta(days=14),
    )
    passing = _observation("weather-settlement-rules")

    _Config, _Observation, Report = _types()
    report = _build((watched, passing, blocked))

    assert isinstance(report, Report)
    assert _module_under_test().STATUSES == ("pass", "watch", "block")
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.pattern_count == Decimal("3")
    assert report.pass_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.block_count == Decimal("1")
    assert report.total_pattern_observation_count == Decimal("20")
    assert report.total_ambiguity_backlog_count == Decimal("9")
    assert report.rule_change_risk_count == Decimal("2")
    assert report.ambiguity_backlog_pattern_count == Decimal("2")
    assert report.urgent_recheck_pattern_count == Decimal("2")
    assert report.average_pattern_memory_confidence == Decimal("0.605556")
    assert report.max_rule_change_risk_score == Decimal("0.800000")
    assert report.max_recheck_urgency_score == Decimal("1.000000")
    assert tuple((row.rule_pattern, row.status) for row in report.rows) == (
        ("election-certification-rules", "block"),
        ("sports-stat-correction-rules", "watch"),
        ("weather-settlement-rules", "pass"),
    )
    assert report.rows[0].pattern_memory_confidence == Decimal("0.250000")
    assert report.rows[0].recheck_urgency_score == Decimal("1.000000")
    assert report.rows[1].pattern_memory_confidence == Decimal("0.666667")
    assert report.rows[1].recheck_urgency_score == Decimal("0.466667")
    assert report.reason_codes == (
        "pattern_memory_confidence_block",
        "rule_change_risk_block",
        "ambiguity_backlog_block",
        "recheck_urgency_block",
        "pattern_memory_confidence_watch",
        "rule_change_risk_watch",
        "ambiguity_backlog_watch",
        "recheck_urgency_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_and_digest_are_deterministic_public_and_tamper_evident() -> None:
    observations = (
        _observation(
            "sports-stat-correction-rules",
            pattern_observation_count=Decimal("6"),
            confirmed_resolution_count=Decimal("4"),
            rule_change_risk_score=Decimal("0.350000"),
            ambiguity_backlog_count=Decimal("3"),
            last_rechecked_at=GENERATED_AT - timedelta(days=14),
        ),
        _observation("weather-settlement-rules"),
    )

    first = _payload(_build(observations))
    second = _payload(_build(tuple(reversed(observations))))

    assert first == second
    assert len(first["derived_validation_digest"]) == 64
    assert all(
        character in "0123456789abcdef"
        for character in first["derived_validation_digest"]
    )
    assert _payload(first) == first
    assert first["paper_only"] is True
    assert first["report_only"] is True
    assert first["readonly"] is True
    assert first["pattern_count"] == "2"
    assert first["rows"][0][0] == "sports-stat-correction-rules"
    assert first["rows"][0][3] == "0.666667"
    _assert_no_public_numeric_scalars(first)

    encoded = repr(first).lower()
    for unsafe_fragment in (
        "https://",
        "source_url",
        "raw_text",
        "raw_ref",
        "market_id",
        "condition_id",
        "question",
        "slug",
        "recommend",
        "sizing",
    ):
        assert unsafe_fragment not in encoded

    tampered = dict(first)
    tampered["max_rule_change_risk_score"] = "0.010000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        _payload(tampered)

    decimal_not_string = dict(first)
    decimal_not_string["pattern_count"] = Decimal("2")
    with pytest.raises(ValueError, match="Decimal-derived string"):
        _payload(decimal_not_string)

    unsafe_key = dict(first)
    unsafe_key["market_slug"] = "raw-market"
    with pytest.raises(ValueError, match="unsafe|unexpected"):
        _payload(unsafe_key)

    unsafe_value = dict(first)
    unsafe_value["reason_codes"] = ["https://raw.example/rule"]
    with pytest.raises(ValueError, match="unsafe"):
        _payload(unsafe_value)


def test_pass_report_is_frozen_report_only_and_exposes_no_raw_identifier_fields() -> None:
    Config, Observation, Report = _types()
    report = _build((_observation(),))
    payload = _payload(report)

    assert report.status == "pass"
    assert report.reason_codes == ("resolution_rule_memory_health_passed",)
    assert payload["status"] == "pass"
    assert payload["pattern_count"] == "1"
    assert payload["max_rule_change_risk_score"] == "0.100000"
    assert payload["average_pattern_memory_confidence"] == "0.900000"
    _assert_no_public_numeric_scalars(payload)

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="watch")

    for cls in (Config, Observation, Report, type(report.rows[0])):
        public_field_names = {field.name for field in fields(cls)}
        for forbidden in (
            "market",
            "condition",
            "url",
            "raw",
            "reference",
            "ref",
            "source",
            "slug",
        ):
            assert not any(
                forbidden in field_name.lower()
                for field_name in public_field_names
            )


def test_rejects_bad_decimal_time_pattern_config_and_flags() -> None:
    with pytest.raises(ValueError, match="pattern_observation_count"):
        _observation(pattern_observation_count=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="rule_change_risk_score"):
        _observation(rule_change_risk_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="rule_change_risk_score"):
        _observation(rule_change_risk_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="ambiguity_backlog_count"):
        _observation(ambiguity_backlog_count=Decimal("-1"))
    with pytest.raises(ValueError, match="confirmed_resolution_count"):
        _observation(
            pattern_observation_count=Decimal("2"),
            confirmed_resolution_count=Decimal("3"),
        )
    with pytest.raises(ValueError, match="rule_pattern"):
        _observation(" weather-settlement-rules")
    with pytest.raises(ValueError, match="rule_pattern"):
        _observation("https://example.invalid/rule")
    with pytest.raises(ValueError, match="rule_pattern"):
        _observation("market-0xabc-condition")
    with pytest.raises(ValueError, match="last_rechecked_at"):
        _observation(last_rechecked_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="paper_only"):
        _observation(paper_only=False)
    with pytest.raises(ValueError, match="min_pattern_memory_confidence_block"):
        _config(min_pattern_memory_confidence_block=Decimal("0.800000"))
    with pytest.raises(ValueError, match="rule_change_risk_watch_score"):
        _config(rule_change_risk_watch_score=Decimal("0.800000"))
    with pytest.raises(ValueError, match="recheck_watch_age_seconds"):
        _config(recheck_watch_age_seconds=Decimal("2592001"))

    module = _module_under_test()
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_resolution_rule_memory_health_report(
            (_observation(),),
            config=_config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_resolution_rule_memory_health_report(
            (_observation(),),
            config=_config(),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_resolution_rule_memory_health_report(
            (_observation(),),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="last_rechecked_at"):
        module.build_research_resolution_rule_memory_health_report(
            (
                _observation(
                    last_rechecked_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_module_is_pure_readonly_report_scope_without_side_effect_surfaces() -> None:
    module = _module_under_test()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
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
        "fetch",
        "request",
        "submit",
        "cancel",
    }
    forbidden_attr_fragments = (
        "broker",
        "client",
        "connection",
        "cursor",
        "session",
    )
    forbidden_source_tokens = (
        "recommendation",
        "sizing",
        "position_size",
        "wallet",
        "auth",
        "order",
        "trade",
        "live execution",
    )

    for token in forbidden_source_tokens:
        assert token not in source.lower()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = node.names if isinstance(node, ast.Import) else [node]
            for alias in names:
                root = (
                    alias.name
                    if isinstance(node, ast.Import)
                    else (node.module or "")
                ).split(".")[0]
                assert root not in forbidden_import_roots
        if isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            if isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
        if isinstance(node, ast.Attribute):
            assert not any(
                fragment in node.attr.lower()
                for fragment in forbidden_attr_fragments
            )
