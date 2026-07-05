from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_hockey_power_play_mismatch_digest import (
    DEFAULT_MARKET_RESEARCH_HOCKEY_POWER_PLAY_MISMATCH_DIGEST_CONFIG_VERSION,
    MarketResearchHockeyPowerPlayMismatchDigestConfig,
    MarketResearchHockeyPowerPlayMismatchDigestItem,
    MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount,
    MarketResearchHockeyPowerPlayMismatchDigestReport,
    MarketResearchHockeyPowerPlayMismatchDigestRow,
    build_market_research_hockey_power_play_mismatch_digest,
    market_research_hockey_power_play_mismatch_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 21, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchHockeyPowerPlayMismatchDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_HOCKEY_POWER_PLAY_MISMATCH_DIGEST_CONFIG_VERSION
        ),
        "max_evidence_age_seconds": d("3600.000000"),
        "min_power_play_edge_score": d("0.650000"),
        "min_penalty_kill_gap_score": d("0.550000"),
        "min_goalie_fatigue_score": d("0.500000"),
        "min_special_teams_sample_count": d("3.000000"),
        "min_source_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "max_conflicting_source_count": d("0.000000"),
        "confidence_decay_per_source_gap": d("0.120000"),
        "confidence_decay_per_stale_evidence": d("0.100000"),
        "confidence_decay_per_conflict": d("0.250000"),
        "confidence_decay_per_goalie_fatigue": d("0.050000"),
    }
    values.update(overrides)
    return MarketResearchHockeyPowerPlayMismatchDigestConfig(**values)


def hockey_item(
    condition_id: str = "condition.nhl.default",
    *,
    hockey_event_key: str = "nhl.nyr.njd.default",
    team_key: str = "nyr",
    opponent_key: str = "njd",
    public_evidence_reference: str = "nhl-official-special-teams-report",
    observed_at: datetime | None = None,
    power_play_edge_score: Decimal = d("0.700000"),
    penalty_kill_gap_score: Decimal = d("0.600000"),
    goalie_fatigue_score: Decimal = d("0.400000"),
    special_teams_sample_count: Decimal = d("4.000000"),
    source_count: Decimal = d("3.000000"),
    independent_source_count: Decimal = d("3.000000"),
    conflicting_source_count: Decimal = d("0.000000"),
    base_confidence_score: Decimal = d("0.800000"),
    item_config_version: str = "hockey-power-play-mismatch-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchHockeyPowerPlayMismatchDigestItem:
    return MarketResearchHockeyPowerPlayMismatchDigestItem(
        condition_id=condition_id,
        hockey_event_key=hockey_event_key,
        team_key=team_key,
        opponent_key=opponent_key,
        public_evidence_reference=public_evidence_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=20),
        power_play_edge_score=power_play_edge_score,
        penalty_kill_gap_score=penalty_kill_gap_score,
        goalie_fatigue_score=goalie_fatigue_score,
        special_teams_sample_count=special_teams_sample_count,
        source_count=source_count,
        independent_source_count=independent_source_count,
        conflicting_source_count=conflicting_source_count,
        base_confidence_score=base_confidence_score,
        item_config_version=item_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    items: tuple[MarketResearchHockeyPowerPlayMismatchDigestItem, ...],
    *,
    cfg: MarketResearchHockeyPowerPlayMismatchDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchHockeyPowerPlayMismatchDigestReport:
    return build_market_research_hockey_power_play_mismatch_digest(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_hockey_power_play_mismatch_digest_tracks_edges_gaps_and_confidence() -> None:
    summary = report(
        (
            hockey_item(
                "condition.ready",
                hockey_event_key="nhl.car.nyr.ready",
                team_key="car",
                opponent_key="nyr",
                power_play_edge_score=d("0.800000"),
                penalty_kill_gap_score=d("0.700000"),
                goalie_fatigue_score=d("0.450000"),
                base_confidence_score=d("0.850000"),
            ),
            hockey_item(
                "condition.watch",
                hockey_event_key="nhl.edm.cgy.watch",
                team_key="edm",
                opponent_key="cgy",
                public_evidence_reference="https://nhl.example/special-teams?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=2),
                power_play_edge_score=d("0.500000"),
                penalty_kill_gap_score=d("0.400000"),
                goalie_fatigue_score=d("0.700000"),
                special_teams_sample_count=d("2.000000"),
                source_count=d("2.000000"),
                independent_source_count=d("1.000000"),
                base_confidence_score=d("0.900000"),
            ),
        ),
    )

    assert isinstance(summary, MarketResearchHockeyPowerPlayMismatchDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.digest_status == "watch"
    assert summary.recommended_next_step == (
        "watch_report_only_market_research_hockey_power_play_mismatch_digest"
    )
    assert summary.item_count == d("2.000000")
    assert summary.ready_item_count == d("1.000000")
    assert summary.watch_item_count == d("1.000000")
    assert summary.blocked_item_count == d("0.000000")
    assert summary.power_play_edge_gap_item_count == d("1.000000")
    assert summary.penalty_kill_gap_item_count == d("1.000000")
    assert summary.goalie_fatigue_item_count == d("1.000000")
    assert summary.sample_gap_item_count == d("1.000000")
    assert summary.source_diversity_gap_item_count == d("1.000000")
    assert summary.average_confidence_score == d("0.570000")
    assert tuple(row.hockey_event_key for row in summary.rows) == (
        "nhl.edm.cgy.watch",
        "nhl.car.nyr.ready",
    )

    watched = summary.rows[0]
    assert watched.digest_status == "watch"
    assert watched.evidence_age_seconds == d("7200.000000")
    assert watched.source_diversity_ratio == d("0.500000")
    assert watched.confidence_decay_score == d("0.610000")
    assert watched.confidence_score == d("0.290000")
    assert watched.redacted_public_evidence_reference == "sha256:d66043ca7ec4"
    assert watched.reason_codes == (
        "market_research_hockey_power_play_mismatch_digest_goalie_fatigue",
        "market_research_hockey_power_play_mismatch_digest_low_penalty_kill_gap",
        "market_research_hockey_power_play_mismatch_digest_low_power_play_edge",
        "market_research_hockey_power_play_mismatch_digest_source_diversity_gap",
        "market_research_hockey_power_play_mismatch_digest_special_teams_sample_gap",
        "market_research_hockey_power_play_mismatch_digest_stale_evidence",
    )

    ready = summary.rows[1]
    assert ready.digest_status == "ready"
    assert ready.confidence_score == d("0.850000")
    assert ready.redacted_public_evidence_reference == "nhl-official-special-teams-report"
    assert ready.reason_codes == (
        "market_research_hockey_power_play_mismatch_digest_ready",
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "nhl.example",
        "wallet",
        "private",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
    ):
        assert token not in public


def test_hockey_power_play_mismatch_digest_blocks_on_conflict_and_empty_inputs() -> None:
    blocked = report(
        (
            hockey_item(
                "condition.conflict",
                hockey_event_key="nhl.bos.tor.conflict",
                public_evidence_reference="wallet://private/special-teams-feed",
                observed_at=GENERATED_AT - timedelta(minutes=40),
                source_count=d("1.000000"),
                independent_source_count=d("1.000000"),
                conflicting_source_count=d("1.000000"),
                power_play_edge_score=d("0.800000"),
                penalty_kill_gap_score=d("0.700000"),
            ),
            hockey_item(
                "condition.ready",
                hockey_event_key="nhl.van.sea.ready",
                team_key="van",
                opponent_key="sea",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert blocked.generated_at == GENERATED_AT
    assert blocked.digest_status == "blocked"
    assert blocked.recommended_next_step == (
        "block_report_only_market_research_hockey_power_play_mismatch_digest"
    )
    assert blocked.conflict_item_count == d("1.000000")
    assert blocked.source_depth_gap_item_count == d("1.000000")
    assert blocked.reason_code_counts == (
        MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount(
            reason_code=(
                "market_research_hockey_power_play_mismatch_digest_conflicting_sources"
            ),
            count=d("1.000000"),
            item_ratio=d("0.500000"),
        ),
        MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount(
            reason_code="market_research_hockey_power_play_mismatch_digest_ready",
            count=d("1.000000"),
            item_ratio=d("0.500000"),
        ),
        MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount(
            reason_code="market_research_hockey_power_play_mismatch_digest_source_depth_gap",
            count=d("1.000000"),
            item_ratio=d("0.500000"),
        ),
    )
    assert blocked.reason_codes == tuple(
        item.reason_code for item in blocked.reason_code_counts
    )
    assert blocked.item_config_versions == (
        ("nhl.bos.tor.conflict", "hockey-power-play-mismatch-v0"),
        ("nhl.van.sea.ready", "hockey-power-play-mismatch-v0"),
    )
    assert blocked.rows[0].redacted_public_evidence_reference == "sha256:2804150eba8e"
    assert blocked.paper_only is True
    assert blocked.report_only is True
    assert blocked.readonly is True

    empty = report(())
    assert empty.digest_status == "blocked"
    assert empty.item_count == d("0.000000")
    assert empty.rows == ()
    assert empty.reason_codes == (
        "market_research_hockey_power_play_mismatch_digest_no_inputs",
    )
    assert empty.reason_code_counts == (
        MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount(
            reason_code="market_research_hockey_power_play_mismatch_digest_no_inputs",
            count=d("1.000000"),
            item_ratio=d("0.000000"),
        ),
    )


def test_hockey_power_play_mismatch_digest_validates_exact_types_flags_and_surface() -> None:
    assert MarketResearchHockeyPowerPlayMismatchDigestConfig.__dataclass_params__.frozen
    assert MarketResearchHockeyPowerPlayMismatchDigestItem.__dataclass_params__.frozen
    assert MarketResearchHockeyPowerPlayMismatchDigestRow.__dataclass_params__.frozen
    assert (
        MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount.__dataclass_params__.frozen
    )
    assert MarketResearchHockeyPowerPlayMismatchDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("hockey-power-play-mismatch-v0"))
    with pytest.raises(ValueError, match="max_evidence_age_seconds"):
        config(max_evidence_age_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="min_power_play_edge_score"):
        config(min_power_play_edge_score=0.5)
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=2)
    with pytest.raises(ValueError, match="condition_id"):
        hockey_item(condition_id=_StringSubclass("condition.nhl.bad"))
    with pytest.raises(ValueError, match="source_count"):
        hockey_item(source_count=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (hockey_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 2, 21, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        report((hockey_item(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="redacted"):
        hockey_item(public_evidence_reference="token=secret-123")
    with pytest.raises(ValueError, match="conflicting_source_count"):
        hockey_item(
            independent_source_count=d("1.000000"),
            conflicting_source_count=d("2.000000"),
            source_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(hockey_item(), paper_only=False)
    frozen_config = config()
    frozen_item = hockey_item()
    frozen_report = report((hockey_item(hockey_event_key="nhl.frozen"),))
    frozen_row = frozen_report.rows[0]
    frozen_reason_count = frozen_report.reason_code_counts[0]
    with pytest.raises(FrozenInstanceError):
        frozen_config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_item.paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_row.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_reason_count.count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        frozen_report.digest_status = "blocked"  # type: ignore[misc]

    source = Path(
        "src/polymarket_alpha_lab/market_research_hockey_power_play_mismatch_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open", "__import__"}
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
    forbidden_import_fragments = (
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
        "pathlib",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "account",
        "advice",
        "open(",
        "private_key",
        "api_key",
        "secret",
    ):
        assert forbidden not in lowered


def test_hockey_power_play_mismatch_digest_rejects_all_false_hard_flags() -> None:
    summary = report((hockey_item(hockey_event_key="nhl.flags"),))
    row = summary.rows[0]
    reason_code_count = summary.reason_code_counts[0]

    records = (
        ("config", lambda flag: config(**{flag: False})),
        ("item", lambda flag: replace(hockey_item(), **{flag: False})),
        ("row", lambda flag: replace(row, **{flag: False})),
        (
            "reason_code_count",
            lambda flag: replace(reason_code_count, **{flag: False}),
        ),
        ("report", lambda flag: replace(summary, **{flag: False})),
    )

    for record_name, mutate in records:
        for flag in ("paper_only", "report_only", "readonly"):
            with pytest.raises(ValueError, match=f"{record_name} {flag} must be True"):
                mutate(flag)


def test_hockey_power_play_mismatch_digest_rejects_bad_consistency_and_subclasses() -> None:
    with pytest.raises(ValueError, match="unique"):
        report(
            (
                hockey_item(hockey_event_key="nhl.duplicate"),
                hockey_item(hockey_event_key="nhl.duplicate"),
            ),
        )

    with pytest.raises(TypeError):
        type(
            "ConfigSubclass",
            (MarketResearchHockeyPowerPlayMismatchDigestConfig,),
            {},
        )

    ready = report((hockey_item(hockey_event_key="nhl.ready"),))
    with pytest.raises(ValueError, match="rows must be sorted"):
        replace(
            ready,
            rows=(
                ready.rows[0],
                MarketResearchHockeyPowerPlayMismatchDigestRow(
                    condition_id="condition.bad",
                    hockey_event_key="nhl.bad",
                    team_key="bad",
                    opponent_key="opp",
                    digest_status="ready",
                    evidence_age_seconds=d("1200.000000"),
                    power_play_edge_score=d("0.800000"),
                    penalty_kill_gap_score=d("0.700000"),
                    goalie_fatigue_score=d("0.000000"),
                    special_teams_sample_count=d("4.000000"),
                    source_count=d("3.000000"),
                    independent_source_count=d("3.000000"),
                    source_diversity_ratio=d("1.000000"),
                    conflicting_source_count=d("0.000000"),
                    base_confidence_score=d("0.800000"),
                    confidence_decay_score=d("0.000000"),
                    confidence_score=d("0.800000"),
                    redacted_public_evidence_reference="nhl-official-special-teams-report",
                    reason_codes=(
                        "market_research_hockey_power_play_mismatch_digest_ready",
                    ),
                ),
            ),
        )

    with pytest.raises(ValueError, match="item_count"):
        replace(ready, item_count=d("2.000000"))
    with pytest.raises(ValueError, match="item_config_versions must be sorted"):
        replace(
            report(
                (
                    hockey_item(hockey_event_key="nhl.b"),
                    hockey_item(hockey_event_key="nhl.a"),
                ),
            ),
            item_config_versions=(
                ("nhl.b", "hockey-power-play-mismatch-v0"),
                ("nhl.a", "hockey-power-play-mismatch-v0"),
            ),
        )
    with pytest.raises(ValueError, match="reason_code_counts must be sorted"):
        replace(
            report(
                (
                    hockey_item(
                        hockey_event_key="nhl.conflict",
                        source_count=d("1.000000"),
                        independent_source_count=d("1.000000"),
                        conflicting_source_count=d("1.000000"),
                    ),
                    hockey_item(hockey_event_key="nhl.ready"),
                ),
            ),
            reason_code_counts=(
                MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount(
                    reason_code="market_research_hockey_power_play_mismatch_digest_ready",
                    count=d("1.000000"),
                    item_ratio=d("0.500000"),
                ),
                MarketResearchHockeyPowerPlayMismatchDigestReasonCodeCount(
                    reason_code=(
                        "market_research_hockey_power_play_mismatch_digest_conflicting_sources"
                    ),
                    count=d("1.000000"),
                    item_ratio=d("0.500000"),
                ),
            ),
        )


def test_hockey_power_play_mismatch_digest_payload_uses_decimal_strings() -> None:
    summary = report(
        (
            hockey_item(
                "condition.public",
                hockey_event_key="nhl.public",
                power_play_edge_score=d("0.400000"),
                penalty_kill_gap_score=d("0.300000"),
            ),
        ),
    )

    payload = market_research_hockey_power_play_mismatch_digest_payload(summary)
    encoded = repr(payload).lower()

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["item_count"] == "1.000000"
    assert payload["rows"][0]["confidence_score"] == "0.560000"
    assert not any(isinstance(value, float) for value in walk_values(payload))
    for field in fields(summary):
        if field.name.endswith("_count") or field.name.endswith("_ratio"):
            assert type(getattr(summary, field.name)) is Decimal
    for forbidden in (
        "wallet",
        "account",
        "token",
        "secret",
        "private_key",
        "broker",
        "signing",
        "submit",
        "cancel",
        "advice",
    ):
        assert forbidden not in encoded


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
    return (value,)
