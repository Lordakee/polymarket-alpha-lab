from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_gold_real_yield_divergence_digest import (
    DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_DIVERGENCE_DIGEST_CONFIG_VERSION,
    MarketResearchGoldRealYieldDivergenceDigestConfig,
    MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount,
    MarketResearchGoldRealYieldDivergenceDigestReport,
    MarketResearchGoldRealYieldDivergenceDigestRow,
    MarketResearchGoldRealYieldDivergenceDigestSignal,
    build_market_research_gold_real_yield_divergence_digest,
    market_research_gold_real_yield_divergence_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchGoldRealYieldDivergenceDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_DIVERGENCE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_gold_momentum_score": d("0.550000"),
        "min_real_yield_inverse_momentum_score": d("0.550000"),
        "min_divergence_score": d("0.450000"),
        "min_divergence_confirmation_score": d("0.650000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "confidence_decay_per_gap": d("0.100000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchGoldRealYieldDivergenceDigestConfig(**values)


def divergence_signal(
    condition_id: str = "condition.gold.ready",
    *,
    gold_real_yield_key: str = "gold.real-yield.ready",
    divergence_family: str = "real-yields",
    public_signal_reference: str = "treasury-real-yield-public-note",
    observed_at: datetime | None = None,
    gold_momentum_score: Decimal = d("0.740000"),
    real_yield_inverse_momentum_score: Decimal = d("0.720000"),
    divergence_score: Decimal = d("0.760000"),
    divergence_confirmation_score: Decimal = d("0.820000"),
    source_family_count: Decimal = d("4.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    base_confidence: Decimal = d("0.860000"),
    signal_config_version: str = "gold-real-yield-divergence-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchGoldRealYieldDivergenceDigestSignal:
    return MarketResearchGoldRealYieldDivergenceDigestSignal(
        condition_id=condition_id,
        gold_real_yield_key=gold_real_yield_key,
        divergence_family=divergence_family,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        gold_momentum_score=gold_momentum_score,
        real_yield_inverse_momentum_score=real_yield_inverse_momentum_score,
        divergence_score=divergence_score,
        divergence_confirmation_score=divergence_confirmation_score,
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
    cfg: MarketResearchGoldRealYieldDivergenceDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchGoldRealYieldDivergenceDigestReport:
    return build_market_research_gold_real_yield_divergence_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float_or_int(value: Any) -> None:
    if type(value) is float or type(value) is int:
        pytest.fail(f"found public numeric that is not a Decimal string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)


def test_gold_real_yield_divergence_digest_reduces_signals_deterministically() -> None:
    summary = report(
        (
            divergence_signal(
                "condition.blocked",
                gold_real_yield_key="gold.real-yield.cpi",
                divergence_family="inflation",
                public_signal_reference="https://gold.example/real-yields?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=3),
                gold_momentum_score=d("0.300000"),
                real_yield_inverse_momentum_score=d("0.200000"),
                divergence_score=d("0.300000"),
                divergence_confirmation_score=d("0.400000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
            divergence_signal(
                "condition.watch",
                gold_real_yield_key="gold.real-yield.jobs",
                divergence_family="labor-market",
                public_signal_reference="wallet://private/gold-real-yield-note",
                divergence_score=d("0.700000"),
                divergence_confirmation_score=d("0.550000"),
                base_confidence=d("0.760000"),
            ),
            divergence_signal(
                "condition.ready",
                gold_real_yield_key="gold.real-yield.tips",
                divergence_family="real-yields",
                public_signal_reference="treasury-real-yield-public-note",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchGoldRealYieldDivergenceDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_GOLD_REAL_YIELD_DIVERGENCE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_real_yield_divergence_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.low_gold_momentum_signal_count == d("1.000000")
    assert summary.low_real_yield_inverse_momentum_signal_count == d("1.000000")
    assert summary.low_divergence_score_signal_count == d("1.000000")
    assert summary.divergence_confirmation_gap_signal_count == d("2.000000")
    assert summary.source_family_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.total_confidence_decay == d("0.700000")
    assert summary.average_final_confidence == d("0.606667")
    assert summary.average_divergence_score == d("0.586667")
    assert summary.average_divergence_confirmation_score == d("0.590000")
    assert summary.max_observed_signal_age_seconds == d("10800.000000")
    assert tuple(row.gold_real_yield_key for row in summary.rows) == (
        "gold.real-yield.cpi",
        "gold.real-yield.jobs",
        "gold.real-yield.tips",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.signal_age_seconds == d("10800.000000")
    assert blocked.confidence_decay_factor == d("0.600000")
    assert blocked.final_confidence == d("0.300000")
    assert blocked.redacted_public_signal_reference.startswith("sha256:")
    assert blocked.reason_codes == (
        "market_research_gold_real_yield_divergence_digest_stale_signal",
        "market_research_gold_real_yield_divergence_digest_low_gold_momentum",
        "market_research_gold_real_yield_divergence_digest_low_real_yield_inverse_momentum",
        "market_research_gold_real_yield_divergence_digest_low_divergence_score",
        "market_research_gold_real_yield_divergence_digest_confirmation_gap",
        "market_research_gold_real_yield_divergence_digest_source_family_gap",
        "market_research_gold_real_yield_divergence_digest_stale_source_ratio",
    )

    watched = summary.rows[1]
    assert watched.digest_status == "watch"
    assert watched.confidence_decay_factor == d("0.100000")
    assert watched.final_confidence == d("0.660000")
    assert watched.redacted_public_signal_reference.startswith("sha256:")
    assert watched.reason_codes == (
        "market_research_gold_real_yield_divergence_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.860000")
    assert ready.redacted_public_signal_reference == "treasury-real-yield-public-note"
    assert ready.reason_codes == (
        "market_research_gold_real_yield_divergence_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_divergence_digest_confirmation_gap",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_divergence_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_divergence_digest_low_gold_momentum",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount(
            reason_code=(
                "market_research_gold_real_yield_divergence_digest_"
                "low_real_yield_inverse_momentum"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_divergence_digest_low_divergence_score",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_divergence_digest_source_family_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_divergence_digest_stale_source_ratio",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_divergence_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.signal_config_versions == (
        ("gold.real-yield.cpi", "gold-real-yield-divergence-source-v0"),
        ("gold.real-yield.jobs", "gold-real-yield-divergence-source-v0"),
        ("gold.real-yield.tips", "gold-real-yield-divergence-source-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    public = repr(asdict(summary)).lower()
    for term in (
        "secret-123",
        "gold.example",
        "wallet://",
        "private/gold-real-yield-note",
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
        assert term not in public


def test_gold_real_yield_divergence_digest_empty_inputs_are_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_gold_real_yield_divergence_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.average_final_confidence == ZERO
    assert summary.average_divergence_score == ZERO
    assert summary.average_divergence_confirmation_score == ZERO
    assert summary.max_observed_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.signal_config_versions == ()
    assert summary.reason_codes == (
        "market_research_gold_real_yield_divergence_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount(
            reason_code="market_research_gold_real_yield_divergence_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )


def test_gold_real_yield_divergence_digest_validates_types_flags_and_payload() -> None:
    assert MarketResearchGoldRealYieldDivergenceDigestConfig.__dataclass_params__.frozen
    assert MarketResearchGoldRealYieldDivergenceDigestSignal.__dataclass_params__.frozen
    assert MarketResearchGoldRealYieldDivergenceDigestRow.__dataclass_params__.frozen
    assert (
        MarketResearchGoldRealYieldDivergenceDigestReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert MarketResearchGoldRealYieldDivergenceDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("gold-real-yield-divergence-v0"))
    with pytest.raises(ValueError, match="max_signal_age_seconds"):
        config(max_signal_age_seconds=_DecimalSubclass("7200.000000"))
    with pytest.raises(ValueError, match="min_divergence_score"):
        config(min_divergence_score=0.45)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="condition_id"):
        divergence_signal(condition_id=_StringSubclass("condition.gold"))
    with pytest.raises(ValueError, match="divergence_family"):
        divergence_signal(divergence_family="broker-feed")
    with pytest.raises(ValueError, match="observed_at"):
        divergence_signal(observed_at=datetime(2026, 7, 3, 11, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (divergence_signal(),),
            generated_at=_DatetimeSubclass(2026, 7, 3, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        report((divergence_signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="divergence_score"):
        divergence_signal(divergence_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="source_family_count"):
        divergence_signal(source_family_count=d("2.500000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(divergence_signal(), paper_only=False)

    summary = report((divergence_signal(),))
    with pytest.raises(FrozenInstanceError):
        config().paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        divergence_signal().paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="unique"):
        report(
            (
                divergence_signal(gold_real_yield_key="duplicate.gold.real-yield"),
                divergence_signal(gold_real_yield_key="duplicate.gold.real-yield"),
            ),
        )

    payload = market_research_gold_real_yield_divergence_digest_payload(
        report((divergence_signal(),)),
    )
    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["final_confidence"] == "0.860000"
    assert "public_signal_reference" not in payload["rows"][0]
    assert "datetime." not in repr(payload).lower()
    assert "decimal(" not in repr(payload).lower()
    assert_no_float_or_int(payload)


def test_gold_real_yield_divergence_digest_validates_direct_report_consistency() -> None:
    summary = report((divergence_signal(),))

    with pytest.raises(ValueError, match="ready_signal_count"):
        replace(summary, ready_signal_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=())
    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary, reason_codes=())
    with pytest.raises(ValueError, match="signal_count"):
        replace(summary, signal_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_gold_real_yield_divergence_digest_rejects_false_phase1_flags(
    flag_name: str,
) -> None:
    summary = report((divergence_signal(),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]

    flagged_config_values: dict[str, object] = {flag_name: False}
    flagged_signal_values: dict[str, object] = {flag_name: False}

    with pytest.raises(ValueError, match=flag_name):
        config(**flagged_config_values)
    with pytest.raises(ValueError, match=flag_name):
        divergence_signal(**flagged_signal_values)
    with pytest.raises(ValueError, match=flag_name):
        replace(row, **{flag_name: False})
    with pytest.raises(ValueError, match=flag_name):
        replace(reason_count, **{flag_name: False})
    with pytest.raises(ValueError, match=flag_name):
        replace(summary, **{flag_name: False})


def test_gold_real_yield_divergence_digest_has_no_io_or_live_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/market_research_gold_real_yield_divergence_digest.py",
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
        "wallet",
        "order",
        "trade",
        "cancel",
        "auth",
        "token",
        "live trading",
        "exchange",
        "mutation",
        "network",
        "database",
        "secret",
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
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            if isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls

    lowered = source.lower()
    for term in forbidden_text:
        assert term not in lowered
