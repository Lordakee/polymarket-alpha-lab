from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_domain_cricket_signal_memory_quality_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_domain_cricket_signal_memory_quality_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def memory_input(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "event_bucket": "cricket_event_group_a",
        "team_memory_bucket": "cricket_research_team",
        "input_family": "squad",
        "memory_present": True,
        "observed_at": GENERATED_AT - timedelta(hours=2),
        "evidence_count": d("3.000000"),
        "conflicting_evidence_count": d("0.000000"),
        "confidence_score": d("0.900000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchDomainCricketSignalMemoryQualityInput(**values)


def build_report(*rows: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_domain_cricket_signal_memory_quality_report(
        rows,
        config=cfg if cfg is not None else module.ResearchDomainCricketSignalMemoryQualityConfig(),
        generated_at=generated_at,
    )


def assert_no_public_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_float_or_int(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is Decimal:
        return
    if type(value) in (float, int):
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


def assert_payload_has_no_forbidden_public_surface(value: object) -> None:
    forbidden_fragments = (
        _join_parts("candidate"),
        _join_parts("market"),
        _join_parts("slug"),
        _join_parts("question"),
        _join_parts("url"),
        _join_parts("http"),
        _join_parts("source", "_text"),
        _join_parts("dsn"),
        _join_parts("table"),
        _join_parts("token"),
        _join_parts("wallet"),
        _join_parts("order"),
        _join_parts("trade"),
        _join_parts("auth"),
        _join_parts("network"),
        _join_parts("database"),
        _join_parts("position"),
        _join_parts("sizing"),
        _join_parts("recommend"),
        _join_parts("buy"),
        _join_parts("sell"),
        _join_parts("live"),
    )
    if type(value) is str:
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in forbidden_fragments)
            assert_payload_has_no_forbidden_public_surface(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_payload_has_no_forbidden_public_surface(item)


def test_cricket_memory_quality_flags_stale_conflicting_and_missing_inputs() -> None:
    module = api()

    report = build_report(
        memory_input(input_family="squad"),
        memory_input(
            input_family="pitch",
            observed_at=GENERATED_AT - timedelta(days=2),
            confidence_score=d("0.800000"),
        ),
        memory_input(
            input_family="weather",
            conflicting_evidence_count=d("2.000000"),
            confidence_score=d("0.860000"),
        ),
        memory_input(
            input_family="toss",
            memory_present=False,
            observed_at=None,
            evidence_count=d("0.000000"),
            confidence_score=d("0.000000"),
        ),
        memory_input(
            input_family="form_context",
            conflicting_evidence_count=d("1.000000"),
            confidence_score=d("0.830000"),
        ),
    )

    assert type(report) is module.ResearchDomainCricketSignalMemoryQualityReport
    assert is_dataclass(report)
    assert report.report_status == "block"
    assert report.input_count == d("5.000000")
    assert report.row_count == d("5.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("2.000000")
    assert report.block_count == d("2.000000")
    assert report.stale_count == d("1.000000")
    assert report.conflict_count == d("2.000000")
    assert report.missing_count == d("1.000000")
    assert report.average_quality_score == d("0.418000")
    assert report.squad_missing_count == d("0.000000")
    assert report.pitch_stale_count == d("1.000000")
    assert report.weather_conflict_count == d("1.000000")
    assert report.toss_missing_count == d("1.000000")
    assert report.form_context_conflict_count == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.input_family for row in report.rows) == (
        "weather",
        "toss",
        "pitch",
        "form_context",
        "squad",
    )
    assert tuple(row.public_status for row in report.rows) == (
        "block",
        "block",
        "watch",
        "watch",
        "pass",
    )

    weather, toss, pitch, form_context, squad = report.rows
    assert weather.quality_score == d("0.160000")
    assert weather.conflict_penalty_score == d("0.700000")
    assert weather.reason_codes == (
        "cricket_signal_memory_quality_conflict_block",
        "cricket_signal_memory_quality_memory_score_block",
        "cricket_signal_memory_quality_weather_conflicting",
    )
    assert toss.memory_age_seconds is None
    assert toss.reason_codes == (
        "cricket_signal_memory_quality_memory_score_block",
        "cricket_signal_memory_quality_toss_missing",
    )
    assert pitch.memory_age_seconds == d("172800.000000")
    assert pitch.quality_score == d("0.550000")
    assert pitch.reason_codes == (
        "cricket_signal_memory_quality_no_conflict",
        "cricket_signal_memory_quality_pitch_stale",
        "cricket_signal_memory_quality_watch",
    )
    assert form_context.quality_score == d("0.480000")
    assert form_context.reason_codes == (
        "cricket_signal_memory_quality_conflict_watch",
        "cricket_signal_memory_quality_form_context_conflicting",
        "cricket_signal_memory_quality_watch",
    )
    assert squad.quality_score == d("0.900000")
    assert squad.reason_codes == (
        "cricket_signal_memory_quality_fresh",
        "cricket_signal_memory_quality_no_conflict",
        "cricket_signal_memory_quality_pass",
    )
    assert report.reason_codes == tuple(item.reason_code for item in report.reason_code_counts)


def test_empty_report_blocks_forecast_handoff_with_digest() -> None:
    module = api()
    report = build_report()

    assert report.report_status == "block"
    assert report.input_count == d("0.000000")
    assert report.rows == ()
    assert report.average_quality_score == d("0.000000")
    assert report.reason_codes == ("cricket_signal_memory_quality_no_inputs",)
    assert report.reason_code_counts == (
        module.ResearchDomainCricketSignalMemoryQualityReasonCodeCount(
            reason_code="cricket_signal_memory_quality_no_inputs",
            count=d("1.000000"),
            input_ratio=d("0.000000"),
        ),
    )
    assert report.derived_validation_digest == (
        module.research_domain_cricket_signal_memory_quality_report_digest(report)
    )


def test_payload_serializes_decimal_strings_and_validates_sha256_digest() -> None:
    module = api()
    report = build_report(memory_input())

    payload = module.research_domain_cricket_signal_memory_quality_report_payload(report)
    payload_again = module.research_domain_cricket_signal_memory_quality_report_payload(
        report,
    )
    digest = module.research_domain_cricket_signal_memory_quality_report_digest(report)

    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()

    assert payload_again == payload
    assert report.payload == payload
    assert payload["derived_validation_digest"] == digest == expected_digest
    assert len(digest) == 64
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["average_quality_score"] == "0.900000"
    assert payload["rows"][0]["quality_score"] == "0.900000"
    assert_no_public_float_or_int(payload)
    assert_payload_has_no_forbidden_public_surface(payload)

    tampered = dict(payload)
    tampered["pass_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_domain_cricket_signal_memory_quality_report_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    cfg = module.ResearchDomainCricketSignalMemoryQualityConfig()
    sample_input = memory_input()
    report = build_report(sample_input)

    for item in (cfg, sample_input, *report.rows, *report.reason_code_counts, report):
        assert is_dataclass(item)
        assert item.__dataclass_params__.frozen is True
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    assert {report.report_status, *(row.public_status for row in report.rows)} <= {
        "pass",
        "watch",
        "block",
    }
    with pytest.raises(TypeError, match="Decimal"):
        memory_input(confidence_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="exactly"):
        memory_input(event_bucket=_StringSubclass("cricket_event_group_a"))
    with pytest.raises(TypeError, match="exactly"):
        memory_input(conflicting_evidence_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        memory_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        module.ResearchDomainCricketSignalMemoryQualityConfig(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        memory_input(readonly=False)


def test_input_validation_rejects_private_or_actionable_public_surfaces() -> None:
    unsafe_values = (
        _join_parts("raw_", "candidate", "_17"),
        _join_parts("market", "_123"),
        _join_parts("team", "_slug"),
        _join_parts("will", "_team", "_win", "_question"),
        _join_parts("https", "://example.test/path"),
        _join_parts("source", "_text"),
        _join_parts("dsn", "_analytics"),
        _join_parts("table", "_name"),
        _join_parts("to", "ken", "_abc"),
        _join_parts("wal", "let", "_field"),
        _join_parts("sub", "mit", "_order"),
        _join_parts("trade", "_surface"),
        _join_parts("size", "_edge"),
        _join_parts("rec", "ommend", "_yes"),
    )

    for value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public value"):
            memory_input(event_bucket=value)

    with pytest.raises(ValueError, match="input_family"):
        memory_input(input_family="injury")
    with pytest.raises(ValueError, match="observed_at"):
        memory_input(memory_present=True, observed_at=None)
    with pytest.raises(ValueError, match="evidence_count"):
        memory_input(memory_present=False, observed_at=None, evidence_count=d("1.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        build_report(memory_input(observed_at=GENERATED_AT + timedelta(seconds=1)))


def test_module_scope_is_pure_report_only_and_action_surface_free() -> None:
    module = api()
    module_source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(module_source)

    forbidden_import_roots = {
        "builtins",
        "io",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "send",
        "submit",
        "write",
    }
    forbidden_terms = (
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("order"),
        _join_parts("trade"),
        _join_parts("trading"),
        _join_parts("position"),
        _join_parts("buy"),
        _join_parts("sell"),
        _join_parts("rec", "ommend"),
    )

    imports: set[str] = set()
    calls: set[str] = set()
    attributes: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attributes.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert imports.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)
    assert attributes.isdisjoint(forbidden_calls)
    assert not float_constants
    assert not any(term in module_source.lower() for term in forbidden_terms)

    assert set(module.__all__) == {
        "DEFAULT_RESEARCH_DOMAIN_CRICKET_SIGNAL_MEMORY_QUALITY_CONFIG_VERSION",
        "ResearchDomainCricketSignalMemoryQualityConfig",
        "ResearchDomainCricketSignalMemoryQualityInput",
        "ResearchDomainCricketSignalMemoryQualityReasonCodeCount",
        "ResearchDomainCricketSignalMemoryQualityReport",
        "ResearchDomainCricketSignalMemoryQualityRow",
        "build_research_domain_cricket_signal_memory_quality_report",
        "research_domain_cricket_signal_memory_quality_report_digest",
        "research_domain_cricket_signal_memory_quality_report_payload",
        "validate_research_domain_cricket_signal_memory_quality_public_payload",
    }
