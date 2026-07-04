from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_tennis_court_speed_mismatch_digest import (
    DEFAULT_MARKET_RESEARCH_TENNIS_COURT_SPEED_MISMATCH_DIGEST_CONFIG_VERSION,
    MarketResearchTennisCourtSpeedMismatchDigestConfig,
    MarketResearchTennisCourtSpeedMismatchObservation,
    MarketResearchTennisCourtSpeedMismatchReasonCodeCount,
    MarketResearchTennisCourtSpeedMismatchReport,
    MarketResearchTennisCourtSpeedMismatchRow,
    build_market_research_tennis_court_speed_mismatch_digest,
    market_research_tennis_court_speed_mismatch_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchTennisCourtSpeedMismatchDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_TENNIS_COURT_SPEED_MISMATCH_DIGEST_CONFIG_VERSION
        ),
        "max_observation_age_seconds": d("86400.000000"),
        "min_source_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "min_surface_history_sample_count": d("3.000000"),
        "min_confidence_score": d("0.600000"),
        "watch_mismatch_ratio_threshold": d("0.030000"),
        "blocked_mismatch_ratio_threshold": d("0.080000"),
    }
    values.update(overrides)
    return MarketResearchTennisCourtSpeedMismatchDigestConfig(**values)


def observation(
    market_id: str = "tennis.speed-mismatch.default",
    *,
    tournament_key: str = "wimbledon",
    match_key: str = "alcaraz.sinner.default",
    probability_event_type: str = "match_probability",
    court_key: str = "centre-court",
    court_surface: str = "grass",
    public_evidence_reference: str = "official-court-speed-note",
    observed_at: datetime | None = None,
    match_start_at: datetime | None = None,
    market_implied_court_speed_index: Decimal = d("1.000000"),
    observed_court_speed_index: Decimal = d("1.120000"),
    source_count: Decimal = d("3.000000"),
    independent_source_count: Decimal = d("3.000000"),
    surface_history_sample_count: Decimal = d("4.000000"),
    confidence_score: Decimal = d("0.900000"),
    observation_config_version: str = "tennis-court-speed-mismatch-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchTennisCourtSpeedMismatchObservation:
    return MarketResearchTennisCourtSpeedMismatchObservation(
        market_id=market_id,
        tournament_key=tournament_key,
        match_key=match_key,
        probability_event_type=probability_event_type,
        court_key=court_key,
        court_surface=court_surface,
        public_evidence_reference=public_evidence_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(hours=1),
        match_start_at=match_start_at or datetime(2026, 7, 6, 14, 0, tzinfo=UTC),
        market_implied_court_speed_index=market_implied_court_speed_index,
        observed_court_speed_index=observed_court_speed_index,
        source_count=source_count,
        independent_source_count=independent_source_count,
        surface_history_sample_count=surface_history_sample_count,
        confidence_score=confidence_score,
        observation_config_version=observation_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[MarketResearchTennisCourtSpeedMismatchObservation, ...],
    *,
    cfg: MarketResearchTennisCourtSpeedMismatchDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchTennisCourtSpeedMismatchReport:
    return build_market_research_tennis_court_speed_mismatch_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_tennis_court_speed_mismatch_digest_tracks_screening_counts_and_sorting() -> None:
    summary = report(
        (
            observation(
                "tennis.pass.market",
                tournament_key="us-open",
                match_key="pegula.gauff.pass",
                probability_event_type="set_probability",
                court_key="grandstand",
                court_surface="hard",
                match_start_at=datetime(2026, 7, 8, 16, 0, tzinfo=UTC),
                market_implied_court_speed_index=d("0.950000"),
                observed_court_speed_index=d("0.955000"),
                confidence_score=d("0.750000"),
            ),
            observation(
                "tennis.blocked.stale.market",
                tournament_key="roland-garros",
                match_key="swiatek.sabalenka.stale",
                court_key="court-philippe-chatrier",
                court_surface="clay",
                observed_at=GENERATED_AT - timedelta(hours=30),
                match_start_at=datetime(2026, 7, 5, 11, 0, tzinfo=UTC),
                market_implied_court_speed_index=d("1.000000"),
                observed_court_speed_index=d("1.010000"),
                source_count=d("1.000000"),
                independent_source_count=d("1.000000"),
                surface_history_sample_count=d("1.000000"),
                confidence_score=d("0.400000"),
            ),
            observation(
                "tennis.watch.below.market",
                tournament_key="rome",
                match_key="fritz.medvedev.below",
                court_key="court-pietrangeli",
                court_surface="clay",
                public_evidence_reference="rome-court-speed-brief",
                match_start_at=datetime(2026, 7, 7, 14, 0, tzinfo=UTC),
                market_implied_court_speed_index=d("1.000000"),
                observed_court_speed_index=d("0.950000"),
                confidence_score=d("0.800000"),
            ),
            observation(
                "tennis.blocked.above.market",
                tournament_key="wimbledon",
                match_key="alcaraz.sinner.above",
                court_key="centre-court",
                court_surface="grass",
                public_evidence_reference=(
                    "https://tennis.example/court-speed?token=abc123"
                ),
                match_start_at=datetime(2026, 7, 6, 14, 0, tzinfo=UTC),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchTennisCourtSpeedMismatchReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_TENNIS_COURT_SPEED_MISMATCH_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_tennis_court_speed_mismatch_digest"
    )
    assert summary.observation_count == d("4.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.blocked_count == d("2.000000")
    assert summary.above_market_speed_mismatch_count == d("1.000000")
    assert summary.below_market_speed_mismatch_count == d("1.000000")
    assert summary.watch_mismatch_count == d("1.000000")
    assert summary.blocked_mismatch_count == d("1.000000")
    assert summary.stale_observation_count == d("1.000000")
    assert summary.source_depth_gap_count == d("1.000000")
    assert summary.surface_history_gap_count == d("1.000000")
    assert summary.low_confidence_count == d("1.000000")
    assert summary.average_absolute_speed_mismatch_ratio == d("0.046315")
    assert summary.max_absolute_speed_mismatch_ratio == d("0.120000")
    assert summary.average_confidence_score == d("0.712500")
    assert tuple(row.market_id for row in summary.rows) == (
        "tennis.blocked.above.market",
        "tennis.blocked.stale.market",
        "tennis.watch.below.market",
        "tennis.pass.market",
    )

    blocked_above = summary.rows[0]
    assert blocked_above.digest_status == "blocked"
    assert blocked_above.speed_mismatch_points == d("0.120000")
    assert blocked_above.speed_mismatch_ratio == d("0.120000")
    assert blocked_above.absolute_speed_mismatch_ratio == d("0.120000")
    assert blocked_above.observation_age_seconds == d("3600.000000")
    assert blocked_above.redacted_public_evidence_reference.startswith("sha256:")
    assert "token=abc123" not in blocked_above.redacted_public_evidence_reference
    assert blocked_above.reason_codes == (
        "market_research_tennis_court_speed_mismatch_digest_above_market_speed_mismatch",
        "market_research_tennis_court_speed_mismatch_digest_blocked_mismatch",
    )

    blocked_stale = summary.rows[1]
    assert blocked_stale.digest_status == "blocked"
    assert blocked_stale.speed_mismatch_ratio == d("0.010000")
    assert blocked_stale.reason_codes == (
        "market_research_tennis_court_speed_mismatch_digest_low_confidence",
        "market_research_tennis_court_speed_mismatch_digest_source_depth_gap",
        "market_research_tennis_court_speed_mismatch_digest_stale_observation",
        "market_research_tennis_court_speed_mismatch_digest_surface_history_gap",
    )

    watch_below = summary.rows[2]
    assert watch_below.digest_status == "watch"
    assert watch_below.speed_mismatch_points == d("-0.050000")
    assert watch_below.speed_mismatch_ratio == d("-0.050000")
    assert watch_below.absolute_speed_mismatch_ratio == d("0.050000")
    assert watch_below.reason_codes == (
        "market_research_tennis_court_speed_mismatch_digest_below_market_speed_mismatch",
        "market_research_tennis_court_speed_mismatch_digest_watch_mismatch",
    )

    passed = summary.rows[3]
    assert passed.digest_status == "pass"
    assert passed.speed_mismatch_ratio == d("0.005263")
    assert passed.absolute_speed_mismatch_ratio == d("0.005263")
    assert passed.reason_codes == (
        "market_research_tennis_court_speed_mismatch_digest_pass",
    )

    assert summary.reason_code_counts == (
        MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
            reason_code=(
                "market_research_tennis_court_speed_mismatch_digest_"
                "above_market_speed_mismatch"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
            reason_code=(
                "market_research_tennis_court_speed_mismatch_digest_"
                "below_market_speed_mismatch"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
            reason_code=(
                "market_research_tennis_court_speed_mismatch_digest_blocked_mismatch"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
            reason_code=(
                "market_research_tennis_court_speed_mismatch_digest_low_confidence"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
            reason_code="market_research_tennis_court_speed_mismatch_digest_pass",
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
            reason_code=(
                "market_research_tennis_court_speed_mismatch_digest_source_depth_gap"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
            reason_code=(
                "market_research_tennis_court_speed_mismatch_digest_stale_observation"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
            reason_code=(
                "market_research_tennis_court_speed_mismatch_digest_surface_history_gap"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
        MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
            reason_code=(
                "market_research_tennis_court_speed_mismatch_digest_watch_mismatch"
            ),
            count=d("1.000000"),
            row_ratio=d("0.250000"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.observation_config_versions == (
        ("tennis.blocked.above.market", "tennis-court-speed-mismatch-v0"),
        ("tennis.blocked.stale.market", "tennis-court-speed-mismatch-v0"),
        ("tennis.pass.market", "tennis-court-speed-mismatch-v0"),
        ("tennis.watch.below.market", "tennis-court-speed-mismatch-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_empty_tennis_court_speed_mismatch_digest_is_blocked_and_decimal_zeroed() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_tennis_court_speed_mismatch_digest"
    )
    assert summary.observation_count == d("0.000000")
    assert summary.pass_count == d("0.000000")
    assert summary.watch_count == d("0.000000")
    assert summary.blocked_count == d("0.000000")
    assert summary.average_absolute_speed_mismatch_ratio == d("0.000000")
    assert summary.max_absolute_speed_mismatch_ratio == d("0.000000")
    assert summary.average_confidence_score == d("0.000000")
    assert summary.rows == ()
    assert summary.observation_config_versions == ()
    assert summary.reason_codes == (
        "market_research_tennis_court_speed_mismatch_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchTennisCourtSpeedMismatchReasonCodeCount(
            reason_code="market_research_tennis_court_speed_mismatch_digest_no_inputs",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )


def test_non_default_thresholds_can_downgrade_speed_mismatch_to_pass() -> None:
    summary = report(
        (observation("tennis.threshold.market"),),
        cfg=config(
            watch_mismatch_ratio_threshold=d("0.150000"),
            blocked_mismatch_ratio_threshold=d("0.250000"),
        ),
    )

    assert summary.digest_status == "pass"
    assert summary.recommended_next_step == (
        "allow_report_only_market_research_tennis_court_speed_mismatch_digest"
    )
    assert summary.rows[0].digest_status == "pass"
    assert summary.rows[0].absolute_speed_mismatch_ratio == d("0.120000")
    assert summary.rows[0].reason_codes == (
        "market_research_tennis_court_speed_mismatch_digest_pass",
    )
    assert summary.reason_codes == (
        "market_research_tennis_court_speed_mismatch_digest_pass",
    )


def test_validation_rejects_bad_inputs_flags_and_subclasses() -> None:
    assert MarketResearchTennisCourtSpeedMismatchDigestConfig.__dataclass_params__.frozen
    assert MarketResearchTennisCourtSpeedMismatchObservation.__dataclass_params__.frozen
    assert MarketResearchTennisCourtSpeedMismatchRow.__dataclass_params__.frozen
    assert MarketResearchTennisCourtSpeedMismatchReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("tennis-court-speed-mismatch-v0"))
    with pytest.raises(ValueError, match="watch_mismatch_ratio_threshold"):
        config(
            watch_mismatch_ratio_threshold=d("0.300000"),
            blocked_mismatch_ratio_threshold=d("0.200000"),
        )
    with pytest.raises(ValueError, match="min_confidence_score"):
        config(min_confidence_score=d("1.100000"))
    with pytest.raises(ValueError, match="observed_court_speed_index"):
        observation(observed_court_speed_index=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 4, 17, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 4, 17, 0))
    with pytest.raises(ValueError, match="market_implied_court_speed_index"):
        observation(market_implied_court_speed_index=d("0.000000"))
    with pytest.raises(ValueError, match="independent_source_count"):
        observation(
            independent_source_count=d("3.000000"),
            source_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(
            (
                observation(
                    "tennis.future",
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="MarketResearchTennisCourtSpeedMismatchObservation"):
        build_market_research_tennis_court_speed_mismatch_digest(
            [object()],  # type: ignore[list-item]
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_market_research_tennis_court_speed_mismatch_digest(
            (observation(),),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        report(
            (
                observation("tennis.duplicate"),
                observation("tennis.duplicate"),
            ),
        )
    with pytest.raises(ValueError, match="config paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="observation report_only must be True"):
        replace(observation("tennis.report-only"), report_only=False)

    frozen_observation = observation("tennis.frozen")
    with pytest.raises(FrozenInstanceError):
        frozen_observation.market_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        type(
            "ConfigSubclass",
            (MarketResearchTennisCourtSpeedMismatchDigestConfig,),
            {},
        )

    summary = report((observation("tennis.valid"),))
    with pytest.raises(ValueError, match="absolute_speed_mismatch_ratio"):
        replace(summary.rows[0], absolute_speed_mismatch_ratio=d("0.999999"))
    with pytest.raises(ValueError, match="row readonly must be True"):
        replace(summary.rows[0], readonly=False)
    with pytest.raises(ValueError, match="report paper_only must be True"):
        replace(summary, paper_only=False)


def test_payload_uses_decimal_strings_redaction_and_report_only_scope() -> None:
    summary = report(
        (
            observation(
                "tennis.payload.market",
                public_evidence_reference=(
                    "https://tennis.example/court-speed?token=abc123"
                ),
            ),
        ),
    )

    payload = market_research_tennis_court_speed_mismatch_digest_payload(summary)
    encoded = repr(payload)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["observation_count"] == "1.000000"
    assert payload["rows"][0]["speed_mismatch_ratio"] == "0.120000"
    assert payload["rows"][0]["absolute_speed_mismatch_ratio"] == "0.120000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T17:00:00+00:00"
    assert payload["rows"][0]["redacted_public_evidence_reference"].startswith("sha256:")
    assert "token=abc123" not in encoded
    assert not any(isinstance(value, (Decimal, datetime, float)) for value in walk_values(payload))

    for public_record in (
        config(),
        observation("tennis.public-record"),
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            field_value = getattr(public_record, field.name)
            if isinstance(field_value, Decimal):
                assert type(field_value) is Decimal, field.name

    source = Path(
        "src/polymarket_alpha_lab/market_research_tennis_court_speed_mismatch_digest.py",
    ).read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    forbidden_source_fragments = (
        "private_key",
        "api_key",
        "wallet",
        "auth",
        "urlopen",
        "connect(",
        "execute(",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live trading",
        "exchange mutation",
        "open(",
        "fast_mode",
        "fast mode",
    )
    lowered_source = source.lower()
    assert not any(fragment in lowered_source for fragment in forbidden_source_fragments)


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        values: list[object] = []
        for item in value.values():
            values.extend(walk_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_values(item))
        return tuple(values)
    if isinstance(value, tuple):
        values = []
        for item in value:
            values.extend(walk_values(item))
        return tuple(values)
    return (value,)
