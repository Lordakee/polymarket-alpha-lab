import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from typing import Any

import pytest


MODULE_UNDER_TEST = (
    "polymarket_alpha_lab.research_resolution_rule_change_watch_report"
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
        module.ResearchResolutionRuleChangeWatchConfig,
        module.ResearchResolutionRuleChangeWatchInput,
        module.ResearchResolutionRuleChangeWatchReport,
    )


def _assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (Decimal, float, int):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_numeric_scalars(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_public_numeric_scalars(item)


def _config(**overrides: object) -> Any:
    Config, _Input, _Report = _types()
    values: dict[str, object] = {
        "config_version": "research-resolution-rule-change-watch-report-v0",
        "rule_version_drift_watch_threshold": Decimal("1"),
        "rule_version_drift_block_threshold": Decimal("3"),
        "min_oracle_source_consistency_watch": Decimal("0.80"),
        "min_oracle_source_consistency_block": Decimal("0.60"),
        "ambiguity_watch_threshold": Decimal("2"),
        "ambiguity_block_threshold": Decimal("5"),
        "deadline_watch_seconds": Decimal("86400"),
        "deadline_block_seconds": Decimal("3600"),
        "max_evidence_age_watch_seconds": Decimal("86400"),
        "max_evidence_age_block_seconds": Decimal("172800"),
    }
    values.update(overrides)
    return Config(**values)


def _observation(
    rule_scope: str = "federal-release-resolution-rules",
    *,
    baseline_rule_version: Decimal = Decimal("10"),
    observed_rule_version: Decimal = Decimal("10"),
    oracle_source_consistency: Decimal = Decimal("0.95"),
    ambiguity_count: Decimal = Decimal("0"),
    seconds_until_resolution_deadline: Decimal = Decimal("172800"),
    evidence_age_seconds: Decimal = Decimal("3600"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    _Config, Input, _Report = _types()
    return Input(
        rule_scope=rule_scope,
        baseline_rule_version=baseline_rule_version,
        observed_rule_version=observed_rule_version,
        oracle_source_consistency=oracle_source_consistency,
        ambiguity_count=ambiguity_count,
        seconds_until_resolution_deadline=seconds_until_resolution_deadline,
        evidence_age_seconds=evidence_age_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _build(observations: tuple[Any, ...], **config_overrides: object) -> Any:
    module = _module_under_test()
    return module.build_research_resolution_rule_change_watch_report(
        observations,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _payload(report: Any) -> dict[str, Any]:
    module = _module_under_test()
    return module.research_resolution_rule_change_watch_report_payload(report)


def test_report_aggregates_resolution_rule_change_risk_public_safe() -> None:
    blocked = _observation(
        "election-certification-rules",
        baseline_rule_version=Decimal("3"),
        observed_rule_version=Decimal("7"),
        oracle_source_consistency=Decimal("0.55"),
        ambiguity_count=Decimal("6"),
        seconds_until_resolution_deadline=Decimal("1800"),
        evidence_age_seconds=Decimal("200000"),
    )
    passing = _observation("federal-release-resolution-rules")
    watched = _observation(
        "weather-settlement-rules",
        baseline_rule_version=Decimal("10"),
        observed_rule_version=Decimal("12"),
        oracle_source_consistency=Decimal("0.75"),
        ambiguity_count=Decimal("3"),
        seconds_until_resolution_deadline=Decimal("36000"),
        evidence_age_seconds=Decimal("100000"),
    )

    _Config, _Input, Report = _types()
    report = _build((watched, passing, blocked))

    assert isinstance(report, Report)
    assert _module_under_test().STATUSES == ("pass", "watch", "block")
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.observation_count == Decimal("3")
    assert report.rule_version_drift_count == Decimal("2")
    assert report.oracle_source_consistency_gap_count == Decimal("2")
    assert report.ambiguity_count == Decimal("9")
    assert report.deadline_pressure_count == Decimal("2")
    assert report.stale_evidence_count == Decimal("2")
    assert report.max_rule_version_drift == Decimal("4.000000")
    assert report.min_oracle_source_consistency == Decimal("0.550000")
    assert report.min_seconds_until_resolution_deadline == Decimal("1800.000000")
    assert report.max_evidence_age_seconds == Decimal("200000.000000")
    assert tuple((row.rule_scope, row.status) for row in report.rows) == (
        ("election-certification-rules", "block"),
        ("federal-release-resolution-rules", "pass"),
        ("weather-settlement-rules", "watch"),
    )
    assert report.reason_codes == (
        "rule_version_drift_block",
        "oracle_source_consistency_block",
        "resolution_rule_ambiguity_block",
        "deadline_pressure_block",
        "evidence_freshness_block",
        "rule_version_drift_watch",
        "oracle_source_consistency_watch",
        "resolution_rule_ambiguity_watch",
        "deadline_pressure_watch",
        "evidence_freshness_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload_text = repr(_payload(report)).lower()
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
        assert unsafe_fragment not in payload_text


def test_payload_and_digest_are_deterministic_and_tamper_evident() -> None:
    observations = (
        _observation(
            "weather-settlement-rules",
            baseline_rule_version=Decimal("10"),
            observed_rule_version=Decimal("12"),
            oracle_source_consistency=Decimal("0.75"),
            ambiguity_count=Decimal("3"),
            seconds_until_resolution_deadline=Decimal("36000"),
            evidence_age_seconds=Decimal("100000"),
        ),
        _observation("federal-release-resolution-rules"),
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
    _assert_no_public_numeric_scalars(first)

    tampered = dict(first)
    tampered["max_evidence_age_seconds"] = "1.000000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        _payload(tampered)

    decimal_not_string = dict(first)
    decimal_not_string["observation_count"] = Decimal("2")
    with pytest.raises(ValueError, match="Decimal-derived string"):
        _payload(decimal_not_string)

    unsafe_key = dict(first)
    unsafe_key["market_id"] = "0xabc"
    with pytest.raises(ValueError, match="unsafe|unexpected"):
        _payload(unsafe_key)

    unsafe_value = dict(first)
    unsafe_value["reason_codes"] = ["https://raw.example/rule"]
    with pytest.raises(ValueError, match="unsafe"):
        _payload(unsafe_value)


def test_pass_report_is_frozen_report_only_and_has_public_decimal_payload() -> None:
    Config, Input, Report = _types()
    report = _build((_observation(),))
    payload = _payload(report)

    assert report.status == "pass"
    assert report.reason_codes == ("research_resolution_rule_change_watch_passed",)
    assert payload["status"] == "pass"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["observation_count"] == "1"
    assert payload["max_rule_version_drift"] == "0.000000"
    assert payload["min_oracle_source_consistency"] == "0.950000"
    _assert_no_public_numeric_scalars(payload)

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    for cls in (Config, Input, Report, type(report.rows[0])):
        public_field_names = {field.name for field in fields(cls)}
        for forbidden in (
            "market",
            "condition",
            "url",
            "raw",
            "reference",
            "ref",
        ):
            assert not any(
                forbidden in field_name.lower()
                for field_name in public_field_names
            )


def test_rejects_non_decimal_numeric_inputs_unsafe_scope_and_bad_time() -> None:
    with pytest.raises(ValueError, match="baseline_rule_version"):
        _observation(baseline_rule_version=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_rule_version"):
        _observation(observed_rule_version=10.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="oracle_source_consistency"):
        _observation(oracle_source_consistency=_DecimalSubclass("0.90"))
    with pytest.raises(ValueError, match="oracle_source_consistency"):
        _observation(oracle_source_consistency=Decimal("1.01"))
    with pytest.raises(ValueError, match="ambiguity_count"):
        _observation(ambiguity_count=Decimal("-1"))
    with pytest.raises(ValueError, match="rule_scope"):
        _observation("https://example.invalid/resolution-rule")
    with pytest.raises(ValueError, match="rule_scope"):
        _observation("market-0xabc-condition")
    with pytest.raises(ValueError, match="paper_only"):
        _observation(paper_only=False)
    with pytest.raises(ValueError, match="rule_version_drift_watch_threshold"):
        _config(rule_version_drift_watch_threshold=1)
    with pytest.raises(ValueError, match="min_oracle_source_consistency_block"):
        _config(min_oracle_source_consistency_block=Decimal("0.90"))

    module = _module_under_test()
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_resolution_rule_change_watch_report(
            (_observation(),),
            config=_config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_resolution_rule_change_watch_report(
            (_observation(),),
            config=_config(),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_resolution_rule_change_watch_report(
            (_observation(),),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )


def test_module_is_pure_readonly_report_scope_without_live_surfaces() -> None:
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
