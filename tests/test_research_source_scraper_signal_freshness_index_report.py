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


MODULE_NAME = (
    "polymarket_alpha_lab.research_source_scraper_signal_freshness_index_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scraper_signal_freshness_index_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
SCRAPED_AT = datetime(2026, 7, 8, 11, 45, tzinfo=UTC)


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
        "fresh_scrape_max_age_seconds": d("1800.000000"),
        "stale_scrape_block_age_seconds": d("19800.000000"),
        "min_parser_confidence_pass_ratio": d("0.850000"),
        "min_parser_confidence_watch_ratio": d("0.600000"),
        "min_authority_pass_score": d("0.750000"),
        "min_authority_watch_score": d("0.500000"),
        "min_signal_freshness_pass_index": d("0.800000"),
        "min_signal_freshness_watch_index": d("0.500000"),
        "scrape_recency_weight": d("0.300000"),
        "parser_confidence_weight": d("0.250000"),
        "authority_weight": d("0.150000"),
        "duplicate_corroboration_weight": d("0.100000"),
        "field_completeness_weight": d("0.100000"),
        "fallback_coverage_weight": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceScraperSignalFreshnessIndexConfig(**values)


def signal_input(
    private_signal_ref: str = "private-signal",
    *,
    scraped_at: datetime = SCRAPED_AT,
    parser_confidence_ratio: Decimal = d("0.960000"),
    authority_tier: str = "tier_1",
    duplicate_corroboration_count: Decimal = d("3"),
    required_duplicate_corroboration_count: Decimal = d("3"),
    expected_field_count: Decimal = d("5"),
    missing_field_count: Decimal = d("0"),
    fallback_observed_count: Decimal = d("2"),
    fallback_required_count: Decimal = d("2"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScraperSignalFreshnessIndexInput(
        private_signal_ref=private_signal_ref,
        scraped_at=scraped_at,
        parser_confidence_ratio=parser_confidence_ratio,
        authority_tier=authority_tier,
        duplicate_corroboration_count=duplicate_corroboration_count,
        required_duplicate_corroboration_count=required_duplicate_corroboration_count,
        expected_field_count=expected_field_count,
        missing_field_count=missing_field_count,
        fallback_observed_count=fallback_observed_count,
        fallback_required_count=fallback_required_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: object, config: object | None = None) -> Any:
    module = api()
    return module.build_research_source_scraper_signal_freshness_index_report(
        items,
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
        "://",
        "www.",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
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


def redigest(payload: dict[str, Any]) -> dict[str, Any]:
    candidate = json.loads(json.dumps(payload))
    candidate["derived_validation_digest"] = canonical_digest(candidate)
    return candidate


def test_empty_input_blocks_with_report_only_digest_and_decimal_payload() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceScraperSignalFreshnessIndexReport
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
    assert report.average_signal_freshness_index == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "signal_freshness_no_inputs",
        "signal_freshness_index_block",
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
    assert module.research_source_scraper_signal_freshness_index_report_digest(
        report,
    ) == payload["derived_validation_digest"]
    assert module.validate_research_source_scraper_signal_freshness_index_report_payload(
        payload,
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)


def test_scores_scrape_recency_parser_authority_duplicates_fields_and_fallbacks() -> None:
    report = build_report(
        signal_input("a-private-pass"),
        signal_input(
            "b-private-watch",
            scraped_at=GENERATED_AT - timedelta(seconds=5400),
            parser_confidence_ratio=d("0.700000"),
            authority_tier="tier_2",
            duplicate_corroboration_count=d("1"),
            required_duplicate_corroboration_count=d("2"),
            expected_field_count=d("4"),
            missing_field_count=d("1"),
            fallback_observed_count=d("1"),
            fallback_required_count=d("2"),
        ),
        signal_input(
            "c-private-block",
            scraped_at=GENERATED_AT - timedelta(seconds=25200),
            parser_confidence_ratio=d("0.400000"),
            authority_tier="tier_4",
            duplicate_corroboration_count=d("0"),
            required_duplicate_corroboration_count=d("2"),
            expected_field_count=d("4"),
            missing_field_count=d("4"),
            fallback_observed_count=d("0"),
            fallback_required_count=d("1"),
        ),
    )

    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.max_scrape_age_seconds == d("25200.000000")
    assert report.average_scrape_recency_score == d("0.600000")
    assert report.average_parser_confidence_score == d("0.686667")
    assert report.average_authority_score == d("0.666667")
    assert report.average_duplicate_corroboration_score == d("0.500000")
    assert report.average_field_completeness_score == d("0.583333")
    assert report.average_fallback_coverage_score == d("0.500000")
    assert report.average_signal_freshness_index == d("0.610000")

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.row_label for row in report.rows) == (
        "redacted-scraper-signal-freshness-000003",
        "redacted-scraper-signal-freshness-000002",
        "redacted-scraper-signal-freshness-000001",
    )

    block_row, watch_row, pass_row = report.rows
    assert block_row.signal_freshness_index == d("0.137500")
    assert block_row.reason_codes == (
        "scrape_recency_block",
        "parser_confidence_block",
        "authority_tier_block",
        "duplicate_corroboration_block",
        "missing_fields_block",
        "fallback_coverage_block",
        "signal_freshness_index_block",
    )
    assert watch_row.scrape_recency_score == d("0.800000")
    assert watch_row.authority_score == d("0.750000")
    assert watch_row.duplicate_corroboration_score == d("0.500000")
    assert watch_row.field_completeness_score == d("0.750000")
    assert watch_row.fallback_coverage_score == d("0.500000")
    assert watch_row.signal_freshness_index == d("0.702500")
    assert watch_row.reason_codes == (
        "scrape_recency_watch",
        "parser_confidence_watch",
        "duplicate_corroboration_watch",
        "missing_fields_watch",
        "fallback_coverage_watch",
        "signal_freshness_index_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.signal_freshness_index == d("0.990000")
    assert pass_row.reason_codes == ("signal_freshness_index_pass",)


def test_payload_is_deterministic_redacted_and_digest_validated() -> None:
    module = api()
    inputs = (
        signal_input("https://example.invalid/raw_candidate/market_id/token"),
        signal_input(
            "postgres://dsn/table/wallet/order/trade/live/source_text",
            scraped_at=GENERATED_AT - timedelta(seconds=3600),
            parser_confidence_ratio=d("0.800000"),
            authority_tier="tier_2",
            duplicate_corroboration_count=d("1"),
            required_duplicate_corroboration_count=d("2"),
            missing_field_count=d("1"),
        ),
    )
    first = build_report(*inputs)
    second = build_report(*reversed(inputs))

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = first.payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.validate_research_source_scraper_signal_freshness_index_report_payload(
        payload,
    )
    assert all(
        row["row_label"].startswith("redacted-scraper-signal-freshness-")
        for row in payload["rows"]
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)

    tampered = build_report(*inputs)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_scraper_signal_freshness_index_report_payload(tampered)

    unsigned = dict(payload)
    unsigned["status"] = "pass"
    assert not module.validate_research_source_scraper_signal_freshness_index_report_payload(
        unsigned,
    )


def test_payload_validator_rejects_noncanonical_or_wrong_schema() -> None:
    module = api()
    payload = build_report(signal_input("strict-schema-private-ref")).payload

    extra_report_field = json.loads(json.dumps(payload))
    extra_report_field["extra"] = "safe"

    missing_report_field = json.loads(json.dumps(payload))
    missing_report_field.pop("attention_count")

    downgraded_flag = json.loads(json.dumps(payload))
    downgraded_flag["readonly"] = False

    noncanonical_decimal = json.loads(json.dumps(payload))
    noncanonical_decimal["input_count"] = "1"

    raw_numeric = json.loads(json.dumps(payload))
    raw_numeric["input_count"] = 1

    malformed_rows = json.loads(json.dumps(payload))
    malformed_rows["rows"] = {}

    extra_row_field = json.loads(json.dumps(payload))
    extra_row_field["rows"][0]["extra"] = "safe"

    missing_row_field = json.loads(json.dumps(payload))
    missing_row_field["rows"][0].pop("authority_score")

    wrong_row_order = json.loads(json.dumps(build_report(
        signal_input("a-private"),
        signal_input(
            "b-private",
            parser_confidence_ratio=d("0.700000"),
        ),
    ).payload))
    wrong_row_order["rows"].reverse()

    for candidate in (
        extra_report_field,
        missing_report_field,
        downgraded_flag,
        noncanonical_decimal,
        raw_numeric,
        malformed_rows,
        extra_row_field,
        missing_row_field,
        wrong_row_order,
    ):
        assert not module.validate_research_source_scraper_signal_freshness_index_report_payload(
            redigest(candidate),
        )


def test_public_records_reject_inconsistent_manual_construction() -> None:
    report = build_report(signal_input("manual-construction-private-ref"))
    row = report.rows[0]

    with pytest.raises(ValueError, match="config_version"):
        replace(report, config_version="unsupported-version")

    with pytest.raises(ValueError, match="row_label"):
        replace(row, row_label="arbitrary-row")

    with pytest.raises(ValueError, match="authority_score"):
        replace(row, authority_score=d("0.500000"))

    with pytest.raises(ValueError, match="status reason"):
        replace(row, status="watch")


def test_frozen_strict_report_only_module_without_io_surfaces() -> None:
    module = api()
    report = build_report(signal_input("a-private-pass"))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(module.ResearchSourceScraperSignalFreshnessIndexInput):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(signal_input(report_only=True), report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(report, status="blocked")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="must be exactly Decimal"):
        signal_input(parser_confidence_ratio=_DecimalSubclass("0.900000"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be exactly datetime"):
        module.build_research_source_scraper_signal_freshness_index_report(
            (signal_input(),),
            config=cfg(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        signal_input(scraped_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="utcoffset"):
        signal_input(scraped_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="cannot be after generated_at"):
        build_report(signal_input(scraped_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="missing_field_count"):
        signal_input(missing_field_count=d("6"), expected_field_count=d("5"))

    with pytest.raises(ValueError, match="fallback_observed_count"):
        signal_input(fallback_observed_count=d("3"), fallback_required_count=d("2"))

    with pytest.raises(ValueError, match="authority_tier"):
        signal_input(authority_tier="market_slug")

    with pytest.raises(ValueError, match="weights"):
        cfg(scrape_recency_weight=d("0.350000"))

    for public_record in (cfg(), signal_input(), report):
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
        "boto3",
        "os",
        "pathlib",
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)
    forbidden_calls = {
        "open",
        "urlopen",
    }
    assert {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }.isdisjoint(forbidden_calls)
    for cls in (
        module.ResearchSourceScraperSignalFreshnessIndexConfig,
        module.ResearchSourceScraperSignalFreshnessIndexInput,
        module.ResearchSourceScraperSignalFreshnessIndexRow,
        module.ResearchSourceScraperSignalFreshnessIndexReasonCodeCount,
        module.ResearchSourceScraperSignalFreshnessIndexReport,
    ):
        for field in fields(cls):
            _assert_payload_has_no_forbidden_surface({"field": field.name})

    public_names = tuple(module.__all__)
    for forbidden in (
        "allocation",
        "position_size",
        "recommend",
        "sizing",
    ):
        assert all(forbidden not in name.casefold() for name in public_names)
