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

from polymarket_alpha_lab.market_research_baseball_late_scratch_lineup_gap_digest import (
    DEFAULT_MARKET_RESEARCH_BASEBALL_LATE_SCRATCH_LINEUP_GAP_DIGEST_CONFIG_VERSION,
    MarketResearchBaseballLateScratchLineupGapDigest,
    MarketResearchBaseballLateScratchLineupGapDigestConfig,
    MarketResearchBaseballLateScratchLineupGapDigestInputRow,
    MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount,
    MarketResearchBaseballLateScratchLineupGapDigestRow,
    build_market_research_baseball_late_scratch_lineup_gap_digest,
    market_research_baseball_late_scratch_lineup_gap_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 21, 0, tzinfo=UTC)
FIRST_PITCH = datetime(2026, 7, 4, 22, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(
    **overrides: object,
) -> MarketResearchBaseballLateScratchLineupGapDigestConfig:
    values: dict[str, object] = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_BASEBALL_LATE_SCRATCH_LINEUP_GAP_DIGEST_CONFIG_VERSION
        ),
        "max_watch_minutes_to_first_pitch": d("60.000000"),
        "max_blocked_minutes_to_first_pitch": d("20.000000"),
        "max_lineup_confirmation_age_minutes": d("30.000000"),
        "min_scratched_player_impact_score": d("0.700000"),
        "max_substitute_quality_score": d("0.450000"),
        "min_quality_gap_score": d("0.250000"),
        "min_pitcher_handedness_fit_score": d("0.600000"),
        "min_source_disagreement_count": d("2.000000"),
    }
    values.update(overrides)
    return MarketResearchBaseballLateScratchLineupGapDigestConfig(**values)


def _row(
    market_slug: str,
    *,
    team: str = "nyy",
    opponent: str = "bos",
    scratched_player_id: str = "player.cleanup",
    scheduled_first_pitch_at: datetime = FIRST_PITCH,
    lineup_confirmed_at: datetime | None = None,
    source_timestamp_at: datetime | None = None,
    scratched_player_impact_score: Decimal = d("0.200000"),
    substitute_quality_score: Decimal = d("0.800000"),
    pitcher_handedness_fit_score: Decimal = d("0.100000"),
    source_disagreement_count: Decimal = d("0.000000"),
    upstream_reason_codes: tuple[str, ...] = (),
) -> MarketResearchBaseballLateScratchLineupGapDigestInputRow:
    return MarketResearchBaseballLateScratchLineupGapDigestInputRow(
        market_slug=market_slug,
        team=team,
        opponent=opponent,
        scratched_player_id=scratched_player_id,
        scheduled_first_pitch_at=scheduled_first_pitch_at,
        lineup_confirmed_at=lineup_confirmed_at
        or GENERATED_AT - timedelta(minutes=5),
        source_timestamp_at=source_timestamp_at or GENERATED_AT - timedelta(minutes=3),
        scratched_player_impact_score=scratched_player_impact_score,
        substitute_quality_score=substitute_quality_score,
        pitcher_handedness_fit_score=pitcher_handedness_fit_score,
        source_disagreement_count=source_disagreement_count,
        upstream_reason_codes=upstream_reason_codes,
    )


def test_digest_flags_late_scratch_lineup_gap_deterministically() -> None:
    eastern_source_at = datetime(
        2026,
        7,
        4,
        16,
        58,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    digest = build_market_research_baseball_late_scratch_lineup_gap_digest(
        (
            _row(
                "zeta-stale",
                team="sea",
                opponent="tex",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=100),
                lineup_confirmed_at=GENERATED_AT - timedelta(minutes=31),
            ),
            _row(
                "alpha-gap",
                team="nyy",
                opponent="bos",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=20),
                lineup_confirmed_at=GENERATED_AT - timedelta(minutes=10),
                source_timestamp_at=eastern_source_at,
                scratched_player_impact_score=d("0.850000"),
                substitute_quality_score=d("0.300000"),
                pitcher_handedness_fit_score=d("0.750000"),
                source_disagreement_count=d("3.000000"),
                upstream_reason_codes=("club-lineup-delta", "beat-writer-scratch"),
            ),
            _row(
                "beta-watch",
                team="lad",
                opponent="sf",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=55),
                lineup_confirmed_at=GENERATED_AT - timedelta(minutes=20),
                source_timestamp_at=GENERATED_AT - timedelta(minutes=8),
                scratched_player_impact_score=d("0.720000"),
                substitute_quality_score=d("0.600000"),
                pitcher_handedness_fit_score=d("0.500000"),
            ),
            _row(
                "clear-pass",
                team="ari",
                opponent="col",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=120),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert digest == MarketResearchBaseballLateScratchLineupGapDigest(
        generated_at=GENERATED_AT,
        config_version=(
            DEFAULT_MARKET_RESEARCH_BASEBALL_LATE_SCRATCH_LINEUP_GAP_DIGEST_CONFIG_VERSION
        ),
        digest_status="blocked",
        market_count=d("4.000000"),
        input_row_count=d("4.000000"),
        pass_market_count=d("1.000000"),
        watch_market_count=d("1.000000"),
        blocked_market_count=d("2.000000"),
        late_window_market_count=d("2.000000"),
        critical_timing_market_count=d("1.000000"),
        stale_lineup_confirmation_market_count=d("1.000000"),
        scratched_player_impact_market_count=d("2.000000"),
        substitute_quality_drop_market_count=d("1.000000"),
        quality_gap_market_count=d("1.000000"),
        pitcher_handedness_fit_market_count=d("1.000000"),
        source_disagreement_market_count=d("1.000000"),
        upstream_context_market_count=d("1.000000"),
        risk_score=d("0.850000"),
        max_quality_gap_score=d("0.550000"),
        min_minutes_to_first_pitch=d("20.000000"),
        max_lineup_confirmation_age_minutes=d("31.000000"),
        rows=(
            MarketResearchBaseballLateScratchLineupGapDigestRow(
                market_slug="alpha-gap",
                team="nyy",
                opponent="bos",
                scratched_player_id="player.cleanup",
                row_status="blocked",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=20),
                lineup_confirmed_at=GENERATED_AT - timedelta(minutes=10),
                source_timestamp_at=datetime(2026, 7, 4, 20, 58, tzinfo=UTC),
                minutes_to_first_pitch=d("20.000000"),
                lineup_confirmation_age_minutes=d("10.000000"),
                source_age_minutes=d("2.000000"),
                scratched_player_impact_score=d("0.850000"),
                substitute_quality_score=d("0.300000"),
                quality_gap_score=d("0.550000"),
                pitcher_handedness_fit_score=d("0.750000"),
                source_disagreement_count=d("3.000000"),
                upstream_reason_codes=("beat-writer-scratch", "club-lineup-delta"),
                row_risk_score=d("0.850000"),
                reason_codes=(
                    "baseball_late_scratch_lineup_gap_late_window",
                    "baseball_late_scratch_lineup_gap_critical_timing",
                    "baseball_late_scratch_lineup_gap_scratched_player_impact",
                    "baseball_late_scratch_lineup_gap_substitute_quality_drop",
                    "baseball_late_scratch_lineup_gap_quality_gap",
                    "baseball_late_scratch_lineup_gap_pitcher_handedness_fit",
                    "baseball_late_scratch_lineup_gap_source_disagreement",
                    "baseball_late_scratch_lineup_gap_upstream_context",
                ),
            ),
            MarketResearchBaseballLateScratchLineupGapDigestRow(
                market_slug="beta-watch",
                team="lad",
                opponent="sf",
                scratched_player_id="player.cleanup",
                row_status="watch",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=55),
                lineup_confirmed_at=GENERATED_AT - timedelta(minutes=20),
                source_timestamp_at=GENERATED_AT - timedelta(minutes=8),
                minutes_to_first_pitch=d("55.000000"),
                lineup_confirmation_age_minutes=d("20.000000"),
                source_age_minutes=d("8.000000"),
                scratched_player_impact_score=d("0.720000"),
                substitute_quality_score=d("0.600000"),
                quality_gap_score=d("0.120000"),
                pitcher_handedness_fit_score=d("0.500000"),
                source_disagreement_count=d("0.000000"),
                upstream_reason_codes=(),
                row_risk_score=d("0.220000"),
                reason_codes=(
                    "baseball_late_scratch_lineup_gap_late_window",
                    "baseball_late_scratch_lineup_gap_scratched_player_impact",
                ),
            ),
            MarketResearchBaseballLateScratchLineupGapDigestRow(
                market_slug="clear-pass",
                team="ari",
                opponent="col",
                scratched_player_id="player.cleanup",
                row_status="pass",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=120),
                lineup_confirmed_at=GENERATED_AT - timedelta(minutes=5),
                source_timestamp_at=GENERATED_AT - timedelta(minutes=3),
                minutes_to_first_pitch=d("120.000000"),
                lineup_confirmation_age_minutes=d("5.000000"),
                source_age_minutes=d("3.000000"),
                scratched_player_impact_score=d("0.200000"),
                substitute_quality_score=d("0.800000"),
                quality_gap_score=d("0.000000"),
                pitcher_handedness_fit_score=d("0.100000"),
                source_disagreement_count=d("0.000000"),
                upstream_reason_codes=(),
                row_risk_score=d("0.000000"),
                reason_codes=("baseball_late_scratch_lineup_gap_clear",),
            ),
            MarketResearchBaseballLateScratchLineupGapDigestRow(
                market_slug="zeta-stale",
                team="sea",
                opponent="tex",
                scratched_player_id="player.cleanup",
                row_status="blocked",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=100),
                lineup_confirmed_at=GENERATED_AT - timedelta(minutes=31),
                source_timestamp_at=GENERATED_AT - timedelta(minutes=3),
                minutes_to_first_pitch=d("100.000000"),
                lineup_confirmation_age_minutes=d("31.000000"),
                source_age_minutes=d("3.000000"),
                scratched_player_impact_score=d("0.200000"),
                substitute_quality_score=d("0.800000"),
                quality_gap_score=d("0.000000"),
                pitcher_handedness_fit_score=d("0.100000"),
                source_disagreement_count=d("0.000000"),
                upstream_reason_codes=(),
                row_risk_score=d("0.200000"),
                reason_codes=(
                    "baseball_late_scratch_lineup_gap_stale_lineup_confirmation",
                ),
            ),
        ),
        reason_code_counts=(
            MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
                reason_code="baseball_late_scratch_lineup_gap_late_window",
                market_count=d("2.000000"),
            ),
            MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
                reason_code="baseball_late_scratch_lineup_gap_critical_timing",
                market_count=d("1.000000"),
            ),
            MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
                reason_code="baseball_late_scratch_lineup_gap_stale_lineup_confirmation",
                market_count=d("1.000000"),
            ),
            MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
                reason_code="baseball_late_scratch_lineup_gap_scratched_player_impact",
                market_count=d("2.000000"),
            ),
            MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
                reason_code="baseball_late_scratch_lineup_gap_substitute_quality_drop",
                market_count=d("1.000000"),
            ),
            MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
                reason_code="baseball_late_scratch_lineup_gap_quality_gap",
                market_count=d("1.000000"),
            ),
            MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
                reason_code="baseball_late_scratch_lineup_gap_pitcher_handedness_fit",
                market_count=d("1.000000"),
            ),
            MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
                reason_code="baseball_late_scratch_lineup_gap_source_disagreement",
                market_count=d("1.000000"),
            ),
            MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
                reason_code="baseball_late_scratch_lineup_gap_upstream_context",
                market_count=d("1.000000"),
            ),
        ),
        reason_codes=(
            "baseball_late_scratch_lineup_gap_late_window",
            "baseball_late_scratch_lineup_gap_critical_timing",
            "baseball_late_scratch_lineup_gap_stale_lineup_confirmation",
            "baseball_late_scratch_lineup_gap_scratched_player_impact",
            "baseball_late_scratch_lineup_gap_substitute_quality_drop",
            "baseball_late_scratch_lineup_gap_quality_gap",
            "baseball_late_scratch_lineup_gap_pitcher_handedness_fit",
            "baseball_late_scratch_lineup_gap_source_disagreement",
            "baseball_late_scratch_lineup_gap_upstream_context",
        ),
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_empty_input_returns_blocked_report_only_reason() -> None:
    digest = build_market_research_baseball_late_scratch_lineup_gap_digest(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert digest.digest_status == "blocked"
    assert digest.market_count == d("0.000000")
    assert digest.input_row_count == d("0.000000")
    assert digest.rows == ()
    assert digest.risk_score == d("0.000000")
    assert digest.reason_codes == ("baseball_late_scratch_lineup_gap_rows_missing",)
    assert digest.reason_code_counts == (
        MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount(
            reason_code="baseball_late_scratch_lineup_gap_rows_missing",
            market_count=d("0.000000"),
        ),
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_payload_is_json_ready_decimal_only_and_utc_normalized() -> None:
    digest = build_market_research_baseball_late_scratch_lineup_gap_digest(
        (
            _row(
                "alpha-gap",
                scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=20),
                source_timestamp_at=datetime(
                    2026,
                    7,
                    4,
                    16,
                    58,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                scratched_player_impact_score=d("0.850000"),
                substitute_quality_score=d("0.300000"),
                pitcher_handedness_fit_score=d("0.750000"),
                source_disagreement_count=d("3.000000"),
                upstream_reason_codes=("club-lineup-delta", "beat-writer-scratch"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = market_research_baseball_late_scratch_lineup_gap_digest_payload(digest)

    assert payload["generated_at"] == "2026-07-04T21:00:00+00:00"
    assert payload["market_count"] == "1.000000"
    assert payload["risk_score"] == "0.850000"
    assert payload["rows"][0]["source_timestamp_at"] == "2026-07-04T20:58:00+00:00"
    assert payload["rows"][0]["minutes_to_first_pitch"] == "20.000000"
    assert payload["rows"][0]["substitute_quality_score"] == "0.300000"
    assert payload["rows"][0]["quality_gap_score"] == "0.550000"
    assert payload["rows"][0]["source_disagreement_count"] == "3.000000"
    assert payload["rows"][0]["upstream_reason_codes"] == [
        "beat-writer-scratch",
        "club-lineup-delta",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert json.loads(json.dumps(payload, allow_nan=False, sort_keys=True)) == payload
    _assert_no_floats(payload)


def test_validates_frozen_decimal_datetime_flags_and_reason_contracts() -> None:
    row = _row("alpha-gap")
    config = _config()
    digest = build_market_research_baseball_late_scratch_lineup_gap_digest(
        (row,),
        config=config,
        generated_at=GENERATED_AT,
    )

    for value in (config, row, digest, digest.rows[0], digest.reason_code_counts[0]):
        assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        row.market_slug = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.digest_status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="max_watch_minutes_to_first_pitch"):
        _config(max_watch_minutes_to_first_pitch=60)
    with pytest.raises(ValueError, match="min_quality_gap_score"):
        _config(min_quality_gap_score=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="min_pitcher_handedness_fit_score"):
        _config(min_pitcher_handedness_fit_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_baseball_late_scratch_lineup_gap_digest(
            (),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 21, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="scheduled_first_pitch_at"):
        _row("naive-first-pitch", scheduled_first_pitch_at=datetime(2026, 7, 4, 22, 0))
    with pytest.raises(ValueError, match="market_slug"):
        _row("wallet-feed")
    with pytest.raises(ValueError, match="upstream_reason_codes"):
        _row("blank-upstream", upstream_reason_codes=("",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="source_timestamp_at"):
        build_market_research_baseball_late_scratch_lineup_gap_digest(
            (_row("future-source", source_timestamp_at=GENERATED_AT + timedelta(seconds=1)),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="scheduled_first_pitch_at"):
        build_market_research_baseball_late_scratch_lineup_gap_digest(
            (
                _row(
                    "already-started",
                    scheduled_first_pitch_at=GENERATED_AT - timedelta(seconds=1),
                ),
            ),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="input rows"):
        build_market_research_baseball_late_scratch_lineup_gap_digest(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        build_market_research_baseball_late_scratch_lineup_gap_digest(
            (_row("duplicate"), _row("duplicate")),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="row_status"):
        MarketResearchBaseballLateScratchLineupGapDigestRow(
            market_slug="manual",
            team="nyy",
            opponent="bos",
            scratched_player_id="player.manual",
            row_status="pass",
            scheduled_first_pitch_at=GENERATED_AT + timedelta(minutes=20),
            lineup_confirmed_at=GENERATED_AT - timedelta(minutes=10),
            source_timestamp_at=GENERATED_AT - timedelta(minutes=2),
            minutes_to_first_pitch=d("20.000000"),
            lineup_confirmation_age_minutes=d("10.000000"),
            source_age_minutes=d("2.000000"),
            scratched_player_impact_score=d("0.850000"),
            substitute_quality_score=d("0.300000"),
            quality_gap_score=d("0.550000"),
            pitcher_handedness_fit_score=d("0.750000"),
            source_disagreement_count=d("3.000000"),
            upstream_reason_codes=("beat-writer-scratch",),
            row_risk_score=d("0.850000"),
            reason_codes=(
                "baseball_late_scratch_lineup_gap_late_window",
                "baseball_late_scratch_lineup_gap_critical_timing",
            ),
        )


def test_public_numeric_fields_are_decimal_only() -> None:
    public_classes = (
        MarketResearchBaseballLateScratchLineupGapDigestConfig,
        MarketResearchBaseballLateScratchLineupGapDigestInputRow,
        MarketResearchBaseballLateScratchLineupGapDigestRow,
        MarketResearchBaseballLateScratchLineupGapDigestReasonCodeCount,
        MarketResearchBaseballLateScratchLineupGapDigest,
    )
    numeric_name_fragments = (
        "count",
        "minutes",
        "score",
    )

    for cls in public_classes:
        for field in fields(cls):
            if field.name == "reason_code_counts":
                continue
            if any(fragment in field.name for fragment in numeric_name_fragments):
                assert field.type in (Decimal, "Decimal")


def test_module_scope_excludes_io_mutation_sensitive_surfaces_and_float_literals() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.market_research_baseball_late_scratch_lineup_gap_digest",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    lowered_source = source.lower()

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )
    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "order",
        "cancel",
        "replace",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "requests",
        "httpx",
        "socket",
        "urlopen",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
    ):
        assert forbidden not in lowered_source

    imported_modules: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "http",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    )
    forbidden_call_names = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "delete",
        "send",
        "write",
    }
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (called_names & forbidden_call_names)
    assert not Path(
        "src/polymarket_alpha_lab/market_research_baseball_late_scratch_lineup_gap_digest.py",
    ).exists() or "open(" not in lowered_source


def _assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if isinstance(value, dict):
        for nested in value.values():
            _assert_no_floats(nested)
    if isinstance(value, list):
        for nested in value:
            _assert_no_floats(nested)
