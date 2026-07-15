from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Context, Decimal, Inexact, localcontext
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_source_scraper_evidence_gap_decay_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scraper_evidence_gap_decay_report.py"
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
        "fresh_evidence_max_age_seconds": d("3600.000000"),
        "stale_evidence_block_age_seconds": d("86400.000000"),
        "recheck_due_after_seconds": d("7200.000000"),
        "recheck_block_after_seconds": d("86400.000000"),
        "min_coverage_pass_ratio": d("0.900000"),
        "min_coverage_watch_ratio": d("0.650000"),
        "min_primary_coverage_pass_ratio": d("0.800000"),
        "min_primary_coverage_watch_ratio": d("0.500000"),
        "min_parser_confidence_pass_ratio": d("0.850000"),
        "min_parser_confidence_watch_ratio": d("0.600000"),
        "watch_gap_decay_score": d("0.350000"),
        "block_gap_decay_score": d("0.700000"),
        "evidence_age_weight": d("0.300000"),
        "coverage_gap_weight": d("0.300000"),
        "primary_gap_weight": d("0.200000"),
        "parser_gap_weight": d("0.100000"),
        "recheck_gap_weight": d("0.100000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceScraperEvidenceGapDecayConfig(**values)


def input_row(
    private_evidence_ref: str = "private-evidence",
    *,
    scraper_family: str = "scrapling",
    observed_at: datetime = OBSERVED_AT,
    last_rechecked_at: datetime = OBSERVED_AT,
    expected_evidence_count: Decimal = d("5"),
    observed_evidence_count: Decimal = d("5"),
    primary_evidence_count: Decimal = d("5"),
    parser_confidence_ratio: Decimal = d("0.950000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScraperEvidenceGapDecayInput(
        private_evidence_ref=private_evidence_ref,
        scraper_family=scraper_family,
        observed_at=observed_at,
        last_rechecked_at=last_rechecked_at,
        expected_evidence_count=expected_evidence_count,
        observed_evidence_count=observed_evidence_count,
        primary_evidence_count=primary_evidence_count,
        parser_confidence_ratio=parser_confidence_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: object, config: object | None = None) -> Any:
    module = api()
    return module.build_research_source_scraper_evidence_gap_decay_report(
        rows,
        config=config or cfg(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


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


def test_empty_input_blocks_with_report_only_digest_and_decimal_payload() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceScraperEvidenceGapDecayReport
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
    assert report.average_gap_decay_score == d("0.000000")
    assert report.max_evidence_age_seconds == d("0.000000")
    assert report.max_recheck_age_seconds == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "scraper_evidence_gap_decay_no_inputs",
        "scraper_evidence_gap_decay_block",
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
    assert module.research_source_scraper_evidence_gap_decay_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    assert module.validate_research_source_scraper_evidence_gap_decay_report_payload(payload)
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)


def test_report_scores_gap_decay_ranks_rows_and_counts_reasons() -> None:
    report = build_report(
        input_row("a-private-pass"),
        input_row(
            "b-private-watch",
            scraper_family="agent_reach",
            observed_at=GENERATED_AT - timedelta(seconds=7200),
            last_rechecked_at=GENERATED_AT - timedelta(seconds=10800),
            observed_evidence_count=d("4"),
            primary_evidence_count=d("3"),
            parser_confidence_ratio=d("0.700000"),
        ),
        input_row(
            "c-private-block",
            scraper_family="generic",
            observed_at=GENERATED_AT - timedelta(seconds=90000),
            last_rechecked_at=GENERATED_AT - timedelta(seconds=90000),
            observed_evidence_count=d("0"),
            primary_evidence_count=d("0"),
            parser_confidence_ratio=d("0.300000"),
        ),
    )

    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.max_evidence_age_seconds == d("90000.000000")
    assert report.max_recheck_age_seconds == d("90000.000000")
    assert report.average_coverage_ratio == d("0.600000")
    assert report.average_primary_coverage_ratio == d("0.533333")
    assert report.average_parser_confidence_ratio == d("0.650000")
    assert report.average_gap_decay_score == d("0.387530")

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.row_label for row in report.rows) == (
        "redacted-evidence-gap-decay-000003",
        "redacted-evidence-gap-decay-000002",
        "redacted-evidence-gap-decay-000001",
    )

    block_row, watch_row, pass_row = report.rows
    assert block_row.gap_decay_score == d("0.970000")
    assert block_row.reason_codes == (
        "evidence_age_decay_block",
        "coverage_gap_block",
        "primary_evidence_gap_block",
        "parser_confidence_gap_block",
        "recheck_gap_block",
        "scraper_evidence_gap_decay_block",
    )
    assert watch_row.evidence_age_decay_score == d("0.043478")
    assert watch_row.coverage_ratio == d("0.800000")
    assert watch_row.primary_coverage_ratio == d("0.600000")
    assert watch_row.recheck_gap_score == d("0.045455")
    assert watch_row.gap_decay_score == d("0.187589")
    assert watch_row.reason_codes == (
        "evidence_age_decay_watch",
        "coverage_gap_watch",
        "primary_evidence_gap_watch",
        "parser_confidence_gap_watch",
        "recheck_gap_watch",
        "scraper_evidence_gap_decay_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.gap_decay_score == d("0.005000")
    assert pass_row.reason_codes == ("scraper_evidence_gap_decay_pass",)

    reason_counts = {item.reason_code: item.count for item in report.reason_code_counts}
    assert reason_counts["coverage_gap_watch"] == d("1.000000")
    assert reason_counts["coverage_gap_block"] == d("1.000000")
    assert reason_counts["scraper_evidence_gap_decay_block"] == d("2.000000")


def test_payload_is_deterministic_redacted_and_digest_validated() -> None:
    module = api()
    rows = (
        input_row("https://example.invalid/raw_candidate/market_id/token"),
        input_row(
            "postgres://dsn/table/wallet/order/trade/live",
            scraper_family="agent_reach",
            observed_evidence_count=d("4"),
            primary_evidence_count=d("2"),
            parser_confidence_ratio=d("0.800000"),
        ),
    )
    first = build_report(*rows)
    second = build_report(*reversed(rows))

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = first.payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.validate_research_source_scraper_evidence_gap_decay_report_payload(payload)
    assert {row["scraper_family"] for row in payload["rows"]} == {
        "agent_reach",
        "scrapling",
    }
    assert all(row["row_label"].startswith("redacted-evidence-gap-decay-") for row in payload["rows"])
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)

    tampered = build_report(*rows)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_scraper_evidence_gap_decay_report_payload(tampered)

    unsigned = dict(payload)
    unsigned["status"] = "pass"
    assert not module.validate_research_source_scraper_evidence_gap_decay_report_payload(unsigned)


def test_dataclasses_are_frozen_strict_and_imports_are_report_only() -> None:
    module = api()
    report = build_report(input_row("a-private-pass"))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(module.ResearchSourceScraperEvidenceGapDecayInput):
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
        input_row(observed_evidence_count=_DecimalSubclass("1"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be exactly datetime"):
        module.build_research_source_scraper_evidence_gap_decay_report(
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

    with pytest.raises(ValueError, match="observed_evidence_count"):
        input_row(observed_evidence_count=d("6"), expected_evidence_count=d("5"))

    with pytest.raises(ValueError, match="primary_evidence_count"):
        input_row(primary_evidence_count=d("6"), observed_evidence_count=d("5"))

    with pytest.raises(ValueError, match="weights"):
        cfg(evidence_age_weight=d("0.400000"))

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
        module.ResearchSourceScraperEvidenceGapDecayConfig,
        module.ResearchSourceScraperEvidenceGapDecayRow,
        module.ResearchSourceScraperEvidenceGapDecayReport,
    ):
        for field in fields(cls):
            _assert_payload_has_no_forbidden_surface({"field": field.name})


def test_rejects_out_of_range_raw_decimals_canonicalizes_signed_zero_and_uses_fixed_context() -> None:
    with pytest.raises(ValueError, match="parser_confidence_ratio"):
        input_row(parser_confidence_ratio=d("1.0000001"))

    with pytest.raises(ValueError, match="observed_evidence_count"):
        input_row(observed_evidence_count=d("-0.0000001"))

    zero_input = input_row(
        observed_evidence_count=d("-0.000000"),
        primary_evidence_count=d("0"),
    )
    assert zero_input.observed_evidence_count == d("0.000000")
    assert zero_input.observed_evidence_count.as_tuple().sign == 0


def test_uses_fixed_decimal_context_for_gap_decay_calculation() -> None:
    row = input_row(
        observed_evidence_count=d("4"),
        primary_evidence_count=d("3"),
        parser_confidence_ratio=d("0.700000"),
        observed_at=GENERATED_AT - timedelta(seconds=7200),
        last_rechecked_at=GENERATED_AT - timedelta(seconds=10800),
    )
    config = cfg()
    with localcontext(Context(prec=1, traps=[Inexact])):
        report = build_report(row, config=config)
    assert report.average_gap_decay_score == d("0.187589")


def test_revalidates_object_setattr_mutations_at_all_public_boundaries() -> None:
    module = api()

    mutated_config = cfg()
    object.__setattr__(mutated_config, "min_coverage_pass_ratio", d("1.000001"))
    with pytest.raises(ValueError, match="min_coverage_pass_ratio"):
        build_report(input_row(), config=mutated_config)

    mutated_input = input_row()
    object.__setattr__(mutated_input, "primary_evidence_count", d("6.000000"))
    with pytest.raises(ValueError, match="primary_evidence_count"):
        build_report(mutated_input)

    mutated_row_report = build_report(input_row())
    object.__setattr__(mutated_row_report.rows[0], "coverage_gap_score", d("0.100000"))
    with pytest.raises(ValueError, match="coverage_gap_score"):
        module.research_source_scraper_evidence_gap_decay_report_payload(mutated_row_report)

    mutated_count_report = build_report(input_row())
    object.__setattr__(
        mutated_count_report.reason_code_counts[0],
        "count",
        d("1"),
    )
    with pytest.raises(ValueError, match="reason count"):
        module.research_source_scraper_evidence_gap_decay_report_payload(mutated_count_report)


def test_payload_reconstruction_rejects_resigned_semantic_tampering() -> None:
    module = api()
    report = build_report(
        input_row(
            observed_evidence_count=d("0"),
            primary_evidence_count=d("0"),
            parser_confidence_ratio=d("0.300000"),
            observed_at=GENERATED_AT - timedelta(seconds=90000),
            last_rechecked_at=GENERATED_AT - timedelta(seconds=90000),
        ),
    )
    tampered = json.loads(json.dumps(report.payload))
    tampered["status"] = "pass"
    tampered["derived_validation_digest"] = canonical_digest(tampered)

    assert not module.validate_research_source_scraper_evidence_gap_decay_report_payload(
        tampered,
    )


def test_payload_requires_exact_schema_key_order_and_row_order() -> None:
    module = api()
    report = build_report(
        input_row("pass-row"),
        input_row(
            "block-row",
            observed_evidence_count=d("0"),
            primary_evidence_count=d("0"),
            parser_confidence_ratio=d("0.300000"),
            observed_at=GENERATED_AT - timedelta(seconds=90000),
            last_rechecked_at=GENERATED_AT - timedelta(seconds=90000),
        ),
    )
    payload = report.payload
    reordered = {"status": payload["status"]}
    reordered.update(payload)
    reordered["derived_validation_digest"] = canonical_digest(reordered)
    assert not module.validate_research_source_scraper_evidence_gap_decay_report_payload(
        reordered,
    )

    object.__setattr__(report, "rows", tuple(reversed(report.rows)))
    with pytest.raises(ValueError):
        module.research_source_scraper_evidence_gap_decay_report_payload(report)


def test_payload_reconstruction_rederives_scores_reasons_counts_and_aggregates() -> None:
    module = api()
    report = build_report(
        input_row("pass-row"),
        input_row(
            "block-row",
            observed_evidence_count=d("0"),
            primary_evidence_count=d("0"),
            parser_confidence_ratio=d("0.300000"),
            observed_at=GENERATED_AT - timedelta(seconds=90000),
            last_rechecked_at=GENERATED_AT - timedelta(seconds=90000),
        ),
    )

    def resigned(mutator: Any) -> dict[str, Any]:
        payload = json.loads(json.dumps(report.payload))
        mutator(payload)
        payload["derived_validation_digest"] = canonical_digest(payload)
        return payload

    invalid_payloads = (
        resigned(lambda payload: payload["rows"][0].update({"gap_decay_score": "0.000000"})),
        resigned(
            lambda payload: payload["rows"][0].update(
                {"reason_codes": ["scraper_evidence_gap_decay_pass"]},
            ),
        ),
        resigned(lambda payload: payload["reason_code_counts"][0].update({"count": "9.000000"})),
        resigned(lambda payload: payload.update({"average_gap_decay_score": "0.000000"})),
    )
    for payload in invalid_payloads:
        assert not module.validate_research_source_scraper_evidence_gap_decay_report_payload(
            payload,
        )

    nested_reordered = json.loads(json.dumps(report.payload))
    row = nested_reordered["rows"][0]
    nested_reordered["rows"][0] = {"status": row["status"], **row}
    nested_reordered["derived_validation_digest"] = canonical_digest(nested_reordered)
    assert not module.validate_research_source_scraper_evidence_gap_decay_report_payload(
        nested_reordered,
    )


def test_public_dataclasses_are_all_frozen_exact_type_final_and_tie_breaks_are_stable() -> None:
    module = api()
    report = build_report(
        input_row("same-ref", scraper_family="scrapling"),
        input_row("same-ref", scraper_family="agent_reach"),
        input_row("same-ref", scraper_family="generic"),
    )
    reversed_report = build_report(
        input_row("same-ref", scraper_family="generic"),
        input_row("same-ref", scraper_family="scrapling"),
        input_row("same-ref", scraper_family="agent_reach"),
    )

    assert report == reversed_report
    assert tuple(row.scraper_family for row in report.rows) == (
        "agent_reach",
        "generic",
        "scrapling",
    )
    public_records = (
        cfg(),
        input_row(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    )
    for record in public_records:
        assert type(record) in {
            module.ResearchSourceScraperEvidenceGapDecayConfig,
            module.ResearchSourceScraperEvidenceGapDecayInput,
            module.ResearchSourceScraperEvidenceGapDecayRow,
            module.ResearchSourceScraperEvidenceGapDecayReasonCodeCount,
            module.ResearchSourceScraperEvidenceGapDecayReport,
        }
        assert record.__dataclass_params__.frozen
        with pytest.raises(TypeError):
            type(f"Bad{type(record).__name__}", (type(record),), {})
