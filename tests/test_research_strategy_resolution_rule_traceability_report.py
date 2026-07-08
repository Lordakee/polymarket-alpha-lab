from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_strategy_resolution_rule_traceability_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing traceability report module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_RESOLUTION_RULE_TRACEABILITY_REPORT_CONFIG_VERSION
        ),
        "min_pass_rule_specificity": d("0.750000"),
        "min_watch_rule_specificity": d("0.500000"),
        "min_pass_official_evidence_strength": d("0.750000"),
        "min_watch_official_evidence_strength": d("0.500000"),
        "min_pass_quorum_source_count": d("3"),
        "min_watch_quorum_source_count": d("2"),
        "max_pass_contradiction_pressure": d("0.100000"),
        "max_watch_contradiction_pressure": d("0.350000"),
    }
    values.update(overrides)
    return module.ResearchStrategyResolutionRuleTraceabilityConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "trace_reference": "https://internal.example/rules/alpha?token=secret",
        "resolution_rule_reference": "raw-market-rule-alpha",
        "official_evidence_reference": "https://official.example/final-result",
        "observed_at": GENERATED_AT,
        "rule_specificity": d("0.900000"),
        "official_evidence_strength": d("0.850000"),
        "quorum_source_count": d("4"),
        "independent_source_count": d("3"),
        "contradiction_pressure": d("0.050000"),
    }
    values.update(overrides)
    return module.ResearchStrategyResolutionRuleTraceabilityObservation(**values)


def report(*observations: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_resolution_rule_traceability_report(
        observations,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_sha256(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def assert_no_decimal_objects(value: Any) -> None:
    if isinstance(value, Decimal):
        raise AssertionError(f"unexpected Decimal object {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            assert_no_decimal_objects(item)


def iter_payload_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(iter_payload_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(iter_payload_keys(item))
        return tuple(keys)
    return ()


def test_builds_aggregate_traceability_rows_with_pass_watch_block_statuses() -> None:
    result = report(
        observation(trace_reference="pass-secret-token", resolution_rule_reference="rule-pass"),
        observation(
            trace_reference="watch-secret-token",
            resolution_rule_reference="rule-watch",
            official_evidence_strength=d("0.600000"),
            quorum_source_count=d("2"),
            independent_source_count=d("2"),
            contradiction_pressure=d("0.250000"),
        ),
        observation(
            trace_reference="block-secret-token",
            resolution_rule_reference="rule-block",
            rule_specificity=d("0.300000"),
            official_evidence_strength=d("0.400000"),
            quorum_source_count=d("1"),
            independent_source_count=d("1"),
            contradiction_pressure=d("0.800000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-strategy-resolution-rule-traceability-report-v0"
    assert result.trace_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.status == "block"
    assert result.max_contradiction_pressure == d("0.800000")
    assert result.average_traceability_score == d("0.654167")
    assert result.reason_codes == (
        "rule_specificity_block",
        "official_evidence_strength_block",
        "source_quorum_block",
        "contradiction_pressure_block",
        "official_evidence_strength_watch",
        "source_quorum_watch",
        "contradiction_pressure_watch",
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")

    blocked, watched, passed = result.rows
    assert blocked.traceability_score == d("0.308333")
    assert blocked.reason_codes == (
        "rule_specificity_block",
        "official_evidence_strength_block",
        "source_quorum_block",
        "contradiction_pressure_block",
    )
    assert watched.traceability_score == d("0.729167")
    assert watched.reason_codes == (
        "official_evidence_strength_watch",
        "source_quorum_watch",
        "contradiction_pressure_watch",
    )
    assert passed.traceability_score == d("0.925000")
    assert passed.reason_codes == ("resolution_rule_traceability_pass",)
    for item in (result, *result.rows):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True


def test_public_payload_is_canonical_redacted_decimal_stringed_and_validated() -> None:
    module = api()
    result = report(
        observation(
            trace_reference="trace-secret-wallet-token",
            resolution_rule_reference="raw-market-rule-secret",
            official_evidence_reference="https://official.example/final?token=private",
        ),
        generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    assert module.validate_research_strategy_resolution_rule_traceability_report(result) is True
    payload = module.research_strategy_resolution_rule_traceability_report_payload(result)
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["trace_count"] == "1.000000"
    assert payload["average_traceability_score"] == "0.925000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["trace_digest"].startswith("trace_")
    assert payload["rows"][0]["rule_digest"].startswith("rule_")
    assert payload["rows"][0]["evidence_digest"].startswith("evidence_")
    assert payload["rows"][0]["traceability_score"] == "0.925000"
    assert payload["rows"][0]["status"] == "pass"
    assert_sha256(payload["rows"][0]["row_sha256"])
    assert_sha256(payload["rows"][0]["derived_validation_digest"])
    assert_sha256(payload["report_sha256"])
    assert_sha256(payload["derived_validation_digest"])
    assert module.validate_research_strategy_resolution_rule_traceability_public_payload(payload)

    for forbidden in (
        "secret",
        "wallet",
        "token",
        "raw-market",
        "official.example",
        "https://",
    ):
        assert forbidden not in rendered
    for key in iter_payload_keys(payload):
        lowered = key.lower()
        assert "candidate" not in lowered
        assert "market" not in lowered
        assert "slug" not in lowered
        assert "question" not in lowered
        assert "source_text" not in lowered
        assert "dsn" not in lowered
        assert "table" not in lowered
    assert {row["status"] for row in payload["rows"]} <= {"pass", "watch", "block"}
    assert_no_float_values(payload)
    assert_no_decimal_objects(payload)


def test_empty_report_is_block_zeroed_decimal_and_readonly() -> None:
    empty = report()

    assert empty.trace_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.max_contradiction_pressure == ZERO
    assert empty.average_traceability_score == ZERO
    assert empty.status == "block"
    assert empty.reason_codes == ("resolution_rule_traceability_empty",)
    assert empty.rows == ()
    assert_sha256(empty.report_sha256)
    for item in fields(empty):
        item_value = getattr(empty, item.name)
        if item.name in {"paper_only", "report_only", "readonly"}:
            continue
        if item.name.endswith(("_count", "_pressure", "_score")):
            assert type(item_value) is Decimal


def test_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    row = report(observation()).rows[0]

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]

    for klass in (
        module.ResearchStrategyResolutionRuleTraceabilityConfig,
        module.ResearchStrategyResolutionRuleTraceabilityObservation,
        module.ResearchStrategyResolutionRuleTraceabilityRow,
        module.ResearchStrategyResolutionRuleTraceabilityReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchStrategyResolutionRuleTraceabilityConfig):
            pass

    with pytest.raises(ValueError, match="Decimal"):
        observation(rule_specificity=0.5)
    with pytest.raises(ValueError, match="exact Decimal"):
        observation(rule_specificity=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="datetime"):
        module.build_research_strategy_resolution_rule_traceability_report(
            [observation()],
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC),
        )


def test_hard_flags_and_digest_validation_reject_tampering() -> None:
    module = api()
    result = report(observation())

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="row_sha256"):
        replace(result.rows[0], row_sha256="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result.rows[0], derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report_sha256"):
        replace(result, report_sha256="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, derived_validation_digest="0" * 64)

    payload = module.research_strategy_resolution_rule_traceability_report_payload(result)
    tampered = {**payload, "average_traceability_score": "0.123456"}
    with pytest.raises(ValueError, match="report_sha256"):
        module.validate_research_strategy_resolution_rule_traceability_public_payload(tampered)


def test_rejects_invalid_inputs_thresholds_statuses_and_public_payload_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="observations"):
        module.build_research_strategy_resolution_rule_traceability_report(
            "not-observations",
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="Observation"):
        module.build_research_strategy_resolution_rule_traceability_report(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_research_strategy_resolution_rule_traceability_report(
            [observation()],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        report(observation(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="duplicate trace_reference"):
        report(observation(), observation())
    with pytest.raises(ValueError, match="quorum_source_count"):
        observation(quorum_source_count=d("1.5"))
    with pytest.raises(ValueError, match="independent_source_count"):
        observation(quorum_source_count=d("2"), independent_source_count=d("3"))
    with pytest.raises(ValueError, match="min_pass_rule_specificity"):
        config(min_pass_rule_specificity=d("0.400000"))
    with pytest.raises(ValueError, match="max_pass_contradiction_pressure"):
        config(max_pass_contradiction_pressure=d("0.400000"))
    with pytest.raises(ValueError, match="status"):
        replace(report(observation()).rows[0], status="blocked")

    payload = module.research_strategy_resolution_rule_traceability_report_payload(
        report(observation()),
    )
    unsafe_payload = {**payload, "wallet": "not public"}
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_research_strategy_resolution_rule_traceability_public_payload(
            unsafe_payload,
        )
    unsafe_value_payload = {**payload, "config_version": "https://example.test/path"}
    with pytest.raises(ValueError, match="unsafe public payload"):
        module.validate_research_strategy_resolution_rule_traceability_public_payload(
            unsafe_value_payload,
        )


def test_source_has_no_io_db_or_live_action_surface() -> None:
    module = api()
    source_path = Path(module.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)

    banned_import_roots = {
        "asyncio",
        "builtins.open",
        "csv",
        "http",
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
    assert not (set(imports) & banned_import_roots)
    lowered = source.lower()
    for term in (
        "private_key",
        "connect(",
        "execute(",
        "submit_",
        "cancel_",
        "exchange",
        "recommendation",
        "sizing",
    ):
        assert term not in lowered
    for public_name in module.__all__:
        assert "recommendation" not in public_name.lower()
        assert "sizing" not in public_name.lower()
