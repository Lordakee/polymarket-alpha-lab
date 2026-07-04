from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 4, 17, 40, tzinfo=UTC)
BASE_SCHEDULED_START_AT = datetime(2026, 7, 4, 18, 30, tzinfo=UTC)
CONFIG_VERSION = "market-research-basketball-late-news-minutes-cap-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_basketball_late_news_minutes_cap_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "late_news_seconds_to_start_threshold": d("3600.000000"),
        "minutes_cap_threshold": d("24.000000"),
        "minutes_delta_threshold": d("6.000000"),
        "critical_minutes_delta_threshold": d("10.000000"),
        "confidence_threshold": d("0.700000"),
    }
    values.update(overrides)
    return module.MarketResearchBasketballLateNewsMinutesCapDigestConfig(**values)


def signal(
    condition_id: str = "condition_alpha",
    player_key: str = "player_embiid",
    *,
    league_key: str = "nba",
    team_key: str = "phi",
    source_ref: str = "team_late_note",
    observed_at: datetime = BASE_OBSERVED_AT,
    scheduled_start_at: datetime = BASE_SCHEDULED_START_AT,
    baseline_projected_minutes: Decimal = d("36.000000"),
    capped_minutes: Decimal | None = d("22.000000"),
    news_confidence: Decimal = d("0.850000"),
    cap_active: bool = True,
    signal_config_version: str = "basketball-late-news-minutes-cap-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.MarketResearchBasketballLateNewsMinutesCapDigestSignal(
        condition_id=condition_id,
        league_key=league_key,
        team_key=team_key,
        player_key=player_key,
        source_ref=source_ref,
        observed_at=observed_at,
        scheduled_start_at=scheduled_start_at,
        baseline_projected_minutes=baseline_projected_minutes,
        capped_minutes=capped_minutes,
        news_confidence=news_confidence,
        cap_active=cap_active,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals: object, **overrides: object):
    module = api()
    values: dict[str, object] = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.build_market_research_basketball_late_news_minutes_cap_digest(
        **values,
    )


def walk(value: object) -> tuple[object, ...]:
    children = (value,)
    if isinstance(value, dict):
        for item in value.values():
            children += walk(item)
    if isinstance(value, list):
        for item in value:
            children += walk(item)
    return children


def test_empty_digest_is_report_only_decimal_zeroed_and_clear() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.research_scope == (
        "basketball late news minutes cap research digest only"
    )
    assert report.digest_status == "pass"
    assert report.recommended_next_step == (
        "continue_report_only_basketball_late_news_minutes_cap_monitoring"
    )
    assert report.player_count == d("0")
    assert report.signal_count == d("0")
    assert report.clear_player_count == d("0")
    assert report.watch_player_count == d("0")
    assert report.blocked_player_count == d("0")
    assert report.late_news_player_count == d("0")
    assert report.active_cap_player_count == d("0")
    assert report.low_cap_player_count == d("0")
    assert report.high_minutes_delta_player_count == d("0")
    assert report.high_confidence_player_count == d("0")
    assert report.critical_cap_risk_player_count == d("0")
    assert report.max_minutes_delta is None
    assert report.min_seconds_to_start is None
    assert report.average_news_confidence == d("0.000000")
    assert report.rows == ()
    assert report.reason_code_counts == ()
    assert report.reason_codes == ("basketball_late_news_minutes_cap_empty",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_risk_digest_blocks_late_active_low_cap_minutes_delta() -> None:
    report = build_report(
        signal(
            "condition_beta",
            "player_davis",
            team_key="lal",
            source_ref="team_late_note_old",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            scheduled_start_at=GENERATED_AT + timedelta(minutes=30),
            baseline_projected_minutes=d("36.000000"),
            capped_minutes=d("22.000000"),
            news_confidence=d("0.850000"),
            signal_config_version="basketball-late-news-minutes-cap-feed-v1",
        ),
        signal(
            "condition_alpha",
            "player_tatum",
            team_key="bos",
            source_ref="routine_rotation_note",
            observed_at=GENERATED_AT - timedelta(hours=4),
            scheduled_start_at=GENERATED_AT + timedelta(hours=3),
            baseline_projected_minutes=d("35.000000"),
            capped_minutes=None,
            news_confidence=d("0.000000"),
            cap_active=False,
        ),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "review_report_only_basketball_late_news_minutes_cap_screening"
    )
    assert report.player_count == d("2")
    assert report.signal_count == d("2")
    assert report.clear_player_count == d("1")
    assert report.watch_player_count == d("0")
    assert report.blocked_player_count == d("1")
    assert report.late_news_player_count == d("1")
    assert report.active_cap_player_count == d("1")
    assert report.low_cap_player_count == d("1")
    assert report.high_minutes_delta_player_count == d("1")
    assert report.high_confidence_player_count == d("1")
    assert report.critical_cap_risk_player_count == d("1")
    assert report.max_minutes_delta == d("14.000000")
    assert report.min_seconds_to_start == d("3000.000000")
    assert report.average_news_confidence == d("0.425000")
    assert report.reason_codes == (
        "basketball_late_news_minutes_cap_blocked_present",
        "basketball_late_news_minutes_cap_late_news",
        "basketball_late_news_minutes_cap_active_cap",
        "basketball_late_news_minutes_cap_low_cap",
        "basketball_late_news_minutes_cap_delta_high",
        "basketball_late_news_minutes_cap_confidence_high",
        "basketball_late_news_minutes_cap_critical_risk",
    )
    assert report.signal_config_versions == (
        ("routine_rotation_note", "basketball-late-news-minutes-cap-feed-v0"),
        ("team_late_note_old", "basketball-late-news-minutes-cap-feed-v1"),
    )

    assert tuple((row.player_key, row.team_key) for row in report.rows) == (
        ("player_davis", "lal"),
        ("player_tatum", "bos"),
    )
    risky = report.rows[0]
    assert risky.digest_status == "blocked"
    assert risky.signal_count == d("1")
    assert risky.observed_at_latest == GENERATED_AT - timedelta(minutes=20)
    assert risky.scheduled_start_at == GENERATED_AT + timedelta(minutes=30)
    assert risky.baseline_projected_minutes_max == d("36.000000")
    assert risky.capped_minutes_min == d("22.000000")
    assert risky.minutes_delta == d("14.000000")
    assert risky.seconds_to_start_at_latest_news == d("3000.000000")
    assert risky.news_confidence_max == d("0.850000")
    assert risky.screening_priority_score == d("1.000000")
    assert risky.reason_codes == (
        "basketball_late_news_minutes_cap_late_news",
        "basketball_late_news_minutes_cap_active_cap",
        "basketball_late_news_minutes_cap_low_cap",
        "basketball_late_news_minutes_cap_delta_high",
        "basketball_late_news_minutes_cap_confidence_high",
        "basketball_late_news_minutes_cap_critical_risk",
    )

    clear = report.rows[1]
    assert clear.digest_status == "clear"
    assert clear.capped_minutes_min is None
    assert clear.minutes_delta == d("0.000000")
    assert clear.screening_priority_score == d("0.000000")
    assert clear.reason_codes == ("basketball_late_news_minutes_cap_clear",)


def test_digest_is_deterministic_for_input_order_and_reason_code_counts() -> None:
    alpha = signal(
        "condition_alpha",
        "player_alpha",
        source_ref="alpha_note",
        observed_at=GENERATED_AT - timedelta(minutes=20),
        scheduled_start_at=GENERATED_AT + timedelta(minutes=30),
    )
    beta = signal(
        "condition_beta",
        "player_beta",
        source_ref="beta_note",
        observed_at=GENERATED_AT - timedelta(minutes=20),
        scheduled_start_at=GENERATED_AT + timedelta(minutes=30),
    )

    first = build_report(beta, alpha)
    second = build_report(alpha, beta)

    assert tuple(row.player_key for row in first.rows) == (
        "player_alpha",
        "player_beta",
    )
    assert asdict(first) == asdict(second)
    assert tuple((item.reason_code, item.player_count) for item in first.reason_code_counts) == (
        ("basketball_late_news_minutes_cap_late_news", d("2")),
        ("basketball_late_news_minutes_cap_active_cap", d("2")),
        ("basketball_late_news_minutes_cap_low_cap", d("2")),
        ("basketball_late_news_minutes_cap_delta_high", d("2")),
        ("basketball_late_news_minutes_cap_confidence_high", d("2")),
        ("basketball_late_news_minutes_cap_critical_risk", d("2")),
    )


def test_validation_rejects_bad_values_flags_duplicates_and_manual_drift() -> None:
    module = api()

    with pytest.raises(ValueError, match="baseline_projected_minutes must be a Decimal"):
        signal(baseline_projected_minutes=36)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="news_confidence must be a Decimal"):
        signal(news_confidence=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="capped_minutes must be nonnegative"):
        signal(capped_minutes=d("-1.000000"))
    with pytest.raises(ValueError, match="news_confidence must be at most 1"):
        signal(news_confidence=d("1.000001"))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 4, 17, 40))
    with pytest.raises(ValueError, match="scheduled_start_at must be at or after observed_at"):
        signal(scheduled_start_at=BASE_OBSERVED_AT - timedelta(seconds=1))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(signal(), generated_at=_DatetimeSubclass(2026, 7, 4, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at values must be at or before generated_at"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="condition_id must be a string"):
        signal(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(ValueError, match="contains unsafe source detail"):
        signal(condition_id="market_slug_alpha")
    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        build_report(
            signal("condition_alpha", "player_alpha", source_ref="same_ref"),
            signal("condition_alpha", "player_alpha", source_ref="same_ref"),
        )
    with pytest.raises(ValueError, match="late_news_seconds_to_start_threshold must be a Decimal"):
        config(late_news_seconds_to_start_threshold=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="critical_minutes_delta_threshold"):
        config(
            minutes_delta_threshold=d("10.000000"),
            critical_minutes_delta_threshold=d("6.000000"),
        )

    report = build_report(signal())
    with pytest.raises(ValueError, match="player_count must be a Decimal"):
        replace(report, player_count=1)
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        replace(report, reason_code_counts=())
    with pytest.raises(ValueError, match="minutes_delta must match calculated value"):
        replace(report.rows[0], minutes_delta=d("1.000000"))
    with pytest.raises(ValueError, match="report must be exactly"):
        module.market_research_basketball_late_news_minutes_cap_digest_payload("bad")


def test_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_BASKETBALL_LATE_NEWS_MINUTES_CAP_DIGEST_CONFIG_VERSION",
        "BASKETBALL_LATE_NEWS_MINUTES_CAP_RESEARCH_SCOPE",
        "MarketResearchBasketballLateNewsMinutesCapDigestConfig",
        "MarketResearchBasketballLateNewsMinutesCapDigestSignal",
        "MarketResearchBasketballLateNewsMinutesCapDigestReasonCodeCount",
        "MarketResearchBasketballLateNewsMinutesCapDigestRow",
        "MarketResearchBasketballLateNewsMinutesCapDigestReport",
        "build_market_research_basketball_late_news_minutes_cap_digest",
        "market_research_basketball_late_news_minutes_cap_digest_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen is True

    item = signal()
    with pytest.raises(FrozenInstanceError):
        item.news_confidence = d("0.100000")
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)

    report = build_report(item)
    with pytest.raises(FrozenInstanceError):
        report.digest_status = "pass"
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(report, paper_only=False)


def test_non_default_thresholds_change_screening_status() -> None:
    strict_report = build_report(
        signal(
            "condition_strict",
            "player_strict",
            observed_at=GENERATED_AT - timedelta(minutes=30),
            scheduled_start_at=GENERATED_AT + timedelta(minutes=60),
            baseline_projected_minutes=d("32.000000"),
            capped_minutes=d("28.000000"),
            news_confidence=d("0.600000"),
        ),
        config=config(
            late_news_seconds_to_start_threshold=d("7200.000000"),
            minutes_cap_threshold=d("30.000000"),
            minutes_delta_threshold=d("3.000000"),
            critical_minutes_delta_threshold=d("4.000000"),
            confidence_threshold=d("0.500000"),
        ),
    )

    assert strict_report.digest_status == "blocked"
    assert strict_report.blocked_player_count == d("1")
    assert strict_report.late_news_player_count == d("1")
    assert strict_report.rows[0].minutes_delta == d("4.000000")
    assert strict_report.rows[0].seconds_to_start_at_latest_news == d("5400.000000")
    assert strict_report.rows[0].digest_status == "blocked"
    assert strict_report.rows[0].screening_priority_score == d("1.000000")
    assert strict_report.reason_codes == (
        "basketball_late_news_minutes_cap_blocked_present",
        "basketball_late_news_minutes_cap_late_news",
        "basketball_late_news_minutes_cap_active_cap",
        "basketball_late_news_minutes_cap_low_cap",
        "basketball_late_news_minutes_cap_delta_high",
        "basketball_late_news_minutes_cap_confidence_high",
        "basketball_late_news_minutes_cap_critical_risk",
    )


def test_payload_decimal_strings_utc_datetimes_and_static_no_io_mutation_surface() -> None:
    module = api()
    payload = module.market_research_basketball_late_news_minutes_cap_digest_payload(
        build_report(
            signal(
                "condition_payload",
                "player_payload",
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    13,
                    40,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                scheduled_start_at=datetime(
                    2026,
                    7,
                    4,
                    14,
                    30,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
        ),
    )

    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-04T18:00:00Z"
    assert payload["player_count"] == "1"
    assert payload["max_minutes_delta"] == "14.000000"
    assert payload["rows"][0]["observed_at_latest"] == "2026-07-04T17:40:00Z"
    assert payload["rows"][0]["scheduled_start_at"] == "2026-07-04T18:30:00Z"
    assert payload["rows"][0]["seconds_to_start_at_latest_news"] == "3000.000000"
    assert payload["reason_code_counts"][0]["player_count"] == "1"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(item, float) for item in walk(payload))
    for item in walk(payload):
        if isinstance(item, bool):
            continue
        assert not isinstance(item, int)

    report = build_report(signal())
    for item in (report, report.rows[0], report.reason_code_counts[0]):
        for field in fields(item):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_threshold")
                or field.name.endswith("_minutes")
                or field.name.endswith("_delta")
                or field.name.endswith("_seconds")
                or field.name.endswith("_confidence")
                or field.name.endswith("_score")
            ):
                value = getattr(item, field.name)
                if value is not None:
                    assert type(value) is Decimal

    source_text = Path(
        "src/polymarket_alpha_lab/"
        "market_research_basketball_late_news_minutes_cap_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()
    tree = ast.parse(source_text)
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    forbidden_imports = {
        "pathlib",
        "os",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    assert imported_modules.isdisjoint(forbidden_imports)
    for forbidden in (
        "market_slug",
        "question",
        "payload_json",
        "wallet",
        "broker",
        "order",
        "account",
        "advice",
        "auth",
        "signing",
        "cancel",
        "replace",
        "exchange mutation",
        "private_key",
    ):
        assert forbidden not in lowered
