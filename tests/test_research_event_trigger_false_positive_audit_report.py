from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_trigger_false_positive_audit_report"


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def audit_input(**overrides: object) -> Any:
    module = api()
    values = {
        "aggregate_catalyst_quality_score": d("0.900000"),
        "source_reliability_score": d("0.880000"),
        "contradiction_count": d("0.000000"),
        "historical_trigger_precision": d("0.840000"),
        "rule_clarity_score": d("0.860000"),
    }
    values.update(overrides)
    return module.ResearchEventTriggerFalsePositiveAuditInput(**values)


def audit(**overrides: object) -> Any:
    module = api()
    return module.build_research_event_trigger_false_positive_audit_report(
        audit_input(**overrides),
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool or isinstance(value, (str, tuple)):
            continue
        assert type(value) is Decimal, field.name


def assert_payload_has_no_runtime_numbers(value: object) -> None:
    if type(value) is bool:
        return
    assert type(value) is not float
    assert type(value) is not int
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for child in value.values():
            assert_payload_has_no_runtime_numbers(child)
    elif isinstance(value, list):
        for child in value:
            assert_payload_has_no_runtime_numbers(child)


def assert_no_raw_identifier_surface(value: object) -> None:
    unsafe_fragments = (
        "eventid",
        "marketid",
        "sourceid",
        "eventslug",
        "marketslug",
        "sourceurl",
        "conditionid",
        "clobtoken",
        "url",
        "slug",
        "title",
    )

    def normalized(text: str) -> str:
        return "".join(character for character in text.lower() if character.isalnum())

    if isinstance(value, dict):
        for key, child in value.items():
            key_text = normalized(key)
            assert not any(fragment in key_text for fragment in unsafe_fragments), key
            assert_no_raw_identifier_surface(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_raw_identifier_surface(child)
    elif type(value) is str:
        text = normalized(value)
        assert not any(fragment in text for fragment in unsafe_fragments), value


def test_pass_report_is_frozen_public_safe_and_report_only() -> None:
    module = api()

    result = audit()

    assert module.STATUSES == ("pass", "watch", "block")
    assert isinstance(result, module.ResearchEventTriggerFalsePositiveAuditReport)
    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen
    assert result.status == "pass"
    assert result.false_positive_risk_score == d("0.108000")
    assert result.reason_codes == ("event_trigger_false_positive_audit_pass",)
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_public_numeric_fields_are_decimal(result)

    payload = module.research_event_trigger_false_positive_audit_report_payload(result)
    assert result.payload == payload
    assert_no_raw_identifier_surface(payload)


def test_watch_and_block_statuses_use_all_quality_dimensions() -> None:
    watch = audit(
        aggregate_catalyst_quality_score=d("0.640000"),
        source_reliability_score=d("0.680000"),
        contradiction_count=d("2.000000"),
        historical_trigger_precision=d("0.660000"),
        rule_clarity_score=d("0.620000"),
    )

    assert watch.status == "watch"
    assert watch.false_positive_risk_score == d("0.355000")
    assert watch.reason_codes == (
        "false_positive_risk_watch",
        "aggregate_catalyst_quality_weak",
        "source_reliability_weak",
        "contradiction_count_elevated",
        "historical_trigger_precision_weak",
        "rule_clarity_weak",
    )

    blocked = audit(
        aggregate_catalyst_quality_score=d("0.350000"),
        source_reliability_score=d("0.420000"),
        contradiction_count=d("5.000000"),
        historical_trigger_precision=d("0.450000"),
        rule_clarity_score=d("0.400000"),
    )

    assert blocked.status == "block"
    assert blocked.false_positive_risk_score == d("0.657500")
    assert blocked.reason_codes == (
        "false_positive_risk_block",
        "aggregate_catalyst_quality_low",
        "source_reliability_low",
        "contradiction_count_high",
        "historical_trigger_precision_low",
        "rule_clarity_low",
    )


def test_payload_serializes_decimal_strings_and_digest_is_deterministic() -> None:
    module = api()
    result = audit()

    payload = module.research_event_trigger_false_positive_audit_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["aggregate_catalyst_quality_score"] == "0.900000"
    assert payload["source_reliability_score"] == "0.880000"
    assert payload["contradiction_count"] == "0.000000"
    assert payload["historical_trigger_precision"] == "0.840000"
    assert payload["rule_clarity_score"] == "0.860000"
    assert payload["false_positive_risk_score"] == "0.108000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] in encoded
    assert_payload_has_no_runtime_numbers(payload)
    module.validate_research_event_trigger_false_positive_audit_public_payload(payload)

    assert audit().derived_validation_digest == result.derived_validation_digest
    changed = audit(rule_clarity_score=d("0.850000"))
    assert changed.derived_validation_digest != result.derived_validation_digest

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest does not match"):
        module.validate_research_event_trigger_false_positive_audit_public_payload(tampered)

    downgraded_flags = dict(payload)
    downgraded_flags["readonly"] = False
    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.validate_research_event_trigger_false_positive_audit_public_payload(
            downgraded_flags,
        )


def test_validation_rejects_non_decimal_nonfinite_granular_counts_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="aggregate_catalyst_quality_score must be exactly Decimal"):
        audit_input(aggregate_catalyst_quality_score=1)
    with pytest.raises(ValueError, match="source_reliability_score must be exactly Decimal"):
        audit_input(source_reliability_score=_DecimalSubclass("0.880000"))
    with pytest.raises(ValueError, match="historical_trigger_precision must be finite"):
        audit_input(historical_trigger_precision=d("NaN"))
    with pytest.raises(ValueError, match="rule_clarity_score precision is too granular"):
        audit_input(rule_clarity_score=d("0.8600001"))
    with pytest.raises(ValueError, match="source_reliability_score must be between 0 and 1"):
        audit_input(source_reliability_score=d("1.000001"))
    with pytest.raises(ValueError, match="contradiction_count must be a whole Decimal"):
        audit_input(contradiction_count=d("1.500000"))
    with pytest.raises(ValueError, match="contradiction_count must be nonnegative"):
        audit_input(contradiction_count=d("-1.000000"))
    with pytest.raises(ValueError, match="input paper_only must be True"):
        audit_input(paper_only=False)

    with pytest.raises(
        ValueError,
        match="audit_input must be a ResearchEventTriggerFalsePositiveAuditInput",
    ):
        module.build_research_event_trigger_false_positive_audit_report(object())

    result = audit()
    with pytest.raises(FrozenInstanceError):
        result.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status must match false-positive risk inputs"):
        module.ResearchEventTriggerFalsePositiveAuditReport(
            **{**result.__dict__, "status": "block", "derived_validation_digest": ""},
        )
    with pytest.raises(ValueError, match="reason_codes must match false-positive risk inputs"):
        module.ResearchEventTriggerFalsePositiveAuditReport(
            **{
                **result.__dict__,
                "reason_codes": ("false_positive_risk_watch",),
                "derived_validation_digest": "",
            },
        )
    with pytest.raises(ValueError, match="derived_validation_digest does not match"):
        module.ResearchEventTriggerFalsePositiveAuditReport(
            **{**result.__dict__, "derived_validation_digest": "0" * 64},
        )


def test_module_is_report_only_without_identifier_io_execution_or_advisory_surface() -> None:
    module = api()
    source = Path(module.__file__).read_text()
    lowered = source.lower()
    prohibited_terms = (
        "api_key",
        "auth",
        "boto3",
        "database",
        "execute",
        "execution",
        "httpx",
        "mysql",
        "network",
        "order",
        "position_size",
        "private_key",
        "psycopg",
        "recommend",
        "requests",
        "secret",
        "sizing",
        "socket",
        "sqlalchemy",
        "sqlite",
        "subprocess",
        "trade",
        "urllib",
        "wallet",
    )
    for term in prohibited_terms:
        assert term not in lowered, term
    for public_name in module.__all__:
        normalized_name = public_name.lower()
        for term in prohibited_terms:
            assert term not in normalized_name, public_name

    payload = module.research_event_trigger_false_positive_audit_report_payload(audit())
    assert_no_raw_identifier_surface(payload)
