from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_crypto_etf_flow_dislocation_digest"
)
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _module() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> object:
    module = _module()
    values: dict[str, object] = {
        "config_version": (
            module
            .DEFAULT_MARKET_RESEARCH_CRYPTO_ETF_FLOW_DISLOCATION_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("1800.000000"),
        "min_source_quorum_count": d("2.000000"),
        "watch_abs_net_flow_usd": d("50000000.000000"),
        "blocked_abs_net_flow_usd": d("300000000.000000"),
        "watch_flow_spot_divergence_abs": d("0.025000"),
        "blocked_flow_spot_divergence_abs": d("0.080000"),
        "watch_premium_discount_abs": d("0.010000"),
        "blocked_premium_discount_abs": d("0.035000"),
        "watch_futures_basis_abs": d("0.005000"),
        "blocked_futures_basis_abs": d("0.020000"),
        "watch_creation_redemption_imbalance": d("0.300000"),
        "blocked_creation_redemption_imbalance": d("0.650000"),
        "watch_risk_score": d("0.350000"),
        "blocked_risk_score": d("0.700000"),
    }
    values.update(overrides)
    return module.MarketResearchCryptoEtfFlowDislocationDigestConfig(**values)


def _snapshot(
    etf_ticker: str = "SOLZ",
    asset_symbol: str = "SOL",
    market_slug: str = "sol-etf-flow-balanced",
    *,
    source_timestamp: datetime = GENERATED_AT,
    net_flow_usd: Decimal = d("15000000.000000"),
    spot_return: Decimal = d("0.005000"),
    premium_discount: Decimal = d("0.002000"),
    futures_basis: Decimal = d("0.001000"),
    creation_redemption_imbalance: Decimal = d("0.050000"),
    source_quorum_count: Decimal = d("4.000000"),
    upstream_reason_codes: tuple[str, ...] = (),
    source_config_version: str = "crypto-etf-flow-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> object:
    module = _module()
    return module.MarketResearchCryptoEtfFlowDislocationSnapshot(
        etf_ticker=etf_ticker,
        asset_symbol=asset_symbol,
        market_slug=market_slug,
        source_timestamp=source_timestamp,
        net_flow_usd=net_flow_usd,
        spot_return=spot_return,
        premium_discount=premium_discount,
        futures_basis=futures_basis,
        creation_redemption_imbalance=creation_redemption_imbalance,
        source_quorum_count=source_quorum_count,
        upstream_reason_codes=upstream_reason_codes,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    *snapshots: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> object:
    module = _module()
    return module.build_market_research_crypto_etf_flow_dislocation_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in _walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in _walk_values(nested))
    return (value,)


def test_crypto_etf_flow_dislocation_digest_empty_input_is_watch_report_only() -> None:
    report = _report()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_market_research_crypto_etf_flow_dislocation_digest"
    )
    assert report.snapshot_count == d("0.000000")
    assert report.pass_snapshot_count == d("0.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("0.000000")
    assert report.aggregate_net_flow_usd == d("0.000000")
    assert report.max_net_flow_abs_usd == d("0.000000")
    assert report.average_risk_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_crypto_etf_flow_dislocation_digest_no_inputs",
    )
    assert report.reason_code_counts == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_crypto_etf_flow_dislocation_digest_scores_pressure_and_source_quality() -> None:
    report = _report(
        _snapshot(
            "IBIT",
            "BTC",
            "btc-etf-flow-vs-spot-stress",
            source_timestamp=datetime(
                2026,
                7,
                4,
                7,
                20,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            net_flow_usd=d("325000000.000000"),
            spot_return=d("-0.090000"),
            premium_discount=d("0.042000"),
            futures_basis=d("-0.024000"),
            creation_redemption_imbalance=d("0.720000"),
            source_quorum_count=d("1.000000"),
            upstream_reason_codes=("desk_flow_gap", "primary_market_lag"),
        ),
        _snapshot(
            "ETHA",
            "ETH",
            "eth-etf-flow-watch",
            source_timestamp=GENERATED_AT - timedelta(seconds=600),
            net_flow_usd=d("-125000000.000000"),
            spot_return=d("0.030000"),
            premium_discount=d("-0.012000"),
            futures_basis=d("0.000000"),
            creation_redemption_imbalance=d("0.310000"),
        ),
        _snapshot(source_timestamp=GENERATED_AT - timedelta(seconds=60)),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_etf_flow_dislocation_digest"
    )
    assert report.snapshot_count == d("3.000000")
    assert report.pass_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("1.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.flow_spot_divergence_snapshot_count == d("2.000000")
    assert report.premium_discount_dislocation_snapshot_count == d("2.000000")
    assert report.futures_basis_dislocation_snapshot_count == d("1.000000")
    assert report.creation_redemption_imbalance_snapshot_count == d("2.000000")
    assert report.source_freshness_gap_snapshot_count == d("1.000000")
    assert report.source_quorum_gap_snapshot_count == d("1.000000")
    assert report.upstream_reason_signal_snapshot_count == d("1.000000")
    assert report.aggregate_net_flow_usd == d("215000000.000000")
    assert report.max_net_flow_abs_usd == d("325000000.000000")
    assert report.average_spot_return == d("-0.018333")
    assert report.average_premium_discount == d("0.010667")
    assert report.average_futures_basis == d("-0.007667")
    assert report.average_creation_redemption_imbalance == d("0.360000")
    assert report.average_risk_score == d("0.443248")
    assert report.max_risk_score == d("1.000000")
    assert report.max_snapshot_age_seconds == d("2400.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.etf_ticker, row.asset_symbol, row.market_slug) for row in report.rows) == (
        ("IBIT", "BTC", "btc-etf-flow-vs-spot-stress"),
        ("ETHA", "ETH", "eth-etf-flow-watch"),
        ("SOLZ", "SOL", "sol-etf-flow-balanced"),
    )
    blocked, watch, passed = report.rows
    assert blocked.digest_status == "blocked"
    assert blocked.source_timestamp == datetime(2026, 7, 4, 11, 20, tzinfo=UTC)
    assert blocked.snapshot_age_seconds == d("2400.000000")
    assert blocked.net_flow_abs_usd == d("325000000.000000")
    assert blocked.spot_return_abs == d("0.090000")
    assert blocked.flow_spot_divergence_abs == d("0.090000")
    assert blocked.premium_discount_abs == d("0.042000")
    assert blocked.futures_basis_abs == d("0.024000")
    assert blocked.risk_score == d("1.000000")
    assert blocked.upstream_reason_codes == ("desk_flow_gap", "primary_market_lag")
    assert blocked.reason_codes == (
        "market_research_crypto_etf_flow_dislocation_digest_flow_spot_divergence",
        "market_research_crypto_etf_flow_dislocation_digest_premium_discount_dislocation",
        "market_research_crypto_etf_flow_dislocation_digest_futures_basis_dislocation",
        "market_research_crypto_etf_flow_dislocation_digest_creation_redemption_imbalance",
        "market_research_crypto_etf_flow_dislocation_digest_source_freshness_gap",
        "market_research_crypto_etf_flow_dislocation_digest_source_quorum_gap",
        "market_research_crypto_etf_flow_dislocation_digest_upstream_reason_signal",
    )

    assert watch.digest_status == "watch"
    assert watch.risk_score == d("0.294276")
    assert watch.flow_spot_divergence_abs == d("0.030000")
    assert watch.reason_codes == (
        "market_research_crypto_etf_flow_dislocation_digest_flow_spot_divergence",
        "market_research_crypto_etf_flow_dislocation_digest_premium_discount_dislocation",
        "market_research_crypto_etf_flow_dislocation_digest_creation_redemption_imbalance",
    )

    assert passed.digest_status == "pass"
    assert passed.risk_score == d("0.035467")
    assert passed.flow_spot_divergence_abs == d("0.000000")
    assert passed.reason_codes == (
        "market_research_crypto_etf_flow_dislocation_digest_pass",
    )

    assert report.reason_codes == blocked.reason_codes


def test_crypto_etf_flow_dislocation_digest_timezones_reason_counts_and_sources() -> None:
    module = _module()
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    source_timestamp = datetime(2026, 7, 4, 13, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "ETHA",
            "ETH",
            "eth-etf-flow-watch",
            source_timestamp=source_timestamp,
            net_flow_usd=d("-125000000.000000"),
            spot_return=d("0.030000"),
            premium_discount=d("-0.012000"),
            creation_redemption_imbalance=d("0.310000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].source_timestamp == GENERATED_AT
    assert report.max_snapshot_age_seconds == d("0.000000")
    assert report.source_config_versions == (
        (
            ("ETHA", "ETH", "eth-etf-flow-watch"),
            "crypto-etf-flow-source-v0",
        ),
    )
    assert report.reason_code_counts == (
        module.MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_etf_flow_dislocation_digest_"
                "flow_spot_divergence"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        module.MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_etf_flow_dislocation_digest_"
                "premium_discount_dislocation"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        module.MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_etf_flow_dislocation_digest_"
                "creation_redemption_imbalance"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )


def test_crypto_etf_flow_dislocation_digest_sorting_is_deterministic() -> None:
    first = _report(
        _snapshot("ETHA", "ETH", "market_b"),
        _snapshot("IBIT", "BTC", "market_a"),
    )
    second = _report(
        _snapshot("IBIT", "BTC", "market_a"),
        _snapshot("ETHA", "ETH", "market_b"),
    )

    assert first == second
    assert tuple(row.market_slug for row in first.rows) == ("market_a", "market_b")


def test_crypto_etf_flow_dislocation_validates_exact_types_flags_and_freezing() -> None:
    module = _module()

    for type_ in (
        module.MarketResearchCryptoEtfFlowDislocationDigestConfig,
        module.MarketResearchCryptoEtfFlowDislocationSnapshot,
        module.MarketResearchCryptoEtfFlowDislocationDigestRow,
        module.MarketResearchCryptoEtfFlowDislocationDigestReasonCodeCount,
        module.MarketResearchCryptoEtfFlowDislocationDigestReport,
    ):
        assert type_.__dataclass_params__.frozen is True
        for field in fields(type_):
            public_type = str(field.type).lower()
            assert "float" not in public_type
            assert "int" not in public_type

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("flow-dislocation-v0"))
    with pytest.raises(ValueError, match="blocked_abs_net_flow_usd"):
        _config(blocked_abs_net_flow_usd=_DecimalSubclass("300000000.000000"))
    with pytest.raises(ValueError, match="min_source_quorum_count"):
        _config(min_source_quorum_count=2)
    with pytest.raises(ValueError, match="watch_risk_score"):
        _config(watch_risk_score=d("0.900000"), blocked_risk_score=d("0.700000"))
    with pytest.raises(ValueError, match="net_flow_usd"):
        _snapshot(net_flow_usd=325000000)
    with pytest.raises(ValueError, match="premium_discount"):
        _snapshot(premium_discount=d("1.100000"))
    with pytest.raises(ValueError, match="etf_ticker"):
        _snapshot(etf_ticker=_StringSubclass("IBIT"))
    with pytest.raises(ValueError, match="source_timestamp"):
        _snapshot(source_timestamp=datetime(2026, 7, 4, 12, 0))
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
    with pytest.raises(ValueError, match="unique"):
        _report(
            _snapshot("IBIT", "BTC", "duplicate-market"),
            _snapshot("IBIT", "BTC", "duplicate-market"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_snapshot(), paper_only=False)

    report = _report(_snapshot())
    with pytest.raises(FrozenInstanceError):
        report.rows = ()  # type: ignore[misc]


def test_crypto_etf_flow_dislocation_public_numeric_fields_are_decimal_only() -> None:
    module = _module()
    config = _config()
    report = _report(_snapshot())

    for item in (config, *report.rows, *report.reason_code_counts, report):
        for field in fields(item):
            value = getattr(item, field.name)
            if (
                field.name.endswith("_count")
                or field.name.endswith("_seconds")
                or field.name.endswith("_score")
                or field.name.endswith("_ratio")
                or field.name.endswith("_usd")
                or field.name.endswith("_return")
                or field.name.endswith("_discount")
                or field.name.endswith("_basis")
                or field.name.endswith("_imbalance")
                or field.name.endswith("_abs")
            ):
                assert type(value) is Decimal

    kwargs = {field.name: getattr(report, field.name) for field in fields(report)}
    with pytest.raises(ValueError, match="snapshot_count"):
        module.MarketResearchCryptoEtfFlowDislocationDigestReport(
            **{**kwargs, "snapshot_count": 1},
        )


def test_crypto_etf_flow_dislocation_payload_is_json_ready_and_canonical() -> None:
    module = _module()
    report = _report(
        _snapshot(
            "IBIT",
            "BTC",
            "btc-etf-flow-vs-spot-stress",
            net_flow_usd=d("325000000.000000"),
            spot_return=d("-0.090000"),
            premium_discount=d("0.042000"),
            futures_basis=d("-0.024000"),
            creation_redemption_imbalance=d("0.720000"),
        ),
    )
    payload = module.market_research_crypto_etf_flow_dislocation_digest_payload(report)
    json.dumps(payload, sort_keys=True)
    payload_text = repr(payload).lower()

    for forbidden in (
        "wallet",
        "auth",
        "private",
        "secret",
        "order",
        "cancel",
        "replace",
        "exchange",
        "payload_json",
    ):
        assert forbidden not in payload_text
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["snapshot_count"] == "1.000000"
    assert payload["aggregate_net_flow_usd"] == "325000000.000000"
    assert payload["average_risk_score"] == "0.900000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["source_timestamp"] == "2026-07-04T12:00:00+00:00"
    assert payload["rows"][0]["market_slug"] == "btc-etf-flow-vs-spot-stress"
    assert payload["rows"][0]["net_flow_usd"] == "325000000.000000"
    assert payload["rows"][0]["spot_return"] == "-0.090000"
    assert payload["rows"][0]["risk_score"] == "0.900000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))

    with pytest.raises(ValueError, match="redacted"):
        _snapshot(market_slug="wallet-flow-gap")


def test_crypto_etf_flow_dislocation_module_scope_excludes_io_and_mutation() -> None:
    module = _module()
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "live trading",
        "account authentication",
        "private-key",
        "wallet",
        "order submission",
        "order cancellation",
        "order replacement",
        "exchange mutation",
        "network io",
        "file io",
        "database",
        "supabase",
        "subprocess",
        "requests",
        "httpx",
        "socket",
        "urlopen",
        "psycopg",
    )
    assert not any(token in lowered for token in forbidden_literals)

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
            assert callee_name not in {
                "open",
                "read",
                "write",
                "submit",
                "cancel",
            }
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_fragments = (
        "db",
        "env",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "pathlib",
        "sqlite",
        "subprocess",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
