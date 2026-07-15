from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Context, Decimal, Inexact, ROUND_DOWN, Rounded, localcontext
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_scraping_gap_prioritization_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "freshness_watch_age_seconds": d("1800.000000"),
        "freshness_block_age_seconds": d("7200.000000"),
        "independence_watch_floor": d("0.600000"),
        "independence_block_floor": d("0.250000"),
        "domain_coverage_watch_floor": d("0.700000"),
        "domain_coverage_block_floor": d("0.400000"),
        "contradiction_watch_ratio": d("0.400000"),
        "contradiction_block_ratio": d("0.750000"),
        "analyst_urgency_watch_ratio": d("0.500000"),
        "analyst_urgency_block_ratio": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchSourceScrapingGapPrioritizationConfig(**values)


def gap_input(
    public_gap_key: str,
    domain_key: str,
    *,
    collection_gap_count: Decimal = d("1.000000"),
    freshest_source_age_seconds: Decimal = d("600.000000"),
    independent_source_ratio: Decimal = d("0.900000"),
    domain_coverage_ratio: Decimal = d("0.850000"),
    contradiction_exposure_ratio: Decimal = d("0.100000"),
    analyst_urgency_ratio: Decimal = d("0.100000"),
) -> Any:
    module = api()
    return module.ResearchSourceScrapingGapPrioritizationInput(
        public_gap_key=public_gap_key,
        domain_key=domain_key,
        collection_gap_count=collection_gap_count,
        freshest_source_age_seconds=freshest_source_age_seconds,
        independent_source_ratio=independent_source_ratio,
        domain_coverage_ratio=domain_coverage_ratio,
        contradiction_exposure_ratio=contradiction_exposure_ratio,
        analyst_urgency_ratio=analyst_urgency_ratio,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_scraping_gap_prioritization_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resigned_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload))
    resigned["derived_validation_digest"] = canonical_digest(resigned)
    return resigned


def test_empty_input_returns_pass_readonly_report() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceScrapingGapPrioritizationReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.gap_count == d("0.000000")
    assert report.block_gap_count == d("0.000000")
    assert report.watch_gap_count == d("0.000000")
    assert report.average_priority_score == d("0.000000")
    assert report.priority_rows == ()
    assert report.reason_codes == (
        "research_source_scraping_gap_prioritization_no_gaps",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64


def test_report_ranks_gap_targets_by_block_watch_score_and_stable_ties() -> None:
    report = build_report(
        gap_input("gap-sports", "sports.soccer"),
        gap_input(
            "gap-politics",
            "politics",
            collection_gap_count=d("3.000000"),
            freshest_source_age_seconds=d("9000.000000"),
            independent_source_ratio=d("0.200000"),
            domain_coverage_ratio=d("0.300000"),
            contradiction_exposure_ratio=d("0.850000"),
            analyst_urgency_ratio=d("0.900000"),
        ),
        gap_input(
            "gap-macro",
            "finance.macro",
            freshest_source_age_seconds=d("3600.000000"),
            independent_source_ratio=d("0.500000"),
            domain_coverage_ratio=d("0.650000"),
            contradiction_exposure_ratio=d("0.450000"),
            analyst_urgency_ratio=d("0.550000"),
        ),
        gap_input(
            "gap-crypto",
            "finance.crypto",
            freshest_source_age_seconds=d("3600.000000"),
            independent_source_ratio=d("0.500000"),
            domain_coverage_ratio=d("0.650000"),
            contradiction_exposure_ratio=d("0.450000"),
            analyst_urgency_ratio=d("0.550000"),
        ),
    )

    assert tuple(row.status for row in report.priority_rows) == (
        "block",
        "watch",
        "watch",
        "pass",
    )
    assert tuple(row.public_gap_key for row in report.priority_rows) == (
        "gap-politics",
        "gap-crypto",
        "gap-macro",
        "gap-sports",
    )
    assert tuple(row.priority_score for row in report.priority_rows) == (
        d("0.855000"),
        d("0.467500"),
        d("0.467500"),
        d("0.105833"),
    )
    assert tuple(row.independence_gap_score for row in report.priority_rows) == (
        d("0.800000"),
        d("0.500000"),
        d("0.500000"),
        d("0.100000"),
    )
    assert report.status == "block"
    assert report.gap_count == d("4.000000")
    assert report.collection_gap_count == d("6.000000")
    assert report.block_gap_count == d("1.000000")
    assert report.watch_gap_count == d("2.000000")
    assert report.reason_codes == (
        "research_source_scraping_gap_prioritization_stale_freshness",
        "research_source_scraping_gap_prioritization_weak_independence",
        "research_source_scraping_gap_prioritization_thin_domain_coverage",
        "research_source_scraping_gap_prioritization_contradiction_exposure",
        "research_source_scraping_gap_prioritization_analyst_urgency",
    )


def test_statuses_are_exactly_pass_watch_block() -> None:
    module = api()
    pass_report = build_report(gap_input("gap-sports", "sports.soccer"))
    watch_report = build_report(
        gap_input(
            "gap-macro",
            "finance.macro",
            freshest_source_age_seconds=d("1800.000000"),
        ),
    )
    block_report = build_report(
        gap_input(
            "gap-politics",
            "politics",
            contradiction_exposure_ratio=d("0.800000"),
        ),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert pass_report.status == "pass"
    assert pass_report.priority_rows[0].status == "pass"
    assert watch_report.status == "watch"
    assert watch_report.priority_rows[0].status == "watch"
    assert block_report.status == "block"
    assert block_report.priority_rows[0].status == "block"


def test_payload_is_deterministic_decimal_only_public_safe_and_digest_checked() -> None:
    module = api()
    rows = (
        gap_input(
            "gap-politics",
            "politics",
            collection_gap_count=d("3.000000"),
            freshest_source_age_seconds=d("9000.000000"),
            independent_source_ratio=d("0.200000"),
            domain_coverage_ratio=d("0.300000"),
            contradiction_exposure_ratio=d("0.850000"),
            analyst_urgency_ratio=d("0.900000"),
        ),
        gap_input("gap-sports", "sports.soccer"),
    )

    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(*rows),
    )
    reversed_payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(*reversed(rows)),
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["priority_rows"][0]["priority_score"] == "0.855000"
    assert payload["priority_rows"][0]["freshness_pressure_score"] == "1.000000"
    assert json.dumps(payload, sort_keys=True)

    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate-123",
        "market-abc",
        "will this happen",
        "https://",
        "postgres://",
        "private-token",
    ):
        assert forbidden not in encoded
    assert not any(type(value) in (float, int, Decimal) for value in _walk_values(payload))

    tampered = dict(payload)
    tampered["watch_gap_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(tampered)


def test_payload_round_trips_custom_config_for_semantic_validation() -> None:
    module = api()
    cfg = config(
        freshness_watch_age_seconds=d("100.000000"),
        freshness_block_age_seconds=d("200.000000"),
    )
    report = build_report(
        gap_input(
            "gap-politics",
            "politics",
            freshest_source_age_seconds=d("150.000000"),
        ),
        cfg=cfg,
    )
    payload = module.research_source_scraping_gap_prioritization_report_payload(report)

    assert report.config is cfg
    assert report.status == "watch"
    assert payload["config"]["freshness_watch_age_seconds"] == "100.000000"
    assert payload["config"]["freshness_block_age_seconds"] == "200.000000"
    assert module.validate_research_source_scraping_gap_prioritization_public_payload(
        payload,
    )


def test_equivalent_aware_datetimes_produce_identical_utc_reports_and_digests() -> None:
    module = api()
    row = gap_input("gap-sports", "sports.soccer")
    utc_report = build_report(row)
    offset_report = module.build_research_source_scraping_gap_prioritization_report(
        (row,),
        config=config(),
        generated_at=datetime(
            2026,
            7,
            8,
            8,
            0,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert offset_report.generated_at == GENERATED_AT
    assert offset_report == utc_report
    assert offset_report.derived_validation_digest == (
        utc_report.derived_validation_digest
    )


def test_public_payload_rejects_noncanonical_equivalent_utc_offset() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )
    payload["generated_at"] = "2026-07-08T08:00:00-04:00"

    with pytest.raises(ValueError, match="canonical UTC datetime"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(payload),
        )


def test_generated_at_requires_an_exact_datetime() -> None:
    module = api()

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_source_scraping_gap_prioritization_report(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )


def test_public_validator_rejects_forged_resigned_derived_semantics() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )

    forged_freshness = json.loads(json.dumps(payload))
    forged_freshness["priority_rows"][0]["freshness_pressure_score"] = "0.500000"
    with pytest.raises(ValueError, match="freshness_pressure_score"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(forged_freshness),
        )

    forged_score = json.loads(json.dumps(payload))
    forged_score["priority_rows"][0]["priority_score"] = "0.500000"
    forged_score["average_priority_score"] = "0.500000"
    with pytest.raises(ValueError, match="priority_score"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(forged_score),
        )

    forged_status = json.loads(json.dumps(payload))
    forged_status["priority_rows"][0]["status"] = "watch"
    forged_status["priority_rows"][0]["reason_codes"] = [
        "research_source_scraping_gap_prioritization_stale_freshness",
    ]
    forged_status["watch_gap_count"] = "1.000000"
    forged_status["status"] = "watch"
    forged_status["reason_codes"] = [
        "research_source_scraping_gap_prioritization_stale_freshness",
    ]
    with pytest.raises(ValueError, match="reason_codes|status"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(forged_status),
        )

    forged_count = resigned_payload({**payload, "gap_count": "2.000000"})
    with pytest.raises(ValueError, match="gap_count"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            forged_count,
        )

    forged_row_count = json.loads(json.dumps(payload))
    forged_row_count["priority_rows"][0]["collection_gap_count"] = "0.000000"
    forged_row_count["collection_gap_count"] = "0.000000"
    with pytest.raises(ValueError, match="collection_gap_count.*positive"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(forged_row_count),
        )


def test_public_payload_requires_exact_report_config_and_row_schemas() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )
    expected_report_fields = {
        "generated_at",
        "config_version",
        "config",
        "gap_count",
        "collection_gap_count",
        "block_gap_count",
        "watch_gap_count",
        "max_freshest_source_age_seconds",
        "min_independent_source_ratio",
        "min_domain_coverage_ratio",
        "max_contradiction_exposure_ratio",
        "max_analyst_urgency_ratio",
        "average_priority_score",
        "status",
        "reason_codes",
        "priority_rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    }
    expected_config_fields = {
        "config_version",
        "freshness_watch_age_seconds",
        "freshness_block_age_seconds",
        "independence_watch_floor",
        "independence_block_floor",
        "domain_coverage_watch_floor",
        "domain_coverage_block_floor",
        "contradiction_watch_ratio",
        "contradiction_block_ratio",
        "analyst_urgency_watch_ratio",
        "analyst_urgency_block_ratio",
        "paper_only",
        "report_only",
        "readonly",
    }
    expected_row_fields = {
        "public_gap_key",
        "domain_key",
        "collection_gap_count",
        "freshest_source_age_seconds",
        "freshness_pressure_score",
        "independent_source_ratio",
        "independence_gap_score",
        "domain_coverage_ratio",
        "domain_gap_score",
        "contradiction_exposure_ratio",
        "analyst_urgency_ratio",
        "priority_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    }

    assert set(payload) == expected_report_fields
    assert set(payload["config"]) == expected_config_fields
    assert set(payload["priority_rows"][0]) == expected_row_fields

    missing_report = dict(payload)
    missing_report.pop("average_priority_score")
    with pytest.raises(ValueError, match="fields must match"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(missing_report),
        )

    extra_report = resigned_payload({**payload, "public_note": "aggregate"})
    with pytest.raises(ValueError, match="fields must match"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            extra_report,
        )

    extra_row = json.loads(json.dumps(payload))
    extra_row["priority_rows"][0]["public_note"] = "aggregate"
    with pytest.raises(ValueError, match="fields must match"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(extra_row),
        )

    missing_config = json.loads(json.dumps(payload))
    missing_config["config"].pop("independence_watch_floor")
    with pytest.raises(ValueError, match="fields must match"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(missing_config),
        )


def test_public_validator_rejects_non_string_mapping_keys_with_value_error() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )
    payload[1] = "unexpected"  # type: ignore[index]

    with pytest.raises(ValueError, match="keys must be strings"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            payload,
        )


def test_public_validator_rejects_unsupported_nested_values_with_value_error() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )
    payload["reason_codes"] = {"unexpected"}

    with pytest.raises(ValueError, match="JSON-compatible"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            payload,
        )


def test_public_validator_rejects_cyclic_payload_values_with_value_error() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )
    cycle: list[Any] = []
    cycle.append(cycle)
    payload["reason_codes"] = cycle

    with pytest.raises(ValueError, match="cyclic"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            payload,
        )


def test_public_validator_rejects_excessive_nesting_with_value_error() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )
    nested: object = "unexpected"
    for _ in range(2000):
        nested = [nested]
    payload["reason_codes"] = nested

    with pytest.raises(ValueError, match="nesting is too deep"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            payload,
        )


def test_public_validator_rejects_mapping_and_sequence_subclasses() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )

    class DictSubclass(dict[str, Any]):
        def items(self) -> Any:
            raise AssertionError("mapping subclass contents must not be inspected")

    class ListSubclass(list[Any]):
        def __iter__(self) -> Any:
            raise AssertionError("list subclass contents must not be inspected")

    class StringSubclass(str):
        def lower(self) -> Any:
            raise AssertionError("string subclass contents must not be inspected")

    with pytest.raises(ValueError, match="payload must be a JSON object"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            DictSubclass(payload),
        )

    nested_mapping = json.loads(json.dumps(payload))
    nested_mapping["config"] = DictSubclass(nested_mapping["config"])
    with pytest.raises(ValueError, match="payload.config must be a JSON object"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            nested_mapping,
        )

    nested_sequence = json.loads(json.dumps(payload))
    nested_sequence["priority_rows"] = ListSubclass(
        nested_sequence["priority_rows"],
    )
    with pytest.raises(ValueError, match="payload.priority_rows must be a JSON array"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            nested_sequence,
        )

    nested_string = json.loads(json.dumps(payload))
    nested_string["status"] = StringSubclass(nested_string["status"])
    with pytest.raises(ValueError, match="payload.status must be a string"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            nested_string,
        )


def test_decimal_contract_rejects_noncanonical_values_and_signed_zero() -> None:
    module = api()

    with pytest.raises(ValueError, match="negative zero"):
        config(independence_block_floor=d("-0.000000"))
    with pytest.raises(ValueError, match="negative zero"):
        gap_input(
            "gap-sports",
            "sports.soccer",
            freshest_source_age_seconds=d("-0.000000"),
        )

    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )
    for field_name, invalid_value in (
        ("gap_count", 1),
        ("gap_count", 1.0),
        ("gap_count", "1"),
        ("gap_count", "1.0000000"),
        ("watch_gap_count", "-0.000000"),
    ):
        forged = resigned_payload({**payload, field_name: invalid_value})
        with pytest.raises(ValueError, match="Decimal|string|negative zero|canonical"):
            module.validate_research_source_scraping_gap_prioritization_public_payload(
                forged,
            )

    forged_row = json.loads(json.dumps(payload))
    forged_row["priority_rows"][0]["independent_source_ratio"] = "-0.000000"
    with pytest.raises(ValueError, match="negative zero"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(forged_row),
        )


def test_zero_valued_derivatives_are_decimal_and_never_signed() -> None:
    module = api()
    report = build_report(
        gap_input(
            "gap-zero",
            "policy",
            freshest_source_age_seconds=d("0.0000004"),
            independent_source_ratio=d("1.000000"),
            domain_coverage_ratio=d("1.000000"),
            contradiction_exposure_ratio=d("0.000000"),
            analyst_urgency_ratio=d("0.000000"),
        ),
    )
    row = report.priority_rows[0]
    zero_values = (
        row.freshest_source_age_seconds,
        row.freshness_pressure_score,
        row.independence_gap_score,
        row.domain_gap_score,
        row.contradiction_exposure_ratio,
        row.analyst_urgency_ratio,
        row.priority_score,
        report.block_gap_count,
        report.watch_gap_count,
        report.max_freshest_source_age_seconds,
        report.max_contradiction_exposure_ratio,
        report.max_analyst_urgency_ratio,
        report.average_priority_score,
    )

    assert all(type(value) is Decimal for value in zero_values)
    assert all(value.is_zero() and not value.is_signed() for value in zero_values)
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        report,
    )
    assert "-0.000000" not in json.dumps(payload, sort_keys=True)


def test_decimal_math_uses_fixed_context_and_checks_raw_bounds() -> None:
    rows = (
        gap_input(
            "gap-alpha",
            "policy",
            collection_gap_count=d("2.000000"),
            freshest_source_age_seconds=d("3333.333333"),
            independent_source_ratio=d("0.123456"),
            domain_coverage_ratio=d("0.234567"),
            contradiction_exposure_ratio=d("0.345678"),
            analyst_urgency_ratio=d("0.456789"),
        ),
        gap_input(
            "gap-beta",
            "policy",
            collection_gap_count=d("3.000000"),
            freshest_source_age_seconds=d("4444.444444"),
            independent_source_ratio=d("0.654321"),
            domain_coverage_ratio=d("0.765432"),
            contradiction_exposure_ratio=d("0.234567"),
            analyst_urgency_ratio=d("0.345678"),
        ),
    )
    expected = build_report(*rows)

    with localcontext(Context(prec=3, rounding=ROUND_DOWN)):
        actual = build_report(*rows)

    assert actual == expected
    assert actual.derived_validation_digest == expected.derived_validation_digest

    with pytest.raises(ValueError, match="must not exceed one"):
        config(independence_watch_floor=d("1.0000004"))
    with pytest.raises(ValueError, match="whole Decimal"):
        gap_input(
            "gap-count",
            "policy",
            collection_gap_count=d("1.0000004"),
        )


def test_build_payload_and_validation_ignore_hostile_decimal_context() -> None:
    module = api()
    rows = (
        gap_input(
            "gap-alpha",
            "policy",
            freshest_source_age_seconds=d("3333.333333"),
            independent_source_ratio=d("0.123456"),
            domain_coverage_ratio=d("0.234567"),
            contradiction_exposure_ratio=d("0.345678"),
            analyst_urgency_ratio=d("0.456789"),
        ),
        gap_input(
            "gap-beta",
            "finance",
            freshest_source_age_seconds=d("4444.444444"),
            independent_source_ratio=d("0.654321"),
            domain_coverage_ratio=d("0.765432"),
            contradiction_exposure_ratio=d("0.234567"),
            analyst_urgency_ratio=d("0.345678"),
        ),
    )
    expected_report = build_report(*rows)
    expected_payload = (
        module.research_source_scraping_gap_prioritization_report_payload(
            expected_report,
        )
    )
    hostile_context = Context(prec=2, rounding=ROUND_DOWN)
    hostile_context.traps[Inexact] = True
    hostile_context.traps[Rounded] = True

    with localcontext(hostile_context):
        actual_report = build_report(*rows)
        actual_payload = (
            module.research_source_scraping_gap_prioritization_report_payload(
                actual_report,
            )
        )
        assert module.validate_research_source_scraping_gap_prioritization_public_payload(
            actual_payload,
        )

    assert actual_report == expected_report
    assert actual_payload == expected_payload


def test_decimal_contract_rejects_all_nonfinite_values() -> None:
    for invalid in ("NaN", "sNaN", "Infinity", "-Infinity"):
        with pytest.raises(ValueError, match="finite"):
            gap_input(
                "gap-nonfinite",
                "policy",
                analyst_urgency_ratio=d(invalid),
            )

    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )
    for invalid in ("NaN", "sNaN", "Infinity", "-Infinity"):
        forged = json.loads(json.dumps(payload))
        forged["priority_rows"][0]["analyst_urgency_ratio"] = invalid
        with pytest.raises(ValueError, match="finite"):
            module.validate_research_source_scraping_gap_prioritization_public_payload(
                resigned_payload(forged),
            )


def test_public_dataclasses_are_non_subclassable() -> None:
    module = api()

    for public_type in (
        module.ResearchSourceScrapingGapPrioritizationConfig,
        module.ResearchSourceScrapingGapPrioritizationInput,
        module.ResearchSourceScrapingGapPrioritizationRow,
        module.ResearchSourceScrapingGapPrioritizationReport,
    ):
        with pytest.raises(TypeError, match="must not be subclassed"):
            type(f"Derived{public_type.__name__}", (public_type,), {})


def test_public_payload_requires_canonical_field_order_at_every_level() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )

    reordered_report = {
        key: payload[key]
        for key in (*tuple(payload)[1:], tuple(payload)[0])
    }
    reordered_report = resigned_payload(reordered_report)
    with pytest.raises(ValueError, match="fields must match|canonical"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            reordered_report,
        )

    reordered_config = json.loads(json.dumps(payload))
    config_payload = reordered_config["config"]
    reordered_config["config"] = {
        key: config_payload[key]
        for key in (*tuple(config_payload)[1:], tuple(config_payload)[0])
    }
    with pytest.raises(ValueError, match="fields must match|canonical"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(reordered_config),
        )

    reordered_row = json.loads(json.dumps(payload))
    row_payload = reordered_row["priority_rows"][0]
    reordered_row["priority_rows"][0] = {
        key: row_payload[key]
        for key in (*tuple(row_payload)[1:], tuple(row_payload)[0])
    }
    with pytest.raises(ValueError, match="fields must match|canonical"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(reordered_row),
        )


def test_digest_requires_lowercase_sha256_hex() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-sports", "sports.soccer")),
    )

    for invalid_digest in (
        payload["derived_validation_digest"].upper(),
        hashlib.sha1(b"not-sha256").hexdigest(),
        "g" * 64,
    ):
        forged = dict(payload)
        forged["derived_validation_digest"] = invalid_digest
        with pytest.raises(ValueError, match="sha256"):
            module.validate_research_source_scraping_gap_prioritization_public_payload(
                forged,
            )


def test_sort_ties_use_domain_then_public_gap_key_independent_of_input_order() -> None:
    rows = (
        gap_input("gap-zeta", "policy"),
        gap_input("gap-alpha", "policy"),
        gap_input("gap-beta", "finance"),
    )

    forward = build_report(*rows)
    reverse = build_report(*reversed(rows))

    assert tuple(row.public_gap_key for row in forward.priority_rows) == (
        "gap-beta",
        "gap-alpha",
        "gap-zeta",
    )
    assert forward == reverse


def test_resigned_payload_rejects_noncanonical_priority_row_sequence() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(
            gap_input("gap-zeta", "policy"),
            gap_input("gap-alpha", "finance"),
        ),
    )
    payload["priority_rows"].reverse()

    with pytest.raises(ValueError, match="deterministic sequence"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(payload),
        )


def test_resigned_payload_rejects_duplicate_public_gap_keys() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-alpha", "finance")),
    )
    payload["priority_rows"].append(
        json.loads(json.dumps(payload["priority_rows"][0])),
    )

    with pytest.raises(ValueError, match="unique public_gap_key"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(payload),
        )


def test_private_source_identifiers_are_rejected_in_public_keys_and_payloads() -> None:
    module = api()
    for private_key in (
        "private-source-17",
        "source_id.internal",
        "internal-endpoint",
    ):
        with pytest.raises(ValueError, match="public-safe"):
            gap_input(private_key, "policy")

    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(gap_input("gap-public", "policy")),
    )
    forged = json.loads(json.dumps(payload))
    forged["priority_rows"][0]["public_gap_key"] = "private-source-17"
    with pytest.raises(ValueError, match="unsafe|public-safe"):
        module.validate_research_source_scraping_gap_prioritization_public_payload(
            resigned_payload(forged),
        )


def test_resigned_payload_recomputes_every_report_derived_field() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(
            gap_input(
                "gap-blocked",
                "policy",
                collection_gap_count=d("3.000000"),
                freshest_source_age_seconds=d("9000.000000"),
                independent_source_ratio=d("0.200000"),
                domain_coverage_ratio=d("0.300000"),
                contradiction_exposure_ratio=d("0.850000"),
                analyst_urgency_ratio=d("0.900000"),
            ),
            gap_input("gap-pass", "sports.soccer"),
        ),
    )
    mutations = {
        "gap_count": "3.000000",
        "collection_gap_count": "5.000000",
        "block_gap_count": "0.000000",
        "watch_gap_count": "1.000000",
        "max_freshest_source_age_seconds": "8000.000000",
        "min_independent_source_ratio": "0.300000",
        "min_domain_coverage_ratio": "0.400000",
        "max_contradiction_exposure_ratio": "0.750000",
        "max_analyst_urgency_ratio": "0.800000",
        "average_priority_score": "0.500000",
        "status": "watch",
        "reason_codes": [
            "research_source_scraping_gap_prioritization_stale_freshness",
        ],
    }

    for field_name, forged_value in mutations.items():
        forged = json.loads(json.dumps(payload))
        forged[field_name] = forged_value
        with pytest.raises(ValueError, match=field_name):
            module.validate_research_source_scraping_gap_prioritization_public_payload(
                resigned_payload(forged),
            )


def test_resigned_payload_recomputes_every_row_derived_field() -> None:
    module = api()
    payload = module.research_source_scraping_gap_prioritization_report_payload(
        build_report(
            gap_input(
                "gap-watch",
                "policy",
                freshest_source_age_seconds=d("3600.000000"),
                independent_source_ratio=d("0.500000"),
                domain_coverage_ratio=d("0.650000"),
                contradiction_exposure_ratio=d("0.450000"),
                analyst_urgency_ratio=d("0.550000"),
            ),
        ),
    )
    mutations = {
        "freshness_pressure_score": "0.400000",
        "independence_gap_score": "0.400000",
        "domain_gap_score": "0.250000",
        "priority_score": "0.400000",
        "status": "pass",
        "reason_codes": [
            "research_source_scraping_gap_prioritization_clear",
        ],
    }

    for field_name, forged_value in mutations.items():
        forged = json.loads(json.dumps(payload))
        forged["priority_rows"][0][field_name] = forged_value
        with pytest.raises(ValueError, match=field_name):
            module.validate_research_source_scraping_gap_prioritization_public_payload(
                resigned_payload(forged),
            )


def test_manual_rows_and_reports_revalidate_all_derived_fields() -> None:
    module = api()
    report = build_report(gap_input("gap-sports", "sports.soccer"))
    row = report.priority_rows[0]

    with pytest.raises(ValueError, match="freshness_pressure_score"):
        module.ResearchSourceScrapingGapPrioritizationRow(
            **{
                **row.__dict__,
                "freshness_pressure_score": d("0.500000"),
                "validation_config": report.config,
            },
        )
    with pytest.raises(ValueError, match="reason_codes|status"):
        module.ResearchSourceScrapingGapPrioritizationRow(
            **{
                **row.__dict__,
                "status": "watch",
                "reason_codes": (
                    "research_source_scraping_gap_prioritization_stale_freshness",
                ),
                "validation_config": report.config,
            },
        )
    with pytest.raises(ValueError, match="collection_gap_count.*positive"):
        replace(row, collection_gap_count=d("0.000000"))
    with pytest.raises(ValueError, match="average_priority_score"):
        replace(
            report,
            average_priority_score=d("0.500000"),
            derived_validation_digest="",
        )


def test_report_revalidates_altered_frozen_row_state() -> None:
    module = api()
    report = build_report(gap_input("gap-sports", "sports.soccer"))
    object.__setattr__(report.priority_rows[0], "public_gap_key", "GAP-SPORTS")

    with pytest.raises(ValueError, match="public_gap_key"):
        module.ResearchSourceScrapingGapPrioritizationReport(
            **{
                **report.__dict__,
                "derived_validation_digest": "",
            },
        )


def test_report_revalidates_altered_row_numerics_before_sequence_checks() -> None:
    module = api()
    report = build_report(gap_input("gap-sports", "sports.soccer"))
    object.__setattr__(report.priority_rows[0], "priority_score", 0.5)

    with pytest.raises(ValueError, match="priority_score must be a Decimal"):
        module.ResearchSourceScrapingGapPrioritizationReport(
            **{
                **report.__dict__,
                "derived_validation_digest": "",
            },
        )


def test_manual_row_requires_config_for_threshold_derived_validation() -> None:
    module = api()
    row = build_report(
        gap_input("gap-sports", "sports.soccer"),
    ).priority_rows[0]

    with pytest.raises(ValueError, match="validation_config.*required"):
        module.ResearchSourceScrapingGapPrioritizationRow(**row.__dict__)

    with pytest.raises(ValueError, match="validation_config.*required"):
        replace(
            row,
            freshest_source_age_seconds=d("9000.000000"),
        )


def test_builder_revalidates_altered_frozen_config_before_use() -> None:
    altered_config = config()
    object.__setattr__(
        altered_config,
        "freshness_watch_age_seconds",
        d("7200.000001"),
    )

    with pytest.raises(
        ValueError,
        match="freshness_block_age_seconds must not be below watch age",
    ):
        build_report(cfg=altered_config)


def test_report_revalidates_altered_config_before_row_reconstruction() -> None:
    module = api()
    report = build_report(gap_input("gap-sports", "sports.soccer"))
    object.__setattr__(
        report.config,
        "independence_watch_floor",
        "0.600000",
    )

    with pytest.raises(ValueError, match="independence_watch_floor must be a Decimal"):
        module.ResearchSourceScrapingGapPrioritizationReport(
            **{
                **report.__dict__,
                "derived_validation_digest": "",
            },
        )


def test_builder_revalidates_altered_frozen_input_before_use() -> None:
    altered_input = gap_input("gap-sports", "sports.soccer")
    object.__setattr__(altered_input, "analyst_urgency_ratio", 0.5)

    with pytest.raises(ValueError, match="analyst_urgency_ratio must be a Decimal"):
        build_report(altered_input)


def test_validation_rejects_bad_types_unsafe_keys_bad_flags_and_digest_tampering() -> None:
    module = api()
    with pytest.raises(ValueError, match="freshness_watch_age_seconds must be a Decimal"):
        config(freshness_watch_age_seconds=1800)
    with pytest.raises(ValueError, match="independence_watch_floor must be a Decimal"):
        config(independence_watch_floor=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="collection_gap_count must be a Decimal"):
        gap_input("gap-politics", "politics", collection_gap_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="analyst_urgency_ratio must be a Decimal"):
        gap_input("gap-politics", "politics", analyst_urgency_ratio=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_gap_key"):
        gap_input("candidate-123", "politics")
    with pytest.raises(ValueError, match="public_gap_key"):
        gap_input("gap-http", "politics")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_source_scraping_gap_prioritization_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)

    report = build_report(gap_input("gap-politics", "politics"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


@pytest.mark.parametrize("field_name", ("paper_only", "report_only", "readonly"))
def test_phase_one_flags_are_hard_true_at_every_public_boundary(
    field_name: str,
) -> None:
    module = api()
    input_value = gap_input("gap-politics", "politics")
    report = build_report(input_value)
    row = report.priority_rows[0]
    invalid_flag = {field_name: False}

    with pytest.raises(ValueError, match=rf"{field_name} must be True"):
        config(**invalid_flag)
    with pytest.raises(ValueError, match=rf"{field_name} must be True"):
        replace(input_value, **invalid_flag)
    with pytest.raises(ValueError, match=rf"{field_name} must be True"):
        replace(row, validation_config=report.config, **invalid_flag)
    with pytest.raises(ValueError, match=rf"{field_name} must be True"):
        replace(
            report,
            derived_validation_digest="",
            **invalid_flag,
        )

    payload = module.research_source_scraping_gap_prioritization_report_payload(
        report,
    )
    for section in (None, "config", "priority_rows"):
        forged = json.loads(json.dumps(payload))
        if section is None:
            forged[field_name] = False
        elif section == "config":
            forged[section][field_name] = False
        else:
            forged[section][0][field_name] = False
        with pytest.raises(ValueError, match=rf"{field_name} must be True"):
            module.validate_research_source_scraping_gap_prioritization_public_payload(
                resigned_payload(forged),
            )


def test_exports_frozen_public_dataclasses_and_validates_manual_consistency() -> None:
    module = api()
    report = build_report(gap_input("gap-politics", "politics"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_SCRAPING_GAP_PRIORITIZATION_CONFIG_VERSION",
        "STATUSES",
        "ResearchSourceScrapingGapPrioritizationConfig",
        "ResearchSourceScrapingGapPrioritizationInput",
        "ResearchSourceScrapingGapPrioritizationReport",
        "ResearchSourceScrapingGapPrioritizationRow",
        "build_research_source_scraping_gap_prioritization_report",
        "research_source_scraping_gap_prioritization_report_payload",
        "validate_research_source_scraping_gap_prioritization_public_payload",
    )
    assert is_dataclass(config())
    assert is_dataclass(gap_input("gap-sports", "sports.soccer"))
    assert is_dataclass(report)
    assert is_dataclass(report.priority_rows[0])
    for value in (
        config(),
        gap_input("gap-sports", "sports.soccer"),
        report.priority_rows[0],
        report,
    ):
        assert value.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.priority_rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().analyst_urgency_watch_ratio = d("0.400000")
    with pytest.raises(ValueError, match="priority_score"):
        replace(report.priority_rows[0], priority_score=d("0.990000"))


def test_scope_is_report_only_and_has_no_collection_or_live_surface() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "scrapling",
        "agent_reach",
        "browser",
        "network",
        "source_url",
        "source_text",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "dsn",
        "table_name",
        "recommendation",
        "sizing",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "trade",
        "private_key",
        "credential",
        "execution",
        "persist",
        "database",
        "sqlite",
        "write_text",
        "write_bytes",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "write",
                "writelines",
                "dump",
                "save",
                "connect",
                "commit",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
        "pathlib",
        "sqlite3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_values(item))
    else:
        values.append(value)
    return tuple(values)
