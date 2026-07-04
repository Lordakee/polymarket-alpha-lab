from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 21, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_basketball_line_movement_injury_correlation_digest.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def digest() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_basketball_line_movement_injury_correlation_digest",
    )


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


def config(**overrides: object) -> Any:
    module = digest()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("3600.000000"),
        "min_source_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "min_line_move_points": d("2.500000"),
        "min_implied_probability_delta": d("0.050000"),
        "high_player_impact_threshold": d("0.750000"),
        "correlation_watch_threshold": d("0.650000"),
        "correlation_blocked_threshold": d("0.850000"),
        "min_market_liquidity_score": d("0.550000"),
    }
    values.update(overrides)
    return module.MarketResearchBasketballLineMovementInjuryCorrelationDigestConfig(
        **values,
    )


def observation(
    source_id: str = "source-lal",
    *,
    condition_id: str = "condition.nba.lakers.nuggets.lebron-ankle",
    basketball_event_key: str = "nba.lakers.nuggets.game-6",
    league_key: str = "nba",
    team_key: str = "los-angeles-lakers",
    opponent_key: str = "denver-nuggets",
    player_key: str = "lebron-james",
    injury_status: str = "questionable",
    market_slug: str = "lakers-vs-nuggets-moneyline",
    public_line_reference: str = "sportsbook-line-screen-lakers-nuggets",
    public_injury_reference: str = "league-injury-report-lakers-nuggets",
    observed_at: datetime | None = None,
    line_move_points: Decimal = d("4.500000"),
    implied_probability_delta: Decimal = d("0.120000"),
    player_impact_score: Decimal = d("0.900000"),
    injury_correlation_score: Decimal = d("0.920000"),
    source_count: Decimal = d("3.000000"),
    independent_source_count: Decimal = d("2.000000"),
    market_liquidity_score: Decimal = d("0.800000"),
    item_config_version: str = "line-movement-injury-correlation-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = digest()
    return module.MarketResearchBasketballLineMovementInjuryCorrelationObservation(
        source_id=source_id,
        condition_id=condition_id,
        basketball_event_key=basketball_event_key,
        league_key=league_key,
        team_key=team_key,
        opponent_key=opponent_key,
        player_key=player_key,
        injury_status=injury_status,
        market_slug=market_slug,
        public_line_reference=public_line_reference,
        public_injury_reference=public_injury_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=20),
        line_move_points=line_move_points,
        implied_probability_delta=implied_probability_delta,
        player_impact_score=player_impact_score,
        injury_correlation_score=injury_correlation_score,
        source_count=source_count,
        independent_source_count=independent_source_count,
        market_liquidity_score=market_liquidity_score,
        item_config_version=item_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, cfg: object | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = digest()
    return module.build_market_research_basketball_line_movement_injury_correlation_digest(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_digest_reduces_line_movement_injury_correlation_pressure() -> None:
    summary = report(
        observation(
            "source-lal",
            observed_at=GENERATED_AT - timedelta(hours=2),
            source_count=d("1.000000"),
            independent_source_count=d("1.000000"),
            market_liquidity_score=d("0.400000"),
        ),
        observation(
            "source-bos",
            condition_id="condition.nba.celtics.heat.tatum-wrist",
            basketball_event_key="nba.celtics.heat.game-4",
            team_key="boston-celtics",
            opponent_key="miami-heat",
            player_key="jayson-tatum",
            injury_status="probable",
            market_slug="celtics-vs-heat-spread",
            public_line_reference="sportsbook-line-screen-celtics-heat",
            public_injury_reference="league-injury-report-celtics-heat",
            observed_at=datetime(
                2026,
                7,
                4,
                16,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            line_move_points=d("3.000000"),
            implied_probability_delta=d("0.080000"),
            player_impact_score=d("0.800000"),
            injury_correlation_score=d("0.700000"),
        ),
        observation(
            "source-nyk",
            condition_id="condition.nba.knicks.sixers.bridges-rest",
            basketball_event_key="nba.knicks.sixers.game-2",
            team_key="new-york-knicks",
            opponent_key="philadelphia-76ers",
            player_key="mikal-bridges",
            injury_status="available",
            market_slug="knicks-vs-sixers-total",
            public_line_reference="sportsbook-line-screen-knicks-sixers",
            public_injury_reference="league-injury-report-knicks-sixers",
            line_move_points=d("0.500000"),
            implied_probability_delta=d("0.010000"),
            player_impact_score=d("0.200000"),
            injury_correlation_score=d("0.100000"),
            market_liquidity_score=d("0.900000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    module = digest()
    assert isinstance(
        summary,
        module.MarketResearchBasketballLineMovementInjuryCorrelationDigestReport,
    )
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_DIGEST_CONFIG_VERSION
    )
    assert summary.research_scope == (
        module.BASKETBALL_LINE_MOVEMENT_INJURY_CORRELATION_RESEARCH_SCOPE
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_basketball_line_movement_injury_correlation_screening"
    )
    assert summary.input_count == d("3.000000")
    assert summary.row_count == d("3.000000")
    assert summary.blocked_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.ready_count == d("1.000000")
    assert summary.material_line_move_count == d("2.000000")
    assert summary.probability_delta_count == d("2.000000")
    assert summary.high_player_impact_count == d("2.000000")
    assert summary.correlation_pressure_count == d("2.000000")
    assert summary.source_gap_count == d("1.000000")
    assert summary.liquidity_gap_count == d("1.000000")
    assert summary.stale_observation_count == d("1.000000")
    assert summary.max_observation_age_seconds_observed == d("7200.000000")
    assert summary.max_line_move_points == d("4.500000")
    assert summary.max_implied_probability_delta == d("0.120000")
    assert summary.max_injury_correlation_score == d("0.920000")
    assert summary.average_injury_correlation_score == d("0.573333")
    assert tuple(row.market_slug for row in summary.rows) == (
        "lakers-vs-nuggets-moneyline",
        "celtics-vs-heat-spread",
        "knicks-vs-sixers-total",
    )

    blocked, watched, ready = summary.rows
    assert blocked.digest_status == "blocked"
    assert blocked.observation_age_seconds == d("7200.000000")
    assert blocked.source_diversity_ratio == d("1.000000")
    assert blocked.reason_codes == (
        "market_research_basketball_line_movement_injury_correlation_digest_material_line_move",
        "market_research_basketball_line_movement_injury_correlation_digest_material_probability_delta",
        "market_research_basketball_line_movement_injury_correlation_digest_high_player_impact",
        "market_research_basketball_line_movement_injury_correlation_digest_correlation_blocked",
        "market_research_basketball_line_movement_injury_correlation_digest_source_gap",
        "market_research_basketball_line_movement_injury_correlation_digest_liquidity_gap",
        "market_research_basketball_line_movement_injury_correlation_digest_stale_observation",
    )
    assert watched.digest_status == "watch"
    assert watched.observed_at == datetime(2026, 7, 4, 20, 30, tzinfo=UTC)
    assert watched.reason_codes == (
        "market_research_basketball_line_movement_injury_correlation_digest_material_line_move",
        "market_research_basketball_line_movement_injury_correlation_digest_material_probability_delta",
        "market_research_basketball_line_movement_injury_correlation_digest_high_player_impact",
        "market_research_basketball_line_movement_injury_correlation_digest_correlation_watch",
    )
    assert ready.digest_status == "ready"
    assert ready.reason_codes == (
        "market_research_basketball_line_movement_injury_correlation_digest_ready",
    )

    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.reason_code_counts[0] == (
        module.MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount(
            reason_code=(
                "market_research_basketball_line_movement_injury_correlation_digest_material_line_move"
            ),
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        )
    )
    assert summary.reason_code_counts[-1] == (
        module.MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount(
            reason_code=(
                "market_research_basketball_line_movement_injury_correlation_digest_ready"
            ),
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
    )
    assert summary.item_config_versions == (
        ("source-bos", "line-movement-injury-correlation-v0"),
        ("source-lal", "line-movement-injury-correlation-v0"),
        ("source-nyk", "line-movement-injury-correlation-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_empty_inputs_are_blocked_report_only_and_deterministic() -> None:
    module = digest()
    summary = report()

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_basketball_line_movement_injury_correlation_screening"
    )
    assert summary.input_count == d("0.000000")
    assert summary.row_count == d("0.000000")
    assert summary.blocked_count == d("0.000000")
    assert summary.watch_count == d("0.000000")
    assert summary.ready_count == d("0.000000")
    assert summary.rows == ()
    assert summary.item_config_versions == ()
    assert summary.reason_codes == (
        "market_research_basketball_line_movement_injury_correlation_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        module.MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount(
            reason_code=(
                "market_research_basketball_line_movement_injury_correlation_digest_no_inputs"
            ),
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )


def test_payload_serializes_decimal_strings_utc_datetimes_and_no_public_ints() -> None:
    module = digest()
    summary = report(
        observation(
            "source-payload",
            observed_at=datetime(
                2026,
                7,
                4,
                16,
                45,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            line_move_points=d("2.750000"),
            implied_probability_delta=d("0.060000"),
            injury_correlation_score=d("0.720000"),
        ),
    )

    payload = (
        module.market_research_basketball_line_movement_injury_correlation_digest_payload(
            summary,
        )
    )

    json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-04T21:00:00Z"
    assert payload["input_count"] == "1.000000"
    assert payload["max_injury_correlation_score"] == "0.720000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T20:45:00Z"
    assert payload["rows"][0]["line_move_points"] == "2.750000"
    assert payload["reason_code_counts"][0]["count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(item, float) for item in walk(payload))
    for item in walk(payload):
        if isinstance(item, bool):
            continue
        assert not isinstance(item, int)


def test_validation_rejects_bad_inputs_flags_futures_duplicates_and_manual_drift() -> None:
    module = digest()
    assert (
        module.MarketResearchBasketballLineMovementInjuryCorrelationDigestConfig.__dataclass_params__.frozen
    )
    assert (
        module.MarketResearchBasketballLineMovementInjuryCorrelationObservation.__dataclass_params__.frozen
    )
    assert (
        module.MarketResearchBasketballLineMovementInjuryCorrelationDigestRow.__dataclass_params__.frozen
    )
    assert (
        module.MarketResearchBasketballLineMovementInjuryCorrelationDigestReport.__dataclass_params__.frozen
    )

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("line-movement-injury-correlation-v0"))
    with pytest.raises(ValueError, match="min_line_move_points"):
        config(min_line_move_points=_DecimalSubclass("2.500000"))
    with pytest.raises(ValueError, match="correlation_watch_threshold"):
        config(correlation_watch_threshold=d("0.900000"))
    with pytest.raises(ValueError, match="source_id"):
        observation(source_id=_StringSubclass("source-bad"))
    with pytest.raises(ValueError, match="line_move_points"):
        observation(line_move_points=Decimal("-0.100000"))
    with pytest.raises(ValueError, match="injury_correlation_score"):
        observation(injury_correlation_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="independent_source_count"):
        observation(
            source_count=d("1.000000"),
            independent_source_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="public_line_reference"):
        observation(public_line_reference="")
    with pytest.raises(ValueError, match="unsafe"):
        observation(public_injury_reference="league-injury-report-token")
    with pytest.raises(ValueError, match="generated_at"):
        report(
            observation("source-datetime"),
            generated_at=_DatetimeSubclass(2026, 7, 4, 21, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="items"):
        module.build_market_research_basketball_line_movement_injury_correlation_digest(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        observation(readonly=False)
    with pytest.raises(FrozenInstanceError):
        summary = report(observation("source-frozen"))
        summary.digest_status = "blocked"  # type: ignore[misc]

    summary = report(observation("source-valid"))
    with pytest.raises(ValueError, match="report"):
        module.market_research_basketball_line_movement_injury_correlation_digest_payload(
            object(),
        )
    with pytest.raises(ValueError, match="row_count"):
        replace(summary, row_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=())
    with pytest.raises(ValueError, match="digest_status"):
        replace(summary.rows[0], digest_status="ready")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary.rows[0], reason_codes=())


def test_public_dataclasses_are_decimal_only_and_module_has_no_io_or_live_surface() -> None:
    module = digest()
    exported_types = (
        module.MarketResearchBasketballLineMovementInjuryCorrelationDigestConfig,
        module.MarketResearchBasketballLineMovementInjuryCorrelationObservation,
        module.MarketResearchBasketballLineMovementInjuryCorrelationDigestRow,
        module.MarketResearchBasketballLineMovementInjuryCorrelationReasonCodeCount,
        module.MarketResearchBasketballLineMovementInjuryCorrelationDigestReport,
    )
    for exported_type in exported_types:
        assert is_dataclass(exported_type)
        assert exported_type.__dataclass_params__.frozen is True

    public_numeric_markers = (
        "_count",
        "_ratio",
        "_seconds",
        "_points",
        "_delta",
        "_score",
        "_threshold",
    )
    for dataclass_type in exported_types:
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
        "replace_order",
        "exchange mutation",
        "api_key",
        "secret_key",
        "private_key",
    ):
        assert forbidden not in lowered
