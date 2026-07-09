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
    "polymarket_alpha_lab.research_source_scrapling_fallback_claim_latency_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scrapling_fallback_claim_latency_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
CLAIM_OBSERVED_AT = datetime(2026, 7, 9, 10, 0, tzinfo=UTC)


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
        "config_version": (
            "research-source-scrapling-fallback-claim-latency-report-v0"
        ),
        "fresh_claim_max_age_seconds": d("1800.000000"),
        "watch_claim_max_age_seconds": d("7200.000000"),
        "block_claim_max_age_seconds": d("21600.000000"),
        "fallback_watch_ratio": d("0.250000"),
        "fallback_block_ratio": d("0.500000"),
        "claim_latency_weight": d("0.600000"),
        "fallback_pressure_weight": d("0.400000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceScraplingFallbackClaimLatencyConfig(**values)


def input_row(
    private_candidate_ref: str = "candidate-private-ref",
    *,
    collector_family: str = "scrapling",
    claim_observed_at: datetime = CLAIM_OBSERVED_AT,
    fallback_attempt_count: Decimal = d("0"),
    primary_attempt_count: Decimal = d("4"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScraplingFallbackClaimLatencyInput(
        private_candidate_ref=private_candidate_ref,
        collector_family=collector_family,
        claim_observed_at=claim_observed_at,
        fallback_attempt_count=fallback_attempt_count,
        primary_attempt_count=primary_attempt_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: object, config: object | None = None) -> Any:
    module = api()
    return module.build_research_source_scrapling_fallback_claim_latency_report(
        rows,
        config=config or cfg(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = json.loads(json.dumps(payload, sort_keys=True))
    resigned["derived_validation_digest"] = canonical_digest(resigned)
    return resigned


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
        "url",
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
        "network",
        "auth",
        "sizing",
        "recommendation",
        "execution",
    ):
        assert all(forbidden not in value for value in rendered_values), forbidden


def test_empty_input_blocks_with_report_only_digest_and_decimal_payload() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchSourceScraplingFallbackClaimLatencyReport
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
    assert report.max_claim_latency_seconds == d("0.000000")
    assert report.average_claim_latency_seconds == d("0.000000")
    assert report.average_fallback_ratio == d("0.000000")
    assert report.average_latency_pressure_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "scrapling_fallback_claim_latency_no_inputs",
        "scrapling_fallback_claim_latency_block",
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
    assert (
        module.research_source_scrapling_fallback_claim_latency_report_digest(report)
        == payload["derived_validation_digest"]
    )
    assert module.validate_research_source_scrapling_fallback_claim_latency_public_payload(
        payload,
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)


def test_report_scores_claim_latency_and_fallback_pressure() -> None:
    report = build_report(
        input_row(
            "a-private-pass",
            claim_observed_at=GENERATED_AT - timedelta(seconds=900),
            fallback_attempt_count=d("0"),
            primary_attempt_count=d("6"),
        ),
        input_row(
            "b-private-watch",
            claim_observed_at=GENERATED_AT - timedelta(seconds=3600),
            fallback_attempt_count=d("1"),
            primary_attempt_count=d("3"),
        ),
        input_row(
            "c-private-block",
            claim_observed_at=GENERATED_AT - timedelta(seconds=24000),
            fallback_attempt_count=d("3"),
            primary_attempt_count=d("3"),
        ),
    )

    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.attention_count == d("2.000000")
    assert report.max_claim_latency_seconds == d("24000.000000")
    assert report.average_claim_latency_seconds == d("9500.000000")
    assert report.average_fallback_ratio == d("0.250000")
    assert report.average_latency_pressure_score == d("0.400000")

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.row_label for row in report.rows) == (
        "redacted-claim-latency-000001",
        "redacted-claim-latency-000002",
        "redacted-claim-latency-000003",
    )

    block_row, watch_row, pass_row = report.rows
    assert block_row.claim_latency_seconds == d("24000.000000")
    assert block_row.fallback_ratio == d("0.500000")
    assert block_row.latency_pressure_score == d("0.800000")
    assert block_row.reason_codes == (
        "claim_latency_block",
        "fallback_ratio_block",
        "scrapling_fallback_claim_latency_block",
    )
    assert watch_row.claim_latency_score == d("0.500000")
    assert watch_row.fallback_ratio == d("0.250000")
    assert watch_row.latency_pressure_score == d("0.400000")
    assert watch_row.reason_codes == (
        "claim_latency_watch",
        "fallback_ratio_watch",
        "scrapling_fallback_claim_latency_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.claim_latency_score == d("0.000000")
    assert pass_row.fallback_ratio == d("0.000000")
    assert pass_row.latency_pressure_score == d("0.000000")
    assert pass_row.reason_codes == ("scrapling_fallback_claim_latency_pass",)


def test_payload_is_deterministic_redacted_digest_validated_and_scrapling_scoped() -> None:
    module = api()
    rows = (
        input_row("https://example.invalid/raw_candidate/market_id/token"),
        input_row(
            "postgres://dsn/table/wallet/order/trade/live",
            collector_family="generic",
            claim_observed_at=GENERATED_AT - timedelta(seconds=3600),
            fallback_attempt_count=d("1"),
            primary_attempt_count=d("3"),
        ),
    )
    first = build_report(*rows)
    second = build_report(*reversed(rows))

    assert first.derived_validation_digest == second.derived_validation_digest
    payload = first.payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.validate_research_source_scrapling_fallback_claim_latency_public_payload(
        payload,
    )
    assert {row["collector_family"] for row in payload["rows"]} == {
        "generic",
        "scrapling",
    }
    assert all(
        row["row_label"].startswith("redacted-claim-latency-")
        for row in payload["rows"]
    )
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)

    tampered = build_report(*rows)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_scrapling_fallback_claim_latency_report_payload(tampered)

    unsigned = dict(payload)
    unsigned["status"] = "pass"
    assert not module.validate_research_source_scrapling_fallback_claim_latency_public_payload(
        unsigned,
    )


def test_payload_digest_and_rows_do_not_depend_on_private_candidate_ref() -> None:
    first = build_report(
        input_row(
            "a-private-pass",
            collector_family="generic",
            claim_observed_at=GENERATED_AT - timedelta(seconds=900),
            fallback_attempt_count=d("0"),
            primary_attempt_count=d("6"),
        ),
        input_row(
            "z-private-block",
            collector_family="scrapling",
            claim_observed_at=GENERATED_AT - timedelta(seconds=24000),
            fallback_attempt_count=d("3"),
            primary_attempt_count=d("3"),
        ),
    )
    second = build_report(
        input_row(
            "z-private-pass",
            collector_family="generic",
            claim_observed_at=GENERATED_AT - timedelta(seconds=900),
            fallback_attempt_count=d("0"),
            primary_attempt_count=d("6"),
        ),
        input_row(
            "a-private-block",
            collector_family="scrapling",
            claim_observed_at=GENERATED_AT - timedelta(seconds=24000),
            fallback_attempt_count=d("3"),
            primary_attempt_count=d("3"),
        ),
    )

    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest


def test_public_payload_validation_rejects_self_signed_schema_drift() -> None:
    module = api()
    payload = build_report(
        input_row(
            "private-watch",
            claim_observed_at=GENERATED_AT - timedelta(seconds=3600),
            fallback_attempt_count=d("1"),
            primary_attempt_count=d("3"),
        ),
    ).payload

    extra_field = dict(payload)
    extra_field["unexpected"] = "pass"
    assert not module.validate_research_source_scrapling_fallback_claim_latency_public_payload(
        resign_payload(extra_field),
    )

    false_flag = dict(payload)
    false_flag["paper_only"] = False
    assert not module.validate_research_source_scrapling_fallback_claim_latency_public_payload(
        resign_payload(false_flag),
    )

    noncanonical_decimal = dict(payload)
    noncanonical_decimal["input_count"] = "1.0"
    assert not module.validate_research_source_scrapling_fallback_claim_latency_public_payload(
        resign_payload(noncanonical_decimal),
    )

    inconsistent_count = dict(payload)
    inconsistent_count["watch_count"] = "0.000000"
    assert not module.validate_research_source_scrapling_fallback_claim_latency_public_payload(
        resign_payload(inconsistent_count),
    )


def test_dataclasses_are_frozen_flags_and_inputs_are_strict_without_live_surfaces() -> None:
    module = api()
    report = build_report(input_row("private-pass"))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(module.ResearchSourceScraplingFallbackClaimLatencyInput):
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
        input_row(fallback_attempt_count=_DecimalSubclass("1"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be exactly datetime"):
        module.build_research_source_scrapling_fallback_claim_latency_report(
            (input_row(),),
            config=cfg(),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        input_row(claim_observed_at=datetime(2026, 7, 9, 10, 0))

    with pytest.raises(ValueError, match="utcoffset"):
        input_row(
            claim_observed_at=datetime(2026, 7, 9, 10, 0, tzinfo=_NoneOffsetTz()),
        )

    with pytest.raises(ValueError, match="cannot be after generated_at"):
        build_report(input_row(claim_observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="primary_attempt_count"):
        input_row(primary_attempt_count=d("0"))

    with pytest.raises(ValueError, match="fallback_attempt_count"):
        input_row(fallback_attempt_count=d("4"), primary_attempt_count=d("3"))

    with pytest.raises(ValueError, match="weights"):
        cfg(claim_latency_weight=d("0.700000"))

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
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    for public_name in module.__all__:
        _assert_payload_has_no_forbidden_surface({"name": public_name})
    for cls in (
        module.ResearchSourceScraplingFallbackClaimLatencyConfig,
        module.ResearchSourceScraplingFallbackClaimLatencyRow,
        module.ResearchSourceScraplingFallbackClaimLatencyReport,
    ):
        for field in fields(cls):
            _assert_payload_has_no_forbidden_surface({"field": field.name})
