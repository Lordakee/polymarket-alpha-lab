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
    "polymarket_alpha_lab.market_candidate_information_freshness_score_report"
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
    official_source_age_hours: Decimal = d("2.000000"),
    independent_source_age_hours: Decimal = d("3.000000"),
    forecast_age_hours: Decimal = d("1.000000"),
    market_price_move_probability: Decimal = d("0.120000"),
    freshness_penalty_probability: Decimal = d("0.050000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.build_market_candidate_information_freshness_score_report(
        official_source_age_hours=official_source_age_hours,
        independent_source_age_hours=independent_source_age_hours,
        forecast_age_hours=forecast_age_hours,
        market_price_move_probability=market_price_move_probability,
        freshness_penalty_probability=freshness_penalty_probability,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def test_builds_pass_freshness_report_with_public_payload_and_digest() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.MarketCandidateInformationFreshnessScoreReport
    assert is_dataclass(report)
    assert report.freshness_status == "pass"
    assert report.freshness_score_probability == d("0.830000")
    assert report.reason_codes == ("candidate_information_fresh_enough",)
    assert report.manual_next_step == "continue_manual_candidate_review"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.public_payload
    assert (
        payload
        == module.market_candidate_information_freshness_score_report_to_public_payload(
            report,
        )
    )
    assert payload["official_source_age_hours"] == "2.000000"
    assert payload["independent_source_age_hours"] == "3.000000"
    assert payload["forecast_age_hours"] == "1.000000"
    assert payload["market_price_move_probability"] == "0.120000"
    assert payload["freshness_penalty_probability"] == "0.050000"
    assert payload["freshness_status"] == "pass"
    assert payload["freshness_score_probability"] == "0.830000"
    assert payload["reason_codes"] == ["candidate_information_fresh_enough"]
    assert payload["manual_next_step"] == "continue_manual_candidate_review"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(report.payload_digest) == 64
    int(report.payload_digest, 16)
    assert payload["payload_digest"] == report.payload_digest
    assert (
        module.market_candidate_information_freshness_score_report_digest(report)
        == report.payload_digest
    )
    assert module.validate_market_candidate_information_freshness_score_report_payload(
        payload,
    )
    assert_no_numeric_objects(payload)
    json.dumps(payload, sort_keys=True)


def test_freshness_status_reason_codes_and_manual_next_step_are_deterministic() -> None:
    watch_report = build_report(
        official_source_age_hours=d("7.000000"),
        independent_source_age_hours=d("4.000000"),
        forecast_age_hours=d("5.000000"),
        market_price_move_probability=d("0.300000"),
        freshness_penalty_probability=d("0.150000"),
    )
    assert watch_report.freshness_status == "watch"
    assert watch_report.freshness_score_probability == d("0.550000")
    assert watch_report.reason_codes == (
        "official_source_age_high",
        "forecast_age_high",
    )
    assert watch_report.manual_next_step == "manually_refresh_candidate_information"

    block_report = build_report(
        official_source_age_hours=d("12.000000"),
        independent_source_age_hours=d("14.000000"),
        forecast_age_hours=d("9.000000"),
        market_price_move_probability=d("0.700000"),
        freshness_penalty_probability=d("0.250000"),
    )
    assert block_report.freshness_status == "block"
    assert block_report.freshness_score_probability == d("0.050000")
    assert block_report.reason_codes == (
        "official_source_age_high",
        "independent_source_age_high",
        "forecast_age_high",
        "market_price_move_probability_high",
        "freshness_penalty_probability_high",
    )
    assert (
        block_report.manual_next_step
        == "pause_candidate_review_until_public_information_refresh"
    )


def test_payload_validation_rejects_tampering_and_numeric_objects() -> None:
    module = api()
    report = build_report(
        official_source_age_hours=d("12.000000"),
        independent_source_age_hours=d("14.000000"),
        forecast_age_hours=d("9.000000"),
        market_price_move_probability=d("0.700000"),
        freshness_penalty_probability=d("0.250000"),
    )
    payload = report.public_payload

    tampered_payload = dict(payload)
    tampered_payload["freshness_status"] = "pass"
    with pytest.raises(ValueError, match="payload_digest"):
        module.validate_market_candidate_information_freshness_score_report_payload(
            tampered_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["official_source_age_hours"] = 12
    with pytest.raises(ValueError, match="public payload"):
        module.validate_market_candidate_information_freshness_score_report_payload(
            numeric_payload,
        )

    flag_payload = dict(payload)
    flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.validate_market_candidate_information_freshness_score_report_payload(
            flag_payload,
        )


def test_public_dataclass_is_frozen_decimal_only_and_rejects_unsafe_flags() -> None:
    module = api()
    assert module.__all__ == (
        "MarketCandidateInformationFreshnessScoreReport",
        "build_market_candidate_information_freshness_score_report",
        "market_candidate_information_freshness_score_report_digest",
        "market_candidate_information_freshness_score_report_to_public_payload",
        "validate_market_candidate_information_freshness_score_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report()
    with pytest.raises(FrozenInstanceError):
        report.freshness_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.MarketCandidateInformationFreshnessScoreReport):
            pass

    with pytest.raises(ValueError, match="official_source_age_hours"):
        build_report(official_source_age_hours=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="market_price_move_probability"):
        build_report(market_price_move_probability=d("1.100000"))
    with pytest.raises(ValueError, match="freshness_penalty_probability"):
        build_report(freshness_penalty_probability=d("-0.100000"))
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
        if field.name.endswith(("_hours", "_probability")):
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
