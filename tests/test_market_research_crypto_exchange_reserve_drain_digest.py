from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.market_research_crypto_exchange_reserve_drain_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DRAIN_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoExchangeReserveDrainDigestConfig,
    MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount,
    MarketResearchCryptoExchangeReserveDrainDigestReport,
    MarketResearchCryptoExchangeReserveDrainDigestRow,
    MarketResearchCryptoExchangeReserveDrainSnapshot,
    build_market_research_crypto_exchange_reserve_drain_digest,
    market_research_crypto_exchange_reserve_drain_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


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
) -> MarketResearchCryptoExchangeReserveDrainDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_EXCHANGE_RESERVE_DRAIN_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("1800.000000"),
        "max_reserve_drop_ratio": d("0.120000"),
        "max_net_outflow_ratio": d("0.080000"),
        "min_source_count": d("3.000000"),
        "min_confidence": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCryptoExchangeReserveDrainDigestConfig(**values)


def _snapshot(
    condition_id: str = "condition_alpha",
    reserve_key: str = "btc_reserve_watch",
    *,
    asset_symbol: str = "BTC",
    source_count: Decimal = d("3.000000"),
    reserve_balance: Decimal = d("1000.000000"),
    previous_reserve_balance: Decimal = d("1000.000000"),
    net_outflow: Decimal = d("0.000000"),
    confidence: Decimal = d("0.840000"),
    source_timestamp: datetime = GENERATED_AT,
    source_config_version: str = "reserve-drain-source-v0",
) -> MarketResearchCryptoExchangeReserveDrainSnapshot:
    return MarketResearchCryptoExchangeReserveDrainSnapshot(
        condition_id=condition_id,
        reserve_key=reserve_key,
        asset_symbol=asset_symbol,
        source_timestamp=source_timestamp,
        source_count=source_count,
        reserve_balance=reserve_balance,
        previous_reserve_balance=previous_reserve_balance,
        net_outflow=net_outflow,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: MarketResearchCryptoExchangeReserveDrainSnapshot,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoExchangeReserveDrainDigestConfig | None = None,
) -> MarketResearchCryptoExchangeReserveDrainDigestReport:
    return build_market_research_crypto_exchange_reserve_drain_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_exchange_reserve_drain_digest_models_drain_pressure_and_gaps() -> None:
    report = _report(
        _snapshot(
            "condition_beta",
            "eth_reserve_pressure",
            asset_symbol="ETH",
            source_timestamp=GENERATED_AT - timedelta(seconds=2_400),
            source_count=d("1.000000"),
            reserve_balance=d("760.000000"),
            previous_reserve_balance=d("1000.000000"),
            net_outflow=d("180.000000"),
            confidence=d("0.520000"),
        ),
        _snapshot(
            "condition_alpha",
            "btc_reserve_clear",
            source_timestamp=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_exchange_reserve_drain_digest"
    )
    assert report.snapshot_count == d("2.000000")
    assert report.ready_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.reserve_drop_snapshot_count == d("1.000000")
    assert report.net_outflow_snapshot_count == d("1.000000")
    assert report.source_gap_snapshot_count == d("1.000000")
    assert report.stale_snapshot_count == d("1.000000")
    assert report.confidence_gap_snapshot_count == d("1.000000")
    assert report.average_reserve_drop_ratio == d("0.120000")
    assert report.average_net_outflow_ratio == d("0.090000")
    assert report.max_snapshot_age_seconds == d("2400.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.condition_id, row.reserve_key) for row in report.rows) == (
        ("condition_beta", "eth_reserve_pressure"),
        ("condition_alpha", "btc_reserve_clear"),
    )
    beta = report.rows[0]
    assert beta.digest_status == "blocked"
    assert beta.snapshot_age_seconds == d("2400.000000")
    assert beta.reserve_drop_ratio == d("0.240000")
    assert beta.net_outflow_ratio == d("0.180000")
    assert beta.reason_codes == (
        "market_research_crypto_exchange_reserve_drain_digest_reserve_drop",
        "market_research_crypto_exchange_reserve_drain_digest_net_outflow",
        "market_research_crypto_exchange_reserve_drain_digest_source_gap",
        "market_research_crypto_exchange_reserve_drain_digest_stale_snapshot",
        "market_research_crypto_exchange_reserve_drain_digest_confidence_gap",
    )
    assert report.reason_codes == beta.reason_codes


def test_exchange_reserve_drain_digest_normalizes_utc_and_counts_reasons() -> None:
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    source_timestamp = datetime(2026, 7, 4, 13, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "condition_gamma",
            "sol_reserve_sources",
            asset_symbol="SOL",
            source_timestamp=source_timestamp,
            source_count=d("2.000000"),
            reserve_balance=d("990.000000"),
            previous_reserve_balance=d("1000.000000"),
            net_outflow=d("20.000000"),
            confidence=d("0.760000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].source_timestamp == GENERATED_AT
    assert report.max_snapshot_age_seconds == d("0.000000")
    assert report.digest_status == "watch"
    assert report.reason_code_counts == (
        MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_exchange_reserve_drain_digest_source_gap"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("sol_reserve_sources", "reserve-drain-source-v0"),
    )


def test_exchange_reserve_drain_digest_empty_input_is_blocked_and_sorting_is_stable() -> None:
    empty = _report()
    assert empty.digest_status == "blocked"
    assert empty.snapshot_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_exchange_reserve_drain_digest_no_inputs",
    )
    assert empty.reason_code_counts == (
        MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount(
            reason_code="market_research_crypto_exchange_reserve_drain_digest_no_inputs",
            count=d("1.000000"),
            snapshot_ratio=d("0.000000"),
        ),
    )

    first = _report(
        _snapshot("condition_b", "source_b"),
        _snapshot("condition_a", "source_a"),
    )
    second = _report(
        _snapshot("condition_a", "source_a"),
        _snapshot("condition_b", "source_b"),
    )

    assert first == second
    assert tuple(row.reserve_key for row in first.rows) == ("source_a", "source_b")


def test_exchange_reserve_drain_digest_rejects_exact_type_decimal_and_time_violations() -> None:
    assert MarketResearchCryptoExchangeReserveDrainDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoExchangeReserveDrainSnapshot.__dataclass_params__.frozen
    assert MarketResearchCryptoExchangeReserveDrainDigestRow.__dataclass_params__.frozen
    assert MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount.__dataclass_params__.frozen
    assert MarketResearchCryptoExchangeReserveDrainDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("reserve-drain-v0"))
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version="unsupported-reserve-drain-v0")
    with pytest.raises(ValueError, match="max_reserve_drop_ratio"):
        _config(max_reserve_drop_ratio=_DecimalSubclass("0.120000"))
    with pytest.raises(ValueError, match="min_source_count"):
        _config(min_source_count=d("3.0"))
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="condition_id"):
        _snapshot(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="source_timestamp"):
        _report(
            _snapshot(
                source_timestamp=datetime(
                    2026,
                    7,
                    4,
                    12,
                    0,
                    tzinfo=_NoneOffsetTimezone(),
                ),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="future"):
        _report(_snapshot(source_timestamp=GENERATED_AT + timedelta(seconds=1)))

    report = _report(_snapshot())
    for item in (
        _config(),
        _snapshot(),
        report.rows[0],
        report.reason_code_counts[0],
        report,
    ):
        for flag in ("paper_only", "report_only", "readonly"):
            with pytest.raises(ValueError, match=flag):
                replace(item, **{flag: False})
    with pytest.raises(FrozenInstanceError):
        _snapshot().paper_only = False  # type: ignore[misc]


@pytest.mark.parametrize(
    "base_type",
    (
        MarketResearchCryptoExchangeReserveDrainDigestConfig,
        MarketResearchCryptoExchangeReserveDrainSnapshot,
        MarketResearchCryptoExchangeReserveDrainDigestRow,
        MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount,
        MarketResearchCryptoExchangeReserveDrainDigestReport,
    ),
)
def test_exchange_reserve_drain_digest_rejects_public_dataclass_subclassing(
    base_type: type,
) -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):
        type(f"Unsupported{base_type.__name__}", (base_type,), {})


def test_exchange_reserve_drain_digest_rejects_lists_and_inconsistent_records() -> None:
    with pytest.raises(ValueError, match="snapshots must be a tuple"):
        build_market_research_crypto_exchange_reserve_drain_digest(
            [_snapshot()],  # type: ignore[arg-type]
            config=_config(),
            generated_at=GENERATED_AT,
        )
    report = _report(
        _snapshot(
            "condition_pressure",
            "source_pressure",
            source_timestamp=GENERATED_AT - timedelta(seconds=2_400),
            source_count=d("1.000000"),
            reserve_balance=d("760.000000"),
            previous_reserve_balance=d("1000.000000"),
            net_outflow=d("180.000000"),
            confidence=d("0.520000"),
        ),
        _snapshot("condition_ready", "source_ready"),
    )
    with pytest.raises(ValueError, match="rows must be a tuple"):
        replace(report, rows=list(report.rows))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(report, reason_codes=list(report.reason_codes))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=tuple(reversed(report.reason_codes)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report.rows[0], reason_codes=tuple(reversed(report.rows[0].reason_codes)))
    with pytest.raises(ValueError, match="reason_code_counts must be a tuple"):
        replace(
            report,
            reason_code_counts=list(report.reason_code_counts),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=tuple(reversed(report.reason_code_counts)))
    with pytest.raises(ValueError, match="source_config_versions must be a tuple"):
        replace(
            report,
            source_config_versions=list(report.source_config_versions),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="source_config_versions"):
        replace(
            report,
            source_config_versions=tuple(reversed(report.source_config_versions)),
        )
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(_report(_snapshot()).rows[0], reason_codes=["bad"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unique"):
        _report(_snapshot(reserve_key="duplicate"), _snapshot(reserve_key="duplicate"))

    valid = _report(_snapshot("condition_a", "source_a"), _snapshot("condition_b", "source_b"))
    kwargs = {
        field.name: getattr(valid, field.name)
        for field in fields(MarketResearchCryptoExchangeReserveDrainDigestReport)
    }
    assert MarketResearchCryptoExchangeReserveDrainDigestReport(**kwargs).digest_status == (
        "ready"
    )

    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoExchangeReserveDrainDigestReport(
            **{**kwargs, "snapshot_count": d("3.000000")},
        )
    with pytest.raises(ValueError, match="rows"):
        MarketResearchCryptoExchangeReserveDrainDigestReport(
            **{**kwargs, "rows": tuple(reversed(valid.rows))},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoExchangeReserveDrainDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_exchange_reserve_drain_digest_ready"
                        ),
                        count=d("3.000000"),
                        snapshot_ratio=d("1.000000"),
                    ),
                ),
            },
        )
    with pytest.raises(ValueError, match="count"):
        MarketResearchCryptoExchangeReserveDrainDigestReasonCodeCount(
            reason_code="market_research_crypto_exchange_reserve_drain_digest_ready",
            count=d("0.000000"),
            snapshot_ratio=d("0.000000"),
        )


def test_exchange_reserve_drain_digest_payload_is_immutable_and_revalidates_nested_records() -> None:
    report = _report(_snapshot("condition_redacted", "btc_reserve_redacted"))
    payload = market_research_crypto_exchange_reserve_drain_digest_payload(report)
    payload_text = repr(payload).lower()

    for forbidden in (
        "market_slug",
        "question",
        "wallet",
        "payload_json",
    ):
        assert forbidden not in payload_text
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["snapshot_count"] == "1.000000"
    assert payload["average_reserve_drop_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["source_timestamp"] == "2026-07-04T12:00:00+00:00"
    assert payload["rows"][0]["reserve_balance"] == "1000.000000"
    assert payload["reason_code_counts"][0]["paper_only"] is True
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["reserve_balance"] = "0.000000"  # type: ignore[index]

    tampered = _report(_snapshot())
    object.__setattr__(tampered.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_crypto_exchange_reserve_drain_digest_payload(tampered)

    tampered = _report(_snapshot())
    object.__setattr__(tampered.rows[0], "reserve_drop_ratio", d("0.999999"))
    with pytest.raises(ValueError, match="reserve_drop_ratio"):
        market_research_crypto_exchange_reserve_drain_digest_payload(tampered)

    tampered = _report(_snapshot())
    object.__setattr__(tampered.reason_code_counts[0], "count", d("0.000000"))
    with pytest.raises(ValueError, match="count"):
        market_research_crypto_exchange_reserve_drain_digest_payload(tampered)

    tampered = _report(_snapshot())
    object.__setattr__(
        tampered,
        "generated_at",
        datetime(2026, 7, 4, 13, 0, tzinfo=timezone(timedelta(hours=1))),
    )
    with pytest.raises(ValueError, match="UTC"):
        market_research_crypto_exchange_reserve_drain_digest_payload(tampered)

    tampered = _report(_snapshot())
    object.__setattr__(tampered.rows[0], "reserve_balance", d("1000.0"))
    with pytest.raises(ValueError, match="six-decimal"):
        market_research_crypto_exchange_reserve_drain_digest_payload(tampered)

    def assert_six_decimal_numeric_strings(value: object) -> None:
        if isinstance(value, str):
            if value.replace("-", "", 1).replace(".", "", 1).isdigit() and "." in value:
                assert len(value.rsplit(".", maxsplit=1)[1]) == 6
            return
        if isinstance(value, Mapping):
            for item in value.values():
                assert_six_decimal_numeric_strings(item)
            return
        if isinstance(value, tuple):
            for item in value:
                assert_six_decimal_numeric_strings(item)

    assert_six_decimal_numeric_strings(payload)


def test_exchange_reserve_drain_digest_module_scope_excludes_io_and_mutation() -> None:
    source_text = (
        MarketResearchCryptoExchangeReserveDrainDigestReport.__module__
    )
    module = __import__(source_text, fromlist=["unused"])
    loaded_source = module.__loader__.get_source(module.__name__)
    assert loaded_source is not None
    lowered = loaded_source.lower()
    tree = ast.parse(loaded_source)

    assert "asdict" not in lowered
    for forbidden in (
        "market_slug",
        "question",
        "payload_json",
        "private_key",
        "wallet",
        "submit_order",
        "cancel_order",
    ):
        assert forbidden not in lowered

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            callee_name = ""
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in {"open", "read", "write"}
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_fragments = (
        "psycopg",
        "requests",
        "socket",
        "urllib",
        "pathlib",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
