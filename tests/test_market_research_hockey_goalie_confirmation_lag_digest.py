from __future__ import annotations

import ast
import importlib
import re
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_hockey_goalie_confirmation_lag_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "market-research-hockey-goalie-confirmation-lag-digest-v0",
        "watch_unconfirmed_window_seconds": d("86400.000000"),
        "blocked_unconfirmed_window_seconds": d("7200.000000"),
        "watch_confirmation_lag_seconds": d("21600.000000"),
        "blocked_confirmation_lag_seconds": d("43200.000000"),
        "min_confirmed_source_count": d("2"),
    }
    values.update(overrides)
    return module.HockeyGoalieConfirmationLagDigestConfig(**values)


def observation(
    source_id: str = "source-alpha",
    *,
    event_id: str = "nhl-game-alpha",
    market_slug: str = "nhl-game-alpha-moneyline",
    team_id: str = "team-alpha",
    scheduled_start_at: datetime = GENERATED_AT + timedelta(days=2),
    confirmation_updated_at: datetime = GENERATED_AT - timedelta(hours=1),
    confirmation_state: str = "confirmed",
    source_count: Decimal = d("2"),
    source_row_count: Decimal = d("1"),
    reason_codes: tuple[str, ...] = ("goalie_confirmed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.HockeyGoalieConfirmationLagObservation(
        source_id=source_id,
        event_id=event_id,
        market_slug=market_slug,
        team_id=team_id,
        scheduled_start_at=scheduled_start_at,
        confirmation_updated_at=confirmation_updated_at,
        confirmation_state=confirmation_state,
        source_count=source_count,
        source_row_count=source_row_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(
    *rows: Any,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_research_hockey_goalie_confirmation_lag_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_zero_digest() -> None:
    module = api()

    report = digest(
        generated_at=datetime(2026, 7, 4, 14, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, module.HockeyGoalieConfirmationLagDigestReport)
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        "market-research-hockey-goalie-confirmation-lag-digest-v0"
    )
    assert report.source_row_count == d("0")
    assert report.observation_count == d("0")
    assert report.confirmed_count == d("0")
    assert report.projected_count == d("0")
    assert report.unconfirmed_count == d("0")
    assert report.close_to_start_count == d("0")
    assert report.stale_confirmation_count == d("0")
    assert report.low_source_count == d("0")
    assert report.watch_count == d("0")
    assert report.blocked_count == d("0")
    assert report.max_confirmation_lag_seconds == ZERO
    assert report.max_risk_score == ZERO
    assert report.risk_ratio == ZERO
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_hockey_goalie_confirmation_lag_digest"
    )
    assert report.goalie_rows == ()
    assert report.reason_codes == ("goalie_confirmation_lag_digest_empty",)
    assert report.reason_code_counts == (
        module.HockeyGoalieConfirmationLagReasonCodeCount(
            reason_code="goalie_confirmation_lag_digest_empty",
            count=d("1"),
            observation_ratio=ZERO,
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_high_risk_unconfirmed_stale_goalie_blocks_screening() -> None:
    report = digest(
        observation(
            "confirmed-safe",
            event_id="nhl-game-safe",
            market_slug="nhl-game-safe-moneyline",
            team_id="team-safe",
        ),
        observation(
            "stale-unconfirmed",
            event_id="nhl-game-risk",
            market_slug="nhl-game-risk-moneyline",
            team_id="team-risk",
            scheduled_start_at=GENERATED_AT + timedelta(minutes=30),
            confirmation_updated_at=GENERATED_AT - timedelta(hours=16),
            confirmation_state="unconfirmed",
            source_count=d("0"),
            source_row_count=d("3"),
            reason_codes=("goalie_unconfirmed",),
        ),
    )

    assert report.digest_status == "blocked"
    assert report.observation_count == d("2")
    assert report.source_row_count == d("4")
    assert report.confirmed_count == d("1")
    assert report.unconfirmed_count == d("1")
    assert report.close_to_start_count == d("1")
    assert report.stale_confirmation_count == d("1")
    assert report.blocked_count == d("1")
    assert report.max_confirmation_lag_seconds == d("57600.000000")
    assert report.max_risk_score == d("8.000000")
    assert report.risk_ratio == d("0.500000")
    assert report.reason_codes == (
        "goalie_confirmation_lag_digest_blocked",
        "goalie_confirmation_close_to_start_present",
        "goalie_confirmation_stale_present",
    )

    blocked, passed = report.goalie_rows
    assert blocked.source_id == "stale-unconfirmed"
    assert blocked.seconds_to_start == d("1800.000000")
    assert blocked.confirmation_lag_seconds == d("57600.000000")
    assert blocked.risk_score == d("8.000000")
    assert blocked.lag_status == "blocked"
    assert blocked.reason_codes == (
        "goalie_confirmation_lag_blocked",
        "unconfirmed_goalie_confirmation_blocked",
    )
    assert passed.source_id == "confirmed-safe"
    assert passed.lag_status == "pass"
    assert passed.reason_codes == ("goalie_confirmation_lag_clear",)


def test_deterministic_sorting_prioritizes_status_score_start_and_slug() -> None:
    inputs = (
        observation("z-pass", market_slug="z-pass", event_id="z-event", team_id="z-team"),
        observation(
            "b-watch",
            event_id="b-event",
            market_slug="b-watch",
            team_id="b-team",
            scheduled_start_at=GENERATED_AT + timedelta(hours=8),
            confirmation_state="projected",
            reason_codes=("goalie_projected",),
        ),
        observation(
            "a-block-low",
            event_id="a-event",
            market_slug="a-block-low",
            team_id="a-team",
            scheduled_start_at=GENERATED_AT + timedelta(minutes=45),
            confirmation_state="projected",
            reason_codes=("goalie_projected",),
        ),
        observation(
            "c-block-high",
            event_id="c-event",
            market_slug="c-block-high",
            team_id="c-team",
            scheduled_start_at=GENERATED_AT + timedelta(minutes=45),
            confirmation_updated_at=GENERATED_AT - timedelta(hours=13),
            confirmation_state="projected",
            reason_codes=("goalie_projected",),
        ),
    )
    report = digest(*inputs)

    assert tuple(row.source_id for row in report.goalie_rows) == (
        "c-block-high",
        "a-block-low",
        "b-watch",
        "z-pass",
    )
    assert tuple(row.lag_status for row in report.goalie_rows) == (
        "blocked",
        "blocked",
        "watch",
        "pass",
    )

    same_again = digest(*reversed(inputs))
    assert same_again.goalie_rows == report.goalie_rows
    assert same_again.reason_codes == report.reason_codes
    assert same_again.reason_code_counts == report.reason_code_counts


def test_validation_rejects_bad_inputs_duplicates_and_inconsistent_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        observation(source_count=_DecimalSubclass("2"))
    with pytest.raises(ValueError, match="source_row_count must be an integer Decimal"):
        observation(source_row_count=d("1.500000"))
    with pytest.raises(ValueError, match="scheduled_start_at must be timezone-aware"):
        observation(scheduled_start_at=datetime(2026, 7, 4, 20, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        digest(
            observation("generated-subclass"),
            generated_at=_DateTimeSubclass(2026, 7, 4, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="confirmation_updated_at must not be after generated_at"):
        digest(
            observation(
                "future-confirmation",
                confirmation_updated_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="reason_codes must match confirmation_state"):
        observation(
            confirmation_state="projected",
            reason_codes=("goalie_confirmed",),
        )
    with pytest.raises(ValueError, match="inputs must not contain duplicate source_id"):
        digest(observation("duplicate"), observation("duplicate"))
    with pytest.raises(ValueError, match="blocked_unconfirmed_window_seconds"):
        config(blocked_unconfirmed_window_seconds=d("90000.000000"))
    with pytest.raises(ValueError, match="watch_confirmation_lag_seconds"):
        config(watch_confirmation_lag_seconds=d("50000.000000"))

    report = digest(
        observation("consistent-b", market_slug="consistent-b", event_id="event-b"),
        observation("consistent-a", market_slug="consistent-a", event_id="event-a"),
    )
    with pytest.raises(ValueError, match="observation_count"):
        replace(report, observation_count=d("3"))
    with pytest.raises(ValueError, match="goalie_rows must be sorted"):
        replace(report, goalie_rows=tuple(reversed(report.goalie_rows)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("goalie_confirmation_lag_digest_watch",))


def test_hard_flags_and_public_numeric_fields_are_enforced() -> None:
    module = api()
    report = digest(observation("frozen"))

    for value in (
        config(),
        observation("public-record"),
        report.goalie_rows[0],
        report.reason_code_counts[0],
        report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                assert field_value is True
                continue
            assert type(field_value) is not int, field.name
            assert type(field_value) is not float, field.name

    with pytest.raises(FrozenInstanceError):
        report.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.goalie_rows[0].risk_score = d("9.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation("bad-paper", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.HockeyGoalieConfirmationLagReasonCodeCount(
            reason_code="goalie_confirmation_lag_clear",
            count=d("1"),
            observation_ratio=d("1.000000"),
            readonly=False,
        )


def test_non_default_block_window_escalates_projected_goalie_to_blocked() -> None:
    projected_three_hours_out = observation(
        "projected-three-hours",
        scheduled_start_at=GENERATED_AT + timedelta(hours=3),
        confirmation_state="projected",
        reason_codes=("goalie_projected",),
    )

    default_report = digest(projected_three_hours_out)
    strict_report = digest(
        projected_three_hours_out,
        cfg=config(blocked_unconfirmed_window_seconds=d("14400.000000")),
    )

    assert default_report.digest_status == "watch"
    assert default_report.goalie_rows[0].lag_status == "watch"
    assert default_report.goalie_rows[0].reason_codes == (
        "projected_goalie_confirmation_watch",
    )
    assert strict_report.digest_status == "blocked"
    assert strict_report.goalie_rows[0].lag_status == "blocked"
    assert strict_report.goalie_rows[0].reason_codes == (
        "projected_goalie_confirmation_blocked",
    )


def test_payload_serializes_decimals_and_static_surface_stays_readonly() -> None:
    module = api()
    report = digest(
        observation(
            "payload-risk",
            scheduled_start_at=GENERATED_AT + timedelta(minutes=45),
            confirmation_updated_at=GENERATED_AT - timedelta(hours=13),
            confirmation_state="projected",
            reason_codes=("goalie_projected",),
        ),
    )

    payload = module.market_research_hockey_goalie_confirmation_lag_digest_payload(report)

    assert payload["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["source_row_count"] == "1"
    assert payload["risk_ratio"] == "1.000000"
    assert payload["goalie_rows"][0]["seconds_to_start"] == "2700.000000"
    assert payload["goalie_rows"][0]["confirmation_lag_seconds"] == "46800.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _contains_decimal_datetime_or_float(payload)

    source = Path(
        "src/polymarket_alpha_lab/market_research_hockey_goalie_confirmation_lag_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "private_key",
        "wallet",
        "requests",
        "httpx",
        "urlopen",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "connect(",
        "execute(",
        "cancel",
        "replace_order",
        "live_trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not re.search(r"\b(private_key|wallet|auth|trade|broker)\b", lowered)


def _contains_decimal_datetime_or_float(value: object) -> bool:
    if isinstance(value, (Decimal, datetime, float)):
        return True
    if isinstance(value, dict):
        return any(_contains_decimal_datetime_or_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_decimal_datetime_or_float(item) for item in value)
    return False
