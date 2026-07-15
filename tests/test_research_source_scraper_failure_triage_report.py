from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Context, Decimal, ROUND_DOWN, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_scraper_failure_triage_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scraper_failure_triage_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_observation_max_age_seconds": d("3600.000000"),
        "stale_observation_block_age_seconds": d("86400.000000"),
        "min_parse_confidence_pass_ratio": d("0.850000"),
        "min_parse_confidence_watch_ratio": d("0.600000"),
        "min_fallback_coverage_pass_ratio": d("0.750000"),
        "min_fallback_coverage_watch_ratio": d("0.400000"),
        "max_failure_rate_pass_ratio": d("0.100000"),
        "max_failure_rate_watch_ratio": d("0.350000"),
        "min_triage_pass_score": d("0.800000"),
        "min_triage_watch_score": d("0.500000"),
        "failure_rate_weight": d("0.250000"),
        "parse_confidence_weight": d("0.200000"),
        "critical_field_weight": d("0.200000"),
        "authority_weight": d("0.150000"),
        "freshness_weight": d("0.100000"),
        "fallback_coverage_weight": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceScraperFailureTriageConfig(**values)


def input_row(
    private_collection_ref: str = "private-source-collection",
    *,
    observed_at: datetime = OBSERVED_AT,
    scrape_attempt_count: Decimal = d("10"),
    scrape_failure_count: Decimal = d("1"),
    parse_confidence_ratio: Decimal = d("0.950000"),
    critical_field_count: Decimal = d("5"),
    missing_critical_field_count: Decimal = d("0"),
    authority_tier: str = "primary",
    fallback_available_count: Decimal = d("3"),
    fallback_required_count: Decimal = d("3"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScraperFailureTriageInput(
        private_collection_ref=private_collection_ref,
        observed_at=observed_at,
        scrape_attempt_count=scrape_attempt_count,
        scrape_failure_count=scrape_failure_count,
        parse_confidence_ratio=parse_confidence_ratio,
        critical_field_count=critical_field_count,
        missing_critical_field_count=missing_critical_field_count,
        authority_tier=authority_tier,
        fallback_available_count=fallback_available_count,
        fallback_required_count=fallback_required_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: object, config: object | None = None) -> Any:
    module = api()
    return module.build_research_source_scraper_failure_triage_report(
        rows,
        config=config or cfg(),
        generated_at=GENERATED_AT,
    )


def _walk_public(value: object) -> list[object]:
    values = [value]
    if type(value) is dict:
        for key, item in value.items():
            values.extend(_walk_public(key))
            values.extend(_walk_public(item))
    elif type(value) is list:
        for item in value:
            values.extend(_walk_public(item))
    return values


def _assert_payload_has_no_raw_numbers(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"payload leaked raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            _assert_payload_has_no_raw_numbers(item)
    elif type(value) is list:
        for item in value:
            _assert_payload_has_no_raw_numbers(item)


def _assert_payload_has_no_forbidden_surface(payload: dict[str, Any]) -> None:
    rendered_values = [str(value).casefold() for value in _walk_public(payload)]
    for forbidden in (
        "raw_candidate",
        "raw candidate",
        "candidate_id",
        "candidate id",
        "market_id",
        "market id",
        "market_slug",
        "market slug",
        "slug",
        "question",
        "source_url",
        "source url",
        "source_text",
        "source text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "network",
        "database",
        "table",
        "token",
        "api_key",
        "private_key",
        "secret",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommend",
        "recommendation",
        "execute",
        "execution",
        "live",
    ):
        assert all(forbidden not in value for value in rendered_values), forbidden


def _assert_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric was not Decimal: {value!r}")
    if type(value) is tuple:
        for item in value:
            _assert_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_decimal_public_numbers(getattr(value, field.name))


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def test_empty_input_blocks_with_report_only_digest_and_decimal_payload() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceScraperFailureTriageReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.attention_count == d("0.000000")
    assert report.average_triage_score == d("0.000000")
    assert report.max_observation_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "scraper_failure_triage_no_inputs",
        "scraper_failure_triage_block",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    _assert_decimal_public_numbers(report)

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["status"] == "block"
    assert payload["rows"] == []
    assert payload["input_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.research_source_scraper_failure_triage_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    assert module.validate_research_source_scraper_failure_triage_report_payload(payload)
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)


def test_report_triages_failure_rate_parse_fields_authority_freshness_and_fallbacks() -> None:
    report = build_report(
        input_row("a-private-pass"),
        input_row(
            "b-private-watch",
            observed_at=GENERATED_AT - timedelta(seconds=7200),
            scrape_failure_count=d("3"),
            parse_confidence_ratio=d("0.700000"),
            missing_critical_field_count=d("1"),
            authority_tier="secondary",
            fallback_available_count=d("2"),
            fallback_required_count=d("4"),
        ),
        input_row(
            "c-private-block",
            observed_at=GENERATED_AT - timedelta(seconds=90000),
            scrape_attempt_count=d("5"),
            scrape_failure_count=d("5"),
            parse_confidence_ratio=d("0.400000"),
            critical_field_count=d("4"),
            missing_critical_field_count=d("4"),
            authority_tier="unverified",
            fallback_available_count=d("0"),
            fallback_required_count=d("3"),
        ),
    )

    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.max_observation_age_seconds == d("90000.000000")
    assert report.average_failure_rate == d("0.466667")
    assert report.average_parse_confidence_score == d("0.683333")
    assert report.average_critical_field_completeness_score == d("0.600000")
    assert report.average_authority_score == d("0.600000")
    assert report.average_freshness_score == d("0.652174")
    assert report.average_fallback_coverage_score == d("0.500000")
    assert report.average_triage_score == d("0.595217")

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.row_label for row in report.rows) == (
        "redacted-scraper-failure-triage-000001",
        "redacted-scraper-failure-triage-000002",
        "redacted-scraper-failure-triage-000003",
    )

    block_row, watch_row, pass_row = report.rows
    assert block_row.triage_score == d("0.110000")
    assert block_row.reason_codes == (
        "failure_rate_block",
        "freshness_block",
        "parse_confidence_block",
        "authority_tier_block",
        "fallback_coverage_block",
        "critical_fields_missing_block",
        "scraper_failure_triage_block",
    )
    assert watch_row.failure_rate == d("0.300000")
    assert watch_row.failure_resilience_score == d("0.700000")
    assert watch_row.freshness_score == d("0.956522")
    assert watch_row.critical_field_completeness_score == d("0.800000")
    assert watch_row.authority_score == d("0.600000")
    assert watch_row.fallback_coverage_score == d("0.500000")
    assert watch_row.triage_score == d("0.710652")
    assert watch_row.reason_codes == (
        "failure_rate_watch",
        "freshness_watch",
        "parse_confidence_watch",
        "authority_tier_watch",
        "fallback_coverage_watch",
        "critical_fields_missing_watch",
        "scraper_failure_triage_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.triage_score == d("0.965000")
    assert pass_row.reason_codes == ("scraper_failure_triage_pass",)


def test_payload_is_deterministic_redacted_digest_validated_and_source_agnostic() -> None:
    module = api()
    rows = (
        input_row("https://example.invalid/raw_candidate/market_id/token"),
        input_row(
            "postgres://dsn/table/wallet/order/trade/live",
            scrape_failure_count=d("2"),
            parse_confidence_ratio=d("0.800000"),
            missing_critical_field_count=d("1"),
            authority_tier="secondary",
            fallback_available_count=d("2"),
        ),
    )
    first = build_report(*rows)
    second = build_report(*reversed(rows))

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = first.payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.validate_research_source_scraper_failure_triage_report_payload(payload)
    assert all(
        row["row_label"].startswith("redacted-scraper-failure-triage-")
        for row in payload["rows"]
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)

    tampered = build_report(*rows)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_scraper_failure_triage_report_payload(tampered)

    unsigned = dict(payload)
    unsigned["status"] = "pass"
    assert not module.validate_research_source_scraper_failure_triage_report_payload(
        unsigned,
    )

    malformed = dict(payload)
    malformed["status"] = "blocked"
    malformed["derived_validation_digest"] = canonical_digest(malformed)
    assert not module.validate_research_source_scraper_failure_triage_report_payload(
        malformed,
    )

    malformed_row = dict(payload)
    malformed_row["rows"] = [dict(row) for row in payload["rows"]]
    malformed_row["rows"][0]["status"] = "blocked"
    malformed_row["derived_validation_digest"] = canonical_digest(malformed_row)
    assert not module.validate_research_source_scraper_failure_triage_report_payload(
        malformed_row,
    )

    malformed_reason_count = dict(payload)
    malformed_reason_count["reason_code_counts"] = [
        dict(reason_count) for reason_count in payload["reason_code_counts"]
    ]
    malformed_reason_count["reason_code_counts"][0]["readonly"] = False
    malformed_reason_count["derived_validation_digest"] = canonical_digest(
        malformed_reason_count,
    )
    assert not module.validate_research_source_scraper_failure_triage_report_payload(
        malformed_reason_count,
    )

    forbidden_surface = dict(payload)
    forbidden_surface["execution_surface"] = "recommendation sizing"
    forbidden_surface["derived_validation_digest"] = canonical_digest(
        forbidden_surface,
    )
    assert not module.validate_research_source_scraper_failure_triage_report_payload(
        forbidden_surface,
    )

    forbidden_auth_surface = dict(payload)
    forbidden_auth_surface["auth"] = "session"
    forbidden_auth_surface["derived_validation_digest"] = canonical_digest(
        forbidden_auth_surface,
    )
    assert not module.validate_research_source_scraper_failure_triage_report_payload(
        forbidden_auth_surface,
    )


def test_payload_validation_requires_exact_canonical_schema_and_consistency() -> None:
    module = api()
    payload = build_report(
        input_row("a-private-pass"),
        input_row(
            "b-private-watch",
            observed_at=GENERATED_AT - timedelta(seconds=7200),
            scrape_failure_count=d("3"),
            parse_confidence_ratio=d("0.700000"),
            missing_critical_field_count=d("1"),
            authority_tier="secondary",
            fallback_available_count=d("2"),
            fallback_required_count=d("4"),
        ),
    ).payload

    invalid_payloads: list[dict[str, Any]] = []

    extra_report_field = deepcopy(payload)
    extra_report_field["extra"] = "benign"
    invalid_payloads.append(resign(extra_report_field))

    missing_report_field = deepcopy(payload)
    missing_report_field.pop("average_authority_score")
    invalid_payloads.append(resign(missing_report_field))

    noncanonical_decimal = deepcopy(payload)
    noncanonical_decimal["input_count"] = "2"
    invalid_payloads.append(resign(noncanonical_decimal))

    inconsistent_count = deepcopy(payload)
    inconsistent_count["input_count"] = "3.000000"
    invalid_payloads.append(resign(inconsistent_count))

    wrong_reason_codes_container = deepcopy(payload)
    wrong_reason_codes_container["reason_codes"] = "scraper_failure_triage_watch"
    invalid_payloads.append(resign(wrong_reason_codes_container))

    extra_row_field = deepcopy(payload)
    extra_row_field["rows"][0]["extra"] = "benign"
    invalid_payloads.append(resign(extra_row_field))

    missing_row_field = deepcopy(payload)
    missing_row_field["rows"][0].pop("triage_score")
    invalid_payloads.append(resign(missing_row_field))

    inconsistent_row_value = deepcopy(payload)
    inconsistent_row_value["rows"][0]["failure_rate"] = "0.200000"
    invalid_payloads.append(resign(inconsistent_row_value))

    noncanonical_row_order = deepcopy(payload)
    noncanonical_row_order["rows"].reverse()
    invalid_payloads.append(resign(noncanonical_row_order))

    extra_reason_count_field = deepcopy(payload)
    extra_reason_count_field["reason_code_counts"][0]["extra"] = "benign"
    invalid_payloads.append(resign(extra_reason_count_field))

    unknown_reason_code = deepcopy(payload)
    unknown_reason_code["reason_code_counts"][0]["reason_code"] = "unknown_reason"
    invalid_payloads.append(resign(unknown_reason_code))

    for invalid_payload in invalid_payloads:
        assert not module.validate_research_source_scraper_failure_triage_report_payload(
            invalid_payload,
        )


def test_reason_code_counts_measure_row_occurrences() -> None:
    report = build_report(
        input_row("a-private-watch", scrape_failure_count=d("2")),
        input_row("b-private-watch", scrape_failure_count=d("2")),
    )

    assert report.status == "watch"
    assert {
        item.reason_code: item.count for item in report.reason_code_counts
    } == {
        "failure_rate_watch": d("2.000000"),
        "scraper_failure_triage_watch": d("2.000000"),
    }


def test_rows_reject_forged_derived_fields_status_reasons_and_labels() -> None:
    row = build_report(input_row("a-private-pass")).rows[0]

    with pytest.raises(ValueError, match="failure_resilience_score"):
        replace(row, failure_resilience_score=d("0.500000"))

    with pytest.raises(ValueError, match="authority_score"):
        replace(row, authority_score=d("0.900000"))

    with pytest.raises(ValueError, match="triage_score"):
        replace(row, triage_score=d("0.500000"))

    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("scraper_failure_triage_watch",))

    with pytest.raises(ValueError, match="row_label"):
        replace(row, row_label="forged-public-row")


def test_public_validator_rejects_forged_resigned_row_semantics() -> None:
    module = api()
    payload = build_report(input_row("a-private-pass")).payload
    invalid_payloads: list[dict[str, Any]] = []

    forged_resilience = deepcopy(payload)
    forged_resilience["rows"][0]["failure_resilience_score"] = "0.500000"
    invalid_payloads.append(resign(forged_resilience))

    forged_authority = deepcopy(payload)
    forged_authority["rows"][0]["authority_score"] = "0.900000"
    forged_authority["average_authority_score"] = "0.900000"
    invalid_payloads.append(resign(forged_authority))

    forged_triage = deepcopy(payload)
    forged_triage["rows"][0]["triage_score"] = "0.500000"
    forged_triage["average_triage_score"] = "0.500000"
    invalid_payloads.append(resign(forged_triage))

    forged_reasons = deepcopy(payload)
    forged_reasons["rows"][0]["reason_codes"] = [
        "scraper_failure_triage_watch",
    ]
    forged_reasons["reason_codes"] = [
        "scraper_failure_triage_watch",
        "scraper_failure_triage_pass",
    ]
    reason_count_template = forged_reasons["reason_code_counts"][0]
    forged_reasons["reason_code_counts"] = [
        {
            **reason_count_template,
            "reason_code": "scraper_failure_triage_watch",
        },
        {
            **reason_count_template,
            "reason_code": "scraper_failure_triage_pass",
        },
    ]
    invalid_payloads.append(resign(forged_reasons))

    forged_label = deepcopy(payload)
    forged_label["rows"][0]["row_label"] = "forged-public-row"
    invalid_payloads.append(resign(forged_label))

    for invalid_payload in invalid_payloads:
        assert not module.validate_research_source_scraper_failure_triage_report_payload(
            invalid_payload,
        )


def test_public_validator_rejects_resigned_status_reason_and_score_forgeries() -> None:
    module = api()
    payload = build_report(input_row("a-private-pass")).payload
    reason_count_template = payload["reason_code_counts"][0]
    invalid_payloads: list[dict[str, Any]] = []

    forged_score = deepcopy(payload)
    forged_score["rows"][0]["triage_score"] = "0.950000"
    forged_score["average_triage_score"] = "0.950000"
    invalid_payloads.append(resign(forged_score))

    forged_status = deepcopy(payload)
    forged_status["rows"][0]["status"] = "watch"
    forged_status["rows"][0]["reason_codes"] = [
        "scraper_failure_triage_watch",
    ]
    forged_status["pass_count"] = "0.000000"
    forged_status["watch_count"] = "1.000000"
    forged_status["attention_count"] = "1.000000"
    forged_status["status"] = "watch"
    forged_status["reason_codes"] = ["scraper_failure_triage_watch"]
    forged_status["reason_code_counts"] = [
        {
            **reason_count_template,
            "reason_code": "scraper_failure_triage_watch",
        },
    ]
    invalid_payloads.append(resign(forged_status))

    forged_reason = deepcopy(payload)
    forged_reason["rows"][0]["status"] = "watch"
    forged_reason["rows"][0]["reason_codes"] = [
        "failure_rate_watch",
        "scraper_failure_triage_watch",
    ]
    forged_reason["pass_count"] = "0.000000"
    forged_reason["watch_count"] = "1.000000"
    forged_reason["attention_count"] = "1.000000"
    forged_reason["status"] = "watch"
    forged_reason["reason_codes"] = [
        "failure_rate_watch",
        "scraper_failure_triage_watch",
    ]
    forged_reason["reason_code_counts"] = [
        {
            **reason_count_template,
            "reason_code": "failure_rate_watch",
        },
        {
            **reason_count_template,
            "reason_code": "scraper_failure_triage_watch",
        },
    ]
    invalid_payloads.append(resign(forged_reason))

    for invalid_payload in invalid_payloads:
        assert not module.validate_research_source_scraper_failure_triage_report_payload(
            invalid_payload,
        )


def test_signed_zero_is_rejected_in_records_and_resigned_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="negative zero"):
        input_row(scrape_failure_count=d("-0"))

    payload = build_report().payload
    payload["input_count"] = "-0.000000"
    assert not module.validate_research_source_scraper_failure_triage_report_payload(
        resign(payload),
    )


def test_raw_decimal_bounds_and_integrality_are_checked_before_quantization() -> None:
    module = api()

    with pytest.raises(ValueError, match="between 0 and 1"):
        input_row(parse_confidence_ratio=d("1.0000004"))

    with pytest.raises(ValueError, match="between 0 and 1"):
        input_row(parse_confidence_ratio=d("-0.0000004"))

    with pytest.raises(ValueError, match="whole number"):
        input_row(scrape_attempt_count=d("10.0000004"))

    with pytest.raises(ValueError, match="nonnegative"):
        input_row(scrape_failure_count=d("-0.0000004"))

    with pytest.raises(ValueError, match="supported config version"):
        cfg(max_failure_rate_pass_ratio=d("0.1000004"))

    row = build_report(input_row()).rows[0]
    with pytest.raises(ValueError, match="nonnegative"):
        replace(row, observation_age_seconds=d("-0.0000004"))

    for invalid in ("NaN", "sNaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="finite"):
            input_row(parse_confidence_ratio=d(invalid))

        payload = build_report().payload
        payload["input_count"] = invalid
        assert not module.validate_research_source_scraper_failure_triage_report_payload(
            resign(payload),
        )


def test_report_math_is_independent_of_the_ambient_decimal_context() -> None:
    module = api()
    config = cfg()
    rows = (
        input_row(
            "a-private-watch",
            observed_at=GENERATED_AT - timedelta(seconds=7200),
            scrape_attempt_count=d("13"),
            scrape_failure_count=d("4"),
            parse_confidence_ratio=d("0.7123456"),
            critical_field_count=d("7"),
            missing_critical_field_count=d("2"),
            authority_tier="secondary",
            fallback_available_count=d("2"),
            fallback_required_count=d("5"),
        ),
        input_row(
            "b-private-pass",
            scrape_attempt_count=d("17"),
            scrape_failure_count=d("1"),
            parse_confidence_ratio=d("0.9234567"),
            critical_field_count=d("11"),
            missing_critical_field_count=d("0"),
            fallback_available_count=d("5"),
            fallback_required_count=d("6"),
        ),
    )
    expected = module.build_research_source_scraper_failure_triage_report(
        rows,
        config=config,
        generated_at=GENERATED_AT,
    ).payload

    with localcontext(Context(prec=2, rounding=ROUND_DOWN)):
        actual = module.build_research_source_scraper_failure_triage_report(
            rows,
            config=config,
            generated_at=GENERATED_AT,
        ).payload

    assert actual == expected


def test_rows_use_complete_severity_sorting_and_canonical_display_labels() -> None:
    severe = input_row(
        "z-private-severe-watch",
        scrape_attempt_count=d("10"),
        scrape_failure_count=d("3"),
        parse_confidence_ratio=d("0.700000"),
        missing_critical_field_count=d("1"),
        authority_tier="secondary",
        fallback_available_count=d("2"),
        fallback_required_count=d("4"),
    )
    mild = input_row(
        "a-private-mild-watch",
        scrape_attempt_count=d("10"),
        scrape_failure_count=d("2"),
    )

    forward = build_report(mild, severe)
    reverse = build_report(severe, mild)

    assert forward == reverse
    assert tuple(row.triage_score for row in forward.rows) == tuple(
        sorted(row.triage_score for row in forward.rows),
    )
    assert tuple(row.row_label for row in forward.rows) == (
        "redacted-scraper-failure-triage-000001",
        "redacted-scraper-failure-triage-000002",
    )


def test_public_rows_recompute_all_derived_fields_from_safe_base_telemetry() -> None:
    module = api()
    payload = build_report(
        input_row(
            "private-sensitive-collection",
            scrape_attempt_count=d("10"),
            scrape_failure_count=d("1"),
            critical_field_count=d("5"),
            missing_critical_field_count=d("1"),
            fallback_available_count=d("3"),
            fallback_required_count=d("4"),
        ),
    ).payload
    row = payload["rows"][0]

    assert row["generated_at"] == GENERATED_AT.isoformat()
    assert row["observed_at"] == OBSERVED_AT.isoformat()
    assert row["scrape_attempt_count"] == "10.000000"
    assert row["scrape_failure_count"] == "1.000000"
    assert row["critical_field_count"] == "5.000000"
    assert row["fallback_available_count"] == "3.000000"
    assert row["fallback_required_count"] == "4.000000"
    assert "private_collection_ref" not in row

    forged = deepcopy(payload)
    forged_row = forged["rows"][0]
    forged_row["critical_field_completeness_score"] = "0.600000"
    forged_row["triage_score"] = "0.860000"
    forged["average_critical_field_completeness_score"] = "0.600000"
    forged["average_triage_score"] = "0.860000"

    assert not module.validate_research_source_scraper_failure_triage_report_payload(
        resign(forged),
    )

    for field_name, forged_value in (
        ("observed_at", (OBSERVED_AT - timedelta(seconds=1)).isoformat()),
        ("scrape_failure_count", "2.000000"),
        ("critical_field_count", "4.000000"),
        ("fallback_available_count", "2.000000"),
    ):
        stale_derived = deepcopy(payload)
        stale_derived["rows"][0][field_name] = forged_value
        assert not module.validate_research_source_scraper_failure_triage_report_payload(
            resign(stale_derived),
        )


def test_payload_revalidates_resigned_object_state_and_supported_config() -> None:
    module = api()

    with pytest.raises(ValueError, match="supported config version"):
        cfg(max_failure_rate_pass_ratio=d("0.200000"))

    signed_zero_report = build_report()
    object.__setattr__(signed_zero_report, "input_count", d("-0.000000"))
    object.__setattr__(
        signed_zero_report,
        "derived_validation_digest",
        module._report_digest(signed_zero_report),
    )
    with pytest.raises(ValueError, match="negative zero"):
        module.research_source_scraper_failure_triage_report_payload(
            signed_zero_report,
        )

    unsafe_row_report = build_report(input_row("a-private-pass"))
    object.__setattr__(unsafe_row_report.rows[0], "paper_only", False)
    object.__setattr__(
        unsafe_row_report,
        "derived_validation_digest",
        module._report_digest(unsafe_row_report),
    )
    with pytest.raises(ValueError, match="paper_only"):
        module.research_source_scraper_failure_triage_report_payload(
            unsafe_row_report,
        )

    unsafe_report = build_report(input_row("a-private-pass"))
    object.__setattr__(unsafe_report, "readonly", False)
    object.__setattr__(
        unsafe_report,
        "derived_validation_digest",
        module._report_digest(unsafe_report),
    )
    with pytest.raises(ValueError, match="readonly"):
        module.research_source_scraper_failure_triage_report_payload(unsafe_report)


def test_builder_revalidates_object_setattr_config_state() -> None:
    config = cfg()
    object.__setattr__(config, "max_failure_rate_pass_ratio", d("0.200000"))

    with pytest.raises(
        ValueError,
        match="max_failure_rate_pass_ratio must match the supported config version",
    ):
        build_report(input_row("a-private-pass"), config=config)


def test_builder_revalidates_object_setattr_input_state() -> None:
    item = input_row("a-private-pass")
    object.__setattr__(item, "private_collection_ref", "")

    with pytest.raises(ValueError, match="private_collection_ref must be a non-empty string"):
        build_report(item)


def test_public_validator_rejects_resigned_noncanonical_payload_key_order() -> None:
    module = api()
    payload = build_report(input_row("a-private-pass")).payload
    reordered = {key: payload[key] for key in reversed(payload)}

    assert not module.validate_research_source_scraper_failure_triage_report_payload(
        resign(reordered),
    )


def test_public_validator_rejects_resigned_noncanonical_nested_key_order() -> None:
    module = api()
    payload = build_report(input_row("a-private-pass")).payload

    reordered_row = deepcopy(payload)
    reordered_row["rows"][0] = {
        key: reordered_row["rows"][0][key]
        for key in reversed(reordered_row["rows"][0])
    }
    reordered_reason_count = deepcopy(payload)
    reordered_reason_count["reason_code_counts"][0] = {
        key: reordered_reason_count["reason_code_counts"][0][key]
        for key in reversed(reordered_reason_count["reason_code_counts"][0])
    }

    for noncanonical_payload in (reordered_row, reordered_reason_count):
        assert not module.validate_research_source_scraper_failure_triage_report_payload(
            resign(noncanonical_payload),
        )


def test_public_validator_rejects_resigned_unsupported_config_version() -> None:
    module = api()
    payload = build_report(input_row("a-private-pass")).payload
    payload["config_version"] = "research-source-scraper-failure-triage-report-v9"

    assert not module.validate_research_source_scraper_failure_triage_report_payload(
        resign(payload),
    )


def test_report_payload_revalidates_mutated_nested_row_and_reason_count_state() -> None:
    module = api()

    mutated_row_report = build_report(input_row("a-private-pass"))
    object.__setattr__(mutated_row_report.rows[0], "triage_score", d("0.500000"))
    object.__setattr__(
        mutated_row_report,
        "derived_validation_digest",
        module._report_digest(mutated_row_report),
    )
    with pytest.raises(ValueError, match="triage_score"):
        module.research_source_scraper_failure_triage_report_payload(mutated_row_report)

    mutated_reason_count_report = build_report(input_row("a-private-pass"))
    object.__setattr__(
        mutated_reason_count_report.reason_code_counts[0],
        "count",
        d("99.000000"),
    )
    object.__setattr__(
        mutated_reason_count_report,
        "derived_validation_digest",
        module._report_digest(mutated_reason_count_report),
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        module.research_source_scraper_failure_triage_report_payload(
            mutated_reason_count_report,
        )


def test_dataclasses_are_frozen_flags_and_inputs_are_strict_without_network_imports() -> None:
    module = api()
    report = build_report(input_row("a-private-pass"))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    for public_type in (
        module.ResearchSourceScraperFailureTriageConfig,
        module.ResearchSourceScraperFailureTriageInput,
        module.ResearchSourceScraperFailureTriageRow,
        module.ResearchSourceScraperFailureTriageReasonCodeCount,
        module.ResearchSourceScraperFailureTriageReport,
    ):
        with pytest.raises(TypeError):
            type(f"Bad{public_type.__name__}", (public_type,), {})

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(input_row(report_only=True), report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="must be exactly Decimal"):
        input_row(scrape_failure_count=_DecimalSubclass("1"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be exactly datetime"):
        module.build_research_source_scraper_failure_triage_report(
            (input_row(),),
            config=cfg(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="utcoffset"):
        input_row(observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="cannot be after generated_at"):
        build_report(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="failure"):
        input_row(scrape_failure_count=d("11"), scrape_attempt_count=d("10"))

    with pytest.raises(ValueError, match="missing_critical"):
        input_row(missing_critical_field_count=d("6"), critical_field_count=d("5"))

    with pytest.raises(ValueError, match="fallback_available"):
        input_row(fallback_available_count=d("4"), fallback_required_count=d("3"))

    with pytest.raises(ValueError, match="weights"):
        cfg(failure_rate_weight=d("0.300000"))

    for public_record in (
        cfg(),
        input_row(),
        report,
        report.rows[0],
        report.reason_code_counts[0],
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        _assert_decimal_public_numbers(public_record)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")

    forbidden_imports = {
        "aiohttp",
        "boto3",
        "http",
        "requests",
        "httpx",
        "os",
        "pathlib",
        "redis",
        "shutil",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "tempfile",
        "urllib",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    forbidden_call_names = {
        "commit",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "mkdir",
        "open",
        "remove",
        "rename",
        "request",
        "rollback",
        "send",
        "sendall",
        "touch",
        "unlink",
        "urlopen",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_call_names
        elif isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden_call_names

    for public_name in module.__all__:
        _assert_payload_has_no_forbidden_surface({"name": public_name})
    for cls in (
        module.ResearchSourceScraperFailureTriageConfig,
        module.ResearchSourceScraperFailureTriageInput,
        module.ResearchSourceScraperFailureTriageReasonCodeCount,
        module.ResearchSourceScraperFailureTriageRow,
        module.ResearchSourceScraperFailureTriageReport,
    ):
        for field in fields(cls):
            _assert_payload_has_no_forbidden_surface({"field": field.name})
