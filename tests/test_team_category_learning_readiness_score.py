from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "team_category_learning_readiness_score.py"
)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.team_category_learning_readiness_score",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def readiness_input(**overrides: object):
    module = api()
    values = {
        "team_id": "crypto_btc",
        "category_id": "finance.crypto.btc",
        "settled_sample_count": d("50"),
        "recent_calibration_quality_score": d("0.900000"),
        "postmortem_completion_score": d("1.000000"),
        "source_reliability_trend_score": d("0.800000"),
        "specialist_coverage_score": d("0.900000"),
    }
    values.update(overrides)
    return module.TeamCategoryLearningReadinessScoreInput(**values)


def build_report(*items: object, **overrides: object):
    module = api()
    values = {
        "inputs": items,
        "generated_at": GENERATED_AT,
    }
    values.update(overrides)
    return module.build_team_category_learning_readiness_score_report(**values)


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_builds_report_only_team_category_learning_readiness_gate() -> None:
    module = api()

    report = build_report(
        readiness_input(),
        readiness_input(
            team_id="politics",
            category_id="politics",
            settled_sample_count=d("20"),
            recent_calibration_quality_score=d("0.720000"),
            postmortem_completion_score=d("0.800000"),
            source_reliability_trend_score=d("0.650000"),
            specialist_coverage_score=d("0.600000"),
        ),
        readiness_input(
            team_id="sports_soccer",
            category_id="sports.soccer",
            settled_sample_count=d("4"),
            recent_calibration_quality_score=d("0.400000"),
            postmortem_completion_score=d("0.500000"),
            source_reliability_trend_score=d("0.300000"),
            specialist_coverage_score=d("0.300000"),
        ),
    )

    assert is_dataclass(report)
    assert report.config_version == (
        module.DEFAULT_TEAM_CATEGORY_LEARNING_READINESS_SCORE_CONFIG_VERSION
    )
    assert report.readiness_status == "block"
    assert report.row_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_readiness_score == d("0.636167")
    assert report.reason_codes == (
        "team_category_learning_readiness_watch_rows",
        "team_category_learning_readiness_block_rows",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.team_id, row.category_id) for row in report.rows) == (
        ("crypto_btc", "finance.crypto.btc"),
        ("politics", "politics"),
        ("sports_soccer", "sports.soccer"),
    )
    assert tuple(row.readiness_status for row in report.rows) == (
        "pass",
        "watch",
        "block",
    )
    assert tuple(row.readiness_score for row in report.rows) == (
        d("0.930000"),
        d("0.658500"),
        d("0.320000"),
    )

    passing, watch, blocked = report.rows
    assert passing.settled_sample_score == d("1.000000")
    assert passing.reason_codes == (
        "team_category_learning_readiness_pass",
        "settled_sample_count_full",
        "recent_calibration_quality_strong",
        "postmortem_completion_complete",
        "source_reliability_trend_positive",
        "specialist_coverage_full",
    )
    assert watch.settled_sample_score == d("0.500000")
    assert watch.reason_codes == (
        "team_category_learning_readiness_watch",
        "settled_sample_count_watch",
        "recent_calibration_quality_watch",
        "postmortem_completion_partial",
        "source_reliability_trend_flat",
        "specialist_coverage_partial",
        "readiness_score_below_pass",
    )
    assert blocked.reason_codes == (
        "team_category_learning_readiness_block",
        "settled_sample_count_thin",
        "recent_calibration_quality_weak",
        "postmortem_completion_gap",
        "source_reliability_trend_weak",
        "specialist_coverage_thin",
        "readiness_score_below_watch",
    )


def test_empty_report_is_blocked_and_payload_is_json_safe() -> None:
    report = build_report()

    assert report.readiness_status == "block"
    assert report.row_count == d("0")
    assert report.average_readiness_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("team_category_learning_readiness_empty_inputs",)

    payload = report.payload
    assert payload == api().team_category_learning_readiness_score_payload(report)
    assert payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["row_count"] == "0"
    assert payload["average_readiness_score"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    json.dumps(payload, sort_keys=True)


def test_input_order_does_not_change_rows_or_payload() -> None:
    first = readiness_input(
        team_id="politics",
        category_id="politics",
        settled_sample_count=d("20"),
        recent_calibration_quality_score=d("0.720000"),
        postmortem_completion_score=d("0.800000"),
        source_reliability_trend_score=d("0.650000"),
        specialist_coverage_score=d("0.600000"),
    )
    second = readiness_input()

    left = build_report(first, second)
    right = build_report(second, first)

    assert tuple((row.team_id, row.category_id) for row in left.rows) == (
        ("crypto_btc", "finance.crypto.btc"),
        ("politics", "politics"),
    )
    assert left.payload == right.payload


def test_validates_decimal_only_taxonomy_pairs_duplicates_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="known category"):
        readiness_input(category_id="crypto-btc")
    with pytest.raises(ValueError, match="category_id must match team_id"):
        readiness_input(team_id="politics", category_id="finance.crypto.btc")
    with pytest.raises(ValueError, match="Decimal"):
        readiness_input(settled_sample_count=50)
    with pytest.raises(ValueError, match="exactly Decimal"):
        readiness_input(recent_calibration_quality_score=DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="between zero and one"):
        readiness_input(source_reliability_trend_score=d("1.000001"))
    with pytest.raises(ValueError, match="nonnegative"):
        readiness_input(settled_sample_count=d("-1"))
    with pytest.raises(ValueError, match="paper_only"):
        readiness_input(paper_only=False)
    with pytest.raises(ValueError, match="inputs must be a sequence"):
        module.build_team_category_learning_readiness_score_report(
            inputs=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="inputs must contain"):
        build_report(object())
    with pytest.raises(ValueError, match="duplicate team/category"):
        build_report(readiness_input(), readiness_input())
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_team_category_learning_readiness_score_report(
            inputs=(),
            generated_at=datetime(2026, 7, 7, 12, 0),
        )


def test_config_rejects_incoherent_thresholds_and_weights() -> None:
    module = api()

    with pytest.raises(ValueError, match="score weights must sum to 1.000000"):
        module.TeamCategoryLearningReadinessScoreConfig(
            specialist_coverage_weight=d("0.110000"),
        )
    with pytest.raises(ValueError, match="minimum_settled_sample_count"):
        module.TeamCategoryLearningReadinessScoreConfig(
            minimum_settled_sample_count=d("60"),
        )
    with pytest.raises(ValueError, match="watch_score_floor"):
        module.TeamCategoryLearningReadinessScoreConfig(
            pass_score_floor=d("0.500000"),
            watch_score_floor=d("0.600000"),
        )
    with pytest.raises(ValueError, match="target_settled_sample_count must be positive"):
        module.TeamCategoryLearningReadinessScoreConfig(
            target_settled_sample_count=d("0"),
        )
    with pytest.raises(ValueError, match="readonly"):
        module.TeamCategoryLearningReadinessScoreConfig(readonly=False)


def test_custom_weight_config_builds_rows_validated_against_supplied_config() -> None:
    module = api()
    config = module.TeamCategoryLearningReadinessScoreConfig(
        settled_sample_weight=d("1.000000"),
        recent_calibration_quality_weight=d("0.000000"),
        postmortem_completion_weight=d("0.000000"),
        source_reliability_trend_weight=d("0.000000"),
        specialist_coverage_weight=d("0.000000"),
        pass_score_floor=d("0.600000"),
        watch_score_floor=d("0.300000"),
    )

    report = build_report(
        readiness_input(
            settled_sample_count=d("20"),
            recent_calibration_quality_score=d("0.720000"),
            postmortem_completion_score=d("0.800000"),
            source_reliability_trend_score=d("0.650000"),
            specialist_coverage_score=d("0.600000"),
        ),
        config=config,
    )

    assert report.readiness_status == "watch"
    assert report.average_readiness_score == d("0.500000")
    assert report.rows[0].readiness_score == d("0.500000")
    assert report.rows[0].readiness_status == "watch"
    assert report.rows[0].reason_codes == (
        "team_category_learning_readiness_watch",
        "settled_sample_count_watch",
        "recent_calibration_quality_watch",
        "postmortem_completion_partial",
        "source_reliability_trend_flat",
        "specialist_coverage_partial",
        "readiness_score_below_pass",
    )
    assert report.payload["rows"][0]["readiness_score"] == "0.500000"


def test_public_dataclasses_are_frozen_and_decimal_only() -> None:
    module = api()
    config = module.TeamCategoryLearningReadinessScoreConfig()
    sample = readiness_input()
    report = build_report(sample)
    row = report.rows[0]

    for dataclass_type in (
        module.TeamCategoryLearningReadinessScoreConfig,
        module.TeamCategoryLearningReadinessScoreInput,
        module.TeamCategoryLearningReadinessScore,
        module.TeamCategoryLearningReadinessScoreReport,
    ):
        assert is_dataclass(dataclass_type)
        assert dataclass_type.__dataclass_params__.frozen is True

    for item in (config, sample, row, report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name.endswith("_count") or field.name.endswith("_score"):
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="readiness_score"):
        replace(row, readiness_score=d("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(row, reason_codes=("team_category_learning_readiness_pass",))
    with pytest.raises(ValueError, match="row_count"):
        replace(report, row_count=d("2"))


def test_report_rejects_duplicate_canonical_team_category_rows() -> None:
    module = api()
    report = build_report(readiness_input())
    row = report.rows[0]

    with pytest.raises(ValueError, match="duplicate team/category"):
        module.TeamCategoryLearningReadinessScoreReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            readiness_status="pass",
            row_count=d("2"),
            pass_count=d("2"),
            watch_count=d("0"),
            block_count=d("0"),
            average_readiness_score=row.readiness_score,
            rows=(row, row),
            reason_codes=("team_category_learning_readiness_passed",),
        )


def test_public_constructors_reject_decimal_subclasses() -> None:
    module = api()

    with pytest.raises(ValueError, match="exactly Decimal"):
        module.TeamCategoryLearningReadinessScoreConfig(
            target_settled_sample_count=DecimalSubclass("40"),
        )
    with pytest.raises(ValueError, match="exactly Decimal"):
        readiness_input(settled_sample_count=DecimalSubclass("50"))


def test_payload_rejects_numeric_type_downgrades_and_unsafe_public_shape() -> None:
    module = api()
    report = build_report(readiness_input())
    payload = module.team_category_learning_readiness_score_payload(report)

    assert payload["rows"][0]["team_id"] == "crypto_btc"
    assert payload["rows"][0]["category_id"] == "finance.crypto.btc"
    assert payload["rows"][0]["settled_sample_count"] == "50"
    assert payload["rows"][0]["readiness_score"] == "0.930000"
    assert "candidate" not in repr(payload).casefold()
    assert "market" not in repr(payload).casefold()
    assert "source_ref" not in repr(payload).casefold()

    with pytest.raises(ValueError, match="integer"):
        module.team_category_learning_readiness_score_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "row_count": 1,
            },
        )
    with pytest.raises(ValueError, match="float"):
        module.team_category_learning_readiness_score_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "readiness_score": 0.1,
            },
        )
    with pytest.raises(ValueError, match="unsafe public field"):
        module.team_category_learning_readiness_score_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "candidate_id": "redacted",
            },
        )


def test_payload_dict_rejects_decimal_subclasses() -> None:
    module = api()

    with pytest.raises(ValueError, match="exactly Decimal"):
        module.team_category_learning_readiness_score_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "row_count": DecimalSubclass("1"),
            },
        )


def test_payload_dict_rejects_nested_phase_flag_downgrades() -> None:
    module = api()
    payload = build_report(readiness_input()).payload

    downgraded_payload = {
        **payload,
        "rows": [
            {
                **payload["rows"][0],
                "paper_only": False,
            },
        ],
    }

    with pytest.raises(ValueError, match="paper_only"):
        module.team_category_learning_readiness_score_payload(downgraded_payload)


def test_payload_dict_requires_nested_row_like_phase_flags() -> None:
    module = api()
    payload = build_report(readiness_input()).payload
    row_without_report_only = {
        key: value for key, value in payload["rows"][0].items() if key != "report_only"
    }

    with pytest.raises(ValueError, match="report_only"):
        module.team_category_learning_readiness_score_payload(
            {
                **payload,
                "rows": [row_without_report_only],
            },
        )


@pytest.mark.parametrize(
    "payload_update",
    (
        {"market_id": "redacted"},
        {"market_slug": "redacted"},
        {"source_ref": "redacted"},
        {"safe_context": "https://example.test/source"},
        {"next_step": "buy yes"},
        {"table_name": "team_memory"},
        {"auth_context": "redacted"},
        {"order_context": "redacted"},
        {"recommendation_text": "sell no"},
    ),
)
def test_payload_rejects_forbidden_public_surfaces_in_keys_and_values(
    payload_update: dict[str, object],
) -> None:
    module = api()
    payload = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        **payload_update,
    }

    with pytest.raises(ValueError, match="unsafe public"):
        module.team_category_learning_readiness_score_payload(payload)


def test_payload_dict_validates_canonical_team_category_labels() -> None:
    module = api()
    payload = build_report(readiness_input()).payload

    mismatched_payload = {
        **payload,
        "rows": [
            {
                **payload["rows"][0],
                "category_id": "politics",
            },
        ],
    }
    with pytest.raises(ValueError, match="category_id must match team_id"):
        module.team_category_learning_readiness_score_payload(mismatched_payload)

    unknown_team_payload = {
        **payload,
        "rows": [
            {
                **payload["rows"][0],
                "team_id": "raw_team_alpha",
            },
        ],
    }
    with pytest.raises(ValueError, match="known team"):
        module.team_category_learning_readiness_score_payload(unknown_team_payload)


def test_payload_dict_rejects_blocked_public_status_vocabulary() -> None:
    module = api()
    payload = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }

    with pytest.raises(ValueError, match="readiness_status"):
        module.team_category_learning_readiness_score_payload(
            {
                **payload,
                "readiness_status": "blocked",
            },
        )
    with pytest.raises(ValueError, match="status"):
        module.team_category_learning_readiness_score_payload(
            {
                **payload,
                "status": "blocked",
            },
        )
    with pytest.raises(ValueError, match="reason_codes"):
        module.team_category_learning_readiness_score_payload(
            {
                **payload,
                "reason_codes": ["team_category_learning_readiness_blocked"],
            },
        )


def test_static_module_source_stays_phase_1_pure() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_modules = (
        "aiohttp",
        "http",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
    )
    forbidden_call_or_attribute_names = {
        "__import__",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "eval",
        "exec",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "place_order",
        "print",
        "rollback",
        "send",
        "sign",
        "write",
    }
    forbidden_public_fragments = (
        "account",
        "auth",
        "buy",
        "dsn",
        "market_id",
        "market_slug",
        "order",
        "private_key",
        "recommend",
        "sell",
        "source_ref",
        "table_name",
        "trade",
        "wallet",
    )

    imports: list[str] = []
    names: list[str] = []
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append(node.module)
        elif isinstance(node, ast.Call):
            names.append(_call_name(node.func))
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert float_constants == []
    assert not any(
        imported == forbidden or imported.startswith(f"{forbidden}.")
        for imported in imports
        for forbidden in forbidden_modules
    )
    assert not any(name in forbidden_call_or_attribute_names for name in names)
    lowered = source.casefold()
    assert not any(fragment in lowered for fragment in forbidden_public_fragments)

    assert api().__all__ == (
        "DEFAULT_TEAM_CATEGORY_LEARNING_READINESS_SCORE_CONFIG_VERSION",
        "TEAM_CATEGORY_LEARNING_READINESS_REASON_CODES",
        "TEAM_CATEGORY_LEARNING_READINESS_STATUSES",
        "TeamCategoryLearningReadinessScore",
        "TeamCategoryLearningReadinessScoreConfig",
        "TeamCategoryLearningReadinessScoreInput",
        "TeamCategoryLearningReadinessScoreReport",
        "build_team_category_learning_readiness_score_report",
        "team_category_learning_readiness_score_payload",
    )


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""
