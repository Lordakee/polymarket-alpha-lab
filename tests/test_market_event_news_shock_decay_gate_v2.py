from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_event_news_shock_decay_gate_v2 import (
    MarketEventNewsShockDecayGateV2Config,
    MarketEventNewsShockDecayGateV2Input,
    MarketEventNewsShockDecayGateV2ReasonCodeCount,
    MarketEventNewsShockDecayGateV2Report,
    build_market_event_news_shock_decay_gate_v2,
    market_event_news_shock_decay_gate_v2_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
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


def config(**overrides: object) -> MarketEventNewsShockDecayGateV2Config:
    values = {
        "config_version": "market-event-news-shock-decay-gate-v2-test",
        "shock_decay_window_seconds": d("3600.000000"),
        "stale_confirmation_seconds": d("7200.000000"),
        "minimum_source_confirmation_count": d("2.000000"),
        "block_shock_decay_score": d("0.120000"),
        "watch_shock_decay_score": d("0.030000"),
        "close_pressure_minutes": d("15.000000"),
    }
    values.update(overrides)
    return MarketEventNewsShockDecayGateV2Config(**values)


def event(
    market_id: str = "market-alpha",
    *,
    event_slug: str = "event-alpha",
    category: str = "politics",
    shock_detected_at: datetime = GENERATED_AT - timedelta(minutes=10),
    latest_confirming_source_at: datetime = GENERATED_AT - timedelta(minutes=8),
    probability_move_since_shock: Decimal = d("0.060000"),
    source_confirmation_count: Decimal = d("3.000000"),
    minutes_to_close: Decimal = d("120.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketEventNewsShockDecayGateV2Input:
    return MarketEventNewsShockDecayGateV2Input(
        market_id=market_id,
        event_slug=event_slug,
        category=category,
        shock_detected_at=shock_detected_at,
        latest_confirming_source_at=latest_confirming_source_at,
        probability_move_since_shock=probability_move_since_shock,
        source_confirmation_count=source_confirmation_count,
        minutes_to_close=minutes_to_close,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *events: object,
    cfg: MarketEventNewsShockDecayGateV2Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketEventNewsShockDecayGateV2Report:
    return build_market_event_news_shock_decay_gate_v2(
        events,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_empty_status_and_zero_decimal_rollups() -> None:
    summary = report()

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == "market-event-news-shock-decay-gate-v2-test"
    assert summary.event_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.stale_shock_count == ZERO
    assert summary.stale_confirmation_count == ZERO
    assert summary.low_confirmation_count == ZERO
    assert summary.max_shock_decay_score == ZERO
    assert summary.report_status == "empty"
    assert summary.rows == ()
    assert summary.reason_code_counts == ()
    assert summary.reason_codes == ("empty_news_shock_decay_inputs",)
    assert summary.derived_validation_digest == (
        ("event_count", "0.000000"),
        ("hard_flags", "paper_only/report_only/readonly"),
        ("reason_code_total", "0.000000"),
        ("row_count", "0.000000"),
        ("status_total", "0.000000"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_rows_gate_by_news_shock_decay_and_sort_deterministically() -> None:
    summary = report(
        event(
            "market-pass",
            event_slug="event-late",
            category="macro",
            shock_detected_at=GENERATED_AT - timedelta(hours=2),
            latest_confirming_source_at=GENERATED_AT - timedelta(minutes=10),
            probability_move_since_shock=d("0.200000"),
            source_confirmation_count=d("5.000000"),
            minutes_to_close=d("240.000000"),
        ),
        event(
            "market-watch",
            event_slug="event-middle",
            category="sports",
            shock_detected_at=GENERATED_AT - timedelta(minutes=40),
            latest_confirming_source_at=GENERATED_AT - timedelta(minutes=35),
            probability_move_since_shock=d("0.120000"),
            source_confirmation_count=d("1.000000"),
            minutes_to_close=d("60.000000"),
        ),
        event(
            "market-block",
            event_slug="event-early",
            category="politics",
            shock_detected_at=GENERATED_AT - timedelta(minutes=5),
            latest_confirming_source_at=GENERATED_AT - timedelta(minutes=4),
            probability_move_since_shock=d("0.180000"),
            source_confirmation_count=d("3.000000"),
            minutes_to_close=d("120.000000"),
        ),
        cfg=config(stale_confirmation_seconds=d("1800.000000")),
    )

    assert summary.event_count == d("3.000000")
    assert summary.block_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.stale_shock_count == d("1.000000")
    assert summary.stale_confirmation_count == d("1.000000")
    assert summary.low_confirmation_count == d("1.000000")
    assert summary.max_shock_decay_score == d("0.165000")
    assert summary.report_status == "block"

    assert tuple(row.market_id for row in summary.rows) == (
        "market-block",
        "market-watch",
        "market-pass",
    )

    blocked, watched, passed = summary.rows
    assert blocked.status == "block"
    assert blocked.shock_age_seconds == d("300.000000")
    assert blocked.confirmation_age_seconds == d("240.000000")
    assert blocked.shock_decay_score == d("0.165000")
    assert blocked.reason_codes == ("fresh_news_shock_block",)

    assert watched.status == "watch"
    assert watched.shock_age_seconds == d("2400.000000")
    assert watched.confirmation_age_seconds == d("2100.000000")
    assert watched.shock_decay_score == d("0.040000")
    assert watched.reason_codes == (
        "active_news_shock_watch",
        "stale_confirmation_source",
        "low_confirmation_count",
    )

    assert passed.status == "pass"
    assert passed.shock_age_seconds == d("7200.000000")
    assert passed.confirmation_age_seconds == d("600.000000")
    assert passed.shock_decay_score == ZERO
    assert passed.reason_codes == (
        "stale_news_shock",
        "news_shock_decay_passed",
    )


def test_reason_rollups_and_derived_validation_digest_are_deterministic() -> None:
    summary = report(
        event(
            "market-block",
            shock_detected_at=GENERATED_AT - timedelta(minutes=5),
            latest_confirming_source_at=GENERATED_AT - timedelta(minutes=4),
            probability_move_since_shock=d("0.180000"),
        ),
        event(
            "market-watch",
            shock_detected_at=GENERATED_AT - timedelta(minutes=40),
            latest_confirming_source_at=GENERATED_AT - timedelta(minutes=35),
            probability_move_since_shock=d("0.120000"),
            source_confirmation_count=d("1.000000"),
        ),
        event(
            "market-pass",
            shock_detected_at=GENERATED_AT - timedelta(hours=2),
            latest_confirming_source_at=GENERATED_AT - timedelta(minutes=10),
            probability_move_since_shock=d("0.200000"),
            source_confirmation_count=d("5.000000"),
        ),
        cfg=config(stale_confirmation_seconds=d("1800.000000")),
    )

    assert summary.reason_codes == (
        "fresh_news_shock_block",
        "active_news_shock_watch",
        "stale_confirmation_source",
        "low_confirmation_count",
        "stale_news_shock",
        "news_shock_decay_passed",
    )
    assert summary.reason_code_counts == (
        MarketEventNewsShockDecayGateV2ReasonCodeCount(
            reason_code="fresh_news_shock_block",
            count=d("1.000000"),
        ),
        MarketEventNewsShockDecayGateV2ReasonCodeCount(
            reason_code="active_news_shock_watch",
            count=d("1.000000"),
        ),
        MarketEventNewsShockDecayGateV2ReasonCodeCount(
            reason_code="stale_confirmation_source",
            count=d("1.000000"),
        ),
        MarketEventNewsShockDecayGateV2ReasonCodeCount(
            reason_code="low_confirmation_count",
            count=d("1.000000"),
        ),
        MarketEventNewsShockDecayGateV2ReasonCodeCount(
            reason_code="stale_news_shock",
            count=d("1.000000"),
        ),
        MarketEventNewsShockDecayGateV2ReasonCodeCount(
            reason_code="news_shock_decay_passed",
            count=d("1.000000"),
        ),
    )
    assert summary.derived_validation_digest == (
        ("block_count", "1.000000"),
        ("event_count", "3.000000"),
        ("hard_flags", "paper_only/report_only/readonly"),
        ("low_confirmation_count", "1.000000"),
        ("max_shock_decay_score", "0.165000"),
        ("pass_count", "1.000000"),
        ("reason_code_total", "6.000000"),
        ("row_count", "3.000000"),
        ("stale_confirmation_count", "1.000000"),
        ("stale_shock_count", "1.000000"),
        ("status_total", "3.000000"),
        ("watch_count", "1.000000"),
    )


def test_payload_uses_decimal_strings_digest_and_no_float_values() -> None:
    summary = report(
        event(
            "market-block",
            shock_detected_at=GENERATED_AT - timedelta(minutes=5),
            latest_confirming_source_at=GENERATED_AT - timedelta(minutes=4),
            probability_move_since_shock=d("0.180000"),
        ),
        event(
            "market-pass",
            shock_detected_at=GENERATED_AT - timedelta(hours=2),
            latest_confirming_source_at=GENERATED_AT - timedelta(minutes=10),
            probability_move_since_shock=d("0.200000"),
            source_confirmation_count=d("5.000000"),
        ),
    )

    payload = market_event_news_shock_decay_gate_v2_payload(summary)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["event_count"] == "2.000000"
    assert payload["max_shock_decay_score"] == "0.165000"
    assert payload["rows"][0]["shock_age_seconds"] == "300.000000"
    assert payload["rows"][0]["shock_decay_score"] == "0.165000"
    assert payload["derived_validation_digest"][0] == [
        "block_count",
        "1.000000",
    ]
    assert '"2.000000"' in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))

    for unsafe_payload in (
        payload | {"live_mode": True},
        payload | {"operator_auth_token": "redacted"},
        payload | {"wallet_id": "0xabc"},
        payload | {"network_endpoint": "http://example.test"},
        payload | {"database_row_id": "db-1"},
        payload | {"rows": [payload["rows"][0] | {"note": "place live order"}]},
    ):
        with pytest.raises(ValueError, match="unsafe"):
            market_event_news_shock_decay_gate_v2_payload(unsafe_payload)


def test_validation_rejects_bad_types_times_flags_and_report_inconsistency() -> None:
    with pytest.raises(ValueError, match="shock_decay_window_seconds"):
        config(shock_decay_window_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="shock_decay_window_seconds"):
        config(shock_decay_window_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="probability_move_since_shock"):
        event(probability_move_since_shock=d("-0.010000"))
    with pytest.raises(ValueError, match="source_confirmation_count"):
        event(source_confirmation_count=d("1.500000"))
    with pytest.raises(ValueError, match="minutes_to_close"):
        event(minutes_to_close=d("-1.000000"))
    with pytest.raises(ValueError, match="shock_detected_at"):
        event(shock_detected_at=datetime(2026, 7, 7, 15, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(event(), generated_at=_DatetimeSubclass(2026, 7, 7, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone-aware"):
        report(
            event(),
            generated_at=datetime(2026, 7, 7, 16, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="at or after shock_detected_at"):
        event(
            shock_detected_at=GENERATED_AT - timedelta(minutes=5),
            latest_confirming_source_at=GENERATED_AT - timedelta(minutes=6),
        )
    with pytest.raises(ValueError, match="at or before generated_at"):
        report(
            event(
                shock_detected_at=GENERATED_AT + timedelta(seconds=1),
                latest_confirming_source_at=GENERATED_AT + timedelta(seconds=2),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        report(event(paper_only=False))
    with pytest.raises(ValueError, match="report_only"):
        report(event(report_only=False))
    with pytest.raises(ValueError, match="readonly"):
        report(event(readonly=False))

    summary = report(event("market-alpha"), event("market-beta"))
    with pytest.raises(FrozenInstanceError):
        summary.report_status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="event_count"):
        replace(summary, event_count=d("3.000000"))
    with pytest.raises(ValueError, match="report_status"):
        replace(summary, report_status="block")


def test_static_module_has_no_live_io_float_literals_or_sensitive_surface() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_event_news_shock_decay_gate_v2.py",
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "http",
        "socket",
        "web3",
        "psycopg",
        "sqlite",
        "subprocess",
        "open(",
        "write(",
        "read(",
        "private_key",
        "account",
        "balance",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
