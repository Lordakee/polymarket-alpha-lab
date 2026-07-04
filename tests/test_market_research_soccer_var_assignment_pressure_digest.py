from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 13, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_soccer_var_assignment_pressure_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str,
    *,
    market_slug: str = "chelsea-vs-arsenal-penalty-awarded",
    match_slug: str = "chelsea-vs-arsenal",
    competition: str = "premier-league",
    official_id: str = "official-taylor",
    assignment_role: str = "var_official",
    public_pressure_index: str = "0.880000",
    var_overturn_tendency: str = "0.760000",
    controversy_recency_score: str = "0.840000",
    market_probability_move: str = "0.110000",
    source_row_count: str = "1",
    observed_at: datetime = datetime(2026, 7, 4, 12, 30, tzinfo=UTC),
    reason_codes: tuple[str, ...] = (
        "soccer_var_assignment_favorite_pressure",
    ),
):
    digest = api()
    return digest.SoccerVarAssignmentPressureObservation(
        source_id=source_id,
        market_slug=market_slug,
        match_slug=match_slug,
        competition=competition,
        official_id=official_id,
        assignment_role=assignment_role,
        public_pressure_index=d(public_pressure_index),
        var_overturn_tendency=d(var_overturn_tendency),
        controversy_recency_score=d(controversy_recency_score),
        market_probability_move=d(market_probability_move),
        source_row_count=d(source_row_count),
        observed_at=observed_at,
        reason_codes=reason_codes,
    )


def report(*rows: object, config: object | None = None):
    digest = api()
    return digest.build_market_research_soccer_var_assignment_pressure_digest(
        rows,
        config=config or digest.SoccerVarAssignmentPressureDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )


def test_empty_digest_is_decimal_zeroed_readonly_and_clear() -> None:
    digest_report = report()

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-soccer-var-assignment-pressure-digest-v0"
    )
    assert digest_report.source_row_count == d("0")
    assert digest_report.observation_count == d("0")
    assert digest_report.pass_count == d("0")
    assert digest_report.watch_count == d("0")
    assert digest_report.blocked_count == d("0")
    assert digest_report.max_assignment_pressure_score == d("0.000000")
    assert digest_report.average_assignment_pressure_score == d("0.000000")
    assert digest_report.top_screening_priority_score == d("0.000000")
    assert digest_report.digest_status == "pass"
    assert digest_report.reason_codes == (
        "soccer_var_assignment_pressure_digest_clear",
    )
    assert digest_report.pressure_rows == ()
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_digest_reduces_assignment_pressure_rows() -> None:
    digest_report = report(
        observation(
            "source-inline",
            market_slug="chelsea-vs-arsenal-yellow-cards-over",
            public_pressure_index="0.300000",
            var_overturn_tendency="0.250000",
            controversy_recency_score="0.350000",
            market_probability_move="0.010000",
            observed_at=datetime(
                2026,
                7,
                4,
                9,
                15,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            reason_codes=("soccer_var_assignment_balanced_pressure",),
        ),
        observation(
            "source-blocked-favorite",
            market_slug="chelsea-vs-arsenal-home-penalty",
            public_pressure_index="0.880000",
            var_overturn_tendency="0.760000",
            controversy_recency_score="0.840000",
            market_probability_move="0.110000",
            source_row_count="3",
            observed_at=datetime(2026, 7, 4, 12, 45, tzinfo=UTC),
            reason_codes=("soccer_var_assignment_favorite_pressure",),
        ),
        observation(
            "source-watch-underdog",
            market_slug="chelsea-vs-arsenal-away-red-card",
            public_pressure_index="0.640000",
            var_overturn_tendency="0.580000",
            controversy_recency_score="0.580000",
            market_probability_move="-0.070000",
            source_row_count="2",
            observed_at=datetime(2026, 7, 4, 11, 30, tzinfo=UTC),
            reason_codes=("soccer_var_assignment_underdog_pressure",),
        ),
    )

    assert digest_report.source_row_count == d("6")
    assert digest_report.observation_count == d("3")
    assert digest_report.pass_count == d("1")
    assert digest_report.watch_count == d("1")
    assert digest_report.blocked_count == d("1")
    assert digest_report.max_assignment_pressure_score == d("0.757000")
    assert digest_report.average_assignment_pressure_score == d("0.525167")
    assert digest_report.top_screening_priority_score == d("1.000000")
    assert digest_report.digest_status == "blocked"
    assert digest_report.reason_codes == (
        "soccer_var_assignment_pressure_blocked_present",
        "soccer_var_assignment_pressure_mixed_direction_present",
    )

    assert tuple(row.source_id for row in digest_report.pressure_rows) == (
        "source-blocked-favorite",
        "source-watch-underdog",
        "source-inline",
    )
    blocked_row = digest_report.pressure_rows[0]
    assert blocked_row.assignment_pressure_score == d("0.757000")
    assert blocked_row.directional_move_abs == d("0.110000")
    assert blocked_row.pressure_direction == "favorite_pressure"
    assert blocked_row.pressure_status == "blocked"
    assert blocked_row.screening_priority_score == d("1.000000")
    assert blocked_row.reason_codes == (
        "soccer_var_assignment_pressure_blocked_favorite",
    )
    assert blocked_row.observed_at == datetime(2026, 7, 4, 12, 45, tzinfo=UTC)

    watch_row = digest_report.pressure_rows[1]
    assert watch_row.assignment_pressure_score == d("0.550000")
    assert watch_row.pressure_direction == "underdog_pressure"
    assert watch_row.pressure_status == "watch"
    assert watch_row.screening_priority_score == d("0.733333")
    assert watch_row.reason_codes == (
        "soccer_var_assignment_pressure_watch_underdog",
    )

    assert digest_report.pressure_rows[2].pressure_direction == "balanced_pressure"
    assert digest_report.pressure_rows[2].pressure_status == "pass"


def test_digest_is_deterministic_for_input_order_and_reason_codes() -> None:
    left = observation(
        "source-a",
        market_slug="match-a-home-penalty",
        public_pressure_index="0.640000",
        var_overturn_tendency="0.580000",
        controversy_recency_score="0.580000",
        market_probability_move="0.070000",
        observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
        reason_codes=("soccer_var_assignment_favorite_pressure",),
    )
    right = observation(
        "source-b",
        market_slug="match-b-home-penalty",
        public_pressure_index="0.640000",
        var_overturn_tendency="0.580000",
        controversy_recency_score="0.580000",
        market_probability_move="0.070000",
        observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
        reason_codes=("soccer_var_assignment_favorite_pressure",),
    )

    first = report(right, left)
    second = report(left, right)

    assert tuple(row.source_id for row in first.pressure_rows) == (
        "source-a",
        "source-b",
    )
    assert asdict(first) == asdict(second)
    assert first.reason_codes == (
        "soccer_var_assignment_pressure_watch_present",
        "soccer_var_assignment_pressure_favorite_present",
    )
    assert first.pressure_rows[0].reason_codes == (
        "soccer_var_assignment_pressure_watch_favorite",
    )


def test_validation_rejects_bad_types_timestamps_reasons_and_duplicates() -> None:
    digest = api()

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="public_pressure_index must be a Decimal"):
        digest.SoccerVarAssignmentPressureObservation(
            source_id="source-float",
            market_slug="chelsea-vs-arsenal-penalty-awarded",
            match_slug="chelsea-vs-arsenal",
            competition="premier-league",
            official_id="official-taylor",
            assignment_role="var_official",
            public_pressure_index=0.88,
            var_overturn_tendency=d("0.760000"),
            controversy_recency_score=d("0.840000"),
            market_probability_move=d("0.110000"),
            source_row_count=d("1"),
            observed_at=datetime(2026, 7, 4, 12, 0, tzinfo=UTC),
            reason_codes=("soccer_var_assignment_favorite_pressure",),
        )

    with pytest.raises(ValueError, match="watch_assignment_pressure_score"):
        digest.SoccerVarAssignmentPressureDigestConfig(
            watch_assignment_pressure_score=DerivedDecimal("0.500000"),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        digest.build_market_research_soccer_var_assignment_pressure_digest(
            (),
            generated_at=datetime(2026, 7, 4, 13, 0),
        )

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation("source-naive", observed_at=datetime(2026, 7, 4, 12, 0))

    with pytest.raises(ValueError, match="reason_codes must match pressure direction"):
        observation(
            "source-bad-reason",
            market_probability_move="-0.070000",
            reason_codes=("soccer_var_assignment_favorite_pressure",),
        )

    with pytest.raises(ValueError, match="assignment_role"):
        observation("source-bad-role", assignment_role="assistant_referee")

    with pytest.raises(ValueError, match="inputs must not contain duplicate"):
        report(observation("source-dupe"), observation("source-dupe"))

    with pytest.raises(ValueError, match="blocked_assignment_pressure_score"):
        digest.SoccerVarAssignmentPressureDigestConfig(
            watch_assignment_pressure_score=d("0.700000"),
            blocked_assignment_pressure_score=d("0.600000"),
        )


def test_frozen_dataclasses_and_hard_flags_are_enforced() -> None:
    digest = api()
    row = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        row.public_pressure_index = d("0.500000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="report_only must be True"):
        digest.SoccerVarAssignmentPressureDigestConfig(report_only=False)

    digest_report = report(row)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(digest_report.pressure_rows[0], readonly=False)

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_non_default_thresholds_change_screening_status() -> None:
    digest = api()
    cfg = digest.SoccerVarAssignmentPressureDigestConfig(
        watch_assignment_pressure_score=d("0.300000"),
        blocked_assignment_pressure_score=d("0.400000"),
        directional_move_threshold=d("0.020000"),
    )
    strict_report = report(
        observation(
            "source-strict",
            public_pressure_index="0.400000",
            var_overturn_tendency="0.350000",
            controversy_recency_score="0.300000",
            market_probability_move="0.030000",
        ),
        config=cfg,
    )

    assert strict_report.digest_status == "watch"
    assert strict_report.watch_count == d("1")
    assert strict_report.pressure_rows[0].assignment_pressure_score == d("0.323000")
    assert strict_report.pressure_rows[0].pressure_status == "watch"
    assert strict_report.pressure_rows[0].screening_priority_score == d("0.807500")
    assert strict_report.reason_codes == (
        "soccer_var_assignment_pressure_watch_present",
        "soccer_var_assignment_pressure_favorite_present",
    )


def test_payload_public_numerics_and_source_surfaces_are_safe() -> None:
    digest = api()
    digest_report = report(observation("source-json"))
    payload = digest.market_research_soccer_var_assignment_pressure_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["pressure_rows"][0]["public_pressure_index"] == "0.880000"
    assert payload["pressure_rows"][0]["assignment_pressure_score"] == "0.757000"
    assert payload["pressure_rows"][0]["observed_at"] == "2026-07-04T12:30:00+00:00"

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        else:
            assert not isinstance(value, float)

    walk(payload)

    for value in asdict(digest_report).values():
        if isinstance(value, Decimal):
            assert type(value) is Decimal
    for row in digest_report.pressure_rows:
        for value in asdict(row).values():
            if isinstance(value, Decimal):
                assert type(value) is Decimal
                assert value.as_tuple().exponent in (0, -6)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_soccer_var_assignment_pressure_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "sqlite",
        "psycopg",
        "supabase",
        "open(",
        "private_key",
        "mnemonic",
        "wallet",
        "auth",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name.split(".")[0] for alias in node.names}
            assert names.isdisjoint({"requests", "httpx", "aiohttp", "socket", "sqlite3"})
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in {
                "requests",
                "httpx",
                "aiohttp",
                "socket",
                "sqlite3",
            }
