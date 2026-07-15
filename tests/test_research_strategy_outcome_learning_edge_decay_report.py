from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
from itertools import permutations
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import polymarket_alpha_lab.research_strategy_outcome_learning_edge_decay_report as edge_decay_api
from polymarket_alpha_lab.research_strategy_outcome_learning_edge_decay_report import (
    DEFAULT_RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_STATUSES,
    ResearchStrategyOutcomeLearningEdgeDecayConfig,
    ResearchStrategyOutcomeLearningEdgeDecayInput,
    ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount,
    ResearchStrategyOutcomeLearningEdgeDecayReport,
    ResearchStrategyOutcomeLearningEdgeDecayRow,
    build_research_strategy_outcome_learning_edge_decay_report,
    research_strategy_outcome_learning_edge_decay_report_payload,
)


MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_outcome_learning_edge_decay_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 17, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
QUANTUM = Decimal("0.000001")

EXPECTED_REPORT_FIELDS = (
    "generated_at",
    "config_version",
    "config",
    "status",
    "input_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_outcome_learning_score",
    "min_outcome_learning_score",
    "max_probability_edge_decay_ratio",
    "min_settled_outcome_feedback_score",
    "min_calibration_update_quality_score",
    "min_evidence_reuse_score",
    "max_cost_pressure_score",
    "max_stale_thesis_pressure_score",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
EXPECTED_CONFIG_FIELDS = (
    "config_version",
    "pass_min_outcome_learning_score",
    "watch_min_outcome_learning_score",
    "max_pass_probability_edge_decay_ratio",
    "max_watch_probability_edge_decay_ratio",
    "min_pass_settled_outcome_feedback_score",
    "min_watch_settled_outcome_feedback_score",
    "min_pass_calibration_update_quality_score",
    "min_watch_calibration_update_quality_score",
    "min_pass_evidence_reuse_score",
    "min_watch_evidence_reuse_score",
    "max_pass_cost_pressure_score",
    "max_watch_cost_pressure_score",
    "max_pass_stale_thesis_pressure_score",
    "max_watch_stale_thesis_pressure_score",
    "settled_feedback_weight",
    "calibration_update_weight",
    "evidence_reuse_weight",
    "cost_pressure_weight",
    "stale_thesis_weight",
    "edge_retention_weight",
    "paper_only",
    "report_only",
    "readonly",
)
EXPECTED_ROW_FIELDS = (
    "learning_ref_digest",
    "observed_at",
    "pre_feedback_probability_edge",
    "post_feedback_probability_edge",
    "probability_edge_decay_ratio",
    "edge_retention_score",
    "settled_outcome_feedback_score",
    "calibration_update_quality_score",
    "evidence_reuse_score",
    "cost_pressure_score",
    "cost_relief_score",
    "stale_thesis_pressure_score",
    "thesis_freshness_score",
    "outcome_learning_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
EXPECTED_REASON_CODE_COUNT_FIELDS = (
    "reason_code",
    "count",
    "input_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
INPUT_DECIMAL_FIELDS = (
    "pre_feedback_probability_edge",
    "post_feedback_probability_edge",
    "settled_outcome_feedback_score",
    "calibration_update_quality_score",
    "evidence_reuse_score",
    "cost_pressure_score",
    "stale_thesis_pressure_score",
)
CONFIG_DECIMAL_FIELDS = EXPECTED_CONFIG_FIELDS[1:-3]
FORBIDDEN_IO_MODULE_ROOTS = {
    "http",
    "httpx",
    "os",
    "pathlib",
    "requests",
    "socket",
    "subprocess",
    "urllib",
}
FORBIDDEN_IO_CALL_SUFFIXES = {
    "connect",
    "create_connection",
    "open",
    "popen",
    "read_bytes",
    "read_text",
    "request",
    "run",
    "socket",
    "system",
    "urlopen",
    "write_bytes",
    "write_text",
}


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyOutcomeLearningEdgeDecayConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_REPORT_CONFIG_VERSION
        ),
        "pass_min_outcome_learning_score": d("0.750000"),
        "watch_min_outcome_learning_score": d("0.550000"),
        "max_pass_probability_edge_decay_ratio": d("0.200000"),
        "max_watch_probability_edge_decay_ratio": d("0.450000"),
        "min_pass_settled_outcome_feedback_score": d("0.750000"),
        "min_watch_settled_outcome_feedback_score": d("0.500000"),
        "min_pass_calibration_update_quality_score": d("0.750000"),
        "min_watch_calibration_update_quality_score": d("0.500000"),
        "min_pass_evidence_reuse_score": d("0.700000"),
        "min_watch_evidence_reuse_score": d("0.450000"),
        "max_pass_cost_pressure_score": d("0.250000"),
        "max_watch_cost_pressure_score": d("0.500000"),
        "max_pass_stale_thesis_pressure_score": d("0.200000"),
        "max_watch_stale_thesis_pressure_score": d("0.450000"),
        "settled_feedback_weight": d("0.250000"),
        "calibration_update_weight": d("0.250000"),
        "evidence_reuse_weight": d("0.150000"),
        "cost_pressure_weight": d("0.150000"),
        "stale_thesis_weight": d("0.100000"),
        "edge_retention_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchStrategyOutcomeLearningEdgeDecayConfig(**values)


def learning_input(**overrides: object) -> ResearchStrategyOutcomeLearningEdgeDecayInput:
    values = {
        "candidate_ref": "candidate-alpha-raw",
        "surface_ref": "market-alpha-slug?token=hidden&wallet=private",
        "observed_at": OBSERVED_AT,
        "pre_feedback_probability_edge": d("0.100000"),
        "post_feedback_probability_edge": d("0.090000"),
        "settled_outcome_feedback_score": d("0.900000"),
        "calibration_update_quality_score": d("0.850000"),
        "evidence_reuse_score": d("0.800000"),
        "cost_pressure_score": d("0.100000"),
        "stale_thesis_pressure_score": d("0.100000"),
        "reason_codes": ("settled_outcome_feedback_ready",),
    }
    values.update(overrides)
    return ResearchStrategyOutcomeLearningEdgeDecayInput(**values)


def report(
    *rows: ResearchStrategyOutcomeLearningEdgeDecayInput,
    cfg: ResearchStrategyOutcomeLearningEdgeDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyOutcomeLearningEdgeDecayReport:
    return build_research_strategy_outcome_learning_edge_decay_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def resign_payload(payload: dict[str, object]) -> dict[str, object]:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    payload["derived_validation_digest"] = sha256(
        json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()
    return payload


def assert_decimal_public_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(
            (
                "_count",
                "_score",
                "_weight",
                "_ratio",
                "_probability",
                "_seconds",
                "_pressure",
                "_edge",
            ),
        ):
            assert type(item) is Decimal


def reordered_mapping(value: dict[str, object]) -> dict[str, object]:
    items = list(value.items())
    items[0], items[1] = items[1], items[0]
    return dict(items)


def nested_payload_object(
    payload: dict[str, object],
    section: str,
) -> tuple[object, object, dict[str, object]]:
    if section == "config":
        return payload, "config", payload["config"]  # type: ignore[return-value]
    if section == "row":
        rows = payload["rows"]
        return rows, 0, rows[0]  # type: ignore[index, return-value]
    if section == "reason_code_count":
        counts = payload["reason_code_counts"]
        return counts, 0, counts[0]  # type: ignore[index, return-value]
    raise AssertionError(f"unsupported section: {section}")


def set_nested_value(parent: object, key: object, value: object) -> None:
    if type(parent) is dict:
        parent[key] = value  # type: ignore[index]
        return
    if type(parent) is list:
        parent[key] = value  # type: ignore[index]
        return
    raise AssertionError("nested payload parent must be a dict or list")


def qualified_ast_name(node: ast.AST, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        parent = qualified_ast_name(node.value, aliases)
        if parent is None:
            return None
        return f"{parent}.{node.attr}"
    return None


def ast_no_io_violations(source: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    aliases: dict[str, str] = {}
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound_name = alias.asname or alias.name.split(".", maxsplit=1)[0]
                aliases[bound_name] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            for alias in node.names:
                if alias.name == "*":
                    continue
                aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        assigned_name = qualified_ast_name(node.value, aliases)
        if assigned_name is None:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                aliases[target.id] = assigned_name

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        call_name = qualified_ast_name(node.func, aliases)
        if call_name is None:
            continue
        root = call_name.split(".", maxsplit=1)[0]
        if root in FORBIDDEN_IO_MODULE_ROOTS:
            violations.append(call_name)
        if call_name.rsplit(".", maxsplit=1)[-1].casefold() in {
            item.casefold() for item in FORBIDDEN_IO_CALL_SUFFIXES
        }:
            violations.append(call_name)
        if call_name in {
            "__import__",
            "builtins.__import__",
            "importlib.import_module",
        }:
            if node.args and isinstance(node.args[0], ast.Constant):
                imported_name = node.args[0].value
                if type(imported_name) is str:
                    imported_root = imported_name.split(".", maxsplit=1)[0]
                    if imported_root in FORBIDDEN_IO_MODULE_ROOTS:
                        violations.append(f"{call_name}({imported_name})")

    return tuple(violations)


def threshold_reason_codes(
    signal_name: str,
    value: Decimal,
) -> tuple[str, ...]:
    values = {
        "upstream_reason_codes": (),
        "probability_edge_decay_ratio": d("0.100000"),
        "settled_outcome_feedback_score": d("0.900000"),
        "calibration_update_quality_score": d("0.900000"),
        "evidence_reuse_score": d("0.900000"),
        "cost_pressure_score": d("0.100000"),
        "stale_thesis_pressure_score": d("0.100000"),
        "outcome_learning_score": d("0.900000"),
        "config": config(),
    }
    values[signal_name] = value
    return edge_decay_api._row_reason_codes(**values)


def sort_probe(**overrides: object) -> SimpleNamespace:
    values = {
        "status": "block",
        "outcome_learning_score": d("0.100000"),
        "probability_edge_decay_ratio": d("0.100000"),
        "pre_feedback_probability_edge": d("0.100000"),
        "post_feedback_probability_edge": d("0.100000"),
        "edge_retention_score": d("0.100000"),
        "settled_outcome_feedback_score": d("0.100000"),
        "calibration_update_quality_score": d("0.100000"),
        "evidence_reuse_score": d("0.100000"),
        "cost_pressure_score": d("0.100000"),
        "cost_relief_score": d("0.100000"),
        "stale_thesis_pressure_score": d("0.100000"),
        "thesis_freshness_score": d("0.100000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("a",),
        "learning_ref_digest": "sha256:" + ("0" * 64),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_scores_outcome_learning_edge_decay_across_pass_watch_and_block() -> None:
    summary = report(
        learning_input(
            candidate_ref="candidate-pass-raw",
            surface_ref="market-pass-slug?token=hidden",
            pre_feedback_probability_edge=d("0.100000"),
            post_feedback_probability_edge=d("0.090000"),
            settled_outcome_feedback_score=d("0.900000"),
            calibration_update_quality_score=d("0.850000"),
            evidence_reuse_score=d("0.800000"),
            cost_pressure_score=d("0.100000"),
            stale_thesis_pressure_score=d("0.100000"),
            reason_codes=("settled_outcome_feedback_ready",),
        ),
        learning_input(
            candidate_ref="candidate-watch-raw",
            surface_ref="market-watch-slug",
            pre_feedback_probability_edge=d("0.100000"),
            post_feedback_probability_edge=d("0.070000"),
            settled_outcome_feedback_score=d("0.650000"),
            calibration_update_quality_score=d("0.600000"),
            evidence_reuse_score=d("0.550000"),
            cost_pressure_score=d("0.350000"),
            stale_thesis_pressure_score=d("0.300000"),
            reason_codes=("calibration_update_ready", "evidence_reuse_ready"),
        ),
        learning_input(
            candidate_ref="candidate-block-raw",
            surface_ref="market-block-slug",
            pre_feedback_probability_edge=d("0.100000"),
            post_feedback_probability_edge=d("0.040000"),
            settled_outcome_feedback_score=d("0.300000"),
            calibration_update_quality_score=d("0.400000"),
            evidence_reuse_score=d("0.200000"),
            cost_pressure_score=d("0.650000"),
            stale_thesis_pressure_score=d("0.700000"),
            reason_codes=("settled_outcome_feedback_ready",),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert type(summary) is ResearchStrategyOutcomeLearningEdgeDecayReport
    assert summary.generated_at == GENERATED_AT
    assert summary.config_version == (
        DEFAULT_RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_REPORT_CONFIG_VERSION
    )
    assert summary.status == "block"
    assert summary.input_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_outcome_learning_score == d("0.610833")
    assert summary.min_outcome_learning_score == d("0.327500")
    assert summary.max_probability_edge_decay_ratio == d("0.600000")
    assert summary.min_settled_outcome_feedback_score == d("0.300000")
    assert summary.min_calibration_update_quality_score == d("0.400000")
    assert summary.min_evidence_reuse_score == d("0.200000")
    assert summary.max_cost_pressure_score == d("0.650000")
    assert summary.max_stale_thesis_pressure_score == d("0.700000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked = summary.rows[0]
    assert type(blocked) is ResearchStrategyOutcomeLearningEdgeDecayRow
    assert blocked.probability_edge_decay_ratio == d("0.600000")
    assert blocked.edge_retention_score == d("0.400000")
    assert blocked.cost_relief_score == d("0.350000")
    assert blocked.thesis_freshness_score == d("0.300000")
    assert blocked.outcome_learning_score == d("0.327500")
    assert blocked.reason_codes == (
        "settled_outcome_feedback_ready",
        "edge_decay_block",
        "settled_feedback_block",
        "calibration_update_block",
        "evidence_reuse_block",
        "cost_pressure_block",
        "stale_thesis_pressure_block",
        "outcome_learning_score_block",
    )

    watched = summary.rows[1]
    assert watched.probability_edge_decay_ratio == d("0.300000")
    assert watched.edge_retention_score == d("0.700000")
    assert watched.cost_relief_score == d("0.650000")
    assert watched.thesis_freshness_score == d("0.700000")
    assert watched.outcome_learning_score == d("0.632500")
    assert watched.reason_codes == (
        "calibration_update_ready",
        "evidence_reuse_ready",
        "edge_decay_watch",
        "settled_feedback_watch",
        "calibration_update_watch",
        "evidence_reuse_watch",
        "cost_pressure_watch",
        "stale_thesis_pressure_watch",
        "outcome_learning_score_watch",
    )

    passed = summary.rows[2]
    assert passed.probability_edge_decay_ratio == d("0.100000")
    assert passed.edge_retention_score == d("0.900000")
    assert passed.outcome_learning_score == d("0.872500")
    assert passed.reason_codes == (
        "settled_outcome_feedback_ready",
        "outcome_learning_pass",
    )

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["edge_decay_block"] == ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount(
        reason_code="edge_decay_block",
        count=d("1.000000"),
        input_ratio=d("0.333333"),
    )


def test_empty_report_is_report_only_block() -> None:
    summary = report()

    assert summary.status == "block"
    assert summary.input_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.average_outcome_learning_score == ZERO
    assert summary.min_outcome_learning_score == ZERO
    assert summary.max_probability_edge_decay_ratio == ZERO
    assert summary.min_settled_outcome_feedback_score == ZERO
    assert summary.min_calibration_update_quality_score == ZERO
    assert summary.min_evidence_reuse_score == ZERO
    assert summary.max_cost_pressure_score == ZERO
    assert summary.max_stale_thesis_pressure_score == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == ("empty_input",)
    assert summary.reason_code_counts == (
        ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            input_ratio=d("1.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_empty_report_payload_round_trips_canonically() -> None:
    payload = research_strategy_outcome_learning_edge_decay_report_payload(report())

    assert tuple(payload) == EXPECTED_REPORT_FIELDS
    assert payload["rows"] == []
    assert research_strategy_outcome_learning_edge_decay_report_payload(payload) == payload


def test_payload_is_deterministic_digest_guarded_and_leak_free() -> None:
    first_payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    second_payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert first_payload["input_count"] == "1.000000"
    assert first_payload["rows"][0]["learning_ref_digest"].startswith("sha256:")
    assert first_payload["rows"][0]["outcome_learning_score"] == "0.872500"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    payload_text = json.dumps(first_payload, sort_keys=True).casefold()
    report_text = repr(asdict(report(learning_input()))).casefold()
    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "recommend",
        "sizing",
        "candidate-alpha-raw",
        "market-alpha-slug",
        "hidden",
        "private",
    ):
        assert forbidden not in payload_text
        assert forbidden not in report_text

    tampered = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    tampered["rows"][0]["outcome_learning_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_outcome_learning_edge_decay_report_payload(tampered)

    raw_digest_payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    raw_digest_payload["rows"][0]["learning_ref_digest"] = "alpha-raw-ref"  # type: ignore[index]
    with pytest.raises(ValueError, match="learning_ref_digest"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(raw_digest_payload),
        )

    missing_flag_payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    del missing_flag_payload["paper_only"]
    with pytest.raises(ValueError, match="paper_only"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(missing_flag_payload),
        )

    execution_surface_payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    execution_surface_payload["execution_action"] = "disabled"
    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(execution_surface_payload),
        )

    with pytest.raises(ValueError, match="unsafe public"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            {
                "market_slug": "raw-market-alpha-slug",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_public_payload_schema_is_exact_and_canonical() -> None:
    extra_top_level = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    extra_top_level["audit_note"] = "pass"
    with pytest.raises(ValueError, match="unexpected fields"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(extra_top_level),
        )

    missing_top_level = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    del missing_top_level["average_outcome_learning_score"]
    with pytest.raises(ValueError, match="missing fields"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(missing_top_level),
        )

    extra_row_field = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    extra_row_field["rows"][0]["audit_note"] = "pass"  # type: ignore[index]
    with pytest.raises(ValueError, match="unexpected fields"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(extra_row_field),
        )

    noncanonical_decimal = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    noncanonical_decimal["input_count"] = "1"
    with pytest.raises(ValueError, match="input_count"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(noncanonical_decimal),
        )


def test_public_dataclass_declaration_and_payload_field_order_are_canonical() -> None:
    summary = report(learning_input())
    payload = research_strategy_outcome_learning_edge_decay_report_payload(summary)

    assert tuple(field.name for field in fields(summary)) == EXPECTED_REPORT_FIELDS
    assert tuple(field.name for field in fields(summary.config)) == EXPECTED_CONFIG_FIELDS
    assert tuple(field.name for field in fields(summary.rows[0])) == EXPECTED_ROW_FIELDS
    assert tuple(
        field.name for field in fields(summary.reason_code_counts[0])
    ) == EXPECTED_REASON_CODE_COUNT_FIELDS
    assert tuple(payload) == EXPECTED_REPORT_FIELDS
    assert tuple(payload["config"]) == EXPECTED_CONFIG_FIELDS  # type: ignore[arg-type]
    assert tuple(payload["rows"][0]) == EXPECTED_ROW_FIELDS  # type: ignore[index]
    assert tuple(payload["reason_code_counts"][0]) == (  # type: ignore[index]
        EXPECTED_REASON_CODE_COUNT_FIELDS
    )


@pytest.mark.parametrize("section", ("config", "row", "reason_code_count"))
@pytest.mark.parametrize("mutation", ("missing", "unknown", "type", "reorder"))
def test_nested_payload_validators_reject_schema_drift(
    section: str,
    mutation: str,
) -> None:
    payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    parent, key, nested = nested_payload_object(payload, section)

    if mutation == "missing":
        mutated = dict(nested)
        mutated.pop(next(iter(mutated)))
    elif mutation == "unknown":
        mutated = dict(nested)
        mutated["audit_note"] = "pass"
    elif mutation == "type":
        mutated = []
    else:
        mutated = reordered_mapping(nested)
    set_nested_value(parent, key, mutated)

    match = "canonical field order" if mutation == "reorder" else None
    with pytest.raises(ValueError, match=match):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(payload),
        )


def test_resigned_top_level_payload_rejects_reordered_fields() -> None:
    payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    reordered = reordered_mapping(payload)

    with pytest.raises(ValueError, match="canonical field order"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(reordered),
        )


@pytest.mark.parametrize(
    ("field_path", "value"),
    (
        ("generated_at", "2026-07-08T18:00:00Z"),
        ("generated_at", "2026-07-08T19:00:00+01:00"),
        ("generated_at", "2026-07-08T18:00:00.000000+00:00"),
        ("rows.0.observed_at", "2026-07-08T17:30:00Z"),
        ("rows.0.observed_at", "2026-07-08T18:30:00+01:00"),
        ("rows.0.observed_at", "2026-07-08T17:30:00.000000+00:00"),
    ),
)
def test_public_payload_rejects_noncanonical_datetimes(
    field_path: str,
    value: str,
) -> None:
    payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    if field_path == "generated_at":
        payload["generated_at"] = value
    else:
        payload["rows"][0]["observed_at"] = value  # type: ignore[index]

    with pytest.raises(ValueError, match="canonical UTC datetime"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(payload),
        )


@pytest.mark.parametrize(
    "value",
    (
        "1",
        "01.000000",
        "+1.000000",
        "1E+0",
        "1.0000000",
        "-0.000000",
    ),
)
@pytest.mark.parametrize(
    "field_path",
    (
        "input_count",
        "config.pass_min_outcome_learning_score",
        "rows.0.outcome_learning_score",
        "reason_code_counts.0.count",
    ),
)
def test_public_payload_rejects_noncanonical_decimal_strings(
    field_path: str,
    value: str,
) -> None:
    payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    if field_path == "input_count":
        payload["input_count"] = value
    elif field_path.startswith("config."):
        payload["config"]["pass_min_outcome_learning_score"] = value  # type: ignore[index]
    elif field_path.startswith("rows."):
        payload["rows"][0]["outcome_learning_score"] = value  # type: ignore[index]
    else:
        payload["reason_code_counts"][0]["count"] = value  # type: ignore[index]

    with pytest.raises(ValueError, match="canonical Decimal string"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(payload),
        )


def test_resigned_public_payload_rejects_internal_consistency_drift() -> None:
    count_drift = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    count_drift["input_count"] = "2.000000"
    with pytest.raises(ValueError, match="input_count must match rows"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(count_drift),
        )

    row_drift = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    row_drift["rows"][0]["probability_edge_decay_ratio"] = "0.200000"  # type: ignore[index]
    with pytest.raises(
        ValueError,
        match="probability_edge_decay_ratio must match feedback edges",
    ):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(row_drift),
        )

    reason_count_drift = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    reason_count_drift["reason_code_counts"][0]["count"] = "2.000000"  # type: ignore[index]
    with pytest.raises(ValueError, match="reason_code_counts must match rows"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(reason_count_drift),
        )


def test_resigned_public_payload_rejects_forged_derived_semantics() -> None:
    forged = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    forged_row = forged["rows"][0]  # type: ignore[index]
    forged_row["outcome_learning_score"] = "0.100000"
    forged_row["status"] = "block"
    forged_row["reason_codes"] = [
        "settled_outcome_feedback_ready",
        "outcome_learning_score_block",
    ]
    forged["status"] = "block"
    forged["pass_count"] = "0.000000"
    forged["block_count"] = "1.000000"
    forged["average_outcome_learning_score"] = "0.100000"
    forged["min_outcome_learning_score"] = "0.100000"
    forged["reason_code_counts"][1][  # type: ignore[index]
        "reason_code"
    ] = "outcome_learning_score_block"
    forged["reason_codes"] = [
        "settled_outcome_feedback_ready",
        "outcome_learning_score_block",
    ]

    with pytest.raises(
        ValueError,
        match="outcome_learning_score must match component scores",
    ):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(forged),
        )


def test_resigned_public_payload_rejects_forged_reason_semantics() -> None:
    forged = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    forged_row = forged["rows"][0]  # type: ignore[index]
    forged_row["status"] = "watch"
    forged_row["reason_codes"] = [
        "settled_outcome_feedback_ready",
        "edge_decay_watch",
    ]
    forged["status"] = "watch"
    forged["pass_count"] = "0.000000"
    forged["watch_count"] = "1.000000"
    forged["reason_code_counts"][1][  # type: ignore[index]
        "reason_code"
    ] = "edge_decay_watch"
    forged["reason_codes"] = [
        "settled_outcome_feedback_ready",
        "edge_decay_watch",
    ]

    with pytest.raises(
        ValueError,
        match="reason_codes must match outcome_learning thresholds",
    ):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(forged),
        )


def test_rows_reject_forged_derived_score_status_and_reasons() -> None:
    row = report(learning_input()).rows[0]

    with pytest.raises(
        ValueError,
        match="outcome_learning_score must match component scores",
    ):
        replace(
            row,
            outcome_learning_score=d("0.100000"),
            status="block",
            reason_codes=(
                "settled_outcome_feedback_ready",
                "outcome_learning_score_block",
            ),
        )


def test_resigned_public_payload_rejects_observation_after_generation() -> None:
    forged = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    forged["generated_at"] = "2026-07-08T17:00:00+00:00"

    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(forged),
        )


def test_decimal_math_is_isolated_from_ambient_context() -> None:
    baseline = report(
        learning_input(
            pre_feedback_probability_edge=d("0.100000"),
            post_feedback_probability_edge=d("0.070000"),
            settled_outcome_feedback_score=d("0.650000"),
            calibration_update_quality_score=d("0.600000"),
            evidence_reuse_score=d("0.550000"),
            cost_pressure_score=d("0.350000"),
            stale_thesis_pressure_score=d("0.300000"),
        ),
    )

    with localcontext() as ambient:
        ambient.prec = 4
        ambient.rounding = ROUND_DOWN
        constrained = report(
            learning_input(
                pre_feedback_probability_edge=d("0.100000"),
                post_feedback_probability_edge=d("0.070000"),
                settled_outcome_feedback_score=d("0.650000"),
                calibration_update_quality_score=d("0.600000"),
                evidence_reuse_score=d("0.550000"),
                cost_pressure_score=d("0.350000"),
                stale_thesis_pressure_score=d("0.300000"),
            ),
        )

    assert constrained == baseline
    assert research_strategy_outcome_learning_edge_decay_report_payload(
        constrained,
    ) == research_strategy_outcome_learning_edge_decay_report_payload(baseline)


@pytest.mark.parametrize("delta", (-1, 0, 1))
@pytest.mark.parametrize(
    (
        "threshold_field",
        "signal_name",
        "reason_family",
        "expected_by_delta",
    ),
    (
        (
            "pass_min_outcome_learning_score",
            "outcome_learning_score",
            ("outcome_learning_score_block", "outcome_learning_score_watch"),
            ("outcome_learning_score_watch", None, None),
        ),
        (
            "watch_min_outcome_learning_score",
            "outcome_learning_score",
            ("outcome_learning_score_block", "outcome_learning_score_watch"),
            (
                "outcome_learning_score_block",
                "outcome_learning_score_watch",
                "outcome_learning_score_watch",
            ),
        ),
        (
            "max_pass_probability_edge_decay_ratio",
            "probability_edge_decay_ratio",
            ("edge_decay_block", "edge_decay_watch"),
            (None, None, "edge_decay_watch"),
        ),
        (
            "max_watch_probability_edge_decay_ratio",
            "probability_edge_decay_ratio",
            ("edge_decay_block", "edge_decay_watch"),
            ("edge_decay_watch", "edge_decay_watch", "edge_decay_block"),
        ),
        (
            "min_pass_settled_outcome_feedback_score",
            "settled_outcome_feedback_score",
            ("settled_feedback_block", "settled_feedback_watch"),
            ("settled_feedback_watch", None, None),
        ),
        (
            "min_watch_settled_outcome_feedback_score",
            "settled_outcome_feedback_score",
            ("settled_feedback_block", "settled_feedback_watch"),
            (
                "settled_feedback_block",
                "settled_feedback_watch",
                "settled_feedback_watch",
            ),
        ),
        (
            "min_pass_calibration_update_quality_score",
            "calibration_update_quality_score",
            ("calibration_update_block", "calibration_update_watch"),
            ("calibration_update_watch", None, None),
        ),
        (
            "min_watch_calibration_update_quality_score",
            "calibration_update_quality_score",
            ("calibration_update_block", "calibration_update_watch"),
            (
                "calibration_update_block",
                "calibration_update_watch",
                "calibration_update_watch",
            ),
        ),
        (
            "min_pass_evidence_reuse_score",
            "evidence_reuse_score",
            ("evidence_reuse_block", "evidence_reuse_watch"),
            ("evidence_reuse_watch", None, None),
        ),
        (
            "min_watch_evidence_reuse_score",
            "evidence_reuse_score",
            ("evidence_reuse_block", "evidence_reuse_watch"),
            (
                "evidence_reuse_block",
                "evidence_reuse_watch",
                "evidence_reuse_watch",
            ),
        ),
        (
            "max_pass_cost_pressure_score",
            "cost_pressure_score",
            ("cost_pressure_block", "cost_pressure_watch"),
            (None, None, "cost_pressure_watch"),
        ),
        (
            "max_watch_cost_pressure_score",
            "cost_pressure_score",
            ("cost_pressure_block", "cost_pressure_watch"),
            ("cost_pressure_watch", "cost_pressure_watch", "cost_pressure_block"),
        ),
        (
            "max_pass_stale_thesis_pressure_score",
            "stale_thesis_pressure_score",
            ("stale_thesis_pressure_block", "stale_thesis_pressure_watch"),
            (None, None, "stale_thesis_pressure_watch"),
        ),
        (
            "max_watch_stale_thesis_pressure_score",
            "stale_thesis_pressure_score",
            ("stale_thesis_pressure_block", "stale_thesis_pressure_watch"),
            (
                "stale_thesis_pressure_watch",
                "stale_thesis_pressure_watch",
                "stale_thesis_pressure_block",
            ),
        ),
    ),
)
def test_each_pass_watch_threshold_covers_equal_and_one_quantum_neighbors(
    threshold_field: str,
    signal_name: str,
    reason_family: tuple[str, str],
    expected_by_delta: tuple[str | None, str | None, str | None],
    delta: int,
) -> None:
    threshold = getattr(config(), threshold_field)
    reasons = threshold_reason_codes(signal_name, threshold + (QUANTUM * delta))
    actual = tuple(reason for reason in reasons if reason in reason_family)
    expected_reason = expected_by_delta[delta + 1]

    assert actual == (() if expected_reason is None else (expected_reason,))


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("pre_feedback_probability_edge", d("1.0000004")),
        ("post_feedback_probability_edge", d("-0.0000004")),
        ("settled_outcome_feedback_score", d("1.0000004")),
        ("cost_pressure_score", d("-0.0000004")),
    ),
)
def test_ratio_inputs_reject_raw_bounds_before_quantization(
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        learning_input(**{field_name: value})


@pytest.mark.parametrize(
    "value",
    (
        d("-0"),
        d("-0E-1000"),
        d("NaN"),
        d("sNaN"),
        d("Infinity"),
        d("-Infinity"),
    ),
)
def test_ratio_inputs_reject_signed_zero_and_non_finite_values(
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match="pre_feedback_probability_edge"):
        learning_input(pre_feedback_probability_edge=value)


@pytest.mark.parametrize("field_name", INPUT_DECIMAL_FIELDS)
@pytest.mark.parametrize(
    "value",
    (
        d("1.0000004"),
        d("-0.0000004"),
        d("-0"),
        d("-0E-1000"),
        d("NaN"),
        d("sNaN"),
        d("Infinity"),
        d("-Infinity"),
        _DecimalSubclass("0.500000"),
    ),
)
def test_every_input_decimal_rejects_raw_invalid_matrix(
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        learning_input(**{field_name: value})


@pytest.mark.parametrize("field_name", CONFIG_DECIMAL_FIELDS)
@pytest.mark.parametrize(
    "value",
    (
        d("1.0000004"),
        d("-0.0000004"),
        d("-0"),
        d("-0E-1000"),
        d("NaN"),
        d("sNaN"),
        d("Infinity"),
        d("-Infinity"),
        _DecimalSubclass("0.500000"),
    ),
)
def test_every_config_decimal_rejects_raw_invalid_matrix(
    field_name: str,
    value: Decimal,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        config(**{field_name: value})


def test_count_decimals_reject_fractional_raw_values_before_quantization() -> None:
    with pytest.raises(ValueError, match="count.*integer"):
        ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount(
            reason_code="empty_input",
            count=d("1.0000004"),
            input_ratio=d("1.000000"),
        )


def test_public_dataclasses_reject_subclassing() -> None:
    with pytest.raises(TypeError, match="may not be subclassed"):

        class _ForgedInput(ResearchStrategyOutcomeLearningEdgeDecayInput):
            pass


def test_reused_config_revalidates_object_setattr_mutations() -> None:
    mutated = config()
    object.__setattr__(mutated, "settled_feedback_weight", d("0.300000"))

    with pytest.raises(ValueError, match="outcome_learning weights"):
        report(learning_input(), cfg=mutated)


def test_reused_inputs_revalidate_object_setattr_mutations() -> None:
    mutated = learning_input()
    object.__setattr__(mutated, "candidate_ref", "")

    with pytest.raises(ValueError, match="candidate_ref"):
        report(mutated)


def test_report_revalidates_object_setattr_mutated_nested_rows() -> None:
    summary = report(learning_input())
    row = summary.rows[0]
    object.__setattr__(row, "learning_ref_digest", "not-a-sha256-digest")

    with pytest.raises(ValueError, match="learning_ref_digest"):
        replace(summary, rows=(row,), derived_validation_digest="")


def test_report_revalidates_object_setattr_mutated_reason_counts() -> None:
    summary = report(learning_input())
    reason_counts = list(summary.reason_code_counts)
    reason_count = reason_counts[0]
    object.__setattr__(reason_count, "count", d("1.0000000"))
    reason_counts[0] = reason_count

    rebuilt = replace(
        summary,
        reason_code_counts=tuple(reason_counts),
        derived_validation_digest="",
    )

    assert rebuilt.reason_code_counts[0].count == d("1.000000")
    assert str(rebuilt.reason_code_counts[0].count) == "1.000000"


def test_resigned_payload_recomputes_derived_fields_from_embedded_config() -> None:
    lenient = config(
        pass_min_outcome_learning_score=d("0.600000"),
        watch_min_outcome_learning_score=d("0.300000"),
        max_pass_probability_edge_decay_ratio=d("0.350000"),
        max_watch_probability_edge_decay_ratio=d("0.700000"),
        min_pass_settled_outcome_feedback_score=d("0.600000"),
        min_watch_settled_outcome_feedback_score=d("0.300000"),
        min_pass_calibration_update_quality_score=d("0.550000"),
        min_watch_calibration_update_quality_score=d("0.300000"),
        min_pass_evidence_reuse_score=d("0.500000"),
        min_watch_evidence_reuse_score=d("0.250000"),
        max_pass_cost_pressure_score=d("0.400000"),
        max_watch_cost_pressure_score=d("0.700000"),
        max_pass_stale_thesis_pressure_score=d("0.350000"),
        max_watch_stale_thesis_pressure_score=d("0.700000"),
    )
    payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(
            learning_input(
                pre_feedback_probability_edge=d("0.100000"),
                post_feedback_probability_edge=d("0.070000"),
                settled_outcome_feedback_score=d("0.650000"),
                calibration_update_quality_score=d("0.600000"),
                evidence_reuse_score=d("0.550000"),
                cost_pressure_score=d("0.350000"),
                stale_thesis_pressure_score=d("0.300000"),
                reason_codes=("calibration_update_ready",),
            ),
            cfg=lenient,
        ),
    )

    assert payload["config"]["max_pass_probability_edge_decay_ratio"] == "0.350000"
    assert research_strategy_outcome_learning_edge_decay_report_payload(payload) == payload

    forged_threshold = json.loads(json.dumps(payload))
    forged_threshold["config"]["max_pass_probability_edge_decay_ratio"] = "0.100000"
    with pytest.raises(ValueError, match="reason_codes"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(forged_threshold),
        )

    forged_weights = json.loads(json.dumps(payload))
    forged_weights["config"]["settled_feedback_weight"] = "0.200000"
    forged_weights["config"]["calibration_update_weight"] = "0.300000"
    with pytest.raises(ValueError, match="outcome_learning_score"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(forged_weights),
        )

    extra_config_field = json.loads(json.dumps(payload))
    extra_config_field["config"]["audit_note"] = "pass"
    with pytest.raises(ValueError, match="unexpected fields"):
        research_strategy_outcome_learning_edge_decay_report_payload(
            resign_payload(extra_config_field),
        )


def test_resigned_payload_recomputes_every_public_derived_field() -> None:
    payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    row_mutations = {
        "probability_edge_decay_ratio": "0.200000",
        "edge_retention_score": "0.800000",
        "cost_relief_score": "0.800000",
        "thesis_freshness_score": "0.800000",
        "outcome_learning_score": "0.800000",
        "status": "watch",
        "reason_codes": [
            "settled_outcome_feedback_ready",
            "edge_decay_watch",
        ],
    }
    for field_name, forged_value in row_mutations.items():
        forged = json.loads(json.dumps(payload))
        forged["rows"][0][field_name] = forged_value
        with pytest.raises(ValueError):
            research_strategy_outcome_learning_edge_decay_report_payload(
                resign_payload(forged),
            )

    report_mutations = {
        "status": "watch",
        "input_count": "2.000000",
        "pass_count": "0.000000",
        "watch_count": "1.000000",
        "block_count": "1.000000",
        "average_outcome_learning_score": "0.800000",
        "min_outcome_learning_score": "0.800000",
        "max_probability_edge_decay_ratio": "0.200000",
        "min_settled_outcome_feedback_score": "0.800000",
        "min_calibration_update_quality_score": "0.800000",
        "min_evidence_reuse_score": "0.700000",
        "max_cost_pressure_score": "0.200000",
        "max_stale_thesis_pressure_score": "0.200000",
        "reason_codes": [
            "settled_outcome_feedback_ready",
            "edge_decay_watch",
        ],
    }
    for field_name, forged_value in report_mutations.items():
        forged = json.loads(json.dumps(payload))
        forged[field_name] = forged_value
        with pytest.raises(ValueError):
            research_strategy_outcome_learning_edge_decay_report_payload(
                resign_payload(forged),
            )

    for field_name, forged_value in (
        ("count", "2.000000"),
        ("input_ratio", "0.500000"),
        ("reason_code", "edge_decay_watch"),
    ):
        forged = json.loads(json.dumps(payload))
        forged["reason_code_counts"][0][field_name] = forged_value
        with pytest.raises(ValueError):
            research_strategy_outcome_learning_edge_decay_report_payload(
                resign_payload(forged),
            )


def test_learning_ref_digest_is_a_resignable_public_pseudonym_not_authentication() -> None:
    payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(learning_input()),
    )
    alternate_pseudonym = "sha256:" + sha256(b"public-pseudonym").hexdigest()
    payload["rows"][0]["learning_ref_digest"] = alternate_pseudonym  # type: ignore[index]
    resigned = resign_payload(payload)

    assert research_strategy_outcome_learning_edge_decay_report_payload(
        resigned,
    ) == resigned


def test_every_reason_count_field_is_recomputed_after_resigning() -> None:
    payload = research_strategy_outcome_learning_edge_decay_report_payload(
        report(
            learning_input(),
            learning_input(
                candidate_ref="candidate-beta-raw",
                surface_ref="surface-beta",
                reason_codes=("calibration_update_ready", "evidence_reuse_ready"),
            ),
        ),
    )

    for index in range(len(payload["reason_code_counts"])):  # type: ignore[arg-type]
        for field_name, forged_value in (
            ("reason_code", "empty_input"),
            ("count", "9.000000"),
            ("input_ratio", "0.123456"),
        ):
            forged = json.loads(json.dumps(payload))
            forged["reason_code_counts"][index][field_name] = forged_value
            with pytest.raises(ValueError):
                research_strategy_outcome_learning_edge_decay_report_payload(
                    resign_payload(forged),
                )


@pytest.mark.parametrize(
    ("sort_index", "field_name", "left_value", "right_value"),
    (
        (0, "status", "block", "watch"),
        (1, "outcome_learning_score", d("0.100000"), d("0.200000")),
        (2, "probability_edge_decay_ratio", d("0.100000"), d("0.200000")),
        (3, "pre_feedback_probability_edge", d("0.100000"), d("0.200000")),
        (4, "post_feedback_probability_edge", d("0.100000"), d("0.200000")),
        (5, "edge_retention_score", d("0.100000"), d("0.200000")),
        (6, "settled_outcome_feedback_score", d("0.100000"), d("0.200000")),
        (7, "calibration_update_quality_score", d("0.100000"), d("0.200000")),
        (8, "evidence_reuse_score", d("0.100000"), d("0.200000")),
        (9, "cost_pressure_score", d("0.100000"), d("0.200000")),
        (10, "cost_relief_score", d("0.100000"), d("0.200000")),
        (11, "stale_thesis_pressure_score", d("0.100000"), d("0.200000")),
        (12, "thesis_freshness_score", d("0.100000"), d("0.200000")),
        (13, "observed_at", OBSERVED_AT, OBSERVED_AT + timedelta(seconds=1)),
        (14, "reason_codes", ("a",), ("b",)),
        (
            15,
            "learning_ref_digest",
            "sha256:" + ("0" * 64),
            "sha256:" + ("1" * 64),
        ),
    ),
)
def test_complete_sort_key_uses_each_successive_tie_break(
    sort_index: int,
    field_name: str,
    left_value: object,
    right_value: object,
) -> None:
    left_key = edge_decay_api._row_sort_key(sort_probe(**{field_name: left_value}))
    right_key = edge_decay_api._row_sort_key(sort_probe(**{field_name: right_value}))

    assert left_key[:sort_index] == right_key[:sort_index]
    assert left_key[sort_index] < right_key[sort_index]
    assert left_key < right_key


def test_equal_status_and_score_rows_use_complete_stable_sorting() -> None:
    lower_decay = learning_input(
        candidate_ref="candidate-a-raw",
        surface_ref="surface-a",
        post_feedback_probability_edge=d("0.090000"),
        cost_pressure_score=d("0.200000"),
    )
    higher_decay = learning_input(
        candidate_ref="candidate-z-raw",
        surface_ref="surface-z",
        post_feedback_probability_edge=d("0.080000"),
        cost_pressure_score=d("0.133333"),
    )

    forward = report(higher_decay, lower_decay)
    reverse = report(lower_decay, higher_decay)

    assert tuple(row.status for row in forward.rows) == ("pass", "pass")
    assert tuple(row.outcome_learning_score for row in forward.rows) == (
        d("0.857500"),
        d("0.857500"),
    )
    assert tuple(row.probability_edge_decay_ratio for row in forward.rows) == (
        d("0.100000"),
        d("0.200000"),
    )
    assert forward == reverse
    assert research_strategy_outcome_learning_edge_decay_report_payload(
        forward,
    ) == research_strategy_outcome_learning_edge_decay_report_payload(reverse)


def test_report_is_invariant_to_every_input_permutation() -> None:
    inputs = (
        learning_input(
            candidate_ref="candidate-a-raw",
            surface_ref="surface-a",
            post_feedback_probability_edge=d("0.040000"),
        ),
        learning_input(
            candidate_ref="candidate-b-raw",
            surface_ref="surface-b",
            post_feedback_probability_edge=d("0.070000"),
            settled_outcome_feedback_score=d("0.650000"),
            calibration_update_quality_score=d("0.600000"),
            evidence_reuse_score=d("0.550000"),
            cost_pressure_score=d("0.350000"),
            stale_thesis_pressure_score=d("0.300000"),
        ),
        learning_input(
            candidate_ref="candidate-c-raw",
            surface_ref="surface-c",
        ),
        learning_input(
            candidate_ref="candidate-d-raw",
            surface_ref="surface-d",
            observed_at=OBSERVED_AT - timedelta(minutes=1),
        ),
    )
    expected = research_strategy_outcome_learning_edge_decay_report_payload(
        report(*inputs),
    )

    for ordering in permutations(inputs):
        assert research_strategy_outcome_learning_edge_decay_report_payload(
            report(*ordering),
        ) == expected


def test_custom_config_changes_thresholds_and_rejects_invalid_shapes() -> None:
    lenient = config(
        pass_min_outcome_learning_score=d("0.600000"),
        watch_min_outcome_learning_score=d("0.300000"),
        max_pass_probability_edge_decay_ratio=d("0.350000"),
        max_watch_probability_edge_decay_ratio=d("0.700000"),
        min_pass_settled_outcome_feedback_score=d("0.600000"),
        min_watch_settled_outcome_feedback_score=d("0.300000"),
        min_pass_calibration_update_quality_score=d("0.550000"),
        min_watch_calibration_update_quality_score=d("0.300000"),
        min_pass_evidence_reuse_score=d("0.500000"),
        min_watch_evidence_reuse_score=d("0.250000"),
        max_pass_cost_pressure_score=d("0.400000"),
        max_watch_cost_pressure_score=d("0.700000"),
        max_pass_stale_thesis_pressure_score=d("0.350000"),
        max_watch_stale_thesis_pressure_score=d("0.700000"),
    )
    summary = report(
        learning_input(
            pre_feedback_probability_edge=d("0.100000"),
            post_feedback_probability_edge=d("0.070000"),
            settled_outcome_feedback_score=d("0.650000"),
            calibration_update_quality_score=d("0.600000"),
            evidence_reuse_score=d("0.550000"),
            cost_pressure_score=d("0.350000"),
            stale_thesis_pressure_score=d("0.300000"),
            reason_codes=("calibration_update_ready",),
        ),
        cfg=lenient,
    )
    assert summary.status == "pass"
    assert summary.rows[0].reason_codes == (
        "calibration_update_ready",
        "outcome_learning_pass",
    )
    assert research_strategy_outcome_learning_edge_decay_report_payload(summary)[
        "status"
    ] == "pass"

    with pytest.raises(ValueError, match="config_version"):
        config(
            config_version=_StringSubclass(
                DEFAULT_RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_outcome_learning_score"):
        config(pass_min_outcome_learning_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_outcome_learning_score"):
        config(watch_min_outcome_learning_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="pass_min_outcome_learning_score"):
        config(pass_min_outcome_learning_score=d("0.500000"))
    with pytest.raises(ValueError, match="max_pass_probability_edge_decay_ratio"):
        config(max_pass_probability_edge_decay_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="outcome_learning weights"):
        config(settled_feedback_weight=d("0.300000"))


def test_validation_rejects_non_decimal_times_flags_and_drift() -> None:
    with pytest.raises(ValueError, match="candidate_ref"):
        learning_input(candidate_ref=_StringSubclass("candidate-alpha"))
    with pytest.raises(ValueError, match="surface_ref"):
        learning_input(surface_ref=" ")
    with pytest.raises(ValueError, match="pre_feedback_probability_edge"):
        learning_input(pre_feedback_probability_edge=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="post_feedback_probability_edge"):
        learning_input(post_feedback_probability_edge=_DecimalSubclass("0.090000"))
    with pytest.raises(ValueError, match="cost_pressure_score"):
        learning_input(cost_pressure_score=d("NaN"))
    with pytest.raises(ValueError, match="pre_feedback_probability_edge.*negative zero"):
        learning_input(pre_feedback_probability_edge=d("-0.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        learning_input(observed_at=_DateTimeSubclass(2026, 7, 8, 17, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(learning_input(observed_at=datetime(2026, 7, 8, 18, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="inputs"):
        build_research_strategy_outcome_learning_edge_decay_report(
            (object(),),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    summary = report(learning_input())
    with pytest.raises(ValueError, match="status"):
        replace(summary.rows[0], status="block")
    with pytest.raises(ValueError, match="outcome_learning_score"):
        replace(summary.rows[0], outcome_learning_score=ZERO, validation_config=config())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)


@pytest.mark.parametrize(
    "source",
    (
        "import pathlib as p\np.Path('x').read_text()",
        "from pathlib import Path as P\nP('x').write_text('x')",
        "import subprocess as sp\nsp.run(['true'])",
        "import socket as s\ns.socket()",
        "import http.client as hc\nhc.HTTPConnection('example.com')",
        "__import__('pathlib')",
        "import importlib as il\nil.import_module('subprocess')",
        "from importlib import import_module as load\nload('socket')",
        "loader = __import__\nloader('http.client')",
    ),
)
def test_ast_no_io_guard_detects_aliases_dynamic_imports_and_io_modules(
    source: str,
) -> None:
    assert ast_no_io_violations(source)


def test_dataclasses_are_frozen_decimal_only_and_public_api_is_narrow() -> None:
    summary = report(learning_input())
    row = summary.rows[0]

    assert is_dataclass(ResearchStrategyOutcomeLearningEdgeDecayConfig)
    assert is_dataclass(ResearchStrategyOutcomeLearningEdgeDecayInput)
    assert is_dataclass(ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount)
    assert is_dataclass(ResearchStrategyOutcomeLearningEdgeDecayRow)
    assert is_dataclass(ResearchStrategyOutcomeLearningEdgeDecayReport)
    assert RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_STATUSES == (
        "pass",
        "watch",
        "block",
    )

    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.reason_code_counts[0], readonly=False)

    assert_decimal_public_fields(learning_input())
    assert_decimal_public_fields(summary)
    assert_decimal_public_fields(row)
    assert_decimal_public_fields(summary.reason_code_counts[0])

    assert __import__(
        "polymarket_alpha_lab.research_strategy_outcome_learning_edge_decay_report",
        fromlist=["__all__"],
    ).__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_OUTCOME_LEARNING_EDGE_DECAY_STATUSES",
        "ResearchStrategyOutcomeLearningEdgeDecayConfig",
        "ResearchStrategyOutcomeLearningEdgeDecayInput",
        "ResearchStrategyOutcomeLearningEdgeDecayReasonCodeCount",
        "ResearchStrategyOutcomeLearningEdgeDecayReport",
        "ResearchStrategyOutcomeLearningEdgeDecayRow",
        "build_research_strategy_outcome_learning_edge_decay_report",
        "research_strategy_outcome_learning_edge_decay_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert ast_no_io_violations(source) == ()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
