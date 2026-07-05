from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_gold_rate_sensitivity_digest import (
    DEFAULT_MARKET_RESEARCH_GOLD_RATE_SENSITIVITY_DIGEST_CONFIG_VERSION,
    MarketResearchGoldRateSensitivityDigestConfig,
    MarketResearchGoldRateSensitivityDigestReasonCodeCount,
    MarketResearchGoldRateSensitivityDigestReport,
    MarketResearchGoldRateSensitivityDigestRow,
    MarketResearchGoldRateSensitivityDigestSignal,
    build_market_research_gold_rate_sensitivity_digest,
    market_research_gold_rate_sensitivity_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
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


def config(**overrides: object) -> MarketResearchGoldRateSensitivityDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_GOLD_RATE_SENSITIVITY_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_real_rate_beta": d("0.550000"),
        "min_nominal_rate_beta": d("0.300000"),
        "max_rate_volatility_score": d("0.700000"),
        "min_inverse_rate_confirmation": d("0.650000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "confidence_decay_per_gap": d("0.100000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchGoldRateSensitivityDigestConfig(**values)


def rate_signal(
    condition_id: str = "condition.gold.ready",
    *,
    gold_rate_key: str = "gold.real-rate.ready",
    rate_family: str = "real-rates",
    public_signal_reference: str = "treasury-real-yield-public-note",
    observed_at: datetime | None = None,
    real_rate_beta: Decimal = d("0.720000"),
    nominal_rate_beta: Decimal = d("0.420000"),
    rate_volatility_score: Decimal = d("0.300000"),
    inverse_rate_confirmation: Decimal = d("0.820000"),
    source_family_count: Decimal = d("4.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    base_confidence: Decimal = d("0.860000"),
    signal_config_version: str = "gold-rate-sensitivity-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchGoldRateSensitivityDigestSignal:
    return MarketResearchGoldRateSensitivityDigestSignal(
        condition_id=condition_id,
        gold_rate_key=gold_rate_key,
        rate_family=rate_family,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        real_rate_beta=real_rate_beta,
        nominal_rate_beta=nominal_rate_beta,
        rate_volatility_score=rate_volatility_score,
        inverse_rate_confirmation=inverse_rate_confirmation,
        source_family_count=source_family_count,
        stale_source_ratio=stale_source_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    signals: tuple[object, ...],
    *,
    cfg: MarketResearchGoldRateSensitivityDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchGoldRateSensitivityDigestReport:
    return build_market_research_gold_rate_sensitivity_digest(
        signals,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_gold_rate_sensitivity_digest_reduces_signals_deterministically() -> None:
    summary = report(
        (
            rate_signal(
                "condition.blocked",
                gold_rate_key="gold.rate.cpi",
                rate_family="inflation",
                public_signal_reference="https://gold.example/rates?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=3),
                real_rate_beta=d("0.300000"),
                nominal_rate_beta=d("0.200000"),
                rate_volatility_score=d("0.900000"),
                inverse_rate_confirmation=d("0.400000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
            rate_signal(
                "condition.watch",
                gold_rate_key="gold.rate.jobs",
                rate_family="labor-market",
                public_signal_reference="wallet://private/gold-rates-note",
                real_rate_beta=d("0.700000"),
                nominal_rate_beta=d("0.360000"),
                rate_volatility_score=d("0.500000"),
                inverse_rate_confirmation=d("0.550000"),
                source_family_count=d("3.000000"),
                stale_source_ratio=d("0.100000"),
                base_confidence=d("0.760000"),
            ),
            rate_signal(
                "condition.ready",
                gold_rate_key="gold.rate.real-yields",
                rate_family="real-rates",
                public_signal_reference="treasury-real-yield-public-note",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchGoldRateSensitivityDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_GOLD_RATE_SENSITIVITY_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_rate_sensitivity_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.low_real_rate_beta_signal_count == d("1.000000")
    assert summary.low_nominal_rate_beta_signal_count == d("1.000000")
    assert summary.rate_volatility_gap_signal_count == d("1.000000")
    assert summary.inverse_rate_confirmation_gap_signal_count == d("2.000000")
    assert summary.source_family_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.total_confidence_decay == d("0.700000")
    assert summary.average_final_confidence == d("0.606667")
    assert summary.average_real_rate_beta == d("0.573333")
    assert summary.average_inverse_rate_confirmation == d("0.590000")
    assert summary.max_observed_signal_age_seconds == d("10800.000000")
    assert tuple(row.gold_rate_key for row in summary.rows) == (
        "gold.rate.cpi",
        "gold.rate.jobs",
        "gold.rate.real-yields",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.confidence_decay_factor == d("0.600000")
    assert blocked.final_confidence == d("0.300000")
    assert blocked.redacted_public_signal_reference == "sha256:18ba37796eab"
    assert blocked.reason_codes == (
        "market_research_gold_rate_sensitivity_digest_stale_signal",
        "market_research_gold_rate_sensitivity_digest_low_real_rate_beta",
        "market_research_gold_rate_sensitivity_digest_low_nominal_rate_beta",
        "market_research_gold_rate_sensitivity_digest_rate_volatility_gap",
        "market_research_gold_rate_sensitivity_digest_inverse_rate_confirmation_gap",
        "market_research_gold_rate_sensitivity_digest_source_family_gap",
        "market_research_gold_rate_sensitivity_digest_stale_source_ratio",
    )

    watched = summary.rows[1]
    assert watched.digest_status == "watch"
    assert watched.confidence_decay_factor == d("0.100000")
    assert watched.final_confidence == d("0.660000")
    assert watched.redacted_public_signal_reference == "sha256:194d87750166"
    assert watched.reason_codes == (
        "market_research_gold_rate_sensitivity_digest_inverse_rate_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.860000")
    assert ready.redacted_public_signal_reference == "treasury-real-yield-public-note"
    assert ready.reason_codes == (
        "market_research_gold_rate_sensitivity_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchGoldRateSensitivityDigestReasonCodeCount(
            reason_code="market_research_gold_rate_sensitivity_digest_inverse_rate_confirmation_gap",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchGoldRateSensitivityDigestReasonCodeCount(
            reason_code="market_research_gold_rate_sensitivity_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRateSensitivityDigestReasonCodeCount(
            reason_code="market_research_gold_rate_sensitivity_digest_low_real_rate_beta",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRateSensitivityDigestReasonCodeCount(
            reason_code="market_research_gold_rate_sensitivity_digest_low_nominal_rate_beta",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRateSensitivityDigestReasonCodeCount(
            reason_code="market_research_gold_rate_sensitivity_digest_rate_volatility_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRateSensitivityDigestReasonCodeCount(
            reason_code="market_research_gold_rate_sensitivity_digest_source_family_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRateSensitivityDigestReasonCodeCount(
            reason_code="market_research_gold_rate_sensitivity_digest_stale_source_ratio",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRateSensitivityDigestReasonCodeCount(
            reason_code="market_research_gold_rate_sensitivity_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.signal_config_versions == (
        ("gold.rate.cpi", "gold-rate-sensitivity-source-v0"),
        ("gold.rate.jobs", "gold-rate-sensitivity-source-v0"),
        ("gold.rate.real-yields", "gold-rate-sensitivity-source-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "gold.example",
        "wallet://",
        "private/gold-rates-note",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "network",
        "database",
        "token",
        "secret",
        "private",
    ):
        assert token not in public


def test_gold_rate_sensitivity_digest_empty_inputs_are_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_rate_sensitivity_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.average_final_confidence == ZERO
    assert summary.average_real_rate_beta == ZERO
    assert summary.average_inverse_rate_confirmation == ZERO
    assert summary.max_observed_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.signal_config_versions == ()
    assert summary.reason_codes == (
        "market_research_gold_rate_sensitivity_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchGoldRateSensitivityDigestReasonCodeCount(
            reason_code="market_research_gold_rate_sensitivity_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )


def test_gold_rate_sensitivity_digest_rejects_manual_row_status_drift() -> None:
    ready_row = report((rate_signal(),)).rows[0]
    with pytest.raises(ValueError, match="digest_status"):
        replace(ready_row, digest_status="blocked")

    blocked_row = report(
        (
            rate_signal(
                "condition.gold.stale",
                gold_rate_key="gold.real-rate.stale",
                observed_at=GENERATED_AT - timedelta(hours=3),
            ),
        ),
    ).rows[0]
    assert blocked_row.reason_codes == (
        "market_research_gold_rate_sensitivity_digest_stale_signal",
    )
    with pytest.raises(ValueError, match="digest_status"):
        replace(blocked_row, digest_status="watch")


def test_gold_rate_sensitivity_digest_rejects_false_phase1_flags() -> None:
    summary = report((rate_signal(),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]

    cases = (
        ("config paper_only", lambda: config(paper_only=False), "paper_only"),
        ("config report_only", lambda: config(report_only=False), "report_only"),
        ("config readonly", lambda: config(readonly=False), "readonly"),
        ("signal paper_only", lambda: rate_signal(paper_only=False), "paper_only"),
        ("signal report_only", lambda: rate_signal(report_only=False), "report_only"),
        ("signal readonly", lambda: rate_signal(readonly=False), "readonly"),
        ("row paper_only", lambda: replace(row, paper_only=False), "paper_only"),
        ("row report_only", lambda: replace(row, report_only=False), "report_only"),
        ("row readonly", lambda: replace(row, readonly=False), "readonly"),
        (
            "reason count paper_only",
            lambda: replace(reason_count, paper_only=False),
            "paper_only",
        ),
        (
            "reason count report_only",
            lambda: replace(reason_count, report_only=False),
            "report_only",
        ),
        (
            "reason count readonly",
            lambda: replace(reason_count, readonly=False),
            "readonly",
        ),
        ("report paper_only", lambda: replace(summary, paper_only=False), "paper_only"),
        ("report report_only", lambda: replace(summary, report_only=False), "report_only"),
        ("report readonly", lambda: replace(summary, readonly=False), "readonly"),
    )

    for _label, factory, match in cases:
        with pytest.raises(ValueError, match=match):
            factory()


def test_gold_rate_sensitivity_digest_validates_types_flags_and_payload() -> None:
    assert MarketResearchGoldRateSensitivityDigestConfig.__dataclass_params__.frozen
    assert MarketResearchGoldRateSensitivityDigestSignal.__dataclass_params__.frozen
    assert MarketResearchGoldRateSensitivityDigestRow.__dataclass_params__.frozen
    assert (
        MarketResearchGoldRateSensitivityDigestReasonCodeCount.__dataclass_params__.frozen
    )
    assert MarketResearchGoldRateSensitivityDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("gold-rate-sensitivity-v0"))
    with pytest.raises(ValueError, match="max_signal_age_seconds"):
        config(max_signal_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="min_real_rate_beta"):
        config(min_real_rate_beta=0.55)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="condition_id"):
        rate_signal(condition_id=_StringSubclass("condition.gold"))
    with pytest.raises(ValueError, match="rate_family"):
        rate_signal(rate_family="broker-feed")
    with pytest.raises(ValueError, match="observed_at"):
        rate_signal(observed_at=datetime(2026, 7, 3, 11, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (rate_signal(),),
            generated_at=_DatetimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_market_research_gold_rate_sensitivity_digest(
            (),
            config=False,  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future"):
        report((rate_signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="real_rate_beta"):
        rate_signal(real_rate_beta=Decimal("NaN"))
    with pytest.raises(ValueError, match="source_family_count"):
        rate_signal(source_family_count=d("2.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(rate_signal(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        rate_signal().paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="unique"):
        report(
            (
                rate_signal(gold_rate_key="duplicate.gold.rate"),
                rate_signal(gold_rate_key="duplicate.gold.rate"),
            ),
        )

    payload = market_research_gold_rate_sensitivity_digest_payload(
        report((rate_signal(),)),
    )
    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["final_confidence"] == "0.860000"
    assert "public_signal_reference" not in payload["rows"][0]
    assert "datetime." not in repr(payload).lower()
    assert "decimal(" not in repr(payload).lower()


def test_gold_rate_sensitivity_digest_public_dataclasses_reject_subclassing() -> None:
    public_dataclasses = (
        MarketResearchGoldRateSensitivityDigestConfig,
        MarketResearchGoldRateSensitivityDigestSignal,
        MarketResearchGoldRateSensitivityDigestRow,
        MarketResearchGoldRateSensitivityDigestReasonCodeCount,
        MarketResearchGoldRateSensitivityDigestReport,
    )

    for dataclass_type in public_dataclasses:
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Unsafe{dataclass_type.__name__}", (dataclass_type,), {})


def test_gold_rate_sensitivity_digest_rejects_manual_noncanonical_ordering() -> None:
    summary = report(
        (
            rate_signal(
                "condition.gold.blocked",
                gold_rate_key="gold.a.blocked",
                observed_at=GENERATED_AT - timedelta(hours=3),
                real_rate_beta=d("0.300000"),
            ),
            rate_signal(
                "condition.gold.ready",
                gold_rate_key="gold.z.ready",
            ),
        ),
    )
    blocked_row = summary.rows[0]
    assert len(blocked_row.reason_codes) > 1

    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(blocked_row, reason_codes=tuple(reversed(blocked_row.reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            summary,
            reason_code_counts=tuple(reversed(summary.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="signal_config_versions"):
        replace(
            summary,
            signal_config_versions=tuple(reversed(summary.signal_config_versions)),
        )


def test_gold_rate_sensitivity_digest_payload_keeps_six_decimal_strings() -> None:
    summary = report((rate_signal(),))

    payload = market_research_gold_rate_sensitivity_digest_payload(summary)

    assert payload["signal_count"] == "1.000000"


def test_gold_rate_sensitivity_digest_payload_rejects_nested_false_phase1_flags() -> None:
    summary = report((rate_signal(),))
    object.__setattr__(summary.rows[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        market_research_gold_rate_sensitivity_digest_payload(summary)


def test_gold_rate_sensitivity_digest_payload_rejects_nested_non_six_decimal_values() -> None:
    summary = report((rate_signal(),))
    object.__setattr__(summary.rows[0], "source_family_count", d("4.0000001"))

    with pytest.raises(ValueError, match="six decimals"):
        market_research_gold_rate_sensitivity_digest_payload(summary)


def test_gold_rate_sensitivity_digest_rejects_none_utcoffset_timezone() -> None:
    non_aware_datetime = datetime(2026, 7, 3, 11, 30, tzinfo=_NoneOffsetTimezone())

    with pytest.raises(ValueError, match="timezone-aware"):
        rate_signal(observed_at=non_aware_datetime)
    with pytest.raises(ValueError, match="timezone-aware"):
        report((rate_signal(),), generated_at=non_aware_datetime)


def test_gold_rate_sensitivity_digest_redacts_api_key_references() -> None:
    summary = report(
        (
            rate_signal(
                public_signal_reference=(
                    "https://gold.example/rates?api_key=gold-rate-alpha-123"
                ),
            ),
        ),
    )

    assert summary.rows[0].redacted_public_signal_reference.startswith("sha256:")
    public = repr(asdict(summary)).lower()
    assert "api_key" not in public
    assert "gold-rate-alpha-123" not in public


def test_gold_rate_sensitivity_digest_rejects_zero_manual_reason_code_counts() -> None:
    with pytest.raises(ValueError, match="count"):
        MarketResearchGoldRateSensitivityDigestReasonCodeCount(
            reason_code="market_research_gold_rate_sensitivity_digest_ready",
            count=ZERO,
            signal_ratio=ZERO,
        )


def test_gold_rate_sensitivity_digest_rejects_count_decimals_that_round_integral() -> None:
    with pytest.raises(ValueError, match="source_family_count"):
        rate_signal(source_family_count=d("2.9999996"))

    with pytest.raises(ValueError, match="count"):
        MarketResearchGoldRateSensitivityDigestReasonCodeCount(
            reason_code="market_research_gold_rate_sensitivity_digest_ready",
            count=d("0.9999996"),
            signal_ratio=d("1.000000"),
        )


def test_gold_rate_sensitivity_digest_has_no_io_auth_wallet_or_trading_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_gold_rate_sensitivity_digest.py",
    ).read_text()
    tree = ast.parse(source)
    forbidden_calls = {
        "connect",
        "open",
        "request",
        "urlopen",
        "run",
        "Popen",
    }
    forbidden_import_roots = {
        "asyncio",
        "http",
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
    forbidden_text = (
        "private_key",
        "api_key",
        "api-key",
        "apikey",
        "password",
        "credential",
        "bearer",
        "wallet",
        "order",
        "trade",
        "cancel",
        "replace",
        "exchange",
        "mutation",
        "auth",
        "token",
        "live trading",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls

    lowered_source = source.lower()
    for token in forbidden_text:
        assert token not in lowered_source
