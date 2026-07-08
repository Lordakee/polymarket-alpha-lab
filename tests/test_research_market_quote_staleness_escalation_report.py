from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 8, 6, 15, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt):  # type: ignore[no-untyped-def]
        return None

    def dst(self, dt):  # type: ignore[no-untyped-def]
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_quote_staleness_escalation_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted_market_reference(value: str) -> str:
    return f"market_ref_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def redacted_source_reference(value: str) -> str:
    return f"source_ref_{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def config(**overrides: object):
    report = api()
    values = {
        "config_version": "research-market-quote-staleness-escalation-report-v0",
        "quote_age_watch_seconds": d("120.000000"),
        "quote_age_block_seconds": d("300.000000"),
        "spread_widening_watch_ratio": d("0.100000"),
        "spread_widening_block_ratio": d("0.250000"),
        "depth_fade_watch_ratio": d("0.250000"),
        "depth_fade_block_ratio": d("0.500000"),
        "catalyst_pressure_watch_score": d("0.500000"),
        "catalyst_pressure_block_score": d("0.800000"),
        "fee_friction_watch_ratio": d("0.020000"),
        "fee_friction_block_ratio": d("0.050000"),
        "watch_escalation_score": d("0.350000"),
        "block_escalation_score": d("0.700000"),
    }
    values.update(overrides)
    return report.ResearchMarketQuoteStalenessEscalationConfig(**values)


def input_row(**overrides: object):
    report = api()
    values = {
        "research_bucket": "beta-bucket",
        "market_reference": "market-beta-secret",
        "source_reference": "source-beta-token",
        "quote_age_seconds": d("150.000000"),
        "spread_widening_ratio": d("0.120000"),
        "depth_fade_ratio": d("0.300000"),
        "catalyst_pressure_score": d("0.550000"),
        "fee_friction_ratio": d("0.025000"),
    }
    values.update(overrides)
    return report.ResearchMarketQuoteStalenessEscalationInput(**values)


def build_report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    report = api()
    return report.build_research_market_quote_staleness_escalation_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def sample_rows():
    return (
        input_row(
            research_bucket="alpha-bucket",
            market_reference="market-alpha-secret",
            source_reference="source-alpha-token",
            quote_age_seconds=d("45.000000"),
            spread_widening_ratio=d("0.020000"),
            depth_fade_ratio=d("0.100000"),
            catalyst_pressure_score=d("0.200000"),
            fee_friction_ratio=d("0.005000"),
        ),
        input_row(),
        input_row(
            research_bucket="gamma-bucket",
            market_reference="market-gamma-secret",
            source_reference="source-gamma-token",
            quote_age_seconds=d("360.000000"),
            spread_widening_ratio=d("0.300000"),
            depth_fade_ratio=d("0.600000"),
            catalyst_pressure_score=d("0.850000"),
            fee_friction_ratio=d("0.060000"),
        ),
    )


def test_report_escalates_quote_staleness_metrics_to_pass_watch_and_block() -> None:
    staleness_report = build_report(*sample_rows())

    assert is_dataclass(staleness_report)
    assert api().STATUSES == ("pass", "watch", "block")
    assert staleness_report.generated_at == GENERATED_AT
    assert staleness_report.generated_at.tzinfo is UTC
    assert staleness_report.config_version == (
        "research-market-quote-staleness-escalation-report-v0"
    )
    assert staleness_report.input_count == d("3")
    assert staleness_report.bucket_count == d("3")
    assert staleness_report.watch_count == d("1")
    assert staleness_report.block_count == d("1")
    assert staleness_report.stale_quote_count == d("2")
    assert staleness_report.spread_widening_count == d("2")
    assert staleness_report.depth_fade_count == d("2")
    assert staleness_report.catalyst_pressure_count == d("2")
    assert staleness_report.fee_friction_count == d("2")
    assert staleness_report.mean_quote_age_seconds == d("185.000000")
    assert staleness_report.mean_spread_widening_ratio == d("0.146667")
    assert staleness_report.mean_depth_fade_ratio == d("0.333333")
    assert staleness_report.mean_catalyst_pressure_score == d("0.533333")
    assert staleness_report.mean_fee_friction_ratio == d("0.030000")
    assert staleness_report.mean_escalation_score == d("0.569833")
    assert staleness_report.status == "block"
    assert staleness_report.reason_codes == (
        "aggregate_quote_age_stale",
        "spread_widening_detected",
        "depth_fade_detected",
        "catalyst_pressure_detected",
        "fee_friction_detected",
        "composite_escalation_detected",
    )
    assert staleness_report.paper_only is True
    assert staleness_report.report_only is True
    assert staleness_report.readonly is True

    first, second, third = staleness_report.rows
    assert first.research_bucket == "gamma-bucket"
    assert first.redacted_market_reference == redacted_market_reference(
        "market-gamma-secret",
    )
    assert first.redacted_source_reference == redacted_source_reference(
        "source-gamma-token",
    )
    assert first.quote_age_pressure == d("1.000000")
    assert first.spread_widening_pressure == d("1.000000")
    assert first.depth_fade_pressure == d("1.000000")
    assert first.catalyst_pressure_signal == d("1.000000")
    assert first.fee_friction_pressure == d("1.000000")
    assert first.escalation_score == d("1.000000")
    assert first.status == "block"
    assert first.reason_codes == (
        "aggregate_quote_age_blocking",
        "spread_widening_blocking",
        "depth_fade_blocking",
        "catalyst_pressure_blocking",
        "fee_friction_blocking",
        "composite_escalation_blocking",
    )

    assert second.research_bucket == "beta-bucket"
    assert second.escalation_score == d("0.553500")
    assert second.status == "watch"
    assert second.reason_codes == (
        "aggregate_quote_age_stale",
        "spread_widening_watch",
        "depth_fade_watch",
        "catalyst_pressure_watch",
        "fee_friction_watch",
        "composite_escalation_watch",
    )
    assert third.research_bucket == "alpha-bucket"
    assert third.escalation_score == d("0.156000")
    assert third.status == "pass"
    assert third.reason_codes == ("quote_staleness_escalation_clear",)


def test_payload_and_digest_are_deterministic_redacted_and_decimal_safe() -> None:
    report_module = api()
    rows = sample_rows()
    first_report = build_report(*rows)
    second_report = build_report(*reversed(rows))

    first_payload = report_module.research_market_quote_staleness_escalation_payload(
        first_report,
    )
    second_payload = report_module.research_market_quote_staleness_escalation_payload(
        second_report,
    )
    first_digest = report_module.research_market_quote_staleness_escalation_digest(
        first_report,
    )

    assert first_payload == second_payload
    assert first_digest == report_module.research_market_quote_staleness_escalation_digest(
        second_report,
    )
    assert first_digest == report_module.research_market_quote_staleness_escalation_digest(
        first_payload,
    )
    assert len(first_digest) == 64
    assert first_payload["generated_at"] == "2026-07-08T06:15:00+00:00"
    assert first_payload["input_count"] == "3"
    assert first_payload["rows"][0]["redacted_market_reference"] == (
        redacted_market_reference("market-gamma-secret")
    )
    assert first_payload["rows"][0]["redacted_source_reference"] == (
        redacted_source_reference("source-gamma-token")
    )
    assert "market-gamma-secret" not in repr(first_payload)
    assert "source-gamma-token" not in repr(first_payload)
    assert "Decimal(" not in repr(first_payload)
    assert "datetime" not in repr(first_payload).lower()

    def assert_no_float(value: object) -> None:
        if isinstance(value, dict):
            for item in value.values():
                assert_no_float(item)
        elif isinstance(value, list):
            for item in value:
                assert_no_float(item)
        else:
            assert type(value) is not float

    assert_no_float(first_payload)


def test_validates_decimal_inputs_flags_statuses_and_frozen_outputs() -> None:
    report_module = api()
    staleness_report = build_report(*sample_rows())

    with pytest.raises(FrozenInstanceError):
        staleness_report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="quote_age_seconds must be a Decimal"):
        input_row(quote_age_seconds=150)

    with pytest.raises(ValueError, match="spread_widening_ratio must be a Decimal"):
        input_row(spread_widening_ratio=0.12)

    with pytest.raises(ValueError, match="depth_fade_ratio"):
        input_row(depth_fade_ratio=_DecimalSubclass("0.300000"))

    with pytest.raises(ValueError, match="fee_friction_ratio must be finite"):
        input_row(fee_friction_ratio=Decimal("NaN"))

    with pytest.raises(ValueError, match="quote_age_block_seconds must exceed"):
        config(quote_age_block_seconds=d("120.000000"))

    with pytest.raises(ValueError, match="config must be paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="input must be readonly"):
        input_row(readonly=False)

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_report(input_row(), generated_at=datetime(2026, 7, 8, 6, 15))

    with pytest.raises(ValueError, match="generated_at must be datetime"):
        build_report(input_row(), generated_at="bad")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at must be datetime"):
        report_module.ResearchMarketQuoteStalenessEscalationReport(
            generated_at=_DatetimeSubclass(2026, 7, 8, 6, 15, tzinfo=UTC),
            config_version="research-market-quote-staleness-escalation-report-v0",
            input_count=d("0"),
            bucket_count=d("0"),
            watch_count=d("0"),
            block_count=d("0"),
            stale_quote_count=d("0"),
            spread_widening_count=d("0"),
            depth_fade_count=d("0"),
            catalyst_pressure_count=d("0"),
            fee_friction_count=d("0"),
            mean_quote_age_seconds=d("0.000000"),
            mean_spread_widening_ratio=d("0.000000"),
            mean_depth_fade_ratio=d("0.000000"),
            mean_catalyst_pressure_score=d("0.000000"),
            mean_fee_friction_ratio=d("0.000000"),
            mean_escalation_score=d("0.000000"),
            status="pass",
            reason_codes=("quote_staleness_escalation_report_clear",),
            reason_code_counts=(),
            rows=(),
        )

    with pytest.raises(ValueError, match="status is not supported"):
        replace(staleness_report.rows[0], status="blocked")

    with pytest.raises(ValueError, match="input_count"):
        replace(staleness_report, input_count=d("2"))

    with pytest.raises(ValueError, match="rows"):
        replace(staleness_report, rows=(staleness_report.rows[0],) * 2)


def test_payload_rejects_unsafe_surface_and_module_scope_stays_report_only() -> None:
    report_module = api()

    with pytest.raises(ValueError, match="payload must be readonly"):
        report_module.research_market_quote_staleness_escalation_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )

    with pytest.raises(ValueError, match="JSON value must not be a float"):
        report_module.research_market_quote_staleness_escalation_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "mean_quote_age_seconds": 1.5,
            },
        )

    with pytest.raises(ValueError, match="unsafe surface"):
        report_module.research_market_quote_staleness_escalation_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet": "redacted",
            },
        )

    source = Path(
        "src/polymarket_alpha_lab/research_market_quote_staleness_escalation_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "network",
        "database",
        "open(",
        "recommendation",
        "sizing",
        "order",
        "trade",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
