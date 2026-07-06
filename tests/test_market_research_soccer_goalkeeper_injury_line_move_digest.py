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


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_soccer_goalkeeper_injury_line_move_digest.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_soccer_goalkeeper_injury_line_move_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_SOCCER_GOALKEEPER_INJURY_LINE_MOVE_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("3600.000000"),
        "min_source_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "min_line_move_goals": d("0.250000"),
        "min_implied_probability_delta": d("0.050000"),
        "watch_goalkeeper_injury_probability": d("0.350000"),
        "blocked_goalkeeper_injury_probability": d("0.650000"),
        "keeper_impact_threshold": d("0.750000"),
        "source_confidence_threshold": d("0.600000"),
    }
    values.update(overrides)
    return module.MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig(**values)


def observation(
    condition_id: str = "condition.clear",
    goalkeeper_id: str = "keeper.clear",
    *,
    event_id: str = "epl.ars.chelsea.match-38",
    league_id: str = "epl",
    team_id: str = "ars",
    opponent_id: str = "che",
    source_id: str = "source.clear",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=15),
    line_move_goals: Decimal = d("0.010000"),
    implied_probability_delta: Decimal = d("0.010000"),
    goalkeeper_injury_probability: Decimal = d("0.050000"),
    keeper_impact_score: Decimal = d("0.200000"),
    source_count: Decimal = d("3.000000"),
    independent_source_count: Decimal = d("2.000000"),
    source_confidence: Decimal = d("0.500000"),
    line_reference: str = "line-screen-clear",
    injury_reference: str = "injury-report-clear",
    observation_config_version: str = "soccer-goalkeeper-injury-line-move-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchSoccerGoalkeeperInjuryLineMoveObservation(
        condition_id=condition_id,
        event_id=event_id,
        league_id=league_id,
        team_id=team_id,
        opponent_id=opponent_id,
        goalkeeper_id=goalkeeper_id,
        source_id=source_id,
        observed_at=observed_at,
        line_move_goals=line_move_goals,
        implied_probability_delta=implied_probability_delta,
        goalkeeper_injury_probability=goalkeeper_injury_probability,
        keeper_impact_score=keeper_impact_score,
        source_count=source_count,
        independent_source_count=independent_source_count,
        source_confidence=source_confidence,
        line_reference=line_reference,
        injury_reference=injury_reference,
        observation_config_version=observation_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: object, **overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "observations": items,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.build_market_research_soccer_goalkeeper_injury_line_move_digest(
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


def test_empty_input_returns_blocked_report_only_digest() -> None:
    module = api()

    report = build_report(
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(
        report,
        module.MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport,
    )
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.research_scope == "soccer goalkeeper injury line move research digest only"
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_soccer_goalkeeper_injury_line_move_screening"
    )
    assert report.observation_count == d("0.000000")
    assert report.row_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.material_line_move_count == d("0.000000")
    assert report.probability_delta_count == d("0.000000")
    assert report.injury_risk_count == d("0.000000")
    assert report.high_keeper_impact_count == d("0.000000")
    assert report.source_confidence_count == d("0.000000")
    assert report.source_gap_count == d("0.000000")
    assert report.stale_observation_count == d("0.000000")
    assert report.max_observation_age_seconds_observed == d("0.000000")
    assert report.max_line_move_goals == d("0.000000")
    assert report.max_implied_probability_delta == d("0.000000")
    assert report.max_risk_score == d("0.000000")
    assert report.average_risk_score == d("0.000000")
    assert report.rows == ()
    assert report.observation_config_versions == ()
    assert report.reason_codes == (
        "soccer_goalkeeper_injury_line_move_digest_empty",
    )
    assert report.reason_code_counts == (
        module.MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount(
            reason_code="soccer_goalkeeper_injury_line_move_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_digest_reduces_goalkeeper_injury_line_moves_deterministically() -> None:
    module = api()

    report = build_report(
        observation(
            "condition.blocked",
            "keeper.blocked",
            source_id="source.blocked",
            observed_at=GENERATED_AT - timedelta(minutes=75),
            line_move_goals=d("0.500000"),
            implied_probability_delta=d("0.120000"),
            goalkeeper_injury_probability=d("0.700000"),
            keeper_impact_score=d("0.900000"),
            source_count=d("1.000000"),
            independent_source_count=d("1.000000"),
            source_confidence=d("0.850000"),
            line_reference="line-screen-blocked",
            injury_reference="injury-report-blocked",
            observation_config_version="soccer-goalkeeper-injury-line-move-feed-v2",
        ),
        observation(
            "condition.watch",
            "keeper.watch",
            event_id="laliga.real.betis.match-4",
            league_id="laliga",
            team_id="rma",
            opponent_id="bet",
            source_id="source.watch",
            observed_at=datetime(
                2026,
                7,
                4,
                13,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            line_move_goals=d("0.300000"),
            implied_probability_delta=d("0.080000"),
            goalkeeper_injury_probability=d("0.400000"),
            keeper_impact_score=d("0.800000"),
            source_confidence=d("0.700000"),
            line_reference="line-screen-watch",
            injury_reference="injury-report-watch",
            observation_config_version="soccer-goalkeeper-injury-line-move-feed-v1",
        ),
        observation(),
    )

    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_soccer_goalkeeper_injury_line_move_screening"
    )
    assert report.observation_count == d("3.000000")
    assert report.row_count == d("3.000000")
    assert report.blocked_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.material_line_move_count == d("2.000000")
    assert report.probability_delta_count == d("2.000000")
    assert report.injury_risk_count == d("2.000000")
    assert report.high_keeper_impact_count == d("2.000000")
    assert report.source_confidence_count == d("2.000000")
    assert report.source_gap_count == d("1.000000")
    assert report.stale_observation_count == d("1.000000")
    assert report.max_observation_age_seconds_observed == d("4500.000000")
    assert report.max_line_move_goals == d("0.500000")
    assert report.max_implied_probability_delta == d("0.120000")
    assert report.max_risk_score == d("0.900000")
    assert report.average_risk_score == d("0.633333")
    assert report.observation_config_versions == (
        ("source.blocked", "soccer-goalkeeper-injury-line-move-feed-v2"),
        ("source.clear", "soccer-goalkeeper-injury-line-move-feed-v0"),
        ("source.watch", "soccer-goalkeeper-injury-line-move-feed-v1"),
    )
    assert report.reason_codes == (
        "soccer_goalkeeper_injury_line_move_blocked_present",
        "soccer_goalkeeper_injury_line_move_watch_present",
        "soccer_goalkeeper_injury_line_move_material_line_move",
        "soccer_goalkeeper_injury_line_move_material_probability_delta",
        "soccer_goalkeeper_injury_line_move_injury_risk",
        "soccer_goalkeeper_injury_line_move_high_keeper_impact",
        "soccer_goalkeeper_injury_line_move_source_confidence",
        "soccer_goalkeeper_injury_line_move_source_gap",
        "soccer_goalkeeper_injury_line_move_stale_observation",
    )
    assert tuple(item.count for item in report.reason_code_counts) == (
        d("1.000000"),
        d("1.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("1.000000"),
        d("1.000000"),
    )
    assert tuple(item.row_ratio for item in report.reason_code_counts) == (
        d("0.333333"),
        d("0.333333"),
        d("0.666667"),
        d("0.666667"),
        d("0.666667"),
        d("0.666667"),
        d("0.666667"),
        d("0.333333"),
        d("0.333333"),
    )
    assert tuple(row.condition_id for row in report.rows) == (
        "condition.blocked",
        "condition.watch",
        "condition.clear",
    )

    blocked, watched, clear = report.rows
    assert blocked.digest_status == "blocked"
    assert blocked.observation_age_seconds == d("4500.000000")
    assert blocked.source_diversity_ratio == d("1.000000")
    assert blocked.risk_score == d("0.900000")
    assert blocked.reason_codes == (
        "soccer_goalkeeper_injury_line_move_material_line_move",
        "soccer_goalkeeper_injury_line_move_material_probability_delta",
        "soccer_goalkeeper_injury_line_move_injury_risk",
        "soccer_goalkeeper_injury_line_move_high_keeper_impact",
        "soccer_goalkeeper_injury_line_move_source_confidence",
        "soccer_goalkeeper_injury_line_move_source_gap",
        "soccer_goalkeeper_injury_line_move_stale_observation",
    )
    assert watched.digest_status == "watch"
    assert watched.observed_at == datetime(2026, 7, 4, 17, 30, tzinfo=UTC)
    assert watched.reason_codes == (
        "soccer_goalkeeper_injury_line_move_material_line_move",
        "soccer_goalkeeper_injury_line_move_material_probability_delta",
        "soccer_goalkeeper_injury_line_move_injury_risk",
        "soccer_goalkeeper_injury_line_move_high_keeper_impact",
        "soccer_goalkeeper_injury_line_move_source_confidence",
    )
    assert clear.digest_status == "pass"
    assert clear.reason_codes == ("soccer_goalkeeper_injury_line_move_clear",)

    data = module.market_research_soccer_goalkeeper_injury_line_move_digest_payload(
        report,
    )
    json.dumps(data, sort_keys=True)
    assert data["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert data["observation_count"] == "3.000000"
    assert data["rows"][0]["observed_at"] == "2026-07-04T16:45:00+00:00"
    assert data["rows"][0]["risk_score"] == "0.900000"
    assert data["reason_code_counts"][0]["count"] == "1.000000"
    assert not any(isinstance(value, float) for value in walk(data))
    assert not any(type(value) is int and not isinstance(value, bool) for value in walk(data))


def test_validation_rejects_bad_types_future_sources_counts_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="line_move_goals"):
        observation(line_move_goals=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="goalkeeper_injury_probability"):
        observation(goalkeeper_injury_probability=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 4, 18, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 4, 18, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        build_report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="unique source_id"):
        build_report(
            observation("condition.one", "keeper.one", source_id="source.dup"),
            observation("condition.two", "keeper.two", source_id="source.dup"),
        )
    with pytest.raises(ValueError, match="independent_source_count"):
        observation(independent_source_count=d("4.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    report = build_report(
        observation("condition.beta", "keeper.beta", source_id="source.beta"),
        observation("condition.alpha", "keeper.alpha", source_id="source.alpha"),
    )
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report.rows[0], reason_codes=list(report.rows[0].reason_codes))
    with pytest.raises(ValueError, match="positive"):
        replace(report.reason_code_counts[0], count=d("0.000000"))
    with pytest.raises(ValueError, match="whole"):
        replace(report.reason_code_counts[0], count=d("1.500000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=report.reason_code_counts[:-1])

    with pytest.raises(TypeError):

        class BadObservation(module.MarketResearchSoccerGoalkeeperInjuryLineMoveObservation):
            pass


def test_public_dataclasses_are_frozen_and_payload_revalidates_tampering() -> None:
    module = api()
    report = build_report(
        observation(
            "condition.blocked",
            "keeper.blocked",
            source_id="source.blocked",
            observed_at=datetime(
                2026,
                7,
                4,
                13,
                50,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            goalkeeper_injury_probability=d("0.700000"),
            keeper_impact_score=d("0.900000"),
        ),
    )
    row = report.rows[0]
    assert row.observed_at == datetime(2026, 7, 4, 17, 50, tzinfo=UTC)

    with pytest.raises(FrozenInstanceError):
        row.goalkeeper_id = "keeper.changed"  # type: ignore[misc]

    public_classes = (
        module.MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig,
        module.MarketResearchSoccerGoalkeeperInjuryLineMoveObservation,
        module.MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount,
        module.MarketResearchSoccerGoalkeeperInjuryLineMoveRow,
        module.MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport,
    )
    for public_class in public_classes:
        assert public_class.__dataclass_params__.frozen is True
        for field in fields(public_class):
            assert field.name not in {"market_slug", "question", "payload_json"}
            if field.name in {
                "observation_config_versions",
                "paper_only",
                "reason_code_counts",
                "reason_codes",
                "report_only",
                "readonly",
                "rows",
            }:
                continue
            if any(
                fragment in field.name
                for fragment in (
                    "count",
                    "delta",
                    "goals",
                    "probability",
                    "ratio",
                    "score",
                    "seconds",
                    "threshold",
                )
            ):
                assert "Decimal" in str(field.type) or field.type is Decimal

    object.__setattr__(
        row,
        "observed_at",
        datetime(2026, 7, 4, 13, 50, tzinfo=timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="UTC"):
        module.market_research_soccer_goalkeeper_injury_line_move_digest_payload(
            report,
        )
    object.__setattr__(row, "observed_at", datetime(2026, 7, 4, 17, 50, tzinfo=UTC))
    object.__setattr__(report.reason_code_counts[0], "count", d("0.000000"))
    with pytest.raises(ValueError, match="positive"):
        module.market_research_soccer_goalkeeper_injury_line_move_digest_payload(
            report,
        )


def test_source_has_no_forbidden_io_or_unsafe_public_names() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_MARKET_RESEARCH_SOCCER_GOALKEEPER_INJURY_LINE_MOVE_DIGEST_CONFIG_VERSION",
        "SOCCER_GOALKEEPER_INJURY_LINE_MOVE_RESEARCH_SCOPE",
        "MarketResearchSoccerGoalkeeperInjuryLineMoveDigestConfig",
        "MarketResearchSoccerGoalkeeperInjuryLineMoveObservation",
        "MarketResearchSoccerGoalkeeperInjuryLineMoveReasonCodeCount",
        "MarketResearchSoccerGoalkeeperInjuryLineMoveRow",
        "MarketResearchSoccerGoalkeeperInjuryLineMoveDigestReport",
        "build_market_research_soccer_goalkeeper_injury_line_move_digest",
        "market_research_soccer_goalkeeper_injury_line_move_digest_payload",
    )
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    forbidden_imports = {
        "builtins.open",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_fragments = (
        "account",
        "auth",
        "database",
        "live",
        "market_slug",
        "payload_json",
        "private",
        "question",
        "secret",
        "token",
        "trade",
        "wallet",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_imports
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_imports
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)
        if isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"asdict", "open"}

    lowered_source = source.lower()
    for forbidden in (*forbidden_fragments, "asdict"):
        assert forbidden not in lowered_source
