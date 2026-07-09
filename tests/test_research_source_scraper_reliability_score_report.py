from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_scraper_reliability_score_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scraper_reliability_score_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
COLLECTED_AT = datetime(2026, 7, 8, 11, 30, tzinfo=UTC)


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
        "fresh_collection_max_age_seconds": d("3600.000000"),
        "stale_collection_block_age_seconds": d("86400.000000"),
        "min_success_rate_pass_ratio": d("0.900000"),
        "min_success_rate_watch_ratio": d("0.650000"),
        "min_parser_confidence_pass_ratio": d("0.850000"),
        "min_parser_confidence_watch_ratio": d("0.600000"),
        "min_authority_pass_ratio": d("0.800000"),
        "min_authority_watch_ratio": d("0.500000"),
        "min_reliability_pass_score": d("0.800000"),
        "min_reliability_watch_score": d("0.500000"),
        "success_rate_weight": d("0.250000"),
        "freshness_weight": d("0.200000"),
        "parser_confidence_weight": d("0.200000"),
        "authority_weight": d("0.150000"),
        "corroboration_weight": d("0.100000"),
        "completeness_weight": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceScraperReliabilityScoreConfig(**values)


def input_row(
    private_collection_ref: str = "private-collection",
    *,
    collector_family: str = "scrapling",
    collected_at: datetime = COLLECTED_AT,
    scraper_attempt_count: Decimal = d("10"),
    scraper_success_count: Decimal = d("10"),
    parser_confidence_ratio: Decimal = d("0.950000"),
    authority_score: Decimal = d("0.900000"),
    duplicate_corroboration_count: Decimal = d("3"),
    required_corroboration_count: Decimal = d("3"),
    critical_field_count: Decimal = d("5"),
    missing_critical_field_count: Decimal = d("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScraperReliabilityScoreInput(
        private_collection_ref=private_collection_ref,
        collector_family=collector_family,
        collected_at=collected_at,
        scraper_attempt_count=scraper_attempt_count,
        scraper_success_count=scraper_success_count,
        parser_confidence_ratio=parser_confidence_ratio,
        authority_score=authority_score,
        duplicate_corroboration_count=duplicate_corroboration_count,
        required_corroboration_count=required_corroboration_count,
        critical_field_count=critical_field_count,
        missing_critical_field_count=missing_critical_field_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: object, config: object | None = None) -> Any:
    module = api()
    return module.build_research_source_scraper_reliability_score_report(
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
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "table",
        "token",
        "api_key",
        "secret",
        "password",
        "credential",
        "bearer",
        "authentication",
        "authorization",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
        "execution",
        "execute",
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


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = dict(payload)
    resigned["derived_validation_digest"] = canonical_digest(resigned)
    return resigned


def test_empty_input_blocks_with_report_only_digest_and_decimal_payload() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceScraperReliabilityScoreReport
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
    assert report.average_reliability_score == d("0.000000")
    assert report.max_collection_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "scraper_reliability_no_inputs",
        "scraper_reliability_block",
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
    assert module.research_source_scraper_reliability_score_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    assert module.validate_research_source_scraper_reliability_score_report_payload(payload)
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)


def test_report_scores_scraper_success_freshness_parser_authority_duplicates_and_fields() -> None:
    report = build_report(
        input_row("a-private-pass"),
        input_row(
            "b-private-watch",
            collector_family="agent_reach",
            collected_at=GENERATED_AT - timedelta(seconds=7200),
            scraper_success_count=d("7"),
            parser_confidence_ratio=d("0.700000"),
            authority_score=d("0.600000"),
            duplicate_corroboration_count=d("2"),
            missing_critical_field_count=d("1"),
        ),
        input_row(
            "c-private-block",
            collector_family="generic",
            collected_at=GENERATED_AT - timedelta(seconds=90000),
            scraper_attempt_count=d("5"),
            scraper_success_count=d("0"),
            parser_confidence_ratio=d("0.400000"),
            authority_score=d("0.400000"),
            duplicate_corroboration_count=d("0"),
            required_corroboration_count=d("3"),
            critical_field_count=d("4"),
            missing_critical_field_count=d("4"),
        ),
    )

    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.max_collection_age_seconds == d("90000.000000")
    assert report.average_success_rate == d("0.566667")
    assert report.average_freshness_score == d("0.652174")
    assert report.average_parser_confidence_score == d("0.683333")
    assert report.average_authority_score == d("0.633333")
    assert report.average_duplicate_corroboration_score == d("0.555556")
    assert report.average_critical_field_completeness_score == d("0.600000")
    assert report.average_reliability_score == d("0.619324")

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.row_label for row in report.rows) == (
        "redacted-scraper-reliability-000003",
        "redacted-scraper-reliability-000002",
        "redacted-scraper-reliability-000001",
    )

    block_row, watch_row, pass_row = report.rows
    assert block_row.reliability_score == d("0.140000")
    assert block_row.reason_codes == (
        "success_rate_block",
        "freshness_block",
        "parser_confidence_block",
        "authority_block",
        "duplicate_corroboration_block",
        "critical_fields_missing_block",
        "scraper_reliability_block",
    )
    assert watch_row.success_rate == d("0.700000")
    assert watch_row.freshness_score == d("0.956522")
    assert watch_row.duplicate_corroboration_score == d("0.666667")
    assert watch_row.critical_field_completeness_score == d("0.800000")
    assert watch_row.reliability_score == d("0.742971")
    assert watch_row.reason_codes == (
        "success_rate_watch",
        "freshness_watch",
        "parser_confidence_watch",
        "authority_watch",
        "duplicate_corroboration_watch",
        "critical_fields_missing_watch",
        "scraper_reliability_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.reliability_score == d("0.975000")
    assert pass_row.reason_codes == ("scraper_reliability_pass",)


def test_payload_is_deterministic_redacted_digest_validated_and_tool_agnostic() -> None:
    module = api()
    rows = (
        input_row("https://example.invalid/raw_candidate/market_id/token"),
        input_row(
            "postgres://dsn/table/wallet/order/trade/live",
            collector_family="agent_reach",
            scraper_success_count=d("8"),
            parser_confidence_ratio=d("0.800000"),
            duplicate_corroboration_count=d("2"),
            missing_critical_field_count=d("1"),
        ),
    )
    first = build_report(*rows)
    second = build_report(*reversed(rows))

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = first.payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.validate_research_source_scraper_reliability_score_report_payload(payload)
    assert {row["collector_family"] for row in payload["rows"]} == {
        "agent_reach",
        "scrapling",
    }
    assert all(row["row_label"].startswith("redacted-scraper-reliability-") for row in payload["rows"])
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)

    tampered = build_report(*rows)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_scraper_reliability_score_report_payload(tampered)

    unsigned = dict(payload)
    unsigned["status"] = "pass"
    assert not module.validate_research_source_scraper_reliability_score_report_payload(unsigned)

    invalid_status = resign_payload({**payload, "status": "blocked"})
    assert not module.validate_research_source_scraper_reliability_score_report_payload(
        invalid_status,
    )

    invalid_extra_field = resign_payload({**payload, "unmodeled_safe_field": "pass"})
    assert not module.validate_research_source_scraper_reliability_score_report_payload(
        invalid_extra_field,
    )


def test_reason_code_counts_count_repeated_row_reasons() -> None:
    report = build_report(
        input_row("a-private-watch", scraper_success_count=d("8")),
        input_row("b-private-watch", scraper_success_count=d("8")),
    )

    assert report.status == "watch"
    assert tuple((item.reason_code, item.count) for item in report.reason_code_counts) == (
        ("success_rate_watch", d("2.000000")),
        ("scraper_reliability_watch", d("2.000000")),
    )
    assert report.payload["reason_code_counts"] == [
        {
            "reason_code": "success_rate_watch",
            "count": "2.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_code": "scraper_reliability_watch",
            "count": "2.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]


def test_public_identifiers_reject_recommendation_execution_sizing_and_auth_surfaces() -> None:
    module = api()
    safe_row = build_report(input_row("a-private-pass")).rows[0]

    for unsafe_row_label in (
        "recommendation_surface",
        "execution_surface",
        "sizing_surface",
        "authentication_surface",
        "authorization_surface",
        "api_key_surface",
        "secret_surface",
        "password_surface",
        "credential_surface",
        "bearer_surface",
    ):
        with pytest.raises(ValueError, match="unsafe public surface"):
            replace(safe_row, row_label=unsafe_row_label)


def test_dataclasses_are_frozen_flags_and_inputs_are_strict_without_network_imports() -> None:
    module = api()
    report = build_report(input_row("a-private-pass"))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(module.ResearchSourceScraperReliabilityScoreInput):
            pass

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
        input_row(scraper_success_count=_DecimalSubclass("1"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be exactly datetime"):
        build_report(input_row(), config=cfg(),) if False else module.build_research_source_scraper_reliability_score_report(
            (input_row(),),
            config=cfg(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(collected_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="utcoffset"):
        input_row(collected_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="cannot be after generated_at"):
        build_report(input_row(collected_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="success"):
        input_row(scraper_success_count=d("11"), scraper_attempt_count=d("10"))

    with pytest.raises(ValueError, match="missing_critical"):
        input_row(missing_critical_field_count=d("6"), critical_field_count=d("5"))

    with pytest.raises(ValueError, match="weights"):
        cfg(success_rate_weight=d("0.300000"))

    for public_record in (cfg(), input_row(), report):
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
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)
    for public_name in module.__all__:
        _assert_payload_has_no_forbidden_surface({"name": public_name})
    for cls in (
        module.ResearchSourceScraperReliabilityScoreConfig,
        module.ResearchSourceScraperReliabilityScoreRow,
        module.ResearchSourceScraperReliabilityScoreReport,
    ):
        for field in fields(cls):
            _assert_payload_has_no_forbidden_surface({"field": field.name})
