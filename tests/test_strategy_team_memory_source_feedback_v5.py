from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import ModuleType

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_team_memory_source_feedback_v5"
GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def test_module_exports_expected_v5_api() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None
    module = _subject()

    for name in (
        "DEFAULT_STRATEGY_TEAM_MEMORY_SOURCE_FEEDBACK_V5_CONFIG_VERSION",
        "StrategyTeamMemorySourceFeedbackV5Config",
        "StrategyTeamMemorySourceFeedbackV5SettledRecommendation",
        "StrategyTeamMemorySourceFamilyScore",
        "StrategyTeamMemorySourceFeedbackV5Report",
        "build_strategy_team_memory_source_feedback_v5_report",
        "strategy_team_memory_source_feedback_v5_report_payload",
    ):
        assert hasattr(module, name)


def test_empty_settled_recommendations_return_readonly_watch_report_payload() -> None:
    module = _subject()

    report = module.build_strategy_team_memory_source_feedback_v5_report(
        (),
        config=module.StrategyTeamMemorySourceFeedbackV5Config(),
        generated_at=GENERATED_AT,
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        module.DEFAULT_STRATEGY_TEAM_MEMORY_SOURCE_FEEDBACK_V5_CONFIG_VERSION
    )
    assert report.source_feedback_status == "watch"
    assert report.recommendation_count == Decimal("0")
    assert report.source_family_count == Decimal("0")
    assert report.pass_family_count == Decimal("0")
    assert report.watch_family_count == Decimal("0")
    assert report.blocked_family_count == Decimal("0")
    assert report.accuracy_rate is None
    assert report.average_source_family_score is None
    assert report.source_family_scores == ()
    assert report.reason_codes == (
        "strategy_team_memory_source_feedback_v5_empty",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = module.strategy_team_memory_source_feedback_v5_report_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["source_feedback_status"] == "watch"
    assert payload["recommendation_count"] == "0"
    assert payload["accuracy_rate"] is None
    assert payload["source_family_scores"] == []
    json.dumps(payload, sort_keys=True)
    _assert_json_ready_without_decimal_or_float(payload)


def test_summarizes_source_family_accuracy_staleness_conflict_and_resolution_lag() -> None:
    module = _subject()
    report = module.build_strategy_team_memory_source_feedback_v5_report(
        (
            _settled(
                module,
                "rec_politics_a",
                team_id="politics",
                source_family="news",
                recommendation_recorded_at=GENERATED_AT - timedelta(seconds=7200),
                source_observed_at=GENERATED_AT - timedelta(seconds=9000),
                settled_at=GENERATED_AT - timedelta(seconds=3600),
                resolution_recorded_at=GENERATED_AT - timedelta(seconds=1800),
                predicted_outcome=True,
                resolved_outcome=True,
            ),
            _settled(
                module,
                "rec_politics_b",
                team_id="politics",
                source_family="news",
                recommendation_recorded_at=GENERATED_AT - timedelta(seconds=6900),
                source_observed_at=GENERATED_AT - timedelta(seconds=6960),
                settled_at=GENERATED_AT - timedelta(seconds=3300),
                resolution_recorded_at=GENERATED_AT - timedelta(seconds=2400),
                predicted_outcome=False,
                resolved_outcome=False,
            ),
            _settled(
                module,
                "rec_crypto_miss_stale_conflict_lag",
                team_id="crypto_btc",
                source_family="social",
                recommendation_recorded_at=GENERATED_AT - timedelta(seconds=10800),
                source_observed_at=GENERATED_AT - timedelta(seconds=20000),
                settled_at=GENERATED_AT - timedelta(seconds=9900),
                resolution_recorded_at=GENERATED_AT - timedelta(seconds=1800),
                predicted_outcome=True,
                resolved_outcome=False,
                source_conflict_count=Decimal("2"),
            ),
            _settled(
                module,
                "rec_crypto_pass",
                team_id="crypto_btc",
                source_family="social",
                recommendation_recorded_at=GENERATED_AT - timedelta(seconds=3000),
                source_observed_at=GENERATED_AT - timedelta(seconds=3300),
                settled_at=GENERATED_AT - timedelta(seconds=2700),
                resolution_recorded_at=GENERATED_AT - timedelta(seconds=900),
                predicted_outcome=True,
                resolved_outcome=True,
            ),
            _settled(
                module,
                "rec_soccer_blocked",
                team_id="sports_soccer",
                source_family="odds",
                recommendation_recorded_at=GENERATED_AT - timedelta(seconds=10900),
                source_observed_at=GENERATED_AT - timedelta(seconds=20000),
                settled_at=GENERATED_AT - timedelta(seconds=10800),
                resolution_recorded_at=GENERATED_AT - timedelta(seconds=3600),
                predicted_outcome=False,
                resolved_outcome=True,
                source_conflict_count=Decimal("1"),
            ),
        ),
        config=module.StrategyTeamMemorySourceFeedbackV5Config(
            max_source_age_seconds=Decimal("7200"),
            max_resolution_lag_seconds=Decimal("3600"),
            min_pass_accuracy_rate=Decimal("0.750000"),
            min_watch_accuracy_rate=Decimal("0.500000"),
            max_pass_staleness_rate=Decimal("0.250000"),
            max_watch_staleness_rate=Decimal("0.500000"),
            max_pass_conflict_rate=Decimal("0.250000"),
            max_watch_conflict_rate=Decimal("0.500000"),
            max_pass_resolution_lag_rate=Decimal("0.250000"),
            max_watch_resolution_lag_rate=Decimal("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.source_feedback_status == "blocked"
    assert report.recommendation_count == Decimal("5")
    assert report.source_family_count == Decimal("3")
    assert report.pass_family_count == Decimal("1")
    assert report.watch_family_count == Decimal("1")
    assert report.blocked_family_count == Decimal("1")
    assert report.correct_recommendation_count == Decimal("3")
    assert report.stale_source_count == Decimal("2")
    assert report.conflicted_recommendation_count == Decimal("2")
    assert report.resolution_lag_breach_count == Decimal("2")
    assert report.source_conflict_count == Decimal("3")
    assert report.accuracy_rate == Decimal("0.600000")
    assert report.staleness_rate == Decimal("0.400000")
    assert report.conflict_rate == Decimal("0.400000")
    assert report.resolution_lag_breach_rate == Decimal("0.400000")
    assert report.average_resolution_lag_seconds == Decimal("3960.000000")
    assert report.average_source_family_score == Decimal("0.500000")
    assert report.reason_codes == (
        "strategy_team_memory_source_feedback_v5_low_accuracy",
        "strategy_team_memory_source_feedback_v5_stale_sources",
        "strategy_team_memory_source_feedback_v5_conflicted_sources",
        "strategy_team_memory_source_feedback_v5_resolution_lag",
    )
    assert report.source_family_scores == (
        module.StrategyTeamMemorySourceFamilyScore(
            team_id="crypto_btc",
            source_family="social",
            recommendation_count=Decimal("2"),
            correct_recommendation_count=Decimal("1"),
            stale_source_count=Decimal("1"),
            conflicted_recommendation_count=Decimal("1"),
            resolution_lag_breach_count=Decimal("1"),
            source_conflict_count=Decimal("2"),
            accuracy_rate=Decimal("0.500000"),
            staleness_rate=Decimal("0.500000"),
            conflict_rate=Decimal("0.500000"),
            resolution_lag_breach_rate=Decimal("0.500000"),
            average_resolution_lag_seconds=Decimal("4950.000000"),
            source_family_score=Decimal("0.500000"),
            source_feedback_status="watch",
            reason_codes=(
                "strategy_team_memory_source_feedback_v5_low_accuracy",
                "strategy_team_memory_source_feedback_v5_stale_sources",
                "strategy_team_memory_source_feedback_v5_conflicted_sources",
                "strategy_team_memory_source_feedback_v5_resolution_lag",
            ),
            recommendation_ids=(
                "rec_crypto_miss_stale_conflict_lag",
                "rec_crypto_pass",
            ),
        ),
        module.StrategyTeamMemorySourceFamilyScore(
            team_id="politics",
            source_family="news",
            recommendation_count=Decimal("2"),
            correct_recommendation_count=Decimal("2"),
            stale_source_count=Decimal("0"),
            conflicted_recommendation_count=Decimal("0"),
            resolution_lag_breach_count=Decimal("0"),
            source_conflict_count=Decimal("0"),
            accuracy_rate=Decimal("1.000000"),
            staleness_rate=Decimal("0.000000"),
            conflict_rate=Decimal("0.000000"),
            resolution_lag_breach_rate=Decimal("0.000000"),
            average_resolution_lag_seconds=Decimal("1350.000000"),
            source_family_score=Decimal("1.000000"),
            source_feedback_status="pass",
            reason_codes=(
                "strategy_team_memory_source_feedback_v5_passed",
            ),
            recommendation_ids=("rec_politics_a", "rec_politics_b"),
        ),
        module.StrategyTeamMemorySourceFamilyScore(
            team_id="sports_soccer",
            source_family="odds",
            recommendation_count=Decimal("1"),
            correct_recommendation_count=Decimal("0"),
            stale_source_count=Decimal("1"),
            conflicted_recommendation_count=Decimal("1"),
            resolution_lag_breach_count=Decimal("1"),
            source_conflict_count=Decimal("1"),
            accuracy_rate=Decimal("0.000000"),
            staleness_rate=Decimal("1.000000"),
            conflict_rate=Decimal("1.000000"),
            resolution_lag_breach_rate=Decimal("1.000000"),
            average_resolution_lag_seconds=Decimal("7200.000000"),
            source_family_score=Decimal("0.000000"),
            source_feedback_status="blocked",
            reason_codes=(
                "strategy_team_memory_source_feedback_v5_low_accuracy",
                "strategy_team_memory_source_feedback_v5_stale_sources",
                "strategy_team_memory_source_feedback_v5_conflicted_sources",
                "strategy_team_memory_source_feedback_v5_resolution_lag",
            ),
            recommendation_ids=("rec_soccer_blocked",),
        ),
    )
    _assert_decimal_public_numbers(report)
    for score in report.source_family_scores:
        _assert_decimal_public_numbers(score)


def test_stale_and_lag_thresholds_are_strict() -> None:
    module = _subject()
    report = module.build_strategy_team_memory_source_feedback_v5_report(
        (
            _settled(
                module,
                "rec_at_threshold",
                recommendation_recorded_at=GENERATED_AT - timedelta(seconds=7200),
                source_observed_at=GENERATED_AT - timedelta(seconds=10800),
                settled_at=GENERATED_AT - timedelta(seconds=7200),
                resolution_recorded_at=GENERATED_AT - timedelta(seconds=3600),
            ),
            _settled(
                module,
                "rec_over_threshold",
                recommendation_recorded_at=GENERATED_AT - timedelta(seconds=7202),
                source_observed_at=GENERATED_AT - timedelta(seconds=10803),
                settled_at=GENERATED_AT - timedelta(seconds=7201),
                resolution_recorded_at=GENERATED_AT - timedelta(seconds=3600),
            ),
        ),
        config=module.StrategyTeamMemorySourceFeedbackV5Config(
            max_source_age_seconds=Decimal("3600"),
            max_resolution_lag_seconds=Decimal("3600"),
            max_pass_staleness_rate=Decimal("0.000000"),
            max_watch_staleness_rate=Decimal("0.500000"),
            max_pass_resolution_lag_rate=Decimal("0.000000"),
            max_watch_resolution_lag_rate=Decimal("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.source_feedback_status == "watch"
    assert report.stale_source_count == Decimal("1")
    assert report.resolution_lag_breach_count == Decimal("1")
    assert report.source_family_scores[0].staleness_rate == Decimal("0.500000")
    assert report.source_family_scores[0].resolution_lag_breach_rate == Decimal("0.500000")


def test_rejects_invalid_inputs_and_false_phase_flags() -> None:
    module = _subject()
    config = module.StrategyTeamMemorySourceFeedbackV5Config()

    with pytest.raises(ValueError, match="max_source_age_seconds"):
        module.StrategyTeamMemorySourceFeedbackV5Config(max_source_age_seconds=3600)
    with pytest.raises(ValueError, match="max_resolution_lag_seconds"):
        module.StrategyTeamMemorySourceFeedbackV5Config(
            max_resolution_lag_seconds=_DecimalSubclass("3600"),
        )
    with pytest.raises(ValueError, match="min_pass_accuracy_rate"):
        module.StrategyTeamMemorySourceFeedbackV5Config(
            min_pass_accuracy_rate=Decimal("0.400000"),
            min_watch_accuracy_rate=Decimal("0.500000"),
        )
    with pytest.raises(ValueError, match="settled_recommendations"):
        module.build_strategy_team_memory_source_feedback_v5_report(
            (object(),),
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="future"):
        module.build_strategy_team_memory_source_feedback_v5_report(
            (
                _settled(
                    module,
                    "future",
                    recommendation_recorded_at=GENERATED_AT + timedelta(seconds=1),
                    settled_at=GENERATED_AT + timedelta(seconds=2),
                    resolution_recorded_at=GENERATED_AT + timedelta(seconds=3),
                ),
            ),
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="unique"):
        module.build_strategy_team_memory_source_feedback_v5_report(
            (_settled(module, "dup"), _settled(module, "dup")),
            config=config,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="source_observed_at"):
        _settled(
            module,
            "bad_source_time",
            source_observed_at=GENERATED_AT + timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="settled_at"):
        _settled(
            module,
            "bad_settlement_time",
            settled_at=GENERATED_AT - timedelta(seconds=100),
            resolution_recorded_at=GENERATED_AT - timedelta(seconds=200),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(_settled(module, "bad_flag"), readonly=False)


def test_public_dataclasses_are_frozen() -> None:
    module = _subject()
    report = module.build_strategy_team_memory_source_feedback_v5_report(
        (_settled(module, "rec_frozen"),),
        config=module.StrategyTeamMemorySourceFeedbackV5Config(),
        generated_at=GENERATED_AT,
    )
    values = (
        module.StrategyTeamMemorySourceFeedbackV5Config(),
        _settled(module, "rec_frozen_input"),
        report.source_family_scores[0],
        report,
    )

    for value in values:
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False


def test_module_static_scope_excludes_persistence_db_network_and_live_surfaces() -> None:
    module = _subject()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_call_names = {
        "cancel",
        "connect",
        "create_order",
        "execute",
        "open",
        "place_order",
        "request",
        "sign",
        "submit",
        "write",
    }
    forbidden_surface_tokens = (
        "account",
        "auth",
        "balance",
        "broker",
        "database",
        "private_key",
        "wallet",
    )

    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            call_name = _call_name(node.func)
            if call_name is not None:
                calls.add(call_name.rsplit(".", maxsplit=1)[-1])
        elif isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)

    lowered_source = source.lower()
    assert not (imported_roots & forbidden_import_roots)
    assert not (calls & forbidden_call_names)
    assert not any(token in lowered_source for token in forbidden_surface_tokens)


def _subject() -> ModuleType:
    return importlib.import_module(MODULE_NAME)


def _settled(
    module: ModuleType,
    recommendation_id: str,
    *,
    team_id: str = "politics",
    source_family: str = "news",
    recommendation_recorded_at: datetime = GENERATED_AT - timedelta(seconds=7200),
    source_observed_at: datetime = GENERATED_AT - timedelta(seconds=7500),
    settled_at: datetime = GENERATED_AT - timedelta(seconds=3600),
    resolution_recorded_at: datetime | None = GENERATED_AT - timedelta(seconds=1800),
    predicted_outcome: bool = True,
    resolved_outcome: bool = True,
    source_conflict_count: Decimal = Decimal("0"),
) -> object:
    return module.StrategyTeamMemorySourceFeedbackV5SettledRecommendation(
        team_id=team_id,
        source_family=source_family,
        recommendation_id=recommendation_id,
        recommendation_recorded_at=recommendation_recorded_at,
        source_observed_at=source_observed_at,
        settled_at=settled_at,
        resolution_recorded_at=resolution_recorded_at,
        predicted_outcome=predicted_outcome,
        resolved_outcome=resolved_outcome,
        source_conflict_count=source_conflict_count,
    )


def _assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        field_value = getattr(value, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_rate")
            or field.name.endswith("_seconds")
            or field.name.endswith("_score")
        ):
            assert field_value is None or type(field_value) is Decimal


def _assert_json_ready_without_decimal_or_float(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            _assert_json_ready_without_decimal_or_float(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_json_ready_without_decimal_or_float(item)
        return
    assert not isinstance(value, Decimal)
    assert not isinstance(value, float)
    assert value is None or type(value) in (str, bool)


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None
