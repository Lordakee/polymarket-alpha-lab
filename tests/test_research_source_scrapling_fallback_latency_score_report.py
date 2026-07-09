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
    "polymarket_alpha_lab.research_source_scrapling_fallback_latency_score_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_scrapling_fallback_latency_score_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 58, tzinfo=UTC)


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
        "max_fallback_latency_pass_seconds": d("60.000000"),
        "max_fallback_latency_watch_seconds": d("180.000000"),
        "min_fallback_success_pass_ratio": d("0.900000"),
        "min_fallback_success_watch_ratio": d("0.600000"),
        "min_latency_improvement_pass_ratio": d("0.500000"),
        "min_latency_improvement_watch_ratio": d("0.200000"),
        "min_fallback_latency_score_pass": d("0.800000"),
        "min_fallback_latency_score_watch": d("0.500000"),
        "fallback_latency_weight": d("0.400000"),
        "fallback_success_weight": d("0.350000"),
        "latency_improvement_weight": d("0.250000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceScraplingFallbackLatencyScoreConfig(**values)


def latency_input(
    private_capture_ref: str = "private-capture",
    *,
    observed_at: datetime = OBSERVED_AT,
    scrapling_latency_seconds: Decimal = d("240.000000"),
    fallback_latency_seconds: Decimal = d("30.000000"),
    fallback_success_ratio: Decimal = d("0.950000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceScraplingFallbackLatencyScoreInput(
        private_capture_ref=private_capture_ref,
        observed_at=observed_at,
        scrapling_latency_seconds=scrapling_latency_seconds,
        fallback_latency_seconds=fallback_latency_seconds,
        fallback_success_ratio=fallback_success_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: object, config: object | None = None) -> Any:
    module = api()
    return module.build_research_source_scrapling_fallback_latency_score_report(
        items,
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
        "://",
        "www.",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
        "auth",
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


def test_pass_report_has_stable_digest_redacted_payload_and_decimal_scores() -> None:
    module = api()
    first = build_report(
        latency_input(
            "raw_candidate_id=secret|market_id=secret-market|market_slug=secret-slug|"
            "question=private question|https://example.invalid/path?token=hidden",
        ),
        latency_input(
            "postgres://dsn/table/wallet/order/trade/live/source_text",
            scrapling_latency_seconds=d("120.000000"),
            fallback_latency_seconds=d("45.000000"),
            fallback_success_ratio=d("0.920000"),
        ),
    )
    second = build_report(
        latency_input(
            "changed-private-b",
            scrapling_latency_seconds=d("120.000000"),
            fallback_latency_seconds=d("45.000000"),
            fallback_success_ratio=d("0.920000"),
        ),
        latency_input("changed-private-a"),
    )
    changed = build_report(latency_input(fallback_latency_seconds=d("31.000000")))

    assert type(first) is module.ResearchSourceScraplingFallbackLatencyScoreReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen
    assert first.status == "pass"
    assert first.reason_codes == ("scrapling_fallback_latency_score_pass",)
    assert first.input_count == d("2.000000")
    assert first.row_count == d("2.000000")
    assert first.max_scrapling_latency_seconds == d("240.000000")
    assert first.max_fallback_latency_seconds == d("45.000000")
    assert first.average_fallback_latency_seconds == d("37.500000")
    assert first.average_latency_improvement_ratio == d("0.750000")
    assert first.average_fallback_success_ratio == d("0.935000")
    assert first.average_fallback_latency_score == d("0.914750")
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.derived_validation_digest != changed.derived_validation_digest
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    _assert_decimal_public_numbers(first)

    payload = first.payload
    json.dumps(payload, sort_keys=True)
    assert payload["status"] == "pass"
    assert payload["input_count"] == "2.000000"
    assert payload["average_fallback_latency_score"] == "0.914750"
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert module.research_source_scrapling_fallback_latency_score_report_digest(
        first,
    ) == payload["derived_validation_digest"]
    assert module.validate_research_source_scrapling_fallback_latency_score_report_payload(
        payload,
    )
    assert [row["row_label"] for row in payload["rows"]] == [
        "redacted-scrapling-fallback-latency-000001",
        "redacted-scrapling-fallback-latency-000002",
    ]
    _assert_payload_has_no_raw_numbers(payload)
    _assert_payload_has_no_forbidden_surface(payload)


def test_watch_and_block_rows_use_fixed_reason_order() -> None:
    watch_report = build_report(
        latency_input(
            "watch-private",
            scrapling_latency_seconds=d("120.000000"),
            fallback_latency_seconds=d("90.000000"),
            fallback_success_ratio=d("0.800000"),
        ),
    )
    block_report = build_report(
        latency_input(
            "block-private",
            scrapling_latency_seconds=d("240.000000"),
            fallback_latency_seconds=d("240.000000"),
            fallback_success_ratio=d("0.400000"),
        ),
    )

    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert watch_report.rows[0].fallback_latency_quality_score == d("0.750000")
    assert watch_report.rows[0].latency_improvement_ratio == d("0.250000")
    assert watch_report.rows[0].fallback_latency_score == d("0.642500")
    assert watch_report.rows[0].reason_codes == (
        "fallback_latency_above_pass_threshold",
        "fallback_success_below_pass_threshold",
        "latency_improvement_below_pass_threshold",
        "fallback_latency_score_below_pass_threshold",
    )

    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"
    assert block_report.rows[0].fallback_latency_quality_score == d("0.000000")
    assert block_report.rows[0].latency_improvement_ratio == d("0.000000")
    assert block_report.rows[0].fallback_latency_score == d("0.140000")
    assert block_report.rows[0].reason_codes == (
        "fallback_latency_above_watch_threshold",
        "fallback_success_below_watch_threshold",
        "latency_improvement_below_watch_threshold",
        "fallback_latency_score_below_watch_threshold",
    )


def test_empty_input_blocks_with_zero_decimal_scores() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.reason_codes == ("scrapling_fallback_latency_no_inputs",)
    assert report.input_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.max_scrapling_latency_seconds == d("0.000000")
    assert report.max_fallback_latency_seconds == d("0.000000")
    assert report.average_fallback_latency_score == d("0.000000")
    assert report.reason_code_counts[0].reason_code == (
        "scrapling_fallback_latency_no_inputs"
    )
    assert report.reason_code_counts[0].count == d("1.000000")
    assert report.rows == ()


def test_dataclass_guards_payload_validation_no_io_and_safe_public_surface() -> None:
    module = api()
    report = build_report(latency_input())

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchSourceScraplingFallbackLatencyScoreConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)

    with pytest.raises(ValueError, match="Decimal"):
        latency_input(scrapling_latency_seconds=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="datetime"):
        latency_input(observed_at=_DatetimeSubclass(2026, 7, 9, tzinfo=UTC))

    with pytest.raises(ValueError, match="utcoffset"):
        latency_input(observed_at=datetime(2026, 7, 9, tzinfo=_NoneOffsetTz()))

    with pytest.raises(ValueError, match="observed_at"):
        build_report(latency_input(observed_at=GENERATED_AT + timedelta(seconds=1)))

    with pytest.raises(ValueError, match="fallback_latency_seconds"):
        latency_input(
            scrapling_latency_seconds=d("0.000000"),
            fallback_latency_seconds=d("1.000000"),
        )

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="Decimal"):
        module.ResearchSourceScraplingFallbackLatencyScoreInput(
            private_capture_ref="private",
            observed_at=OBSERVED_AT,
            scrapling_latency_seconds=_DecimalSubclass("1.000000"),
            fallback_latency_seconds=d("1.000000"),
            fallback_success_ratio=d("1.000000"),
        )

    payload = report.payload
    broken_payload = dict(payload)
    broken_payload["average_fallback_latency_score"] = "0.100000"
    assert not module.validate_research_source_scrapling_fallback_latency_score_report_payload(
        broken_payload,
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert {row.status for row in report.rows}.issubset(set(module.STATUSES))

    forbidden_terms = (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "sizing",
        "recommendation",
        "auth",
    )
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_terms)

    for cls in (
        module.ResearchSourceScraplingFallbackLatencyScoreConfig,
        module.ResearchSourceScraplingFallbackLatencyScoreInput,
        module.ResearchSourceScraplingFallbackLatencyScoreReport,
    ):
        for field in fields(cls):
            if field.name == "private_capture_ref":
                continue
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_terms)

    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "web3",
        "ccxt",
        "boto3",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
