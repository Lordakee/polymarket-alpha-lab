from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_probability_edge_explainability_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_probability_edge_explainability_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 15, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "probability edge explainability report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION
        ),
        "pass_min_explainability_score": d("0.800000"),
        "watch_min_explainability_score": d("0.600000"),
        "min_pass_evidence_quality_score": d("0.750000"),
        "min_watch_evidence_quality_score": d("0.500000"),
        "min_pass_model_confidence_score": d("0.750000"),
        "min_watch_model_confidence_score": d("0.500000"),
        "min_pass_market_divergence_score": d("0.700000"),
        "min_watch_market_divergence_score": d("0.450000"),
        "max_pass_cost_drag_score": d("0.150000"),
        "max_watch_cost_drag_score": d("0.350000"),
        "min_pass_liquidity_quality_score": d("0.750000"),
        "min_watch_liquidity_quality_score": d("0.500000"),
        "min_pass_resolution_clarity_score": d("0.750000"),
        "min_watch_resolution_clarity_score": d("0.500000"),
        "evidence_quality_weight": d("0.250000"),
        "model_confidence_weight": d("0.200000"),
        "market_divergence_weight": d("0.200000"),
        "cost_drag_quality_weight": d("0.150000"),
        "liquidity_quality_weight": d("0.100000"),
        "resolution_clarity_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyProbabilityEdgeExplainabilityConfig(**values)


def _input(
    module: Any,
    edge_ref: str = "raw-candidate-alpha/market-slug?token=hidden&wallet=private",
    **overrides: object,
) -> Any:
    values = {
        "edge_ref": edge_ref,
        "evidence_quality_score": d("0.950000"),
        "model_confidence_score": d("0.900000"),
        "market_divergence_score": d("0.850000"),
        "cost_drag_score": d("0.080000"),
        "liquidity_quality_score": d("0.820000"),
        "resolution_clarity_score": d("0.880000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return module.ResearchStrategyProbabilityEdgeExplainabilityInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_probability_edge_explainability_report(
        rows,
        generated_at=generated_at,
        config=cfg or _config(module),
    )


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(_walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(_walk_values(item))
        return tuple(nested)
    return (value,)


def _assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_score", "_ratio", "_weight")):
            assert type(item) is Decimal


def test_builds_pass_watch_and_block_explainability_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate-block/market-slug?source_url=https://example.test",
                evidence_quality_score=d("0.450000"),
                model_confidence_score=d("0.400000"),
                market_divergence_score=d("0.300000"),
                cost_drag_score=d("0.700000"),
                liquidity_quality_score=d("0.350000"),
                resolution_clarity_score=d("0.420000"),
            ),
            _input(
                module,
                "edge-watch",
                evidence_quality_score=d("0.700000"),
                model_confidence_score=d("0.650000"),
                market_divergence_score=d("0.600000"),
                cost_drag_score=d("0.250000"),
                liquidity_quality_score=d("0.650000"),
                resolution_clarity_score=d("0.700000"),
            ),
            _input(module, "edge-pass"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyProbabilityEdgeExplainabilityReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_explainability_score == d("0.647500")
    assert report.min_explainability_score == d("0.374500")
    assert report.min_evidence_quality_score == d("0.450000")
    assert report.min_model_confidence_score == d("0.400000")
    assert report.min_market_divergence_score == d("0.300000")
    assert report.max_cost_drag_score == d("0.700000")
    assert report.min_liquidity_quality_score == d("0.350000")
    assert report.min_resolution_clarity_score == d("0.420000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategyProbabilityEdgeExplainabilityRow
    assert blocked.cost_drag_quality_score == d("0.300000")
    assert blocked.explainability_score == d("0.374500")
    assert blocked.reason_codes == (
        "evidence_quality_block",
        "model_confidence_block",
        "market_divergence_block",
        "cost_drag_block",
        "liquidity_quality_block",
        "resolution_clarity_block",
        "explainability_score_block",
    )

    watched = report.rows[1]
    assert watched.cost_drag_quality_score == d("0.750000")
    assert watched.explainability_score == d("0.672500")
    assert watched.reason_codes == (
        "evidence_quality_watch",
        "model_confidence_watch",
        "market_divergence_watch",
        "cost_drag_watch",
        "liquidity_quality_watch",
        "resolution_clarity_watch",
        "explainability_score_watch",
    )

    passed = report.rows[2]
    assert passed.explainability_score == d("0.895500")
    assert passed.reason_codes == ("probability_edge_explainability_pass",)

    assert report.reason_code_counts[0] == (
        module.ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount(
            reason_code="cost_drag_block",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
    )


def test_empty_report_is_report_only_block() -> None:
    module = _module()
    report = _report(module, ())

    assert report.status == "block"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_explainability_score == ZERO
    assert report.min_explainability_score == ZERO
    assert report.min_evidence_quality_score == ZERO
    assert report.min_model_confidence_score == ZERO
    assert report.min_market_divergence_score == ZERO
    assert report.max_cost_drag_score == ZERO
    assert report.min_liquidity_quality_score == ZERO
    assert report.min_resolution_clarity_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_redacts_private_refs_and_serializes_decimal_strings() -> None:
    module = _module()
    report = _report(module, (_input(module),))

    payload = module.research_strategy_probability_edge_explainability_report_payload(
        report,
    )
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["explainability_score"] == "0.895500"
    assert payload["rows"][0]["edge_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(type(value) is Decimal for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "raw-candidate-alpha",
        "market-slug",
        "candidate",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "token",
        "hidden",
        "wallet",
        "private",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "dsn",
        "table",
    ):
        assert leaked not in rendered


def test_payload_digest_validation_rejects_tampering_and_unsafe_surfaces() -> None:
    module = _module()
    payload = module.research_strategy_probability_edge_explainability_report_payload(
        _report(module, (_input(module),)),
    )
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest")
    expected_digest = __import__("hashlib").sha256(
        json.dumps(
            digest_input,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()
    assert payload["derived_validation_digest"] == expected_digest

    tampered = dict(payload)
    tampered["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_probability_edge_explainability_report_payload(tampered)

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0])]
    tampered_row["rows"][0]["edge_digest"] = "raw-candidate-market"
    with pytest.raises(ValueError, match="unsafe public value|derived_validation_digest"):
        module.research_strategy_probability_edge_explainability_report_payload(
            tampered_row,
        )

    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_probability_edge_explainability_report_payload(
            {
                "market_slug": "hidden",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
            },
        )


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    module = _module()

    assert is_dataclass(module.ResearchStrategyProbabilityEdgeExplainabilityConfig)
    assert is_dataclass(module.ResearchStrategyProbabilityEdgeExplainabilityInput)
    assert is_dataclass(module.ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyProbabilityEdgeExplainabilityReport)
    assert is_dataclass(module.ResearchStrategyProbabilityEdgeExplainabilityRow)

    cfg = _config(module)
    source_row = _input(module)
    report = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.cost_drag_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].explainability_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_explainability_score"):
        _config(module, pass_min_explainability_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_explainability_score"):
        _config(module, watch_min_explainability_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_min_explainability_score"):
        _config(module, pass_min_explainability_score=d("0.500000"))
    with pytest.raises(ValueError, match="max_pass_cost_drag_score"):
        _config(module, max_pass_cost_drag_score=d("0.500000"))
    with pytest.raises(ValueError, match="explainability weights"):
        _config(module, evidence_quality_weight=d("0.300000"))
    with pytest.raises(ValueError, match="edge_ref"):
        _input(module, _StringSubclass("edge-alpha"))
    with pytest.raises(ValueError, match="edge_ref"):
        _input(module, " ")
    with pytest.raises(ValueError, match="evidence_quality_score"):
        _input(module, evidence_quality_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="model_confidence_score"):
        _input(module, model_confidence_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="market_divergence_score"):
        _input(module, market_divergence_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 8, 15, 45, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        _report(module, (), generated_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="config"):
        _report(module, (), cfg=object())
    with pytest.raises(ValueError, match="inputs"):
        _report(module, (object(),))
    with pytest.raises(ValueError, match="observed_at"):
        _report(
            module,
            (
                _input(
                    module,
                    observed_at=datetime(2026, 7, 8, 16, 1, tzinfo=UTC),
                ),
            ),
        )
    with pytest.raises(ValueError, match="duplicate"):
        _report(module, (_input(module, "same-edge"), _input(module, "same-edge")))


def test_hard_flags_and_manual_drift_are_rejected() -> None:
    module = _module()

    with pytest.raises(ValueError, match="paper_only"):
        _config(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _config(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _input(module, readonly=False)

    report = _report(module, (_input(module),))
    passed = report.rows[0]

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(passed, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(passed, status="watch")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(passed, reason_codes=("probability_edge_explainability_pass", "cost_drag_watch"))
    with pytest.raises(ValueError, match="explainability_score"):
        replace(passed, explainability_score=ZERO, validation_config=_config(module))
    with pytest.raises(ValueError, match="edge_digest"):
        replace(passed, edge_digest="raw-candidate-market")
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_order() -> None:
    module = _module()
    rows = (
        _input(module, "edge-c", cost_drag_score=d("0.700000")),
        _input(module, "edge-a"),
        _input(module, "edge-b", evidence_quality_score=d("0.700000")),
    )

    report_a = _report(module, rows)
    report_b = _report(module, tuple(reversed(rows)))

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_probability_edge_explainability_report_payload(
        report_a,
    ) == module.research_strategy_probability_edge_explainability_report_payload(
        report_b,
    )


def test_public_numeric_fields_are_decimals_and_api_is_narrow() -> None:
    module = _module()
    source_row = _input(module)
    report = _report(module, (source_row,))

    assert module.RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_PROBABILITY_EDGE_EXPLAINABILITY_STATUSES",
        "ResearchStrategyProbabilityEdgeExplainabilityConfig",
        "ResearchStrategyProbabilityEdgeExplainabilityInput",
        "ResearchStrategyProbabilityEdgeExplainabilityReasonCodeCount",
        "ResearchStrategyProbabilityEdgeExplainabilityReport",
        "ResearchStrategyProbabilityEdgeExplainabilityRow",
        "build_research_strategy_probability_edge_explainability_report",
        "research_strategy_probability_edge_explainability_report_payload",
    )

    _assert_decimal_numeric_fields(_config(module))
    _assert_decimal_numeric_fields(source_row)
    _assert_decimal_numeric_fields(report)
    _assert_decimal_numeric_fields(report.rows[0])
    _assert_decimal_numeric_fields(report.reason_code_counts[0])

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
