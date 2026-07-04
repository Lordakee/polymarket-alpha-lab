from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_basketball_injury_report_flip_digest import (
    DEFAULT_MARKET_RESEARCH_BASKETBALL_INJURY_REPORT_FLIP_DIGEST_CONFIG_VERSION,
    BASKETBALL_INJURY_REPORT_FLIP_RESEARCH_SCOPE,
    MarketResearchBasketballInjuryReportFlipDigestConfig,
    MarketResearchBasketballInjuryReportFlipDigestItem,
    MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount,
    MarketResearchBasketballInjuryReportFlipDigestReport,
    MarketResearchBasketballInjuryReportFlipDigestRow,
    build_market_research_basketball_injury_report_flip_digest,
    market_research_basketball_injury_report_flip_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_basketball_injury_report_flip_digest.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def walk(value: object) -> tuple[object, ...]:
    children = (value,)
    if isinstance(value, dict):
        for item in value.values():
            children += walk(item)
    if isinstance(value, list):
        for item in value:
            children += walk(item)
    return children


def config(
    **overrides: object,
) -> MarketResearchBasketballInjuryReportFlipDigestConfig:
    values: dict[str, object] = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_BASKETBALL_INJURY_REPORT_FLIP_DIGEST_CONFIG_VERSION
        ),
        "max_report_age_seconds": d("3600.000000"),
        "min_source_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "material_flip_threshold": d("0.250000"),
        "high_player_impact_threshold": d("0.750000"),
        "min_market_liquidity_score": d("0.550000"),
    }
    values.update(overrides)
    return MarketResearchBasketballInjuryReportFlipDigestConfig(**values)


def flip_item(
    condition_id: str = "condition.nba.lakers.warriors.davis-knee",
    *,
    basketball_event_key: str = "nba.lakers.warriors.game-5",
    league_key: str = "nba",
    team_key: str = "los-angeles-lakers",
    opponent_key: str = "golden-state-warriors",
    player_key: str = "anthony-davis",
    injury_key: str = "left-knee",
    previous_report_status: str = "questionable",
    current_report_status: str = "out",
    public_report_reference: str = "league-injury-report-lakers-warriors",
    observed_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    independent_source_count: Decimal = d("2.000000"),
    previous_availability_probability: Decimal = d("0.650000"),
    current_availability_probability: Decimal = d("0.150000"),
    player_impact_score: Decimal = d("0.900000"),
    market_liquidity_score: Decimal = d("0.800000"),
    item_config_version: str = "basketball-injury-report-flip-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchBasketballInjuryReportFlipDigestItem:
    return MarketResearchBasketballInjuryReportFlipDigestItem(
        condition_id=condition_id,
        basketball_event_key=basketball_event_key,
        league_key=league_key,
        team_key=team_key,
        opponent_key=opponent_key,
        player_key=player_key,
        injury_key=injury_key,
        previous_report_status=previous_report_status,
        current_report_status=current_report_status,
        public_report_reference=public_report_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=20),
        source_count=source_count,
        independent_source_count=independent_source_count,
        previous_availability_probability=previous_availability_probability,
        current_availability_probability=current_availability_probability,
        player_impact_score=player_impact_score,
        market_liquidity_score=market_liquidity_score,
        item_config_version=item_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    items: tuple[MarketResearchBasketballInjuryReportFlipDigestItem, ...],
    *,
    cfg: MarketResearchBasketballInjuryReportFlipDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchBasketballInjuryReportFlipDigestReport:
    return build_market_research_basketball_injury_report_flip_digest(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_digest_reduces_injury_report_flips_sources_freshness_impact_and_liquidity() -> None:
    summary = report(
        (
            flip_item(
                "condition.blocked",
                basketball_event_key="nba.lakers.warriors.game-5",
                observed_at=GENERATED_AT - timedelta(hours=2),
                source_count=d("1.000000"),
                independent_source_count=d("1.000000"),
                previous_availability_probability=d("0.800000"),
                current_availability_probability=d("0.200000"),
                player_impact_score=d("0.920000"),
                market_liquidity_score=d("0.450000"),
            ),
            flip_item(
                "condition.watch",
                basketball_event_key="wnba.liberty.aces.final",
                league_key="wnba",
                team_key="new-york-liberty",
                opponent_key="las-vegas-aces",
                player_key="jonquel-jones",
                injury_key="ankle",
                previous_report_status="available",
                current_report_status="questionable",
                public_report_reference="league-injury-report-liberty-aces",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                previous_availability_probability=d("0.900000"),
                current_availability_probability=d("0.600000"),
                player_impact_score=d("0.850000"),
                market_liquidity_score=d("0.500000"),
            ),
            flip_item(
                "condition.ready",
                basketball_event_key="nba.nuggets.suns.game-3",
                team_key="denver-nuggets",
                opponent_key="phoenix-suns",
                player_key="jamal-murray",
                injury_key="rest",
                previous_report_status="probable",
                current_report_status="probable",
                public_report_reference="league-injury-report-nuggets-suns",
                previous_availability_probability=d("0.850000"),
                current_availability_probability=d("0.800000"),
                player_impact_score=d("0.400000"),
                market_liquidity_score=d("0.900000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchBasketballInjuryReportFlipDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_BASKETBALL_INJURY_REPORT_FLIP_DIGEST_CONFIG_VERSION
    )
    assert summary.research_scope == BASKETBALL_INJURY_REPORT_FLIP_RESEARCH_SCOPE
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_basketball_injury_report_flip_research"
    )
    assert summary.item_count == d("3.000000")
    assert summary.ready_item_count == d("1.000000")
    assert summary.watch_item_count == d("1.000000")
    assert summary.blocked_item_count == d("1.000000")
    assert summary.status_downgrade_item_count == d("2.000000")
    assert summary.material_flip_item_count == d("2.000000")
    assert summary.high_player_impact_item_count == d("2.000000")
    assert summary.liquidity_gap_item_count == d("2.000000")
    assert summary.source_gap_item_count == d("1.000000")
    assert summary.stale_report_item_count == d("1.000000")
    assert summary.max_report_age_seconds_observed == d("7200.000000")
    assert summary.max_availability_probability_delta == d("0.600000")
    assert summary.average_availability_probability_delta == d("0.316667")
    assert tuple(row.basketball_event_key for row in summary.rows) == (
        "nba.lakers.warriors.game-5",
        "wnba.liberty.aces.final",
        "nba.nuggets.suns.game-3",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.report_age_seconds == d("7200.000000")
    assert blocked.source_diversity_ratio == d("1.000000")
    assert blocked.status_rank_delta == d("2.000000")
    assert blocked.availability_probability_delta == d("0.600000")
    assert blocked.reason_codes == (
        "market_research_basketball_injury_report_flip_digest_status_downgrade",
        "market_research_basketball_injury_report_flip_digest_material_probability_flip",
        "market_research_basketball_injury_report_flip_digest_high_player_impact",
        "market_research_basketball_injury_report_flip_digest_liquidity_gap",
        "market_research_basketball_injury_report_flip_digest_source_gap",
        "market_research_basketball_injury_report_flip_digest_stale_report",
    )

    watched = summary.rows[1]
    assert watched.digest_status == "watch"
    assert watched.status_rank_delta == d("2.000000")
    assert watched.reason_codes == (
        "market_research_basketball_injury_report_flip_digest_status_downgrade",
        "market_research_basketball_injury_report_flip_digest_material_probability_flip",
        "market_research_basketball_injury_report_flip_digest_high_player_impact",
        "market_research_basketball_injury_report_flip_digest_liquidity_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.availability_probability_delta == d("0.050000")
    assert ready.reason_codes == (
        "market_research_basketball_injury_report_flip_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
            reason_code=(
                "market_research_basketball_injury_report_flip_digest_status_downgrade"
            ),
            count=d("2.000000"),
            item_ratio=d("0.666667"),
        ),
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
            reason_code=(
                "market_research_basketball_injury_report_flip_digest_material_probability_flip"
            ),
            count=d("2.000000"),
            item_ratio=d("0.666667"),
        ),
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
            reason_code=(
                "market_research_basketball_injury_report_flip_digest_high_player_impact"
            ),
            count=d("2.000000"),
            item_ratio=d("0.666667"),
        ),
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
            reason_code=(
                "market_research_basketball_injury_report_flip_digest_liquidity_gap"
            ),
            count=d("2.000000"),
            item_ratio=d("0.666667"),
        ),
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
            reason_code="market_research_basketball_injury_report_flip_digest_ready",
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
            reason_code=(
                "market_research_basketball_injury_report_flip_digest_source_gap"
            ),
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
            reason_code=(
                "market_research_basketball_injury_report_flip_digest_stale_report"
            ),
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.item_config_versions == (
        ("nba.lakers.warriors.game-5", "basketball-injury-report-flip-v0"),
        ("nba.nuggets.suns.game-3", "basketball-injury-report-flip-v0"),
        ("wnba.liberty.aces.final", "basketball-injury-report-flip-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_empty_inputs_are_blocked_report_only_and_deterministic() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_basketball_injury_report_flip_research"
    )
    assert summary.item_count == d("0.000000")
    assert summary.ready_item_count == d("0.000000")
    assert summary.watch_item_count == d("0.000000")
    assert summary.blocked_item_count == d("0.000000")
    assert summary.max_report_age_seconds_observed == d("0.000000")
    assert summary.max_availability_probability_delta == d("0.000000")
    assert summary.average_availability_probability_delta == d("0.000000")
    assert summary.rows == ()
    assert summary.item_config_versions == ()
    assert summary.reason_codes == (
        "market_research_basketball_injury_report_flip_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount(
            reason_code="market_research_basketball_injury_report_flip_digest_no_inputs",
            count=d("1.000000"),
            item_ratio=d("0.000000"),
        ),
    )


def test_payload_serializes_decimal_strings_utc_datetimes_and_no_public_ints() -> None:
    summary = report(
        (
            flip_item(
                observed_at=datetime(
                    2026,
                    7,
                    4,
                    13,
                    30,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                previous_availability_probability=d("0.700000"),
                current_availability_probability=d("0.300000"),
            ),
        ),
    )

    payload = market_research_basketball_injury_report_flip_digest_payload(summary)

    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-04T18:00:00Z"
    assert payload["item_count"] == "1.000000"
    assert payload["max_availability_probability_delta"] == "0.400000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T17:30:00Z"
    assert payload["rows"][0]["status_rank_delta"] == "2.000000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(item, float) for item in walk(payload))

    for item in walk(payload):
        if isinstance(item, bool):
            continue
        assert not isinstance(item, int)


def test_validates_exact_types_flags_duplicates_futures_and_manual_drift() -> None:
    assert MarketResearchBasketballInjuryReportFlipDigestConfig.__dataclass_params__.frozen
    assert MarketResearchBasketballInjuryReportFlipDigestItem.__dataclass_params__.frozen
    assert MarketResearchBasketballInjuryReportFlipDigestRow.__dataclass_params__.frozen
    assert MarketResearchBasketballInjuryReportFlipDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("basketball-injury-report-flip-v0"))
    with pytest.raises(ValueError, match="max_report_age_seconds"):
        config(max_report_age_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="material_flip_threshold"):
        config(material_flip_threshold=0.25)
    with pytest.raises(ValueError, match="condition_id"):
        flip_item(condition_id=_StringSubclass("condition.bad"))
    with pytest.raises(ValueError, match="source_count"):
        flip_item(source_count=1.0)
    with pytest.raises(ValueError, match="current_report_status"):
        flip_item(current_report_status="not-listed")
    with pytest.raises(ValueError, match="previous_availability_probability"):
        flip_item(previous_availability_probability=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (flip_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 4, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        report((flip_item(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="public_report_reference"):
        flip_item(public_report_reference="")
    with pytest.raises(ValueError, match="unsafe"):
        flip_item(public_report_reference="https://basketball.example/auth/token")
    for unsafe_reference in (
        "https://basketball.example/injury-report?api-key=abc123",
        "https://basketball.example/injury-report/order/123",
        "https://basketball.example/injury-report/replace/123",
        "https://basketball.example/exchange/injury-report",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            flip_item(public_report_reference=unsafe_reference)
    with pytest.raises(ValueError, match="items"):
        build_market_research_basketball_injury_report_flip_digest(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        report((flip_item(), flip_item(condition_id="condition.other")))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        flip_item(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        flip_item(readonly=False)
    with pytest.raises(FrozenInstanceError):
        summary = report((flip_item(),))
        summary.digest_status = "blocked"  # type: ignore[misc]

    summary = report((flip_item(),))
    with pytest.raises(ValueError, match="report"):
        market_research_basketball_injury_report_flip_digest_payload(object())
    with pytest.raises(ValueError, match="item_count"):
        replace(summary, item_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=())
    with pytest.raises(ValueError, match="status_rank_delta"):
        replace(summary.rows[0], status_rank_delta=d("1.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary.rows[0], reason_codes=())


def test_public_dataclasses_are_decimal_only_and_module_has_no_io_or_live_surface() -> None:
    for exported_type in (
        MarketResearchBasketballInjuryReportFlipDigestConfig,
        MarketResearchBasketballInjuryReportFlipDigestItem,
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount,
        MarketResearchBasketballInjuryReportFlipDigestRow,
        MarketResearchBasketballInjuryReportFlipDigestReport,
    ):
        assert is_dataclass(exported_type)
        assert exported_type.__dataclass_params__.frozen is True

    public_numeric_markers = (
        "_count",
        "_ratio",
        "_seconds",
        "_score",
        "_threshold",
        "_probability",
        "_delta",
    )
    for dataclass_type in (
        MarketResearchBasketballInjuryReportFlipDigestConfig,
        MarketResearchBasketballInjuryReportFlipDigestItem,
        MarketResearchBasketballInjuryReportFlipDigestReasonCodeCount,
        MarketResearchBasketballInjuryReportFlipDigestRow,
        MarketResearchBasketballInjuryReportFlipDigestReport,
    ):
        for field in fields(dataclass_type):
            if any(field.name.endswith(marker) for marker in public_numeric_markers):
                assert field.type in (Decimal, "Decimal")
            if field.name == "count":
                assert field.type in (Decimal, "Decimal")

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    attribute_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
        if isinstance(node, ast.Attribute):
            attribute_names.add(node.attr)

    forbidden_imports = {
        "os",
        "pathlib",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
        "subprocess",
    }
    forbidden_calls_or_attributes = {
        "open",
        "connect",
        "cursor",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "write",
        "read_text",
        "getenv",
        "environ",
        "trade",
    }
    assert imported_modules.isdisjoint(forbidden_imports)
    assert not (call_names & forbidden_calls_or_attributes)
    assert not (attribute_names & forbidden_calls_or_attributes)
    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "auth",
        "secret",
        "private",
        "exchange mutation",
    ):
        assert forbidden not in lowered
