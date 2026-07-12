from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 12, 8, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _module():
    return importlib.import_module(
        "polymarket_alpha_lab.probability_event_source_family_redundancy_report",
    )


def _build(
    *,
    source_family_count: Decimal = d("4.000000"),
    official_family_count: Decimal = d("1.000000"),
    independent_family_count: Decimal = d("3.000000"),
    single_source_dependency_count: Decimal = d("0.000000"),
    contradiction_count: Decimal = d("0.000000"),
    generated_at: datetime = GENERATED_AT,
    config=None,
):
    module = _module()
    return module.build_probability_event_source_family_redundancy_report(
        source_family_count=source_family_count,
        official_family_count=official_family_count,
        independent_family_count=independent_family_count,
        single_source_dependency_count=single_source_dependency_count,
        contradiction_count=contradiction_count,
        generated_at=generated_at,
        config=config
        or module.ProbabilityEventSourceFamilyRedundancyConfig(
            config_version="probability-event-source-family-redundancy-v0",
        ),
    )


def test_balanced_source_family_mix_passes_with_report_only_next_step() -> None:
    report = _build()
    module = _module()

    assert type(report) is module.ProbabilityEventSourceFamilyRedundancyReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "probability-event-source-family-redundancy-v0"
    assert report.redundancy_status == "pass"
    assert report.status == "pass"
    assert report.reason_codes == ("source_family_redundancy_pass",)
    assert report.manual_next_step == "continue_paper_review_with_current_source_mix"
    assert report.source_family_count == d("4.000000")
    assert report.official_family_count == d("1.000000")
    assert report.independent_family_count == d("3.000000")
    assert report.single_source_dependency_count == d("0.000000")
    assert report.contradiction_count == d("0.000000")
    assert report.independent_family_ratio == d("0.750000")
    assert report.official_family_ratio == d("0.250000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.payload
    assert payload == module.probability_event_source_family_redundancy_report_payload(
        report,
    )
    assert payload["source_family_count"] == "4.000000"
    assert payload["independent_family_ratio"] == "0.750000"
    assert payload["reason_codes"] == ["source_family_redundancy_pass"]
    assert payload["manual_next_step"] == "continue_paper_review_with_current_source_mix"
    json.dumps(payload, sort_keys=True)
    _assert_no_decimal_objects(payload)
    _assert_no_non_decimal_public_numbers(report)


def test_low_independent_redundancy_and_single_source_dependency_trigger_watch() -> None:
    report = _build(
        source_family_count=d("3.000000"),
        official_family_count=d("2.000000"),
        independent_family_count=d("1.000000"),
        single_source_dependency_count=d("1.000000"),
        contradiction_count=d("0.000000"),
    )

    assert report.redundancy_status == "watch"
    assert report.reason_codes == (
        "independent_family_under_minimum",
        "official_family_concentration",
        "single_source_dependency_present",
    )
    assert report.manual_next_step == "manually_add_independent_source_family"
    assert report.independent_family_ratio == d("0.333333")
    assert report.official_family_ratio == d("0.666667")


def test_contradictions_or_too_few_families_block_without_actions() -> None:
    contradiction_report = _build(
        source_family_count=d("4.000000"),
        official_family_count=d("1.000000"),
        independent_family_count=d("3.000000"),
        single_source_dependency_count=d("0.000000"),
        contradiction_count=d("1.000000"),
    )
    insufficient_report = _build(
        source_family_count=d("1.000000"),
        official_family_count=d("1.000000"),
        independent_family_count=d("0.000000"),
        single_source_dependency_count=d("1.000000"),
        contradiction_count=d("0.000000"),
    )

    assert contradiction_report.redundancy_status == "block"
    assert contradiction_report.reason_codes == ("source_family_contradiction_present",)
    assert contradiction_report.manual_next_step == (
        "pause_paper_event_and_resolve_source_contradictions"
    )
    assert insufficient_report.redundancy_status == "block"
    assert insufficient_report.reason_codes == (
        "source_family_count_below_minimum",
        "independent_family_under_minimum",
        "official_family_concentration",
        "single_source_dependency_present",
    )
    assert insufficient_report.manual_next_step == (
        "pause_paper_event_and_collect_more_source_families"
    )


def test_validation_enforces_decimal_only_flags_datetime_and_consistency() -> None:
    module = _module()
    report = _build(
        generated_at=datetime(2026, 7, 12, 4, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    with pytest.raises(FrozenInstanceError):
        report.redundancy_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_family_count"):
        _build(source_family_count="4.000000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_family_count"):
        _build(source_family_count=d("4.0000001"))
    with pytest.raises(ValueError, match="source_family_count"):
        _build(source_family_count=d("-1.000000"))
    with pytest.raises(ValueError, match="official_family_count"):
        _build(source_family_count=d("2.000000"), official_family_count=d("3.000000"))
    with pytest.raises(ValueError, match="independent_family_count"):
        _build(source_family_count=d("2.000000"), independent_family_count=d("3.000000"))
    with pytest.raises(ValueError, match="single_source_dependency_count"):
        _build(
            source_family_count=d("2.000000"),
            independent_family_count=d("2.000000"),
            single_source_dependency_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _build(generated_at=datetime(2026, 7, 12, 8, 0))
    with pytest.raises(ValueError, match="paper_only"):
        module.ProbabilityEventSourceFamilyRedundancyConfig(
            config_version="probability-event-source-family-redundancy-v0",
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("source_family_redundancy_pass", "x"))
    with pytest.raises(ValueError, match="manual_next_step"):
        replace(report, manual_next_step="place_order")
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
