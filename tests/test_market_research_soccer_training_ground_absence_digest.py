from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
BASE_MATCH_START_AT = datetime(2026, 7, 4, 16, 0, tzinfo=UTC)
CONFIG_VERSION = "market-research-soccer-training-ground-absence-digest-test-v0"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "market_research_soccer_training_ground_absence_digest.py",
)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab."
        "market_research_soccer_training_ground_absence_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": CONFIG_VERSION,
        "blocked_risk_score_threshold": d("0.700000"),
        "watch_risk_score_threshold": d("0.400000"),
        "blocked_absence_count": d("2"),
        "watch_absence_count": d("1"),
        "high_role_importance_threshold": d("0.700000"),
        "high_lineup_dependency_threshold": d("0.600000"),
        "match_proximity_blocked_hours": d("6.000000"),
        "match_proximity_watch_hours": d("36.000000"),
        "max_source_age_hours": d("6.000000"),
        "max_source_disagreement_count": d("0"),
    }
    values.update(overrides)
    return module.MarketResearchSoccerTrainingGroundAbsenceDigestConfig(**values)


def signal(
    condition_id: str = "condition_alpha",
    market_slug: str = "arsenal-chelsea-player-starts",
    club: str = "arsenal",
    player: str = "player_alpha",
    opponent: str = "chelsea",
    match_ref: str = "arsenal_chelsea",
    *,
    match_start_at: datetime = BASE_MATCH_START_AT,
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    absence_count: Decimal = d("0"),
    role_importance_score: Decimal = d("0.100000"),
    lineup_dependency_score: Decimal = d("0.100000"),
    source_disagreement_count: Decimal = d("0"),
    upstream_reason_codes: tuple[str, ...] = (),
    signal_ref: str = "local_training_absence_feed_v0",
    signal_config_version: str = "soccer-training-ground-absence-feed-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.MarketResearchSoccerTrainingGroundAbsenceDigestSignal(
        condition_id=condition_id,
        market_slug=market_slug,
        club=club,
        player=player,
        opponent=opponent,
        match_ref=match_ref,
        match_start_at=match_start_at,
        observed_at=observed_at,
        absence_count=absence_count,
        role_importance_score=role_importance_score,
        lineup_dependency_score=lineup_dependency_score,
        source_disagreement_count=source_disagreement_count,
        upstream_reason_codes=upstream_reason_codes,
        signal_ref=signal_ref,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*signals: object, **overrides: object):
    module = api()
    values: dict[str, object] = {
        "signals": signals,
        "config": config(),
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.build_market_research_soccer_training_ground_absence_digest(
        **values,
    )


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in {float, int}:
        pytest.fail(f"found public number in JSON payload: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_public_number_payload(child)
    if isinstance(value, list):
        for child in value:
            assert_no_public_number_payload(child)


def test_digest_flags_blocked_watch_and_pass_training_ground_absence() -> None:
    module = api()

    report = build_report(
        signal(
            "condition_watch",
            "psg-bayern-player-absence-impact",
            "psg",
            "player_watch",
            "bayern",
            "psg_bayern",
            match_start_at=GENERATED_AT + timedelta(hours=20),
            observed_at=GENERATED_AT - timedelta(hours=7),
            absence_count=d("1"),
            role_importance_score=d("0.550000"),
            lineup_dependency_score=d("0.650000"),
            upstream_reason_codes=("limited_training_absence",),
            signal_config_version="soccer-training-ground-absence-feed-v1",
        ),
        signal(
            "condition_pass",
            "milan-inter-player-appearance",
            "milan",
            "player_clear",
            "inter",
            "milan_inter",
            match_start_at=GENERATED_AT + timedelta(hours=48),
            observed_at=GENERATED_AT - timedelta(minutes=30),
            absence_count=d("0"),
            role_importance_score=d("0.200000"),
            lineup_dependency_score=d("0.100000"),
        ),
        signal(
            "condition_blocked",
            "liverpool-chelsea-player-minutes",
            "liverpool",
            "player_blocked",
            "chelsea",
            "liverpool_chelsea",
            match_start_at=BASE_MATCH_START_AT,
            observed_at=GENERATED_AT - timedelta(hours=3),
            absence_count=d("3"),
            role_importance_score=d("0.900000"),
            lineup_dependency_score=d("0.800000"),
            source_disagreement_count=d("1"),
            upstream_reason_codes=("first_team_absence_confirmed",),
            signal_config_version="soccer-training-ground-absence-feed-v2",
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG_VERSION
    assert report.digest_status == "blocked"
    assert report.recommended_next_step == (
        "block_report_only_soccer_training_ground_absence_review"
    )
    assert report.signal_count == d("3.000000")
    assert report.pass_signal_count == d("1.000000")
    assert report.watch_signal_count == d("1.000000")
    assert report.blocked_signal_count == d("1.000000")
    assert report.source_disagreement_signal_count == d("1.000000")
    assert report.blocked_risk_signal_count == d("1.000000")
    assert report.watch_risk_signal_count == d("1.000000")
    assert report.blocked_absence_signal_count == d("1.000000")
    assert report.watch_absence_signal_count == d("1.000000")
    assert report.high_role_importance_signal_count == d("1.000000")
    assert report.high_lineup_dependency_signal_count == d("2.000000")
    assert report.close_match_signal_count == d("1.000000")
    assert report.stale_source_signal_count == d("1.000000")
    assert report.upstream_reason_signal_count == d("2.000000")
    assert report.max_risk_score == d("0.873333")
    assert report.average_risk_score == d("0.491111")
    assert report.reason_codes == (
        "soccer_training_ground_absence_source_disagreement",
        "soccer_training_ground_absence_risk_score_blocked",
        "soccer_training_ground_absence_absence_count_blocked",
        "soccer_training_ground_absence_match_proximity_blocked",
        "soccer_training_ground_absence_risk_score_watch",
        "soccer_training_ground_absence_absence_count_watch",
        "soccer_training_ground_absence_role_importance_high",
        "soccer_training_ground_absence_lineup_dependency_high",
        "soccer_training_ground_absence_source_stale",
        "soccer_training_ground_absence_upstream_reason_present",
    )
    assert report.reason_code_counts == (
        module.MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount(
            reason_code="soccer_training_ground_absence_source_disagreement",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount(
            reason_code="soccer_training_ground_absence_risk_score_blocked",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount(
            reason_code="soccer_training_ground_absence_absence_count_blocked",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount(
            reason_code="soccer_training_ground_absence_match_proximity_blocked",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount(
            reason_code="soccer_training_ground_absence_risk_score_watch",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount(
            reason_code="soccer_training_ground_absence_absence_count_watch",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount(
            reason_code="soccer_training_ground_absence_role_importance_high",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount(
            reason_code="soccer_training_ground_absence_lineup_dependency_high",
            signal_count=d("2.000000"),
        ),
        module.MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount(
            reason_code="soccer_training_ground_absence_source_stale",
            signal_count=d("1.000000"),
        ),
        module.MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount(
            reason_code="soccer_training_ground_absence_upstream_reason_present",
            signal_count=d("2.000000"),
        ),
    )
    assert report.signal_config_versions == (
        (
            "liverpool_chelsea",
            "liverpool",
            "player_blocked",
            "soccer-training-ground-absence-feed-v2",
        ),
        (
            "milan_inter",
            "milan",
            "player_clear",
            "soccer-training-ground-absence-feed-v0",
        ),
        (
            "psg_bayern",
            "psg",
            "player_watch",
            "soccer-training-ground-absence-feed-v1",
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.condition_id for row in report.rows) == (
        "condition_blocked",
        "condition_watch",
        "condition_pass",
    )
    blocked = report.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.absence_count == d("3.000000")
    assert blocked.match_proximity_hours == d("4.000000")
    assert blocked.source_age_hours == d("3.000000")
    assert blocked.risk_score == d("0.873333")
    assert blocked.reason_codes == (
        "soccer_training_ground_absence_source_disagreement",
        "soccer_training_ground_absence_risk_score_blocked",
        "soccer_training_ground_absence_absence_count_blocked",
        "soccer_training_ground_absence_match_proximity_blocked",
        "soccer_training_ground_absence_role_importance_high",
        "soccer_training_ground_absence_lineup_dependency_high",
        "soccer_training_ground_absence_upstream_reason_present",
    )
    watch = report.rows[1]
    assert watch.digest_status == "watch"
    assert watch.match_proximity_hours == d("20.000000")
    assert watch.source_age_hours == d("7.000000")
    assert watch.risk_score == d("0.531667")
    assert watch.reason_codes == (
        "soccer_training_ground_absence_risk_score_watch",
        "soccer_training_ground_absence_absence_count_watch",
        "soccer_training_ground_absence_lineup_dependency_high",
        "soccer_training_ground_absence_source_stale",
        "soccer_training_ground_absence_upstream_reason_present",
    )
    passed = report.rows[2]
    assert passed.digest_status == "pass"
    assert passed.risk_score == d("0.068333")
    assert passed.reason_codes == ("soccer_training_ground_absence_clear",)


def test_empty_and_clear_inputs_pass_with_decimal_zeroes() -> None:
    empty_report = build_report()

    assert empty_report.digest_status == "pass"
    assert empty_report.signal_count == d("0.000000")
    assert empty_report.rows == ()
    assert empty_report.reason_codes == ("soccer_training_ground_absence_empty",)
    assert empty_report.reason_code_counts == ()
    assert empty_report.max_risk_score == d("0.000000")
    assert empty_report.average_risk_score == d("0.000000")

    clear_report = build_report(
        signal(
            "condition_clear",
            "real-betis-player-appearance",
            "real",
            "player_clear",
            "betis",
            "real_betis",
            match_start_at=GENERATED_AT + timedelta(hours=40),
            observed_at=GENERATED_AT - timedelta(minutes=15),
            absence_count=d("0"),
            role_importance_score=d("0.150000"),
            lineup_dependency_score=d("0.150000"),
        ),
    )

    assert clear_report.digest_status == "pass"
    assert clear_report.reason_codes == ("soccer_training_ground_absence_passed",)
    assert clear_report.rows[0].digest_status == "pass"
    assert clear_report.rows[0].reason_codes == (
        "soccer_training_ground_absence_clear",
    )


def test_payload_helper_uses_six_decimal_strings_utc_datetimes_and_safe_text() -> None:
    module = api()
    report = build_report(
        signal(
            "condition_payload",
            "dortmund-leipzig-player-minutes",
            "dortmund",
            "player_payload",
            "leipzig",
            "dortmund_leipzig",
            match_start_at=datetime(2026, 7, 4, 20, 0, tzinfo=timezone(timedelta(hours=2))),
            observed_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-3))),
            absence_count=d("1"),
            role_importance_score=d("0.600000"),
            lineup_dependency_score=d("0.700000"),
            source_disagreement_count=d("0"),
        ),
    )

    payload = module.market_research_soccer_training_ground_absence_digest_payload(
        report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["match_start_at"] == "2026-07-04T18:00:00+00:00"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T11:00:00+00:00"
    assert payload["rows"][0]["absence_count"] == "1.000000"
    assert payload["rows"][0]["match_proximity_hours"] == "6.000000"
    assert payload["rows"][0]["source_age_hours"] == "1.000000"
    assert payload["rows"][0]["risk_score"] == "0.526667"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_number_payload(payload)
    for token in (
        "wallet",
        "broker",
        "account",
        "auth",
        "signing",
        "submit",
        "cancel",
        "advice",
        "database",
        "persist",
        "private_key",
        "exchange",
    ):
        assert token not in encoded.lower()


def test_dataclasses_are_frozen_and_public_numeric_fields_are_decimal_only() -> None:
    cfg = config()
    item = signal()
    report = build_report(signal(absence_count=d("2"), role_importance_score=d("0.800000")))

    assert is_dataclass(cfg)
    assert is_dataclass(item)
    assert is_dataclass(report.rows[0])
    assert is_dataclass(report.reason_code_counts[0])
    with pytest.raises(FrozenInstanceError):
        cfg.blocked_risk_score_threshold = d("0.900000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        item.absence_count = d("1")  # type: ignore[misc]

    with pytest.raises(ValueError, match="blocked_risk_score_threshold must be a Decimal"):
        config(blocked_risk_score_threshold=1)
    with pytest.raises(ValueError, match="absence_count must be a Decimal"):
        signal(absence_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="risk_score must be a Decimal"):
        module = api()
        module.MarketResearchSoccerTrainingGroundAbsenceDigestRow(
            condition_id="condition_manual",
            market_slug="manual-player-minutes",
            club="manual",
            player="player_manual",
            opponent="opponent",
            match_ref="manual_match",
            match_start_at=BASE_MATCH_START_AT,
            observed_at=GENERATED_AT - timedelta(hours=1),
            absence_count=d("1"),
            role_importance_score=d("0.600000"),
            lineup_dependency_score=d("0.600000"),
            source_disagreement_count=d("0"),
            match_proximity_hours=d("4.000000"),
            source_age_hours=d("1.000000"),
            risk_score=_DecimalSubclass("0.500000"),
            upstream_reason_codes=(),
            signal_ref="manual_signal",
            digest_status="watch",
            reason_codes=("soccer_training_ground_absence_risk_score_watch",),
        )

    numeric_field_names = {
        "blocked_risk_score_threshold",
        "watch_risk_score_threshold",
        "blocked_absence_count",
        "watch_absence_count",
        "high_role_importance_threshold",
        "high_lineup_dependency_threshold",
        "match_proximity_blocked_hours",
        "match_proximity_watch_hours",
        "max_source_age_hours",
        "max_source_disagreement_count",
        "absence_count",
        "role_importance_score",
        "lineup_dependency_score",
        "source_disagreement_count",
        "match_proximity_hours",
        "source_age_hours",
        "risk_score",
        "signal_count",
        "pass_signal_count",
        "watch_signal_count",
        "blocked_signal_count",
        "source_disagreement_signal_count",
        "blocked_risk_signal_count",
        "watch_risk_signal_count",
        "blocked_absence_signal_count",
        "watch_absence_signal_count",
        "high_role_importance_signal_count",
        "high_lineup_dependency_signal_count",
        "close_match_signal_count",
        "stale_source_signal_count",
        "upstream_reason_signal_count",
        "max_risk_score",
        "average_risk_score",
        "signal_count",
    }
    for obj in (cfg, item, report, report.rows[0], report.reason_code_counts[0]):
        assert is_dataclass(obj)
        assert obj.__dataclass_params__.frozen
        for field_name, value in asdict(obj).items():
            if field_name in numeric_field_names:
                assert type(value) is Decimal
    for obj in (cfg, item, report, report.rows[0], report.reason_code_counts[0]):
        for field in fields(obj):
            if field.name in numeric_field_names:
                assert type(getattr(obj, field.name)) is Decimal


def test_validation_rejects_unsafe_inputs_subclasses_duplicates_and_stale_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="config_version must be a string"):
        config(config_version=_StringSubclass("test"))
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="match_start_at must not be in the past"):
        build_report(signal(match_start_at=GENERATED_AT - timedelta(seconds=1)))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        build_report(signal(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="market_slug contains unsafe source detail"):
        signal(market_slug="wallet-private-player-minutes")
    with pytest.raises(ValueError, match="upstream_reason_codes must be sorted"):
        signal(upstream_reason_codes=("zeta_reason", "alpha_reason"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="signals must not contain duplicate"):
        build_report(signal(match_ref="dup_match"), signal(match_ref="dup_match"))

    report = build_report(
        signal(
            "condition_blocked",
            "liverpool-chelsea-player-minutes",
            "liverpool",
            "player_blocked",
            "chelsea",
            "liverpool_chelsea",
            absence_count=d("3"),
            role_importance_score=d("0.900000"),
            lineup_dependency_score=d("0.800000"),
            source_disagreement_count=d("1"),
        ),
        signal(
            "condition_pass",
            "milan-inter-player-appearance",
            "milan",
            "player_clear",
            "inter",
            "milan_inter",
            match_start_at=GENERATED_AT + timedelta(hours=48),
        ),
    )
    with pytest.raises(ValueError, match="recommended_next_step must match digest_status"):
        replace(report, recommended_next_step="continue_report_only_absence_review")
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(report, rows=tuple(reversed(report.rows)))
    with pytest.raises(ValueError, match="reason_codes must be sorted"):
        module.MarketResearchSoccerTrainingGroundAbsenceDigestRow(
            condition_id="condition_manual",
            market_slug="manual-player-minutes",
            club="manual",
            player="player_manual",
            opponent="opponent",
            match_ref="manual_match",
            match_start_at=BASE_MATCH_START_AT,
            observed_at=GENERATED_AT - timedelta(hours=1),
            absence_count=d("2"),
            role_importance_score=d("0.900000"),
            lineup_dependency_score=d("0.900000"),
            source_disagreement_count=d("0"),
            match_proximity_hours=d("4.000000"),
            source_age_hours=d("1.000000"),
            risk_score=d("0.700000"),
            upstream_reason_codes=(),
            signal_ref="manual_signal",
            digest_status="blocked",
            reason_codes=(
                "soccer_training_ground_absence_absence_count_blocked",
                "soccer_training_ground_absence_risk_score_blocked",
            ),
        )


def test_module_exports_are_explicit_and_do_not_expose_live_or_external_io_surface() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text())

    exported = set(module.__all__)
    assert {
        "DEFAULT_MARKET_RESEARCH_SOCCER_TRAINING_GROUND_ABSENCE_DIGEST_CONFIG_VERSION",
        "MarketResearchSoccerTrainingGroundAbsenceDigestConfig",
        "MarketResearchSoccerTrainingGroundAbsenceDigestSignal",
        "MarketResearchSoccerTrainingGroundAbsenceDigestReasonCodeCount",
        "MarketResearchSoccerTrainingGroundAbsenceDigestRow",
        "MarketResearchSoccerTrainingGroundAbsenceDigestReport",
        "build_market_research_soccer_training_ground_absence_digest",
        "market_research_soccer_training_ground_absence_digest_payload",
    } <= exported

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "post",
        "put",
        "delete",
        "patch",
        "commit",
        "execute",
    }
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
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
        "http",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    source = MODULE_PATH.read_text().lower()
    public_text = "\n".join(
        name
        for name in exported
        if not name.startswith("_")
    ).lower()
    for token in (
        "wallet",
        "broker",
        "account",
        "auth",
        "signing",
        "live_trading",
        "exchange",
        "network",
        "secret",
        "database",
        "subprocess",
        "socket",
        "psycopg",
        "supabase",
        "private_key",
    ):
        assert token not in public_text
        assert token not in source
