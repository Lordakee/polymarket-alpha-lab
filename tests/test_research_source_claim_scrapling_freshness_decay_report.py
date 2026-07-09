from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_source_claim_scrapling_freshness_decay_report import (
    RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_STATUSES,
    ResearchSourceClaimScraplingFreshnessDecayConfig,
    ResearchSourceClaimScraplingFreshnessDecayInput,
    ResearchSourceClaimScraplingFreshnessDecayReport,
    ResearchSourceClaimScraplingFreshnessDecayRow,
    build_research_source_claim_scrapling_freshness_decay_report,
    research_source_claim_scrapling_freshness_decay_report_digest,
    research_source_claim_scrapling_freshness_decay_report_payload,
    validate_research_source_claim_scrapling_freshness_decay_report_digest,
    validate_research_source_claim_scrapling_freshness_decay_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_claim_scrapling_freshness_decay_report.py"
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


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchSourceClaimScraplingFreshnessDecayConfig:
    values = {
        "fresh_claim_max_age_seconds": d("3600.000000"),
        "decayed_claim_watch_age_seconds": d("21600.000000"),
        "decayed_claim_block_age_seconds": d("86400.000000"),
        "min_scrapling_confidence_pass_ratio": d("0.850000"),
        "min_scrapling_confidence_watch_ratio": d("0.600000"),
        "min_claim_support_pass_ratio": d("0.800000"),
        "min_claim_support_watch_ratio": d("0.500000"),
        "min_authority_alignment_pass_ratio": d("0.750000"),
        "min_authority_alignment_watch_ratio": d("0.500000"),
        "max_contradiction_watch_pressure": d("0.150000"),
        "max_contradiction_block_pressure": d("0.400000"),
        "min_freshness_decay_pass_score": d("0.800000"),
        "min_freshness_decay_watch_score": d("0.500000"),
        "freshness_weight": d("0.300000"),
        "scrapling_confidence_weight": d("0.250000"),
        "claim_support_weight": d("0.200000"),
        "authority_alignment_weight": d("0.150000"),
        "contradiction_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchSourceClaimScraplingFreshnessDecayConfig(**values)


def input_row(
    private_candidate_ref: str = "private-candidate",
    *,
    observed_at: datetime = OBSERVED_AT,
    scrapling_confidence_ratio: Decimal = d("0.950000"),
    supporting_source_count: Decimal = d("4"),
    independent_source_count: Decimal = d("4"),
    authority_alignment_ratio: Decimal = d("0.900000"),
    contradiction_flag_count: Decimal = d("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSourceClaimScraplingFreshnessDecayInput:
    return ResearchSourceClaimScraplingFreshnessDecayInput(
        private_candidate_ref=private_candidate_ref,
        observed_at=observed_at,
        scrapling_confidence_ratio=scrapling_confidence_ratio,
        supporting_source_count=supporting_source_count,
        independent_source_count=independent_source_count,
        authority_alignment_ratio=authority_alignment_ratio,
        contradiction_flag_count=contradiction_flag_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchSourceClaimScraplingFreshnessDecayInput,
    cfg: ResearchSourceClaimScraplingFreshnessDecayConfig | None = None,
) -> ResearchSourceClaimScraplingFreshnessDecayReport:
    return build_research_source_claim_scrapling_freshness_decay_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _walk_payload_values(value: object) -> list[object]:
    values = [value]
    if type(value) is dict:
        for key, item in value.items():
            values.extend(_walk_payload_values(key))
            values.extend(_walk_payload_values(item))
    elif type(value) is list:
        for item in value:
            values.extend(_walk_payload_values(item))
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
    rendered_values = [str(value).casefold() for value in _walk_payload_values(payload)]
    for forbidden in (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "http://",
        "https://",
        "www.",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommend",
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


def _assert_no_signed_zero_decimals(value: object) -> None:
    if type(value) is Decimal:
        assert not (value.is_zero() and value.is_signed())
        return
    if type(value) is tuple:
        for item in value:
            _assert_no_signed_zero_decimals(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_signed_zero_decimals(getattr(value, field.name))


def test_empty_report_blocks_with_digest_flags_and_decimal_payload() -> None:
    decay_report = report()

    assert type(decay_report) is ResearchSourceClaimScraplingFreshnessDecayReport
    assert is_dataclass(decay_report)
    assert decay_report.__dataclass_params__.frozen
    assert decay_report.generated_at == GENERATED_AT
    assert decay_report.status == "block"
    assert decay_report.input_count == d("0.000000")
    assert decay_report.row_count == d("0.000000")
    assert decay_report.pass_count == d("0.000000")
    assert decay_report.watch_count == d("0.000000")
    assert decay_report.block_count == d("0.000000")
    assert decay_report.attention_count == d("0.000000")
    assert decay_report.max_claim_age_seconds == d("0.000000")
    assert decay_report.average_freshness_decay_score == d("0.000000")
    assert decay_report.rows == ()
    assert decay_report.reason_codes == (
        "scrapling_claim_freshness_decay_no_inputs",
        "scrapling_claim_freshness_decay_block",
    )
    assert decay_report.paper_only is True
    assert decay_report.report_only is True
    assert decay_report.readonly is True
    _assert_decimal_public_numbers(decay_report)

    payload = decay_report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["status"] == "block"
    assert payload["rows"] == []
    assert payload["input_count"] == "0.000000"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert (
        research_source_claim_scrapling_freshness_decay_report_digest(decay_report)
        == payload["derived_validation_digest"]
    )
    validate_research_source_claim_scrapling_freshness_decay_report_digest(decay_report)
    assert validate_research_source_claim_scrapling_freshness_decay_report_payload(
        payload,
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)


def test_report_scores_claim_freshness_confidence_support_and_contradictions() -> None:
    decay_report = report(
        input_row("a-private-pass"),
        input_row(
            "b-private-watch",
            observed_at=GENERATED_AT - timedelta(seconds=7200),
            scrapling_confidence_ratio=d("0.700000"),
            independent_source_count=d("2"),
            authority_alignment_ratio=d("0.600000"),
            contradiction_flag_count=d("1"),
        ),
        input_row(
            "c-private-block",
            observed_at=GENERATED_AT - timedelta(seconds=90000),
            scrapling_confidence_ratio=d("0.400000"),
            independent_source_count=d("0"),
            authority_alignment_ratio=d("0.400000"),
            contradiction_flag_count=d("4"),
        ),
    )

    assert decay_report.status == "block"
    assert decay_report.input_count == d("3.000000")
    assert decay_report.pass_count == d("1.000000")
    assert decay_report.watch_count == d("1.000000")
    assert decay_report.block_count == d("1.000000")
    assert decay_report.attention_count == d("2.000000")
    assert decay_report.max_claim_age_seconds == d("90000.000000")
    assert decay_report.average_claim_freshness_score == d("0.652174")
    assert decay_report.average_scrapling_confidence_score == d("0.683333")
    assert decay_report.average_claim_support_ratio == d("0.500000")
    assert decay_report.average_authority_alignment_score == d("0.633333")
    assert decay_report.average_contradiction_pressure_score == d("0.416667")
    assert decay_report.average_freshness_decay_score == d("0.619819")

    assert tuple(row.status for row in decay_report.rows) == ("block", "watch", "pass")
    assert tuple(row.row_label for row in decay_report.rows) == (
        "redacted-scrapling-claim-freshness-000003",
        "redacted-scrapling-claim-freshness-000002",
        "redacted-scrapling-claim-freshness-000001",
    )

    block_row, watch_row, pass_row = decay_report.rows
    assert type(block_row) is ResearchSourceClaimScraplingFreshnessDecayRow
    assert block_row.claim_age_seconds == d("90000.000000")
    assert block_row.claim_freshness_score == d("0.000000")
    assert block_row.freshness_decay_score == d("0.160000")
    assert block_row.reason_codes == (
        "claim_age_block",
        "scrapling_confidence_block",
        "claim_support_block",
        "authority_alignment_block",
        "contradiction_pressure_block",
        "scrapling_claim_freshness_decay_block",
    )

    assert watch_row.claim_age_seconds == d("7200.000000")
    assert watch_row.claim_freshness_score == d("0.956522")
    assert watch_row.claim_support_ratio == d("0.500000")
    assert watch_row.contradiction_pressure_score == d("0.250000")
    assert watch_row.freshness_decay_score == d("0.726957")
    assert watch_row.reason_codes == (
        "claim_age_watch",
        "scrapling_confidence_watch",
        "claim_support_watch",
        "authority_alignment_watch",
        "contradiction_pressure_watch",
        "scrapling_claim_freshness_decay_watch",
    )

    assert pass_row.status == "pass"
    assert pass_row.freshness_decay_score == d("0.972500")
    assert pass_row.reason_codes == ("scrapling_claim_freshness_decay_pass",)


def test_reason_code_counts_reflect_row_occurrences_not_presence_flags() -> None:
    decay_report = report(
        input_row("a-private-pass"),
        input_row("b-private-pass"),
    )

    assert decay_report.reason_codes == ("scrapling_claim_freshness_decay_pass",)
    assert tuple(
        (item.reason_code, item.count)
        for item in decay_report.reason_code_counts
    ) == (("scrapling_claim_freshness_decay_pass", d("2.000000")),)


def test_payload_is_deterministic_redacted_and_digest_validated() -> None:
    rows = (
        input_row("https://example.invalid/raw_candidate/market_id/token"),
        input_row(
            "postgres://dsn/table_name/wallet/order/trade/live",
            scrapling_confidence_ratio=d("0.800000"),
            independent_source_count=d("2"),
            authority_alignment_ratio=d("0.800000"),
            contradiction_flag_count=d("1"),
        ),
    )
    first = report(*rows)
    second = report(*reversed(rows))

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = research_source_claim_scrapling_freshness_decay_report_payload(first)
    assert payload == research_source_claim_scrapling_freshness_decay_report_payload(first)
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert validate_research_source_claim_scrapling_freshness_decay_report_payload(
        payload,
    )
    assert all(
        row["row_label"].startswith("redacted-scrapling-claim-freshness-")
        for row in payload["rows"]
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)

    tampered_report = report(*rows)
    object.__setattr__(tampered_report, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_source_claim_scrapling_freshness_decay_report_payload(tampered_report)

    tampered_payload = dict(payload)
    tampered_payload["status"] = "pass"
    assert not validate_research_source_claim_scrapling_freshness_decay_report_payload(
        tampered_payload,
    )


def test_payload_validation_rejects_schema_tampering_with_matching_digest() -> None:
    payload = research_source_claim_scrapling_freshness_decay_report_payload(
        report(input_row("a-private-pass")),
    )

    extra_top_level_payload = dict(payload)
    extra_top_level_payload["safe_extra"] = "redacted_extra"
    extra_top_level_payload["derived_validation_digest"] = canonical_digest(
        extra_top_level_payload,
    )

    missing_rows_payload = dict(payload)
    missing_rows_payload.pop("rows")
    missing_rows_payload["derived_validation_digest"] = canonical_digest(
        missing_rows_payload,
    )

    wrong_rows_type_payload = dict(payload)
    wrong_rows_type_payload["rows"] = "redacted_rows"
    wrong_rows_type_payload["derived_validation_digest"] = canonical_digest(
        wrong_rows_type_payload,
    )

    extra_row_field_payload = json.loads(json.dumps(payload))
    extra_row_field_payload["rows"][0]["safe_extra"] = "redacted_extra"
    extra_row_field_payload["derived_validation_digest"] = canonical_digest(
        extra_row_field_payload,
    )

    for tampered_payload in (
        extra_top_level_payload,
        missing_rows_payload,
        wrong_rows_type_payload,
        extra_row_field_payload,
    ):
        assert not validate_research_source_claim_scrapling_freshness_decay_report_payload(
            tampered_payload,
        )


def test_negative_zero_inputs_are_canonicalized_in_public_decimal_surfaces() -> None:
    decay_report = report(
        input_row(
            "negative-zero-private",
            independent_source_count=d("-0"),
            authority_alignment_ratio=d("-0"),
            contradiction_flag_count=d("-0"),
        ),
    )

    _assert_no_signed_zero_decimals(decay_report)
    payload = research_source_claim_scrapling_freshness_decay_report_payload(decay_report)
    assert "-0.000000" not in json.dumps(payload, sort_keys=True)
    assert validate_research_source_claim_scrapling_freshness_decay_report_payload(
        payload,
    )


def test_strict_validation_flags_statuses_imports_and_public_surfaces() -> None:
    decay_report = report(input_row("a-private-pass"))

    assert RESEARCH_SOURCE_CLAIM_SCRAPLING_FRESHNESS_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )

    with pytest.raises(FrozenInstanceError):
        decay_report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ResearchSourceClaimScraplingFreshnessDecayInput):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(input_row(report_only=True), report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(decay_report, readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(decay_report, status="blocked")

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(decay_report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="must be exactly Decimal"):
        input_row(scrapling_confidence_ratio=_DecimalSubclass("1"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be exactly datetime"):
        build_research_source_claim_scrapling_freshness_decay_report(
            (input_row(),),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(observed_at=datetime(2026, 7, 8, 11, 30))

    with pytest.raises(ValueError, match="utcoffset"):
        input_row(observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="cannot be after generated_at"):
        report(input_row(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="independent_source_count"):
        input_row(independent_source_count=d("5"), supporting_source_count=d("4"))

    with pytest.raises(ValueError, match="contradiction_flag_count"):
        input_row(contradiction_flag_count=d("5"), supporting_source_count=d("4"))

    with pytest.raises(ValueError, match="weights"):
        config(freshness_weight=d("0.310000"))

    for public_record in (config(), decay_report, decay_report.rows[0]):
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

    forbidden_public_field_names = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
        "recommendation",
        "sizing",
    }
    for cls in (
        ResearchSourceClaimScraplingFreshnessDecayConfig,
        ResearchSourceClaimScraplingFreshnessDecayRow,
        ResearchSourceClaimScraplingFreshnessDecayReport,
    ):
        assert forbidden_public_field_names.isdisjoint({field.name for field in fields(cls)})
