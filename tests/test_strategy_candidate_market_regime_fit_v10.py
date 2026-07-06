from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_market_regime_fit_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-candidate-market-regime-fit-v10",
        "fit_threshold": d("0.750000"),
        "watch_threshold": d("0.500000"),
        "fresh_source_update_cadence_minutes": d("60.000000"),
        "stale_source_update_cadence_minutes": d("360.000000"),
        "volatility_weight": d("0.200000"),
        "liquidity_weight": d("0.200000"),
        "source_cadence_weight": d("0.200000"),
        "anti_crowding_weight": d("0.200000"),
        "specialist_confidence_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.StrategyCandidateMarketRegimeFitConfig(**values)


def candidate(candidate_id: str = "candidate-alpha", **overrides: object):
    module = api()
    values = {
        "candidate_id": candidate_id,
        "market_slug": f"{candidate_id}-market",
        "market_question": f"Will {candidate_id} resolve yes?",
        "category": "macro",
        "volatility_regime": "normal",
        "liquidity_regime": "deep",
        "source_update_cadence_minutes": d("30.000000"),
        "crowding_score": d("0.100000"),
        "specialist_confidence": d("0.880000"),
        "reason_codes": ("candidate_screened",),
    }
    values.update(overrides)
    return module.StrategyCandidateMarketRegimeFitCandidate(**values)


def report(*candidates_: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_candidate_market_regime_fit_v10(
        candidates_,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk(value: object):
    if isinstance(value, dict):
        for nested in value.values():
            yield nested
            yield from walk(nested)
    elif isinstance(value, list):
        for nested in value:
            yield nested
            yield from walk(nested)


def test_regime_fit_scores_and_orders_candidate_rows() -> None:
    result = report(
        candidate("fit"),
        candidate(
            "watch",
            volatility_regime="elevated",
            liquidity_regime="adequate",
            source_update_cadence_minutes=d("180.000000"),
            crowding_score=d("0.450000"),
            specialist_confidence=d("0.620000"),
        ),
        candidate(
            "blocked",
            volatility_regime="stressed",
            liquidity_regime="thin",
            source_update_cadence_minutes=d("720.000000"),
            crowding_score=d("0.850000"),
            specialist_confidence=d("0.300000"),
        ),
    )

    assert result.generated_at == GENERATED_AT
    assert result.config_version == "strategy-candidate-market-regime-fit-v10"
    assert result.candidate_count == d("3")
    assert result.fit_count == d("1")
    assert result.watch_count == d("1")
    assert result.blocked_count == d("1")
    assert result.average_regime_fit_score == d("0.576667")
    assert result.top_regime_fit_score == d("0.916000")
    assert result.status == "blocked"
    assert result.reason_codes == (
        "market_regime_fit_blocked",
        "market_regime_fit_passed",
        "market_regime_fit_watch",
        "market_regime_fit_blocked_row",
        "source_cadence_stale",
        "crowding_elevated",
        "specialist_confidence_low",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.candidate_id for row in result.rows) == ("fit", "watch", "blocked")
    fit, watched, blocked = result.rows
    assert fit.regime_fit_score == d("0.916000")
    assert fit.fit_status == "fit"
    assert fit.reason_codes == ("market_regime_fit_passed",)
    assert watched.regime_fit_score == d("0.614000")
    assert watched.source_update_cadence_score == d("0.600000")
    assert watched.fit_status == "watch"
    assert watched.reason_codes == ("market_regime_fit_watch",)
    assert blocked.regime_fit_score == d("0.200000")
    assert blocked.source_update_cadence_score == d("0.000000")
    assert blocked.anti_crowding_score == d("0.150000")
    assert blocked.fit_status == "blocked"
    assert blocked.reason_codes == (
        "market_regime_fit_blocked_row",
        "source_cadence_stale",
        "crowding_elevated",
        "specialist_confidence_low",
    )


def test_empty_report_is_readonly_and_decimal_zeroes() -> None:
    result = report()

    assert result.candidate_count == d("0")
    assert result.fit_count == d("0")
    assert result.watch_count == d("0")
    assert result.blocked_count == d("0")
    assert result.average_regime_fit_score == d("0.000000")
    assert result.top_regime_fit_score == d("0.000000")
    assert result.status == "watch"
    assert result.reason_codes == ("market_regime_fit_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_validation_rejects_non_decimal_inputs_bad_datetimes_and_false_flags() -> None:
    module = api()
    result = report(candidate())

    with pytest.raises(FrozenInstanceError):
        result.rows[0].regime_fit_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_update_cadence_minutes must be a Decimal"):
        candidate(source_update_cadence_minutes=30)
    with pytest.raises(ValueError, match="crowding_score must be a Decimal"):
        candidate(crowding_score=0.1)
    with pytest.raises(ValueError, match="specialist_confidence must be finite"):
        candidate(specialist_confidence=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(candidate(), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(candidate(), generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=NoneOffsetTz()))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(candidate(), generated_at=DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="reason_codes must match rows"):
        replace(result, reason_codes=("market_regime_fit_tampered",))
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_candidate_market_regime_fit_v10(
            (candidate(),),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_payload_preserves_decimal_strings_utc_and_rejects_unsafe_payloads() -> None:
    module = api()
    result = report(
        candidate(
            source_update_cadence_minutes=d("180.000000"),
            crowding_score=d("0.450000"),
            specialist_confidence=d("0.620000"),
        ),
        generated_at=datetime(2026, 7, 6, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    payload = module.strategy_candidate_market_regime_fit_v10_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00Z"
    assert payload["candidate_count"] == "1.000000"
    assert payload["rows"][0]["source_update_cadence_score"] == "0.600000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is float for value in walk(payload))
    assert not any(type(value) is int for value in walk(payload))
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.strategy_candidate_market_regime_fit_v10_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="unsafe live surface"):
        module.strategy_candidate_market_regime_fit_v10_payload(
            {**payload, "wallet_address": "0xabc"},
        )
    with pytest.raises(ValueError, match="unsafe live surface"):
        module.strategy_candidate_market_regime_fit_v10_payload(
            {**payload, "rows": [{**payload["rows"][0], "reason_codes": ["place_order"]}]},
        )


def test_public_numeric_fields_are_decimal_only() -> None:
    module = api()
    decimal_fields = {
        "StrategyCandidateMarketRegimeFitConfig": {
            "fit_threshold",
            "watch_threshold",
            "fresh_source_update_cadence_minutes",
            "stale_source_update_cadence_minutes",
            "volatility_weight",
            "liquidity_weight",
            "source_cadence_weight",
            "anti_crowding_weight",
            "specialist_confidence_weight",
        },
        "StrategyCandidateMarketRegimeFitCandidate": {
            "source_update_cadence_minutes",
            "crowding_score",
            "specialist_confidence",
        },
        "StrategyCandidateMarketRegimeFitRow": {
            "source_update_cadence_minutes",
            "crowding_score",
            "volatility_regime_score",
            "liquidity_regime_score",
            "source_update_cadence_score",
            "anti_crowding_score",
            "specialist_confidence",
            "regime_fit_score",
        },
        "StrategyCandidateMarketRegimeFitReport": {
            "candidate_count",
            "fit_count",
            "watch_count",
            "blocked_count",
            "average_regime_fit_score",
            "top_regime_fit_score",
        },
    }

    for class_name, field_names in decimal_fields.items():
        annotations = getattr(module, class_name).__annotations__
        for field_name in field_names:
            assert annotations[field_name] == "Decimal"


class NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


class DatetimeSubclass(datetime):
    pass
