from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import inspect
from json import dumps
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def api():
    return import_module("polymarket_alpha_lab.strategy_information_refresh_policy")


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "refresh_now_close_window_seconds": d("900.000000"),
        "watch_close_window_seconds": d("3600.000000"),
        "source_stale_watch_seconds": d("3600.000000"),
        "source_stale_refresh_now_seconds": d("21600.000000"),
        "critical_source_stale_refresh_now_seconds": d("1800.000000"),
        "watch_probability_movement": d("0.030000"),
        "material_probability_movement": d("0.100000"),
        "team_confidence_watch_threshold": d("0.600000"),
        "team_confidence_refresh_now_threshold": d("0.350000"),
    }
    values.update(overrides)
    return module.StrategyInformationRefreshPolicyConfig(**values)


def signal(market_id: str, **overrides: object):
    module = api()
    values = {
        "market_id": market_id,
        "team_id": "politics",
        "market_close_time": GENERATED_AT + timedelta(days=2),
        "last_source_timestamp": GENERATED_AT - timedelta(seconds=300),
        "source_criticality": "medium",
        "previous_probability": d("0.400000"),
        "current_probability": d("0.410000"),
        "team_confidence": d("0.850000"),
    }
    values.update(overrides)
    return module.StrategyInformationRefreshSignal(**values)


def policy(*signals: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_information_refresh_policy(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_policy_generates_refresh_now_watch_and_no_refresh_decisions() -> None:
    module = api()

    report = policy(
        signal(
            "close-imminent",
            market_close_time=GENERATED_AT + timedelta(seconds=300),
            source_criticality="low",
        ),
        signal(
            "critical-stale",
            last_source_timestamp=GENERATED_AT - timedelta(seconds=2700),
            source_criticality="critical",
            current_probability=d("0.400000"),
        ),
        signal(
            "probability-watch",
            current_probability=d("0.450000"),
            team_confidence=d("0.900000"),
        ),
        signal(
            "confidence-watch",
            current_probability=d("0.405000"),
            team_confidence=d("0.500000"),
        ),
        signal(
            "clean",
            source_criticality="low",
            current_probability=d("0.410000"),
            team_confidence=d("0.900000"),
        ),
    )

    assert type(report) is module.StrategyInformationRefreshPolicyReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "strategy-information-refresh-policy-v0"
    assert report.signal_count == d("5")
    assert report.refresh_now_count == d("2")
    assert report.watch_count == d("2")
    assert report.no_refresh_count == d("1")
    assert report.reason_codes == (
        "market_close_imminent",
        "critical_source_stale",
        "notable_probability_movement",
        "team_confidence_watch",
        "information_refresh_not_needed",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.market_id for row in report.decisions) == (
        "close-imminent",
        "critical-stale",
        "confidence-watch",
        "probability-watch",
        "clean",
    )
    assert tuple(row.decision for row in report.decisions) == (
        "refresh_now",
        "refresh_now",
        "watch",
        "watch",
        "no_refresh",
    )
    assert report.decisions[0].reason_codes == ("market_close_imminent",)
    assert report.decisions[0].time_to_close_seconds == d("300.000000")
    assert report.decisions[1].reason_codes == ("critical_source_stale",)
    assert report.decisions[1].source_age_seconds == d("2700.000000")
    assert report.decisions[2].reason_codes == ("team_confidence_watch",)
    assert report.decisions[3].reason_codes == ("notable_probability_movement",)
    assert report.decisions[3].probability_movement == d("0.050000")
    assert report.decisions[4].reason_codes == ("information_refresh_not_needed",)


def test_policy_handles_missing_source_and_timezone_aware_inputs() -> None:
    eastern = timezone(timedelta(hours=-4))

    report = policy(
        signal(
            "missing-source",
            last_source_timestamp=None,
            source_criticality="high",
            current_probability=d("0.400000"),
        ),
        signal(
            "offset-times",
            market_close_time=datetime(2026, 7, 2, 9, 15, tzinfo=eastern),
            last_source_timestamp=datetime(2026, 7, 2, 7, 55, tzinfo=eastern),
            source_criticality="low",
            current_probability=d("0.400000"),
            team_confidence=d("0.950000"),
        ),
        cfg=config(watch_close_window_seconds=d("7200.000000")),
    )

    assert tuple(row.market_id for row in report.decisions) == (
        "missing-source",
        "offset-times",
    )
    assert report.decisions[0].decision == "refresh_now"
    assert report.decisions[0].reason_codes == ("source_timestamp_missing",)
    assert report.decisions[0].source_age_seconds is None
    assert report.decisions[1].decision == "watch"
    assert report.decisions[1].reason_codes == ("market_close_approaching",)
    assert report.decisions[1].market_close_time == datetime(
        2026,
        7,
        2,
        13,
        15,
        tzinfo=UTC,
    )
    assert report.decisions[1].last_source_timestamp == datetime(
        2026,
        7,
        2,
        11,
        55,
        tzinfo=UTC,
    )
    assert report.decisions[1].time_to_close_seconds == d("4500.000000")
    assert report.decisions[1].source_age_seconds == d("300.000000")


def test_payload_is_json_ready_and_omits_network_storage_trading_surfaces() -> None:
    payload = api().strategy_information_refresh_policy_payload(
        policy(
            signal(
                "payload-market",
                last_source_timestamp=None,
                current_probability=d("0.400000"),
            ),
        ),
    )

    payload_text = repr(payload).lower()
    for forbidden in (
        "market_slug",
        "question",
        "payload_json",
        "wallet",
        "account",
        "order",
        "trade",
        "advice",
        "auth",
        "broker",
        "investment",
    ):
        assert forbidden not in payload_text
    assert payload["signal_count"] == "1"
    assert payload["refresh_now_count"] == "1"
    assert payload["decisions"][0]["decision"] == "refresh_now"
    assert payload["decisions"][0]["reason_codes"] == ["source_timestamp_missing"]
    assert _float_paths(payload) == ()
    dumps(payload, sort_keys=True)


def test_dataclasses_are_frozen_strict_and_validate_inputs() -> None:
    module = api()
    source_signal = signal("strict")
    report = policy(source_signal)

    assert module.__all__ == (
        "DEFAULT_STRATEGY_INFORMATION_REFRESH_POLICY_CONFIG_VERSION",
        "StrategyInformationRefreshPolicyConfig",
        "StrategyInformationRefreshPolicyDecision",
        "StrategyInformationRefreshPolicyReport",
        "StrategyInformationRefreshSignal",
        "build_strategy_information_refresh_policy",
        "strategy_information_refresh_policy_payload",
    )

    with pytest.raises(FrozenInstanceError):
        source_signal.market_id = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(source_signal, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)
    with pytest.raises(ValueError, match="Decimal"):
        signal("float-probability", previous_probability=0.4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_criticality"):
        signal("bad-criticality", source_criticality="urgent")
    with pytest.raises(ValueError, match="timezone-aware"):
        signal("naive-close", market_close_time=datetime(2026, 7, 2, 12, 0))
    with pytest.raises(ValueError, match="at most 1"):
        signal("bad-confidence", team_confidence=d("1.100000"))
    with pytest.raises(ValueError, match="duplicate market_id"):
        policy(source_signal, source_signal)
    with pytest.raises(ValueError, match="decision"):
        replace(report.decisions[0], decision="refresh_now")
    with pytest.raises(ValueError, match="signal_count"):
        replace(report, signal_count=d("2"))


def test_module_scope_has_no_network_storage_order_or_process_surface() -> None:
    source = inspect.getsource(api())
    forbidden_terms = (
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "socket",
        "subprocess",
        "open(",
        "submit_order",
        "cancel_order",
        "place_order",
    )

    for term in forbidden_terms:
        assert term not in source


def _float_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if isinstance(value, float):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
