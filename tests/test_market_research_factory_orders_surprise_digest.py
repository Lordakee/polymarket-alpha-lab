from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 3, 9, 30, tzinfo=timezone(timedelta(hours=-4)))


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, _dt: datetime | None) -> None:
        return None

    def dst(self, _dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_factory_orders_surprise_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def item(
    series_id: str,
    *,
    period: str = "2026-05",
    actual_value: str = "104.0",
    consensus_value: str = "100.0",
    prior_value: str = "99.0",
    source_row_count: str = "1",
    released_at: datetime = datetime(2026, 7, 3, 12, 0, tzinfo=UTC),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = api()
    return digest.FactoryOrdersSurpriseInput(
        series_id=series_id,
        period=period,
        actual_value=d(actual_value),
        consensus_value=d(consensus_value),
        prior_value=d(prior_value),
        source_row_count=d(source_row_count),
        released_at=released_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows):
    digest = api()
    return digest.build_market_research_factory_orders_surprise_digest(
        rows,
        config=digest.FactoryOrdersSurpriseDigestConfig(),
        generated_at=GENERATED_AT,
    )


def test_digest_summarizes_surprises_with_deterministic_sorting_and_reason_codes() -> None:
    digest_report = report(
        item(
            "factory_orders_ex_transportation",
            period="2026-05",
            actual_value="95.0",
            consensus_value="100.0",
            prior_value="96.0",
            released_at=datetime(2026, 7, 3, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
        ),
        item(
            "factory_orders_total",
            period="2026-05",
            actual_value="104.0",
            consensus_value="100.0",
            prior_value="101.0",
        ),
        item(
            "factory_orders_capital_goods",
            period="2026-05",
            actual_value="101.0",
            consensus_value="100.0",
            prior_value="98.0",
        ),
    )

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == datetime(2026, 7, 3, 13, 30, tzinfo=UTC)
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.source_row_count == d("3")
    assert digest_report.series_count == d("3")
    assert digest_report.positive_surprise_count == d("2")
    assert digest_report.negative_surprise_count == d("1")
    assert digest_report.neutral_surprise_count == d("0")
    assert digest_report.max_abs_surprise_ratio == d("0.050000")
    assert digest_report.digest_status == "watch"
    assert digest_report.reason_codes == (
        "factory_orders_mixed_surprises",
        "factory_orders_watch_surprise",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True

    assert tuple(row.series_id for row in digest_report.rows) == (
        "factory_orders_ex_transportation",
        "factory_orders_total",
        "factory_orders_capital_goods",
    )
    first = digest_report.rows[0]
    assert first.surprise_value == d("-5.000000")
    assert first.surprise_ratio == d("-0.050000")
    assert first.prior_revision_value == d("-1.000000")
    assert first.surprise_direction == "negative"
    assert first.reason_codes == (
        "factory_orders_negative_surprise",
        "factory_orders_watch_surprise",
    )
    assert first.released_at == datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


def test_empty_digest_is_readonly_and_uses_decimal_zeroes() -> None:
    digest = api()
    digest_report = report()

    assert digest_report.source_row_count == d("0")
    assert digest_report.series_count == d("0")
    assert digest_report.positive_surprise_count == d("0")
    assert digest_report.negative_surprise_count == d("0")
    assert digest_report.neutral_surprise_count == d("0")
    assert digest_report.max_abs_surprise_ratio == d("0.000000")
    assert digest_report.digest_status == "blocked"
    assert digest_report.reason_codes == ("factory_orders_no_inputs",)
    assert digest_report.reason_code_counts == (
        digest.FactoryOrdersSurpriseReasonCodeCount(
            reason_code="factory_orders_no_inputs",
            count=d("1.000000"),
            series_ratio=d("0.000000"),
        ),
    )
    assert digest_report.rows == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_digest_rejects_float_numeric_inputs_naive_datetimes_duplicates_and_mutation() -> None:
    digest = api()

    with pytest.raises(ValueError, match="actual_value must be a Decimal"):
        digest.FactoryOrdersSurpriseInput(
            series_id="factory_orders_total",
            period="2026-05",
            actual_value=1.0,
            consensus_value=d("100"),
            prior_value=d("99"),
            source_row_count=d("1"),
            released_at=datetime(2026, 7, 3, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="released_at must be timezone-aware"):
        item("factory_orders_total", released_at=datetime(2026, 7, 3, 12, 0))

    with pytest.raises(ValueError, match="released_at must be timezone-aware"):
        item(
            "factory_orders_total",
            released_at=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTz()),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_research_factory_orders_surprise_digest(
            (),
            config=digest.FactoryOrdersSurpriseDigestConfig(),
            generated_at=datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTz()),
        )

    row = item("factory_orders_total")
    with pytest.raises(FrozenInstanceError):
        row.actual_value = d("1")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        digest.FactoryOrdersSurpriseDigestConfig(paper_only=False)

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(
            item("factory_orders_total", period="2026-05"),
            item("factory_orders_total", period="2026-05"),
        )


def test_public_dataclasses_reject_subclasses_and_noncanonical_ordering() -> None:
    digest = api()
    digest_report = report(
        item(
            "factory_orders_ex_transportation",
            actual_value="95.0",
            consensus_value="100.0",
        ),
        item(
            "factory_orders_total",
            actual_value="104.0",
            consensus_value="100.0",
        ),
    )

    for base_type in (
        digest.FactoryOrdersSurpriseDigestConfig,
        digest.FactoryOrdersSurpriseInput,
        digest.FactoryOrdersSurpriseDigestRow,
        digest.FactoryOrdersSurpriseReasonCodeCount,
        digest.FactoryOrdersSurpriseDigestReport,
    ):
        with pytest.raises(TypeError, match="subclassing"):
            type(f"{base_type.__name__}Subclass", (base_type,), {})

    with pytest.raises(ValueError, match="count"):
        digest.FactoryOrdersSurpriseReasonCodeCount(
            reason_code="factory_orders_no_inputs",
            count=d("0.000000"),
            series_ratio=d("0.000000"),
        )

    with pytest.raises(ValueError, match="rows must use deterministic ordering"):
        replace(digest_report, rows=tuple(reversed(digest_report.rows)))
    with pytest.raises(ValueError, match="reason_code_counts must use deterministic ordering"):
        replace(
            digest_report,
            reason_code_counts=tuple(reversed(digest_report.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_codes must not include no_inputs"):
        replace(
            digest_report,
            reason_codes=(
                "factory_orders_no_inputs",
                "factory_orders_mixed_surprises",
            ),
        )
    with pytest.raises(ValueError, match="digest_status must match reason_codes"):
        replace(report(), digest_status="clear")
    with pytest.raises(ValueError, match="digest_status must match reason_codes"):
        replace(digest_report, digest_status="clear")


def test_digest_rejects_each_false_report_only_guard_flag() -> None:
    digest = api()
    digest_report = report(item("factory_orders_total"))
    digest_row = digest_report.rows[0]

    false_flag_cases = (
        (
            "config paper_only",
            lambda: digest.FactoryOrdersSurpriseDigestConfig(paper_only=False),
            "paper_only must be True",
        ),
        (
            "config report_only",
            lambda: digest.FactoryOrdersSurpriseDigestConfig(report_only=False),
            "report_only must be True",
        ),
        (
            "config readonly",
            lambda: digest.FactoryOrdersSurpriseDigestConfig(readonly=False),
            "readonly must be True",
        ),
        (
            "input paper_only",
            lambda: item("factory_orders_total", paper_only=False),
            "paper_only must be True",
        ),
        (
            "input report_only",
            lambda: item("factory_orders_total", report_only=False),
            "report_only must be True",
        ),
        (
            "input readonly",
            lambda: item("factory_orders_total", readonly=False),
            "readonly must be True",
        ),
        (
            "row paper_only",
            lambda: replace(digest_row, paper_only=False),
            "paper_only must be True",
        ),
        (
            "row report_only",
            lambda: replace(digest_row, report_only=False),
            "report_only must be True",
        ),
        (
            "row readonly",
            lambda: replace(digest_row, readonly=False),
            "readonly must be True",
        ),
        (
            "report paper_only",
            lambda: replace(digest_report, paper_only=False),
            "paper_only must be True",
        ),
        (
            "report report_only",
            lambda: replace(digest_report, report_only=False),
            "report_only must be True",
        ),
        (
            "report readonly",
            lambda: replace(digest_report, readonly=False),
            "readonly must be True",
        ),
    )
    for _label, make_value, message in false_flag_cases:
        with pytest.raises(ValueError, match=message):
            make_value()


def test_payload_is_json_ready_and_omits_live_or_durable_surfaces() -> None:
    payload = api().market_research_factory_orders_surprise_digest_payload(
        report(
            item(
                "factory_orders_total",
                actual_value="102.0",
                consensus_value="100.0",
                prior_value="101.0",
            ),
        ),
    )

    payload_text = repr(payload).lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "market_slug",
        "question",
        "payload_json",
        "investment_recommendation",
        "durable",
        "order_id",
        "submit_order",
        "cancel_order",
    ):
        assert forbidden not in payload_text
    assert payload["source_row_count"] == "1.000000"
    assert payload["series_count"] == "1.000000"
    assert payload["positive_surprise_count"] == "1.000000"
    assert payload["negative_surprise_count"] == "0.000000"
    assert payload["neutral_surprise_count"] == "0.000000"
    assert payload["max_abs_surprise_ratio"] == "0.020000"
    assert payload["rows"][0]["source_row_count"] == "1.000000"
    assert payload["rows"][0]["surprise_ratio"] == "0.020000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["reason_code_counts"][0]["series_ratio"] == "1.000000"

    empty_payload = api().market_research_factory_orders_surprise_digest_payload(report())
    assert empty_payload["reason_codes"] == ["factory_orders_no_inputs"]
    assert empty_payload["reason_code_counts"][0]["count"] == "1.000000"
    assert empty_payload["reason_code_counts"][0]["series_ratio"] == "0.000000"


def test_module_scope_has_no_network_store_fast_live_trading_or_float_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_factory_orders_surprise_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "psycopg",
        "sqlite",
        "supabase",
        "auth",
        "wallet",
        "account",
        "market_slug",
        "question",
        "payload_json",
        "investment_recommendation",
        "durable",
        "open(",
        "trade",
        "order_id",
        "submit_order",
        "cancel_order",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
