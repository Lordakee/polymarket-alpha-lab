from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_hockey_injury_cluster_digest import (
    DEFAULT_MARKET_RESEARCH_HOCKEY_INJURY_CLUSTER_DIGEST_CONFIG_VERSION,
    MarketResearchHockeyInjuryClusterDigestConfig,
    MarketResearchHockeyInjuryClusterDigestItem,
    MarketResearchHockeyInjuryClusterDigestReasonCodeCount,
    MarketResearchHockeyInjuryClusterDigestReport,
    MarketResearchHockeyInjuryClusterDigestRow,
    build_market_research_hockey_injury_cluster_digest,
    market_research_hockey_injury_cluster_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_hockey_injury_cluster_digest.py",
)


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
) -> MarketResearchHockeyInjuryClusterDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_HOCKEY_INJURY_CLUSTER_DIGEST_CONFIG_VERSION
        ),
        "max_cluster_age_seconds": d("5400.000000"),
        "critical_cluster_age_seconds": d("1800.000000"),
        "min_source_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "min_team_injury_count": d("2.000000"),
        "min_cluster_confidence_score": d("0.650000"),
        "high_cluster_severity_threshold": d("0.750000"),
        "min_market_liquidity_score": d("0.550000"),
        "confidence_decay_per_stale_cluster": d("0.180000"),
        "confidence_decay_per_source_gap": d("0.120000"),
        "confidence_decay_per_thin_cluster": d("0.090000"),
        "confidence_decay_per_liquidity_gap": d("0.080000"),
    }
    values.update(overrides)
    return MarketResearchHockeyInjuryClusterDigestConfig(**values)


def cluster_item(
    condition_id: str = "condition.nhl.rangers.defense.cluster",
    *,
    hockey_event_key: str = "nhl.rangers.bruins.game-7",
    league_key: str = "nhl",
    team_key: str = "new-york-rangers",
    opponent_key: str = "boston-bruins",
    injury_cluster_key: str = "defensemen-questionable",
    public_news_reference: str = "league-injury-report-rangers-bruins",
    observed_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    independent_source_count: Decimal = d("3.000000"),
    team_injury_count: Decimal = d("2.000000"),
    cluster_confidence_score: Decimal = d("0.800000"),
    cluster_severity_score: Decimal = d("0.300000"),
    market_liquidity_score: Decimal = d("0.850000"),
    base_confidence_score: Decimal = d("0.820000"),
    item_config_version: str = "hockey-injury-cluster-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchHockeyInjuryClusterDigestItem:
    return MarketResearchHockeyInjuryClusterDigestItem(
        condition_id=condition_id,
        hockey_event_key=hockey_event_key,
        league_key=league_key,
        team_key=team_key,
        opponent_key=opponent_key,
        injury_cluster_key=injury_cluster_key,
        public_news_reference=public_news_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=20),
        source_count=source_count,
        independent_source_count=independent_source_count,
        team_injury_count=team_injury_count,
        cluster_confidence_score=cluster_confidence_score,
        cluster_severity_score=cluster_severity_score,
        market_liquidity_score=market_liquidity_score,
        base_confidence_score=base_confidence_score,
        item_config_version=item_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    items: tuple[MarketResearchHockeyInjuryClusterDigestItem, ...],
    *,
    cfg: MarketResearchHockeyInjuryClusterDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchHockeyInjuryClusterDigestReport:
    return build_market_research_hockey_injury_cluster_digest(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_hockey_injury_cluster_digest_models_cluster_age_sources_severity_liquidity_and_decay() -> None:
    summary = report(
        (
            cluster_item(
                "condition.blocked",
                hockey_event_key="nhl.oilers.stars.game-5",
                league_key="nhl",
                team_key="edmonton-oilers",
                opponent_key="dallas-stars",
                injury_cluster_key="top-six-late-scratches",
                public_news_reference="https://hockey.example/injury?api_key=redacted-test",
                observed_at=GENERATED_AT - timedelta(hours=2),
                source_count=d("1.000000"),
                independent_source_count=d("1.000000"),
                team_injury_count=d("1.000000"),
                cluster_confidence_score=d("0.900000"),
                cluster_severity_score=d("0.850000"),
                market_liquidity_score=d("0.450000"),
                base_confidence_score=d("0.920000"),
            ),
            cluster_item(
                "condition.watch",
                hockey_event_key="nhl.avalanche.golden-knights.final",
                league_key="nhl",
                team_key="colorado-avalanche",
                opponent_key="vegas-golden-knights",
                injury_cluster_key="blue-line-depth-risk",
                public_news_reference="private-hockey-injury-feed",
                observed_at=GENERATED_AT - timedelta(minutes=45),
                team_injury_count=d("3.000000"),
                cluster_confidence_score=d("0.600000"),
                cluster_severity_score=d("0.820000"),
                market_liquidity_score=d("0.500000"),
                base_confidence_score=d("0.780000"),
            ),
            cluster_item(
                "condition.ready",
                hockey_event_key="nhl.maple-leafs.panthers.game-3",
                league_key="nhl",
                team_key="toronto-maple-leafs",
                opponent_key="florida-panthers",
                injury_cluster_key="depth-forward-monitor",
                public_news_reference="league-injury-report-maple-leafs-panthers",
                source_count=d("4.000000"),
                independent_source_count=d("3.000000"),
                team_injury_count=d("2.000000"),
                cluster_confidence_score=d("0.750000"),
                cluster_severity_score=d("0.250000"),
                market_liquidity_score=d("0.900000"),
                base_confidence_score=d("0.840000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchHockeyInjuryClusterDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_HOCKEY_INJURY_CLUSTER_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_hockey_injury_cluster_digest"
    )
    assert summary.item_count == d("3.000000")
    assert summary.ready_item_count == d("1.000000")
    assert summary.watch_item_count == d("1.000000")
    assert summary.blocked_item_count == d("1.000000")
    assert summary.stale_cluster_item_count == d("1.000000")
    assert summary.source_gap_item_count == d("1.000000")
    assert summary.thin_cluster_item_count == d("1.000000")
    assert summary.low_cluster_confidence_item_count == d("1.000000")
    assert summary.high_cluster_severity_item_count == d("2.000000")
    assert summary.liquidity_gap_item_count == d("2.000000")
    assert summary.average_confidence_score == d("0.663333")
    assert summary.max_observed_cluster_age_seconds == d("7200.000000")
    assert tuple(row.hockey_event_key for row in summary.rows) == (
        "nhl.oilers.stars.game-5",
        "nhl.avalanche.golden-knights.final",
        "nhl.maple-leafs.panthers.game-3",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.cluster_age_seconds == d("7200.000000")
    assert blocked.source_diversity_ratio == d("1.000000")
    assert blocked.confidence_decay_score == d("0.470000")
    assert blocked.confidence_score == d("0.450000")
    assert blocked.redacted_public_news_reference == "sha256:d7ef6fb25cee"
    assert blocked.reason_codes == (
        "market_research_hockey_injury_cluster_digest_high_cluster_severity",
        "market_research_hockey_injury_cluster_digest_liquidity_gap",
        "market_research_hockey_injury_cluster_digest_source_gap",
        "market_research_hockey_injury_cluster_digest_stale_cluster",
        "market_research_hockey_injury_cluster_digest_thin_cluster",
    )

    watched = summary.rows[1]
    assert watched.digest_status == "watch"
    assert watched.confidence_decay_score == d("0.080000")
    assert watched.confidence_score == d("0.700000")
    assert watched.redacted_public_news_reference == "sha256:5bfdf6562060"
    assert watched.reason_codes == (
        "market_research_hockey_injury_cluster_digest_high_cluster_severity",
        "market_research_hockey_injury_cluster_digest_liquidity_gap",
        "market_research_hockey_injury_cluster_digest_low_cluster_confidence",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.confidence_score == d("0.840000")
    assert ready.redacted_public_news_reference == (
        "league-injury-report-maple-leafs-panthers"
    )
    assert ready.reason_codes == (
        "market_research_hockey_injury_cluster_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
            reason_code="market_research_hockey_injury_cluster_digest_high_cluster_severity",
            count=d("2.000000"),
            item_ratio=d("0.666667"),
        ),
        MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
            reason_code="market_research_hockey_injury_cluster_digest_liquidity_gap",
            count=d("2.000000"),
            item_ratio=d("0.666667"),
        ),
        MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
            reason_code="market_research_hockey_injury_cluster_digest_low_cluster_confidence",
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
        MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
            reason_code="market_research_hockey_injury_cluster_digest_ready",
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
        MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
            reason_code="market_research_hockey_injury_cluster_digest_source_gap",
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
        MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
            reason_code="market_research_hockey_injury_cluster_digest_stale_cluster",
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
        MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
            reason_code="market_research_hockey_injury_cluster_digest_thin_cluster",
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.item_config_versions == (
        ("nhl.avalanche.golden-knights.final", "hockey-injury-cluster-v0"),
        ("nhl.maple-leafs.panthers.game-3", "hockey-injury-cluster-v0"),
        ("nhl.oilers.stars.game-5", "hockey-injury-cluster-v0"),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    public = repr(asdict(summary)).lower()
    for token in (
        "redacted-test",
        "hockey.example",
        "private-hockey-injury-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
    ):
        assert token not in public


def test_hockey_injury_cluster_digest_empty_inputs_are_report_only_and_deterministic() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_hockey_injury_cluster_digest"
    )
    assert summary.item_count == d("0.000000")
    assert summary.ready_item_count == d("0.000000")
    assert summary.watch_item_count == d("0.000000")
    assert summary.blocked_item_count == d("0.000000")
    assert summary.average_confidence_score == d("0.000000")
    assert summary.rows == ()
    assert summary.item_config_versions == ()
    assert summary.reason_codes == (
        "market_research_hockey_injury_cluster_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
            reason_code="market_research_hockey_injury_cluster_digest_no_inputs",
            count=d("1.000000"),
            item_ratio=d("0.000000"),
        ),
    )


def test_hockey_injury_cluster_digest_validates_types_flags_no_io_and_public_payload() -> None:
    assert MarketResearchHockeyInjuryClusterDigestConfig.__dataclass_params__.frozen
    assert MarketResearchHockeyInjuryClusterDigestItem.__dataclass_params__.frozen
    assert MarketResearchHockeyInjuryClusterDigestRow.__dataclass_params__.frozen
    assert (
        MarketResearchHockeyInjuryClusterDigestReasonCodeCount.__dataclass_params__.frozen
    )
    assert MarketResearchHockeyInjuryClusterDigestReport.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("hockey-injury-cluster-v0"))
    with pytest.raises(ValueError, match="max_cluster_age_seconds"):
        config(max_cluster_age_seconds=_DecimalSubclass("5400.000000"))
    with pytest.raises(ValueError, match="min_cluster_confidence_score"):
        config(min_cluster_confidence_score=0.65)
    with pytest.raises(ValueError, match="condition_id"):
        cluster_item(condition_id=_StringSubclass("condition.bad"))
    with pytest.raises(ValueError, match="source_count"):
        cluster_item(source_count=1.0)
    with pytest.raises(ValueError, match="cluster_confidence_score"):
        cluster_item(cluster_confidence_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (cluster_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 4, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="future"):
        report((cluster_item(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="public_news_reference"):
        cluster_item(public_news_reference="")
    with pytest.raises(ValueError, match="unsafe"):
        cluster_item(public_news_reference="https://hockey.example/auth/token")
    with pytest.raises(ValueError, match="items"):
        build_market_research_hockey_injury_cluster_digest(
            [object()],
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        report((cluster_item(), cluster_item(condition_id="condition.other")))
    with pytest.raises(ValueError, match="config"):
        build_market_research_hockey_injury_cluster_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        cluster_item(paper_only=False)
    summary = report((cluster_item(),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]
    cfg = config()
    item = cluster_item()
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        item.condition_id = "condition.changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="report"):
        market_research_hockey_injury_cluster_digest_payload(object())
    payload = market_research_hockey_injury_cluster_digest_payload(summary)

    assert payload["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["item_count"] == "1.000000"
    assert payload["average_confidence_score"] == "0.820000"
    assert payload["rows"][0]["confidence_score"] == "0.820000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T17:40:00+00:00"

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    forbidden_calls = {
        "open",
        "connect",
        "request",
        "post",
        "put",
        "delete",
        "execute",
        "commit",
        "rollback",
        "trade",
        "order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    )
    assert "requests" not in imports
    assert "psycopg" not in imports
    assert "sqlite3" not in imports


def test_hockey_injury_cluster_digest_rejects_each_false_report_only_flag() -> None:
    summary = report((cluster_item(),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]

    false_flag_cases = (
        ("config paper_only", lambda: config(paper_only=False)),
        ("config report_only", lambda: config(report_only=False)),
        ("config readonly", lambda: config(readonly=False)),
        ("item paper_only", lambda: cluster_item(paper_only=False)),
        ("item report_only", lambda: cluster_item(report_only=False)),
        ("item readonly", lambda: cluster_item(readonly=False)),
        ("row paper_only", lambda: replace(row, paper_only=False)),
        ("row report_only", lambda: replace(row, report_only=False)),
        ("row readonly", lambda: replace(row, readonly=False)),
        ("reason count paper_only", lambda: replace(reason_count, paper_only=False)),
        ("reason count report_only", lambda: replace(reason_count, report_only=False)),
        ("reason count readonly", lambda: replace(reason_count, readonly=False)),
        ("report paper_only", lambda: replace(summary, paper_only=False)),
        ("report report_only", lambda: replace(summary, report_only=False)),
        ("report readonly", lambda: replace(summary, readonly=False)),
    )
    for label, make_value in false_flag_cases:
        flag_name = label.rsplit(" ", 1)[1]
        with pytest.raises(ValueError, match=f"{flag_name} must be True"):
            make_value()


def test_hockey_injury_cluster_digest_rejects_inconsistent_constructed_outputs() -> None:
    row = report((cluster_item(),)).rows[0]

    with pytest.raises(ValueError, match="digest_status"):
        replace(row, digest_status="blocked")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            row,
            reason_codes=("market_research_hockey_injury_cluster_digest_no_inputs",),
        )

    reason_count = MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
        reason_code="market_research_hockey_injury_cluster_digest_ready",
        count=d("1.000000"),
        item_ratio=d("1.000000"),
    )
    with pytest.raises(ValueError, match="item_count"):
        MarketResearchHockeyInjuryClusterDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_MARKET_RESEARCH_HOCKEY_INJURY_CLUSTER_DIGEST_CONFIG_VERSION
            ),
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_hockey_injury_cluster_digest"
            ),
            item_count=d("2.000000"),
            ready_item_count=d("1.000000"),
            watch_item_count=d("0.000000"),
            blocked_item_count=d("0.000000"),
            stale_cluster_item_count=d("0.000000"),
            source_gap_item_count=d("0.000000"),
            thin_cluster_item_count=d("0.000000"),
            low_cluster_confidence_item_count=d("0.000000"),
            high_cluster_severity_item_count=d("0.000000"),
            liquidity_gap_item_count=d("0.000000"),
            average_confidence_score=d("0.820000"),
            max_cluster_age_seconds=d("5400.000000"),
            critical_cluster_age_seconds=d("1800.000000"),
            min_source_count=d("2.000000"),
            min_independent_source_count=d("2.000000"),
            min_team_injury_count=d("2.000000"),
            min_cluster_confidence_score=d("0.650000"),
            high_cluster_severity_threshold=d("0.750000"),
            min_market_liquidity_score=d("0.550000"),
            max_observed_cluster_age_seconds=d("1200.000000"),
            rows=(row,),
            item_config_versions=(("nhl.rangers.bruins.game-7", "hockey-injury-cluster-v0"),),
            reason_code_counts=(reason_count,),
            reason_codes=("market_research_hockey_injury_cluster_digest_ready",),
        )
