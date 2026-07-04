from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 3, 23, 30, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_basketball_shootaround_participation_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_basketball_shootaround_participation_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "beat-alpha",
    *,
    team_slug: str = "nyk",
    player_slug: str = "jalen-brunson",
    opponent_slug: str = "bos",
    market_slug: str = "jalen-brunson-over-26-5-points",
    participation_score: str | Decimal = "0.720000",
    noncontact_participation_flag: str | Decimal = "0.000000",
    minutes_restriction_probability: str | Decimal = "0.180000",
    injury_report_age_minutes: str | Decimal = "45.000000",
    beat_source_confirmation_count: str | Decimal = "2.000000",
    source_disagreement_count: str | Decimal = "0.000000",
    time_to_tip_minutes: str | Decimal = "210.000000",
    observed_at: datetime = datetime(2026, 7, 3, 22, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("beat_shootaround_note",),
):
    module = api()
    return module.BasketballShootaroundParticipationObservation(
        source_id=source_id,
        team_slug=team_slug,
        player_slug=player_slug,
        opponent_slug=opponent_slug,
        market_slug=market_slug,
        participation_score=(
            participation_score
            if isinstance(participation_score, Decimal)
            else d(participation_score)
        ),
        noncontact_participation_flag=(
            noncontact_participation_flag
            if isinstance(noncontact_participation_flag, Decimal)
            else d(noncontact_participation_flag)
        ),
        minutes_restriction_probability=(
            minutes_restriction_probability
            if isinstance(minutes_restriction_probability, Decimal)
            else d(minutes_restriction_probability)
        ),
        injury_report_age_minutes=(
            injury_report_age_minutes
            if isinstance(injury_report_age_minutes, Decimal)
            else d(injury_report_age_minutes)
        ),
        beat_source_confirmation_count=(
            beat_source_confirmation_count
            if isinstance(beat_source_confirmation_count, Decimal)
            else d(beat_source_confirmation_count)
        ),
        source_disagreement_count=(
            source_disagreement_count
            if isinstance(source_disagreement_count, Decimal)
            else d(source_disagreement_count)
        ),
        time_to_tip_minutes=(
            time_to_tip_minutes
            if isinstance(time_to_tip_minutes, Decimal)
            else d(time_to_tip_minutes)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = api()
    return module.build_market_research_basketball_shootaround_participation_digest(
        rows,
        config=cfg or module.BasketballShootaroundParticipationDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )


def assert_no_floats_or_public_objects(value: object) -> None:
    if isinstance(value, (Decimal, datetime, float)):
        raise AssertionError(f"non-json payload value found: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_floats_or_public_objects(item)
    if isinstance(value, list):
        for item in value:
            assert_no_floats_or_public_objects(item)


def test_empty_input_returns_blocked_report_only_zero_digest() -> None:
    module = api()

    digest_report = report()

    assert isinstance(digest_report, module.BasketballShootaroundParticipationDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-basketball-shootaround-participation-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_basketball_shootaround_participation_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.noncontact_count == d("0.000000")
    assert digest_report.minutes_restriction_risk_count == d("0.000000")
    assert digest_report.stale_injury_report_count == d("0.000000")
    assert digest_report.low_confirmation_count == d("0.000000")
    assert digest_report.source_disagreement_row_count == d("0.000000")
    assert digest_report.late_to_tip_count == d("0.000000")
    assert digest_report.max_participation_score == d("0.000000")
    assert digest_report.average_participation_score == d("0.000000")
    assert digest_report.shootaround_risk_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == (
        "basketball_shootaround_participation_digest_empty",
    )
    assert digest_report.reason_code_counts == (
        module.BasketballShootaroundParticipationReasonCodeCount(
            reason_code="basketball_shootaround_participation_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_high_risk_shootaround_signal_blocks_event_screening() -> None:
    digest_report = report(
        observation(
            "beat-limited",
            market_slug="jalen-brunson-over-26-5-points",
            participation_score="0.920000",
            noncontact_participation_flag="1.000000",
            minutes_restriction_probability="0.740000",
            injury_report_age_minutes="260.000000",
            beat_source_confirmation_count="1.000000",
            source_disagreement_count="2.000000",
            time_to_tip_minutes="45.000000",
            observed_at=datetime(2026, 7, 3, 18, 0, tzinfo=timezone(timedelta(hours=-4))),
        ),
        observation(
            "beat-minutes-watch",
            player_slug="jaylen-brown",
            market_slug="jaylen-brown-over-22-5-points",
            participation_score="0.680000",
            minutes_restriction_probability="0.420000",
            time_to_tip_minutes="90.000000",
            observed_at=datetime(2026, 7, 3, 22, 15, tzinfo=UTC),
        ),
        observation(
            "beat-clear",
            player_slug="derrick-white",
            market_slug="derrick-white-over-4-5-assists",
            participation_score="0.310000",
            minutes_restriction_probability="0.050000",
            injury_report_age_minutes="20.000000",
            beat_source_confirmation_count="3.000000",
            time_to_tip_minutes="260.000000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_basketball_shootaround_participation_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.noncontact_count == d("1.000000")
    assert digest_report.minutes_restriction_risk_count == d("2.000000")
    assert digest_report.stale_injury_report_count == d("1.000000")
    assert digest_report.low_confirmation_count == d("1.000000")
    assert digest_report.source_disagreement_row_count == d("1.000000")
    assert digest_report.late_to_tip_count == d("2.000000")
    assert digest_report.max_participation_score == d("0.920000")
    assert digest_report.average_participation_score == d("0.636667")
    assert digest_report.shootaround_risk_score == d("1.000000")
    assert digest_report.reason_codes == (
        "basketball_shootaround_blocked_signal_present",
        "basketball_shootaround_late_to_tip_present",
        "basketball_shootaround_low_confirmation_present",
        "basketball_shootaround_minutes_restriction_present",
        "basketball_shootaround_noncontact_participation_present",
        "basketball_shootaround_source_disagreement_present",
        "basketball_shootaround_stale_injury_report_present",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "jalen-brunson-over-26-5-points",
        "jaylen-brown-over-22-5-points",
        "derrick-white-over-4-5-assists",
    )

    blocked, watch, passed = digest_report.rows
    assert blocked.shootaround_status == "blocked"
    assert blocked.observed_at == datetime(2026, 7, 3, 22, 0, tzinfo=UTC)
    assert blocked.row_risk_score == d("1.000000")
    assert blocked.reason_codes == (
        "basketball_shootaround_blocked_participation_score",
        "basketball_shootaround_late_to_tip",
        "basketball_shootaround_low_beat_confirmation",
        "basketball_shootaround_minutes_restriction_blocked",
        "basketball_shootaround_noncontact_participation",
        "basketball_shootaround_source_disagreement",
        "basketball_shootaround_stale_injury_report",
    )
    assert watch.shootaround_status == "watch"
    assert watch.row_risk_score == d("0.500000")
    assert watch.reason_codes == (
        "basketball_shootaround_late_to_tip",
        "basketball_shootaround_minutes_restriction_watch",
        "basketball_shootaround_watch_participation_score",
    )
    assert passed.shootaround_status == "pass"
    assert passed.reason_codes == ("basketball_shootaround_participation_inline",)


def test_rows_reason_codes_and_reason_counts_are_sorted_deterministically() -> None:
    first = observation(
        "beat-watch-beta",
        market_slug="beta-watch-market",
        participation_score="0.650000",
        minutes_restriction_probability="0.410000",
    )
    second = observation(
        "beat-blocked-alpha",
        market_slug="alpha-blocked-market",
        participation_score="0.910000",
        noncontact_participation_flag="1.000000",
        minutes_restriction_probability="0.660000",
    )
    third = observation(
        "beat-watch-alpha",
        market_slug="alpha-watch-market",
        participation_score="0.650000",
        minutes_restriction_probability="0.410000",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked-market",
        "alpha-watch-market",
        "beta-watch-market",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(sorted(row.reason_codes))
    assert forward.reason_codes == tuple(sorted(forward.reason_codes))
    assert tuple(item.reason_code for item in forward.reason_code_counts) == tuple(
        sorted(item.reason_code for item in forward.reason_code_counts),
    )


def test_non_default_thresholds_can_downgrade_moderate_signal() -> None:
    module = api()
    cfg = module.BasketballShootaroundParticipationDigestConfig(
        watch_participation_score=d("0.800000"),
        blocked_participation_score=d("0.950000"),
        watch_minutes_restriction_probability=d("0.600000"),
        blocked_minutes_restriction_probability=d("0.900000"),
        stale_injury_report_age_minutes=d("500.000000"),
        minimum_beat_source_confirmation_count=d("1.000000"),
        blocked_source_disagreement_count=d("3.000000"),
        late_to_tip_minutes=d("30.000000"),
    )

    digest_report = report(
        observation(
            "beat-moderate",
            participation_score="0.720000",
            minutes_restriction_probability="0.420000",
            time_to_tip_minutes="90.000000",
        ),
        cfg=cfg,
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_basketball_shootaround_participation_screening"
    )
    assert digest_report.rows[0].shootaround_status == "pass"
    assert digest_report.rows[0].reason_codes == (
        "basketball_shootaround_participation_inline",
    )
    assert digest_report.shootaround_risk_score == d("0.000000")
    assert digest_report.reason_codes == (
        "basketball_shootaround_participation_digest_clear",
    )


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = api()

    with pytest.raises(ValueError, match="participation_score must be a Decimal"):
        observation(participation_score=_DecimalSubclass("0.720000"))
    with pytest.raises(ValueError, match="noncontact_participation_flag must be 0 or 1"):
        observation(noncontact_participation_flag="0.500000")
    with pytest.raises(ValueError, match="minutes_restriction_probability must be between"):
        observation(minutes_restriction_probability="1.200000")
    with pytest.raises(ValueError, match="injury_report_age_minutes must be nonnegative"):
        observation(injury_report_age_minutes="-1.000000")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 3, 22, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_basketball_shootaround_participation_digest(
            (),
            config=module.BasketballShootaroundParticipationDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 3, 23, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("beat-dupe"), observation("beat-dupe"))
    with pytest.raises(ValueError, match="watch_participation_score"):
        module.BasketballShootaroundParticipationDigestConfig(
            watch_participation_score=d("0.950000"),
            blocked_participation_score=d("0.900000"),
        )

    valid_row = report(observation("beat-valid")).rows[0]
    with pytest.raises(ValueError, match="row_risk_score must match"):
        replace(valid_row, row_risk_score=d("0.990000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "basketball_shootaround_participation_inline",
                "basketball_shootaround_watch_participation_score",
            ),
        )

    frozen_observation = observation("beat-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_observations_rows_counts_and_report() -> None:
    module = api()

    digest_report = report(observation("beat-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)
    assert all(
        count.paper_only and count.report_only and count.readonly
        for count in digest_report.reason_code_counts
    )

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.BasketballShootaroundParticipationDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("beat-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="reason code count readonly must be True"):
        replace(digest_report.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_canonical_string_numerics_and_module_has_no_live_surfaces() -> None:
    module = api()
    digest_report = report(
        observation(
            "beat-payload",
            participation_score="0.7254321",
            observed_at=datetime(2026, 7, 3, 18, 0, tzinfo=timezone(timedelta(hours=-4))),
        ),
    )

    payload = module.market_research_basketball_shootaround_participation_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["participation_score"] == "0.725432"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T22:00:00+00:00"
    assert payload["rows"][0]["upstream_reason_codes"] == ["beat_shootaround_note"]
    assert_no_floats_or_public_objects(payload)

    for public_record in (
        module.BasketballShootaroundParticipationDigestConfig(),
        observation("beat-dataclass"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if _is_public_numeric(field_value):
                assert type(field_value) is Decimal, field.name

    source = MODULE_PATH.read_text()
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
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
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
        "os.environ",
        "getenv",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
