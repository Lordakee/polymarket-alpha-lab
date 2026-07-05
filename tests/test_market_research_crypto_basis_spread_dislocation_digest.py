from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_crypto_basis_spread_dislocation_digest import (
    DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION,
    MarketResearchCryptoBasisSpreadDislocationDigestConfig,
    MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount,
    MarketResearchCryptoBasisSpreadDislocationDigestReport,
    MarketResearchCryptoBasisSpreadDislocationDigestRow,
    MarketResearchCryptoBasisSpreadDislocationSnapshot,
    build_market_research_crypto_basis_spread_dislocation_digest,
    market_research_crypto_basis_spread_dislocation_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 5, 12, 0, tzinfo=UTC)


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


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(
    **overrides: object,
) -> MarketResearchCryptoBasisSpreadDislocationDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CRYPTO_BASIS_SPREAD_DISLOCATION_DIGEST_CONFIG_VERSION
        ),
        "max_snapshot_age_seconds": d("3600.000000"),
        "watch_spread_dislocation_abs": d("0.015000"),
        "blocked_spread_dislocation_abs": d("0.035000"),
        "watch_spread_change_abs": d("0.010000"),
        "blocked_spread_change_abs": d("0.025000"),
        "min_source_count": d("3.000000"),
        "min_liquidity_usd": d("1000000.000000"),
        "min_confidence": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchCryptoBasisSpreadDislocationDigestConfig(**values)


def _snapshot(
    condition_id: str = "condition_alpha",
    spread_id: str = "btc_calendar_spread",
    *,
    asset_symbol: str = "BTC",
    basis_pair: str = "perp_quarterly",
    near_tenor: str = "perp",
    far_tenor: str = "quarterly",
    observed_at: datetime = GENERATED_AT,
    near_basis_pct: Decimal = d("0.004000"),
    far_basis_pct: Decimal = d("0.010000"),
    expected_spread_pct: Decimal = d("0.002000"),
    observed_spread_pct: Decimal = d("0.006000"),
    previous_spread_pct: Decimal = d("0.004000"),
    source_count: Decimal = d("3.000000"),
    liquidity_usd: Decimal = d("2500000.000000"),
    confidence: Decimal = d("0.820000"),
    source_config_version: str = "basis-spread-source-v0",
) -> MarketResearchCryptoBasisSpreadDislocationSnapshot:
    return MarketResearchCryptoBasisSpreadDislocationSnapshot(
        condition_id=condition_id,
        spread_id=spread_id,
        asset_symbol=asset_symbol,
        basis_pair=basis_pair,
        near_tenor=near_tenor,
        far_tenor=far_tenor,
        observed_at=observed_at,
        near_basis_pct=near_basis_pct,
        far_basis_pct=far_basis_pct,
        expected_spread_pct=expected_spread_pct,
        observed_spread_pct=observed_spread_pct,
        previous_spread_pct=previous_spread_pct,
        source_count=source_count,
        liquidity_usd=liquidity_usd,
        confidence=confidence,
        source_config_version=source_config_version,
    )


def _report(
    *snapshots: MarketResearchCryptoBasisSpreadDislocationSnapshot,
    generated_at: datetime = GENERATED_AT,
    config: MarketResearchCryptoBasisSpreadDislocationDigestConfig | None = None,
) -> MarketResearchCryptoBasisSpreadDislocationDigestReport:
    return build_market_research_crypto_basis_spread_dislocation_digest(
        snapshots,
        config=config or _config(),
        generated_at=generated_at,
    )


def test_basis_spread_dislocation_digest_summarizes_blocked_watch_and_pass_rows() -> None:
    report = _report(
        _snapshot(
            "condition_watch",
            "sol_calendar_spread",
            asset_symbol="SOL",
            basis_pair="perp_monthly",
            near_tenor="perp",
            far_tenor="monthly",
            observed_at=GENERATED_AT - timedelta(seconds=900),
            near_basis_pct=d("0.007000"),
            far_basis_pct=d("0.027000"),
            expected_spread_pct=d("0.003000"),
            observed_spread_pct=d("0.020000"),
            previous_spread_pct=d("0.014000"),
            source_count=d("2.000000"),
            liquidity_usd=d("800000.000000"),
            confidence=d("0.760000"),
        ),
        _snapshot(
            "condition_pass",
            "btc_calendar_spread",
            observed_at=GENERATED_AT - timedelta(seconds=120),
        ),
        _snapshot(
            "condition_blocked",
            "eth_calendar_spread",
            asset_symbol="ETH",
            basis_pair="perp_quarterly",
            near_tenor="perp",
            far_tenor="quarterly",
            observed_at=GENERATED_AT - timedelta(seconds=4_200),
            near_basis_pct=d("0.011000"),
            far_basis_pct=d("0.061000"),
            expected_spread_pct=d("0.004000"),
            observed_spread_pct=d("0.050000"),
            previous_spread_pct=d("0.018000"),
            source_count=d("1.000000"),
            liquidity_usd=d("700000.000000"),
            confidence=d("0.520000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_crypto_basis_spread_dislocation_digest"
    )
    assert report.snapshot_count == d("3.000000")
    assert report.pass_snapshot_count == d("1.000000")
    assert report.watch_snapshot_count == d("1.000000")
    assert report.blocked_snapshot_count == d("1.000000")
    assert report.spread_dislocation_snapshot_count == d("2.000000")
    assert report.spread_change_snapshot_count == d("1.000000")
    assert report.source_gap_snapshot_count == d("2.000000")
    assert report.liquidity_gap_snapshot_count == d("2.000000")
    assert report.stale_snapshot_count == d("1.000000")
    assert report.confidence_gap_snapshot_count == d("1.000000")
    assert report.average_observed_spread_pct == d("0.025333")
    assert report.average_spread_dislocation_abs == d("0.022333")
    assert report.max_spread_dislocation_abs == d("0.046000")
    assert report.max_snapshot_age_seconds == d("4200.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.spread_id for row in report.rows) == (
        "eth_calendar_spread",
        "sol_calendar_spread",
        "btc_calendar_spread",
    )
    blocked, watch, passed = report.rows
    assert blocked.digest_status == "blocked"
    assert blocked.snapshot_age_seconds == d("4200.000000")
    assert blocked.spread_dislocation_abs == d("0.046000")
    assert blocked.spread_change_abs == d("0.032000")
    assert blocked.reason_codes == (
        "market_research_crypto_basis_spread_dislocation_digest_blocked_spread_dislocation",
        "market_research_crypto_basis_spread_dislocation_digest_blocked_spread_change",
        "market_research_crypto_basis_spread_dislocation_digest_source_gap",
        "market_research_crypto_basis_spread_dislocation_digest_liquidity_gap",
        "market_research_crypto_basis_spread_dislocation_digest_stale_snapshot",
        "market_research_crypto_basis_spread_dislocation_digest_confidence_gap",
    )
    assert watch.digest_status == "watch"
    assert watch.reason_codes == (
        "market_research_crypto_basis_spread_dislocation_digest_watch_spread_dislocation",
        "market_research_crypto_basis_spread_dislocation_digest_source_gap",
        "market_research_crypto_basis_spread_dislocation_digest_liquidity_gap",
    )
    assert passed.digest_status == "pass"
    assert passed.reason_codes == (
        "market_research_crypto_basis_spread_dislocation_digest_spread_aligned",
    )
    assert report.reason_codes == (
        "market_research_crypto_basis_spread_dislocation_digest_blocked_spread_dislocation",
        "market_research_crypto_basis_spread_dislocation_digest_watch_spread_dislocation",
        "market_research_crypto_basis_spread_dislocation_digest_blocked_spread_change",
        "market_research_crypto_basis_spread_dislocation_digest_source_gap",
        "market_research_crypto_basis_spread_dislocation_digest_liquidity_gap",
        "market_research_crypto_basis_spread_dislocation_digest_stale_snapshot",
        "market_research_crypto_basis_spread_dislocation_digest_confidence_gap",
    )


def test_basis_spread_dislocation_digest_normalizes_timezones_and_reason_counts() -> None:
    generated_at = datetime(2026, 7, 5, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 7, 5, 12, 0, tzinfo=timezone(timedelta(hours=1)))

    report = _report(
        _snapshot(
            "condition_gamma",
            "xrp_calendar_spread",
            asset_symbol="XRP",
            observed_at=observed_at,
            observed_spread_pct=d("0.012000"),
            expected_spread_pct=d("0.001000"),
            previous_spread_pct=d("0.004000"),
            source_count=d("2.000000"),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 7, 5, 11, 0, tzinfo=UTC)
    assert report.max_snapshot_age_seconds == d("3600.000000")
    assert report.digest_status == "watch"
    assert report.reason_code_counts == (
        MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_basis_spread_dislocation_digest_source_gap"
            ),
            count=d("1.000000"),
            snapshot_ratio=d("1.000000"),
        ),
    )
    assert report.source_config_versions == (
        ("xrp_calendar_spread", "basis-spread-source-v0"),
    )


def test_basis_spread_dislocation_digest_empty_input_is_blocked_and_sorting_is_deterministic() -> None:
    empty = _report()
    assert empty.digest_status == "blocked"
    assert empty.recommended_next_step == (
        "block_report_only_market_research_crypto_basis_spread_dislocation_digest"
    )
    assert empty.snapshot_count == d("0.000000")
    assert empty.pass_snapshot_count == d("0.000000")
    assert empty.blocked_snapshot_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_crypto_basis_spread_dislocation_digest_no_inputs",
    )

    first = _report(
        _snapshot("condition_b", "spread_b"),
        _snapshot("condition_a", "spread_a"),
    )
    second = _report(
        _snapshot("condition_a", "spread_a"),
        _snapshot("condition_b", "spread_b"),
    )

    assert first == second
    assert tuple(row.spread_id for row in first.rows) == ("spread_a", "spread_b")


def test_basis_spread_dislocation_digest_exercises_watch_spread_change_branch() -> None:
    report = _report(
        _snapshot(
            "condition_change_watch",
            "spread_change_watch",
            expected_spread_pct=d("0.014000"),
            observed_spread_pct=d("0.016000"),
            previous_spread_pct=d("0.004000"),
        ),
    )

    assert report.digest_status == "watch"
    assert report.spread_dislocation_snapshot_count == d("0.000000")
    assert report.spread_change_snapshot_count == d("1.000000")
    assert report.rows[0].spread_dislocation_abs == d("0.002000")
    assert report.rows[0].spread_change_abs == d("0.012000")
    assert report.rows[0].reason_codes == (
        "market_research_crypto_basis_spread_dislocation_digest_watch_spread_change",
    )
    assert report.reason_codes == (
        "market_research_crypto_basis_spread_dislocation_digest_watch_spread_change",
    )


def test_basis_spread_dislocation_digest_validates_types_flags_freezing_and_canonical_inputs() -> None:
    assert MarketResearchCryptoBasisSpreadDislocationDigestConfig.__dataclass_params__.frozen
    assert MarketResearchCryptoBasisSpreadDislocationSnapshot.__dataclass_params__.frozen
    assert MarketResearchCryptoBasisSpreadDislocationDigestRow.__dataclass_params__.frozen
    assert (
        MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount.__dataclass_params__.frozen
    )
    assert MarketResearchCryptoBasisSpreadDislocationDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("basis-spread-dislocation-v0"))
    with pytest.raises(ValueError, match="watch_spread_dislocation_abs"):
        _config(watch_spread_dislocation_abs=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="max_snapshot_age_seconds"):
        _config(max_snapshot_age_seconds=d("3600"))
    with pytest.raises(ValueError, match="blocked_spread_dislocation_abs"):
        _config(
            watch_spread_dislocation_abs=d("0.040000"),
            blocked_spread_dislocation_abs=d("0.035000"),
        )
    for flag_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=flag_name):
            _config(**{flag_name: False})
    with pytest.raises(ValueError, match="source_count"):
        _config(min_source_count=3)
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=_DecimalSubclass("0.820000"))
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=d("0.82"))
    with pytest.raises(ValueError, match="confidence"):
        _snapshot(confidence=Decimal("0.8200000"))
    with pytest.raises(ValueError, match="condition_id"):
        _snapshot(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="redacted"):
        _snapshot(source_config_version="source-wallet-v0")
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=_DateTimeSubclass(2026, 7, 5, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            _snapshot(),
            generated_at=datetime(2026, 7, 5, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _snapshot(observed_at=datetime(2026, 7, 5, 12, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="observed_at"):
        _snapshot(observed_at=_DateTimeSubclass(2026, 7, 5, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="future"):
        _report(_snapshot(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique"):
        _report(_snapshot(spread_id="duplicate"), _snapshot(spread_id="duplicate"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(_snapshot(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(_snapshot(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_snapshot(), readonly=False)
    with pytest.raises(FrozenInstanceError):
        _snapshot().paper_only = False  # type: ignore[misc]

    report = _report(_snapshot("condition_b", "spread_b"), _snapshot("condition_a", "spread_a"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchCryptoBasisSpreadDislocationDigestReport)
    }
    row_kwargs = {
        field.name: getattr(report.rows[0], field.name)
        for field in fields(MarketResearchCryptoBasisSpreadDislocationDigestRow)
    }
    for flag_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=flag_name):
            MarketResearchCryptoBasisSpreadDislocationDigestRow(
                **{**row_kwargs, flag_name: False},
            )
    with pytest.raises(ValueError, match="confidence"):
        MarketResearchCryptoBasisSpreadDislocationDigestRow(
            **{**row_kwargs, "confidence": _DecimalSubclass("0.820000")},
        )
    with pytest.raises(ValueError, match="snapshot_age_seconds"):
        MarketResearchCryptoBasisSpreadDislocationDigestRow(
            **{**row_kwargs, "snapshot_age_seconds": d("0.0")},
        )
    with pytest.raises(ValueError, match="snapshot_age_seconds"):
        MarketResearchCryptoBasisSpreadDislocationDigestRow(
            **{**row_kwargs, "snapshot_age_seconds": Decimal("0.0000000")},
        )
    with pytest.raises(ValueError, match="reason_codes"):
        MarketResearchCryptoBasisSpreadDislocationDigestRow(
            **{**row_kwargs, "reason_codes": list(report.rows[0].reason_codes)},
        )
    with pytest.raises(ValueError, match="rows"):
        MarketResearchCryptoBasisSpreadDislocationDigestReport(
            **{**kwargs, "rows": list(report.rows)},
        )
    with pytest.raises(ValueError, match="rows"):
        MarketResearchCryptoBasisSpreadDislocationDigestReport(
            **{**kwargs, "rows": tuple(reversed(report.rows))},
        )
    with pytest.raises(ValueError, match="source_config_versions"):
        MarketResearchCryptoBasisSpreadDislocationDigestReport(
            **{
                **kwargs,
                "source_config_versions": list(report.source_config_versions),
            },
        )
    with pytest.raises(ValueError, match="source_config_versions"):
        MarketResearchCryptoBasisSpreadDislocationDigestReport(
            **{
                **kwargs,
                "source_config_versions": tuple(reversed(report.source_config_versions)),
            },
        )
    reason_report = _report(
        _snapshot(
            "condition_reason",
            "spread_reason",
            source_count=d("2.000000"),
            liquidity_usd=d("800000.000000"),
        ),
    )
    reason_kwargs = {
        field.name: getattr(reason_report, field.name)
        for field in fields(MarketResearchCryptoBasisSpreadDislocationDigestReport)
    }
    reason_count_kwargs = {
        field.name: getattr(reason_report.reason_code_counts[0], field.name)
        for field in fields(MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount)
    }
    for flag_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=flag_name):
            MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount(
                **{**reason_count_kwargs, flag_name: False},
            )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoBasisSpreadDislocationDigestReport(
            **{
                **reason_kwargs,
                "reason_code_counts": list(reason_report.reason_code_counts),
            },
        )
    with pytest.raises(ValueError, match="reason_codes"):
        MarketResearchCryptoBasisSpreadDislocationDigestReport(
            **{**reason_kwargs, "reason_codes": list(reason_report.reason_codes)},
        )
    with pytest.raises(ValueError, match="reason_codes"):
        MarketResearchCryptoBasisSpreadDislocationDigestReport(
            **{
                **reason_kwargs,
                "reason_codes": tuple(reversed(reason_report.reason_codes)),
            },
        )


def test_basis_spread_dislocation_digest_public_numerics_are_decimal_only() -> None:
    report = _report(_snapshot())

    for row in report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if _is_public_numeric_field(field.name):
                assert type(value) is Decimal, field.name
    for field in fields(report):
        value = getattr(report, field.name)
        if _is_public_numeric_field(field.name):
            assert type(value) is Decimal, field.name
    for reason_count in report.reason_code_counts:
        assert reason_count.paper_only is True
        assert reason_count.report_only is True
        assert reason_count.readonly is True
        assert type(reason_count.count) is Decimal
        assert type(reason_count.snapshot_ratio) is Decimal

    kwargs = {
        field.name: getattr(report, field.name)
        for field in fields(MarketResearchCryptoBasisSpreadDislocationDigestReport)
    }
    assert (
        MarketResearchCryptoBasisSpreadDislocationDigestReport(**kwargs).digest_status
        == "pass"
    )
    with pytest.raises(ValueError, match="snapshot_count"):
        MarketResearchCryptoBasisSpreadDislocationDigestReport(
            **{**kwargs, "snapshot_count": d("2.000000")},
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        MarketResearchCryptoBasisSpreadDislocationDigestReport(
            **{
                **kwargs,
                "reason_code_counts": (
                    MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount(
                        reason_code=(
                            "market_research_crypto_basis_spread_dislocation_digest_spread_aligned"
                        ),
                        count=d("2.000000"),
                        snapshot_ratio=d("1.000000"),
                    ),
                ),
            },
        )
    with pytest.raises(ValueError, match="count"):
        MarketResearchCryptoBasisSpreadDislocationDigestReasonCodeCount(
            reason_code=(
                "market_research_crypto_basis_spread_dislocation_digest_spread_aligned"
            ),
            count=d("0.000000"),
            snapshot_ratio=d("0.000000"),
        )


def test_basis_spread_dislocation_digest_payload_is_immutable_redacted_and_six_decimal() -> None:
    payload = market_research_crypto_basis_spread_dislocation_digest_payload(
        _report(
            _snapshot(
                "condition_redacted",
                "btc_calendar_spread_redacted",
                asset_symbol="BTC",
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
        "private",
        "payload_json",
    ):
        assert forbidden not in payload_text
    assert payload["generated_at"] == "2026-07-05T12:00:00+00:00"
    assert payload["snapshot_count"] == "1.000000"
    assert payload["average_spread_dislocation_abs"] == "0.004000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["observed_at"] == "2026-07-05T12:00:00+00:00"
    assert payload["rows"][0]["near_basis_pct"] == "0.004000"
    assert payload["rows"][0]["spread_dislocation_abs"] == "0.004000"
    assert payload["rows"][0]["paper_only"] is True
    assert_no_float_int_or_decimal_payload_numbers(payload)
    with pytest.raises(TypeError):
        payload["snapshot_count"] = "0.000000"  # type: ignore[index]
    with pytest.raises(TypeError):
        payload["rows"][0]["spread_dislocation_abs"] = "0.000000"  # type: ignore[index]


def test_basis_spread_dislocation_digest_payload_recursively_revalidates_public_dataclasses() -> None:
    report = _report(_snapshot())
    object.__setattr__(report, "snapshot_count", 1)
    with pytest.raises(ValueError, match="snapshot_count"):
        market_research_crypto_basis_spread_dislocation_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report, "generated_at", datetime(2026, 7, 5, 8, 0, tzinfo=timezone(timedelta(hours=-4))))
    with pytest.raises(ValueError, match="payload datetimes must be UTC"):
        market_research_crypto_basis_spread_dislocation_digest_payload(report)

    report = _report(_snapshot())
    row = report.rows[0]
    object.__setattr__(row, "spread_dislocation_abs", d("0.999999"))
    with pytest.raises(ValueError, match="spread_dislocation_abs"):
        market_research_crypto_basis_spread_dislocation_digest_payload(report)

    report = _report(_snapshot())
    object.__setattr__(report, "rows", (object(),))
    with pytest.raises(ValueError, match="rows"):
        market_research_crypto_basis_spread_dislocation_digest_payload(report)

    with pytest.raises(ValueError, match="report must be exactly"):
        market_research_crypto_basis_spread_dislocation_digest_payload(object())


def test_basis_spread_dislocation_digest_module_scope_is_pure_report_only() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_crypto_basis_spread_dislocation_digest",
    )
    source_text = module.__loader__.get_source(module.__name__)
    assert source_text is not None
    lowered = source_text.lower()
    tree = ast.parse(source_text)

    forbidden_literals = (
        "market_slug",
        "question",
        "live trading",
        "trade",
        "auth",
        "wallet",
        "private",
        "token",
        "secret",
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
        "subprocess",
        "socket",
        "http",
        "psycopg",
        "payload_json",
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
                "replace",
            }
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "pathlib",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_float_int_or_decimal_payload_numbers(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_int_or_decimal_payload_numbers(item)
        return
    if isinstance(value, tuple):
        for item in value:
            assert_no_float_int_or_decimal_payload_numbers(item)
        return
    if isinstance(value, bool):
        return
    assert not isinstance(value, (Decimal, float, int))


def _is_public_numeric_field(field_name: str) -> bool:
    return (
        field_name.endswith("_count")
        or field_name.endswith("_seconds")
        or field_name.endswith("_pct")
        or field_name.endswith("_abs")
        or field_name.endswith("_usd")
        or field_name.endswith("_ratio")
        or field_name == "confidence"
    )
