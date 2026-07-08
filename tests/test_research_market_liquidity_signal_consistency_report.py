from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_market_liquidity_signal_consistency_report"
)
GENERATED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTzinfo(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_MARKET_LIQUIDITY_SIGNAL_CONSISTENCY_CONFIG_VERSION
        ),
        "minimum_aggregate_depth_usd": d("1000.000000"),
        "blocked_aggregate_depth_usd": d("250.000000"),
        "maximum_spread_ratio": d("0.050000"),
        "blocked_spread_ratio": d("0.120000"),
        "maximum_quote_age_seconds": d("600.000000"),
        "blocked_quote_age_seconds": d("1800.000000"),
        "maximum_evidence_age_seconds": d("86400.000000"),
        "blocked_evidence_age_seconds": d("172800.000000"),
        "catalyst_pressure_watch_threshold": d("0.600000"),
        "catalyst_pressure_block_threshold": d("0.850000"),
        "confidence_dispersion_watch_threshold": d("0.250000"),
        "confidence_dispersion_block_threshold": d("0.500000"),
        "confidence_gap_watch_threshold": d("0.200000"),
        "confidence_gap_block_threshold": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchMarketLiquiditySignalConsistencyConfig(**values)


def sample(
    market_reference: str = "https://markets.example/raw-pass?token=pass-secret",
    *,
    evidence_reference: str = "https://feed.example/raw-pass?secret=pass-token",
    observed_at: datetime | None = None,
    quote_observed_at: datetime | None = None,
    evidence_observed_at: datetime | None = None,
    aggregate_depth_usd: Decimal = d("5000.000000"),
    bid_ask_spread_ratio: Decimal = d("0.015000"),
    liquidity_signal_confidence: Decimal = d("0.720000"),
    research_signal_confidence: Decimal = d("0.700000"),
    catalyst_pressure: Decimal = d("0.200000"),
    confidence_dispersion: Decimal = d("0.080000"),
) -> Any:
    module = api()
    return module.ResearchMarketLiquiditySignalConsistencyInput(
        market_reference=market_reference,
        evidence_reference=evidence_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=2),
        quote_observed_at=quote_observed_at or GENERATED_AT - timedelta(minutes=1),
        evidence_observed_at=evidence_observed_at or GENERATED_AT - timedelta(hours=1),
        aggregate_depth_usd=aggregate_depth_usd,
        bid_ask_spread_ratio=bid_ask_spread_ratio,
        liquidity_signal_confidence=liquidity_signal_confidence,
        research_signal_confidence=research_signal_confidence,
        catalyst_pressure=catalyst_pressure,
        confidence_dispersion=confidence_dispersion,
    )


def report(
    *samples: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_market_liquidity_signal_consistency_report(
        samples,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)


def test_liquidity_signal_consistency_report_reduces_public_safe_rows() -> None:
    module = api()
    mixed = report(
        sample(),
        sample(
            "https://markets.example/raw-watch?token=watch-secret",
            evidence_reference="https://feed.example/raw-watch?secret=watch-token",
            quote_observed_at=GENERATED_AT - timedelta(minutes=15),
            evidence_observed_at=GENERATED_AT - timedelta(hours=6),
            aggregate_depth_usd=d("700.000000"),
            bid_ask_spread_ratio=d("0.060000"),
            liquidity_signal_confidence=d("0.650000"),
            research_signal_confidence=d("0.400000"),
            catalyst_pressure=d("0.650000"),
            confidence_dispersion=d("0.300000"),
        ),
        sample(
            "https://markets.example/raw-block?token=block-secret",
            evidence_reference="https://feed.example/raw-block?secret=block-token",
            quote_observed_at=GENERATED_AT - timedelta(minutes=40),
            evidence_observed_at=GENERATED_AT - timedelta(days=3),
            aggregate_depth_usd=d("100.000000"),
            bid_ask_spread_ratio=d("0.150000"),
            liquidity_signal_confidence=d("0.100000"),
            research_signal_confidence=d("0.850000"),
            catalyst_pressure=d("0.900000"),
            confidence_dispersion=d("0.600000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(mixed, module.ResearchMarketLiquiditySignalConsistencyReport)
    assert is_dataclass(mixed)
    assert mixed.generated_at == GENERATED_AT
    assert mixed.generated_at.tzinfo is UTC
    assert module.REPORT_STATUSES == ("pass", "watch", "block")
    assert mixed.report_status == "block"
    assert mixed.sample_count == d("3.000000")
    assert mixed.pass_count == d("1.000000")
    assert mixed.watch_count == d("1.000000")
    assert mixed.block_count == d("1.000000")
    assert mixed.thin_depth_count == d("2.000000")
    assert mixed.wide_spread_count == d("2.000000")
    assert mixed.stale_quote_count == d("2.000000")
    assert mixed.stale_evidence_count == d("1.000000")
    assert mixed.catalyst_pressure_count == d("2.000000")
    assert mixed.confidence_dispersion_count == d("2.000000")
    assert mixed.confidence_gap_count == d("2.000000")
    assert mixed.max_quote_age_seconds == d("2400.000000")
    assert mixed.max_evidence_age_seconds == d("259200.000000")

    assert tuple(row.consistency_status for row in mixed.rows) == (
        "block",
        "watch",
        "pass",
    )
    blocked, watched, passed = mixed.rows
    assert blocked.reason_codes == (
        "research_market_liquidity_signal_consistency_aggregate_depth_block",
        "research_market_liquidity_signal_consistency_spread_block",
        "research_market_liquidity_signal_consistency_quote_stale_block",
        "research_market_liquidity_signal_consistency_evidence_stale_block",
        "research_market_liquidity_signal_consistency_catalyst_pressure_block",
        "research_market_liquidity_signal_consistency_confidence_dispersion_block",
        "research_market_liquidity_signal_consistency_confidence_gap_block",
    )
    assert watched.reason_codes == (
        "research_market_liquidity_signal_consistency_aggregate_depth_watch",
        "research_market_liquidity_signal_consistency_spread_watch",
        "research_market_liquidity_signal_consistency_quote_stale_watch",
        "research_market_liquidity_signal_consistency_catalyst_pressure_watch",
        "research_market_liquidity_signal_consistency_confidence_dispersion_watch",
        "research_market_liquidity_signal_consistency_confidence_gap_watch",
    )
    assert passed.reason_codes == (
        "research_market_liquidity_signal_consistency_consistent",
    )
    assert all(row.public_row_id.startswith("sha256:") for row in mixed.rows)
    assert all(row.paper_only and row.report_only and row.readonly for row in mixed.rows)
    assert mixed.paper_only is True
    assert mixed.report_only is True
    assert mixed.readonly is True

    public = repr(asdict(mixed)).lower()
    for token in (
        "https://",
        "token=",
        "secret",
        "markets.example",
        "feed.example",
        "raw-pass",
        "raw-watch",
        "raw-block",
    ):
        assert token not in public


def test_empty_report_payload_and_digest_are_deterministic_decimal_strings() -> None:
    module = api()
    empty = report()

    assert empty.report_status == "block"
    assert empty.sample_count == ZERO
    assert empty.rows == ()
    assert empty.reason_codes == (
        "research_market_liquidity_signal_consistency_no_inputs",
    )
    assert empty.reason_code_counts == (
        module.ResearchMarketLiquiditySignalConsistencyReasonCodeCount(
            reason_code="research_market_liquidity_signal_consistency_no_inputs",
            count=d("1.000000"),
            sample_ratio=ZERO,
        ),
    )

    payload = module.research_market_liquidity_signal_consistency_report_payload(
        report(sample()),
    )
    digest = module.research_market_liquidity_signal_consistency_report_digest(
        report(sample()),
    )

    assert json.dumps(payload, sort_keys=True)
    assert payload == module.research_market_liquidity_signal_consistency_report_payload(
        report(sample()),
    )
    assert payload == module.research_market_liquidity_signal_consistency_report_payload(
        report(sample(), generated_at=GENERATED_AT),
    )
    assert digest == hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    assert digest == module.research_market_liquidity_signal_consistency_report_digest(
        report(sample()),
    )
    assert payload["generated_at"] == "2026-07-04T15:00:00+00:00"
    assert payload["sample_count"] == "1.000000"
    assert payload["average_aggregate_depth_usd"] == "5000.000000"
    assert payload["rows"][0]["quote_age_seconds"] == "60.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in walk_values(payload))

    assert report(
        sample(),
        sample(
            "https://markets.example/second?token=secret",
            evidence_reference="https://feed.example/second?secret=token",
            aggregate_depth_usd=d("900.000000"),
        ),
    ) == report(
        sample(
            "https://markets.example/second?token=secret",
            evidence_reference="https://feed.example/second?secret=token",
            aggregate_depth_usd=d("900.000000"),
        ),
        sample(),
    )


def test_payload_revalidates_tampered_reports_and_public_safety() -> None:
    module = api()
    good = report(sample())

    tampered_count = replace(good)
    object.__setattr__(tampered_count, "sample_count", d("2.000000"))
    with pytest.raises(ValueError, match="sample_count"):
        module.research_market_liquidity_signal_consistency_report_payload(
            tampered_count,
        )

    unsafe_row = replace(good.rows[0])
    object.__setattr__(unsafe_row, "public_row_id", "https://unsafe.example?token=x")
    tampered_row = replace(good)
    object.__setattr__(tampered_row, "rows", (unsafe_row,))
    with pytest.raises(ValueError, match="unsafe|redacted"):
        module.research_market_liquidity_signal_consistency_report_payload(
            tampered_row,
        )

    tampered_flags = replace(good)
    object.__setattr__(tampered_flags, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        module.research_market_liquidity_signal_consistency_report_payload(
            tampered_flags,
        )

    bad_flag_row = replace(good.rows[0])
    object.__setattr__(bad_flag_row, "paper_only", False)
    tampered_nested_flags = replace(good)
    object.__setattr__(tampered_nested_flags, "rows", (bad_flag_row,))
    with pytest.raises(ValueError, match="paper_only"):
        module.research_market_liquidity_signal_consistency_report_payload(
            tampered_nested_flags,
        )

    with pytest.raises(ValueError, match="ResearchMarketLiquiditySignalConsistencyReport"):
        module.research_market_liquidity_signal_consistency_report_payload({"payload": 1})
    with pytest.raises(ValueError, match="ResearchMarketLiquiditySignalConsistencyReport"):
        module.research_market_liquidity_signal_consistency_report_digest({"payload": 1})


def test_dataclasses_are_frozen_hard_flagged_and_decimal_only() -> None:
    module = api()
    cfg = config()
    source = sample()
    built = report(source, cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        source.aggregate_depth_usd = d("1.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].consistency_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.sample_count = d("2.000000")  # type: ignore[misc]

    for public_type in (
        module.ResearchMarketLiquiditySignalConsistencyConfig,
        module.ResearchMarketLiquiditySignalConsistencyInput,
        module.ResearchMarketLiquiditySignalConsistencyRow,
        module.ResearchMarketLiquiditySignalConsistencyReasonCodeCount,
        module.ResearchMarketLiquiditySignalConsistencyReport,
    ):
        assert is_dataclass(public_type)
        assert all("float" not in str(field.type) for field in fields(public_type))
        assert all("int" not in str(field.type) for field in fields(public_type))

    numeric_public_fragments = {
        "age",
        "count",
        "depth",
        "dispersion",
        "gap",
        "pressure",
        "ratio",
        "score",
    }
    for item in (cfg, source, built, built.rows[0], built.reason_code_counts[0]):
        for field_name, value in asdict(item).items():
            if field_name in {"reason_code_counts", "reason_codes", "rows"}:
                continue
            if any(fragment in field_name for fragment in numeric_public_fragments):
                assert type(value) is Decimal, (field_name, type(value))
                assert value.as_tuple().exponent == -6

    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchMarketLiquiditySignalConsistencyInput(
            **{**asdict(source), "paper_only": False},
        )
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(built.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(built.reason_code_counts[0], report_only=False)


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: config(
                minimum_aggregate_depth_usd=_DecimalSubclass("1000.000000"),
            ),
            "Decimal",
        ),
        (lambda: config(blocked_aggregate_depth_usd=250), "Decimal"),
        (lambda: config(blocked_spread_ratio=d("0.030000")), "blocked_spread_ratio"),
        (lambda: config(maximum_quote_age_seconds=d("1800.000000")), "blocked"),
        (lambda: sample(aggregate_depth_usd=d("-1.000000")), "aggregate_depth_usd"),
        (lambda: sample(bid_ask_spread_ratio=d("1.500000")), "bid_ask_spread_ratio"),
        (lambda: sample(catalyst_pressure=50), "catalyst_pressure"),
        (lambda: sample(confidence_dispersion=d("-0.010000")), "confidence_dispersion"),
        (lambda: sample(market_reference=_StringSubclass("market-public")), "market"),
        (
            lambda: sample(
                observed_at=_DatetimeSubclass(2026, 7, 4, 14, 58, tzinfo=UTC),
            ),
            "observed_at",
        ),
        (
            lambda: sample(
                observed_at=datetime(2026, 7, 4, tzinfo=_NoneOffsetTzinfo()),
            ),
            "timezone-aware",
        ),
    ),
)
def test_validates_inputs(factory: object, message: str) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        factory()


def test_rejects_subclasses_duplicates_future_rows_and_inconsistent_reports() -> None:
    module = api()

    with pytest.raises(TypeError, match="subclassing"):
        type("ConfigSubclass", (module.ResearchMarketLiquiditySignalConsistencyConfig,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type("InputSubclass", (module.ResearchMarketLiquiditySignalConsistencyInput,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type("RowSubclass", (module.ResearchMarketLiquiditySignalConsistencyRow,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type(
            "ReasonCodeCountSubclass",
            (module.ResearchMarketLiquiditySignalConsistencyReasonCodeCount,),
            {},
        )
    with pytest.raises(TypeError, match="subclassing"):
        type("ReportSubclass", (module.ResearchMarketLiquiditySignalConsistencyReport,), {})

    with pytest.raises(ValueError, match="timezone-aware"):
        report(sample(), generated_at=datetime(2026, 7, 4, 15, 0))
    with pytest.raises(ValueError, match="after generated_at"):
        report(sample(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="after generated_at"):
        report(sample(quote_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="after generated_at"):
        report(sample(evidence_observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique redacted row identifiers"):
        report(sample(), sample())

    good = report(sample())
    with pytest.raises(ValueError, match="reason_codes"):
        replace(good, reason_codes=("unexpected",))
    with pytest.raises(ValueError, match="sample_count"):
        replace(good, sample_count=d("99.000000"))
    with pytest.raises(ValueError, match="rows must be ranked"):
        replace(
            report(
                sample(),
                sample(
                    "https://markets.example/second?token=secret",
                    evidence_reference="https://feed.example/second?secret=token",
                    aggregate_depth_usd=d("900.000000"),
                ),
            ),
            rows=tuple(
                reversed(
                    report(
                        sample(),
                        sample(
                            "https://markets.example/second?token=secret",
                            evidence_reference=(
                                "https://feed.example/second?secret=token"
                            ),
                            aggregate_depth_usd=d("900.000000"),
                        ),
                    ).rows,
                ),
            ),
        )


def test_module_scope_is_pure_report_only_and_has_no_forbidden_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "research_market_liquidity_signal_consistency_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "cancel",
        "replace",
        "exchange mutation",
        "private_key",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "database",
        "durable",
        "store",
        "open(",
        "live execution",
        "sizing",
        "recommend",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
        "pathlib",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "float",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
