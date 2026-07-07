from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.team_memory_specialist_resolution_latency_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg():
    score_module = module()
    return score_module.TeamMemorySpecialistResolutionLatencyScoreV2Config(
        config_version="team-memory-specialist-resolution-latency-score-v2-test",
        max_pass_median_resolution_latency_seconds=d("100.000000"),
        max_watch_median_resolution_latency_seconds=d("300.000000"),
        max_pass_p95_resolution_latency_seconds=d("200.000000"),
        max_watch_p95_resolution_latency_seconds=d("600.000000"),
        min_pass_postmortem_completion_ratio=d("0.900000"),
        min_watch_postmortem_completion_ratio=d("0.700000"),
        stale_resolution_age_seconds=d("86400.000000"),
        min_pass_learning_loop_score=d("90.000000"),
        min_watch_learning_loop_score=d("50.000000"),
    )


def source(
    team_id: str,
    domain: str,
    *,
    resolved_market_count: Decimal = d("8.000000"),
    median_resolution_latency_seconds: Decimal = d("100.000000"),
    p95_resolution_latency_seconds: Decimal = d("200.000000"),
    postmortem_completion_ratio: Decimal = d("0.950000"),
    latest_resolution_at: datetime | None = None,
):
    score_module = module()
    return score_module.TeamMemorySpecialistResolutionLatencyScoreV2Source(
        team_id=team_id,
        domain=domain,
        resolved_market_count=resolved_market_count,
        median_resolution_latency_seconds=median_resolution_latency_seconds,
        p95_resolution_latency_seconds=p95_resolution_latency_seconds,
        postmortem_completion_ratio=postmortem_completion_ratio,
        latest_resolution_at=latest_resolution_at
        or GENERATED_AT - timedelta(seconds=3600),
    )


def build_report(*sources):
    score_module = module()
    return score_module.build_team_memory_specialist_resolution_latency_score_v2_report(
        sources,
        config=cfg(),
        generated_at=GENERATED_AT,
    )


def assert_json_ready_without_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError("payload contains a float")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_json_ready_without_floats(item)
    elif isinstance(value, list):
        for item in value:
            assert_json_ready_without_floats(item)


def test_builds_readonly_report_with_deterministic_scores_rollups_and_payload() -> None:
    report = build_report(
        source(
            "team-b",
            "sports",
            latest_resolution_at=GENERATED_AT - timedelta(seconds=3600),
        ),
        source(
            "team-c",
            "crypto",
            resolved_market_count=d("3.000000"),
            median_resolution_latency_seconds=d("350.000000"),
            p95_resolution_latency_seconds=d("700.000000"),
            postmortem_completion_ratio=d("0.600000"),
            latest_resolution_at=GENERATED_AT - timedelta(seconds=172800),
        ),
        source(
            "team-a",
            "crypto",
            resolved_market_count=d("5.000000"),
            median_resolution_latency_seconds=d("200.000000"),
            p95_resolution_latency_seconds=d("400.000000"),
            postmortem_completion_ratio=d("1.000000"),
            latest_resolution_at=GENERATED_AT - timedelta(seconds=7200),
        ),
    )

    assert report.report_status == "block"
    assert report.team_domain_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.high_latency_count == d("2.000000")
    assert report.weak_postmortem_count == d("1.000000")
    assert report.stale_resolution_count == d("1.000000")
    assert report.min_learning_loop_score == d("0.000000")
    assert tuple((row.domain, row.team_id) for row in report.rows) == (
        ("crypto", "team-a"),
        ("crypto", "team-c"),
        ("sports", "team-b"),
    )

    watch_row, block_row, pass_row = report.rows
    assert watch_row.latency_score == d("50.000000")
    assert watch_row.learning_loop_score == d("50.000000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "team_memory_specialist_resolution_latency_high",
    )
    assert block_row.latency_score == d("0.000000")
    assert block_row.learning_loop_score == d("0.000000")
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "team_memory_specialist_resolution_latency_high",
        "team_memory_specialist_postmortem_completion_weak",
        "team_memory_specialist_latest_resolution_stale",
        "team_memory_specialist_learning_loop_score_below_watch",
    )
    assert pass_row.latency_score == d("100.000000")
    assert pass_row.learning_loop_score == d("95.000000")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == (
        "team_memory_specialist_learning_loop_ready",
    )

    assert tuple(count.reason_code for count in report.reason_code_counts) == (
        "team_memory_specialist_latest_resolution_stale",
        "team_memory_specialist_learning_loop_ready",
        "team_memory_specialist_learning_loop_score_below_watch",
        "team_memory_specialist_postmortem_completion_weak",
        "team_memory_specialist_resolution_latency_high",
    )
    assert tuple(count.count for count in report.reason_code_counts) == (
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("1.000000"),
        d("2.000000"),
    )
    assert report.reason_codes == tuple(
        count.reason_code for count in report.reason_code_counts
    )
    assert len(report.derived_validation_digest) == 64
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    payload = report.payload
    assert payload["team_domain_count"] == "3.000000"
    assert payload["min_learning_loop_score"] == "0.000000"
    assert payload["rows"][0]["latency_score"] == "50.000000"  # type: ignore[index]
    assert payload["rows"][0]["latest_resolution_at"] == "2026-07-07T10:00:00+00:00"  # type: ignore[index]
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert_json_ready_without_floats(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_input_returns_empty_status_and_zero_decimals() -> None:
    report = build_report()

    assert report.report_status == "empty"
    assert report.rows == ()
    assert report.reason_codes == ()
    assert report.reason_code_counts == ()
    for field in fields(report):
        if field.name.endswith("_count") or field.name.endswith("_score"):
            assert getattr(report, field.name) == d("0.000000")
            assert type(getattr(report, field.name)) is Decimal


def test_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    score_module = module()

    assert score_module.__all__ == (
        "DEFAULT_TEAM_MEMORY_SPECIALIST_RESOLUTION_LATENCY_SCORE_V2_CONFIG_VERSION",
        "TeamMemorySpecialistResolutionLatencyScoreV2Config",
        "TeamMemorySpecialistResolutionLatencyScoreV2ReasonCodeCount",
        "TeamMemorySpecialistResolutionLatencyScoreV2Report",
        "TeamMemorySpecialistResolutionLatencyScoreV2Row",
        "TeamMemorySpecialistResolutionLatencyScoreV2Source",
        "build_team_memory_specialist_resolution_latency_score_v2_report",
    )
    for exported_name in score_module.__all__:
        value = getattr(score_module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(source("team-z", "macro"))
    for row in report.rows:
        for field in fields(row):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_score")
            ):
                assert type(getattr(row, field.name)) is Decimal
    for field in fields(report):
        if field.name.endswith("_count") or field.name.endswith("_score"):
            assert type(getattr(report, field.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"  # type: ignore[misc]

    with pytest.raises(TypeError, match="does not support subclassing"):

        class DerivedConfig(  # type: ignore[unused-ignore]
            score_module.TeamMemorySpecialistResolutionLatencyScoreV2Config
        ):
            pass


def test_rejects_bad_types_sequences_duplicates_flags_and_digest_tampering() -> None:
    score_module = module()

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="median_resolution_latency_seconds"):
        source(
            "team-float",
            "sports",
            median_resolution_latency_seconds=1.0,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="max_pass_median_resolution_latency_seconds"):
        score_module.TeamMemorySpecialistResolutionLatencyScoreV2Config(
            max_pass_median_resolution_latency_seconds=DerivedDecimal("1.000000"),
        )
    with pytest.raises(ValueError, match="p95_resolution_latency_seconds"):
        source(
            "team-bad-sequence",
            "sports",
            median_resolution_latency_seconds=d("300.000000"),
            p95_resolution_latency_seconds=d("100.000000"),
        )
    with pytest.raises(ValueError, match="latest_resolution_at must not be after generated_at"):
        build_report(
            source(
                "team-future",
                "sports",
                latest_resolution_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="latest_resolution_at must be timezone-aware"):
        source(
            "team-naive",
            "sports",
            latest_resolution_at=datetime(2026, 7, 7, 12, 0),
        )
    with pytest.raises(ValueError, match="duplicate team_id/domain"):
        build_report(
            source("team-dup", "sports"),
            source("team-dup", "sports"),
        )
    with pytest.raises(ValueError, match="report_only must be True"):
        score_module.TeamMemorySpecialistResolutionLatencyScoreV2Config(
            report_only=False,
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        score_module.TeamMemorySpecialistResolutionLatencyScoreV2Source(
            team_id="team-flags",
            domain="sports",
            resolved_market_count=d("1.000000"),
            median_resolution_latency_seconds=d("1.000000"),
            p95_resolution_latency_seconds=d("1.000000"),
            postmortem_completion_ratio=d("1.000000"),
            latest_resolution_at=GENERATED_AT,
            paper_only=False,
        )

    report = build_report(source("team-digest", "politics"))
    with pytest.raises(ValueError, match="derived_validation_digest does not match"):
        replace(report, derived_validation_digest="0" * 64)


def test_module_omits_live_mutation_io_imports() -> None:
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
        "wallet",
        "private_key",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
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
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "polymarket_alpha_lab",
    }
