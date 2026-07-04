from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import inspect

import pytest


MODULE = "polymarket_alpha_lab.market_research_basketball_rotation_injury_cluster_digest"


def _mod():
    return import_module(MODULE)


def _signal(
    *,
    market_slug: str = "nba-lakers-vs-suns-james-points",
    event_id: str = "nba-2026-01-02-lal-phx",
    team_name: str = "Los Angeles",
    player_name: str = "A. Starter",
    rotation_role: str = "starter",
    injury_status: str = "questionable",
    event_start: datetime | None = None,
    observed_at: datetime | None = None,
    minutes_share: Decimal = Decimal("0.300000"),
    usage_share: Decimal = Decimal("0.250000"),
    absence_probability: Decimal = Decimal("0.500000"),
    market_reference_probability: Decimal = Decimal("0.500000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    m = _mod()
    generated_at = datetime(2026, 1, 2, 18, tzinfo=UTC)
    return m.BasketballRotationInjurySignal(
        market_slug=market_slug,
        event_id=event_id,
        team_name=team_name,
        player_name=player_name,
        rotation_role=rotation_role,
        injury_status=injury_status,
        event_start=event_start or generated_at + timedelta(hours=3),
        observed_at=observed_at or generated_at - timedelta(minutes=20),
        minutes_share=minutes_share,
        usage_share=usage_share,
        absence_probability=absence_probability,
        market_reference_probability=market_reference_probability,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _assert_public_numerics_are_decimal(value: object) -> None:
    assert is_dataclass(value)
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, bool) or item is None:
            continue
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    _assert_public_numerics_are_decimal(nested)
            continue
        assert not isinstance(item, float), field.name
        assert not (isinstance(item, int) and not isinstance(item, bool)), field.name


def test_empty_digest_reports_zero_counts_and_hard_flags() -> None:
    m = _mod()
    generated_at = datetime(2026, 1, 2, 18, tzinfo=UTC)

    report = m.build_basketball_rotation_injury_cluster_digest(
        [],
        generated_at=generated_at,
    )

    assert report.generated_at == generated_at
    assert report.config_version == m.DEFAULT_BASKETBALL_ROTATION_INJURY_CLUSTER_DIGEST_CONFIG_VERSION
    assert report.market_count == Decimal("0")
    assert report.screen_count == Decimal("0")
    assert report.watch_count == Decimal("0")
    assert report.pass_count == Decimal("0")
    assert report.total_affected_player_count == Decimal("0")
    assert report.max_injury_cluster_score == Decimal("0")
    assert report.digest_status == "clear"
    assert report.reason_codes == ("no_rotation_injury_signals",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    _assert_public_numerics_are_decimal(report)


def test_high_risk_cluster_surfaces_screenable_market_research_row() -> None:
    m = _mod()
    generated_at = datetime(2026, 1, 2, 18, tzinfo=UTC)
    event_start = generated_at + timedelta(hours=3)
    signals = (
        _signal(
            player_name="B. Sixth",
            rotation_role="key_reserve",
            injury_status="doubtful",
            event_start=event_start,
            minutes_share=Decimal("0.220000"),
            usage_share=Decimal("0.180000"),
            absence_probability=Decimal("0.800000"),
            market_reference_probability=Decimal("0.520000"),
        ),
        _signal(
            player_name="A. Starter",
            rotation_role="starter",
            injury_status="out",
            event_start=event_start,
            minutes_share=Decimal("0.380000"),
            usage_share=Decimal("0.310000"),
            absence_probability=Decimal("0.900000"),
            market_reference_probability=Decimal("0.520000"),
        ),
    )

    report = m.build_basketball_rotation_injury_cluster_digest(
        signals,
        generated_at=generated_at,
    )

    assert report.digest_status == "screen"
    assert report.market_count == Decimal("1")
    assert report.screen_count == Decimal("1")
    assert report.watch_count == Decimal("0")
    assert report.pass_count == Decimal("0")
    assert report.total_affected_player_count == Decimal("2")
    assert report.max_injury_cluster_score == Decimal("0.900000")
    assert report.reason_codes == ("screenable_injury_cluster",)

    row = report.rows[0]
    assert row.market_slug == "nba-lakers-vs-suns-james-points"
    assert row.event_start == event_start
    assert row.team_name == "Los Angeles"
    assert row.affected_player_count == Decimal("2")
    assert row.affected_minutes_share == Decimal("0.600000")
    assert row.affected_usage_share == Decimal("0.490000")
    assert row.expected_absence_count == Decimal("1.700000")
    assert row.max_absence_probability == Decimal("0.900000")
    assert row.market_reference_probability == Decimal("0.520000")
    assert row.injury_probability_gap == Decimal("0.380000")
    assert row.injury_cluster_score == Decimal("0.900000")
    assert row.screening_status == "screen"
    assert row.reason_codes == (
        "rotation_minutes_cluster",
        "high_usage_cluster",
        "multi_player_absence",
        "starter_absence_signal",
        "short_event_window",
        "priced_probability_gap",
    )
    assert row.affected_players == ("A. Starter", "B. Sixth")
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_public_numerics_are_decimal(report)


def test_digest_is_deterministic_for_input_order_reason_codes_and_row_sorting() -> None:
    m = _mod()
    generated_at = datetime(2026, 1, 2, 18, tzinfo=UTC)
    later_event = generated_at + timedelta(hours=5)
    sooner_event = generated_at + timedelta(hours=2)
    signals = (
        _signal(
            market_slug="nba-beta-player-points",
            event_id="beta-game",
            team_name="Beta",
            player_name="Beta Reserve",
            rotation_role="reserve",
            event_start=later_event,
            minutes_share=Decimal("0.180000"),
            usage_share=Decimal("0.100000"),
            absence_probability=Decimal("0.250000"),
            market_reference_probability=Decimal("0.500000"),
        ),
        _signal(
            market_slug="nba-alpha-player-points",
            event_id="alpha-game",
            team_name="Alpha",
            player_name="Alpha Starter",
            rotation_role="starter",
            injury_status="out",
            event_start=sooner_event,
            minutes_share=Decimal("0.400000"),
            usage_share=Decimal("0.350000"),
            absence_probability=Decimal("0.850000"),
            market_reference_probability=Decimal("0.450000"),
        ),
        _signal(
            market_slug="nba-alpha-player-points",
            event_id="alpha-game",
            team_name="Alpha",
            player_name="Alpha Wing",
            rotation_role="key_reserve",
            injury_status="doubtful",
            event_start=sooner_event,
            minutes_share=Decimal("0.170000"),
            usage_share=Decimal("0.120000"),
            absence_probability=Decimal("0.550000"),
            market_reference_probability=Decimal("0.450000"),
        ),
    )

    report_a = m.build_basketball_rotation_injury_cluster_digest(
        signals,
        generated_at=generated_at,
    )
    report_b = m.build_basketball_rotation_injury_cluster_digest(
        tuple(reversed(signals)),
        generated_at=generated_at,
    )

    assert report_a == report_b
    assert tuple(row.market_slug for row in report_a.rows) == (
        "nba-alpha-player-points",
        "nba-beta-player-points",
    )
    assert report_a.rows[0].reason_codes == (
        "rotation_minutes_cluster",
        "high_usage_cluster",
        "multi_player_absence",
        "starter_absence_signal",
        "short_event_window",
        "priced_probability_gap",
    )


def test_validation_rejects_unsafe_types_times_thresholds_and_secret_like_text() -> None:
    m = _mod()

    with pytest.raises(ValueError, match="absence_probability.*Decimal"):
        _signal(absence_probability=0.7)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="generated_at.*timezone-aware"):
        m.build_basketball_rotation_injury_cluster_digest(
            [],
            generated_at=datetime(2026, 1, 2, 18),
        )

    with pytest.raises(ValueError, match="event_start.*timezone-aware"):
        _signal(event_start=datetime(2026, 1, 2, 21))

    with pytest.raises(ValueError, match="high_risk_score_threshold"):
        m.BasketballRotationInjuryClusterDigestConfig(
            high_risk_score_threshold=Decimal("0.30"),
            watch_risk_score_threshold=Decimal("0.40"),
        )

    with pytest.raises(ValueError, match="player_name.*sensitive"):
        _signal(player_name="sk_live_do_not_leak")


def test_hard_report_only_flags_are_enforced_on_public_dataclasses() -> None:
    m = _mod()
    generated_at = datetime(2026, 1, 2, 18, tzinfo=UTC)

    with pytest.raises(ValueError, match="paper_only"):
        m.BasketballRotationInjuryClusterDigestConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _signal(report_only=False)  # type: ignore[call-arg]

    with pytest.raises(ValueError, match="readonly"):
        m.BasketballRotationInjuryClusterRow(
            market_slug="market",
            event_id="event",
            team_name="Team",
            event_start=generated_at + timedelta(hours=1),
            affected_player_count=Decimal("0"),
            affected_minutes_share=Decimal("0"),
            affected_usage_share=Decimal("0"),
            expected_absence_count=Decimal("0"),
            max_absence_probability=Decimal("0"),
            market_reference_probability=Decimal("0"),
            injury_probability_gap=Decimal("0"),
            injury_cluster_score=Decimal("0"),
            screening_status="pass",
            reason_codes=("insufficient_cluster_risk",),
            affected_players=(),
            readonly=False,
        )

    with pytest.raises(ValueError, match="paper_only"):
        m.BasketballRotationInjuryClusterDigestReport(
            generated_at=generated_at,
            config_version=m.DEFAULT_BASKETBALL_ROTATION_INJURY_CLUSTER_DIGEST_CONFIG_VERSION,
            market_count=Decimal("0"),
            screen_count=Decimal("0"),
            watch_count=Decimal("0"),
            pass_count=Decimal("0"),
            total_affected_player_count=Decimal("0"),
            max_injury_cluster_score=Decimal("0"),
            digest_status="clear",
            reason_codes=("no_rotation_injury_signals",),
            rows=(),
            paper_only=False,
        )


def test_non_default_thresholds_change_watch_screening_without_changing_flags() -> None:
    m = _mod()
    generated_at = datetime(2026, 1, 2, 18, tzinfo=UTC)
    signal = _signal(
        market_slug="nba-threshold-example",
        event_id="threshold-game",
        player_name="Threshold Reserve",
        rotation_role="reserve",
        minutes_share=Decimal("0.250000"),
        usage_share=Decimal("0.100000"),
        absence_probability=Decimal("0.300000"),
        market_reference_probability=Decimal("0.500000"),
    )

    default_report = m.build_basketball_rotation_injury_cluster_digest(
        [signal],
        generated_at=generated_at,
    )
    custom_report = m.build_basketball_rotation_injury_cluster_digest(
        [signal],
        generated_at=generated_at,
        config=m.BasketballRotationInjuryClusterDigestConfig(
            watch_risk_score_threshold=Decimal("0.250000"),
            affected_minutes_share_threshold=Decimal("0.200000"),
        ),
    )

    assert default_report.rows[0].screening_status == "pass"
    assert default_report.rows[0].reason_codes == ("insufficient_cluster_risk",)
    assert custom_report.rows[0].screening_status == "watch"
    assert custom_report.rows[0].reason_codes == (
        "rotation_minutes_cluster",
        "short_event_window",
    )
    assert custom_report.paper_only is True
    assert custom_report.report_only is True
    assert custom_report.readonly is True


def test_module_is_pure_report_only_surface_without_io_or_trading_dependencies() -> None:
    m = _mod()
    source = inspect.getsource(m)

    forbidden_fragments = (
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "sqlalchemy",
        "supabase",
        "open(",
        ".write(",
        ".read(",
        "private_key",
        "place_order",
        "cancel_order",
        "replace_order",
    )
    lowered = source.lower()
    for fragment in forbidden_fragments:
        assert fragment not in lowered
