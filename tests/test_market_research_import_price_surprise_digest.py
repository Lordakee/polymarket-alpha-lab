from __future__ import annotations

import ast
import importlib
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
SIX_DECIMAL_STRING = re.compile(r"^-?\d+\.\d{6}$")


def d(value: str) -> Decimal:
    return Decimal(value)


def module() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_import_price_surprise_digest",
    )


def config(**overrides: object) -> Any:
    m = module()
    values = {
        "config_version": (
            m.DEFAULT_MARKET_RESEARCH_IMPORT_PRICE_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_price_signal_age_seconds": d("7200.000000"),
        "min_abs_import_price_surprise": d("0.200000"),
        "min_market_probability_delta": d("0.030000"),
        "min_source_family_count": d("3.000000"),
        "min_confirmation_ratio": d("0.650000"),
        "confidence_decay_per_gap": d("0.100000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return m.MarketResearchImportPriceSurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition.alpha",
    *,
    import_price_key: str = "us.import-prices.goods",
    country_code: str = "us",
    release_key: str = "bls.import-price-index",
    public_signal_reference: str = "bls-import-price-index-release",
    observed_at: datetime | None = None,
    actual_import_price_change: Decimal = d("0.500000"),
    consensus_import_price_change: Decimal = d("0.100000"),
    market_probability_delta: Decimal = d("0.050000"),
    source_family_count: Decimal = d("3.000000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.850000"),
    signal_config_version: str = "import-price-surprise-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    m = module()
    return m.MarketResearchImportPriceSurpriseDigestSignal(
        condition_id=condition_id,
        import_price_key=import_price_key,
        country_code=country_code,
        release_key=release_key,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        actual_import_price_change=actual_import_price_change,
        consensus_import_price_change=consensus_import_price_change,
        market_probability_delta=market_probability_delta,
        source_family_count=source_family_count,
        confirmation_ratio=confirmation_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    signals: tuple[object, ...],
    *,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    m = module()
    return m.build_market_research_import_price_surprise_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    elif isinstance(value, list | tuple):
        for item in value:
            assert_no_floats(item)


def assert_decimal_public_numeric_fields(value: object) -> None:
    numeric_names = (
        "age",
        "average",
        "change",
        "confidence",
        "count",
        "delta",
        "max_",
        "min_",
        "ratio",
        "surprise",
        "total",
    )
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item = getattr(value, field.name)
            if isinstance(item, tuple):
                assert_decimal_public_numeric_fields(item)
            elif field.name == "country_code":
                pass
            elif any(token in field.name for token in numeric_names):
                assert type(item) is Decimal, field.name
            assert_decimal_public_numeric_fields(item)
    elif isinstance(value, tuple):
        for item in value:
            assert_decimal_public_numeric_fields(item)


def assert_serialized_public_numerics_are_six_decimal_strings(value: object) -> None:
    numeric_names = (
        "age",
        "average",
        "change",
        "confidence",
        "count",
        "delta",
        "max_",
        "min_",
        "ratio",
        "surprise",
        "total",
    )
    non_numeric_names = {"country_code"}
    if isinstance(value, dict):
        for key, item in value.items():
            if (
                key not in non_numeric_names
                and not isinstance(item, dict | list)
                and any(token in key for token in numeric_names)
            ):
                assert type(item) is str, key
                assert SIX_DECIMAL_STRING.fullmatch(item), key
            assert_serialized_public_numerics_are_six_decimal_strings(item)
    elif isinstance(value, list):
        for item in value:
            assert_serialized_public_numerics_are_six_decimal_strings(item)


def test_import_price_surprise_digest_reduces_rows_with_deterministic_reasons() -> None:
    m = module()

    report = build_report(
        (
            signal(
                "condition.ready",
                import_price_key="jp.import-prices.energy",
                country_code="jp",
                release_key="boj.import-prices",
                observed_at=GENERATED_AT - timedelta(minutes=20),
                actual_import_price_change=d("-0.600000"),
                consensus_import_price_change=d("-0.100000"),
                market_probability_delta=d("0.080000"),
                source_family_count=d("4.000000"),
                confirmation_ratio=d("0.900000"),
                base_confidence=d("0.910000"),
            ),
            signal(
                "condition.watch",
                import_price_key="eu.import-prices.goods",
                country_code="eu",
                release_key="eurostat.import-prices",
                observed_at=datetime(
                    2026,
                    7,
                    3,
                    11,
                    0,
                    tzinfo=timezone(timedelta(hours=1)),
                ),
                actual_import_price_change=d("0.250000"),
                consensus_import_price_change=d("0.100000"),
                market_probability_delta=d("0.020000"),
                source_family_count=d("3.000000"),
                confirmation_ratio=d("0.600000"),
                base_confidence=d("0.760000"),
            ),
            signal(
                "condition.blocked",
                import_price_key="us.import-prices.goods",
                country_code="us",
                release_key="bls.import-price-index",
                public_signal_reference="https://example.invalid/import-price?ref=alpha",
                observed_at=GENERATED_AT - timedelta(hours=3),
                actual_import_price_change=d("0.150000"),
                consensus_import_price_change=d("0.100000"),
                market_probability_delta=d("0.010000"),
                source_family_count=d("2.000000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert type(report) is m.MarketResearchImportPriceSurpriseDigestReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        m.DEFAULT_MARKET_RESEARCH_IMPORT_PRICE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_import_price_surprise_digest"
    )
    assert report.signal_count == d("3.000000")
    assert report.ready_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.blocked_signal_count == d("1.000000")
    assert report.stale_price_signal_count == d("1.000000")
    assert report.low_surprise_signal_count == d("2.000000")
    assert report.low_probability_delta_signal_count == d("2.000000")
    assert report.source_family_gap_signal_count == d("1.000000")
    assert report.confirmation_gap_signal_count == d("2.000000")
    assert report.total_confidence_decay == d("0.800000")
    assert report.average_final_confidence == d("0.590000")
    assert report.average_abs_import_price_surprise == d("0.233333")
    assert report.average_market_probability_delta == d("0.036667")
    assert report.average_confirmation_ratio == d("0.633333")
    assert report.max_observed_signal_age_seconds == d("10800.000000")

    assert tuple(row.condition_id for row in report.rows) == (
        "condition.blocked",
        "condition.watch",
        "condition.ready",
    )

    blocked = report.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.observed_at == datetime(2026, 7, 3, 9, 0, tzinfo=UTC)
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.abs_import_price_surprise == d("0.050000")
    assert blocked.confidence_decay_factor == d("0.500000")
    assert blocked.final_confidence == d("0.400000")
    assert blocked.redacted_public_signal_reference == "sha256:c14ec1fefb3f"
    assert blocked.reason_codes == (
        "market_research_import_price_surprise_digest_stale_price_signal",
        "market_research_import_price_surprise_digest_low_probability_delta",
        "market_research_import_price_surprise_digest_low_surprise",
        "market_research_import_price_surprise_digest_source_family_gap",
        "market_research_import_price_surprise_digest_confirmation_gap",
    )

    watch = report.rows[1]
    assert watch.digest_status == "watch"
    assert watch.signal_age_seconds == d("7200.000000")
    assert watch.confidence_decay_factor == d("0.300000")
    assert watch.final_confidence == d("0.460000")
    assert watch.reason_codes == (
        "market_research_import_price_surprise_digest_low_probability_delta",
        "market_research_import_price_surprise_digest_low_surprise",
        "market_research_import_price_surprise_digest_confirmation_gap",
    )

    ready = report.rows[2]
    assert ready.digest_status == "ready"
    assert ready.abs_import_price_surprise == d("0.500000")
    assert ready.final_confidence == d("0.910000")
    assert ready.reason_codes == (
        "market_research_import_price_surprise_digest_ready",
    )

    assert report.reason_code_counts == (
        m.MarketResearchImportPriceSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_import_price_surprise_digest_confirmation_gap"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        m.MarketResearchImportPriceSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_import_price_surprise_digest_low_probability_delta"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        m.MarketResearchImportPriceSurpriseDigestReasonCodeCount(
            reason_code="market_research_import_price_surprise_digest_low_surprise",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        m.MarketResearchImportPriceSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_import_price_surprise_digest_stale_price_signal"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        m.MarketResearchImportPriceSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_import_price_surprise_digest_source_family_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        m.MarketResearchImportPriceSurpriseDigestReasonCodeCount(
            reason_code="market_research_import_price_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert_decimal_public_numeric_fields(report)


def test_empty_inputs_return_report_only_blocked_digest() -> None:
    m = module()

    report = build_report(())

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_import_price_surprise_digest"
    )
    assert report.signal_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == (
        m.MarketResearchImportPriceSurpriseDigestReasonCodeCount(
            reason_code="market_research_import_price_surprise_digest_no_inputs",
            count=d("0.000000"),
            signal_ratio=d("0.000000"),
        ),
    )


def test_digest_payload_is_json_ready_without_float_or_durable_side_effects() -> None:
    m = module()
    report = build_report((signal(),))

    payload = m.market_research_import_price_surprise_digest_payload(report)

    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T11:30:00+00:00"
    assert payload["rows"][0]["final_confidence"] == "0.850000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_floats(payload)
    assert_serialized_public_numerics_are_six_decimal_strings(payload)

    assert build_report((signal(), signal("condition.zzz"),)) == build_report(
        (signal("condition.zzz"), signal()),
    )


def test_dataclasses_are_frozen_and_enforce_decimal_datetime_and_flags() -> None:
    report = build_report((signal(),))

    with pytest.raises(FrozenInstanceError):
        config().paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        signal().paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "ready"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].final_confidence = d("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.reason_code_counts[0].paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="generated_at"):
        build_report((signal(),), generated_at=datetime(2026, 7, 3, 12, 0))
    with pytest.raises(ValueError, match="actual_import_price_change"):
        signal(actual_import_price_change=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_probability_delta"):
        signal(market_probability_delta=0.01)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="config paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="config report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="config readonly must be True"):
        config(readonly=False)
    with pytest.raises(ValueError, match="signal paper_only must be True"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="signal report_only must be True"):
        signal(report_only=False)
    with pytest.raises(ValueError, match="signal readonly must be True"):
        signal(readonly=False)
    with pytest.raises(ValueError, match="row paper_only must be True"):
        replace(report.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="row report_only must be True"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason_code_count paper_only must be True"):
        replace(report.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="reason_code_count report_only must be True"):
        replace(report.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="reason_code_count readonly must be True"):
        replace(report.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report report_only must be True"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="report readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_report((signal(),), cfg=object())
    with pytest.raises(ValueError, match="signal"):
        build_report((object(),))


def test_manual_rows_and_reports_reject_inconsistent_public_records() -> None:
    report = build_report(
        (
            signal("condition.blocked", observed_at=GENERATED_AT - timedelta(hours=3)),
            signal("condition.watch", market_probability_delta=d("0.010000")),
            signal("condition.ready"),
        ),
    )
    row = report.rows[-1]

    with pytest.raises(ValueError, match="import_price_surprise must match"):
        replace(row, import_price_surprise=d("99.000000"))
    with pytest.raises(ValueError, match="abs_import_price_surprise must match"):
        replace(row, abs_import_price_surprise=d("99.000000"))
    with pytest.raises(ValueError, match="confidence_decay_factor must match"):
        replace(row, confidence_decay_factor=d("0.500000"))
    with pytest.raises(ValueError, match="final_confidence must match"):
        replace(row, final_confidence=d("0.100000"))
    with pytest.raises(ValueError, match="digest_status must match"):
        replace(row, digest_status="blocked")
    with pytest.raises(ValueError, match="reason_codes must be deterministic"):
        replace(
            row,
            reason_codes=(
                "market_research_import_price_surprise_digest_ready",
                "market_research_import_price_surprise_digest_low_surprise",
            ),
        )
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(
            row,
            reason_codes=(
                "market_research_import_price_surprise_digest_ready",
                "market_research_import_price_surprise_digest_ready",
            ),
        )

    with pytest.raises(ValueError, match="signal_count must match rows"):
        replace(report, signal_count=d("4.000000"))
    with pytest.raises(ValueError, match="ready_signal_count must match rows"):
        replace(report, ready_signal_count=d("9.000000"))
    with pytest.raises(ValueError, match="average_final_confidence must match rows"):
        replace(report, average_final_confidence=d("0.999999"))
    with pytest.raises(ValueError, match="rows must use deterministic ordering"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(report, reason_code_counts=())


def test_module_has_no_io_network_trading_or_auth_surface() -> None:
    source_path = Path(
        "src/polymarket_alpha_lab/market_research_import_price_surprise_digest.py",
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imported_modules <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
    }

    lowered = source.lower()
    for banned in (
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "web3",
        "clob",
        "private_key",
        "mnemonic",
        "signature",
        "wallet",
        "live_trading",
        "place_order",
        "cancel_order",
        "open(",
    ):
        assert banned not in lowered
