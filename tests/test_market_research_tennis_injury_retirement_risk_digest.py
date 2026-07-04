from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_tennis_injury_retirement_risk_digest",
    )


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_TENNIS_INJURY_RETIREMENT_RISK_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("3600.000000"),
        "min_source_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "min_confirmation_ratio": d("0.600000"),
        "min_injury_confidence_score": d("0.650000"),
        "high_injury_severity_threshold": d("0.750000"),
        "high_retirement_risk_threshold": d("0.700000"),
        "min_market_liquidity_score": d("0.550000"),
        "max_conflicting_source_count": d("0.000000"),
    }
    values.update(overrides)
    return module.MarketResearchTennisInjuryRetirementRiskDigestConfig(**values)


def injury_item(
    condition_id: str = "condition.tennis.injury.alcaraz",
    *,
    tennis_event_key: str = "atp.wimbledon.alcaraz.sinner.sf",
    tour_key: str = "atp",
    tournament_key: str = "wimbledon",
    round_key: str = "semifinal",
    player_key: str = "carlos-alcaraz",
    opponent_key: str = "jannik-sinner",
    injury_key: str = "right-leg",
    public_signal_reference: str = "atp-official-media-note",
    observed_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    independent_source_count: Decimal = d("3.000000"),
    confirmed_source_count: Decimal = d("3.000000"),
    conflicting_source_count: Decimal = d("0.000000"),
    injury_confidence_score: Decimal = d("0.800000"),
    injury_severity_score: Decimal = d("0.300000"),
    retirement_risk_score: Decimal = d("0.100000"),
    market_liquidity_score: Decimal = d("0.800000"),
    item_config_version: str = "tennis-injury-retirement-risk-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.MarketResearchTennisInjuryRetirementRiskDigestItem(
        condition_id=condition_id,
        tennis_event_key=tennis_event_key,
        tour_key=tour_key,
        tournament_key=tournament_key,
        round_key=round_key,
        player_key=player_key,
        opponent_key=opponent_key,
        injury_key=injury_key,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=20),
        source_count=source_count,
        independent_source_count=independent_source_count,
        confirmed_source_count=confirmed_source_count,
        conflicting_source_count=conflicting_source_count,
        injury_confidence_score=injury_confidence_score,
        injury_severity_score=injury_severity_score,
        retirement_risk_score=retirement_risk_score,
        market_liquidity_score=market_liquidity_score,
        item_config_version=item_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    items: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_market_research_tennis_injury_retirement_risk_digest(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_tennis_injury_retirement_risk_digest_reduces_conflict_retirement_and_freshness_gaps() -> None:
    module = api()
    summary = report(
        (
            injury_item(
                "condition.blocked",
                tennis_event_key="atp.wimbledon.playera.playerb.qf",
                player_key="player-a",
                opponent_key="player-b",
                public_signal_reference="https://tennis.example/injury?token=secret-ace",
                observed_at=GENERATED_AT - timedelta(hours=2),
                source_count=d("1.000000"),
                independent_source_count=d("1.000000"),
                confirmed_source_count=d("0.000000"),
                conflicting_source_count=d("1.000000"),
                injury_confidence_score=d("0.500000"),
                injury_severity_score=d("0.900000"),
                retirement_risk_score=d("0.850000"),
                market_liquidity_score=d("0.450000"),
            ),
            injury_item(
                "condition.watch",
                tennis_event_key="wta.roland-garros.playerc.playerd.final",
                tour_key="wta",
                tournament_key="roland-garros",
                round_key="final",
                player_key="player-c",
                opponent_key="player-d",
                injury_key="left-shoulder",
                public_signal_reference="beat-report-redacted-reference",
                observed_at=GENERATED_AT - timedelta(minutes=45),
                source_count=d("2.000000"),
                independent_source_count=d("1.000000"),
                confirmed_source_count=d("1.000000"),
                injury_confidence_score=d("0.600000"),
                injury_severity_score=d("0.800000"),
                retirement_risk_score=d("0.400000"),
                market_liquidity_score=d("0.500000"),
            ),
            injury_item(
                "condition.ready",
                tennis_event_key="atp.us-open.playere.playerf.r16",
                tournament_key="us-open",
                round_key="round-16",
                player_key="player-e",
                opponent_key="player-f",
                injury_key="no-material-injury",
                public_signal_reference="atp-official-media-note",
                source_count=d("4.000000"),
                independent_source_count=d("3.000000"),
                confirmed_source_count=d("4.000000"),
                injury_confidence_score=d("0.850000"),
                injury_severity_score=d("0.300000"),
                retirement_risk_score=d("0.100000"),
                market_liquidity_score=d("0.900000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(
        summary,
        module.MarketResearchTennisInjuryRetirementRiskDigestReport,
    )
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_TENNIS_INJURY_RETIREMENT_RISK_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_tennis_injury_retirement_risk_digest"
    )
    assert summary.item_count == d("3.000000")
    assert summary.ready_item_count == d("1.000000")
    assert summary.watch_item_count == d("1.000000")
    assert summary.blocked_item_count == d("1.000000")
    assert summary.stale_signal_item_count == d("1.000000")
    assert summary.source_gap_item_count == d("2.000000")
    assert summary.confirmation_gap_item_count == d("2.000000")
    assert summary.conflict_item_count == d("1.000000")
    assert summary.low_injury_confidence_item_count == d("2.000000")
    assert summary.high_injury_severity_item_count == d("2.000000")
    assert summary.high_retirement_risk_item_count == d("1.000000")
    assert summary.liquidity_gap_item_count == d("2.000000")
    assert summary.source_count == d("7.000000")
    assert summary.independent_source_count == d("5.000000")
    assert summary.confirmed_source_count == d("5.000000")
    assert summary.conflicting_source_count == d("1.000000")
    assert summary.confirmation_ratio == d("0.714286")
    assert summary.source_diversity_ratio == d("0.714286")
    assert summary.average_retirement_risk_score == d("0.450000")
    assert summary.max_observed_signal_age_seconds == d("7200.000000")
    assert tuple(row.tennis_event_key for row in summary.rows) == (
        "atp.wimbledon.playera.playerb.qf",
        "wta.roland-garros.playerc.playerd.final",
        "atp.us-open.playere.playerf.r16",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.signal_age_seconds == d("7200.000000")
    assert blocked.confirmation_ratio == d("0.000000")
    assert blocked.source_diversity_ratio == d("1.000000")
    assert blocked.redacted_public_signal_reference == "sha256:effaa8988448"
    assert blocked.reason_codes == (
        "market_research_tennis_injury_retirement_risk_digest_conflicting_sources",
        "market_research_tennis_injury_retirement_risk_digest_high_injury_severity",
        "market_research_tennis_injury_retirement_risk_digest_high_retirement_risk",
        "market_research_tennis_injury_retirement_risk_digest_liquidity_gap",
        "market_research_tennis_injury_retirement_risk_digest_low_confirmation",
        "market_research_tennis_injury_retirement_risk_digest_low_injury_confidence",
        "market_research_tennis_injury_retirement_risk_digest_source_gap",
        "market_research_tennis_injury_retirement_risk_digest_stale_signal",
    )

    watched = summary.rows[1]
    assert watched.digest_status == "watch"
    assert watched.reason_codes == (
        "market_research_tennis_injury_retirement_risk_digest_high_injury_severity",
        "market_research_tennis_injury_retirement_risk_digest_liquidity_gap",
        "market_research_tennis_injury_retirement_risk_digest_low_confirmation",
        "market_research_tennis_injury_retirement_risk_digest_low_injury_confidence",
        "market_research_tennis_injury_retirement_risk_digest_source_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.reason_codes == (
        "market_research_tennis_injury_retirement_risk_digest_ready",
    )

    assert summary.reason_code_counts == (
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
            reason_code=(
                "market_research_tennis_injury_retirement_risk_digest_high_retirement_risk"
            ),
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
            reason_code=(
                "market_research_tennis_injury_retirement_risk_digest_high_injury_severity"
            ),
            count=d("2.000000"),
            item_ratio=d("0.666667"),
        ),
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
            reason_code="market_research_tennis_injury_retirement_risk_digest_liquidity_gap",
            count=d("2.000000"),
            item_ratio=d("0.666667"),
        ),
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
            reason_code="market_research_tennis_injury_retirement_risk_digest_low_confirmation",
            count=d("2.000000"),
            item_ratio=d("0.666667"),
        ),
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
            reason_code=(
                "market_research_tennis_injury_retirement_risk_digest_low_injury_confidence"
            ),
            count=d("2.000000"),
            item_ratio=d("0.666667"),
        ),
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
            reason_code=(
                "market_research_tennis_injury_retirement_risk_digest_conflicting_sources"
            ),
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
            reason_code="market_research_tennis_injury_retirement_risk_digest_ready",
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
            reason_code="market_research_tennis_injury_retirement_risk_digest_source_gap",
            count=d("2.000000"),
            item_ratio=d("0.666667"),
        ),
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
            reason_code="market_research_tennis_injury_retirement_risk_digest_stale_signal",
            count=d("1.000000"),
            item_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )
    assert summary.item_config_versions == (
        ("atp.us-open.playere.playerf.r16", "tennis-injury-retirement-risk-v0"),
        ("atp.wimbledon.playera.playerb.qf", "tennis-injury-retirement-risk-v0"),
        (
            "wta.roland-garros.playerc.playerd.final",
            "tennis-injury-retirement-risk-v0",
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    public = repr(asdict(summary)).lower()
    for forbidden in (
        "secret-ace",
        "tennis.example",
        "wallet",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "exchange",
        "order",
        "account",
        "advice",
        "private",
    ):
        assert forbidden not in public


def test_tennis_injury_retirement_risk_empty_inputs_are_report_only_and_deterministic() -> None:
    module = api()
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_tennis_injury_retirement_risk_digest"
    )
    assert summary.item_count == d("0.000000")
    assert summary.ready_item_count == d("0.000000")
    assert summary.watch_item_count == d("0.000000")
    assert summary.blocked_item_count == d("0.000000")
    assert summary.confirmation_ratio == d("0.000000")
    assert summary.source_diversity_ratio == d("0.000000")
    assert summary.average_retirement_risk_score == d("0.000000")
    assert summary.rows == ()
    assert summary.item_config_versions == ()
    assert summary.reason_codes == (
        "market_research_tennis_injury_retirement_risk_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
            reason_code="market_research_tennis_injury_retirement_risk_digest_no_inputs",
            count=d("1.000000"),
            item_ratio=d("0.000000"),
        ),
    )


def test_tennis_injury_retirement_risk_validates_exact_types_flags_utc_and_duplicates() -> None:
    module = api()
    for dataclass_type in (
        module.MarketResearchTennisInjuryRetirementRiskDigestConfig,
        module.MarketResearchTennisInjuryRetirementRiskDigestItem,
        module.MarketResearchTennisInjuryRetirementRiskDigestRow,
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount,
        module.MarketResearchTennisInjuryRetirementRiskDigestReport,
    ):
        assert dataclass_type.__dataclass_params__.frozen

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("tennis-injury-retirement-risk-v0"))
    with pytest.raises(ValueError, match="max_signal_age_seconds"):
        config(max_signal_age_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="min_confirmation_ratio"):
        config(min_confirmation_ratio=0.6)
    with pytest.raises(ValueError, match="min_source_count"):
        config(min_source_count=2)
    with pytest.raises(ValueError, match="condition_id"):
        injury_item(condition_id=_StringSubclass("condition.alpha"))
    with pytest.raises(ValueError, match="source_count"):
        injury_item(source_count=1.0)
    with pytest.raises(ValueError, match="confirmed_source_count"):
        injury_item(confirmed_source_count=Decimal("NaN"))
    with pytest.raises(ValueError, match="retirement_risk_score"):
        injury_item(retirement_risk_score=d("1.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (injury_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 4, 15, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        report((injury_item(),), generated_at=datetime(2026, 7, 4, 15, 0))
    with pytest.raises(ValueError, match="future"):
        report((injury_item(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="redacted"):
        injury_item(public_signal_reference="token=secret-ace")
    with pytest.raises(ValueError, match="source_count"):
        injury_item(independent_source_count=d("4.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        injury_item(paper_only=False)
    with pytest.raises(FrozenInstanceError):
        injury_item().paper_only = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="unique"):
        report(
            (
                injury_item(tennis_event_key="duplicate.event"),
                injury_item(tennis_event_key="duplicate.event"),
            ),
        )
    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "BadConfig",
            (module.MarketResearchTennisInjuryRetirementRiskDigestConfig,),
            {},
        )

    numeric_markers = (
        "_count",
        "_ratio",
        "_seconds",
        "_score",
        "_threshold",
    )
    for dataclass_type in (
        module.MarketResearchTennisInjuryRetirementRiskDigestConfig,
        module.MarketResearchTennisInjuryRetirementRiskDigestItem,
        module.MarketResearchTennisInjuryRetirementRiskDigestRow,
        module.MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount,
        module.MarketResearchTennisInjuryRetirementRiskDigestReport,
    ):
        for field in fields(dataclass_type):
            if any(field.name.endswith(marker) for marker in numeric_markers):
                assert field.type in (Decimal, "Decimal")


def test_tennis_injury_retirement_risk_payload_serializes_decimal_strings_and_no_live_io_surface() -> None:
    module = api()
    summary = report((injury_item(),))
    payload = module.market_research_tennis_injury_retirement_risk_digest_payload(summary)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["item_count"] == "1.000000"
    assert payload["rows"][0]["retirement_risk_score"] == "0.100000"
    assert payload["generated_at"] == "2026-07-04T15:00:00+00:00"
    assert not any(isinstance(value, float) for value in walk_values(payload))

    source = Path(
        "src/polymarket_alpha_lab/market_research_tennis_injury_retirement_risk_digest.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    attribute_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
        if isinstance(node, ast.Attribute):
            attribute_names.add(node.attr)
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
    )
    forbidden_call_or_attribute_names = {
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "getenv",
        "insert",
        "open",
        "persist",
        "rollback",
        "send",
        "write",
    }
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
    assert not (call_names & forbidden_call_or_attribute_names)
    assert not (attribute_names & forbidden_call_or_attribute_names)
    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange mutation",
        "account",
        "auth",
        "secret",
        "token",
        "advice",
        "fast",
    ):
        assert forbidden not in source.lower()


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
