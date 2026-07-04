from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_crypto_bridge_finality_dispute_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_FINALITY_DISPUTE_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoBridgeFinalityDisputeDigestConfig,
    MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount,
    MarketResearchCryptoBridgeFinalityDisputeDigestReport,
    MarketResearchCryptoBridgeFinalityDisputeDigestRow,
    MarketResearchCryptoBridgeFinalityDisputeObservation,
    build_market_research_crypto_bridge_finality_dispute_digest,
    market_research_crypto_bridge_finality_dispute_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_crypto_bridge_finality_dispute_digest.py",
)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(
    **overrides: object,
) -> MarketResearchCryptoBridgeFinalityDisputeDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_FINALITY_DISPUTE_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("1800.000000"),
        "max_finality_lag_seconds": d("900.000000"),
        "max_finality_expansion_ratio": d("0.500000"),
        "max_dispute_window_seconds": d("3600.000000"),
        "max_challenge_ratio": d("0.050000"),
        "min_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoBridgeFinalityDisputeDigestConfig(**values)


def _observation(
    condition_id: str = "condition_alpha",
    bridge_finality_key: str = "arb_eth_finality",
    *,
    bridge_name: str = "Arbitrum",
    source_chain: str = "ethereum",
    destination_chain: str = "arbitrum",
    observed_at: datetime = GENERATED_AT,
    finality_lag_seconds: Decimal = d("300.000000"),
    baseline_finality_seconds: Decimal = d("240.000000"),
    dispute_window_seconds: Decimal = d("600.000000"),
    challenged_transfer_count: Decimal = d("0.000000"),
    finalized_transfer_count: Decimal = d("100.000000"),
    source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "bridge-finality-source-v0",
) -> MarketResearchCryptoBridgeFinalityDisputeObservation:
    return MarketResearchCryptoBridgeFinalityDisputeObservation(
        condition_id=condition_id,
        bridge_finality_key=bridge_finality_key,
        bridge_name=bridge_name,
        source_chain=source_chain,
        destination_chain=destination_chain,
        observed_at=observed_at,
        finality_lag_seconds=finality_lag_seconds,
        baseline_finality_seconds=baseline_finality_seconds,
        dispute_window_seconds=dispute_window_seconds,
        challenged_transfer_count=challenged_transfer_count,
        finalized_transfer_count=finalized_transfer_count,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *observations: MarketResearchCryptoBridgeFinalityDisputeObservation,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoBridgeFinalityDisputeDigestConfig | None = None,
) -> MarketResearchCryptoBridgeFinalityDisputeDigestReport:
    return build_market_research_crypto_bridge_finality_dispute_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_floats(item)


def test_bridge_finality_dispute_digest_models_finality_and_dispute_pressure() -> None:
    report = _report(
        _observation(
            "condition_beta",
            "op_usdc_finality",
            bridge_name="Optimism",
            source_chain="ethereum",
            destination_chain="optimism",
            observed_at=GENERATED_AT - timedelta(seconds=2400),
            finality_lag_seconds=d("1200.000000"),
            baseline_finality_seconds=d("300.000000"),
            dispute_window_seconds=d("7200.000000"),
            challenged_transfer_count=d("12.000000"),
            finalized_transfer_count=d("100.000000"),
            source_count=d("1.000000"),
            confidence=d("0.550000"),
        ),
        _observation(
            "condition_alpha",
            "arb_eth_finality",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_bridge_finality_dispute_digest"
    )
    assert report.observation_count == d("2.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.finality_lag_observation_count == d("1.000000")
    assert report.finality_expansion_observation_count == d("1.000000")
    assert report.dispute_window_observation_count == d("1.000000")
    assert report.challenge_pressure_observation_count == d("1.000000")
    assert report.source_diversity_gap_observation_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.confidence_gap_observation_count == d("1.000000")
    assert report.average_finality_lag_seconds == d("750.000000")
    assert report.average_finality_expansion_ratio == d("1.625000")
    assert report.average_challenge_ratio == d("0.060000")
    assert report.observed_max_finality_lag_seconds == d("1200.000000")
    assert report.observed_max_dispute_window_seconds == d("7200.000000")
    assert report.max_observation_age_seconds == d("2400.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.bridge_finality_key) for row in report.rows) == (
        ("condition_beta", "op_usdc_finality"),
        ("condition_alpha", "arb_eth_finality"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.observation_age_seconds == d("2400.000000")
    assert beta.finality_expansion_ratio == d("3.000000")
    assert beta.challenge_ratio == d("0.120000")
    assert beta.reason_codes == (
        "market_research_crypto_bridge_finality_dispute_digest_finality_lag",
        "market_research_crypto_bridge_finality_dispute_digest_finality_expansion",
        "market_research_crypto_bridge_finality_dispute_digest_dispute_window",
        "market_research_crypto_bridge_finality_dispute_digest_challenge_pressure",
        "market_research_crypto_bridge_finality_dispute_digest_source_diversity_gap",
        "market_research_crypto_bridge_finality_dispute_digest_stale_observation",
        "market_research_crypto_bridge_finality_dispute_digest_confidence_gap",
    )
    assert report.reason_codes == beta.reason_codes


def test_bridge_finality_dispute_digest_normalizes_timezones_reason_counts_and_sources() -> None:
    generated_at = datetime(2026, 7, 4, 12, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 4, 16, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _observation(
            "condition_gamma",
            "base_eth_finality",
            bridge_name="Base",
            destination_chain="base",
            observed_at=observed_at,
            source_count=d("2.000000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
    assert report.max_observation_age_seconds == d("3600.000000")
    assert report.digest_status == "blocked"
    assert report.reason_code_counts == (
        MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_bridge_finality_dispute_digest_source_diversity_gap"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
        MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_bridge_finality_dispute_digest_stale_observation"
            ),
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("base_eth_finality", "bridge-finality-source-v0"),
    )


def test_bridge_finality_dispute_digest_empty_input_and_sorting_are_deterministic() -> None:
    empty = _report()
    assert empty.digest_status == "watch"
    assert empty.observation_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_bridge_finality_dispute_digest_no_inputs",
    )

    first = _report(
        _observation("condition_b", "source_b"),
        _observation("condition_a", "source_a"),
    )
    second = _report(
        _observation("condition_a", "source_a"),
        _observation("condition_b", "source_b"),
    )

    assert first == second
    assert tuple(row.bridge_finality_key for row in first.rows) == (
        "source_a",
        "source_b",
    )


def test_bridge_finality_dispute_digest_validates_exact_types_flags_and_freezing() -> None:
    assert MarketResearchCryptoBridgeFinalityDisputeDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoBridgeFinalityDisputeObservation.__dataclass_params__.frozen
    assert MarketResearchCryptoBridgeFinalityDisputeDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoBridgeFinalityDisputeDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("bridge-finality-v0"))
    with pytest.raises(ValueError, match="max_finality_expansion_ratio"):
        _config(max_finality_expansion_ratio=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=3)
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=0.8)
    with pytest.raises(ValueError, match="condition_id"):
        _observation(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="redacted"):
        _observation(source_config_version="source-order-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=datetime(2026, 7, 4, 16, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 4, 16, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="finality_lag_seconds"):
        _observation(finality_lag_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="challenged_transfer_count"):
        _observation(challenged_transfer_count=d("101.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _observation().paper_only = False  # type: ignore[misc]


def test_bridge_finality_dispute_digest_public_numeric_fields_are_decimal_only() -> None:
    report = _report(_observation())

    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_seconds")
                or field.name.endswith("_ratio")
                or field.name == "confidence"
            ):
                assert type(value) is Decimal
    for field in fields(report):
        value = getattr(report, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
        ):
            assert type(value) is Decimal
    for reason_count in report.reason_code_counts:
        assert type(reason_count.count) is Decimal
        assert type(reason_count.observation_ratio) is Decimal

    kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchCryptoBridgeFinalityDisputeDigestReport)
    }
    with pytest.raises(ValueError, match="observation_count"):
        MarketResearchCryptoBridgeFinalityDisputeDigestReport(
            **{**kwargs, "observation_count": 1},
        )


def test_bridge_finality_dispute_digest_payload_is_immutable_redacted_and_report_only() -> None:
    payload = market_research_crypto_bridge_finality_dispute_digest_payload(
        _report(
            _observation(
                "condition_redacted",
                "arb_eth_finality_redacted",
                bridge_name="Arbitrum",
            ),
        ),
    )
    payload_text = repr(payload).lower()

    for forbidden in (
        "market_slug",
        "question",
        "wallet",
        "order",
        "auth",
        "token",
        "secret",
        "private",
        "payload_json",
    ):
        assert forbidden not in payload_text
    assert_no_floats(payload)
    assert payload["payload_kind"] == (
        "market_research_crypto_bridge_finality_dispute_digest"
    )
    assert payload["generated_at"] == "2026-07-04T16:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-04T16:00:00+00:00"
    assert payload["rows"][0]["finality_lag_seconds"] == "300.000000"
    assert payload["rows"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["finality_lag_seconds"] = "1.000000"  # type: ignore[index]


def test_bridge_finality_dispute_digest_rejects_duplicates_and_bad_report_consistency() -> None:
    with pytest.raises(ValueError, match="unique"):
        _report(
            _observation(bridge_finality_key="duplicate"),
            _observation(bridge_finality_key="duplicate"),
        )

    valid = _report(_observation())
    kwargs = {
        field.name: getattr(valid, field.name)
        for field in fields(MarketResearchCryptoBridgeFinalityDisputeDigestReport)
    }
    assert (
        MarketResearchCryptoBridgeFinalityDisputeDigestReport(**kwargs).digest_status
        == "ready"
    )

    with pytest.raises(ValueError, match="observation_count"):
        MarketResearchCryptoBridgeFinalityDisputeDigestReport(
            **{**kwargs, "observation_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="digest_status"):
        MarketResearchCryptoBridgeFinalityDisputeDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoBridgeFinalityDisputeDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_bridge_finality_dispute_digest_ready"
                        ),
                        count=d("2.000000"),
                        observation_ratio=d("1.000000"),
                    ),
                ),
            },
        )


def test_bridge_finality_dispute_digest_static_source_is_pure_and_safe() -> None:
    source = MODULE_PATH.read_text()
    lowered = source.lower()
    for forbidden in (
        "market_slug",
        "question",
        "trading",
        "trade",
        "auth",
        "wallet",
        "order",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "account",
        "advice",
        "network",
        "database",
        "store",
        "durable",
        "supabase",
        "persist",
        "sqlite",
        "exchange_mutation",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"open", "eval", "exec", "__import__"}
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def test_bridge_finality_dispute_digest_module_stays_unwired() -> None:
    root = MODULE_PATH.parent
    needle = "market_research_crypto_bridge_finality_dispute_digest"
    references: list[str] = []
    for path in root.glob("*.py"):
        if path == MODULE_PATH:
            continue
        if needle in path.read_text():
            references.append(str(path))

    assert references == []


def test_bridge_finality_dispute_digest_import_surface_is_explicit() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_bridge_finality_dispute_digest",
    )

    assert set(module.__all__) == {
        "DEFAULT_MARKET_RESEARCH_CRYPTO_BRIDGE_FINALITY_DISPUTE_DIGEST_CONFIG_VERSION",
        "MarketResearchCryptoBridgeFinalityDisputeDigestConfig",
        "MarketResearchCryptoBridgeFinalityDisputeDigestReasonCodeCount",
        "MarketResearchCryptoBridgeFinalityDisputeDigestReport",
        "MarketResearchCryptoBridgeFinalityDisputeDigestRow",
        "MarketResearchCryptoBridgeFinalityDisputeObservation",
        "build_market_research_crypto_bridge_finality_dispute_digest",
        "market_research_crypto_bridge_finality_dispute_digest_payload",
    }
