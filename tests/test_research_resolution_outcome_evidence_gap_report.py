from __future__ import annotations

import ast
import importlib.util
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_resolution_outcome_evidence_gap_report"
SOURCE = Path("src/polymarket_alpha_lab/research_resolution_outcome_evidence_gap_report.py")
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return import_module(MODULE_NAME)


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_RESEARCH_RESOLUTION_OUTCOME_EVIDENCE_GAP_REPORT_CONFIG_VERSION
        ),
        "fresh_source_age_seconds": d("3600.000000"),
        "stale_source_age_seconds": d("7200.000000"),
        "required_source_class_count": d("3.000000"),
        "minimum_source_class_count": d("2.000000"),
        "contradiction_watch_threshold": d("0.250000"),
        "contradiction_block_threshold": d("0.500000"),
        "oracle_clarity_watch_threshold": d("0.700000"),
        "oracle_clarity_block_threshold": d("0.450000"),
        "near_deadline_seconds": d("86400.000000"),
        "imminent_deadline_seconds": d("3600.000000"),
    }
    values.update(overrides)
    return api.ResearchResolutionOutcomeEvidenceGapConfig(**values)


def _inputs(**overrides: object) -> object:
    api = _api()
    values = {
        "resolution_event_count": d("4.000000"),
        "aggregate_source_age_seconds": d("1200.000000"),
        "source_class_count": d("3.000000"),
        "contradiction_pressure": d("0.050000"),
        "oracle_clarity_score": d("0.900000"),
        "seconds_to_resolution_deadline": d("259200.000000"),
    }
    values.update(overrides)
    return api.ResearchResolutionOutcomeEvidenceGapInputs(**values)


def _report(**input_overrides: object) -> object:
    api = _api()
    return api.build_research_resolution_outcome_evidence_gap_report(
        _inputs(**input_overrides),
        config=_config(),
        generated_at=GENERATED_AT,
    )


def test_report_summarizes_evidence_gap_drivers_and_digest() -> None:
    api = _api()
    report = _report(
        aggregate_source_age_seconds=d("8100.000000"),
        source_class_count=d("2.000000"),
        contradiction_pressure=d("0.620000"),
        oracle_clarity_score=d("0.380000"),
        seconds_to_resolution_deadline=d("2700.000000"),
    )

    assert type(report) is api.ResearchResolutionOutcomeEvidenceGapReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.report_status == "block"
    assert report.reason_codes == (
        "resolution_outcome_evidence_gap_block",
        "aggregate_source_age_block",
        "source_class_diversity_watch",
        "contradiction_pressure_block",
        "oracle_clarity_block",
        "resolution_deadline_imminent",
    )
    assert report.resolution_event_count == d("4.000000")
    assert report.aggregate_source_age_seconds == d("8100.000000")
    assert report.source_class_count == d("2.000000")
    assert report.required_source_class_count == d("3.000000")
    assert report.source_class_gap_count == d("1.000000")
    assert report.contradiction_pressure == d("0.620000")
    assert report.oracle_clarity_score == d("0.380000")
    assert report.seconds_to_resolution_deadline == d("2700.000000")
    assert report.source_age_pressure == d("1.000000")
    assert report.source_class_gap_ratio == d("0.333333")
    assert report.oracle_ambiguity_pressure == d("0.620000")
    assert report.deadline_proximity_pressure == d("0.968750")
    assert report.evidence_gap_score == d("0.708417")
    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    rebuilt = api.build_research_resolution_outcome_evidence_gap_report(
        _inputs(
            aggregate_source_age_seconds=d("8100.000000"),
            source_class_count=d("2.000000"),
            contradiction_pressure=d("0.620000"),
            oracle_clarity_score=d("0.380000"),
            seconds_to_resolution_deadline=d("2700.000000"),
        ),
        config=_config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    assert rebuilt.derived_validation_digest == report.derived_validation_digest
    assert json.dumps(
        api.research_resolution_outcome_evidence_gap_report_payload(report),
        allow_nan=False,
        sort_keys=True,
    ) == json.dumps(
        api.research_resolution_outcome_evidence_gap_report_payload(rebuilt),
        allow_nan=False,
        sort_keys=True,
    )


def test_statuses_are_exactly_pass_watch_block() -> None:
    api = _api()

    assert api.RESOLUTION_OUTCOME_EVIDENCE_GAP_STATUSES == ("pass", "watch", "block")
    assert _report().report_status == "pass"
    assert _report(
        aggregate_source_age_seconds=d("5400.000000"),
        source_class_count=d("3.000000"),
        contradiction_pressure=d("0.260000"),
        oracle_clarity_score=d("0.650000"),
        seconds_to_resolution_deadline=d("7200.000000"),
    ).report_status == "watch"
    assert _report(
        source_class_count=d("1.000000"),
        contradiction_pressure=d("0.100000"),
    ).report_status == "block"


def test_payload_is_public_safe_json_ready_and_tamper_evident() -> None:
    api = _api()
    report = _report(
        aggregate_source_age_seconds=d("5400.000000"),
        source_class_count=d("2.000000"),
        contradiction_pressure=d("0.300000"),
        oracle_clarity_score=d("0.680000"),
        seconds_to_resolution_deadline=d("7200.000000"),
    )

    payload = api.research_resolution_outcome_evidence_gap_report_payload(report)
    payload_text = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["report_status"] == "watch"
    assert payload["aggregate_source_age_seconds"] == "5400.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert ".0," not in repr(payload)
    for token in (
        "http",
        "://",
        "source_url",
        "source_text",
        "source_reference",
        "source_ref",
        "market_id",
        "market_slug",
        "condition_id",
        "question",
        "wallet",
        "account",
        "order",
        "trade",
        "recommend",
        "sizing",
    ):
        assert token not in payload_text.lower(), token

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_dataclasses_reject_non_decimal_inputs_false_flags_subclasses_and_mutation() -> None:
    api = _api()

    with pytest.raises(ValueError, match="aggregate_source_age_seconds must be a Decimal"):
        _inputs(aggregate_source_age_seconds=3600.0)

    with pytest.raises(ValueError, match="resolution_event_count must be a Decimal"):
        _inputs(resolution_event_count=4)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_research_resolution_outcome_evidence_gap_report(
            _inputs(),
            config=_config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )

    inputs = _inputs()
    with pytest.raises(FrozenInstanceError):
        inputs.source_class_count = d("4.000000")

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(inputs, paper_only=False)

    with pytest.raises(ValueError, match="config must be a ResearchResolutionOutcomeEvidenceGapConfig"):
        api.build_research_resolution_outcome_evidence_gap_report(
            inputs,
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ConfigSubclass(api.ResearchResolutionOutcomeEvidenceGapConfig):
            pass


def test_public_numeric_annotations_are_decimal_and_module_scope_is_side_effect_free() -> None:
    api = _api()
    numeric_fragments = (
        "count",
        "ratio",
        "seconds",
        "pressure",
        "score",
        "threshold",
    )

    for cls_name in (
        "ResearchResolutionOutcomeEvidenceGapConfig",
        "ResearchResolutionOutcomeEvidenceGapInputs",
        "ResearchResolutionOutcomeEvidenceGapReport",
    ):
        cls = getattr(api, cls_name)
        assert is_dataclass(cls)
        assert getattr(cls, "__dataclass_params__").frozen is True
        hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "config_version",
                "report_status",
                "reason_codes",
                "generated_at",
                "derived_validation_digest",
            }:
                continue
            if any(fragment in field.name for fragment in numeric_fragments):
                assert hints[field.name] is Decimal, (cls_name, field.name, hints[field.name])

    text = SOURCE.read_text(encoding="utf-8")
    lowered = text.lower()
    forbidden_text = (
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "private_key",
        "wallet",
        "account",
        "order",
        "trade",
        "execution",
        "recommend",
        "sizing",
        "open(",
        "print(",
    )
    for token in forbidden_text:
        assert token not in lowered, token

    allowed_import_prefixes = (
        "from __future__",
        "from dataclasses",
        "from datetime",
        "from decimal",
        "from hashlib",
        "from typing",
        "import json",
        "from polymarket_alpha_lab.team_paper_guard",
    )
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert any(
                stripped.startswith(prefix) for prefix in allowed_import_prefixes
            ), stripped

    tree = ast.parse(text)
    forbidden_calls = {"open", "print", "exec", "eval", "compile"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls

    assert importlib.util.find_spec(MODULE_NAME) is not None
    for name, value in inspect.getmembers(api):
        if name.startswith("_"):
            continue
        if isinstance(value, float):
            raise AssertionError(name)
