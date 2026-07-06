from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 2, 11, 55, tzinfo=UTC)
CONTEXT_AT = datetime(2026, 7, 2, 8, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _api():
    return import_module("polymarket_alpha_lab.market_momentum_reversal_watchlist_report")


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    api = _api()
    values = {
        "config_version": "market-momentum-reversal-watchlist-report-v0",
        "sharp_reversal_delta_threshold": d("0.050000"),
        "stale_context_age_seconds_threshold": d("7200"),
        "thin_depth_available_threshold": d("500"),
    }
    values.update(overrides)
    return api.MarketMomentumReversalWatchlistConfig(**values)


def _candidate(
    market_key: str = "market-alpha",
    *,
    prior_probability: Decimal = d("0.640000"),
    extreme_probability: Decimal = d("0.780000"),
    latest_probability: Decimal = d("0.700000"),
    reversal_direction: str = "up_to_down",
    probability_observed_at: datetime = OBSERVED_AT,
    context_updated_at: datetime = CONTEXT_AT,
    available_depth: Decimal = d("250"),
    research_acknowledged: bool = False,
):
    api = _api()
    return api.MarketMomentumReversalWatchlistInput(
        market_key=market_key,
        prior_probability=prior_probability,
        extreme_probability=extreme_probability,
        latest_probability=latest_probability,
        reversal_direction=reversal_direction,
        probability_observed_at=probability_observed_at,
        context_updated_at=context_updated_at,
        available_depth=available_depth,
        research_acknowledged=research_acknowledged,
    )


def _report(rows: tuple[object, ...], *, cfg=None, generated_at: datetime = GENERATED_AT):
    api = _api()
    return api.build_market_momentum_reversal_watchlist_report(
        rows,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def test_watchlist_flags_reversal_stale_depth_and_missing_research_acknowledgement():
    api = _api()
    report = _report(
        (
            _candidate("market-alpha"),
            _candidate(
                "market-beta",
                prior_probability=d("0.420000"),
                extreme_probability=d("0.360000"),
                latest_probability=d("0.410000"),
                reversal_direction="down_to_up",
                probability_observed_at=GENERATED_AT - timedelta(minutes=20),
                context_updated_at=GENERATED_AT - timedelta(minutes=40),
                available_depth=d("900"),
                research_acknowledged=True,
            ),
            _candidate(
                "market-gamma",
                prior_probability=d("0.500000"),
                extreme_probability=d("0.530000"),
                latest_probability=d("0.510000"),
                probability_observed_at=GENERATED_AT - timedelta(minutes=10),
                context_updated_at=GENERATED_AT - timedelta(minutes=30),
                available_depth=d("900"),
                research_acknowledged=True,
            ),
        ),
        generated_at=datetime(2026, 7, 2, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is api.MarketMomentumReversalWatchlistReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-momentum-reversal-watchlist-report-v0"
    assert report.source_market_count == d("3")
    assert report.watchlist_market_count == d("2")
    assert report.sharp_reversal_count == d("2")
    assert report.stale_context_count == d("1")
    assert report.thin_depth_count == d("1")
    assert report.missing_research_acknowledgement_count == d("1")
    assert report.watchlist_ratio == d("0.666667")
    assert report.max_reversal_delta == d("0.080000")
    assert report.max_context_age_seconds == d("14400")
    assert report.min_available_depth == d("250")
    assert report.status == "blocked"
    assert report.reason_codes == (
        "sharp_probability_reversal_present",
        "stale_market_context_present",
        "thin_market_depth_present",
        "missing_research_acknowledgement_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert report.watchlist_rows == (
        api.MarketMomentumReversalWatchlistRow(
            market_key="market-alpha",
            status="blocked",
            reversal_direction="up_to_down",
            prior_probability=d("0.640000"),
            extreme_probability=d("0.780000"),
            latest_probability=d("0.700000"),
            probability_delta=d("0.060000"),
            reversal_delta=d("0.080000"),
            probability_observation_age_seconds=d("300"),
            context_age_seconds=d("14400"),
            available_depth=d("250"),
            flag_count=d("4"),
            sharp_reversal=True,
            stale_context=True,
            thin_depth=True,
            missing_research_acknowledgement=True,
            reason_codes=(
                "sharp_probability_reversal",
                "stale_market_context",
                "thin_market_depth",
                "missing_research_acknowledgement",
            ),
        ),
        api.MarketMomentumReversalWatchlistRow(
            market_key="market-beta",
            status="watch",
            reversal_direction="down_to_up",
            prior_probability=d("0.420000"),
            extreme_probability=d("0.360000"),
            latest_probability=d("0.410000"),
            probability_delta=d("-0.010000"),
            reversal_delta=d("0.050000"),
            probability_observation_age_seconds=d("1200"),
            context_age_seconds=d("2400"),
            available_depth=d("900"),
            flag_count=d("1"),
            sharp_reversal=True,
            stale_context=False,
            thin_depth=False,
            missing_research_acknowledgement=False,
            reason_codes=("sharp_probability_reversal",),
        ),
    )


def test_empty_and_clear_reports_are_decimal_report_only_and_json_ready():
    api = _api()
    empty = _report(())
    clear = _report(
        (
            _candidate(
                "market-clear",
                prior_probability=d("0.500000"),
                extreme_probability=d("0.530000"),
                latest_probability=d("0.510000"),
                probability_observed_at=GENERATED_AT - timedelta(minutes=5),
                context_updated_at=GENERATED_AT - timedelta(minutes=30),
                available_depth=d("900"),
                research_acknowledged=True,
            ),
        ),
    )

    assert empty.source_market_count == d("0")
    assert empty.watchlist_market_count == d("0")
    assert empty.watchlist_ratio == d("0.000000")
    assert empty.status == "empty"
    assert empty.reason_codes == ("market_momentum_reversal_watchlist_empty",)
    assert empty.watchlist_rows == ()

    assert clear.source_market_count == d("1")
    assert clear.watchlist_market_count == d("0")
    assert clear.watchlist_ratio == d("0.000000")
    assert clear.status == "pass"
    assert clear.reason_codes == ("market_momentum_reversal_watchlist_clear",)
    assert clear.watchlist_rows == ()

    payload = api.market_momentum_reversal_watchlist_payload(clear)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["source_market_count"] == "1"
    assert payload["watchlist_ratio"] == "0.000000"
    assert payload["watchlist_rows"] == []
    assert payload["derived_validation_digest"] == clear.derived_validation_digest
    _assert_no_floats(payload)


def test_payload_exposes_stable_derived_validation_digest_and_rejects_unsafe_surfaces():
    api = _api()
    report = _report((_candidate(),))

    assert type(report.derived_validation_digest) is str
    assert len(report.derived_validation_digest) == 64
    assert int(report.derived_validation_digest, 16) >= 0
    assert _report((_candidate(),)).derived_validation_digest == report.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = api.market_momentum_reversal_watchlist_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert type(payload["source_market_count"]) is str
    assert type(payload["watchlist_market_count"]) is str
    assert type(payload["watchlist_ratio"]) is str
    assert type(payload["watchlist_rows"][0]["reversal_delta"]) is str
    assert type(payload["watchlist_rows"][0]["context_age_seconds"]) is str
    assert api.market_momentum_reversal_watchlist_payload(payload) == payload

    with pytest.raises(ValueError, match="paper_only"):
        api.market_momentum_reversal_watchlist_payload({**payload, "paper_only": False})
    with pytest.raises(ValueError, match="Decimal-derived"):
        api.market_momentum_reversal_watchlist_payload(
            {**payload, "source_market_count": 1},
        )
    with pytest.raises(ValueError, match="float"):
        api.market_momentum_reversal_watchlist_payload(
            {**payload, "watchlist_ratio": 0.5},
        )

    for unsafe_key in (
        "live_trading_enabled",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_url",
        "database_uri",
        "persist_path",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            api.market_momentum_reversal_watchlist_payload(
                {**payload, unsafe_key: "redacted"},
            )

    for unsafe_value in (
        "live-market",
        "auth-market",
        "wallet-market",
        "order-market",
        "network-market",
        "database-market",
        "persist-market",
    ):
        bad_row = {**payload["watchlist_rows"][0], "market_key": unsafe_value}
        with pytest.raises(ValueError, match="unsafe"):
            api.market_momentum_reversal_watchlist_payload(
                {**payload, "watchlist_rows": [bad_row]},
            )


def test_dataclasses_are_frozen_strict_decimal_utc_and_flag_guarded():
    api = _api()
    report = _report((_candidate(),))

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.watchlist_rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        _config(sharp_reversal_delta_threshold=_DecimalSubclass("0.050000"))
    with pytest.raises(ValueError, match="Decimal"):
        _candidate(prior_probability=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        _candidate(probability_observed_at=datetime(2026, 7, 2, 11, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        _report((), generated_at=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="UTC offset"):
        _candidate(
            probability_observed_at=datetime(
                2026,
                7,
                2,
                11,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="UTC offset"):
        _report(
            (),
            generated_at=datetime(
                2026,
                7,
                2,
                12,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            (),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="research_acknowledged"):
        _candidate(research_acknowledged=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="config"):
        api.build_market_momentum_reversal_watchlist_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_report_rejects_duplicates_future_inputs_and_inconsistent_public_counts():
    report = _report(
        (
            _candidate("market-alpha"),
            _candidate(
                "market-beta",
                prior_probability=d("0.420000"),
                extreme_probability=d("0.360000"),
                latest_probability=d("0.410000"),
                reversal_direction="down_to_up",
                probability_observed_at=GENERATED_AT - timedelta(minutes=20),
                context_updated_at=GENERATED_AT - timedelta(minutes=40),
                available_depth=d("900"),
                research_acknowledged=True,
            ),
        ),
    )

    with pytest.raises(ValueError, match="duplicate market_key"):
        _report((_candidate("market-dup"), _candidate("market-dup")))
    with pytest.raises(ValueError, match="probability_observed_at must not be after"):
        _report(
            (
                _candidate(
                    "market-future",
                    probability_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="context_updated_at must not be after"):
        _report(
            (
                _candidate(
                    "market-future-context",
                    context_updated_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="watchlist_market_count"):
        replace(report, watchlist_market_count=d("3"))
    with pytest.raises(ValueError, match="watchlist_rows"):
        replace(report, watchlist_rows=tuple(reversed(report.watchlist_rows)))
    with pytest.raises(ValueError, match="flag_count"):
        replace(report.watchlist_rows[0], flag_count=d("3"))


def test_module_scope_is_pure_in_memory_report_only_without_sensitive_surfaces():
    module = _api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert {
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
    }.issubset(set(module.UNSAFE_PUBLIC_SURFACE_FRAGMENTS))

    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name is not None:
                called_names.add(call_name.rsplit(".", maxsplit=1)[-1])

    assert imported_modules == {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
        "polymarket_alpha_lab.team_paper_guard",
    }
    assert {
        "connect",
        "execute",
        "executemany",
        "open",
        "print",
        "read_text",
        "request",
        "send",
        "write_text",
    }.isdisjoint(called_names)

    sample_report = _report((_candidate(),))
    report_field_names = {field.name for field in fields(sample_report)}
    row_field_names = {field.name for field in fields(sample_report.watchlist_rows[0])}
    assert {
        "market_slug",
        "question",
        "condition_id",
        "raw_payload",
        "private_key",
    }.isdisjoint(report_field_names | row_field_names)

    for field_name in (
        "source_market_count",
        "watchlist_market_count",
        "sharp_reversal_count",
        "stale_context_count",
        "thin_depth_count",
        "missing_research_acknowledgement_count",
        "watchlist_ratio",
        "max_reversal_delta",
        "max_context_age_seconds",
        "min_available_depth",
    ):
        assert type(getattr(sample_report, field_name)) is Decimal
    for field_name in (
        "probability_delta",
        "reversal_delta",
        "probability_observation_age_seconds",
        "context_age_seconds",
        "flag_count",
    ):
        assert type(getattr(sample_report.watchlist_rows[0], field_name)) is Decimal


def _assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("JSON-ready values must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, list | tuple):
        for item in value:
            _assert_no_floats(item)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None
