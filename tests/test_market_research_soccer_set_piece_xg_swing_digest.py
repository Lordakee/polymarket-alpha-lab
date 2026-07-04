from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 20, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def digest():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_soccer_set_piece_xg_swing_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    source_id: str = "source-alpha",
    *,
    match_id: str = "match-alpha",
    market_slug: str = "club-alpha-v-club-beta",
    club: str = "club-alpha",
    opponent: str = "club-beta",
    baseline_set_piece_xg: str | Decimal = "0.300000",
    projected_set_piece_xg: str | Decimal = "0.460000",
    set_piece_xg_share: str | Decimal = "0.380000",
    corner_pressure_delta: str | Decimal = "3.500000",
    aerial_mismatch_score: str | Decimal = "0.450000",
    foul_zone_entry_delta: str | Decimal = "2.000000",
    primary_taker_change_signal: str | Decimal = "0.300000",
    observed_at: datetime = datetime(2026, 7, 4, 18, 0, tzinfo=UTC),
    upstream_reason_codes: tuple[str, ...] = ("official_match_context",),
):
    module = digest()
    return module.SoccerSetPieceXgSwingObservation(
        source_id=source_id,
        match_id=match_id,
        market_slug=market_slug,
        club=club,
        opponent=opponent,
        baseline_set_piece_xg=(
            baseline_set_piece_xg
            if isinstance(baseline_set_piece_xg, Decimal)
            else d(baseline_set_piece_xg)
        ),
        projected_set_piece_xg=(
            projected_set_piece_xg
            if isinstance(projected_set_piece_xg, Decimal)
            else d(projected_set_piece_xg)
        ),
        set_piece_xg_share=(
            set_piece_xg_share
            if isinstance(set_piece_xg_share, Decimal)
            else d(set_piece_xg_share)
        ),
        corner_pressure_delta=(
            corner_pressure_delta
            if isinstance(corner_pressure_delta, Decimal)
            else d(corner_pressure_delta)
        ),
        aerial_mismatch_score=(
            aerial_mismatch_score
            if isinstance(aerial_mismatch_score, Decimal)
            else d(aerial_mismatch_score)
        ),
        foul_zone_entry_delta=(
            foul_zone_entry_delta
            if isinstance(foul_zone_entry_delta, Decimal)
            else d(foul_zone_entry_delta)
        ),
        primary_taker_change_signal=(
            primary_taker_change_signal
            if isinstance(primary_taker_change_signal, Decimal)
            else d(primary_taker_change_signal)
        ),
        observed_at=observed_at,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(*rows: object, cfg: object | None = None):
    module = digest()
    return module.build_market_research_soccer_set_piece_xg_swing_digest(
        rows,
        config=cfg or module.SoccerSetPieceXgSwingDigestConfig(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=2))),
    )


def test_empty_input_returns_report_only_blocked_zero_digest() -> None:
    module = digest()

    digest_report = report()

    assert isinstance(digest_report, module.SoccerSetPieceXgSwingDigestReport)
    assert is_dataclass(digest_report)
    assert digest_report.__dataclass_params__.frozen
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.config_version == (
        "market-research-soccer-set-piece-xg-swing-digest-v0"
    )
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_soccer_set_piece_xg_swing_screening"
    )
    assert digest_report.input_count == d("0.000000")
    assert digest_report.row_count == d("0.000000")
    assert digest_report.blocked_count == d("0.000000")
    assert digest_report.watch_count == d("0.000000")
    assert digest_report.pass_count == d("0.000000")
    assert digest_report.material_xg_delta_count == d("0.000000")
    assert digest_report.high_set_piece_share_count == d("0.000000")
    assert digest_report.corner_pressure_count == d("0.000000")
    assert digest_report.aerial_mismatch_count == d("0.000000")
    assert digest_report.foul_zone_pressure_count == d("0.000000")
    assert digest_report.primary_taker_change_count == d("0.000000")
    assert digest_report.max_xg_swing_pressure_score == d("0.000000")
    assert digest_report.average_xg_swing_pressure_score == d("0.000000")
    assert digest_report.max_absolute_set_piece_xg_delta == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_codes == ("soccer_set_piece_xg_swing_digest_empty",)
    assert digest_report.reason_code_counts == (
        module.SoccerSetPieceXgSwingReasonCodeCount(
            reason_code="soccer_set_piece_xg_swing_digest_empty",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True


def test_compounded_set_piece_xg_pressure_blocks_market_screening() -> None:
    digest_report = report(
        observation(
            "source-blocked",
            match_id="match-blocked",
            market_slug="corner-mismatch-market",
            club="club-corners",
            baseline_set_piece_xg="0.180000",
            projected_set_piece_xg="0.420000",
            set_piece_xg_share="0.440000",
            corner_pressure_delta="5.500000",
            aerial_mismatch_score="0.820000",
            foul_zone_entry_delta="5.500000",
            primary_taker_change_signal="0.850000",
        ),
        observation(
            "source-watch",
            match_id="match-watch",
            market_slug="set-piece-watch-market",
            baseline_set_piece_xg="0.240000",
            projected_set_piece_xg="0.390000",
            set_piece_xg_share="0.370000",
            corner_pressure_delta="3.200000",
            aerial_mismatch_score="0.200000",
            foul_zone_entry_delta="1.000000",
            primary_taker_change_signal="0.100000",
            observed_at=datetime(2026, 7, 4, 10, 15, tzinfo=timezone(timedelta(hours=-4))),
        ),
        observation(
            "source-pass",
            match_id="match-pass",
            market_slug="low-set-piece-baseline",
            baseline_set_piece_xg="0.250000",
            projected_set_piece_xg="0.280000",
            set_piece_xg_share="0.200000",
            corner_pressure_delta="0.500000",
            aerial_mismatch_score="0.100000",
            foul_zone_entry_delta="-1.000000",
            primary_taker_change_signal="0.000000",
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == (
        "block_report_only_soccer_set_piece_xg_swing_screening"
    )
    assert digest_report.input_count == d("3.000000")
    assert digest_report.row_count == d("3.000000")
    assert digest_report.blocked_count == d("1.000000")
    assert digest_report.watch_count == d("1.000000")
    assert digest_report.pass_count == d("1.000000")
    assert digest_report.material_xg_delta_count == d("2.000000")
    assert digest_report.high_set_piece_share_count == d("2.000000")
    assert digest_report.corner_pressure_count == d("2.000000")
    assert digest_report.aerial_mismatch_count == d("1.000000")
    assert digest_report.foul_zone_pressure_count == d("1.000000")
    assert digest_report.primary_taker_change_count == d("1.000000")
    assert digest_report.max_xg_swing_pressure_score == d("1.000000")
    assert digest_report.average_xg_swing_pressure_score == d("0.500000")
    assert digest_report.max_absolute_set_piece_xg_delta == d("0.240000")
    assert digest_report.reason_codes == (
        "soccer_set_piece_xg_swing_blocked_present",
        "soccer_set_piece_xg_swing_delta_present",
        "soccer_set_piece_xg_swing_share_present",
        "soccer_set_piece_xg_swing_corner_pressure_present",
        "soccer_set_piece_xg_swing_aerial_mismatch_present",
        "soccer_set_piece_xg_swing_foul_zone_present",
        "soccer_set_piece_xg_swing_taker_change_present",
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "corner-mismatch-market",
        "set-piece-watch-market",
        "low-set-piece-baseline",
    )

    blocked, watched, passed = digest_report.rows
    assert blocked.xg_swing_status == "blocked"
    assert blocked.set_piece_xg_delta == d("0.240000")
    assert blocked.xg_swing_pressure_score == d("1.000000")
    assert blocked.observed_at == datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
    assert blocked.reason_codes == (
        "soccer_set_piece_xg_swing_set_piece_xg_delta",
        "soccer_set_piece_xg_swing_high_set_piece_share",
        "soccer_set_piece_xg_swing_corner_pressure_delta",
        "soccer_set_piece_xg_swing_aerial_mismatch",
        "soccer_set_piece_xg_swing_foul_zone_pressure",
        "soccer_set_piece_xg_swing_primary_taker_change",
        "soccer_set_piece_xg_swing_blocked",
    )
    assert watched.xg_swing_status == "watch"
    assert watched.observed_at == datetime(2026, 7, 4, 14, 15, tzinfo=UTC)
    assert watched.xg_swing_pressure_score == d("0.500000")
    assert watched.reason_codes == (
        "soccer_set_piece_xg_swing_set_piece_xg_delta",
        "soccer_set_piece_xg_swing_high_set_piece_share",
        "soccer_set_piece_xg_swing_corner_pressure_delta",
        "soccer_set_piece_xg_swing_watch",
    )
    assert passed.xg_swing_status == "pass"
    assert passed.xg_swing_pressure_score == d("0.000000")
    assert passed.reason_codes == ("soccer_set_piece_xg_swing_clear",)

    assert tuple(item.reason_code for item in digest_report.reason_code_counts) == (
        "soccer_set_piece_xg_swing_blocked_present",
        "soccer_set_piece_xg_swing_delta_present",
        "soccer_set_piece_xg_swing_share_present",
        "soccer_set_piece_xg_swing_corner_pressure_present",
        "soccer_set_piece_xg_swing_aerial_mismatch_present",
        "soccer_set_piece_xg_swing_foul_zone_present",
        "soccer_set_piece_xg_swing_taker_change_present",
    )
    assert tuple(item.count for item in digest_report.reason_code_counts) == (
        d("1.000000"),
        d("2.000000"),
        d("2.000000"),
        d("2.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
    )


def test_rows_and_reason_codes_are_sorted_deterministically() -> None:
    first = observation(
        "source-watch-b",
        match_id="match-watch-b",
        market_slug="zeta-watch",
    )
    second = observation(
        "source-blocked",
        match_id="match-blocked",
        market_slug="alpha-blocked",
        baseline_set_piece_xg="0.180000",
        projected_set_piece_xg="0.420000",
        set_piece_xg_share="0.440000",
        corner_pressure_delta="5.500000",
        aerial_mismatch_score="0.820000",
        foul_zone_entry_delta="5.500000",
        primary_taker_change_signal="0.850000",
    )
    third = observation(
        "source-watch-a",
        match_id="match-watch-a",
        market_slug="alpha-watch",
    )

    forward = report(first, second, third)
    reverse = report(third, second, first)

    assert forward == reverse
    assert tuple(row.market_slug for row in forward.rows) == (
        "alpha-blocked",
        "alpha-watch",
        "zeta-watch",
    )
    for row in forward.rows:
        assert row.reason_codes == tuple(
            sorted(
                row.reason_codes,
                key=digest().ROW_REASON_CODES.index,
            ),
        )
    assert forward.reason_codes == (
        "soccer_set_piece_xg_swing_blocked_present",
        "soccer_set_piece_xg_swing_delta_present",
        "soccer_set_piece_xg_swing_share_present",
        "soccer_set_piece_xg_swing_corner_pressure_present",
        "soccer_set_piece_xg_swing_aerial_mismatch_present",
        "soccer_set_piece_xg_swing_foul_zone_present",
        "soccer_set_piece_xg_swing_taker_change_present",
    )


def test_non_default_thresholds_can_downgrade_moderate_xg_swing() -> None:
    module = digest()
    cfg = module.SoccerSetPieceXgSwingDigestConfig(
        material_set_piece_xg_delta=d("0.200000"),
        high_set_piece_xg_share=d("0.450000"),
        corner_pressure_delta=d("5.000000"),
        watch_xg_swing_signal_count=d("4.000000"),
        blocked_xg_swing_signal_count=d("6.000000"),
    )

    digest_report = report(observation("source-moderate"), cfg=cfg)

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == (
        "allow_report_only_soccer_set_piece_xg_swing_screening"
    )
    assert digest_report.rows[0].xg_swing_status == "pass"
    assert digest_report.rows[0].reason_codes == ("soccer_set_piece_xg_swing_clear",)
    assert digest_report.max_xg_swing_pressure_score == d("0.000000")
    assert digest_report.reason_codes == ("soccer_set_piece_xg_swing_digest_clear",)


def test_validation_rejects_bad_inputs_and_inconsistent_public_records() -> None:
    module = digest()

    with pytest.raises(ValueError, match="baseline_set_piece_xg must be a Decimal"):
        observation(baseline_set_piece_xg=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="set_piece_xg_share must be no greater than one"):
        observation(set_piece_xg_share="1.500000")
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 4, 18, 0))
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_market_research_soccer_set_piece_xg_swing_digest(
            (),
            config=module.SoccerSetPieceXgSwingDigestConfig(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 20, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observations must contain"):
        report("not-an-observation")
    with pytest.raises(ValueError, match="duplicate source_id"):
        report(observation("source-dupe"), observation("source-dupe"))
    with pytest.raises(ValueError, match="watch_xg_swing_signal_count"):
        module.SoccerSetPieceXgSwingDigestConfig(
            watch_xg_swing_signal_count=d("5.000000"),
            blocked_xg_swing_signal_count=d("4.000000"),
        )

    valid_row = report(observation("source-valid")).rows[0]
    with pytest.raises(ValueError, match="absolute_set_piece_xg_delta must match"):
        replace(valid_row, absolute_set_piece_xg_delta=d("999.000000"))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(
            valid_row,
            reason_codes=(
                "soccer_set_piece_xg_swing_clear",
                "soccer_set_piece_xg_swing_blocked",
            ),
        )

    frozen_observation = observation("source-frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.source_id = "changed"  # type: ignore[misc]


def test_hard_flags_are_enforced_on_config_rows_counts_and_report() -> None:
    module = digest()

    digest_report = report(observation("source-hard-flags"))
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert all(row.paper_only and row.report_only and row.readonly for row in digest_report.rows)
    assert all(
        count.paper_only and count.report_only and count.readonly
        for count in digest_report.reason_code_counts
    )

    with pytest.raises(ValueError, match="config paper_only must be True"):
        module.SoccerSetPieceXgSwingDigestConfig(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("source-report-only"), report_only=False)
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(digest_report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(digest_report, paper_only=False)


def test_payload_uses_six_decimal_strings_and_module_has_no_durable_or_live_surfaces() -> None:
    module = digest()
    digest_report = report(observation("source-payload"))

    payload = module.market_research_soccer_set_piece_xg_swing_digest_payload(
        digest_report,
    )

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["input_count"] == "1.000000"
    assert payload["rows"][0]["baseline_set_piece_xg"] == "0.300000"
    assert payload["rows"][0]["set_piece_xg_delta"] == "0.160000"
    assert payload["rows"][0]["xg_swing_pressure_score"] == "0.500000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T18:00:00+00:00"

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                assert "private_key" not in lowered
                assert "wallet" not in lowered
                assert "auth" not in lowered
                assert "order" not in lowered
                assert "cancel" not in lowered
                assert "replace" not in lowered
                assert "exchange" not in lowered
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))

    walk_payload(payload)

    for public_record in (
        module.SoccerSetPieceXgSwingDigestConfig(),
        observation("source-dataclass"),
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

    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_soccer_set_piece_xg_swing_digest.py",
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
        "cancel(",
        "exchange",
    ):
        assert forbidden not in source.lower()


def _is_public_numeric(value: object) -> bool:
    return isinstance(value, Decimal)
