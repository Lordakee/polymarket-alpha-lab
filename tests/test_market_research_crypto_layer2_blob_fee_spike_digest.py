from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_crypto_layer2_blob_fee_spike_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_LAYER2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig,
    MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount,
    MarketResearchCryptoLayer2BlobFeeSpikeDigestReport,
    MarketResearchCryptoLayer2BlobFeeSpikeDigestRow,
    MarketResearchCryptoLayer2BlobFeeSpikeObservation,
    build_market_research_crypto_layer2_blob_fee_spike_digest,
    market_research_crypto_layer2_blob_fee_spike_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_crypto_layer2_blob_fee_spike_digest.py",
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


def _observation(
    screening_key: str = "base_blob_fee_window",
    *,
    condition_id: str = "condition_alpha",
    layer2_name: str = "Base",
    rollup_family: str = "optimistic",
    observed_at: datetime = GENERATED_AT,
    blob_base_fee_gwei: Decimal = d("12.000000"),
    baseline_blob_base_fee_gwei: Decimal = d("10.000000"),
    blob_gas_used_ratio: Decimal = d("0.600000"),
    data_availability_backlog_ratio: Decimal = d("0.100000"),
    batch_submission_delay_seconds: Decimal = d("120.000000"),
    source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "layer2-blob-source-v0",
) -> MarketResearchCryptoLayer2BlobFeeSpikeObservation:
    return MarketResearchCryptoLayer2BlobFeeSpikeObservation(
        screening_key=screening_key,
        condition_id=condition_id,
        layer2_name=layer2_name,
        rollup_family=rollup_family,
        observed_at=observed_at,
        blob_base_fee_gwei=blob_base_fee_gwei,
        baseline_blob_base_fee_gwei=baseline_blob_base_fee_gwei,
        blob_gas_used_ratio=blob_gas_used_ratio,
        data_availability_backlog_ratio=data_availability_backlog_ratio,
        batch_submission_delay_seconds=batch_submission_delay_seconds,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _config(
    **overrides: object,
) -> MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_LAYER2_BLOB_FEE_SPIKE_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("1800.000000"),
        "watch_blob_base_fee_spike_ratio": d("0.750000"),
        "blocked_blob_base_fee_spike_ratio": d("2.000000"),
        "max_blob_gas_used_ratio": d("0.850000"),
        "max_data_availability_backlog_ratio": d("0.600000"),
        "max_batch_submission_delay_seconds": d("600.000000"),
        "min_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig(**values)


def _report(
    *observations: MarketResearchCryptoLayer2BlobFeeSpikeObservation,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig | None = None,
) -> MarketResearchCryptoLayer2BlobFeeSpikeDigestReport:
    return build_market_research_crypto_layer2_blob_fee_spike_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_watch_digest() -> None:
    report = _report()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-crypto-layer2-blob-fee-spike-digest-v0"
    )
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_market_research_crypto_layer2_blob_fee_spike_digest"
    )
    assert report.observation_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_crypto_layer2_blob_fee_spike_digest_no_inputs",
    )
    assert report.reason_code_counts == ()
    assert report.average_blob_base_fee_spike_ratio == d("0.000000")
    assert report.max_observation_age_seconds == d("0.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_risk_blob_fee_pressure_blocks_screening_report() -> None:
    report = _report(
        _observation(
            "base_high_pressure",
            condition_id="condition_beta",
            layer2_name="Base",
            observed_at=GENERATED_AT - timedelta(seconds=2400),
            blob_base_fee_gwei=d("45.000000"),
            baseline_blob_base_fee_gwei=d("10.000000"),
            blob_gas_used_ratio=d("0.930000"),
            data_availability_backlog_ratio=d("0.750000"),
            batch_submission_delay_seconds=d("900.000000"),
            source_count=d("1.000000"),
            confidence=d("0.500000"),
        ),
        _observation(
            "optimism_normal_pressure",
            condition_id="condition_alpha",
            layer2_name="Optimism",
        ),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_layer2_blob_fee_spike_digest"
    )
    assert report.observation_count == d("2.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.blob_base_fee_spike_observation_count == d("1.000000")
    assert report.blob_gas_congestion_observation_count == d("1.000000")
    assert report.data_availability_backlog_observation_count == d("1.000000")
    assert report.batch_submission_delay_observation_count == d("1.000000")
    assert report.source_diversity_gap_observation_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.confidence_gap_observation_count == d("1.000000")
    assert report.average_blob_base_fee_spike_ratio == d("1.850000")
    assert report.average_blob_gas_used_ratio == d("0.765000")
    assert report.average_data_availability_backlog_ratio == d("0.425000")
    assert report.average_batch_submission_delay_seconds == d("510.000000")
    assert report.max_observation_age_seconds == d("2400.000000")

    assert tuple(row.screening_key for row in report.rows) == (
        "base_high_pressure",
        "optimism_normal_pressure",
    )
    high_risk = report.rows[0]
    assert high_risk.digest_status == "blocked"
    assert high_risk.observation_age_seconds == d("2400.000000")
    assert high_risk.blob_base_fee_spike_ratio == d("3.500000")
    assert high_risk.reason_codes == (
        "market_research_crypto_layer2_blob_fee_spike_digest_blob_base_fee_spike",
        "market_research_crypto_layer2_blob_fee_spike_digest_blob_gas_congestion",
        "market_research_crypto_layer2_blob_fee_spike_digest_data_availability_backlog",
        "market_research_crypto_layer2_blob_fee_spike_digest_batch_submission_delay",
        "market_research_crypto_layer2_blob_fee_spike_digest_source_diversity_gap",
        "market_research_crypto_layer2_blob_fee_spike_digest_stale_observation",
        "market_research_crypto_layer2_blob_fee_spike_digest_confidence_gap",
    )
    assert report.reason_codes == high_risk.reason_codes


def test_sorting_reason_counts_and_timezone_normalization_are_deterministic() -> None:
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 4, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    first = _report(
        _observation("zeta_signal", observed_at=observed_at),
        _observation("alpha_signal", layer2_name="Arbitrum"),
        generated_at=generated_at,
    )
    second = _report(
        _observation("alpha_signal", layer2_name="Arbitrum"),
        _observation("zeta_signal", observed_at=observed_at),
        generated_at=generated_at,
    )

    assert first == second
    assert tuple(row.screening_key for row in first.rows) == (
        "zeta_signal",
        "alpha_signal",
    )
    assert first.generated_at == GENERATED_AT
    assert first.rows[0].observed_at == datetime(2026, 7, 4, 11, 0, tzinfo=UTC)
    assert first.max_observation_age_seconds == d("3600.000000")
    assert first.digest_status == "blocked"
    assert first.reason_code_counts == (
        MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_layer2_blob_fee_spike_digest_stale_observation"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.500000"),
        ),
    )
    assert first.source_config_versions == (
        ("alpha_signal", "layer2-blob-source-v0"),
        ("zeta_signal", "layer2-blob-source-v0"),
    )


def test_non_default_threshold_can_keep_moderate_spike_ready() -> None:
    moderate = _observation(
        "moderate_spike",
        blob_base_fee_gwei=d("18.000000"),
        baseline_blob_base_fee_gwei=d("10.000000"),
    )

    default_report = _report(moderate)
    relaxed_report = _report(
        moderate,
        config=_config(watch_blob_base_fee_spike_ratio=d("0.900000")),
    )

    assert default_report.digest_status == "watch"
    assert default_report.rows[0].reason_codes == (
        "market_research_crypto_layer2_blob_fee_spike_digest_blob_base_fee_spike",
    )
    assert relaxed_report.digest_status == "ready"
    assert relaxed_report.rows[0].reason_codes == (
        "market_research_crypto_layer2_blob_fee_spike_digest_ready",
    )
    assert relaxed_report.watch_blob_base_fee_spike_ratio == d("0.900000")


def test_validates_exact_types_utc_flags_duplicates_and_freezing() -> None:
    assert MarketResearchCryptoLayer2BlobFeeSpikeDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoLayer2BlobFeeSpikeObservation.__dataclass_params__.frozen
    assert MarketResearchCryptoLayer2BlobFeeSpikeDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoLayer2BlobFeeSpikeDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("layer2-blob-v0"))
    with pytest.raises(ValueError, match="watch_blob_base_fee_spike_ratio"):
        _config(watch_blob_base_fee_spike_ratio=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="watch_blob_base_fee_spike_ratio"):
        _config(
            watch_blob_base_fee_spike_ratio=d("2.500000"),
            blocked_blob_base_fee_spike_ratio=d("2.000000"),
        )
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=3)
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="screening_key"):
        _observation(screening_key=_StringSubclass("base_blob_fee_window"))
    with pytest.raises(ValueError, match="redacted"):
        _observation(source_config_version="source-wallet-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="future"):
        _report(_observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        _report(_observation("duplicate"), _observation("duplicate"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _observation().paper_only = False  # type: ignore[misc]


def test_public_numerics_are_decimal_only_and_payload_numbers_are_strings() -> None:
    report = _report(_observation())

    for item in (report, report.rows[0], report.reason_code_counts[0]):
        for field in fields(item):
            value = getattr(item, field.name)
            if _is_public_numeric_field(field.name) or field.name == "confidence":
                assert type(value) is Decimal, field.name

    with pytest.raises(ValueError, match="observation_count"):
        MarketResearchCryptoLayer2BlobFeeSpikeDigestReport(
            **{
                **{field.name: getattr(report, field.name) for field in fields(report)},
                "observation_count": 1,  # type: ignore[arg-type]
            },
        )

    payload = market_research_crypto_layer2_blob_fee_spike_digest_payload(report)
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["rows"][0]["blob_base_fee_gwei"] == "12.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_int_or_decimal_payload_numbers(payload)
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["blob_base_fee_gwei"] = "1.000000"  # type: ignore[index]


def test_report_consistency_and_hard_flags_are_enforced() -> None:
    report = _report(_observation())
    kwargs = {field.name: getattr(report, field.name) for field in fields(report)}

    assert MarketResearchCryptoLayer2BlobFeeSpikeDigestReport(**kwargs) == report
    with pytest.raises(ValueError, match="digest_status"):
        MarketResearchCryptoLayer2BlobFeeSpikeDigestReport(
            **{**kwargs, "digest_status": "blocked"},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoLayer2BlobFeeSpikeDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_layer2_blob_fee_spike_digest_ready"
                        ),
                        count=d("2.000000"),
                        observation_ratio=d("1.000000"),
                    ),
                ),
            },
        )
    with pytest.raises(ValueError, match="readonly"):
        MarketResearchCryptoLayer2BlobFeeSpikeDigestReasonCodeCount(
            reason_code="market_research_crypto_layer2_blob_fee_spike_digest_ready",
            count=d("1.000000"),
            observation_ratio=d("1.000000"),
            readonly=False,
        )


def test_module_scope_excludes_execution_io_network_persistence_and_secret_logic() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_layer2_blob_fee_spike_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    for forbidden in (
        "private_key",
        "requests",
        "httpx",
        "urlopen",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "connect(",
        "execute(",
        "cancel",
        "replace_order",
        "payload_json",
    ):
        assert forbidden not in lowered

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {
                    "open",
                    "eval",
                    "exec",
                    "__import__",
                    "connect",
                    "execute",
                }

    assert imported_modules <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "datetime",
        "decimal",
        "types",
        "typing",
    }
    assert MODULE_PATH.read_text() == source_text


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_seconds")
        or field_name.endswith("_ratio")
        or field_name.endswith("_gwei")
    )


def _assert_no_float_int_or_decimal_payload_numbers(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_int_or_decimal_payload_numbers(item)
        return
    if isinstance(value, tuple):
        for item in value:
            _assert_no_float_int_or_decimal_payload_numbers(item)
        return
    if isinstance(value, bool):
        return
    assert not isinstance(value, (Decimal, float, int))
