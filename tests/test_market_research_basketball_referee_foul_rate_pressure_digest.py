from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 5, 20, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_basketball_referee_foul_rate_pressure_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    event_id: str = "nba-finals-game-7",
    league_key: str = "nba",
    referee_id: str = "referee-alpha",
    team_key: str = "team-alpha",
    crew_fouls_per_game: str | Decimal = "19.000000",
    league_fouls_per_game: str | Decimal = "18.000000",
    late_game_foul_delta_per_game: str | Decimal = "0.500000",
    lookback_games: str | Decimal = "20.000000",
    evidence_confidence: str | Decimal = "0.840000",
    observed_at: datetime = datetime(2026, 7, 5, 19, 50, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_box_score",),
):
    module = digest()
    return module.BasketballRefereeFoulRatePressureObservation(
        source_id=source_id,
        event_id=event_id,
        league_key=league_key,
        referee_id=referee_id,
        team_key=team_key,
        crew_fouls_per_game=(
            crew_fouls_per_game
            if isinstance(crew_fouls_per_game, Decimal)
            else d(crew_fouls_per_game)
        ),
        league_fouls_per_game=(
            league_fouls_per_game
            if isinstance(league_fouls_per_game, Decimal)
            else d(league_fouls_per_game)
        ),
        late_game_foul_delta_per_game=(
            late_game_foul_delta_per_game
            if isinstance(late_game_foul_delta_per_game, Decimal)
            else d(late_game_foul_delta_per_game)
        ),
        lookback_games=lookback_games if isinstance(lookback_games, Decimal) else d(lookback_games),
        evidence_confidence=(
            evidence_confidence
            if isinstance(evidence_confidence, Decimal)
            else d(evidence_confidence)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_basketball_referee_foul_rate_pressure_digest(
        rows,
        config=cfg or module.BasketballRefereeFoulRatePressureDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.BasketballRefereeFoulRatePressureDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-basketball-referee-foul-rate-pressure-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_basketball_referee_foul_rate_pressure_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.elevated_foul_rate_count == d("0.000000")
    assert digest_report.late_game_pressure_count == d("0.000000")
    assert digest_report.low_sample_count == d("0.000000")
    assert digest_report.max_pressure_score == d("0.000000")
    assert digest_report.average_pressure_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "basketball_referee_foul_pressure_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.BasketballRefereeFoulRatePressureReasonCodeCount(
            reason_code="basketball_referee_foul_pressure_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_elevated_referee_foul_pressure_blocks_probability_event_screening() -> None:
    digest_report = report(
        observation(
            "source-blocked",
            event_id="nba-finals-game-7",
            referee_id="referee-alpha",
            crew_fouls_per_game="25.000000",
            league_fouls_per_game="18.000000",
            late_game_foul_delta_per_game="3.500000",
            lookback_games="18.000000",
            evidence_confidence="0.920000",
            observed_at=datetime(
                2026,
                7,
                5,
                15,
                50,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
        observation(
            "source-watch",
            event_id="nba-semis-game-6",
            referee_id="referee-beta",
            crew_fouls_per_game="21.500000",
            league_fouls_per_game="18.000000",
            late_game_foul_delta_per_game="0.500000",
            lookback_games="12.000000",
        ),
        observation(
            "source-pass",
            event_id="nba-regular-game-82",
            referee_id="referee-gamma",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_basketball_referee_foul_rate_pressure_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.elevated_foul_rate_count == d("2.000000")
    assert digest_report.late_game_pressure_count == d("1.000000")
    assert digest_report.low_sample_count == d("0.000000")
    assert digest_report.max_pressure_score == d("1.000000")
    assert digest_report.average_pressure_score == d("0.583333")
    assert tuple(row.event_id for row in digest_report.rows) == (
        "nba-finals-game-7",
        "nba-semis-game-6",
        "nba-regular-game-82",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.pressure_status == "blocked"
    assert blocked.foul_rate_delta_per_game == d("7.000000")
    assert blocked.absolute_foul_rate_delta_per_game == d("7.000000")
    assert blocked.absolute_late_game_foul_delta_per_game == d("3.500000")
    assert blocked.pressure_score == d("1.000000")
    assert blocked.observed_at == datetime(2026, 7, 5, 19, 50, tzinfo=UTC)
    assert blocked.source_age_seconds == d("600.000000")
    assert blocked.reason_codes == (
        "basketball_referee_foul_pressure_blocked",
        "basketball_referee_foul_pressure_late_game_delta",
        "basketball_referee_foul_pressure_rate_delta",
        "basketball_referee_foul_pressure_source_fresh",
    )
    assert watched.pressure_status == "watch"
    assert watched.pressure_score == d("0.583333")
    assert watched.reason_codes == (
        "basketball_referee_foul_pressure_rate_delta",
        "basketball_referee_foul_pressure_source_fresh",
        "basketball_referee_foul_pressure_watch",
    )
    assert passed.pressure_status == "pass"
    assert passed.reason_codes == (
        "basketball_referee_foul_pressure_below_threshold",
        "basketball_referee_foul_pressure_source_fresh",
    )


def test_rows_and_public_tuples_are_canonical_and_deterministic() -> None:
    first = observation(
        "source-watch-b",
        event_id="beta-watch",
        crew_fouls_per_game="21.500000",
        league_fouls_per_game="18.000000",
    )
    second = observation(
        "source-blocked",
        event_id="alpha-blocked",
        crew_fouls_per_game="25.000000",
        league_fouls_per_game="18.000000",
    )
    third = observation(
        "source-watch-a",
        event_id="alpha-watch",
        crew_fouls_per_game="21.500000",
        league_fouls_per_game="18.000000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.event_id for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "beta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert forward.reason_codes == tuple(sorted(forward.reason_codes))
    assert tuple(item.reason_code for item in forward.reason_code_counts) == tuple(
        sorted(item.reason_code for item in forward.reason_code_counts),
    )

    with pytest.raises(ValueError, match="rows must be a tuple"):
        replace(forward, rows=list(forward.rows))
    with pytest.raises(ValueError, match="rows must be sorted"):
        replace(forward, rows=tuple(reversed(forward.rows)))
    with pytest.raises(ValueError, match="reason_code_counts must be a tuple"):
        replace(forward, reason_code_counts=list(forward.reason_code_counts))
    with pytest.raises(ValueError, match="reason_code_counts must be sorted"):
        replace(forward, reason_code_counts=tuple(reversed(forward.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(forward, reason_codes=list(forward.reason_codes))
    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        replace(forward.rows[0], reason_codes=tuple(reversed(forward.rows[0].reason_codes)))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(forward.rows[0], reason_codes=list(forward.rows[0].reason_codes))
    with pytest.raises(ValueError, match="upstream_reason_codes must be a tuple"):
        observation(upstream_reason_codes=["official_box_score"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="upstream_reason_codes must be sorted"):
        observation(upstream_reason_codes=("official_box_score", "arena_feed"))


def test_non_default_thresholds_can_downgrade_moderate_referee_pressure() -> None:
    module = digest()
    cfg = module.BasketballRefereeFoulRatePressureDigestConfig(
        watch_foul_rate_delta_per_game=d("5.000000"),
        blocked_foul_rate_delta_per_game=d("8.000000"),
        watch_late_game_foul_delta_per_game=d("4.000000"),
        blocked_late_game_foul_delta_per_game=d("6.000000"),
    )

    digest_report = report(
        observation(
            "source-moderate",
            crew_fouls_per_game="21.500000",
            league_fouls_per_game="18.000000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_basketball_referee_foul_rate_pressure_screening"
    )
    assert digest_report.rows[0].pressure_status == "pass"
    assert digest_report.rows[0].pressure_score == d("0.437500")
    assert digest_report.rows[0].reason_codes == (
        "basketball_referee_foul_pressure_below_threshold",
        "basketball_referee_foul_pressure_source_fresh",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    for class_name in (
        "BasketballRefereeFoulRatePressureDigestConfig",
        "BasketballRefereeFoulRatePressureObservation",
        "BasketballRefereeFoulRatePressureDigestRow",
        "BasketballRefereeFoulRatePressureReasonCodeCount",
        "BasketballRefereeFoulRatePressureDigestReport",
    ):
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"Bad{class_name}", (getattr(module, class_name),), {})

    with pytest.raises(ValueError, match="watch_foul_rate_delta_per_game must be a Decimal"):
        module.BasketballRefereeFoulRatePressureDigestConfig(
            watch_foul_rate_delta_per_game=_DecimalSubclass("3.000000"),
        )
    with pytest.raises(
        ValueError,
        match="watch_foul_rate_delta_per_game must use six-decimal precision",
    ):
        module.BasketballRefereeFoulRatePressureDigestConfig(
            watch_foul_rate_delta_per_game=d("3"),
        )
    with pytest.raises(ValueError, match="crew_fouls_per_game must be a Decimal"):
        observation(crew_fouls_per_game=_DecimalSubclass("19.000000"))
    with pytest.raises(ValueError, match="crew_fouls_per_game must use six-decimal precision"):
        observation(crew_fouls_per_game=d("19"))
    with pytest.raises(ValueError, match="lookback_games must be nonnegative"):
        observation(lookback_games="-1.000000")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 5, 19, 50))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_basketball_referee_foul_rate_pressure_digest(
            (),
            config=module.BasketballRefereeFoulRatePressureDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 5, 20, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="rows must contain"):
        replace(report(observation("source-row-type")), rows=("not-a-row",))
    with pytest.raises(ValueError, match="reason_code_counts must contain"):
        replace(
            report(observation("source-count-type")),
            reason_code_counts=("not-a-count",),
        )
    with pytest.raises(ValueError, match="watch_foul_rate_delta_per_game"):
        module.BasketballRefereeFoulRatePressureDigestConfig(
            watch_foul_rate_delta_per_game=d("9.000000"),
            blocked_foul_rate_delta_per_game=d("8.000000"),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(
            observation(
                "source-future",
                observed_at=datetime(2026, 7, 5, 20, 1, tzinfo=UTC),
            ),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="pressure_score must be a Decimal"):
        replace(valid_row, pressure_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="pressure_score must use six-decimal precision"):
        replace(valid_row, pressure_score=d("0.1"))
    with pytest.raises(ValueError, match="pressure_score must match row factors"):
        replace(valid_row, pressure_score=d("0.999000"))
    with pytest.raises(ValueError, match="pressure_status must match reason_codes"):
        replace(
            valid_row,
            reason_codes=("basketball_referee_foul_pressure_watch",),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_payload_revalidates_nested_public_records_and_rejects_non_utc_payload_time() -> None:
    module = digest()
    digest_report = report(observation("source-payload-utc"))

    object.__setattr__(
        digest_report.rows[0],
        "observed_at",
        datetime(2026, 7, 5, 15, 50, tzinfo=timezone(timedelta(hours=-4))),
    )

    with pytest.raises(ValueError, match="observed_at must be UTC before payload serialization"):
        module.market_research_basketball_referee_foul_rate_pressure_digest_payload(
            digest_report,
        )


def test_hard_flags_are_enforced_on_config_rows_reason_counts_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)
    assert all(
        item.paper_only and item.report_only and item.readonly
        for item in digest_report.reason_code_counts
    )

    for flag_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=f"config {flag_name} must be True"):
            module.BasketballRefereeFoulRatePressureDigestConfig(
                **{flag_name: False},
            )
        with pytest.raises(ValueError, match=f"observation {flag_name} must be True"):
            replace(observation(f"source-observation-{flag_name}"), **{flag_name: False})
        with pytest.raises(ValueError, match=f"row {flag_name} must be True"):
            replace(digest_report.rows[0], **{flag_name: False})
        with pytest.raises(
            ValueError,
            match=f"reason_code_count {flag_name} must be True",
        ):
            replace(digest_report.reason_code_counts[0], **{flag_name: False})
        with pytest.raises(ValueError, match=f"report {flag_name} must be True"):
            replace(digest_report, **{flag_name: False})
    with pytest.raises(ValueError, match="count must be positive"):
        module.BasketballRefereeFoulRatePressureReasonCodeCount(
            reason_code="basketball_referee_foul_pressure_digest_empty",
            count=d("0.000000"),
            row_ratio=d("0.000000"),
        )


def test_payload_uses_string_numerics_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_basketball_referee_foul_rate_pressure_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["crew_fouls_per_game"] == "19.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-05T19:50:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                assert "secret" not in lowered
                assert "token" not in lowered
                assert "order" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    forbidden_field_names = {"market_slug", "question", "payload_json"}
    for public_record in (
        module.BasketballRefereeFoulRatePressureDigestConfig(),
        observation("source-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        assert forbidden_field_names.isdisjoint(
            {field.name for field in fields(public_record)},
        )
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_basketball_referee_foul_rate_pressure_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
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
        "pathlib",
        "sqlite",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    source_lower = source.lower()
    for forbidden in (
        "asdict",
        "private_key",
        "wallet",
        "urlopen",
        "connect(",
        "execute(",
        "live trading",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange mutation",
        "auth_token",
        "secret_key",
        "market_slug",
        "question",
        "payload_json",
    ):
        assert forbidden not in source_lower


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
