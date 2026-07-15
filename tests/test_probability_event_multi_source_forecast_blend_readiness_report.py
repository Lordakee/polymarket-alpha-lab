from __future__ import annotations

import ast
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import get_type_hints

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "probability_event_multi_source_forecast_blend_readiness_report"
)
SOURCE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_multi_source_forecast_blend_readiness_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return importlib.import_module(MODULE_NAME)


def _input(**overrides: object):
    api = _api()
    values = {
        "model_forecast_probability": d("0.620000"),
        "specialist_forecast_probability": d("0.600000"),
        "market_implied_probability": d("0.580000"),
        "source_quality_probability": d("0.640000"),
        "blend_disagreement_probability": d("0.040000"),
    }
    values.update(overrides)
    return api.ProbabilityEventMultiSourceForecastBlendReadinessInput(**values)


def test_ready_report_blends_multi_source_forecasts_with_digest_and_payload() -> None:
    api = _api()
    report = api.build_probability_event_multi_source_forecast_blend_readiness_report(
        _input(),
    )

    assert type(report) is api.ProbabilityEventMultiSourceForecastBlendReadinessReport
    assert is_dataclass(report)
    assert report.blend_status == "ready"
    assert report.blended_probability == d("0.610000")
    assert report.reason_codes == (
        "multi_source_forecast_blend_ready",
    )
    assert report.manual_next_step == (
        "Record blended probability in the manual review packet; no programmatic "
        "execution is permitted."
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    json.dumps(payload)
    assert payload == {
        "config_version": (
            "probability-event-multi-source-forecast-blend-readiness-v0"
        ),
        "model_forecast_probability": "0.620000",
        "specialist_forecast_probability": "0.600000",
        "market_implied_probability": "0.580000",
        "source_quality_probability": "0.640000",
        "blend_disagreement_probability": "0.040000",
        "blend_status": "ready",
        "blended_probability": "0.610000",
        "reason_codes": ["multi_source_forecast_blend_ready"],
        "manual_next_step": report.manual_next_step,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    assert report.payload_digest == api.probability_event_multi_source_forecast_blend_readiness_report_digest(report)
    assert len(report.payload_digest) == 64
    assert report.payload_digest == api.probability_event_multi_source_forecast_blend_readiness_report_digest(report)


def test_watch_and_blocked_statuses_are_reasoned_from_quality_and_disagreement() -> None:
    api = _api()

    watch = api.build_probability_event_multi_source_forecast_blend_readiness_report(
        _input(
            source_quality_probability=d("0.540000"),
            blend_disagreement_probability=d("0.110000"),
        ),
    )
    assert watch.blend_status == "watch"
    assert watch.blended_probability == d("0.590000")
    assert watch.reason_codes == (
        "multi_source_forecast_quality_watch",
        "multi_source_forecast_disagreement_watch",
    )
    assert watch.manual_next_step == (
        "Review source quality and forecast disagreement before using the blend "
        "in paper-only decision support."
    )

    blocked = api.build_probability_event_multi_source_forecast_blend_readiness_report(
        _input(
            model_forecast_probability=d("0.800000"),
            specialist_forecast_probability=d("0.420000"),
            market_implied_probability=d("0.390000"),
            source_quality_probability=d("0.400000"),
            blend_disagreement_probability=d("0.260000"),
        ),
    )
    assert blocked.blend_status == "blocked"
    assert blocked.blended_probability == d("0.524000")
    assert blocked.reason_codes == (
        "multi_source_forecast_quality_blocked",
        "multi_source_forecast_disagreement_blocked",
    )
    assert blocked.manual_next_step == (
        "Escalate to manual review and gather corroborating source evidence; do "
        "not use this blend for execution."
    )


def test_payload_validation_rejects_schema_drift_and_unsafe_surfaces() -> None:
    api = _api()
    report = api.build_probability_event_multi_source_forecast_blend_readiness_report(
        _input(),
    )

    assert (
        api.validate_probability_event_multi_source_forecast_blend_readiness_public_payload(
            report.public_payload,
        )
        == report.public_payload
    )

    tampered = dict(report.public_payload)
    tampered["payload_digest"] = report.payload_digest
    with pytest.raises(ValueError, match="canonical blend readiness schema"):
        api.validate_probability_event_multi_source_forecast_blend_readiness_public_payload(
            tampered,
        )

    bad_reason = dict(report.public_payload)
    bad_reason["reason_codes"] = ["multi_source_forecast_disagreement_blocked"]
    with pytest.raises(ValueError, match="reason_codes must match forecast inputs"):
        api.validate_probability_event_multi_source_forecast_blend_readiness_public_payload(
            bad_reason,
        )

    unsafe = dict(report.public_payload)
    unsafe["wallet"] = "0xabc"
    with pytest.raises(ValueError, match="canonical blend readiness schema"):
        api.validate_probability_event_multi_source_forecast_blend_readiness_public_payload(
            unsafe,
        )


def test_dataclasses_reject_floats_out_of_range_false_flags_subclasses_and_mutation() -> None:
    api = _api()

    assert getattr(
        api.ProbabilityEventMultiSourceForecastBlendReadinessInput,
        "__dataclass_params__",
    ).frozen is True
    assert getattr(
        api.ProbabilityEventMultiSourceForecastBlendReadinessReport,
        "__dataclass_params__",
    ).frozen is True

    with pytest.raises(ValueError, match="model_forecast_probability must be a Decimal"):
        _input(model_forecast_probability=0.62)

    with pytest.raises(ValueError, match="source_quality_probability must be between"):
        _input(source_quality_probability=d("1.010000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(_input(), paper_only=False)

    input_value = _input()
    with pytest.raises(FrozenInstanceError):
        input_value.model_forecast_probability = d("0.500000")

    with pytest.raises(
        ValueError,
        match=(
            "forecast_input must be a "
            "ProbabilityEventMultiSourceForecastBlendReadinessInput"
        ),
    ):
        api.build_probability_event_multi_source_forecast_blend_readiness_report(
            object(),
        )

    with pytest.raises(TypeError, match="does not support subclassing"):
        class InputSubclass(api.ProbabilityEventMultiSourceForecastBlendReadinessInput):
            pass


def test_public_numeric_annotations_are_decimal_and_module_is_readonly() -> None:
    api = _api()
    numeric_fragments = ("probability",)

    for cls_name in (
        "ProbabilityEventMultiSourceForecastBlendReadinessInput",
        "ProbabilityEventMultiSourceForecastBlendReadinessReport",
    ):
        cls = getattr(api, cls_name)
        assert is_dataclass(cls)
        assert getattr(cls, "__dataclass_params__").frozen is True
        hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if any(fragment in field.name for fragment in numeric_fragments):
                assert hints[field.name] is Decimal, (
                    cls_name,
                    field.name,
                    hints[field.name],
                )

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
        "sign",
        "signature",
        "trade",
        "order",
        "execute",
        "auto",
        "open(",
        "print(",
    )
    for token in forbidden_text:
        assert token not in lowered, token

    allowed_import_prefixes = (
        "from __future__",
        "from dataclasses",
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

    for name, value in inspect.getmembers(api):
        if name.startswith("_"):
            continue
        if isinstance(value, float):
            raise AssertionError(name)
