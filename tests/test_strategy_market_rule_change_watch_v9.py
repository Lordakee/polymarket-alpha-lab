from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.strategy_market_rule_change_watch_v9 import (
    StrategyMarketRuleChangeWatchV9Config,
    StrategyMarketRuleChangeWatchV9Input,
    StrategyMarketRuleChangeWatchV9Report,
    StrategyMarketRuleChangeWatchV9Row,
    build_strategy_market_rule_change_watch_v9_report,
    strategy_market_rule_change_watch_v9_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
BASE_CLOSE_TIME = datetime(2026, 8, 1, 20, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyMarketRuleChangeWatchV9Config:
    values = {
        "config_version": "strategy-market-rule-change-watch-v9",
        "material_close_time_change_seconds": d("0.000000"),
    }
    values.update(overrides)
    return StrategyMarketRuleChangeWatchV9Config(**values)


def market(**overrides: object) -> StrategyMarketRuleChangeWatchV9Input:
    values = {
        "market_slug": "btc-etf-approval",
        "previous_resolution_rules": "Resolves Yes if the SEC approves a spot BTC ETF.",
        "current_resolution_rules": "Resolves Yes if the SEC approves a spot BTC ETF.",
        "previous_market_description": "Tracks spot BTC ETF approval before the deadline.",
        "current_market_description": "Tracks spot BTC ETF approval before the deadline.",
        "previous_best_source_tier": "official_rules",
        "current_best_source_tier": "official_rules",
        "previous_close_time": BASE_CLOSE_TIME,
        "current_close_time": BASE_CLOSE_TIME,
        "previous_dispute_indicators": (),
        "current_dispute_indicators": (),
    }
    values.update(overrides)
    return StrategyMarketRuleChangeWatchV9Input(**values)


def report(
    rows: tuple[object, ...],
    *,
    cfg: StrategyMarketRuleChangeWatchV9Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyMarketRuleChangeWatchV9Report:
    return build_strategy_market_rule_change_watch_v9_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_v9_tracks_rule_description_source_close_time_and_dispute_changes() -> None:
    built = report(
        (
            market(market_slug="unchanged-market"),
            market(
                market_slug="description-source-watch",
                previous_market_description="Tracks final certification on the agency page.",
                current_market_description="Tracks final certification plus published addenda.",
                previous_best_source_tier="secondary_news",
                current_best_source_tier="official_rules",
            ),
            market(
                market_slug="rules-close-dispute-blocked",
                previous_resolution_rules="Resolves Yes if the bill is signed by close.",
                current_resolution_rules="Resolves Yes only if the signed bill is published by close.",
                previous_market_description="Tracks bill signature timing.",
                current_market_description="Tracks publication timing for the signed bill.",
                previous_best_source_tier="official_rules",
                current_best_source_tier="secondary_news",
                current_close_time=BASE_CLOSE_TIME - timedelta(hours=1),
                current_dispute_indicators=("ambiguous-settlement-language",),
            ),
        ),
    )

    assert built.generated_at == GENERATED_AT
    assert built.config_version == "strategy-market-rule-change-watch-v9"
    assert built.market_count == d("3.000000")
    assert built.unchanged_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.blocked_count == d("1.000000")
    assert built.rule_change_status == "blocked"
    assert built.required_research_action == "escalate_rule_change_review"
    assert built.reason_codes == (
        "close_time_changed",
        "close_time_moved_earlier",
        "dispute_indicators_added",
        "dispute_indicators_changed",
        "market_description_changed",
        "market_rule_change_watch_unchanged",
        "resolution_rules_changed",
        "source_hierarchy_changed",
        "source_hierarchy_strengthened",
        "source_hierarchy_weakened",
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    blocked, watched, unchanged = built.rows
    assert blocked.market_slug == "rules-close-dispute-blocked"
    assert blocked.resolution_rules_changed is True
    assert blocked.market_description_changed is True
    assert blocked.source_hierarchy_changed is True
    assert blocked.close_time_changed is True
    assert blocked.dispute_indicators_changed is True
    assert blocked.close_time_delta_seconds == d("-3600.000000")
    assert blocked.change_signal_count == d("5.000000")
    assert blocked.rule_change_status == "blocked"
    assert blocked.required_research_action == "escalate_rule_change_review"
    assert blocked.reason_codes == (
        "close_time_changed",
        "close_time_moved_earlier",
        "dispute_indicators_added",
        "dispute_indicators_changed",
        "market_description_changed",
        "resolution_rules_changed",
        "source_hierarchy_changed",
        "source_hierarchy_weakened",
    )

    assert watched.market_slug == "description-source-watch"
    assert watched.rule_change_status == "watch"
    assert watched.required_research_action == "refresh_market_rule_research"
    assert watched.close_time_delta_seconds == ZERO
    assert watched.change_signal_count == d("2.000000")
    assert watched.reason_codes == (
        "market_description_changed",
        "source_hierarchy_changed",
        "source_hierarchy_strengthened",
    )

    assert unchanged.market_slug == "unchanged-market"
    assert unchanged.rule_change_status == "unchanged"
    assert unchanged.required_research_action == "no_action"
    assert unchanged.change_signal_count == ZERO
    assert unchanged.reason_codes == ("market_rule_change_watch_unchanged",)


def test_v9_payload_is_json_ready_and_decimal_only() -> None:
    built = report(
        (
            market(
                current_close_time=BASE_CLOSE_TIME + timedelta(minutes=30),
                current_dispute_indicators=("source-contradiction",),
            ),
        ),
    )
    payload = strategy_market_rule_change_watch_v9_report_payload(built)

    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["market_count"] == "1.000000"
    assert payload["blocked_count"] == "1.000000"
    assert payload["rule_change_status"] == "blocked"
    assert payload["rows"][0]["close_time_delta_seconds"] == "1800.000000"
    assert payload["rows"][0]["change_signal_count"] == "2.000000"
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


def test_v9_empty_report_is_readonly_unchanged_with_reason_code() -> None:
    built = report(())

    assert built.rule_change_status == "unchanged"
    assert built.required_research_action == "no_action"
    assert built.market_count == ZERO
    assert built.unchanged_count == ZERO
    assert built.watch_count == ZERO
    assert built.blocked_count == ZERO
    assert built.rows == ()
    assert built.reason_codes == ("market_rule_change_watch_empty",)


def test_v9_validates_decimal_utc_source_tiers_flags_and_consistency() -> None:
    built = report((market(),))

    with pytest.raises(FrozenInstanceError):
        built.rows[0].rule_change_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="material_close_time_change_seconds must be a Decimal"):
        config(material_close_time_change_seconds=1)
    with pytest.raises(ValueError, match="material_close_time_change_seconds must be a Decimal"):
        config(material_close_time_change_seconds=DecimalSubclass("0.000000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware UTC"):
        report((market(),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="current_close_time must be timezone-aware UTC"):
        market(current_close_time=datetime(2026, 8, 1, 13, 0, tzinfo=timezone(timedelta(hours=-7))))
    with pytest.raises(ValueError, match="current_best_source_tier must be a known source tier"):
        market(current_best_source_tier="private-chat")
    with pytest.raises(ValueError, match="paper_only must be True"):
        market(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="market_count must match rows"):
        replace(built, market_count=d("2.000000"))


def test_v9_rejects_unsafe_live_surface_fields_on_supplied_shapes() -> None:
    @dataclass(frozen=True)
    class SuppliedShape:
        market_slug: str = "shape-market"
        previous_resolution_rules: str = "Old rules."
        current_resolution_rules: str = "Old rules."
        previous_market_description: str = "Old description."
        current_market_description: str = "Old description."
        previous_best_source_tier: str = "official_rules"
        current_best_source_tier: str = "official_rules"
        previous_close_time: datetime = BASE_CLOSE_TIME
        current_close_time: datetime = BASE_CLOSE_TIME
        previous_dispute_indicators: tuple[str, ...] = ()
        current_dispute_indicators: tuple[str, ...] = ()
        order_id: str = "must-not-surface"
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    with pytest.raises(ValueError, match="unsafe live surface field"):
        report((SuppliedShape(),))


def test_manual_v9_row_and_report_consistency_validation() -> None:
    row = StrategyMarketRuleChangeWatchV9Row(
        market_slug="manual-market",
        previous_resolution_rules="Old rules.",
        current_resolution_rules="New rules.",
        previous_market_description="Old description.",
        current_market_description="Old description.",
        previous_best_source_tier="official_rules",
        current_best_source_tier="official_rules",
        previous_close_time=BASE_CLOSE_TIME,
        current_close_time=BASE_CLOSE_TIME,
        previous_dispute_indicators=(),
        current_dispute_indicators=(),
        resolution_rules_changed=True,
        market_description_changed=False,
        source_hierarchy_changed=False,
        close_time_changed=False,
        dispute_indicators_changed=False,
        close_time_delta_seconds=ZERO,
        change_signal_count=d("1.000000"),
        rule_change_status="blocked",
        required_research_action="escalate_rule_change_review",
        reason_codes=("resolution_rules_changed",),
    )

    assert row.paper_only is True
    with pytest.raises(ValueError, match="rule_change_status must match reason_codes"):
        replace(row, rule_change_status="watch")
    with pytest.raises(ValueError, match="change_signal_count must match changed fields"):
        replace(row, change_signal_count=d("2.000000"))
    with pytest.raises(ValueError, match="blocked_count must match rows"):
        StrategyMarketRuleChangeWatchV9Report(
            generated_at=GENERATED_AT,
            config_version="strategy-market-rule-change-watch-v9",
            market_count=d("1.000000"),
            unchanged_count=ZERO,
            watch_count=ZERO,
            blocked_count=ZERO,
            rule_change_status="blocked",
            required_research_action="escalate_rule_change_review",
            reason_codes=row.reason_codes,
            rows=(row,),
        )
