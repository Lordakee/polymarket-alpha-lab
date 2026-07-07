from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import json

import pytest

import polymarket_alpha_lab.market_context_source_freshness_ladder_report as module
from polymarket_alpha_lab.market_context_source_freshness_ladder_report import (
    CHECK_NAMES,
    MarketContextSourceFreshnessLadderConfig,
    MarketContextSourceFreshnessLadderReport,
    MarketContextSourceFreshnessLadderRow,
    MarketContextSourceFreshnessObservation,
    build_market_context_source_freshness_ladder_report,
    to_market_context_source_freshness_ladder_payload,
)


GENERATED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _thresholds() -> tuple[tuple[str, Decimal], ...]:
    return (
        ("liquidity", Decimal("60")),
        ("price_probability", Decimal("300")),
        ("event_news", Decimal("600")),
        ("close_time", Decimal("300")),
        ("resolution_source", Decimal("86400")),
    )


def _config(**overrides) -> MarketContextSourceFreshnessLadderConfig:
    values = {
        "config_version": "market-context-source-freshness-ladder-v0",
        "max_age_seconds_by_check": _thresholds(),
        "min_market_count": Decimal("1"),
    }
    values.update(overrides)
    return MarketContextSourceFreshnessLadderConfig(**values)


def _single_check_config(
    check_name: str = "liquidity",
    *,
    max_age_seconds: Decimal = Decimal("60"),
) -> MarketContextSourceFreshnessLadderConfig:
    return _config(
        max_age_seconds_by_check=((check_name, max_age_seconds),),
        required_check_names=(check_name,),
    )


def _observation(
    check_name: str,
    *,
    market_slug: str = "alpha-market",
    source_id: str | None = None,
    seconds_old: int = 10,
    observed_at: datetime | None = None,
    stale_acknowledged_at: datetime | None = None,
    missing_reason: str | None = None,
    blocked_reason: str | None = None,
) -> MarketContextSourceFreshnessObservation:
    return MarketContextSourceFreshnessObservation(
        market_slug=market_slug,
        check_name=check_name,
        source_id=source_id if source_id is not None else f"{check_name}-feed",
        observed_at=(
            observed_at
            if observed_at is not None
            else GENERATED_AT - timedelta(seconds=seconds_old)
        ),
        stale_acknowledged_at=stale_acknowledged_at,
        missing_reason=missing_reason,
        blocked_reason=blocked_reason,
    )


def _assert_public_payload_has_no_numeric_scalars(value: object) -> None:
    if type(value) in (Decimal, float, int):
        pytest.fail(f"public payload must serialize numeric values as strings: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_public_payload_has_no_numeric_scalars(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_public_payload_has_no_numeric_scalars(item)


def test_ladder_report_reduces_required_checks_with_decimal_counts_ratios_and_sorting():
    report = build_market_context_source_freshness_ladder_report(
        (
            _observation("resolution_source", seconds_old=120),
            _observation(
                "price_probability",
                seconds_old=305,
                stale_acknowledged_at=GENERATED_AT - timedelta(seconds=5),
            ),
            _observation("event_news", seconds_old=120),
            _observation("close_time", seconds_old=400),
            _observation("liquidity", seconds_old=30),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MarketContextSourceFreshnessLadderReport)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.status == "blocked"
    assert report.reason_codes == (
        "unacknowledged_stale_market_context_source",
        "stale_acknowledged_market_context_source",
    )
    assert report.market_count == Decimal("1")
    assert report.required_check_count == Decimal("5")
    assert report.row_count == Decimal("5")
    assert report.pass_count == Decimal("3")
    assert report.watch_count == Decimal("1")
    assert report.blocked_count == Decimal("1")
    assert report.stale_acknowledged_count == Decimal("1")
    assert report.unacknowledged_stale_count == Decimal("1")
    assert report.missing_count == Decimal("0")
    assert report.source_blocked_count == Decimal("0")
    assert report.freshness_ratio == Decimal("0.6")
    assert report.stale_acknowledged_ratio == Decimal("0.2")
    assert report.max_observed_age_seconds == Decimal("400")
    assert tuple(row.check_name for row in report.rows) == (
        "close_time",
        "price_probability",
        "liquidity",
        "event_news",
        "resolution_source",
    )
    assert tuple(row.status for row in report.rows) == (
        "blocked",
        "watch",
        "pass",
        "pass",
        "pass",
    )
    assert tuple(row.stale_acknowledgement_severity for row in report.rows) == (
        "unacknowledged",
        "acknowledged",
        "none",
        "none",
        "none",
    )
    assert report.rows[0].age_seconds == Decimal("400")
    assert report.rows[0].reason_codes == ("unacknowledged_stale_close_time_source",)
    assert report.rows[1].age_seconds == Decimal("305")
    assert report.rows[1].reason_codes == (
        "acknowledged_stale_price_probability_source",
    )
    assert all(type(value) is Decimal for value in (
        report.market_count,
        report.required_check_count,
        report.row_count,
        report.pass_count,
        report.watch_count,
        report.blocked_count,
        report.freshness_ratio,
        report.stale_acknowledged_ratio,
        report.rows[0].age_seconds,
    ))


def test_ladder_report_expands_missing_required_checks_and_blocks():
    report = build_market_context_source_freshness_ladder_report(
        (_observation("liquidity", seconds_old=30),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.status == "blocked"
    assert report.reason_codes == ("missing_market_context_source",)
    assert report.market_count == Decimal("1")
    assert report.row_count == Decimal("5")
    assert report.pass_count == Decimal("1")
    assert report.blocked_count == Decimal("4")
    assert report.missing_count == Decimal("4")
    assert tuple(row.check_name for row in report.rows[:4]) == (
        "price_probability",
        "event_news",
        "close_time",
        "resolution_source",
    )
    assert tuple(row.source_id for row in report.rows[:4]) == (
        "required_check",
        "required_check",
        "required_check",
        "required_check",
    )
    assert tuple(row.reason_codes for row in report.rows[:4]) == (
        ("missing_price_probability_source",),
        ("missing_event_news_source",),
        ("missing_close_time_source",),
        ("missing_resolution_source_source",),
    )


def test_ladder_report_normalizes_offset_datetimes_to_utc_and_rejects_naive_datetimes():
    generated_at = datetime(2026, 6, 18, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    observed_at = datetime(2026, 6, 18, 13, 30, tzinfo=timezone(timedelta(hours=2)))

    report = build_market_context_source_freshness_ladder_report(
        (_observation("liquidity", observed_at=observed_at),),
        config=_single_check_config(max_age_seconds=Decimal("3600")),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].observed_at == datetime(2026, 6, 18, 11, 30, tzinfo=UTC)
    assert report.rows[0].age_seconds == Decimal("1800")

    with pytest.raises(ValueError, match="timezone-aware"):
        build_market_context_source_freshness_ladder_report(
            (_observation("liquidity"),),
            config=_single_check_config(),
            generated_at=datetime(2026, 6, 18, 12, 0),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        MarketContextSourceFreshnessObservation(
            market_slug="naive-market",
            check_name="liquidity",
            source_id="liquidity-feed",
            observed_at=datetime(2026, 6, 18, 12, 0),
        )
    with pytest.raises(ValueError, match="UTC offset"):
        MarketContextSourceFreshnessObservation(
            market_slug="none-offset-market",
            check_name="liquidity",
            source_id="liquidity-feed",
            observed_at=datetime(2026, 6, 18, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )


def test_ladder_report_validates_stale_acknowledgement_severity():
    with pytest.raises(ValueError, match="timezone-aware"):
        MarketContextSourceFreshnessObservation(
            market_slug="alpha-market",
            check_name="price_probability",
            source_id="price-feed",
            observed_at=GENERATED_AT - timedelta(seconds=305),
            stale_acknowledged_at=datetime(2026, 6, 18, 12, 0),
        )

    with pytest.raises(ValueError, match="future"):
        build_market_context_source_freshness_ladder_report(
            (
                _observation(
                    "price_probability",
                    seconds_old=305,
                    stale_acknowledged_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_single_check_config(
                "price_probability",
                max_age_seconds=Decimal("300"),
            ),
            generated_at=GENERATED_AT,
        )

    acknowledged_report = build_market_context_source_freshness_ladder_report(
        (
            _observation(
                "price_probability",
                seconds_old=305,
                stale_acknowledged_at=GENERATED_AT - timedelta(seconds=1),
            ),
        ),
        config=_single_check_config("price_probability", max_age_seconds=Decimal("300")),
        generated_at=GENERATED_AT,
    )
    unacknowledged_report = build_market_context_source_freshness_ladder_report(
        (_observation("price_probability", seconds_old=305),),
        config=_single_check_config("price_probability", max_age_seconds=Decimal("300")),
        generated_at=GENERATED_AT,
    )

    assert acknowledged_report.status == "watch"
    assert acknowledged_report.rows[0].stale_acknowledgement_severity == "acknowledged"
    assert unacknowledged_report.status == "blocked"
    assert unacknowledged_report.rows[0].stale_acknowledgement_severity == (
        "unacknowledged"
    )


def test_ladder_report_payload_is_json_ready():
    report = build_market_context_source_freshness_ladder_report(
        (_observation("liquidity", seconds_old=30),),
        config=_single_check_config(max_age_seconds=Decimal("60")),
        generated_at=GENERATED_AT,
    )

    payload = to_market_context_source_freshness_ladder_payload(report)

    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    _assert_public_payload_has_no_numeric_scalars(payload)
    assert payload["generated_at"] == "2026-06-18T12:00:00+00:00"
    assert payload["status"] == "pass"
    assert payload["counts"]["row_count"] == "1"
    assert payload["counts"]["pass_count"] == "1"
    assert payload["ratios"]["freshness_ratio"] == "1"
    assert payload["max_observed_age_seconds"] == "30"
    assert payload["min_market_count"] == "1"
    assert payload["thresholds"] == [
        {"check_name": "liquidity", "max_age_seconds": "60"}
    ]
    assert payload["rows"] == [
        {
            "market_slug": "alpha-market",
            "check_name": "liquidity",
            "source_id": "liquidity-feed",
            "observed_at": "2026-06-18T11:59:30+00:00",
            "stale_acknowledged_at": None,
            "age_seconds": "30",
            "max_age_seconds": "60",
            "status": "pass",
            "stale_acknowledgement_severity": "none",
            "missing_reason": None,
            "blocked_reason": None,
            "reason_codes": ["fresh_liquidity_source"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert all(character in "0123456789abcdef" for character in payload["derived_validation_digest"])


def test_ladder_report_uses_tamper_evident_derived_validation_digest():
    report = build_market_context_source_freshness_ladder_report(
        (_observation("liquidity", seconds_old=30),),
        config=_single_check_config(max_age_seconds=Decimal("60")),
        generated_at=GENERATED_AT,
    )

    assert len(report.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in report.derived_validation_digest)

    payload = to_market_context_source_freshness_ladder_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert to_market_context_source_freshness_ladder_payload(payload) == payload

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, derived_validation_digest="0" * 64)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        to_market_context_source_freshness_ladder_payload(missing_digest)

    tampered = dict(payload)
    tampered["status"] = "blocked"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        to_market_context_source_freshness_ladder_payload(tampered)

    numeric_payload = dict(payload)
    numeric_payload["counts"] = {**payload["counts"], "row_count": Decimal("1")}
    with pytest.raises(ValueError, match="row_count"):
        to_market_context_source_freshness_ladder_payload(numeric_payload)


def test_ladder_public_payload_rejects_recomputed_digest_with_inconsistent_row_state():
    report = build_market_context_source_freshness_ladder_report(
        (_observation("liquidity", seconds_old=30),),
        config=_single_check_config(max_age_seconds=Decimal("60")),
        generated_at=GENERATED_AT,
    )
    payload = to_market_context_source_freshness_ladder_payload(report)
    inconsistent_payload = dict(payload)
    inconsistent_payload["rows"] = [
        {
            **payload["rows"][0],
            "age_seconds": "61",
            "status": "pass",
            "reason_codes": ["fresh_liquidity_source"],
        },
    ]
    inconsistent_payload["derived_validation_digest"] = module._derived_validation_digest(
        inconsistent_payload,
    )

    with pytest.raises(ValueError, match="status must match row freshness state"):
        to_market_context_source_freshness_ladder_payload(inconsistent_payload)


def test_ladder_public_payload_rejects_recomputed_digest_with_inconsistent_report_counts():
    report = build_market_context_source_freshness_ladder_report(
        (_observation("liquidity", seconds_old=30),),
        config=_single_check_config(max_age_seconds=Decimal("60")),
        generated_at=GENERATED_AT,
    )
    payload = to_market_context_source_freshness_ladder_payload(report)
    inconsistent_payload = dict(payload)
    inconsistent_payload["counts"] = {
        **payload["counts"],
        "pass_count": "0",
        "blocked_count": "1",
    }
    inconsistent_payload["ratios"] = {
        **payload["ratios"],
        "freshness_ratio": "0",
    }
    inconsistent_payload["status"] = "blocked"
    inconsistent_payload["reason_codes"] = ["missing_market_context_source"]
    inconsistent_payload["derived_validation_digest"] = module._derived_validation_digest(
        inconsistent_payload,
    )

    with pytest.raises(ValueError, match="pass_count must match rows"):
        to_market_context_source_freshness_ladder_payload(inconsistent_payload)


def test_ladder_report_validates_exact_scalar_types_and_decimal_only_counts():
    with pytest.raises(ValueError, match="min_market_count"):
        _config(min_market_count=1)
    with pytest.raises(ValueError, match="max_age_seconds"):
        _config(max_age_seconds_by_check=(("liquidity", _DecimalSubclass("60")),))
    with pytest.raises(ValueError, match="check_name"):
        MarketContextSourceFreshnessObservation(
            market_slug="alpha-market",
            check_name=_StringSubclass("liquidity"),
            source_id="liquidity-feed",
            observed_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_context_source_freshness_ladder_report(
            (_observation("liquidity"),),
            config=_single_check_config(),
            generated_at=_DateTimeSubclass(2026, 6, 18, 12, 0, tzinfo=UTC),
        )

    report = build_market_context_source_freshness_ladder_report(
        (_observation("liquidity", seconds_old=30),),
        config=_single_check_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="age_seconds"):
        replace(report.rows[0], age_seconds=30)
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=1)


def test_ladder_report_dataclasses_are_frozen_and_hard_flags_are_true():
    observation = _observation("liquidity", seconds_old=30)
    report = build_market_context_source_freshness_ladder_report(
        (observation,),
        config=_single_check_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        observation.source_id = "other"
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"
    with pytest.raises(ValueError, match="paper_only"):
        replace(_single_check_config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(observation, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)


def test_ladder_report_rejects_duplicate_future_and_invalid_source_shapes():
    with pytest.raises(ValueError, match="duplicate"):
        build_market_context_source_freshness_ladder_report(
            (
                _observation("liquidity", source_id="first-feed"),
                _observation("liquidity", source_id="second-feed"),
            ),
            config=_single_check_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future"):
        build_market_context_source_freshness_ladder_report(
            (
                _observation(
                    "liquidity",
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
            config=_single_check_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="observed_at"):
        MarketContextSourceFreshnessObservation(
            market_slug="alpha-market",
            check_name="liquidity",
            source_id="liquidity-feed",
            observed_at=GENERATED_AT,
            missing_reason="source_not_available",
        )
    with pytest.raises(ValueError, match="unsafe text"):
        MarketContextSourceFreshnessObservation(
            market_slug="alpha-market",
            check_name="liquidity",
            source_id="token-bearing-source",
            observed_at=GENERATED_AT,
        )
    for unsafe_source_id in (
        "live-mode-source",
        "network-client-source",
        "database-backed-source",
        "persist-path-source",
    ):
        with pytest.raises(ValueError, match="unsafe text"):
            MarketContextSourceFreshnessObservation(
                market_slug="alpha-market",
                check_name="liquidity",
                source_id=unsafe_source_id,
                observed_at=GENERATED_AT,
            )
    with pytest.raises(ValueError, match="blocked_reason"):
        MarketContextSourceFreshnessObservation(
            market_slug="alpha-market",
            check_name="liquidity",
            source_id="liquidity-feed",
            missing_reason="source_not_available",
            blocked_reason="source_disabled",
        )


def test_ladder_report_requires_full_required_check_coverage_per_market():
    report = build_market_context_source_freshness_ladder_report(
        (_observation("liquidity", seconds_old=30),),
        config=_single_check_config(max_age_seconds=Decimal("60")),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="required check coverage"):
        replace(
            report,
            required_check_count=Decimal("5"),
            max_age_seconds_by_check=_thresholds(),
            derived_validation_digest="",
        )


def test_ladder_report_requires_row_thresholds_to_match_report_thresholds():
    report = build_market_context_source_freshness_ladder_report(
        (_observation("liquidity", seconds_old=30),),
        config=_single_check_config(max_age_seconds=Decimal("60")),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="max_age_seconds must match thresholds"):
        replace(
            report,
            max_age_seconds_by_check=(("liquidity", Decimal("120")),),
            derived_validation_digest="",
        )


def test_ladder_public_payload_rejects_live_auth_wallet_order_network_database_persist_surface():
    report = build_market_context_source_freshness_ladder_report(
        (_observation("liquidity", seconds_old=30),),
        config=_single_check_config(max_age_seconds=Decimal("60")),
        generated_at=GENERATED_AT,
    )
    payload = to_market_context_source_freshness_ladder_payload(report)

    unsafe_keys = (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_client",
        "database_url",
        "persist_path",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            to_market_context_source_freshness_ladder_payload(unsafe_payload)

    unsafe_values = (
        "live mode enabled",
        "auth token configured",
        "wallet transfer configured",
        "submit order configured",
        "network client configured",
        "database url configured",
        "persist path configured",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_payload["rows"] = [
            {**payload["rows"][0], "source_id": unsafe_value},
        ]
        with pytest.raises(ValueError, match="unsafe"):
            to_market_context_source_freshness_ladder_payload(unsafe_payload)


def test_ladder_module_public_api_has_no_live_execution_surfaces():
    blocked_terms = (
        "live",
        "auth",
        "wallet",
        "account",
        "broker",
        "order",
        "network",
        "database",
        "persist",
        "submit",
        "cancel",
        "signing",
        "advice",
        "trade",
        "trading",
    )

    assert set(CHECK_NAMES) == {
        "liquidity",
        "price_probability",
        "event_news",
        "close_time",
        "resolution_source",
    }
    assert module.__all__
    assert not [
        public_name
        for public_name in module.__all__
        if any(term in public_name.lower() for term in blocked_terms)
    ]
