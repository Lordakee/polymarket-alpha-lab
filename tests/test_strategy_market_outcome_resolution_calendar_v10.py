from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.strategy_market_outcome_resolution_calendar_v10 import (
    StrategyMarketOutcomeResolutionCalendarV10Config,
    StrategyMarketOutcomeResolutionCalendarV10Input,
    StrategyMarketOutcomeResolutionCalendarV10Result,
    build_strategy_market_outcome_resolution_calendar_v10_result,
    resolve_market_outcome_resolution_calendar_v10,
    strategy_market_outcome_resolution_calendar_v10_payload,
)


CLOSE_TIME = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
EXPECTED_RESOLUTION_TIME = datetime(2026, 7, 6, 13, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyMarketOutcomeResolutionCalendarV10Config:
    values = {
        "config_version": "strategy-market-outcome-resolution-calendar-v10",
        "ready_expected_wait_minutes": d("180.000000"),
        "watch_expected_wait_minutes": d("1440.000000"),
        "manual_check_lead_minutes": d("30.000000"),
        "medium_timezone_risk_minutes": d("60.000000"),
        "high_timezone_risk_minutes": d("180.000000"),
        "weekend_or_holiday_risk_minutes": d("1440.000000"),
    }
    values.update(overrides)
    return StrategyMarketOutcomeResolutionCalendarV10Config(**values)


def input_row(**overrides: object) -> StrategyMarketOutcomeResolutionCalendarV10Input:
    values = {
        "close_time": CLOSE_TIME,
        "expected_resolution_time": EXPECTED_RESOLUTION_TIME,
        "source_publication_lag_minutes": d("15.000000"),
        "timezone_risk": "low",
        "weekend_or_holiday": False,
        "event_type": "economic_data",
    }
    values.update(overrides)
    return StrategyMarketOutcomeResolutionCalendarV10Input(**values)


def result(
    row: StrategyMarketOutcomeResolutionCalendarV10Input,
    *,
    cfg: StrategyMarketOutcomeResolutionCalendarV10Config | None = None,
) -> StrategyMarketOutcomeResolutionCalendarV10Result:
    return build_strategy_market_outcome_resolution_calendar_v10_result(
        row,
        config=cfg or config(),
    )


def test_resolution_calendar_v10_marks_low_risk_calendar_ready() -> None:
    built = result(input_row())

    assert built.config_version == "strategy-market-outcome-resolution-calendar-v10"
    assert built.close_time == CLOSE_TIME
    assert built.expected_resolution_time == EXPECTED_RESOLUTION_TIME
    assert built.source_publication_lag_minutes == d("15.000000")
    assert built.timezone_risk == "low"
    assert built.weekend_or_holiday is False
    assert built.event_type == "economic_data"
    assert built.resolution_calendar_status == "ready"
    assert built.expected_wait_minutes == d("135.000000")
    assert built.manual_check_deadline_minutes == d("105.000000")
    assert built.reason_codes == (
        "calendar_ready",
        "event_type_economic_data",
        "low_timezone_risk",
        "manual_check_scheduled",
        "source_lag_included",
        "wait_within_ready_threshold",
        "weekday_resolution",
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True
    assert built.payload["expected_wait_minutes"] == "135.000000"


def test_resolution_calendar_v10_marks_medium_timezone_sports_watch() -> None:
    built = result(
        input_row(
            expected_resolution_time=datetime(2026, 7, 6, 15, 0, tzinfo=UTC),
            source_publication_lag_minutes=d("30.000000"),
            timezone_risk="medium",
            event_type="sports",
        ),
    )

    assert built.resolution_calendar_status == "watch"
    assert built.expected_wait_minutes == d("300.000000")
    assert built.manual_check_deadline_minutes == d("270.000000")
    assert built.reason_codes == (
        "calendar_watch",
        "event_type_sports",
        "manual_check_scheduled",
        "medium_timezone_risk",
        "source_lag_included",
        "wait_exceeds_ready_threshold",
        "weekday_resolution",
    )


def test_resolution_calendar_v10_blocks_weekend_holiday_election_lag() -> None:
    built = result(
        input_row(
            expected_resolution_time=datetime(2026, 7, 6, 20, 0, tzinfo=UTC),
            source_publication_lag_minutes=d("30.000000"),
            timezone_risk="high",
            weekend_or_holiday=True,
            event_type="election",
        ),
    )

    assert built.resolution_calendar_status == "blocked"
    assert built.expected_wait_minutes == d("2850.000000")
    assert built.manual_check_deadline_minutes == ZERO
    assert built.reason_codes == (
        "calendar_blocked",
        "event_type_election",
        "high_timezone_risk",
        "manual_check_immediate",
        "source_lag_included",
        "wait_exceeds_watch_threshold",
        "weekend_or_holiday_resolution",
    )


def test_resolution_calendar_v10_direct_resolver_matches_input_dataclass_path() -> None:
    direct = resolve_market_outcome_resolution_calendar_v10(
        close_time=CLOSE_TIME,
        expected_resolution_time=EXPECTED_RESOLUTION_TIME,
        source_publication_lag_minutes=d("15.000000"),
        timezone_risk="low",
        weekend_or_holiday=False,
        event_type="economic_data",
        config=config(),
    )
    built = result(input_row())

    assert direct == built


def test_resolution_calendar_v10_payload_is_json_ready_and_decimal_only() -> None:
    built = result(input_row())
    payload = strategy_market_outcome_resolution_calendar_v10_payload(built)

    json.dumps(payload, sort_keys=True)
    assert payload == built.payload
    assert payload["close_time"] == "2026-07-06T12:00:00+00:00"
    assert payload["expected_resolution_time"] == "2026-07-06T13:00:00+00:00"
    assert payload["source_publication_lag_minutes"] == "15.000000"
    assert payload["expected_wait_minutes"] == "135.000000"
    assert payload["manual_check_deadline_minutes"] == "105.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    def walk(value: object) -> None:
        assert not isinstance(value, float)
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)


def test_resolution_calendar_v10_result_exposes_tamper_evident_digest() -> None:
    built = result(input_row())

    assert type(built.derived_validation_digest) is str
    assert len(built.derived_validation_digest) == 64
    int(built.derived_validation_digest, 16)
    assert built.payload["derived_validation_digest"] == built.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(built, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="payload derived_validation_digest must match"):
        replace(
            built,
            payload={**built.payload, "derived_validation_digest": "0" * 64},
        )


def test_resolution_calendar_v10_public_payload_revalidates_dict_payloads() -> None:
    built = result(input_row())

    assert strategy_market_outcome_resolution_calendar_v10_payload(built.payload) == built.payload

    tampered_wait = {**built.payload, "expected_wait_minutes": "999.000000"}
    with pytest.raises(ValueError, match="expected_wait_minutes must match inputs"):
        strategy_market_outcome_resolution_calendar_v10_payload(tampered_wait)

    missing_digest = dict(built.payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest is required"):
        strategy_market_outcome_resolution_calendar_v10_payload(missing_digest)

    unsafe_key = {**built.payload, "wallet_address": "redacted"}
    with pytest.raises(ValueError, match="unsafe live surface field"):
        strategy_market_outcome_resolution_calendar_v10_payload(unsafe_key)

    unsafe_value = {**built.payload, "public_note": "wallet handoff"}
    with pytest.raises(ValueError, match="unsafe public payload value"):
        strategy_market_outcome_resolution_calendar_v10_payload(unsafe_value)

    downgraded_flags = {**built.payload, "paper_only": False}
    with pytest.raises(ValueError, match="paper_only must be True"):
        strategy_market_outcome_resolution_calendar_v10_payload(downgraded_flags)


def test_resolution_calendar_v10_validates_inputs_flags_and_consistency() -> None:
    built = result(input_row())

    with pytest.raises(FrozenInstanceError):
        built.resolution_calendar_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_publication_lag_minutes must be a Decimal"):
        input_row(source_publication_lag_minutes=1)
    with pytest.raises(ValueError, match="source_publication_lag_minutes must use six decimal places"):
        input_row(source_publication_lag_minutes=d("1.0000001"))
    with pytest.raises(ValueError, match="ready_expected_wait_minutes must be a Decimal"):
        config(ready_expected_wait_minutes=DecimalSubclass("180.000000"))
    with pytest.raises(ValueError, match="close_time must be a datetime"):
        input_row(close_time=DatetimeSubclass(2026, 7, 6, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="expected_resolution_time must be timezone-aware UTC"):
        input_row(expected_resolution_time=datetime(2026, 7, 6, 13, 0))
    with pytest.raises(ValueError, match="expected_resolution_time must not be before close_time"):
        input_row(expected_resolution_time=datetime(2026, 7, 6, 11, 59, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone_risk must be low, medium, or high"):
        input_row(timezone_risk="unknown")
    with pytest.raises(ValueError, match="weekend_or_holiday must be a bool"):
        input_row(weekend_or_holiday=1)
    with pytest.raises(ValueError, match="event_type must be known"):
        input_row(event_type="unmapped")
    with pytest.raises(ValueError, match="paper_only must be True"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="expected_wait_minutes must match payload"):
        replace(
            built,
            payload={**built.payload, "expected_wait_minutes": "999.000000"},
        )
    with pytest.raises(ValueError, match="manual_check_deadline_minutes must match status"):
        replace(built, manual_check_deadline_minutes=d("999.000000"))


def test_resolution_calendar_v10_rejects_unsafe_supplied_shapes() -> None:
    @dataclass(frozen=True)
    class SuppliedShape:
        close_time: datetime = CLOSE_TIME
        expected_resolution_time: datetime = EXPECTED_RESOLUTION_TIME
        source_publication_lag_minutes: Decimal = d("15.000000")
        timezone_risk: str = "low"
        weekend_or_holiday: bool = False
        event_type: str = "economic_data"
        wallet_address: str = "must-not-surface"
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    with pytest.raises(ValueError, match="unsafe live surface field"):
        build_strategy_market_outcome_resolution_calendar_v10_result(
            SuppliedShape(),
            config=config(),
        )


def test_resolution_calendar_v10_manual_result_consistency_validation() -> None:
    built = result(input_row())

    manual = StrategyMarketOutcomeResolutionCalendarV10Result(
        config_version=built.config_version,
        close_time=built.close_time,
        expected_resolution_time=built.expected_resolution_time,
        source_publication_lag_minutes=built.source_publication_lag_minutes,
        timezone_risk=built.timezone_risk,
        weekend_or_holiday=built.weekend_or_holiday,
        event_type=built.event_type,
        resolution_calendar_status=built.resolution_calendar_status,
        expected_wait_minutes=built.expected_wait_minutes,
        manual_check_deadline_minutes=built.manual_check_deadline_minutes,
        reason_codes=built.reason_codes,
        payload=built.payload,
    )

    assert manual == built
    with pytest.raises(ValueError, match="reason_codes must match status"):
        replace(
            manual,
            reason_codes=tuple(
                reason for reason in manual.reason_codes if reason != "calendar_ready"
            ),
        )
    with pytest.raises(ValueError, match="payload reason_codes must match result"):
        replace(manual, payload={**manual.payload, "reason_codes": []})


def test_resolution_calendar_v10_static_forbidden_surface_terms_are_absent() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "strategy_market_outcome_resolution_calendar_v10.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()

    forbidden_terms = (
        "sqlite",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "websocket",
        "wallet",
        "broker",
        "order",
        "signing",
        "auth",
        "private_key",
        "execute_trade",
        "live_trading",
        "investment_advice",
        "financial_advice",
        "open(",
    )
    assert not [term for term in forbidden_terms if term in source]
