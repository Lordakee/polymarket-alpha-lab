from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_event_information_asymmetry_watch_report"


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
    market_move_probability: Decimal = d("0.020000"),
    official_source_age_hours: Decimal = d("1.000000"),
    independent_source_age_hours: Decimal = d("1.500000"),
    source_conflict_count: Decimal = d("0.000000"),
    spread_probability: Decimal = d("0.010000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.build_market_event_information_asymmetry_watch_report(
        market_move_probability=market_move_probability,
        official_source_age_hours=official_source_age_hours,
        independent_source_age_hours=independent_source_age_hours,
        source_conflict_count=source_conflict_count,
        spread_probability=spread_probability,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_builds_pass_report_with_public_payload_and_digest() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.MarketEventInformationAsymmetryWatchReport
    assert is_dataclass(report)
    assert report.asymmetry_status == "pass"
    assert report.reason_codes == ("information_asymmetry_within_limit",)
    assert report.manual_next_step == "continue_manual_information_monitoring"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert payload == module.market_event_information_asymmetry_watch_report_to_public_payload(
        report,
    )
    assert payload["market_move_probability"] == "0.020000"
    assert payload["official_source_age_hours"] == "1.000000"
    assert payload["independent_source_age_hours"] == "1.500000"
    assert payload["source_conflict_count"] == "0.000000"
    assert payload["spread_probability"] == "0.010000"
    assert payload["asymmetry_status"] == "pass"
    assert payload["reason_codes"] == ["information_asymmetry_within_limit"]
    assert payload["manual_next_step"] == "continue_manual_information_monitoring"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(report.payload_digest) == 64
    int(report.payload_digest, 16)
    assert payload["payload_digest"] == report.payload_digest
    assert module.market_event_information_asymmetry_watch_report_digest(report) == report.payload_digest
    assert module.validate_market_event_information_asymmetry_watch_report_payload(payload)
    assert_no_numeric_objects(payload)
    json.dumps(payload, sort_keys=True)


def test_status_reason_codes_and_manual_next_step_are_deterministic() -> None:
    watch_report = build_report(
        market_move_probability=d("0.090000"),
        official_source_age_hours=d("2.000000"),
        independent_source_age_hours=d("2.500000"),
        source_conflict_count=d("0.000000"),
        spread_probability=d("0.055000"),
    )
    assert watch_report.asymmetry_status == "watch"
    assert watch_report.reason_codes == (
        "market_move_probability_high",
        "spread_probability_wide",
    )
    assert watch_report.manual_next_step == "manually_compare_public_information_sources"

    block_report = build_report(
        market_move_probability=d("0.180000"),
        official_source_age_hours=d("8.000000"),
        independent_source_age_hours=d("0.500000"),
        source_conflict_count=d("2.000000"),
        spread_probability=d("0.080000"),
    )
    assert block_report.asymmetry_status == "block"
    assert block_report.reason_codes == (
        "market_move_probability_high",
        "official_source_stale",
        "independent_source_fresh",
        "source_conflicts_present",
        "spread_probability_wide",
    )
    assert block_report.manual_next_step == "pause_probability_interpretation_for_manual_source_review"


def test_payload_validation_rejects_tampering_numeric_objects_and_flag_downgrades() -> None:
    module = api()
    report = build_report(
        market_move_probability=d("0.180000"),
        official_source_age_hours=d("8.000000"),
        independent_source_age_hours=d("0.500000"),
        source_conflict_count=d("2.000000"),
        spread_probability=d("0.080000"),
    )
    payload = report.public_payload

    tampered_payload = dict(payload)
    tampered_payload["asymmetry_status"] = "pass"
    with pytest.raises(ValueError, match="payload_digest"):
        module.validate_market_event_information_asymmetry_watch_report_payload(
            tampered_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["market_move_probability"] = 0.18
    with pytest.raises(ValueError, match="public payload"):
        module.validate_market_event_information_asymmetry_watch_report_payload(
            numeric_payload,
        )

    flag_payload = dict(payload)
    flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.validate_market_event_information_asymmetry_watch_report_payload(
            flag_payload,
        )


def test_public_dataclass_is_frozen_decimal_only_and_rejects_unsafe_flags() -> None:
    module = api()
    assert module.__all__ == (
        "MarketEventInformationAsymmetryWatchReport",
        "build_market_event_information_asymmetry_watch_report",
        "market_event_information_asymmetry_watch_report_digest",
        "market_event_information_asymmetry_watch_report_to_public_payload",
        "validate_market_event_information_asymmetry_watch_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report()
    with pytest.raises(FrozenInstanceError):
        report.asymmetry_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.MarketEventInformationAsymmetryWatchReport):
            pass

    with pytest.raises(ValueError, match="market_move_probability"):
        build_report(market_move_probability=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="market_move_probability"):
        build_report(market_move_probability=d("1.100000"))
    with pytest.raises(ValueError, match="official_source_age_hours"):
        build_report(official_source_age_hours=d("-0.000001"))
    with pytest.raises(ValueError, match="source_conflict_count"):
        build_report(source_conflict_count=d("1.250000"))
    with pytest.raises(ValueError, match="spread_probability"):
        build_report(spread_probability=d("1.100000"))
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
        if field.name.endswith(("_probability", "_hours", "_count")):
            assert type(value) is Decimal


def test_module_has_no_network_persistence_or_action_surface() -> None:
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
