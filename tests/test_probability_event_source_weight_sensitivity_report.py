from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json

import pytest


GENERATED_AT = datetime(2026, 7, 11, 14, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _module():
    return importlib.import_module(
        "polymarket_alpha_lab.probability_event_source_weight_sensitivity_report",
    )


def _build(
    *,
    official_source_weight: Decimal = d("0.450000"),
    independent_source_weight: Decimal = d("0.350000"),
    specialist_memory_weight: Decimal = d("0.200000"),
    contradiction_penalty: Decimal = d("0.100000"),
    source_quality_status: str = "pass",
    generated_at: datetime = GENERATED_AT,
    config=None,
):
    module = _module()
    return module.build_probability_event_source_weight_sensitivity_report(
        official_source_weight=official_source_weight,
        independent_source_weight=independent_source_weight,
        specialist_memory_weight=specialist_memory_weight,
        contradiction_penalty=contradiction_penalty,
        source_quality_status=source_quality_status,
        generated_at=generated_at,
        config=config
        or module.ProbabilityEventSourceWeightSensitivityConfig(
            config_version="probability-event-source-weight-sensitivity-v0",
        ),
    )


def test_balanced_source_weights_pass_without_auto_adjustment() -> None:
    report = _build()

    module = _module()
    assert type(report) is module.ProbabilityEventSourceWeightSensitivityReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "probability-event-source-weight-sensitivity-v0"
    assert report.sensitivity_status == "pass"
    assert report.status == "pass"
    assert report.weight_imbalance_reason_codes == ()
    assert report.manual_next_step == "continue_paper_review_without_weight_change"
    assert report.total_source_weight == d("1.000000")
    assert report.max_source_weight == d("0.450000")
    assert report.min_source_weight == d("0.200000")
    assert report.weight_spread == d("0.250000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.payload
    assert payload == module.probability_event_source_weight_sensitivity_report_payload(report)
    assert payload["official_source_weight"] == "0.450000"
    assert payload["weight_imbalance_reason_codes"] == []
    assert payload["manual_next_step"] == "continue_paper_review_without_weight_change"
    json.dumps(payload, sort_keys=True)
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)


def test_official_dominance_and_low_independent_support_trigger_watch() -> None:
    report = _build(
        official_source_weight=d("0.760000"),
        independent_source_weight=d("0.140000"),
        specialist_memory_weight=d("0.100000"),
        contradiction_penalty=d("0.200000"),
        source_quality_status="watch",
    )

    assert report.sensitivity_status == "watch"
    assert report.weight_imbalance_reason_codes == (
        "official_source_overweight",
        "independent_source_underweight",
        "source_quality_watch",
    )
    assert report.manual_next_step == "manually_review_official_source_dependency"
    assert report.total_source_weight == d("1.000000")
    assert report.weight_spread == d("0.660000")


def test_contradiction_penalty_and_blocked_quality_trigger_block_without_mutation() -> None:
    report = _build(
        official_source_weight=d("0.300000"),
        independent_source_weight=d("0.300000"),
        specialist_memory_weight=d("0.400000"),
        contradiction_penalty=d("0.900000"),
        source_quality_status="blocked",
    )

    assert report.sensitivity_status == "block"
    assert report.weight_imbalance_reason_codes == (
        "contradiction_penalty_high",
        "source_quality_blocked",
    )
    assert report.manual_next_step == "pause_paper_event_and_escalate_source_review"
    assert report.official_source_weight == d("0.300000")
    assert report.independent_source_weight == d("0.300000")
    assert report.specialist_memory_weight == d("0.400000")


def test_specialist_memory_overweight_is_watch_and_reason_codes_are_deterministic() -> None:
    first = _build(
        official_source_weight=d("0.180000"),
        independent_source_weight=d("0.220000"),
        specialist_memory_weight=d("0.600000"),
        contradiction_penalty=d("0.500000"),
        source_quality_status="pass",
    )
    second = _build(
        specialist_memory_weight=d("0.600000"),
        independent_source_weight=d("0.220000"),
        official_source_weight=d("0.180000"),
        contradiction_penalty=d("0.500000"),
        source_quality_status="pass",
    )

    assert first.sensitivity_status == "watch"
    assert first.weight_imbalance_reason_codes == (
        "official_source_underweight",
        "specialist_memory_overweight",
        "weight_spread_high",
        "contradiction_penalty_watch",
    )
    assert first.manual_next_step == "manually_review_specialist_memory_dependency"
    assert first.payload == second.payload
    encoded = json.dumps(first.payload, sort_keys=True)
    assert "wallet" not in encoded
    assert "order" not in encoded
    assert "live" not in encoded
    assert "market_id" not in encoded


def test_validation_enforces_decimal_only_flags_datetime_and_public_surface() -> None:
    module = _module()
    report = _build(
        generated_at=datetime(2026, 7, 11, 10, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    with pytest.raises(FrozenInstanceError):
        report.sensitivity_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="official_source_weight"):
        _build(official_source_weight="0.450000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="official_source_weight"):
        _build(official_source_weight=d("1.100000"))
    with pytest.raises(ValueError, match="total_source_weight"):
        _build(
            official_source_weight=d("0.500000"),
            independent_source_weight=d("0.300000"),
            specialist_memory_weight=d("0.300000"),
        )
    with pytest.raises(ValueError, match="source_quality_status"):
        _build(source_quality_status="ready")
    with pytest.raises(ValueError, match="generated_at"):
        _build(generated_at=datetime(2026, 7, 11, 14, 0))
    with pytest.raises(ValueError, match="paper_only"):
        module.ProbabilityEventSourceWeightSensitivityConfig(
            config_version="probability-event-source-weight-sensitivity-v0",
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="config"):
        _build(config=object())

    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(
            fragment in lowered
            for fragment in ("wallet", "order", "live", "auth", "market_id")
        )


def test_owned_module_has_no_runtime_persistence_or_trading_surfaces() -> None:
    module = _module()
    forbidden_names = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "web3",
        "ccxt",
    )

    for forbidden_name in forbidden_names:
        assert not hasattr(module, forbidden_name)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field_name in value.__dataclass_fields__:
            _assert_no_non_decimal_public_numbers(getattr(value, field_name))
