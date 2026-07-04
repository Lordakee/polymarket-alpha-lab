from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import ModuleType

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "market_research_crypto_options_iv_surface_dislocation_digest"
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
    values = {
        "config_version": (
            module
            .DEFAULT_MARKET_RESEARCH_CRYPTO_OPTIONS_IV_SURFACE_DISLOCATION_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("1800.000000"),
        "min_source_quorum_count": d("2.000000"),
        "watch_atm_iv_z_score_abs": d("2.000000"),
        "blocked_atm_iv_z_score_abs": d("4.000000"),
        "watch_skew_change_abs": d("0.050000"),
        "blocked_skew_change_abs": d("0.150000"),
        "watch_term_structure_kink_abs": d("0.040000"),
        "blocked_term_structure_kink_abs": d("0.120000"),
        "watch_options_volume_oi_pressure": d("0.300000"),
        "blocked_options_volume_oi_pressure": d("0.650000"),
        "watch_spot_vol_divergence_abs": d("0.080000"),
        "blocked_spot_vol_divergence_abs": d("0.220000"),
        "watch_risk_score": d("0.350000"),
        "blocked_risk_score": d("0.700000"),
    }
    values.update(overrides)
    return module.MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig(**values)


def _snapshot(
    venue: str = "cme",
    asset_symbol: str = "SOL",
    expiry_bucket: str = "90d",
    market_slug: str = "sol-options-quiet",
    *,
    source_timestamp: datetime = GENERATED_AT,
    atm_iv_z_score: Decimal = d("0.500000"),
    skew_change: Decimal = d("0.010000"),
    term_structure_kink: Decimal = d("0.010000"),
    options_volume_oi_pressure: Decimal = d("0.050000"),
    spot_vol_divergence: Decimal = d("0.020000"),
    source_quorum_count: Decimal = d("4.000000"),
    upstream_reason_codes: tuple[str, ...] = (),
    source_config_version: str = "crypto-options-iv-surface-source-v0",
) -> object:
    module = _module()
    return module.MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot(
        venue=venue,
        asset_symbol=asset_symbol,
        expiry_bucket=expiry_bucket,
        market_slug=market_slug,
        source_timestamp=source_timestamp,
        atm_iv_z_score=atm_iv_z_score,
        skew_change=skew_change,
        term_structure_kink=term_structure_kink,
        options_volume_oi_pressure=options_volume_oi_pressure,
        spot_vol_divergence=spot_vol_divergence,
        source_quorum_count=source_quorum_count,
        upstream_reason_codes=upstream_reason_codes,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: object,
    generated_at: datetime = GENERATED_AT,
    config: object | None = None,
) -> object:
    module = _module()
    return module.build_market_research_crypto_options_iv_surface_dislocation_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def _assert_no_float(value: object) -> None:
    if isinstance(value, float):
        pytest.fail(f"float found in payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_float(item)


def test_iv_surface_dislocation_digest_empty_input_is_watch_report_only() -> None:
    report = _report()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "watch"
    assert report.recommended_next_step == (
        "review_report_only_market_research_crypto_options_iv_surface_dislocation_digest"
    )
    assert report.snapshot_count == d("0.000000")
    assert report.pass_snapshot_count == d("0.000000")
    assert report.watch_snapshot_count == d("0.000000")
    assert report.blocked_snapshot_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "market_research_crypto_options_iv_surface_dislocation_digest_no_inputs",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_iv_surface_dislocation_digest_scores_pressure_and_source_quality() -> None:
    report = _report(
        _snapshot(
            "deribit",
            "BTC",
            "7d",
            "btc-etf-july-iv-dislocation",
            source_timestamp=GENERATED_AT - timedelta(seconds=2400),
            atm_iv_z_score=d("4.400000"),
            skew_change=d("-0.180000"),
            term_structure_kink=d("0.150000"),
            options_volume_oi_pressure=d("0.720000"),
            spot_vol_divergence=d("0.250000"),
            source_quorum_count=d("1.000000"),
            upstream_reason_codes=("vol_index_jump", "iv_surface_feed_gap"),
        ),
        _snapshot(
            "okx",
            "ETH",
            "30d",
            "eth-election-week-iv-watch",
            source_timestamp=GENERATED_AT - timedelta(seconds=600),
            atm_iv_z_score=d("2.000000"),
            skew_change=d("0.050000"),
            term_structure_kink=d("0.000000"),
            options_volume_oi_pressure=d("0.300000"),
            spot_vol_divergence=d("0.000000"),
        ),
        _snapshot(source_timestamp=GENERATED_AT - timedelta(seconds=60)),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_options_iv_surface_dislocation_digest"
    )
    assert report.snapshot_count == d("3.000000")
    assert report.pass_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("1.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.atm_iv_z_score_pressure_snapshot_count == d("2.000000")
    assert report.skew_change_pressure_snapshot_count == d("2.000000")
    assert report.term_structure_kink_snapshot_count == d("1.000000")
    assert report.options_volume_oi_pressure_snapshot_count == d("2.000000")
    assert report.spot_vol_divergence_snapshot_count == d("1.000000")
    assert report.source_freshness_gap_snapshot_count == d("1.000000")
    assert report.source_quorum_gap_snapshot_count == d("1.000000")
    assert report.upstream_reason_signal_snapshot_count == d("1.000000")
    assert report.average_atm_iv_z_score == d("2.300000")
    assert report.average_skew_change == d("-0.040000")
    assert report.average_term_structure_kink == d("0.053333")
    assert report.average_options_volume_oi_pressure == d("0.356667")
    assert report.average_spot_vol_divergence == d("0.090000")
    assert report.average_risk_score == d("0.447377")
    assert report.max_risk_score == d("1.000000")
    assert report.max_snapshot_age_seconds == d("2400.000000")
    assert report.watch_risk_score == d("0.350000")
    assert report.blocked_risk_score == d("0.700000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(
        (row.venue, row.asset_symbol, row.expiry_bucket, row.market_slug)
        for row in report.rows
    ) == (
        ("deribit", "BTC", "7d", "btc-etf-july-iv-dislocation"),
        ("okx", "ETH", "30d", "eth-election-week-iv-watch"),
        ("cme", "SOL", "90d", "sol-options-quiet"),
    )
    blocked = report.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.snapshot_age_seconds == d("2400.000000")
    assert blocked.atm_iv_z_score_abs == d("4.400000")
    assert blocked.skew_change_abs == d("0.180000")
    assert blocked.term_structure_kink_abs == d("0.150000")
    assert blocked.spot_vol_divergence_abs == d("0.250000")
    assert blocked.risk_score == d("1.000000")
    assert blocked.upstream_reason_codes == (
        "iv_surface_feed_gap",
        "vol_index_jump",
    )
    assert blocked.reason_codes == (
        "market_research_crypto_options_iv_surface_dislocation_digest_atm_iv_z_score_pressure",
        "market_research_crypto_options_iv_surface_dislocation_digest_skew_change_pressure",
        "market_research_crypto_options_iv_surface_dislocation_digest_term_structure_kink",
        "market_research_crypto_options_iv_surface_dislocation_digest_options_volume_oi_pressure",
        "market_research_crypto_options_iv_surface_dislocation_digest_spot_vol_divergence",
        "market_research_crypto_options_iv_surface_dislocation_digest_source_freshness_gap",
        "market_research_crypto_options_iv_surface_dislocation_digest_source_quorum_gap",
        "market_research_crypto_options_iv_surface_dislocation_digest_upstream_reason_signal",
    )
    assert report.rows[1].digest_status == "watch"
    assert report.rows[1].risk_score == d("0.258846")
    assert report.rows[2].digest_status == "pass"
    assert report.rows[2].risk_score == d("0.083285")
    assert report.reason_codes == blocked.reason_codes


def test_iv_surface_dislocation_digest_timezones_reason_counts_and_sources() -> None:
    module = _module()
    generated_at = datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    source_timestamp = datetime(2026, 7, 4, 13, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "okx",
            "ETH",
            "30d",
            "eth-election-week-iv-watch",
            source_timestamp=source_timestamp,
            atm_iv_z_score=d("2.000000"),
            skew_change=d("0.050000"),
            options_volume_oi_pressure=d("0.300000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].source_timestamp == GENERATED_AT
    assert report.max_snapshot_age_seconds == d("0.000000")
    assert report.source_config_versions == (
        (
            ("okx", "ETH", "30d", "eth-election-week-iv-watch"),
            "crypto-options-iv-surface-source-v0",
        ),
    )
    assert report.reason_code_counts == (
        module.MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_options_iv_surface_dislocation_digest_"
                "atm_iv_z_score_pressure"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        module.MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_options_iv_surface_dislocation_digest_"
                "skew_change_pressure"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
        module.MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_options_iv_surface_dislocation_digest_"
                "options_volume_oi_pressure"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )


def test_iv_surface_dislocation_digest_empty_and_row_sorting_are_deterministic() -> None:
    empty = _report()
    assert empty.digest_status == "watch"
    assert empty.reason_code_counts == ()

    first = _report(
        _snapshot("venue_b", "BTC", "7d", "market_b"),
        _snapshot("venue_a", "BTC", "7d", "market_a"),
    )
    second = _report(
        _snapshot("venue_a", "BTC", "7d", "market_a"),
        _snapshot("venue_b", "BTC", "7d", "market_b"),
    )

    assert first == second
    assert tuple(row.market_slug for row in first.rows) == ("market_a", "market_b")


def test_iv_surface_dislocation_digest_validates_exact_types_flags_and_freezing() -> None:
    module = _module()

    assert (
        module
        .MarketResearchCryptoOptionsIvSurfaceDislocationDigestConfig
        .__dataclass_params__
        .frozen
    )
    assert (
        module
        .MarketResearchCryptoOptionsIvSurfaceDislocationSnapshot
        .__dataclass_params__
        .frozen
    )
    assert (
        module
        .MarketResearchCryptoOptionsIvSurfaceDislocationDigestRow
        .__dataclass_params__
        .frozen
    )
    assert (
        module
        .MarketResearchCryptoOptionsIvSurfaceDislocationDigestReasonCodeCount
        .__dataclass_params__
        .frozen
    )
    assert (
        module
        .MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport
        .__dataclass_params__
        .frozen
    )

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("iv-surface-v0"))
    with pytest.raises(ValueError, match="blocked_atm_iv_z_score_abs"):
        _config(blocked_atm_iv_z_score_abs=_DecimalSubclass("4.000000"))
    with pytest.raises(ValueError, match="min_source_quorum_count"):
        _config(min_source_quorum_count=2)
    with pytest.raises(ValueError, match="watch_risk_score"):
        _config(watch_risk_score=d("0.900000"), blocked_risk_score=d("0.700000"))
    with pytest.raises(ValueError, match="atm_iv_z_score"):
        _snapshot(atm_iv_z_score=2)
    with pytest.raises(ValueError, match="venue"):
        _snapshot(venue=_StringSubclass("deribit"))
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
            _snapshot("deribit", "BTC", "7d", "duplicate"),
            _snapshot("deribit", "BTC", "7d", "duplicate"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(_snapshot(), paper_only=False)
    with pytest.raises(FrozenInstanceError):
        _snapshot().paper_only = False  # type: ignore[misc]


def test_iv_surface_dislocation_digest_public_numeric_fields_are_decimal_only() -> None:
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
                or field.name.endswith("_pressure")
                or field.name.endswith("_divergence")
                or field.name.endswith("_change")
                or field.name.endswith("_kink")
                or field.name.endswith("_z_score")
                or field.name.endswith("_abs")
            ):
                assert type(value) is Decimal

    kwargs = {field.name: getattr(report, field.name) for field in fields(report)}
    with pytest.raises(ValueError, match="snapshot_count"):
        module.MarketResearchCryptoOptionsIvSurfaceDislocationDigestReport(
            **{**kwargs, "snapshot_count": 1},
        )


def test_iv_surface_dislocation_digest_payload_is_immutable_and_canonical() -> None:
    module = _module()
    payload = module.market_research_crypto_options_iv_surface_dislocation_digest_payload(
        _report(
            _snapshot(
                "deribit",
                "BTC",
                "7d",
                "btc-etf-july-iv-dislocation",
                atm_iv_z_score=d("4.400000"),
                skew_change=d("-0.180000"),
                term_structure_kink=d("0.150000"),
                options_volume_oi_pressure=d("0.720000"),
                spot_vol_divergence=d("0.250000"),
            ),
        ),
    )
    payload_text = repr(payload).lower()

    for forbidden in (
        "wallet",
        "auth",
        "private",
        "secret",
        "order",
        "cancel",
        "replace",
        "payload_json",
    ):
        assert forbidden not in payload_text
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["snapshot_count"] == "1.000000"
    assert payload["average_risk_score"] == "0.910000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["source_timestamp"] == "2026-07-04T12:00:00+00:00"
    assert payload["rows"][0]["market_slug"] == "btc-etf-july-iv-dislocation"
    assert payload["rows"][0]["atm_iv_z_score"] == "4.400000"
    assert payload["rows"][0]["skew_change"] == "-0.180000"
    assert payload["rows"][0]["risk_score"] == "0.910000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    _assert_no_float(payload)
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["risk_score"] = "0.000000"  # type: ignore[index]


def test_iv_surface_dislocation_digest_module_scope_excludes_io_and_mutation() -> None:
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
