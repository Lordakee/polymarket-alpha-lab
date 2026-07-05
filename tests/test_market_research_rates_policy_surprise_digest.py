from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_rates_policy_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_RATES_POLICY_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchRatesPolicySurpriseDigestConfig,
    MarketResearchRatesPolicySurpriseDigestReasonCodeCount,
    MarketResearchRatesPolicySurpriseDigestReport,
    MarketResearchRatesPolicySurpriseDigestRow,
    MarketResearchRatesPolicySurpriseDigestSignal,
    build_market_research_rates_policy_surprise_digest,
    market_research_rates_policy_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
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


def config(**overrides: object) -> MarketResearchRatesPolicySurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_RATES_POLICY_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_policy_signal_age_seconds": d("7200.000000"),
        "min_implied_probability_delta": d("0.050000"),
        "min_statement_surprise_score": d("0.600000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "min_confirmation_ratio": d("0.650000"),
        "confidence_decay_per_gap": d("0.100000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchRatesPolicySurpriseDigestConfig(**values)


def surprise_signal(
    condition_id: str = "condition.alpha",
    *,
    rates_policy_key: str = "fed.path.statement",
    central_bank: str = "fed",
    policy_event_key: str = "fomc.statement",
    public_signal_reference: str = "fomc-statement-calendar",
    observed_at: datetime | None = None,
    policy_signal_age_seconds: Decimal = d("900.000000"),
    implied_probability_delta: Decimal = d("0.080000"),
    statement_surprise_score: Decimal = d("0.750000"),
    source_family_count: Decimal = d("3.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.850000"),
    signal_config_version: str = "rates-policy-surprise-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchRatesPolicySurpriseDigestSignal:
    return MarketResearchRatesPolicySurpriseDigestSignal(
        condition_id=condition_id,
        rates_policy_key=rates_policy_key,
        central_bank=central_bank,
        policy_event_key=policy_event_key,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=15),
        policy_signal_age_seconds=policy_signal_age_seconds,
        implied_probability_delta=implied_probability_delta,
        statement_surprise_score=statement_surprise_score,
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
    cfg: MarketResearchRatesPolicySurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchRatesPolicySurpriseDigestReport:
    return build_market_research_rates_policy_surprise_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_plain_numbers(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError("payload must not expose plain float/int values")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_plain_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_plain_numbers(item)


def test_rates_policy_surprise_digest_reduces_signals_and_redacts_references() -> None:
    summary = report(
        (
            surprise_signal(
                "condition.fed",
                rates_policy_key="fed.path.cpi",
                central_bank="fed",
                policy_event_key="fomc.statement",
                public_signal_reference="https://rates.example/fomc?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=3),
                policy_signal_age_seconds=d("9000.000000"),
                implied_probability_delta=d("0.020000"),
                statement_surprise_score=d("0.400000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.350000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
            surprise_signal(
                "condition.ecb",
                rates_policy_key="ecb.path.guidance",
                central_bank="ecb",
                policy_event_key="ecb.press-conference",
                public_signal_reference="wallet://private/ecb-rates-note",
                implied_probability_delta=d("0.070000"),
                statement_surprise_score=d("0.700000"),
                source_family_count=d("3.000000"),
                stale_source_ratio=d("0.100000"),
                confirmation_ratio=d("0.550000"),
                base_confidence=d("0.760000"),
            ),
            surprise_signal(
                "condition.boe",
                rates_policy_key="boe.path.ready",
                central_bank="boe",
                policy_event_key="boe.minutes",
                public_signal_reference="boe-minutes-calendar",
                implied_probability_delta=d("0.090000"),
                statement_surprise_score=d("0.820000"),
                source_family_count=d("4.000000"),
                stale_source_ratio=d("0.050000"),
                confirmation_ratio=d("0.840000"),
                base_confidence=d("0.880000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert isinstance(summary, MarketResearchRatesPolicySurpriseDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_RATES_POLICY_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_rates_policy_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_policy_signal_count == d("1.000000")
    assert summary.low_probability_delta_signal_count == d("1.000000")
    assert summary.low_statement_surprise_signal_count == d("1.000000")
    assert summary.source_family_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.confirmation_gap_signal_count == d("2.000000")
    assert summary.total_confidence_decay == d("0.700000")
    assert summary.average_final_confidence == d("0.613333")
    assert summary.average_implied_probability_delta == d("0.060000")
    assert summary.average_statement_surprise_score == d("0.640000")
    assert summary.average_confirmation_ratio == d("0.596667")
    assert summary.max_observed_signal_age_seconds == d("10800.000000")
    assert tuple(row.rates_policy_key for row in summary.rows) == (
        "fed.path.cpi",
        "ecb.path.guidance",
        "boe.path.ready",
    )

    fed = summary.rows[0]
    assert fed.digest_status == "blocked"
    assert fed.signal_age_seconds == d("10800.000000")
    assert fed.confidence_decay_factor == d("0.600000")
    assert fed.final_confidence == d("0.300000")
    assert fed.redacted_public_signal_reference == "sha256:6c513eaacbb8"
    assert fed.reason_codes == (
        "market_research_rates_policy_surprise_digest_stale_policy_signal",
        "market_research_rates_policy_surprise_digest_low_probability_delta",
        "market_research_rates_policy_surprise_digest_low_statement_surprise",
        "market_research_rates_policy_surprise_digest_source_family_gap",
        "market_research_rates_policy_surprise_digest_stale_source_ratio",
        "market_research_rates_policy_surprise_digest_confirmation_gap",
    )

    ecb = summary.rows[1]
    assert ecb.digest_status == "watch"
    assert ecb.confidence_decay_factor == d("0.100000")
    assert ecb.final_confidence == d("0.660000")
    assert ecb.redacted_public_signal_reference == "sha256:f3885ce77589"
    assert ecb.reason_codes == (
        "market_research_rates_policy_surprise_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.880000")
    assert ready.redacted_public_signal_reference == "boe-minutes-calendar"
    assert ready.reason_codes == (
        "market_research_rates_policy_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
            reason_code="market_research_rates_policy_surprise_digest_confirmation_gap",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
            reason_code="market_research_rates_policy_surprise_digest_stale_policy_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
            reason_code="market_research_rates_policy_surprise_digest_low_probability_delta",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
            reason_code="market_research_rates_policy_surprise_digest_low_statement_surprise",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
            reason_code="market_research_rates_policy_surprise_digest_source_family_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
            reason_code="market_research_rates_policy_surprise_digest_stale_source_ratio",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
            reason_code="market_research_rates_policy_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.signal_config_versions == (
        ("boe.path.ready", "rates-policy-surprise-v0"),
        ("ecb.path.guidance", "rates-policy-surprise-v0"),
        ("fed.path.cpi", "rates-policy-surprise-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "rates.example",
        "wallet://",
        "private/ecb-rates-note",
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


def test_rates_policy_surprise_digest_empty_inputs_are_report_only_and_deterministic() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_rates_policy_surprise_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.average_final_confidence == ZERO
    assert summary.rows == ()
    assert summary.signal_config_versions == ()
    assert summary.reason_codes == (
        "market_research_rates_policy_surprise_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
            reason_code="market_research_rates_policy_surprise_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )


def test_rates_policy_surprise_digest_validates_types_flags_no_io_and_payload() -> None:
    assert MarketResearchRatesPolicySurpriseDigestConfig.__dataclass_params__.frozen
    assert MarketResearchRatesPolicySurpriseDigestSignal.__dataclass_params__.frozen
    assert MarketResearchRatesPolicySurpriseDigestRow.__dataclass_params__.frozen
    assert MarketResearchRatesPolicySurpriseDigestReasonCodeCount.__dataclass_params__.frozen
    assert MarketResearchRatesPolicySurpriseDigestReport.__dataclass_params__.frozen

    for public_dataclass in (
        MarketResearchRatesPolicySurpriseDigestConfig,
        MarketResearchRatesPolicySurpriseDigestSignal,
        MarketResearchRatesPolicySurpriseDigestRow,
        MarketResearchRatesPolicySurpriseDigestReasonCodeCount,
        MarketResearchRatesPolicySurpriseDigestReport,
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{public_dataclass.__name__}", (public_dataclass,), {})

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("rates-policy-surprise-v0"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="unsupported-version")
    with pytest.raises(ValueError, match="max_policy_signal_age_seconds"):
        config(max_policy_signal_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="min_confirmation_ratio"):
        config(min_confirmation_ratio=0.65)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="condition_id"):
        surprise_signal(condition_id=_StringSubclass("condition.alpha"))
    with pytest.raises(ValueError, match="central_bank"):
        surprise_signal(central_bank="fed private")
    with pytest.raises(ValueError, match="implied_probability_delta"):
        surprise_signal(implied_probability_delta=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (surprise_signal(),),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone offset"):
        report(
            (surprise_signal(),),
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="future"):
        report((surprise_signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="redacted"):
        surprise_signal(public_signal_reference="token=secret-123")
    with pytest.raises(ValueError, match="paper_only"):
        replace(surprise_signal(), paper_only=False)
    with pytest.raises(ValueError, match="count"):
        MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
            reason_code="market_research_rates_policy_surprise_digest_ready",
            count=ZERO,
            signal_ratio=ZERO,
        )
    with pytest.raises(FrozenInstanceError):
        surprise_signal().paper_only = False  # type: ignore[misc]

    payload = market_research_rates_policy_surprise_digest_payload(
        report((surprise_signal(),)),
    )
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["final_confidence"] == "0.850000"
    assert_no_public_plain_numbers(payload)
    assert "public_signal_reference" not in payload["rows"][0]

    source = Path(
        "src/polymarket_alpha_lab/market_research_rates_policy_surprise_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "account",
        "advice",
    ):
        assert forbidden not in source.lower()


def test_rates_policy_surprise_digest_payload_revalidates_mutated_public_surface() -> None:
    mutated_flag = report((surprise_signal(),))
    object.__setattr__(mutated_flag, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_rates_policy_surprise_digest_payload(mutated_flag)

    mutated_numeric = report((surprise_signal(),))
    object.__setattr__(mutated_numeric, "signal_count", 1)
    with pytest.raises(ValueError, match="Decimal|numeric"):
        market_research_rates_policy_surprise_digest_payload(mutated_numeric)

    mutated_reference = report((surprise_signal(),))
    object.__setattr__(
        mutated_reference.rows[0],
        "redacted_public_signal_reference",
        "token=secret-123",
    )
    with pytest.raises(ValueError, match="redacted|unsafe|sensitive"):
        market_research_rates_policy_surprise_digest_payload(mutated_reference)


def test_rates_policy_surprise_digest_rejects_duplicates_and_bad_consistency() -> None:
    with pytest.raises(ValueError, match="unique"):
        report(
            (
                surprise_signal(rates_policy_key="duplicate.event"),
                surprise_signal(rates_policy_key="duplicate.event"),
            ),
        )

    row = MarketResearchRatesPolicySurpriseDigestRow(
        condition_id="condition.alpha",
        rates_policy_key="fed.path.statement",
        central_bank="fed",
        policy_event_key="fomc.statement",
        digest_status="ready",
        observed_at=GENERATED_AT - timedelta(minutes=15),
        signal_age_seconds=d("900.000000"),
        policy_signal_age_seconds=d("900.000000"),
        implied_probability_delta=d("0.080000"),
        statement_surprise_score=d("0.750000"),
        source_family_count=d("3.000000"),
        stale_source_ratio=d("0.100000"),
        confirmation_ratio=d("0.800000"),
        base_confidence=d("0.850000"),
        confidence_decay_factor=ZERO,
        final_confidence=d("0.850000"),
        redacted_public_signal_reference="fomc-statement-calendar",
        reason_codes=("market_research_rates_policy_surprise_digest_ready",),
    )
    with pytest.raises(ValueError, match="reason_codes"):
        MarketResearchRatesPolicySurpriseDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_MARKET_RESEARCH_RATES_POLICY_SURPRISE_DIGEST_CONFIG_VERSION
            ),
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_rates_policy_surprise_digest"
            ),
            signal_count=d("1.000000"),
            ready_signal_count=d("1.000000"),
            watch_signal_count=ZERO,
            blocked_signal_count=ZERO,
            stale_policy_signal_count=ZERO,
            low_probability_delta_signal_count=ZERO,
            low_statement_surprise_signal_count=ZERO,
            source_family_gap_signal_count=ZERO,
            stale_source_signal_count=ZERO,
            confirmation_gap_signal_count=ZERO,
            total_confidence_decay=ZERO,
            average_final_confidence=d("0.850000"),
            average_implied_probability_delta=d("0.080000"),
            average_statement_surprise_score=d("0.750000"),
            average_confirmation_ratio=d("0.800000"),
            max_policy_signal_age_seconds=d("7200.000000"),
            min_implied_probability_delta=d("0.050000"),
            min_statement_surprise_score=d("0.600000"),
            min_source_family_count=d("3.000000"),
            max_stale_source_ratio=d("0.250000"),
            min_confirmation_ratio=d("0.650000"),
            max_observed_signal_age_seconds=d("900.000000"),
            rows=(row,),
            signal_config_versions=(("fed.path.statement", "rates-policy-surprise-v0"),),
            reason_code_counts=(
                MarketResearchRatesPolicySurpriseDigestReasonCodeCount(
                    reason_code="market_research_rates_policy_surprise_digest_ready",
                    count=d("1.000000"),
                    signal_ratio=d("1.000000"),
                ),
            ),
            reason_codes=(
                "market_research_rates_policy_surprise_digest_confirmation_gap",
            ),
        )

    with pytest.raises(TypeError, match="does not support subclassing"):
        class BadConfig(MarketResearchRatesPolicySurpriseDigestConfig):
            pass
