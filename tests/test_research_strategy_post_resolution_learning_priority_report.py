from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_post_resolution_learning_priority_report.py"
)


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_post_resolution_learning_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def learning_input(
    analyst_label: str = "rates_research",
    learning_scope_label: str = "inflation_resolution_review",
    *,
    settled_outcome_signal_strength: Decimal = d("0.200000"),
    forecast_miss_severity: Decimal = d("0.100000"),
    source_evidence_gap: Decimal = d("0.100000"),
    calibration_freshness_score: Decimal = d("0.900000"),
    review_backlog_count: Decimal = d("0"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchStrategyPostResolutionLearningPriorityInput(
        analyst_label=analyst_label,
        learning_scope_label=learning_scope_label,
        settled_outcome_signal_strength=settled_outcome_signal_strength,
        forecast_miss_severity=forecast_miss_severity,
        source_evidence_gap=source_evidence_gap,
        calibration_freshness_score=calibration_freshness_score,
        review_backlog_count=review_backlog_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            "research-strategy-post-resolution-learning-priority-report-v0"
        ),
        "watch_min_learning_priority_score": d("0.500000"),
        "block_min_learning_priority_score": d("0.750000"),
        "watch_min_settled_outcome_signal_strength": d("0.650000"),
        "block_min_settled_outcome_signal_strength": d("0.850000"),
        "watch_min_forecast_miss_severity": d("0.300000"),
        "block_min_forecast_miss_severity": d("0.600000"),
        "watch_min_source_evidence_gap": d("0.250000"),
        "block_min_source_evidence_gap": d("0.500000"),
        "watch_max_calibration_freshness_score": d("0.600000"),
        "block_max_calibration_freshness_score": d("0.350000"),
        "watch_min_review_backlog_count": d("3"),
        "block_min_review_backlog_count": d("8"),
        "settled_outcome_signal_weight": d("0.200000"),
        "forecast_miss_weight": d("0.300000"),
        "source_evidence_gap_weight": d("0.200000"),
        "calibration_staleness_weight": d("0.150000"),
        "review_backlog_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchStrategyPostResolutionLearningPriorityConfig(**values)


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_strategy_post_resolution_learning_priority_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_payload_has_no_raw_numbers(value: Any) -> None:
    if type(value) in (int, float, Decimal):
        raise AssertionError(f"unexpected raw public numeric value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_raw_numbers(item)
    if isinstance(value, list):
        for item in value:
            assert_payload_has_no_raw_numbers(item)


def assert_payload_has_no_forbidden_surface(payload: dict[str, Any]) -> None:
    payload_text = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "raw_source",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "auth",
        "live",
    ):
        assert forbidden not in payload_text


def test_priority_report_scores_pass_watch_and_block_analyst_rows() -> None:
    module = api()
    report = build_report(
        learning_input(),
        learning_input(
            "energy_research",
            "load_resolution_review",
            settled_outcome_signal_strength=d("0.700000"),
            forecast_miss_severity=d("0.350000"),
            source_evidence_gap=d("0.300000"),
            calibration_freshness_score=d("0.500000"),
            review_backlog_count=d("4"),
        ),
        learning_input(
            "crypto_research",
            "protocol_resolution_review",
            settled_outcome_signal_strength=d("0.900000"),
            forecast_miss_severity=d("0.700000"),
            source_evidence_gap=d("0.600000"),
            calibration_freshness_score=d("0.200000"),
            review_backlog_count=d("9"),
        ),
    )

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert module.POST_RESOLUTION_LEARNING_PRIORITY_STATUSES == ("pass", "watch", "block")
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-strategy-post-resolution-learning-priority-report-v0"
    )
    assert report.analyst_count == d("3")
    assert report.row_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.attention_count == d("2")
    assert report.average_learning_priority_score == d("0.446667")
    assert report.max_learning_priority_score == d("0.780000")
    assert report.max_forecast_miss_severity == d("0.700000")
    assert report.max_source_evidence_gap == d("0.600000")
    assert report.min_calibration_freshness_score == d("0.200000")
    assert report.max_review_backlog_count == d("9")
    assert report.status == "block"
    assert report.reason_codes == (
        "post_resolution_learning_priority_block",
        "settled_outcome_signal_block",
        "forecast_miss_block",
        "source_evidence_gap_block",
        "calibration_freshness_block",
        "review_backlog_block",
        "settled_outcome_signal_watch",
        "forecast_miss_watch",
        "source_evidence_gap_watch",
        "calibration_freshness_watch",
        "review_backlog_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    block_row, watch_row, pass_row = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert block_row.analyst_label == "crypto_research"
    assert block_row.learning_priority_score == d("0.780000")
    assert block_row.review_backlog_pressure == d("1.000000")
    assert block_row.reason_codes == (
        "settled_outcome_signal_block",
        "forecast_miss_block",
        "source_evidence_gap_block",
        "calibration_freshness_block",
        "review_backlog_block",
        "post_resolution_learning_priority_block",
    )
    assert watch_row.analyst_label == "energy_research"
    assert watch_row.learning_priority_score == d("0.455000")
    assert watch_row.calibration_staleness_score == d("0.500000")
    assert watch_row.review_backlog_pressure == d("0.500000")
    assert watch_row.reason_codes == (
        "settled_outcome_signal_watch",
        "forecast_miss_watch",
        "source_evidence_gap_watch",
        "calibration_freshness_watch",
        "review_backlog_watch",
        "post_resolution_learning_priority_watch",
    )
    assert pass_row.analyst_label == "rates_research"
    assert pass_row.learning_priority_score == d("0.105000")
    assert pass_row.reason_codes == ("post_resolution_learning_priority_pass",)

    payload = report.public_payload
    assert payload == module.research_strategy_post_resolution_learning_priority_report_public_payload(report)
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert payload["rows"][0]["derived_validation_digest"] == block_row.derived_validation_digest
    assert payload["rows"][1]["learning_priority_score"] == "0.455000"
    assert module.validate_research_strategy_post_resolution_learning_priority_public_payload(payload)
    assert_payload_has_no_raw_numbers(payload)
    assert_payload_has_no_forbidden_surface(payload)
    json.dumps(payload, sort_keys=True)


def test_post_resolution_learning_thresholds_and_custom_config_are_validated() -> None:
    module = api()
    custom = config(
        watch_min_learning_priority_score=d("0.400000"),
        block_min_learning_priority_score=d("0.600000"),
        watch_min_review_backlog_count=d("2"),
        block_min_review_backlog_count=d("5"),
    )
    report = build_report(
        learning_input(
            "custom_watch",
            "threshold_review",
            settled_outcome_signal_strength=d("0.500000"),
            forecast_miss_severity=d("0.300000"),
            source_evidence_gap=d("0.200000"),
            calibration_freshness_score=d("0.500000"),
            review_backlog_count=d("1"),
        ),
        learning_input(
            "custom_block",
            "threshold_review",
            settled_outcome_signal_strength=d("0.850000"),
            forecast_miss_severity=d("0.600000"),
            source_evidence_gap=d("0.500000"),
            calibration_freshness_score=d("0.350000"),
            review_backlog_count=d("5"),
        ),
        cfg=custom,
    )

    assert tuple(row.status for row in report.rows) == ("block", "watch")
    assert report.rows[0].learning_priority_score == d("0.697500")
    assert report.rows[1].learning_priority_score == d("0.335000")

    with pytest.raises(ValueError, match="Decimal"):
        module.ResearchStrategyPostResolutionLearningPriorityConfig(
            settled_outcome_signal_weight=0.2,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="watch priority threshold"):
        config(
            watch_min_learning_priority_score=d("0.800000"),
            block_min_learning_priority_score=d("0.700000"),
        )
    with pytest.raises(ValueError, match="calibration freshness"):
        config(
            watch_max_calibration_freshness_score=d("0.300000"),
            block_max_calibration_freshness_score=d("0.400000"),
        )
    with pytest.raises(ValueError, match="review backlog"):
        config(
            watch_min_review_backlog_count=d("8"),
            block_min_review_backlog_count=d("8"),
        )
    with pytest.raises(ValueError, match="weights"):
        config(settled_outcome_signal_weight=d("0.300000"))


def test_digest_is_deterministic_and_rejects_tampering() -> None:
    module = api()
    rows = (
        learning_input("rates_research", "inflation_resolution_review"),
        learning_input(
            "crypto_research",
            "protocol_resolution_review",
            settled_outcome_signal_strength=d("0.900000"),
            forecast_miss_severity=d("0.700000"),
            source_evidence_gap=d("0.600000"),
            calibration_freshness_score=d("0.200000"),
            review_backlog_count=d("9"),
        ),
    )
    first = build_report(*rows)
    second = build_report(*reversed(rows))

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.public_payload == second.public_payload
    assert first.public_payload["derived_validation_digest"] == canonical_digest(
        first.public_payload,
    )

    tampered = build_report(*rows)
    object.__setattr__(tampered, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_post_resolution_learning_priority_report_public_payload(
            tampered,
        )

    unsigned = dict(first.public_payload)
    unsigned["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_strategy_post_resolution_learning_priority_public_payload(
            unsigned,
        )


def test_public_payload_prevents_leaks_and_module_exposes_no_live_surfaces() -> None:
    module = api()
    report = build_report(learning_input())

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        module.ResearchStrategyPostResolutionLearningPriorityConfig(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        learning_input(forecast_miss_severity=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsafe public"):
        learning_input(analyst_label="candidate_id abc")
    with pytest.raises(ValueError, match="unsafe public"):
        learning_input(learning_scope_label="market_slug question source_url")
    with pytest.raises(ValueError, match="timezone-aware"):
        module.build_research_strategy_post_resolution_learning_priority_report(
            (learning_input(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )

    for item in (config(), learning_input(), report, *report.rows):
        assert is_dataclass(item)
        assert item.__dataclass_params__.frozen
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                assert value is True
            elif isinstance(value, Decimal):
                assert type(value) is Decimal

    payload = report.public_payload
    assert_payload_has_no_raw_numbers(payload)
    assert_payload_has_no_forbidden_surface(payload)

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")

    forbidden_imports = {
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "py_clob_client",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    for public_name in module.__all__:
        assert_payload_has_no_forbidden_surface({"name": public_name})
    for cls in (
        module.ResearchStrategyPostResolutionLearningPriorityConfig,
        module.ResearchStrategyPostResolutionLearningPriorityInput,
        module.ResearchStrategyPostResolutionLearningPriorityRow,
        module.ResearchStrategyPostResolutionLearningPriorityReport,
    ):
        for field in fields(cls):
            assert_payload_has_no_forbidden_surface({"field": field.name})
