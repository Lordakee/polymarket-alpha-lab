from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "team_specialist_source_rotation_learning_score_v2.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_specialist_source_rotation_learning_score_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def source_mix(**overrides: object):
    module = api()
    values = {
        "specialist_id": "alpha_specialists",
        "domain_id": "macro_rates",
        "source_mix_id": "weekly_mix",
        "unique_source_count": d("5"),
        "rotated_source_count": d("2"),
        "stale_source_count": d("0"),
        "successful_rotation_count": d("2"),
        "evaluated_rotation_count": d("2"),
        "learning_capture_score": d("0.900000"),
        "source_quality_score": d("0.900000"),
    }
    values.update(overrides)
    return module.TeamSpecialistSourceRotationLearningV2Input(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    generated_at = overrides.pop(
        "generated_at",
        datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
    )
    config = overrides.pop("config", None)
    use_default_items = overrides.pop("use_default_items", True)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    if not items and use_default_items:
        items = (
            source_mix(specialist_id="alpha_specialists"),
            source_mix(
                specialist_id="beta_specialists",
                unique_source_count=d("4"),
                rotated_source_count=d("1"),
                stale_source_count=d("1"),
                successful_rotation_count=d("1"),
                evaluated_rotation_count=d("2"),
                learning_capture_score=d("0.700000"),
                source_quality_score=d("0.650000"),
            ),
            source_mix(
                specialist_id="gamma_specialists",
                unique_source_count=d("3"),
                rotated_source_count=d("0"),
                stale_source_count=d("2"),
                successful_rotation_count=d("0"),
                evaluated_rotation_count=d("1"),
                learning_capture_score=d("0.400000"),
                source_quality_score=d("0.300000"),
            ),
        )
    return module.build_team_specialist_source_rotation_learning_score_v2(
        items,
        config=config,
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_builds_source_rotation_learning_score_report_and_payload() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.report_status == "blocked"
    assert report.specialist_count == d("3")
    assert report.pass_specialist_count == d("1")
    assert report.watch_specialist_count == d("1")
    assert report.blocked_specialist_count == d("1")
    assert report.stale_source_mix_count == d("2")
    assert report.successful_rotation_boosted_count == d("2")
    assert report.average_source_rotation_learning_score == d("0.602778")
    assert report.top_source_rotation_learning_score == d("1.000000")
    assert report.bottom_source_rotation_learning_score == d("0.158333")
    assert report.reason_codes == (
        "source_rotation_learning_report_blocked_rows",
        "source_rotation_learning_report_watch_rows",
        "stale_source_mix_penalty_rows",
        "successful_rotation_boost_rows",
    )

    rows = report.rows
    assert tuple(row.specialist_id for row in rows) == (
        "alpha_specialists",
        "beta_specialists",
        "gamma_specialists",
    )
    assert tuple(row.rank for row in rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.source_rotation_learning_score for row in rows) == (
        d("1.000000"),
        d("0.650000"),
        d("0.158333"),
    )
    assert tuple(row.learning_status for row in rows) == ("pass", "watch", "blocked")

    payload = report.payload
    assert payload["specialist_count"] == "3"
    assert payload["average_source_rotation_learning_score"] == "0.602778"
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["rank"] == "1"
    assert payload["rows"][0]["source_rotation_learning_score"] == "1.000000"
    assert len(report.derived_validation_digest) == 64
    assert_no_float_values(payload)


def test_stale_source_mix_penalties_reduce_score_and_flag_rows() -> None:
    fresh = source_mix(specialist_id="fresh_specialists")
    stale = source_mix(
        specialist_id="stale_specialists",
        stale_source_count=d("3"),
    )

    report = build_report(fresh, stale)
    by_specialist = {row.specialist_id: row for row in report.rows}

    assert by_specialist["fresh_specialists"].stale_source_mix_penalty == d("0.000000")
    assert by_specialist["stale_specialists"].stale_source_ratio == d("0.600000")
    assert by_specialist["stale_specialists"].stale_source_mix_penalty == d("0.150000")
    assert (
        by_specialist["stale_specialists"].source_rotation_learning_score
        < by_specialist["fresh_specialists"].source_rotation_learning_score
    )
    assert "stale_source_mix_stale" in by_specialist["stale_specialists"].reason_codes
    assert report.stale_source_mix_count == d("1")
    assert "stale_source_mix_penalty_rows" in report.reason_codes


def test_successful_rotation_boosts_score() -> None:
    successful = source_mix(
        specialist_id="successful_specialists",
        successful_rotation_count=d("2"),
        evaluated_rotation_count=d("2"),
    )
    unsuccessful = source_mix(
        specialist_id="unsuccessful_specialists",
        successful_rotation_count=d("0"),
        evaluated_rotation_count=d("2"),
    )

    report = build_report(successful, unsuccessful)
    by_specialist = {row.specialist_id: row for row in report.rows}

    assert by_specialist["successful_specialists"].successful_rotation_boost == d("0.100000")
    assert by_specialist["unsuccessful_specialists"].successful_rotation_boost == d("0.000000")
    assert (
        by_specialist["successful_specialists"].source_rotation_learning_score
        > by_specialist["unsuccessful_specialists"].source_rotation_learning_score
    )
    assert "successful_rotation_boost_applied" in by_specialist["successful_specialists"].reason_codes
    assert report.successful_rotation_boosted_count == d("1")


def test_empty_report_is_report_only_and_digest_backed() -> None:
    report = build_report(
        *(),
        generated_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
        use_default_items=False,
    )

    assert report.report_status == "blocked"
    assert report.specialist_count == d("0")
    assert report.average_source_rotation_learning_score == d("0.000000")
    assert report.top_source_rotation_learning_score == d("0.000000")
    assert report.bottom_source_rotation_learning_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("source_rotation_learning_report_empty",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    config = module.TeamSpecialistSourceRotationLearningScoreV2Config()
    sample = source_mix()
    report = build_report(sample)
    row = report.rows[0]

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {
                "source_diversity_weight",
                "rotation_success_weight",
                "learning_capture_weight",
                "source_quality_weight",
                "stale_source_mix_penalty_weight",
                "successful_rotation_boost_weight",
                "target_source_count",
                "stale_source_mix_watch_floor",
                "stale_source_mix_block_floor",
                "pass_score_floor",
                "watch_score_floor",
                "unique_source_count",
                "rotated_source_count",
                "stale_source_count",
                "successful_rotation_count",
                "evaluated_rotation_count",
                "learning_capture_score",
                "source_quality_score",
                "rank",
                "source_diversity_score",
                "stale_source_ratio",
                "stale_source_mix_penalty",
                "rotation_success_ratio",
                "successful_rotation_boost",
                "source_rotation_learning_score",
                "specialist_count",
                "pass_specialist_count",
                "watch_specialist_count",
                "blocked_specialist_count",
                "stale_source_mix_count",
                "successful_rotation_boosted_count",
                "average_source_rotation_learning_score",
                "top_source_rotation_learning_score",
                "bottom_source_rotation_learning_score",
            }:
                assert type(value) is Decimal


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "unique_source_count",
            _DecimalSubclass("5"),
            "unique_source_count must be exactly Decimal",
        ),
        (
            "rotated_source_count",
            d("1.5"),
            "rotated_source_count must be an integral Decimal",
        ),
        (
            "stale_source_count",
            d("-1"),
            "stale_source_count must be >= 0.000000",
        ),
        (
            "learning_capture_score",
            d("0.9000004"),
            "learning_capture_score must use six decimal places or fewer",
        ),
        (
            "source_quality_score",
            Decimal("NaN"),
            "source_quality_score must be finite",
        ),
    ),
)
def test_input_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        source_mix(**{field_name: bad_value})


def test_config_and_build_validation_reject_bad_values_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_diversity_weight must be exactly Decimal"):
        module.TeamSpecialistSourceRotationLearningScoreV2Config(
            source_diversity_weight=0,
        )
    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.TeamSpecialistSourceRotationLearningScoreV2Config(
            source_quality_weight=d("0.160000"),
        )
    with pytest.raises(ValueError, match="watch_score_floor must not exceed pass_score_floor"):
        module.TeamSpecialistSourceRotationLearningScoreV2Config(
            watch_score_floor=d("0.900000"),
        )
    with pytest.raises(ValueError, match="paper_only must be True"):
        module.TeamSpecialistSourceRotationLearningScoreV2Config(paper_only=False)
    with pytest.raises(ValueError, match="source_mixes must be an iterable"):
        module.build_team_specialist_source_rotation_learning_score_v2(
            object(),
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(
        ValueError,
        match="source mix items must be TeamSpecialistSourceRotationLearningV2Input",
    ):
        module.build_team_specialist_source_rotation_learning_score_v2(
            [object()],
            generated_at=datetime(2026, 7, 6, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_specialist_source_rotation_learning_score_v2(
            [source_mix()],
            generated_at=datetime(2026, 7, 6),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        source_mix(readonly=False)
    with pytest.raises(ValueError, match="stale_source_count must not exceed unique_source_count"):
        source_mix(stale_source_count=d("6"))


def test_custom_config_report_revalidates_against_derived_row_reasons() -> None:
    module = api()
    config = module.TeamSpecialistSourceRotationLearningScoreV2Config(
        stale_source_mix_watch_floor=d("0.300000"),
        stale_source_mix_block_floor=d("0.700000"),
    )

    report = build_report(
        source_mix(stale_source_count=d("1")),
        config=config,
    )

    assert report.stale_source_mix_count == d("0")
    assert "stale_source_mix_penalty_rows" not in report.reason_codes
    assert report.payload["config_version"] == (
        "team-specialist-source-rotation-learning-score-v2"
    )


def test_derived_validation_digest_rejects_tampering() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest must match report fields"):
        replace(
            report,
            average_source_rotation_learning_score=d("0.600000"),
        )


def test_rejects_unsafe_public_keys_and_values() -> None:
    module = api()

    for unsafe_value in (
        "live_team",
        "auth_team",
        "wallet_team",
        "order_team",
        "network_team",
        "database_team",
        "persist_team",
        "signing_team",
        "mutation_team",
        "buy_team",
        "sell_team",
        "trade_team",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            source_mix(specialist_id=unsafe_value)

    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"order_id": "redacted"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        module._reject_unsafe_public_payload("example", {"safe_key": "network note"})
    with pytest.raises(ValueError, match="unsafe public payload"):
        replace(build_report().rows[0], reason_codes=("trade",))


def test_report_revalidates_row_order_counts_and_reason_codes() -> None:
    report = build_report()

    with pytest.raises(ValueError, match="rows must be sorted by score and rank"):
        replace(
            report,
            rows=(report.rows[1], report.rows[0], report.rows[2]),
        )
    with pytest.raises(ValueError, match="status counts must match rows"):
        replace(
            report,
            pass_specialist_count=d("2"),
        )
    with pytest.raises(ValueError, match="reason_codes must match report_status"):
        replace(
            report,
            reason_codes=("source_rotation_learning_report_passed",),
        )


def test_module_scope_has_no_file_database_network_or_order_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []
    float_constants: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.append(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.append(function.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "http",
        "network",
        "pathlib",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "place_order",
        "rollback",
        "sell",
        "send",
        "trade",
        "write",
    }

    assert not float_constants
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in call_names)
    assert not any(name in forbidden_call_or_attribute_names for name in attribute_names)
    assert_no_float_values([imports, call_names, attribute_names])
