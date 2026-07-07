from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal

import pytest


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.team_memory_specialist_playbook_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg():
    score_module = module()
    return score_module.TeamMemorySpecialistPlaybookScoreConfig(
        config_version="team-memory-specialist-playbook-score-test",
        min_memory_ready_settled_sample_count=d("50"),
        min_memory_ready_recent_sample_count=d("10"),
        max_memory_ready_calibration_error=d("0.050000"),
        max_watch_calibration_error=d("0.150000"),
        min_memory_ready_source_reliability_score=d("0.800000"),
        min_watch_source_reliability_score=d("0.600000"),
        max_memory_ready_playbook_revision_age_days=d("30.000000"),
        max_watch_playbook_revision_age_days=d("90.000000"),
        max_unresolved_failure_count=d("0"),
    )


def observation(
    team_id: str,
    *,
    settled_sample_count: Decimal = d("120"),
    recent_sample_count: Decimal = d("25"),
    calibration_error: Decimal = d("0.030000"),
    source_reliability_score: Decimal = d("0.910000"),
    playbook_revision_age_days: Decimal = d("10.000000"),
    unresolved_failure_count: Decimal = d("0"),
):
    score_module = module()
    return score_module.TeamMemorySpecialistPlaybookScoreObservation(
        team_id=team_id,
        settled_sample_count=settled_sample_count,
        recent_sample_count=recent_sample_count,
        calibration_error=calibration_error,
        source_reliability_score=source_reliability_score,
        playbook_revision_age_days=playbook_revision_age_days,
        unresolved_failure_count=unresolved_failure_count,
    )


def build_report(*observations):
    score_module = module()
    return score_module.build_team_memory_specialist_playbook_score_report(
        observations,
        config=cfg(),
    )


def assert_json_ready_without_numbers(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise AssertionError("payload contains a non-Decimal number")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_json_ready_without_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_json_ready_without_numbers(item)


def test_mature_calibrated_team_is_memory_ready_with_payload_digest() -> None:
    score_module = module()
    report = build_report(observation("politics"))

    assert score_module.__all__ == (
        "DEFAULT_TEAM_MEMORY_SPECIALIST_PLAYBOOK_SCORE_CONFIG_VERSION",
        "TeamMemorySpecialistPlaybookScoreConfig",
        "TeamMemorySpecialistPlaybookScoreObservation",
        "TeamMemorySpecialistPlaybookScoreReasonCodeCount",
        "TeamMemorySpecialistPlaybookScoreReport",
        "TeamMemorySpecialistPlaybookScoreRow",
        "build_team_memory_specialist_playbook_score_report",
    )
    assert report.report_status == "memory_ready"
    assert report.team_count == d("1.000000")
    assert report.memory_ready_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_playbook_readiness_score == d("0.910000")
    assert report.min_playbook_readiness_score == d("0.910000")
    assert report.reason_codes == (
        "team_memory_specialist_playbook_ready",
    )

    (row,) = report.rows
    assert row.team_id == "politics"
    assert row.calibration_score == d("0.970000")
    assert row.revision_freshness_score == d("1.000000")
    assert row.playbook_readiness_score == d("0.910000")
    assert row.memory_status == "memory_ready"
    assert row.reason_codes == (
        "team_memory_specialist_playbook_ready",
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.payload
    assert payload["team_count"] == "1.000000"
    assert payload["average_playbook_readiness_score"] == "0.910000"
    assert payload["rows"][0]["playbook_readiness_score"] == "0.910000"  # type: ignore[index]
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert_json_ready_without_numbers(payload)
    json.dumps(payload, sort_keys=True)


def test_insufficient_samples_are_watch_not_block() -> None:
    report = build_report(
        observation(
            "crypto_btc",
            settled_sample_count=d("20"),
            recent_sample_count=d("4"),
        ),
    )

    (row,) = report.rows
    assert report.report_status == "watch"
    assert report.watch_count == d("1.000000")
    assert row.memory_status == "watch"
    assert row.playbook_readiness_score == d("0.400000")
    assert row.reason_codes == (
        "team_memory_specialist_settled_sample_count_insufficient",
        "team_memory_specialist_recent_sample_count_insufficient",
    )


def test_high_calibration_error_blocks_memory_readiness() -> None:
    report = build_report(
        observation(
            "equity_index",
            calibration_error=d("0.200000"),
        ),
    )

    (row,) = report.rows
    assert report.report_status == "block"
    assert report.block_count == d("1.000000")
    assert row.memory_status == "block"
    assert row.calibration_score == d("0.800000")
    assert row.reason_codes == (
        "team_memory_specialist_calibration_error_high",
    )


def test_stale_playbook_revisions_are_watch_until_block_threshold() -> None:
    watch_report = build_report(
        observation(
            "commodities_gold",
            playbook_revision_age_days=d("45.000000"),
        ),
    )
    block_report = build_report(
        observation(
            "commodities_gold",
            playbook_revision_age_days=d("120.000000"),
        ),
    )

    (watch_row,) = watch_report.rows
    assert watch_report.report_status == "watch"
    assert watch_row.memory_status == "watch"
    assert watch_row.revision_freshness_score == d("0.500000")
    assert watch_row.reason_codes == (
        "team_memory_specialist_playbook_revision_stale",
    )

    (block_row,) = block_report.rows
    assert block_report.report_status == "block"
    assert block_row.memory_status == "block"
    assert block_row.revision_freshness_score == d("0.000000")
    assert block_row.reason_codes == (
        "team_memory_specialist_playbook_revision_stale",
    )


def test_unresolved_failures_block_memory_readiness() -> None:
    report = build_report(
        observation(
            "basketball",
            unresolved_failure_count=d("1"),
        ),
    )

    (row,) = report.rows
    assert report.report_status == "block"
    assert row.memory_status == "block"
    assert row.playbook_readiness_score == d("0.000000")
    assert row.reason_codes == (
        "team_memory_specialist_unresolved_failures_present",
    )


def test_report_order_reason_counts_empty_report_and_digest_are_deterministic() -> None:
    empty_report = build_report()
    assert empty_report.report_status == "empty"
    assert empty_report.rows == ()
    assert empty_report.reason_codes == ()
    assert empty_report.reason_code_counts == ()
    assert empty_report.team_count == d("0.000000")
    assert empty_report.average_playbook_readiness_score == d("0.000000")
    assert empty_report.min_playbook_readiness_score == d("0.000000")

    report = build_report(
        observation("soccer"),
        observation(
            "general",
            source_reliability_score=d("0.700000"),
        ),
        observation(
            "crypto_btc",
            recent_sample_count=d("4"),
        ),
    )

    assert tuple(row.team_id for row in report.rows) == (
        "crypto_btc",
        "soccer",
        "general",
    )
    assert report.report_status == "watch"
    assert report.reason_codes == (
        "team_memory_specialist_playbook_ready",
        "team_memory_specialist_recent_sample_count_insufficient",
        "team_memory_specialist_source_reliability_low",
    )
    assert tuple(count.reason_code for count in report.reason_code_counts) == report.reason_codes
    assert tuple(count.count for count in report.reason_code_counts) == (
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
    )
    assert report.derived_validation_digest == build_report(
        observation(
            "crypto_btc",
            recent_sample_count=d("4"),
        ),
        observation("soccer"),
        observation(
            "general",
            source_reliability_score=d("0.700000"),
        ),
    ).derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest does not match"):
        replace(report, derived_validation_digest="0" * 64)


def test_uses_canonical_strategy_team_taxonomy_ids_and_order() -> None:
    taxonomy = importlib.import_module("polymarket_alpha_lab.strategy_team_taxonomy")

    assert tuple(taxonomy.STRATEGY_TEAM_IDS) == (
        "politics",
        "crypto_btc",
        "equity_index",
        "commodities_gold",
        "soccer",
        "basketball",
        "other_sports",
        "general",
    )
    assert hasattr(taxonomy, "require_strategy_team_id")

    report = build_report(
        *(observation(team_id) for team_id in reversed(taxonomy.STRATEGY_TEAM_IDS)),
    )

    assert tuple(row.team_id for row in report.rows) == taxonomy.STRATEGY_TEAM_IDS

    with pytest.raises(ValueError, match="rows must be sorted by canonical team taxonomy"):
        replace(report, rows=tuple(reversed(report.rows)))


def test_dataclasses_are_frozen_decimal_only_hard_flagged_and_taxonomy_validated() -> None:
    score_module = module()

    for exported_name in score_module.__all__:
        value = getattr(score_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(observation("other_sports"))
    for row in report.rows:
        for field in fields(row):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_score")
                or field.name.endswith("_error")
                or field.name.endswith("_days")
            ):
                assert type(getattr(row, field.name)) is Decimal
    for field in fields(report):
        if field.name.endswith("_count") or field.name.endswith("_score"):
            assert type(getattr(report, field.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].memory_status = "block"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):

        class DerivedObservation(  # type: ignore[unused-ignore]
            score_module.TeamMemorySpecialistPlaybookScoreObservation
        ):
            pass

    with pytest.raises(ValueError, match="team_id must be a known strategy team"):
        observation("not_a_strategy_team")

    with pytest.raises(ValueError, match="report_only must be True"):
        score_module.TeamMemorySpecialistPlaybookScoreConfig(report_only=False)

    with pytest.raises(ValueError, match="readonly must be True"):
        score_module.TeamMemorySpecialistPlaybookScoreObservation(
            team_id="general",
            settled_sample_count=d("1"),
            recent_sample_count=d("1"),
            calibration_error=d("0.010000"),
            source_reliability_score=d("1.000000"),
            playbook_revision_age_days=d("1.000000"),
            unresolved_failure_count=d("0"),
            readonly=False,
        )


def test_rejects_unsafe_values_bad_decimals_duplicates_and_config_shape() -> None:
    score_module = module()

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="unsafe public payload entry"):
        score_module.TeamMemorySpecialistPlaybookScoreConfig(
            config_version="paper-auth-test",
        )
    with pytest.raises(ValueError, match="settled_sample_count must be a Decimal"):
        observation(
            "general",
            settled_sample_count=1.0,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="source_reliability_score must be a Decimal"):
        observation(
            "general",
            source_reliability_score=DerivedDecimal("1.000000"),
        )
    with pytest.raises(ValueError, match="settled_sample_count must be integral"):
        observation(
            "general",
            settled_sample_count=d("1.0000001"),
            recent_sample_count=d("1"),
        )
    with pytest.raises(ValueError, match="recent_sample_count must not exceed"):
        observation(
            "general",
            settled_sample_count=d("1"),
            recent_sample_count=d("2"),
        )
    with pytest.raises(ValueError, match="duplicate team_id"):
        build_report(
            observation("general"),
            observation("general"),
        )
    with pytest.raises(ValueError, match="max_watch_calibration_error"):
        score_module.TeamMemorySpecialistPlaybookScoreConfig(
            max_memory_ready_calibration_error=d("0.200000"),
            max_watch_calibration_error=d("0.100000"),
        )


def test_module_omits_io_network_mutation_and_numeric_runtime_boundaries() -> None:
    score_module = module()
    source_text = score_module.__loader__.get_source(score_module.__name__)
    assert source_text is not None
    lowered = source_text.lower()

    for forbidden in (
        "requests",
        "urllib",
        "http",
        "socket",
        "sqlite",
        "redis",
        "mongo",
        "postgres",
        "supabase",
        "psycopg",
        "sql",
        "open(",
        "pathlib",
        "pandas",
        "numpy",
        "subprocess",
        "wallet",
        "private_key",
        "account",
        "auth",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "signing",
        "mutation",
        "trade",
        "buy",
        "sell",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_text)
    imports = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert imports <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "json",
        "polymarket_alpha_lab",
    }
