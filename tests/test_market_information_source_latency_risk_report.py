from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.market_information_source_latency_risk_report"
)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def assert_no_numeric_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_objects(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_numeric_objects(item)
        return
    assert type(value) not in (float, int)


def build_report(
    *,
    official_source_latency_ms: Decimal = d("1200.000000"),
    alternative_source_latency_ms: Decimal = d("900.000000"),
    capture_age_hours: Decimal = d("0.500000"),
    market_move_probability: Decimal = d("0.200000"),
    max_latency_ms: Decimal = d("2000.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.build_market_information_source_latency_risk_report(
        official_source_latency_ms=official_source_latency_ms,
        alternative_source_latency_ms=alternative_source_latency_ms,
        capture_age_hours=capture_age_hours,
        market_move_probability=market_move_probability,
        max_latency_ms=max_latency_ms,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_builds_pass_latency_risk_report_with_public_payload_and_digest() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.MarketInformationSourceLatencyRiskReport
    assert is_dataclass(report)
    assert report.latency_status == "pass"
    assert report.reason_codes == ("information_source_latency_within_limit",)
    assert report.manual_next_step == "continue_manual_review"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == module.market_information_source_latency_risk_report_to_public_payload(
        report,
    )
    assert payload["official_source_latency_ms"] == "1200.000000"
    assert payload["alternative_source_latency_ms"] == "900.000000"
    assert payload["capture_age_hours"] == "0.500000"
    assert payload["market_move_probability"] == "0.200000"
    assert payload["max_latency_ms"] == "2000.000000"
    assert payload["latency_status"] == "pass"
    assert payload["reason_codes"] == ["information_source_latency_within_limit"]
    assert payload["manual_next_step"] == "continue_manual_review"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(report.payload_digest) == 64
    int(report.payload_digest, 16)
    assert payload["payload_digest"] == report.payload_digest
    assert (
        module.market_information_source_latency_risk_report_digest(report)
        == report.payload_digest
    )
    assert module.validate_market_information_source_latency_risk_report_payload(payload)
    assert_no_numeric_objects(payload)
    json.dumps(payload, sort_keys=True)


def test_latency_status_reason_codes_and_manual_next_step_are_deterministic() -> None:
    watch_report = build_report(
        official_source_latency_ms=d("2100.000000"),
        alternative_source_latency_ms=d("1900.000000"),
        capture_age_hours=d("1.000000"),
        market_move_probability=d("0.300000"),
        max_latency_ms=d("2000.000000"),
    )
    assert watch_report.latency_status == "watch"
    assert watch_report.reason_codes == (
        "official_source_latency_above_limit",
    )
    assert watch_report.manual_next_step == "manually_recheck_public_sources"

    block_report = build_report(
        official_source_latency_ms=d("3500.000000"),
        alternative_source_latency_ms=d("3250.000000"),
        capture_age_hours=d("5.000000"),
        market_move_probability=d("0.800000"),
        max_latency_ms=d("2000.000000"),
    )
    assert block_report.latency_status == "block"
    assert block_report.reason_codes == (
        "official_source_latency_above_limit",
        "alternative_source_latency_above_limit",
        "capture_age_high",
        "market_move_probability_high",
    )
    assert block_report.manual_next_step == "pause_and_refresh_information_manually"


def test_payload_validation_rejects_tampering_and_numeric_objects() -> None:
    module = api()
    report = build_report(
        official_source_latency_ms=d("3500.000000"),
        alternative_source_latency_ms=d("3250.000000"),
        capture_age_hours=d("5.000000"),
        market_move_probability=d("0.800000"),
        max_latency_ms=d("2000.000000"),
    )
    payload = report.public_payload

    tampered_payload = dict(payload)
    tampered_payload["latency_status"] = "pass"
    with pytest.raises(ValueError, match="payload_digest"):
        module.validate_market_information_source_latency_risk_report_payload(
            tampered_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["official_source_latency_ms"] = 3500
    with pytest.raises(ValueError, match="public payload"):
        module.validate_market_information_source_latency_risk_report_payload(
            numeric_payload,
        )

    flag_payload = dict(payload)
    flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.validate_market_information_source_latency_risk_report_payload(
            flag_payload,
        )


def test_public_dataclass_is_frozen_decimal_only_and_rejects_unsafe_flags() -> None:
    module = api()
    assert module.__all__ == (
        "MarketInformationSourceLatencyRiskReport",
        "build_market_information_source_latency_risk_report",
        "market_information_source_latency_risk_report_digest",
        "market_information_source_latency_risk_report_to_public_payload",
        "validate_market_information_source_latency_risk_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report()
    with pytest.raises(FrozenInstanceError):
        report.latency_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.MarketInformationSourceLatencyRiskReport):
            pass

    with pytest.raises(ValueError, match="official_source_latency_ms"):
        build_report(official_source_latency_ms=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="market_move_probability"):
        build_report(market_move_probability=d("1.100000"))
    with pytest.raises(ValueError, match="max_latency_ms"):
        build_report(max_latency_ms=d("0.000000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        build_report(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        build_report(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        build_report(readonly=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)

    for field in fields(report):
        value = getattr(report, field.name)
        assert type(value) is not float
        if field.name.endswith(("_ms", "_hours", "_probability")):
            assert type(value) is Decimal


def test_module_has_no_execution_network_or_persistence_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    for forbidden in (
        "requests",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "subprocess",
        "Path(",
        "open(",
        ".write(",
        ".read(",
        "jsonl",
        "auth",
        "wallet",
        "order",
        "keys",
        "sign",
        "execute",
        "execution",
        "crawl",
        "scrape",
        "live",
    ):
        assert forbidden not in source

    payload = build_report().public_payload
    material = {key: value for key, value in payload.items() if key != "payload_digest"}
    expected_digest = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert payload["payload_digest"] == expected_digest
