from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 4, 18, 0, tzinfo=UTC)
BASE_OBSERVED_AT = datetime(2026, 7, 4, 15, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-hockey-goalie-start-digest-test-v0"


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_research_hockey_goalie_start_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides):
    digest = module()
    values = {
        "config_version": CONFIG_VERSION,
        "max_start_report_age_seconds": d("3600.000000"),
        "max_observation_age_seconds": d("5400.000000"),
        "min_source_count": d("2.000000"),
        "min_independent_source_count": d("2.000000"),
        "min_confirmation_ratio": d("0.666667"),
        "fatigue_watch_threshold": d("0.600000"),
        "late_scratch_watch_threshold": d("0.300000"),
        "confidence_decay_per_stale_start": d("0.150000"),
        "confidence_decay_per_source_gap": d("0.100000"),
        "confidence_decay_per_confirmation_gap": d("0.100000"),
        "confidence_decay_per_fatigue": d("0.050000"),
        "confidence_decay_per_late_scratch": d("0.050000"),
    }
    values.update(overrides)
    return digest.MarketResearchHockeyGoalieStartDigestConfig(**values)


def observation(
    research_key: str = "research.nhl.nyr.shesterkin",
    *,
    condition_id: str = "condition_nhl_nyr_bos_goalie",
    game_key: str = "nhl.nyr.bos.20260704",
    team_key: str = "nyr",
    goalie_key: str = "goalie.shesterkin",
    public_source_reference: str = "nhl-official-starter-report",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=45),
    start_reported_at: datetime | None = GENERATED_AT - timedelta(minutes=40),
    source_count: Decimal = d("2.000000"),
    independent_source_count: Decimal = d("2.000000"),
    confirming_source_count: Decimal = d("2.000000"),
    conflicting_source_count: Decimal = d("0.000000"),
    back_to_back_start_flag: bool = False,
    recent_workload_score: Decimal = d("0.200000"),
    late_scratch_risk_score: Decimal = d("0.050000"),
    base_confidence_score: Decimal = d("0.850000"),
    source_config_version: str = "goalie-start-source-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    digest = module()
    return digest.MarketResearchHockeyGoalieStartDigestObservation(
        research_key=research_key,
        condition_id=condition_id,
        game_key=game_key,
        team_key=team_key,
        goalie_key=goalie_key,
        public_source_reference=public_source_reference,
        observed_at=observed_at,
        start_reported_at=start_reported_at,
        source_count=source_count,
        independent_source_count=independent_source_count,
        confirming_source_count=confirming_source_count,
        conflicting_source_count=conflicting_source_count,
        back_to_back_start_flag=back_to_back_start_flag,
        recent_workload_score=recent_workload_score,
        late_scratch_risk_score=late_scratch_risk_score,
        base_confidence_score=base_confidence_score,
        source_config_version=source_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations, **overrides):
    digest = module()
    values = {
        "observations": observations,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return digest.build_market_research_hockey_goalie_start_digest(**values)


def test_goalie_start_digest_flags_stale_thin_conflicted_fatigue_and_late_scratch_context() -> None:
    report = build_report(
        observation(
            "research.nhl.nyr.shesterkin",
            game_key="nhl.nyr.bos.20260704",
            team_key="nyr",
            goalie_key="goalie.shesterkin",
            public_source_reference="https://nhl.example/starters?api_key=redacted-test",
            observed_at=GENERATED_AT - timedelta(hours=2),
            start_reported_at=GENERATED_AT - timedelta(hours=3),
            source_count=d("1.000000"),
            independent_source_count=d("1.000000"),
            confirming_source_count=d("0.000000"),
            conflicting_source_count=d("1.000000"),
            back_to_back_start_flag=True,
            recent_workload_score=d("0.750000"),
            late_scratch_risk_score=d("0.400000"),
            base_confidence_score=d("0.900000"),
            source_config_version="goalie-feed-v1",
        ),
        observation(
            "research.nhl.dal.oettinger",
            game_key="nhl.dal.col.20260704",
            team_key="dal",
            goalie_key="goalie.oettinger",
            observed_at=datetime(
                2026,
                7,
                4,
                13,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            start_reported_at=datetime(
                2026,
                7,
                4,
                13,
                15,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            source_count=d("3.000000"),
            independent_source_count=d("3.000000"),
            confirming_source_count=d("3.000000"),
            base_confidence_score=d("0.820000"),
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_market_research_hockey_goalie_start_digest"
    )
    assert report.observation_count == d("2")
    assert report.ready_observation_count == d("1")
    assert report.watch_observation_count == d("0")
    assert report.blocked_observation_count == d("1")
    assert report.stale_start_report_count == d("1")
    assert report.stale_observation_count == d("1")
    assert report.thin_source_count == d("1")
    assert report.source_diversity_gap_count == d("1")
    assert report.confirmation_gap_count == d("1")
    assert report.conflicting_source_count == d("1")
    assert report.back_to_back_start_count == d("1")
    assert report.workload_fatigue_count == d("1")
    assert report.late_scratch_risk_count == d("1")
    assert report.average_confidence_score == d("0.585000")
    assert report.max_start_report_age_seconds == d("10800.000000")
    assert report.max_observation_age_seconds == d("7200.000000")
    assert report.average_source_count == d("2.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.game_key, row.goalie_key) for row in report.rows) == (
        ("nhl.nyr.bos.20260704", "goalie.shesterkin"),
        ("nhl.dal.col.20260704", "goalie.oettinger"),
    )

    blocked = report.rows[0]
    assert blocked.start_status == "blocked"
    assert blocked.observation_age_seconds == d("7200.000000")
    assert blocked.start_report_age_seconds == d("10800.000000")
    assert blocked.source_confirmation_ratio == d("0.000000")
    assert blocked.source_diversity_ratio == d("1.000000")
    assert blocked.confidence_decay_score == d("0.550000")
    assert blocked.confidence_score == d("0.350000")
    assert blocked.redacted_public_source_reference == "sha256:d2d9d8df39ce"
    assert blocked.reason_codes == (
        "market_research_hockey_goalie_start_digest_back_to_back_start",
        "market_research_hockey_goalie_start_digest_confirmation_gap",
        "market_research_hockey_goalie_start_digest_conflicting_sources",
        "market_research_hockey_goalie_start_digest_late_scratch_risk",
        "market_research_hockey_goalie_start_digest_source_diversity_gap",
        "market_research_hockey_goalie_start_digest_stale_observation",
        "market_research_hockey_goalie_start_digest_stale_start_report",
        "market_research_hockey_goalie_start_digest_thin_sources",
        "market_research_hockey_goalie_start_digest_workload_fatigue",
    )

    ready = report.rows[1]
    assert ready.start_status == "ready"
    assert ready.observed_at == datetime(2026, 7, 4, 17, 30, tzinfo=UTC)
    assert ready.start_reported_at == datetime(2026, 7, 4, 17, 15, tzinfo=UTC)
    assert ready.confidence_score == d("0.820000")
    assert ready.reason_codes == (
        "market_research_hockey_goalie_start_digest_ready",
    )

    assert report.reason_codes == (
        "market_research_hockey_goalie_start_digest_back_to_back_start",
        "market_research_hockey_goalie_start_digest_confirmation_gap",
        "market_research_hockey_goalie_start_digest_conflicting_sources",
        "market_research_hockey_goalie_start_digest_late_scratch_risk",
        "market_research_hockey_goalie_start_digest_ready",
        "market_research_hockey_goalie_start_digest_source_diversity_gap",
        "market_research_hockey_goalie_start_digest_stale_observation",
        "market_research_hockey_goalie_start_digest_stale_start_report",
        "market_research_hockey_goalie_start_digest_thin_sources",
        "market_research_hockey_goalie_start_digest_workload_fatigue",
    )
    assert report.reason_code_counts == (
        module().MarketResearchHockeyGoalieStartDigestReasonCodeCount(
            reason_code="market_research_hockey_goalie_start_digest_back_to_back_start",
            observation_count=d("1"),
            observation_ratio=d("0.500000"),
        ),
        module().MarketResearchHockeyGoalieStartDigestReasonCodeCount(
            reason_code="market_research_hockey_goalie_start_digest_confirmation_gap",
            observation_count=d("1"),
            observation_ratio=d("0.500000"),
        ),
        module().MarketResearchHockeyGoalieStartDigestReasonCodeCount(
            reason_code="market_research_hockey_goalie_start_digest_conflicting_sources",
            observation_count=d("1"),
            observation_ratio=d("0.500000"),
        ),
        module().MarketResearchHockeyGoalieStartDigestReasonCodeCount(
            reason_code="market_research_hockey_goalie_start_digest_late_scratch_risk",
            observation_count=d("1"),
            observation_ratio=d("0.500000"),
        ),
        module().MarketResearchHockeyGoalieStartDigestReasonCodeCount(
            reason_code="market_research_hockey_goalie_start_digest_ready",
            observation_count=d("1"),
            observation_ratio=d("0.500000"),
        ),
        module().MarketResearchHockeyGoalieStartDigestReasonCodeCount(
            reason_code="market_research_hockey_goalie_start_digest_source_diversity_gap",
            observation_count=d("1"),
            observation_ratio=d("0.500000"),
        ),
        module().MarketResearchHockeyGoalieStartDigestReasonCodeCount(
            reason_code="market_research_hockey_goalie_start_digest_stale_observation",
            observation_count=d("1"),
            observation_ratio=d("0.500000"),
        ),
        module().MarketResearchHockeyGoalieStartDigestReasonCodeCount(
            reason_code="market_research_hockey_goalie_start_digest_stale_start_report",
            observation_count=d("1"),
            observation_ratio=d("0.500000"),
        ),
        module().MarketResearchHockeyGoalieStartDigestReasonCodeCount(
            reason_code="market_research_hockey_goalie_start_digest_thin_sources",
            observation_count=d("1"),
            observation_ratio=d("0.500000"),
        ),
        module().MarketResearchHockeyGoalieStartDigestReasonCodeCount(
            reason_code="market_research_hockey_goalie_start_digest_workload_fatigue",
            observation_count=d("1"),
            observation_ratio=d("0.500000"),
        ),
    )
    assert report.source_config_versions == (
        ("goalie.oettinger", "goalie-start-source-v0"),
        ("goalie.shesterkin", "goalie-feed-v1"),
    )


def test_empty_and_missing_starter_inputs_return_passive_report_only_statuses() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.recommended_next_step == (
        "allow_report_only_market_research_hockey_goalie_start_digest"
    )
    assert empty_report.observation_count == d("0")
    assert empty_report.rows == ()
    assert empty_report.reason_codes == (
        "market_research_hockey_goalie_start_digest_no_inputs",
    )

    watch_report = build_report(
        observation(
            "research.nhl.sea.daccord",
            game_key="nhl.sea.van.20260704",
            team_key="sea",
            goalie_key="goalie.daccord",
            start_reported_at=None,
        ),
    )

    assert watch_report.digest_status == "watch"
    assert watch_report.watch_observation_count == d("1")
    assert watch_report.rows[0].start_status == "watch"
    assert watch_report.rows[0].start_report_age_seconds is None
    assert watch_report.rows[0].reason_codes == (
        "market_research_hockey_goalie_start_digest_missing_start_report",
    )


def test_payload_helper_uses_json_ready_scalars_without_sensitive_surface() -> None:
    digest = module()
    report = build_report(
        observation(
            "research.nhl.payload",
            game_key="nhl.payload.test.20260704",
            goalie_key="goalie.payload",
            public_source_reference="private-goalie-start-feed",
            observed_at=GENERATED_AT - timedelta(minutes=45),
            start_reported_at=GENERATED_AT - timedelta(minutes=40),
        ),
    )

    payload = digest.market_research_hockey_goalie_start_digest_payload(report)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["observation_count"] == "1.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T17:15:00+00:00"
    assert payload["rows"][0]["confidence_score"] == "0.850000"
    assert payload["rows"][0]["redacted_public_source_reference"] == (
        "sha256:979fd5d9e876"
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))

    payload_text = repr(payload).lower()
    for forbidden in (
        "wallet",
        "broker",
        "order",
        "account",
        "advice",
        "auth",
        "signing",
        "submit",
        "cancel",
        "secret",
        "token",
        "private",
    ):
        assert forbidden not in payload_text


def test_dataclasses_validate_decimal_datetime_flags_consistency_and_types() -> None:
    digest = module()

    row = observation()
    with pytest.raises(FrozenInstanceError):
        row.source_count = d("3.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        observation(source_count=2)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 4, 15, 0))

    with pytest.raises(ValueError, match="research_key must be a string"):
        observation(research_key=_StringSubclass("research.nhl.bad"))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(
            observation(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 18, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="min_confirmation_ratio"):
        config(min_confirmation_ratio=_DecimalSubclass("0.666667"))

    with pytest.raises(ValueError, match="source_count"):
        observation(source_count=d("1.500000"))

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="observations must not contain duplicate"):
        build_report(observation(), observation(source_config_version="goalie-feed-v2"))

    report = build_report(observation())
    bad_report_values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
    }
    bad_report_values["observation_count"] = d("2")
    with pytest.raises(ValueError, match="observation_count"):
        digest.MarketResearchHockeyGoalieStartDigestReport(**bad_report_values)


def test_module_scope_has_no_io_live_trading_float_or_durable_store_surface() -> None:
    source_text = Path(
        "src/polymarket_alpha_lab/market_research_hockey_goalie_start_digest.py",
    ).read_text(encoding="utf-8")
    lowered = source_text.lower()

    for forbidden in (
        "live trading",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "auth",
        "private",
        "secret",
        "token",
        "open(",
        "requests",
        "http",
        "socket",
        "psycopg",
        "sqlite",
        "sql",
        "float(",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
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
        "db",
        "env",
        "requests",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _walk_payload_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_payload_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_payload_values(item)
    else:
        yield value
