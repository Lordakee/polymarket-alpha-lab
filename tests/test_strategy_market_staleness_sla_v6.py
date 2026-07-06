from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.strategy_market_staleness_sla_v6 import (
    StrategyMarketStalenessSlaV6Config,
    StrategyMarketStalenessSlaV6Input,
    StrategyMarketStalenessSlaV6Report,
    StrategyMarketStalenessSlaV6Row,
    build_strategy_market_staleness_sla_v6_report,
    strategy_market_staleness_sla_v6_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyMarketStalenessSlaV6Config:
    values = {
        "config_version": "strategy-market-staleness-sla-v6",
        "imminent_resolution_minutes": d("60.000000"),
        "near_resolution_minutes": d("360.000000"),
        "standard_resolution_minutes": d("1440.000000"),
        "imminent_refresh_minutes": d("5.000000"),
        "near_refresh_minutes": d("15.000000"),
        "standard_refresh_minutes": d("60.000000"),
        "distant_refresh_minutes": d("240.000000"),
        "critical_source_multiplier": d("0.500000"),
        "normal_source_multiplier": d("1.000000"),
        "low_source_multiplier": d("2.000000"),
        "watch_multiple": d("2.000000"),
    }
    values.update(overrides)
    return StrategyMarketStalenessSlaV6Config(**values)


def market(**overrides: object) -> StrategyMarketStalenessSlaV6Input:
    values = {
        "market_slug": "btc-etf-approval",
        "team_id": "crypto_btc",
        "category_id": "finance.crypto.btc",
        "time_to_resolution_minutes": d("45.000000"),
        "source_criticality": "critical",
        "last_refresh_age_minutes": d("1.000000"),
    }
    values.update(overrides)
    return StrategyMarketStalenessSlaV6Input(**values)


def report(
    rows: tuple[object, ...],
    *,
    cfg: StrategyMarketStalenessSlaV6Config | None = None,
    generated_at: datetime = GENERATED_AT,
) -> StrategyMarketStalenessSlaV6Report:
    return build_strategy_market_staleness_sla_v6_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_sla_v6_scores_by_team_category_resolution_criticality_and_age() -> None:
    built = report(
        (
            market(
                market_slug="btc-fresh-critical",
                time_to_resolution_minutes=d("45.000000"),
                source_criticality="critical",
                last_refresh_age_minutes=d("1.000000"),
            ),
            market(
                market_slug="rates-watch-normal",
                team_id="macro_rates",
                category_id="finance.macro.rates",
                time_to_resolution_minutes=d("300.000000"),
                source_criticality="normal",
                last_refresh_age_minutes=d("20.000000"),
            ),
            market(
                market_slug="soccer-blocked-low",
                team_id="sports_soccer",
                category_id="sports.soccer",
                time_to_resolution_minutes=d("2000.000000"),
                source_criticality="low",
                last_refresh_age_minutes=d("1000.000000"),
            ),
        ),
    )

    assert built.generated_at == GENERATED_AT
    assert built.config_version == "strategy-market-staleness-sla-v6"
    assert built.market_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.blocked_count == d("1.000000")
    assert built.report_status == "blocked"
    assert built.reason_codes == (
        "critical_source",
        "last_refresh_blocked",
        "last_refresh_watch",
        "low_source",
        "normal_source",
        "refresh_within_sla",
        "resolution_distant",
        "resolution_imminent",
        "resolution_near",
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True

    blocked, watched, passed = built.rows
    assert blocked.market_slug == "soccer-blocked-low"
    assert blocked.team_id == "sports_soccer"
    assert blocked.category_id == "sports.soccer"
    assert blocked.time_to_resolution_minutes == d("2000.000000")
    assert blocked.source_criticality == "low"
    assert blocked.last_refresh_age_minutes == d("1000.000000")
    assert blocked.sla_refresh_minutes == d("480.000000")
    assert blocked.sla_status == "blocked"
    assert blocked.next_refresh_minutes == ZERO
    assert blocked.reason_codes == (
        "last_refresh_blocked",
        "low_source",
        "resolution_distant",
    )

    assert watched.market_slug == "rates-watch-normal"
    assert watched.sla_refresh_minutes == d("15.000000")
    assert watched.sla_status == "watch"
    assert watched.next_refresh_minutes == ZERO
    assert watched.reason_codes == (
        "last_refresh_watch",
        "normal_source",
        "resolution_near",
    )

    assert passed.market_slug == "btc-fresh-critical"
    assert passed.sla_refresh_minutes == d("2.500000")
    assert passed.sla_status == "pass"
    assert passed.next_refresh_minutes == d("1.500000")
    assert passed.reason_codes == (
        "critical_source",
        "refresh_within_sla",
        "resolution_imminent",
    )


def test_sla_v6_payload_is_json_ready_and_decimal_only() -> None:
    built = report((market(),))
    payload = strategy_market_staleness_sla_v6_report_payload(built)

    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["market_count"] == "1.000000"
    assert payload["rows"][0]["sla_refresh_minutes"] == "2.500000"
    assert payload["rows"][0]["next_refresh_minutes"] == "1.500000"
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


def test_sla_v6_empty_report_is_readonly_pass_with_reason_code() -> None:
    built = report(())

    assert built.report_status == "pass"
    assert built.market_count == ZERO
    assert built.pass_count == ZERO
    assert built.watch_count == ZERO
    assert built.blocked_count == ZERO
    assert built.rows == ()
    assert built.reason_codes == ("market_staleness_sla_empty",)


def test_sla_v6_validates_decimal_utc_taxonomy_flags_and_consistency() -> None:
    built = report((market(),))

    with pytest.raises(FrozenInstanceError):
        built.rows[0].sla_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="last_refresh_age_minutes must be a Decimal"):
        market(last_refresh_age_minutes=1)
    with pytest.raises(ValueError, match="time_to_resolution_minutes must use six decimal places"):
        market(time_to_resolution_minutes=d("1.0000001"))
    with pytest.raises(ValueError, match="imminent_refresh_minutes must be a Decimal"):
        config(imminent_refresh_minutes=DecimalSubclass("5.000000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware UTC"):
        report((market(),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware UTC"):
        report(
            (market(),),
            generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        )
    with pytest.raises(ValueError, match="category_id must match team_id"):
        market(team_id="crypto_btc", category_id="finance.crypto.eth")
    with pytest.raises(ValueError, match="source_criticality must be one of"):
        market(source_criticality="exchange")
    with pytest.raises(ValueError, match="paper_only must be True"):
        market(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(built, readonly=False)
    with pytest.raises(ValueError, match="market_count must match rows"):
        replace(built, market_count=d("2.000000"))


def test_sla_v6_rejects_unsafe_live_surface_fields_on_supplied_shapes() -> None:
    @dataclass(frozen=True)
    class SuppliedShape:
        market_slug: str = "shape-market"
        team_id: str = "crypto_eth"
        category_id: str = "finance.crypto.eth"
        time_to_resolution_minutes: Decimal = d("90.000000")
        source_criticality: str = "normal"
        last_refresh_age_minutes: Decimal = d("14.000000")
        order_id: str = "must-not-surface"
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    with pytest.raises(ValueError, match="unsafe live surface field"):
        report((SuppliedShape(),))


def test_manual_sla_v6_row_and_report_consistency_validation() -> None:
    row = StrategyMarketStalenessSlaV6Row(
        market_slug="manual-market",
        team_id="commodities_gold",
        category_id="finance.commodities.gold",
        time_to_resolution_minutes=d("120.000000"),
        source_criticality="normal",
        last_refresh_age_minutes=d("16.000000"),
        sla_refresh_minutes=d("15.000000"),
        sla_status="watch",
        next_refresh_minutes=ZERO,
        reason_codes=(
            "last_refresh_watch",
            "normal_source",
            "resolution_near",
        ),
    )

    assert row.paper_only is True
    with pytest.raises(ValueError, match="next_refresh_minutes must be zero"):
        replace(row, next_refresh_minutes=d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes must match row state"):
        replace(row, reason_codes=("normal_source", "resolution_near"))
    with pytest.raises(ValueError, match="watch_count must match rows"):
        StrategyMarketStalenessSlaV6Report(
            generated_at=GENERATED_AT,
            config_version="strategy-market-staleness-sla-v6",
            market_count=d("1.000000"),
            pass_count=ZERO,
            watch_count=ZERO,
            blocked_count=ZERO,
            report_status="watch",
            reason_codes=row.reason_codes,
            rows=(row,),
        )
