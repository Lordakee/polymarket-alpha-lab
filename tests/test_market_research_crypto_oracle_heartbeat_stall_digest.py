from __future__ import annotations

import ast
import importlib
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import MappingProxyType
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_crypto_oracle_heartbeat_stall_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_HEARTBEAT_STALL_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoOracleHeartbeatStallDigestConfig,
    MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount,
    MarketResearchCryptoOracleHeartbeatStallDigestReport,
    MarketResearchCryptoOracleHeartbeatStallDigestRow,
    MarketResearchCryptoOracleHeartbeatStallObservation,
    build_market_research_crypto_oracle_heartbeat_stall_digest,
    market_research_crypto_oracle_heartbeat_stall_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
SIX_DECIMAL_RE = re.compile(r"^-?\d+\.\d{6}$")


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


def _config(**overrides: object) -> MarketResearchCryptoOracleHeartbeatStallDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_ORACLE_HEARTBEAT_STALL_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("1800.000000"),
        "watch_heartbeat_gap_ratio": d("1.500000"),
        "blocked_heartbeat_gap_ratio": d("3.000000"),
        "max_heartbeat_gap_seconds": d("900.000000"),
        "max_publish_lag_seconds": d("300.000000"),
        "min_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoOracleHeartbeatStallDigestConfig(**values)


def _observation(
    condition_id: str = "condition_alpha",
    oracle_key: str = "eth_usd_chainlink",
    *,
    asset_symbol: str = "ETH",
    observed_at: datetime = GENERATED_AT,
    last_heartbeat_at: datetime = GENERATED_AT - timedelta(seconds=60),
    published_at: datetime = GENERATED_AT - timedelta(seconds=30),
    expected_heartbeat_interval_seconds: Decimal = d("60.000000"),
    heartbeat_gap_seconds: Decimal = d("60.000000"),
    source_count: Decimal = d("3.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "oracle-heartbeat-source-v0",
) -> MarketResearchCryptoOracleHeartbeatStallObservation:
    return MarketResearchCryptoOracleHeartbeatStallObservation(
        condition_id=condition_id,
        oracle_key=oracle_key,
        asset_symbol=asset_symbol,
        observed_at=observed_at,
        last_heartbeat_at=last_heartbeat_at,
        published_at=published_at,
        expected_heartbeat_interval_seconds=expected_heartbeat_interval_seconds,
        heartbeat_gap_seconds=heartbeat_gap_seconds,
        source_count=source_count,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *observations: MarketResearchCryptoOracleHeartbeatStallObservation,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoOracleHeartbeatStallDigestConfig | None = None,
) -> MarketResearchCryptoOracleHeartbeatStallDigestReport:
    return build_market_research_crypto_oracle_heartbeat_stall_digest(
        observations,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_heartbeat_stall_digest_models_stalls_and_reason_counts() -> None:
    report = _report(
        _observation(
            "condition_beta",
            "btc_usd_chainlink",
            asset_symbol="BTC",
            observed_at=GENERATED_AT - timedelta(seconds=2400),
            last_heartbeat_at=GENERATED_AT - timedelta(seconds=3000),
            published_at=GENERATED_AT - timedelta(seconds=1200),
            expected_heartbeat_interval_seconds=d("120.000000"),
            heartbeat_gap_seconds=d("600.000000"),
            source_count=d("1.000000"),
            confidence=d("0.550000"),
        ),
        _observation(
            "condition_alpha",
            "eth_usd_chainlink",
            observed_at=GENERATED_AT - timedelta(seconds=120),
            last_heartbeat_at=GENERATED_AT - timedelta(seconds=180),
            published_at=GENERATED_AT - timedelta(seconds=30),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-crypto-oracle-heartbeat-stall-digest-v0"
    )
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_oracle_heartbeat_stall_digest"
    )
    assert report.observation_count == d("2.000000")
    assert report.ready_observation_count == d("1.000000")
    assert report.watch_observation_count == d("0.000000")
    assert report.blocked_observation_count == d("1.000000")
    assert report.heartbeat_stall_observation_count == d("1.000000")
    assert report.max_gap_observation_count == d("0.000000")
    assert report.publish_lag_observation_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.source_diversity_gap_observation_count == d("1.000000")
    assert report.confidence_gap_observation_count == d("1.000000")
    assert report.average_heartbeat_gap_seconds == d("330.000000")
    assert report.average_heartbeat_gap_ratio == d("2.000000")
    assert report.average_publish_lag_seconds == d("615.000000")
    assert report.max_observed_heartbeat_gap_seconds == d("600.000000")
    assert report.max_observation_age_seconds == d("2400.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.oracle_key) for row in report.rows) == (
        ("condition_beta", "btc_usd_chainlink"),
        ("condition_alpha", "eth_usd_chainlink"),
    )
    blocked = report.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.observation_age_seconds == d("2400.000000")
    assert blocked.heartbeat_gap_ratio == d("4.000000")
    assert blocked.missed_heartbeat_count == d("4.000000")
    assert blocked.publish_lag_seconds == d("1200.000000")
    assert blocked.reason_codes == (
        "market_research_crypto_oracle_heartbeat_stall_digest_heartbeat_stall",
        "market_research_crypto_oracle_heartbeat_stall_digest_publish_lag",
        "market_research_crypto_oracle_heartbeat_stall_digest_stale_observation",
        "market_research_crypto_oracle_heartbeat_stall_digest_source_diversity_gap",
        "market_research_crypto_oracle_heartbeat_stall_digest_confidence_gap",
    )
    assert report.reason_code_counts == (
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_oracle_heartbeat_stall_digest_heartbeat_stall"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.500000"),
        ),
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(
            reason_code="market_research_crypto_oracle_heartbeat_stall_digest_publish_lag",
            count=d("1.000000"),
            observation_ratio=d("0.500000"),
        ),
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_oracle_heartbeat_stall_digest_stale_observation"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.500000"),
        ),
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_oracle_heartbeat_stall_digest_source_diversity_gap"
            ),
            count=d("1.000000"),
            observation_ratio=d("0.500000"),
        ),
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(
            reason_code="market_research_crypto_oracle_heartbeat_stall_digest_confidence_gap",
            count=d("1.000000"),
            observation_ratio=d("0.500000"),
        ),
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(
            reason_code="market_research_crypto_oracle_heartbeat_stall_digest_ready",
            count=d("1.000000"),
            observation_ratio=d("0.500000"),
        ),
    )
    assert tuple(item.reason_code for item in report.reason_code_counts) == report.reason_codes


def test_heartbeat_stall_digest_empty_input_is_blocked_report_only() -> None:
    report = _report()

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_oracle_heartbeat_stall_digest"
    )
    assert report.observation_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_crypto_oracle_heartbeat_stall_digest_no_inputs",
    )
    assert report.reason_code_counts == (
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(
            reason_code="market_research_crypto_oracle_heartbeat_stall_digest_no_inputs",
            count=d("1.000000"),
            observation_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_heartbeat_stall_digest_validates_exact_types_flags_and_timestamps() -> None:
    assert MarketResearchCryptoOracleHeartbeatStallDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoOracleHeartbeatStallObservation.__dataclass_params__.frozen
    assert MarketResearchCryptoOracleHeartbeatStallDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoOracleHeartbeatStallDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("oracle-heartbeat-v0"))
    with pytest.raises(ValueError, match="watch_heartbeat_gap_ratio"):
        _config(watch_heartbeat_gap_ratio=_DecimalSubclass("1.500000"))
    with pytest.raises(ValueError, match="watch_heartbeat_gap_ratio"):
        _config(watch_heartbeat_gap_ratio=d("1.5"))
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence"):
        _observation(confidence=d("0.82"))
    with pytest.raises(ValueError, match="condition_id"):
        _observation(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="redacted"):
        _observation(source_config_version="source-" + "pay" + "load" + "_" + "json")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _observation(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="UTC-aware"):
        _observation(
            observed_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
        )
    with pytest.raises(ValueError, match="UTC-aware"):
        _report(
            _observation(),
            generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
        )
    with pytest.raises(ValueError, match="future"):
        _report(
            _observation(
                observed_at=GENERATED_AT + timedelta(seconds=1),
                last_heartbeat_at=GENERATED_AT - timedelta(seconds=59),
            ),
        )
    with pytest.raises(ValueError, match="last_heartbeat_at"):
        _observation(last_heartbeat_at=GENERATED_AT + timedelta(seconds=1))
    with pytest.raises(ValueError, match="heartbeat_gap_seconds"):
        _observation(heartbeat_gap_seconds=d("61.000000"))
    with pytest.raises(ValueError, match="heartbeat_gap_seconds"):
        _observation(heartbeat_gap_seconds=d("60"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_observation(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_observation(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_observation(), readonly=False)
    hardened = _report(_observation())
    with pytest.raises(ValueError, match="paper_only"):
        replace(hardened.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(hardened.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(hardened.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(hardened.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(hardened.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(hardened.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(hardened, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(hardened, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(hardened, readonly=False)
    with pytest.raises(FrozenInstanceError):
        _observation().paper_only = False  # type: ignore[misc]


def test_heartbeat_stall_digest_public_numerics_and_payload_are_canonical() -> None:
    report = _report(_observation())

    for item in (
        _config(),
        _observation(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(item)
        for field in fields(item):
            value = getattr(item, field.name)
            if _is_public_numeric_field(field.name) or field.name == "confidence":
                assert type(value) is Decimal, field.name
                assert value.as_tuple().exponent == -6, field.name

    payload = market_research_crypto_oracle_heartbeat_stall_digest_payload(report)
    assert isinstance(payload, MappingProxyType)
    assert payload["payload_kind"] == (
        "market_research_crypto_oracle_heartbeat_stall_digest"
    )
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["rows"][0]["heartbeat_gap_seconds"] == "60.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    for token in _unsafe_tokens():
        assert token not in repr(payload).lower()
    _assert_payload_numeric_strings(payload)
    _assert_no_payload_numbers(payload)
    with pytest.raises(TypeError):
        payload["observation_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["heartbeat_gap_seconds"] = "1.000000"  # type: ignore[index]


def test_heartbeat_stall_digest_rejects_drift_and_keeps_module_pure() -> None:
    with pytest.raises(ValueError, match="unique"):
        _report(
            _observation(oracle_key="duplicate"),
            _observation(oracle_key="duplicate"),
        )

    valid = _report(_observation())
    kwargs = {
        field.name: getattr(valid, field.name)
        for field in fields(MarketResearchCryptoOracleHeartbeatStallDigestReport)
    }
    assert MarketResearchCryptoOracleHeartbeatStallDigestReport(**kwargs).digest_status == "ready"
    with pytest.raises(ValueError, match="observation_count"):
        MarketResearchCryptoOracleHeartbeatStallDigestReport(
            **{**kwargs, "observation_count": d("2.000000")},
        )
    two_row = _report(
        _observation("condition_b", "source_b"),
        _observation("condition_a", "source_a"),
    )
    drift_report = _report(
        _observation("condition_ready", "source_ready"),
        _observation(
            "condition_blocked",
            "source_blocked",
            last_heartbeat_at=GENERATED_AT - timedelta(seconds=600),
            published_at=GENERATED_AT - timedelta(seconds=1200),
            expected_heartbeat_interval_seconds=d("120.000000"),
            heartbeat_gap_seconds=d("600.000000"),
        ),
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoOracleHeartbeatStallDigestReport(
            **{
                **{
                    field.name: getattr(drift_report, field.name)
                    for field in fields(MarketResearchCryptoOracleHeartbeatStallDigestReport)
                },
                "reason_code_counts": tuple(reversed(drift_report.reason_code_counts)),
            },
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoOracleHeartbeatStallDigestReport(
            **{
                **{
                    field.name: getattr(drift_report, field.name)
                    for field in fields(MarketResearchCryptoOracleHeartbeatStallDigestReport)
                },
                "reason_code_counts": list(drift_report.reason_code_counts),
            },
        )
    with pytest.raises(ValueError, match="reason_codes"):
        MarketResearchCryptoOracleHeartbeatStallDigestReport(
            **{
                **{
                    field.name: getattr(drift_report, field.name)
                    for field in fields(MarketResearchCryptoOracleHeartbeatStallDigestReport)
                },
                "reason_codes": list(drift_report.reason_codes),
            },
        )
    with pytest.raises(ValueError, match="rows"):
        MarketResearchCryptoOracleHeartbeatStallDigestReport(
            **{
                **{
                    field.name: getattr(two_row, field.name)
                    for field in fields(MarketResearchCryptoOracleHeartbeatStallDigestReport)
                },
                "rows": tuple(reversed(two_row.rows)),
            },
        )
    with pytest.raises(ValueError, match="rows"):
        MarketResearchCryptoOracleHeartbeatStallDigestReport(
            **{
                **{
                    field.name: getattr(two_row, field.name)
                    for field in fields(MarketResearchCryptoOracleHeartbeatStallDigestReport)
                },
                "rows": list(two_row.rows),
            },
        )
    with pytest.raises(ValueError, match="source_config_versions"):
        MarketResearchCryptoOracleHeartbeatStallDigestReport(
            **{
                **{
                    field.name: getattr(two_row, field.name)
                    for field in fields(MarketResearchCryptoOracleHeartbeatStallDigestReport)
                },
                "source_config_versions": list(two_row.source_config_versions),
            },
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(two_row.rows[0], reason_codes=list(two_row.rows[0].reason_codes))
    with pytest.raises(ValueError, match="count"):
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(
            reason_code="market_research_crypto_oracle_heartbeat_stall_digest_ready",
            count=d("0.000000"),
            observation_ratio=d("0.000000"),
        )
    with pytest.raises(ValueError, match="whole"):
        MarketResearchCryptoOracleHeartbeatStallDigestReasonCodeCount(
            reason_code="market_research_crypto_oracle_heartbeat_stall_digest_ready",
            count=d("1.500000"),
            observation_ratio=d("0.500000"),
        )

    tampered_report_only = _report(_observation())
    object.__setattr__(tampered_report_only, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        market_research_crypto_oracle_heartbeat_stall_digest_payload(tampered_report_only)
    tampered_readonly = _report(_observation())
    object.__setattr__(tampered_readonly.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_crypto_oracle_heartbeat_stall_digest_payload(tampered_readonly)
    tampered_decimal = _report(_observation())
    object.__setattr__(tampered_decimal.rows[0], "heartbeat_gap_seconds", Decimal("60.0"))
    with pytest.raises(ValueError, match="six decimal"):
        market_research_crypto_oracle_heartbeat_stall_digest_payload(tampered_decimal)
    tampered_time = _report(_observation())
    object.__setattr__(
        tampered_time.rows[0],
        "observed_at",
        datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="UTC-aware"):
        market_research_crypto_oracle_heartbeat_stall_digest_payload(tampered_time)

    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_oracle_heartbeat_stall_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)
    assert "as" + "dict" not in lowered
    for token in _unsafe_tokens():
        assert token not in lowered
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "open",
                "eval",
                "exec",
                "".join(("__", "import", "__")),
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


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_seconds")
        or field_name.endswith("_ratio")
    )


def _assert_payload_numeric_strings(value: object) -> None:
    if isinstance(value, MappingProxyType):
        for key, child in value.items():
            if _is_public_numeric_field(str(key)) or key == "confidence":
                assert type(child) is str, key
                assert SIX_DECIMAL_RE.fullmatch(child), (key, child)
            _assert_payload_numeric_strings(child)
        return
    if isinstance(value, tuple):
        for child in value:
            _assert_payload_numeric_strings(child)


def _assert_no_payload_numbers(value: Any) -> None:
    if isinstance(value, MappingProxyType):
        for item in value.values():
            _assert_no_payload_numbers(item)
        return
    if isinstance(value, tuple):
        for item in value:
            _assert_no_payload_numbers(item)
        return
    if isinstance(value, bool):
        return
    assert not isinstance(value, (Decimal, float, int))


def _unsafe_tokens() -> tuple[str, ...]:
    return (
        "".join(("market", "_", "slug")),
        "".join(("ques", "tion")),
        "".join(("pay", "load", "_", "json")),
        "".join(("wa", "llet")),
        "".join(("pri", "vate")),
    )
