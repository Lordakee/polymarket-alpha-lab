from __future__ import annotations

import ast
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_gold_real_yield_shock_digest import (
    DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_SHOCK_DIGEST_CONFIG_VERSION,
    MarketResearchGoldRealYieldShockDigestConfig,
    MarketResearchGoldRealYieldShockDigestReasonCodeCount,
    MarketResearchGoldRealYieldShockDigestReport,
    MarketResearchGoldRealYieldShockDigestRow,
    MarketResearchGoldRealYieldShockDigestSignal,
    build_market_research_gold_real_yield_shock_digest,
    market_research_gold_real_yield_shock_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 5, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchGoldRealYieldShockDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_SHOCK_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_real_yield_move_bp_abs": d("12.000000"),
        "min_gold_inverse_move_pct_abs": d("0.750000"),
        "min_etf_flow_pressure_ratio_abs": d("0.200000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "min_confirmation_ratio": d("0.650000"),
        "confidence_decay_per_gap": d("0.100000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchGoldRealYieldShockDigestConfig(**values)


def signal(
    condition_id: str = "condition.gold.real-yield.ready",
    *,
    shock_key: str = "gold.real-yield.ready",
    public_signal_reference: str = "treasury-real-yield-public-release",
    observed_at: datetime | None = None,
    real_yield_move_bp: Decimal = d("18.000000"),
    gold_inverse_move_pct: Decimal = d("1.200000"),
    etf_flow_pressure_ratio: Decimal = d("0.350000"),
    source_family_count: Decimal = d("4.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    confirmation_ratio: Decimal = d("0.820000"),
    base_confidence: Decimal = d("0.860000"),
    signal_config_version: str = "gold-real-yield-shock-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchGoldRealYieldShockDigestSignal:
    return MarketResearchGoldRealYieldShockDigestSignal(
        condition_id=condition_id,
        shock_key=shock_key,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        real_yield_move_bp=real_yield_move_bp,
        gold_inverse_move_pct=gold_inverse_move_pct,
        etf_flow_pressure_ratio=etf_flow_pressure_ratio,
        source_family_count=source_family_count,
        stale_source_ratio=stale_source_ratio,
        confirmation_ratio=confirmation_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    signals: tuple[object, ...],
    *,
    cfg: MarketResearchGoldRealYieldShockDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchGoldRealYieldShockDigestReport:
    return build_market_research_gold_real_yield_shock_digest(
        signals,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_gold_real_yield_shock_digest_reduces_signals_deterministically() -> None:
    summary = report(
        (
            signal(
                "condition.blocked",
                shock_key="gold.shock.cpi",
                public_signal_reference=(
                    "https://gold.example/real-yields?token=secret-123"
                ),
                observed_at=GENERATED_AT - timedelta(hours=3),
                real_yield_move_bp=d("8.000000"),
                gold_inverse_move_pct=d("0.300000"),
                etf_flow_pressure_ratio=d("0.100000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
            signal(
                "condition.watch",
                shock_key="gold.shock.tips-auction",
                public_signal_reference="wallet://private/gold-real-yield-note",
                real_yield_move_bp=d("-15.000000"),
                gold_inverse_move_pct=d("-0.900000"),
                etf_flow_pressure_ratio=d("0.300000"),
                source_family_count=d("3.000000"),
                stale_source_ratio=d("0.100000"),
                confirmation_ratio=d("0.550000"),
                base_confidence=d("0.760000"),
            ),
            signal(
                "condition.ready",
                shock_key="gold.shock.real-yields",
                public_signal_reference="treasury-real-yield-public-release",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchGoldRealYieldShockDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_SHOCK_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_real_yield_shock_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.low_real_yield_move_signal_count == d("1.000000")
    assert summary.low_gold_inverse_move_signal_count == d("1.000000")
    assert summary.low_etf_flow_pressure_signal_count == d("1.000000")
    assert summary.source_family_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.confirmation_gap_signal_count == d("2.000000")
    assert summary.total_confidence_decay == d("0.700000")
    assert summary.average_final_confidence == d("0.606667")
    assert summary.average_real_yield_move_bp_abs == d("13.666667")
    assert summary.average_gold_inverse_move_pct_abs == d("0.800000")
    assert summary.average_etf_flow_pressure_ratio_abs == d("0.250000")
    assert summary.average_confirmation_ratio == d("0.590000")
    assert summary.max_observed_signal_age_seconds == d("10800.000000")
    assert tuple(row.shock_key for row in summary.rows) == (
        "gold.shock.cpi",
        "gold.shock.tips-auction",
        "gold.shock.real-yields",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.real_yield_move_bp_abs == d("8.000000")
    assert blocked.gold_inverse_move_pct_abs == d("0.300000")
    assert blocked.etf_flow_pressure_ratio_abs == d("0.100000")
    assert blocked.confidence_decay_factor == d("0.600000")
    assert blocked.final_confidence == d("0.300000")
    assert blocked.redacted_public_signal_reference == "sha256:c7552da2eaea"
    assert blocked.reason_codes == (
        "market_research_gold_real_yield_shock_digest_stale_signal",
        "market_research_gold_real_yield_shock_digest_low_real_yield_move",
        "market_research_gold_real_yield_shock_digest_low_gold_inverse_move",
        "market_research_gold_real_yield_shock_digest_low_etf_flow_pressure",
        "market_research_gold_real_yield_shock_digest_source_family_gap",
        "market_research_gold_real_yield_shock_digest_stale_source_ratio",
        "market_research_gold_real_yield_shock_digest_confirmation_gap",
    )

    watched = summary.rows[1]
    assert watched.digest_status == "watch"
    assert watched.real_yield_move_bp_abs == d("15.000000")
    assert watched.gold_inverse_move_pct_abs == d("0.900000")
    assert watched.etf_flow_pressure_ratio_abs == d("0.300000")
    assert watched.confidence_decay_factor == d("0.100000")
    assert watched.final_confidence == d("0.660000")
    assert watched.redacted_public_signal_reference == "sha256:146e9449553a"
    assert watched.reason_codes == (
        "market_research_gold_real_yield_shock_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.860000")
    assert ready.redacted_public_signal_reference == "treasury-real-yield-public-release"
    assert ready.reason_codes == (
        "market_research_gold_real_yield_shock_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchGoldRealYieldShockDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_real_yield_shock_digest_confirmation_gap"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchGoldRealYieldShockDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_shock_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldShockDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_real_yield_shock_digest_low_real_yield_move"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldShockDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_real_yield_shock_digest_low_gold_inverse_move"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldShockDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_real_yield_shock_digest_low_etf_flow_pressure"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldShockDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_real_yield_shock_digest_source_family_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldShockDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_real_yield_shock_digest_stale_source_ratio"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldShockDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_shock_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.signal_config_versions == (
        ("gold.shock.cpi", "gold-real-yield-shock-source-v0"),
        ("gold.shock.tips-auction", "gold-real-yield-shock-source-v0"),
        ("gold.shock.real-yields", "gold-real-yield-shock-source-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_empty_digest_is_blocked_report_only_with_one_reason_count() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_real_yield_shock_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.total_confidence_decay == ZERO
    assert summary.average_final_confidence == ZERO
    assert summary.average_real_yield_move_bp_abs == ZERO
    assert summary.average_gold_inverse_move_pct_abs == ZERO
    assert summary.average_etf_flow_pressure_ratio_abs == ZERO
    assert summary.average_confirmation_ratio == ZERO
    assert summary.max_observed_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.signal_config_versions == ()
    assert summary.reason_codes == (
        "market_research_gold_real_yield_shock_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchGoldRealYieldShockDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_shock_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_dataclasses_are_frozen_and_public_numbers_are_exact_decimals() -> None:
    summary = report((signal(),))

    public_dataclasses = (
        MarketResearchGoldRealYieldShockDigestConfig,
        MarketResearchGoldRealYieldShockDigestSignal,
        MarketResearchGoldRealYieldShockDigestRow,
        MarketResearchGoldRealYieldShockDigestReasonCodeCount,
        MarketResearchGoldRealYieldShockDigestReport,
    )
    for dataclass_type in public_dataclasses:
        assert dataclass_type.__dataclass_params__.frozen
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Unsafe{dataclass_type.__name__}", (dataclass_type,), {})

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].final_confidence = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        config().max_signal_age_seconds = ZERO  # type: ignore[misc]

    for value in (config(), signal(), summary.rows[0], summary.reason_code_counts[0], summary):
        assert is_dataclass(value)
        for item_field in fields(value):
            if item_field.name in {"paper_only", "report_only", "readonly"}:
                continue
            item = getattr(value, item_field.name)
            if (
                item_field.name.endswith("_count")
                or item_field.name.endswith("_ratio")
                or item_field.name.endswith("_seconds")
                or item_field.name.endswith("_confidence")
                or item_field.name.endswith("_decay")
                or item_field.name.endswith("_bp")
                or item_field.name.endswith("_bp_abs")
                or item_field.name.endswith("_pct")
                or item_field.name.endswith("_pct_abs")
                or item_field.name.endswith("_abs")
            ):
                assert type(item) is Decimal, item_field.name


def test_validation_rejects_noncanonical_types_timezones_and_false_flags() -> None:
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("gold-real-yield-shock-v0"))
    with pytest.raises(ValueError, match="max_signal_age_seconds"):
        config(max_signal_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="min_real_yield_move_bp_abs"):
        config(min_real_yield_move_bp_abs=12)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="condition_id"):
        signal(condition_id=_StringSubclass("condition.gold"))
    with pytest.raises(ValueError, match="condition_id"):
        signal(condition_id="condition-order-flow")
    with pytest.raises(ValueError, match="shock_key"):
        signal(shock_key="gold.wallet.flow")
    with pytest.raises(ValueError, match="signal_config_version"):
        signal(signal_config_version="config-auth-surface")
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 5, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report((signal(),), generated_at=_DatetimeSubclass(2026, 7, 5, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 5, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            (signal(),),
            generated_at=datetime(2026, 7, 5, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="config"):
        build_market_research_gold_real_yield_shock_digest(
            (),
            config=False,  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future"):
        report((signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="real_yield_move_bp"):
        signal(real_yield_move_bp=_DecimalSubclass("12.000000"))
    with pytest.raises(ValueError, match="real_yield_move_bp"):
        signal(real_yield_move_bp=12)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_family_count"):
        signal(source_family_count=d("2.500000"))
    with pytest.raises(ValueError, match="source_family_count"):
        signal(source_family_count=d("2.9999996"))
    with pytest.raises(ValueError, match="signals must contain"):
        report(("not-a-signal",))
    with pytest.raises(ValueError, match="unique"):
        report(
            (
                signal(shock_key="duplicate.gold.shock"),
                signal(shock_key="duplicate.gold.shock"),
            ),
        )

    summary = report((signal(),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]
    false_flag_cases = (
        lambda: config(paper_only=False),
        lambda: config(report_only=False),
        lambda: config(readonly=False),
        lambda: signal(paper_only=False),
        lambda: signal(report_only=False),
        lambda: signal(readonly=False),
        lambda: replace(row, paper_only=False),
        lambda: replace(row, report_only=False),
        lambda: replace(row, readonly=False),
        lambda: replace(reason_count, paper_only=False),
        lambda: replace(reason_count, report_only=False),
        lambda: replace(reason_count, readonly=False),
        lambda: replace(summary, paper_only=False),
        lambda: replace(summary, report_only=False),
        lambda: replace(summary, readonly=False),
    )
    for factory in false_flag_cases:
        with pytest.raises(ValueError, match="must be True"):
            factory()


def test_manual_public_records_reject_status_drift_and_noncanonical_ordering() -> None:
    summary = report(
        (
            signal(
                "condition.blocked",
                shock_key="gold.a.blocked",
                observed_at=GENERATED_AT - timedelta(hours=3),
                real_yield_move_bp=d("8.000000"),
                gold_inverse_move_pct=d("0.300000"),
                etf_flow_pressure_ratio=d("0.100000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
            signal(
                "condition.ready",
                shock_key="gold.z.ready",
            ),
        ),
    )
    blocked_row = summary.rows[0]
    assert len(blocked_row.reason_codes) > 1

    with pytest.raises(ValueError, match="digest_status"):
        replace(blocked_row, digest_status="ready")
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(blocked_row, reason_codes=tuple(reversed(blocked_row.reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            summary,
            reason_code_counts=tuple(reversed(summary.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary, reason_codes=tuple(reversed(summary.reason_codes)))
    with pytest.raises(ValueError, match="signal_config_versions"):
        replace(
            summary,
            signal_config_versions=tuple(reversed(summary.signal_config_versions)),
        )


def test_reason_code_count_rejects_zero_manual_count() -> None:
    with pytest.raises(ValueError, match="count must be positive"):
        MarketResearchGoldRealYieldShockDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_shock_digest_ready",
            count=ZERO,
            signal_ratio=ZERO,
        )


def test_payload_is_json_safe_deterministic_and_keeps_six_decimal_strings() -> None:
    summary = report(
        (
            signal("condition.b", shock_key="gold.z"),
            signal("condition.a", shock_key="gold.a"),
        ),
    )

    payload = market_research_gold_real_yield_shock_digest_payload(summary)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-05T15:00:00+00:00"
    assert payload["signal_count"] == "2.000000"
    assert payload["average_final_confidence"] == "0.860000"
    assert payload["max_observed_signal_age_seconds"] == "1800.000000"
    assert tuple(row["condition_id"] for row in payload["rows"]) == (
        "condition.a",
        "condition.b",
    )
    assert payload["rows"][0]["observed_at"] == "2026-07-05T14:30:00+00:00"
    assert payload["rows"][0]["real_yield_move_bp"] == "18.000000"
    assert payload["rows"][0]["gold_inverse_move_pct"] == "1.200000"
    assert "public_signal_reference" not in payload["rows"][0]

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))
            if isinstance(value, str) and re.fullmatch(r"-?\d+\.\d{6}", value):
                assert Decimal(value) == Decimal(value).quantize(d("0.000001"))

    walk(payload)


def test_payload_rejects_nested_false_phase1_flags() -> None:
    summary = report((signal(),))
    object.__setattr__(summary.rows[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        market_research_gold_real_yield_shock_digest_payload(summary)


def test_payload_rejects_nested_non_six_decimal_values() -> None:
    summary = report((signal(),))
    object.__setattr__(summary.rows[0], "source_family_count", d("4.0000001"))

    with pytest.raises(ValueError, match="six decimals"):
        market_research_gold_real_yield_shock_digest_payload(summary)


def test_redacts_public_references_without_leaking_unsafe_material() -> None:
    summary = report(
        (
            signal(
                public_signal_reference=(
                    "https://gold.example/real-yields?api_key=gold-shock-alpha-123"
                ),
            ),
        ),
    )

    assert summary.rows[0].redacted_public_signal_reference.startswith("sha256:")
    public = repr(summary).lower()
    assert "api_key" not in public
    assert "gold-shock-alpha-123" not in public


def test_static_purity_guards_reject_io_auth_wallet_and_trading_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_gold_real_yield_shock_digest.py",
    ).read_text()
    tree = ast.parse(source)
    lowered_source = source.lower()

    for forbidden in (
        "auth",
        "wallet",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered_source

    banned_imports = {
        "asyncio",
        "http",
        "httpx",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "connect",
        "open",
        "request",
        "urlopen",
        "run",
        "Popen",
        "get",
        "post",
        "put",
        "delete",
        "send",
        "submit",
        "cancel",
        "trade",
        "order",
        "wallet",
        "auth",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_imports
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_imports
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in banned_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in banned_calls
