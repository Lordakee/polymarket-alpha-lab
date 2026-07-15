from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal, Inexact, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_scraping_source_reconciliation_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scraping_source_reconciliation_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
CAPTURED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)


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
        "fresh_extraction_max_age_seconds": d("3600.000000"),
        "stale_extraction_block_age_seconds": d("86400.000000"),
        "min_extraction_confidence_pass_ratio": d("0.850000"),
        "min_extraction_confidence_watch_ratio": d("0.600000"),
        "min_authority_score_pass_ratio": d("0.800000"),
        "min_authority_score_watch_ratio": d("0.500000"),
        "max_conflict_pressure_pass_ratio": d("0.200000"),
        "max_conflict_pressure_watch_ratio": d("0.500000"),
        "min_fallback_coverage_pass_ratio": d("0.800000"),
        "min_fallback_coverage_watch_ratio": d("0.400000"),
        "min_reconciliation_pass_score": d("0.800000"),
        "min_reconciliation_watch_score": d("0.500000"),
        "freshness_weight": d("0.200000"),
        "extraction_confidence_weight": d("0.250000"),
        "authority_weight": d("0.200000"),
        "conflict_pressure_weight": d("0.200000"),
        "fallback_coverage_weight": d("0.150000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceScrapingSourceReconciliationConfig(**values)


def input_row(
    private_reconciliation_ref: str = "private-reconciliation",
    *,
    retrieval_tool: str = "scrapling",
    captured_at: datetime = CAPTURED_AT,
    extraction_confidence: Decimal = d("0.950000"),
    authority_tier: str = "primary",
    conflict_pressure: Decimal = d("0.100000"),
    fallback_coverage: Decimal = d("1.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScrapingSourceReconciliationInput(
        private_reconciliation_ref=private_reconciliation_ref,
        retrieval_tool=retrieval_tool,
        captured_at=captured_at,
        extraction_confidence=extraction_confidence,
        authority_tier=authority_tier,
        conflict_pressure=conflict_pressure,
        fallback_coverage=fallback_coverage,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: object, config: object | None = None) -> Any:
    module = api()
    return module.build_research_source_scraping_source_reconciliation_report(
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
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "recommendation",
        "position_size",
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


def test_empty_input_blocks_with_report_only_public_payload_digest() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceScrapingSourceReconciliationReport
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
    assert report.average_reconciliation_score == d("0.000000")
    assert report.max_extraction_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "source_reconciliation_no_inputs",
        "source_reconciliation_block",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    _assert_decimal_public_numbers(report)

    payload = report.public_payload
    json.dumps(payload, sort_keys=True)
    assert payload["status"] == "block"
    assert payload["rows"] == []
    assert payload["input_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert (
        module.research_source_scraping_source_reconciliation_report_digest(report)
        == payload["derived_validation_digest"]
    )
    assert module.validate_research_source_scraping_source_reconciliation_report_public_payload(
        payload,
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)


def test_reconciliation_scores_freshness_confidence_authority_conflict_and_fallback() -> None:
    report = build_report(
        input_row("a-private-pass"),
        input_row(
            "b-private-watch",
            retrieval_tool="agent_reach",
            captured_at=GENERATED_AT - timedelta(seconds=7200),
            extraction_confidence=d("0.700000"),
            authority_tier="secondary",
            conflict_pressure=d("0.300000"),
            fallback_coverage=d("0.600000"),
        ),
        input_row(
            "c-private-block",
            retrieval_tool="generic",
            captured_at=GENERATED_AT - timedelta(seconds=90000),
            extraction_confidence=d("0.400000"),
            authority_tier="unknown",
            conflict_pressure=d("0.800000"),
            fallback_coverage=d("0.100000"),
        ),
    )

    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.max_extraction_age_seconds == d("90000.000000")
    assert report.average_freshness_score == d("0.652174")
    assert report.average_extraction_confidence_score == d("0.683333")
    assert report.average_authority_score == d("0.666667")
    assert report.average_conflict_pressure_score == d("0.600000")
    assert report.average_fallback_coverage_score == d("0.566667")
    assert report.average_reconciliation_score == d("0.639601")

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.row_label for row in report.rows) == (
        "redacted-source-reconciliation-000001",
        "redacted-source-reconciliation-000002",
        "redacted-source-reconciliation-000003",
    )
    assert tuple(row.rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    block_row, watch_row, pass_row = report.rows
    assert block_row.reconciliation_score == d("0.205000")
    assert block_row.reason_codes == (
        "freshness_block",
        "extraction_confidence_block",
        "authority_tier_block",
        "conflict_pressure_block",
        "fallback_coverage_block",
        "source_reconciliation_block",
    )
    assert watch_row.extraction_age_seconds == d("7200.000000")
    assert watch_row.freshness_score == d("0.956522")
    assert watch_row.extraction_confidence_score == d("0.700000")
    assert watch_row.authority_score == d("0.750000")
    assert watch_row.conflict_pressure_score == d("0.700000")
    assert watch_row.fallback_coverage_score == d("0.600000")
    assert watch_row.reconciliation_score == d("0.746304")
    assert watch_row.reason_codes == (
        "freshness_watch",
        "extraction_confidence_watch",
        "authority_tier_watch",
        "conflict_pressure_watch",
        "fallback_coverage_watch",
        "source_reconciliation_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.reconciliation_score == d("0.967500")
    assert pass_row.reason_codes == ("source_reconciliation_pass",)


def test_stale_extraction_penalty_blocks_even_when_other_dimensions_are_strong() -> None:
    report = build_report(
        input_row(
            "stale-but-otherwise-good",
            captured_at=GENERATED_AT - timedelta(seconds=86400),
            extraction_confidence=d("1.000000"),
            authority_tier="official",
            conflict_pressure=d("0.000000"),
            fallback_coverage=d("1.000000"),
        ),
    )

    row = report.rows[0]
    assert report.status == "block"
    assert row.status == "block"
    assert row.freshness_score == d("0.000000")
    assert row.reconciliation_score == d("0.800000")
    assert row.reason_codes == (
        "freshness_block",
        "source_reconciliation_block",
    )


def test_public_payload_is_deterministic_redacted_and_digest_validated() -> None:
    module = api()
    rows = (
        input_row("https://example.invalid/raw_candidate/market_id/token"),
        input_row(
            "postgres://dsn/table/wallet/order/trade/live",
            retrieval_tool="agent_reach",
            extraction_confidence=d("0.800000"),
            conflict_pressure=d("0.250000"),
            fallback_coverage=d("0.700000"),
        ),
    )
    first = build_report(*rows)
    second = build_report(*reversed(rows))

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = first.public_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.validate_research_source_scraping_source_reconciliation_report_public_payload(
        payload,
    )
    assert {row["retrieval_tool"] for row in payload["rows"]} == {
        "agent_reach",
        "scrapling",
    }
    assert all(
        row["row_label"].startswith("redacted-source-reconciliation-")
        for row in payload["rows"]
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)

    tampered = build_report(*rows)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_scraping_source_reconciliation_report_public_payload(
            tampered,
        )

    unsigned = dict(payload)
    unsigned["status"] = "pass"
    assert not module.validate_research_source_scraping_source_reconciliation_report_public_payload(
        unsigned,
    )


def test_resigned_public_payload_rejects_forged_derived_values() -> None:
    module = api()
    original = build_report(input_row("derived-pass")).public_payload

    forged_payloads: list[dict[str, Any]] = []

    forged = deepcopy(original)
    forged["status"] = "watch"
    forged_payloads.append(resign(forged))

    forged = deepcopy(original)
    forged["pass_count"] = "0.000000"
    forged_payloads.append(resign(forged))

    forged = deepcopy(original)
    forged["average_reconciliation_score"] = "0.123456"
    forged_payloads.append(resign(forged))

    forged = deepcopy(original)
    forged["rows"][0]["freshness_score"] = "0.500000"
    forged_payloads.append(resign(forged))

    forged = deepcopy(original)
    forged["rows"][0]["reconciliation_score"] = "0.500000"
    forged_payloads.append(resign(forged))

    forged = deepcopy(original)
    forged["rows"][0]["status"] = "watch"
    forged_payloads.append(resign(forged))

    forged = deepcopy(original)
    forged["rows"][0]["reason_codes"] = ["source_reconciliation_watch"]
    forged_payloads.append(resign(forged))

    forged = deepcopy(original)
    forged["reason_code_counts"][0]["count"] = "2.000000"
    forged_payloads.append(resign(forged))

    for payload in forged_payloads:
        assert not (
            module.validate_research_source_scraping_source_reconciliation_report_public_payload(
                payload,
            )
        )


def test_resigned_payload_recomputes_rank_scores_counts_and_aggregates() -> None:
    module = api()
    original = build_report(
        input_row("pass-source"),
        input_row(
            "watch-source",
            retrieval_tool="agent_reach",
            captured_at=GENERATED_AT - timedelta(seconds=7200),
            extraction_confidence=d("0.700000"),
            authority_tier="secondary",
            conflict_pressure=d("0.300000"),
            fallback_coverage=d("0.600000"),
        ),
        input_row(
            "block-source",
            retrieval_tool="generic",
            captured_at=GENERATED_AT - timedelta(seconds=90000),
            extraction_confidence=d("0.400000"),
            authority_tier="unknown",
            conflict_pressure=d("0.800000"),
            fallback_coverage=d("0.100000"),
        ),
    ).public_payload

    forged_payloads: list[dict[str, Any]] = []
    mutations = (
        ("watch_count", "0.000000"),
        ("attention_count", "1.000000"),
        ("max_extraction_age_seconds", "89999.000000"),
        ("average_freshness_score", "0.500000"),
        ("average_authority_score", "0.500000"),
        ("average_conflict_pressure_score", "0.500000"),
        ("average_fallback_coverage_score", "0.500000"),
    )
    for field_name, value in mutations:
        forged = deepcopy(original)
        forged[field_name] = value
        forged_payloads.append(resign(forged))

    row_mutations = (
        ("rank", "2.000000"),
        ("row_label", "redacted-source-reconciliation-999999"),
        ("extraction_age_seconds", "89999.000000"),
        ("freshness_score", "0.500000"),
        ("extraction_confidence_score", "0.500000"),
        ("authority_score", "0.500000"),
        ("conflict_pressure_score", "0.500000"),
        ("fallback_coverage_score", "0.500000"),
        ("reconciliation_score", "0.500000"),
        ("status", "watch"),
        ("reason_codes", ["source_reconciliation_watch"]),
    )
    for field_name, value in row_mutations:
        forged = deepcopy(original)
        forged["rows"][0][field_name] = value
        forged_payloads.append(resign(forged))

    forged = deepcopy(original)
    forged["rows"] = list(reversed(forged["rows"]))
    forged_payloads.append(resign(forged))

    forged = deepcopy(original)
    forged["reason_code_counts"][0]["count"] = "99.000000"
    forged_payloads.append(resign(forged))

    for payload in forged_payloads:
        assert not (
            module.validate_research_source_scraping_source_reconciliation_report_public_payload(
                payload,
            )
        )


def test_reason_code_counts_aggregate_row_occurrences() -> None:
    module = api()
    report = build_report(
        input_row(
            "first-watch",
            extraction_confidence=d("0.700000"),
        ),
        input_row(
            "second-watch",
            retrieval_tool="agent_reach",
            extraction_confidence=d("0.700000"),
        ),
    )

    counts = {
        item.reason_code: item.count
        for item in report.reason_code_counts
    }
    assert counts["extraction_confidence_watch"] == d("2.000000")
    assert counts["source_reconciliation_watch"] == d("2.000000")

    forged = deepcopy(report.public_payload)
    for item in forged["reason_code_counts"]:
        if item["reason_code"] == "extraction_confidence_watch":
            item["count"] = "1.000000"
    assert not (
        module.validate_research_source_scraping_source_reconciliation_report_public_payload(
            resign(forged),
        )
    )


def test_private_reconciliation_refs_do_not_change_public_payload_or_digest() -> None:
    first = build_report(
        input_row(
            "a-private-authority-source",
            retrieval_tool="generic",
            extraction_confidence=d("0.700000"),
            authority_tier="secondary",
        ),
        input_row(
            "z-private-scraped-source",
            retrieval_tool="scrapling",
        ),
    )
    second = build_report(
        input_row(
            "z-private-authority-source",
            retrieval_tool="generic",
            extraction_confidence=d("0.700000"),
            authority_tier="secondary",
        ),
        input_row(
            "a-private-scraped-source",
            retrieval_tool="scrapling",
        ),
    )

    assert first.public_payload == second.public_payload
    assert first.derived_validation_digest == second.derived_validation_digest


def test_rows_use_canonical_decimal_rank_and_redacted_rank_label() -> None:
    module = api()
    report = build_report(
        input_row("private-pass"),
        input_row(
            "private-block",
            extraction_confidence=d("0.400000"),
        ),
    )

    assert tuple(row.rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
    )
    assert tuple(row.row_label for row in report.rows) == (
        "redacted-source-reconciliation-000001",
        "redacted-source-reconciliation-000002",
    )

    forged = deepcopy(report.public_payload)
    forged["rows"][0]["rank"] = "2.000000"
    forged["rows"][1]["rank"] = "1.000000"
    assert not (
        module.validate_research_source_scraping_source_reconciliation_report_public_payload(
            resign(forged),
        )
    )

    forged = deepcopy(report.public_payload)
    forged["rows"][0]["row_label"] = "redacted-source-reconciliation-999999"
    assert not (
        module.validate_research_source_scraping_source_reconciliation_report_public_payload(
            resign(forged),
        )
    )


def test_decimal_math_is_independent_of_ambient_context() -> None:
    config = cfg()
    row = input_row(
        "hostile-decimal-context",
        captured_at=GENERATED_AT - timedelta(seconds=7200),
        extraction_confidence=d("0.733333"),
        authority_tier="secondary",
        conflict_pressure=d("0.333333"),
        fallback_coverage=d("0.666667"),
    )
    expected = build_report(row, config=config).public_payload

    with localcontext() as hostile_context:
        hostile_context.prec = 4
        hostile_context.traps[Inexact] = True
        actual = build_report(row, config=config).public_payload

    assert actual == expected


def test_public_payload_requires_exact_report_row_and_reason_count_schemas() -> None:
    module = api()
    original = build_report(input_row("schema-pass")).public_payload

    malformed_payloads: list[dict[str, Any]] = []

    malformed = deepcopy(original)
    malformed["unexpected"] = "pass"
    malformed_payloads.append(resign(malformed))

    malformed = deepcopy(original)
    malformed.pop("attention_count")
    malformed_payloads.append(resign(malformed))

    malformed = deepcopy(original)
    malformed["config"]["unexpected"] = "pass"
    malformed_payloads.append(resign(malformed))

    malformed = deepcopy(original)
    malformed["config"].pop("freshness_weight")
    malformed_payloads.append(resign(malformed))

    malformed = deepcopy(original)
    malformed["rows"][0]["unexpected"] = "pass"
    malformed_payloads.append(resign(malformed))

    malformed = deepcopy(original)
    malformed["rows"][0].pop("retrieval_tool")
    malformed_payloads.append(resign(malformed))

    malformed = deepcopy(original)
    malformed["reason_code_counts"][0]["unexpected"] = "pass"
    malformed_payloads.append(resign(malformed))

    malformed = deepcopy(original)
    malformed["reason_code_counts"][0].pop("count")
    malformed_payloads.append(resign(malformed))

    for payload in malformed_payloads:
        assert not (
            module.validate_research_source_scraping_source_reconciliation_report_public_payload(
                payload,
            )
        )


def test_public_payload_uses_exact_canonical_schema_and_sha256() -> None:
    module = api()
    payload = build_report(input_row("canonical-schema")).public_payload

    assert tuple(payload) == (
        "generated_at",
        "config_version",
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "max_extraction_age_seconds",
        "average_freshness_score",
        "average_extraction_confidence_score",
        "average_authority_score",
        "average_conflict_pressure_score",
        "average_fallback_coverage_score",
        "average_reconciliation_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "config",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["rows"][0]) == (
        "row_label",
        "rank",
        "retrieval_tool",
        "extraction_age_seconds",
        "freshness_score",
        "extraction_confidence_score",
        "authority_score",
        "conflict_pressure_score",
        "fallback_coverage_score",
        "reconciliation_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["reason_code_counts"][0]) == (
        "reason_code",
        "count",
        "paper_only",
        "report_only",
        "readonly",
    )
    assert tuple(payload["config"]) == (
        "config_version",
        "fresh_extraction_max_age_seconds",
        "stale_extraction_block_age_seconds",
        "min_extraction_confidence_pass_ratio",
        "min_extraction_confidence_watch_ratio",
        "min_authority_score_pass_ratio",
        "min_authority_score_watch_ratio",
        "max_conflict_pressure_pass_ratio",
        "max_conflict_pressure_watch_ratio",
        "min_fallback_coverage_pass_ratio",
        "min_fallback_coverage_watch_ratio",
        "min_reconciliation_pass_score",
        "min_reconciliation_watch_score",
        "freshness_weight",
        "extraction_confidence_weight",
        "authority_weight",
        "conflict_pressure_weight",
        "fallback_coverage_weight",
        "paper_only",
        "report_only",
        "readonly",
    )
    digest = payload["derived_validation_digest"]
    assert digest == canonical_digest(payload)
    assert len(digest) == 64
    assert digest == digest.lower()

    uppercase = deepcopy(payload)
    uppercase["derived_validation_digest"] = digest.upper()
    assert not (
        module.validate_research_source_scraping_source_reconciliation_report_public_payload(
            uppercase,
        )
    )


def test_resigned_public_payload_rejects_noncanonical_mapping_key_order() -> None:
    module = api()
    payload = build_report(input_row("canonical-key-order")).public_payload

    reordered_payloads = (
        dict(reversed(tuple(payload.items()))),
        {
            **payload,
            "config": dict(reversed(tuple(payload["config"].items()))),
        },
        {
            **payload,
            "rows": [dict(reversed(tuple(payload["rows"][0].items())))],
        },
        {
            **payload,
            "reason_code_counts": [
                dict(reversed(tuple(payload["reason_code_counts"][0].items()))),
            ],
        },
    )

    for reordered in reordered_payloads:
        assert not (
            module.validate_research_source_scraping_source_reconciliation_report_public_payload(
                resign(reordered),
            )
        )


def test_object_setattr_mutations_are_revalidated_at_public_boundaries() -> None:
    module = api()

    invalid_config = cfg()
    object.__setattr__(
        invalid_config,
        "fresh_extraction_max_age_seconds",
        d("86400.000000"),
    )
    with pytest.raises(ValueError, match="fresh_extraction_max_age_seconds"):
        build_report(input_row("mutated-config"), config=invalid_config)

    invalid_input = input_row("mutated-input")
    object.__setattr__(invalid_input, "retrieval_tool", "not-a-retrieval-tool")
    with pytest.raises(ValueError, match="retrieval_tool"):
        build_report(invalid_input)

    report = build_report(input_row("mutated-nested-members"))
    object.__setattr__(report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="row paper_only"):
        _ = report.public_payload

    report = build_report(input_row("mutated-reason-count"))
    object.__setattr__(report.reason_code_counts[0], "readonly", False)
    with pytest.raises(ValueError, match="reason count readonly"):
        _ = report.public_payload


def test_frozen_final_records_reject_object_setattr_shadow_attributes() -> None:
    report = build_report(input_row("shadow-attribute"))

    for record in (
        cfg(),
        input_row(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        with pytest.raises(AttributeError):
            object.__setattr__(record, "unvalidated_shadow", "value")


def test_resigned_public_payload_preserves_phase_one_hard_flags() -> None:
    module = api()
    original = build_report(input_row("flag-pass")).public_payload

    forged_payloads: list[dict[str, Any]] = []
    for field_name in ("paper_only", "report_only", "readonly"):
        forged = deepcopy(original)
        forged[field_name] = False
        forged_payloads.append(resign(forged))

        forged = deepcopy(original)
        forged["config"][field_name] = False
        forged_payloads.append(resign(forged))

        forged = deepcopy(original)
        forged["rows"][0][field_name] = False
        forged_payloads.append(resign(forged))

        forged = deepcopy(original)
        forged["reason_code_counts"][0][field_name] = False
        forged_payloads.append(resign(forged))

    for payload in forged_payloads:
        assert not (
            module.validate_research_source_scraping_source_reconciliation_report_public_payload(
                payload,
            )
        )


def test_decimal_bounds_and_whole_counts_are_checked_before_quantization() -> None:
    module = api()

    with pytest.raises(ValueError, match="between 0 and 1"):
        input_row(extraction_confidence=d("1.0000004"))

    with pytest.raises(ValueError, match="between 0 and 1"):
        input_row(conflict_pressure=d("-0.0000004"))

    with pytest.raises(ValueError, match="whole number"):
        module.ResearchSourceScrapingSourceReconciliationReasonCodeCount(
            reason_code="source_reconciliation_pass",
            count=d("1.0000004"),
        )

    report = build_report(input_row("raw-bound-pass"))
    with pytest.raises(ValueError, match="nonnegative"):
        replace(
            report.rows[0],
            extraction_age_seconds=d("-0.0000004"),
        )


def test_signed_zero_is_rejected_in_records_and_resigned_payloads() -> None:
    module = api()

    with pytest.raises(ValueError, match="signed zero"):
        input_row(extraction_confidence=d("-0"))

    report = build_report(input_row("signed-zero-pass"))
    with pytest.raises(ValueError, match="signed zero"):
        replace(report, attention_count=d("-0"))

    forged = deepcopy(report.public_payload)
    forged["attention_count"] = "-0.000000"
    assert not (
        module.validate_research_source_scraping_source_reconciliation_report_public_payload(
            resign(forged),
        )
    )


@pytest.mark.parametrize("value", ("NaN", "sNaN", "Infinity", "-Infinity"))
def test_non_finite_decimals_are_rejected_in_records_and_resigned_payloads(
    value: str,
) -> None:
    module = api()
    with pytest.raises(ValueError, match="finite"):
        input_row(extraction_confidence=d(value))

    forged = deepcopy(build_report(input_row("finite-pass")).public_payload)
    forged["rows"][0]["reconciliation_score"] = value
    assert not (
        module.validate_research_source_scraping_source_reconciliation_report_public_payload(
            resign(forged),
        )
    )


def test_custom_config_validation_and_thresholds_are_enforced() -> None:
    custom = cfg(
        min_reconciliation_pass_score=d("0.900000"),
        min_reconciliation_watch_score=d("0.650000"),
        max_conflict_pressure_pass_ratio=d("0.100000"),
    )
    report = build_report(
        input_row("custom-threshold", conflict_pressure=d("0.150000")),
        config=custom,
    )

    assert report.status == "watch"
    assert report.rows[0].status == "watch"
    assert report.rows[0].reason_codes == (
        "conflict_pressure_watch",
        "source_reconciliation_watch",
    )
    payload = report.public_payload
    assert payload["config"]["min_reconciliation_pass_score"] == "0.900000"
    assert payload["config"]["min_reconciliation_watch_score"] == "0.650000"
    assert payload["config"]["max_conflict_pressure_pass_ratio"] == "0.100000"
    assert api().validate_research_source_scraping_source_reconciliation_report_public_payload(
        payload,
    )

    forged = deepcopy(payload)
    forged["config"]["max_conflict_pressure_pass_ratio"] = "0.200000"
    assert not (
        api().validate_research_source_scraping_source_reconciliation_report_public_payload(
            resign(forged),
        )
    )

    with pytest.raises(ValueError, match="weights"):
        cfg(freshness_weight=d("0.300000"))
    with pytest.raises(ValueError, match="watch threshold"):
        cfg(min_reconciliation_watch_score=d("0.900000"))
    with pytest.raises(ValueError, match="conflict pressure"):
        cfg(max_conflict_pressure_watch_ratio=d("0.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="must be exactly Decimal"):
        cfg(fallback_coverage_weight=_DecimalSubclass("0.150000"))  # type: ignore[arg-type]


def test_dataclasses_flags_inputs_and_static_surface_are_strict() -> None:
    module = api()
    report = build_report(input_row("a-private-pass"))
    reason_count = report.reason_code_counts[0]

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    for public_record in (
        cfg(),
        input_row(),
        report.rows[0],
        reason_count,
        report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        with pytest.raises(FrozenInstanceError):
            public_record.paper_only = False
        _assert_decimal_public_numbers(public_record)

    with pytest.raises(TypeError):

        class BadInput(module.ResearchSourceScrapingSourceReconciliationInput):
            pass

    for public_class in (
        module.ResearchSourceScrapingSourceReconciliationConfig,
        module.ResearchSourceScrapingSourceReconciliationRow,
        module.ResearchSourceScrapingSourceReconciliationReasonCodeCount,
        module.ResearchSourceScrapingSourceReconciliationReport,
    ):
        with pytest.raises(TypeError, match="subclassing"):
            type("UnsafeSubclass", (public_class,), {})

    with pytest.raises(ValueError, match="report_only"):
        replace(input_row(report_only=True), report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="must be exactly Decimal"):
        input_row(extraction_confidence=_DecimalSubclass("0.900000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be exactly datetime"):
        module.build_research_source_scraping_source_reconciliation_report(
            (input_row(),),
            config=cfg(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(captured_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="utcoffset"):
        input_row(captured_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="cannot be after generated_at"):
        build_report(input_row(captured_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="retrieval_tool"):
        input_row(retrieval_tool="wallet")

    with pytest.raises(ValueError, match="authority_tier"):
        input_row(authority_tier="unknown-tier")

    with pytest.raises(ValueError, match="unique"):
        build_report(input_row("dup"), input_row("dup", retrieval_tool="agent_reach"))

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert imported_roots <= {
        "__future__",
        "collections",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
        "typing",
    }
    assert called_names.isdisjoint(
        {
            "connect",
            "delete",
            "execute",
            "executemany",
            "mkdir",
            "open",
            "post",
            "put",
            "remove",
            "rename",
            "replace_file",
            "request",
            "send",
            "touch",
            "unlink",
            "write",
            "write_bytes",
            "write_text",
        },
    )
    for public_name in module.__all__:
        _assert_payload_has_no_forbidden_surface({"name": public_name})
    for cls in (
        module.ResearchSourceScrapingSourceReconciliationConfig,
        module.ResearchSourceScrapingSourceReconciliationInput,
        module.ResearchSourceScrapingSourceReconciliationRow,
        module.ResearchSourceScrapingSourceReconciliationReasonCodeCount,
        module.ResearchSourceScrapingSourceReconciliationReport,
    ):
        for field in fields(cls):
            _assert_payload_has_no_forbidden_surface({"field": field.name})
