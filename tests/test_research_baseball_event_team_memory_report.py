from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_baseball_event_team_memory_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_baseball_event_team_memory_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def input_row(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "research_slug": "mlb.event.memory.readiness",
        "specialist_id": "baseball_event_specialist",
        "market_category": "baseball",
        "event_bucket": "mlb_regular_season",
        "lineup_observed_at": GENERATED_AT - timedelta(minutes=20),
        "injury_observed_at": GENERATED_AT - timedelta(minutes=35),
        "news_observed_at": GENERATED_AT - timedelta(minutes=45),
        "lineup_memory_score": d("0.900000"),
        "injury_memory_score": d("0.850000"),
        "news_memory_score": d("0.800000"),
        "calibration_sample_count": d("40.000000"),
        "calibration_hit_rate": d("0.620000"),
        "calibration_error": d("0.080000"),
    }
    values.update(overrides)
    return module.ResearchBaseballEventTeamMemoryInputRow(**values)


def report(rows: tuple[Any, ...], **overrides: object):
    module = api()
    cfg = overrides.pop("config", None) or module.ResearchBaseballEventTeamMemoryConfig()
    return module.build_research_baseball_event_team_memory_report(
        rows,
        config=cfg,
        generated_at=overrides.pop("generated_at", GENERATED_AT),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_baseball_event_team_memory_aggregates_freshness_and_calibration_readiness() -> None:
    module = api()

    summary = report(
        (
            input_row(
                research_slug="alpha.ready",
                lineup_observed_at=GENERATED_AT - timedelta(minutes=15),
                injury_observed_at=GENERATED_AT - timedelta(minutes=20),
                news_observed_at=GENERATED_AT - timedelta(minutes=25),
                lineup_memory_score=d("0.920000"),
                injury_memory_score=d("0.880000"),
                news_memory_score=d("0.840000"),
                calibration_sample_count=d("60.000000"),
                calibration_hit_rate=d("0.650000"),
                calibration_error=d("0.060000"),
            ),
            input_row(
                research_slug="beta.watch",
                lineup_observed_at=GENERATED_AT - timedelta(minutes=50),
                injury_observed_at=GENERATED_AT - timedelta(hours=2),
                news_observed_at=GENERATED_AT - timedelta(minutes=70),
                lineup_memory_score=d("0.760000"),
                injury_memory_score=d("0.620000"),
                news_memory_score=d("0.700000"),
                calibration_sample_count=d("18.000000"),
                calibration_hit_rate=d("0.570000"),
                calibration_error=d("0.140000"),
            ),
            input_row(
                research_slug="gamma.block",
                lineup_observed_at=None,
                injury_observed_at=GENERATED_AT - timedelta(hours=5),
                news_observed_at=GENERATED_AT - timedelta(hours=4),
                lineup_memory_score=d("0.400000"),
                injury_memory_score=d("0.480000"),
                news_memory_score=d("0.500000"),
                calibration_sample_count=d("4.000000"),
                calibration_hit_rate=d("0.440000"),
                calibration_error=d("0.310000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, module.ResearchBaseballEventTeamMemoryReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.status == "block"
    assert summary.recommended_next_step == "block_report_only_baseball_event_team_memory"
    assert summary.event_memory_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.lineup_fresh_count == d("2.000000")
    assert summary.injury_fresh_count == d("1.000000")
    assert summary.news_fresh_count == d("1.000000")
    assert summary.lineup_missing_count == d("1.000000")
    assert summary.freshness_pass_count == d("1.000000")
    assert summary.freshness_watch_count == d("1.000000")
    assert summary.freshness_block_count == d("1.000000")
    assert summary.calibration_pass_count == d("1.000000")
    assert summary.calibration_watch_count == d("1.000000")
    assert summary.calibration_block_count == d("1.000000")
    assert summary.average_specialist_memory_score == d("0.677778")
    assert summary.average_calibration_error == d("0.170000")
    assert summary.average_freshness_score == d("0.500000")
    assert summary.max_news_age_seconds == d("14400.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.research_slug for row in summary.rows) == (
        "gamma.block",
        "beta.watch",
        "alpha.ready",
    )

    blocked, watched, passed = summary.rows
    assert blocked.status == "block"
    assert blocked.freshness_status == "block"
    assert blocked.calibration_status == "block"
    assert blocked.lineup_age_seconds is None
    assert blocked.injury_age_seconds == d("18000.000000")
    assert blocked.news_age_seconds == d("14400.000000")
    assert blocked.specialist_memory_score == d("0.460000")
    assert blocked.freshness_score == d("0.000000")
    assert blocked.reason_codes == (
        "baseball_event_team_memory_calibration_block",
        "baseball_event_team_memory_injury_stale",
        "baseball_event_team_memory_lineup_missing",
        "baseball_event_team_memory_memory_score_block",
        "baseball_event_team_memory_news_stale",
    )

    assert watched.status == "watch"
    assert watched.freshness_status == "watch"
    assert watched.calibration_status == "watch"
    assert watched.specialist_memory_score == d("0.693333")
    assert watched.freshness_score == d("0.333333")
    assert watched.reason_codes == (
        "baseball_event_team_memory_calibration_watch",
        "baseball_event_team_memory_injury_stale",
        "baseball_event_team_memory_news_stale",
        "baseball_event_team_memory_watch",
    )

    assert passed.status == "pass"
    assert passed.freshness_status == "pass"
    assert passed.calibration_status == "pass"
    assert passed.specialist_memory_score == d("0.880000")
    assert passed.freshness_score == d("1.000000")
    assert passed.reason_codes == (
        "baseball_event_team_memory_calibration_pass",
        "baseball_event_team_memory_fresh",
        "baseball_event_team_memory_pass",
    )

    assert summary.reason_code_counts == (
        module.ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code="baseball_event_team_memory_calibration_block",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code="baseball_event_team_memory_calibration_pass",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code="baseball_event_team_memory_calibration_watch",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code="baseball_event_team_memory_fresh",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code="baseball_event_team_memory_injury_stale",
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        module.ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code="baseball_event_team_memory_lineup_missing",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code="baseball_event_team_memory_memory_score_block",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code="baseball_event_team_memory_news_stale",
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        module.ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code="baseball_event_team_memory_pass",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        module.ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code="baseball_event_team_memory_watch",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(row.reason_code for row in summary.reason_code_counts)


def test_payload_and_digest_are_deterministic_and_omit_raw_team_game_and_source_surfaces() -> None:
    module = api()
    rows = (
        input_row(
            research_slug="zeta.watch",
            specialist_id="specialist.public",
            lineup_observed_at=GENERATED_AT - timedelta(minutes=15),
            injury_observed_at=GENERATED_AT - timedelta(hours=3),
            news_observed_at=GENERATED_AT - timedelta(hours=2),
            lineup_memory_score=d("0.820000"),
            injury_memory_score=d("0.660000"),
            news_memory_score=d("0.720000"),
            calibration_sample_count=d("16.000000"),
            calibration_hit_rate=d("0.580000"),
            calibration_error=d("0.120000"),
        ),
        input_row(
            research_slug="alpha.pass",
            specialist_id="specialist.public",
        ),
    )

    first = report(rows)
    second = report(tuple(reversed(rows)))
    first_payload = module.research_baseball_event_team_memory_report_payload(first)
    second_payload = module.research_baseball_event_team_memory_report_payload(second)

    assert first_payload == second_payload
    assert module.research_baseball_event_team_memory_report_digest(first) == (
        module.research_baseball_event_team_memory_report_digest(second)
    )
    assert first.payload == first_payload
    assert first.digest == module.research_baseball_event_team_memory_report_digest(first)
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True

    public = repr(first_payload).lower()
    for token in (
        "team_id",
        "team_name",
        "home_team",
        "away_team",
        "game_id",
        "game_slug",
        "source_id",
        "source_url",
        "source_reference",
        "raw_team",
        "raw_game",
        "raw_source",
    ):
        assert token not in public
    assert_no_float_values(first_payload)


def test_empty_inputs_returns_report_only_blocked_digest() -> None:
    module = api()
    summary = report(())

    assert summary.status == "block"
    assert summary.recommended_next_step == "block_report_only_baseball_event_team_memory"
    assert summary.event_memory_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == ("baseball_event_team_memory_no_inputs",)
    assert summary.reason_code_counts == (
        module.ResearchBaseballEventTeamMemoryReasonCodeCount(
            reason_code="baseball_event_team_memory_no_inputs",
            count=d("1.000000"),
            event_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_validation_freezing_decimal_only_and_safety_surface() -> None:
    module = api()

    with pytest.raises(TypeError, match="Decimal"):
        input_row(lineup_memory_score=0.9)
    with pytest.raises(TypeError, match="exactly Decimal"):
        input_row(calibration_error=_DecimalSubclass("0.080000"))
    with pytest.raises(ValueError, match="unit interval"):
        input_row(calibration_hit_rate=d("1.000001"))
    with pytest.raises(ValueError, match="canonical"):
        input_row(research_slug=" Bad Slug ")
    with pytest.raises(ValueError, match="baseball"):
        input_row(market_category="football")
    with pytest.raises(ValueError, match="future"):
        report((input_row(lineup_observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)

    frozen = input_row()
    with pytest.raises(FrozenInstanceError):
        frozen.research_slug = "other"  # type: ignore[misc]

    summary = report((frozen,))
    with pytest.raises(FrozenInstanceError):
        summary.status = "pass"  # type: ignore[misc]

    for item in (frozen, summary, summary.rows[0]):
        for field in fields(item):
            value = getattr(item, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(summary, recommended_next_step="place_order")
    with pytest.raises(ValueError, match="reason_code"):
        replace(summary.rows[0], reason_codes=("unknown_reason",))
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=(object(),))  # type: ignore[arg-type]

    for cls in (
        module.ResearchBaseballEventTeamMemoryConfig,
        module.ResearchBaseballEventTeamMemoryInputRow,
        module.ResearchBaseballEventTeamMemoryReportRow,
        module.ResearchBaseballEventTeamMemoryReasonCodeCount,
        module.ResearchBaseballEventTeamMemoryReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True


def test_module_is_report_only_and_has_no_io_network_wallet_or_trading_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "io",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }
    forbidden_terms = (
        "wallet",
        "broker",
        "signing",
        "order",
        "cancel",
        "account",
        "advice",
        "team_id",
        "game_id",
        "source_id",
    )

    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)
    assert not any(term in source.lower() for term in forbidden_terms)
