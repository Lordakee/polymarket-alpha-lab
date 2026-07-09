from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_cross_domain_edge_quality_gate_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_cross_domain_edge_quality_gate_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 30, tzinfo=UTC)
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
    assert spec is not None, "cross-domain edge quality gate report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_QUALITY_GATE_REPORT_CONFIG_VERSION
        ),
        "pass_min_quality_score": d("0.800000"),
        "watch_min_quality_score": d("0.600000"),
        "min_pass_dimension_score": d("0.750000"),
        "min_watch_dimension_score": d("0.500000"),
        "max_pass_cost_drag_score": d("0.200000"),
        "max_watch_cost_drag_score": d("0.450000"),
        "domain_signal_weight": d("0.170000"),
        "evidence_quality_weight": d("0.180000"),
        "source_independence_weight": d("0.150000"),
        "probability_edge_weight": d("0.170000"),
        "liquidity_quality_weight": d("0.130000"),
        "resolution_clarity_weight": d("0.110000"),
        "cost_efficiency_weight": d("0.090000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCrossDomainEdgeQualityGateConfig(**values)


def _input(
    module: Any,
    edge_item_ref: str = "cross-domain-edge-alpha",
    **overrides: object,
) -> Any:
    values = {
        "edge_item_ref": edge_item_ref,
        "domain_signal_score": d("0.900000"),
        "evidence_quality_score": d("0.920000"),
        "source_independence_score": d("0.880000"),
        "probability_edge_score": d("0.860000"),
        "liquidity_quality_score": d("0.850000"),
        "resolution_clarity_score": d("0.900000"),
        "cost_drag_score": d("0.100000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("cross_domain_review_ready",),
    }
    values.update(overrides)
    return module.ResearchStrategyCrossDomainEdgeQualityGateInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_cross_domain_edge_quality_gate_report(
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


def _resign_payload(payload: dict[str, object]) -> dict[str, object]:
    unsigned = json.loads(json.dumps(payload, sort_keys=True))
    unsigned["derived_validation_digest"] = ""
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    unsigned["derived_validation_digest"] = sha256(encoded.encode("utf-8")).hexdigest()
    return unsigned


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
        if field.name.endswith(("_count", "_score", "_weight", "_ratio")):
            assert type(item) is Decimal


def test_builds_pass_watch_and_block_quality_gate_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "candidate=abc&market_slug=hidden-question&token=secret&wallet=0xabc",
                reason_codes=("cross_domain_review_ready",),
            ),
            _input(
                module,
                "quality-watch",
                domain_signal_score=d("0.700000"),
                evidence_quality_score=d("0.720000"),
                source_independence_score=d("0.660000"),
                probability_edge_score=d("0.680000"),
                liquidity_quality_score=d("0.670000"),
                resolution_clarity_score=d("0.650000"),
                cost_drag_score=d("0.350000"),
                reason_codes=(
                    "domain_disagreement_observed",
                    "manual_review_requested",
                ),
            ),
            _input(
                module,
                "quality-block",
                domain_signal_score=d("0.450000"),
                evidence_quality_score=d("0.500000"),
                source_independence_score=d("0.400000"),
                probability_edge_score=d("0.480000"),
                liquidity_quality_score=d("0.450000"),
                resolution_clarity_score=d("0.550000"),
                cost_drag_score=d("0.700000"),
                reason_codes=(
                    "manual_review_requested",
                    "source_independence_review_requested",
                ),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyCrossDomainEdgeQualityGateReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_quality_score == d("0.673900")
    assert report.min_quality_score == d("0.454100")
    assert report.min_domain_signal_score == d("0.450000")
    assert report.min_evidence_quality_score == d("0.500000")
    assert report.min_source_independence_score == d("0.400000")
    assert report.min_probability_edge_score == d("0.480000")
    assert report.min_liquidity_quality_score == d("0.450000")
    assert report.min_resolution_clarity_score == d("0.550000")
    assert report.max_cost_drag_score == d("0.700000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategyCrossDomainEdgeQualityGateRow
    assert blocked.cost_efficiency_score == d("0.300000")
    assert blocked.quality_score == d("0.454100")
    assert blocked.lowest_dimension_score == d("0.300000")
    assert blocked.reason_codes == (
        "source_independence_review_requested",
        "manual_review_requested",
        "domain_signal_quality_block",
        "evidence_quality_watch",
        "source_independence_block",
        "probability_edge_block",
        "liquidity_quality_block",
        "resolution_clarity_watch",
        "cost_drag_block",
        "quality_score_block",
    )

    watched = report.rows[1]
    assert watched.cost_efficiency_score == d("0.650000")
    assert watched.quality_score == d("0.680300")
    assert watched.reason_codes == (
        "domain_disagreement_observed",
        "manual_review_requested",
        "domain_signal_quality_watch",
        "evidence_quality_watch",
        "source_independence_watch",
        "probability_edge_watch",
        "liquidity_quality_watch",
        "resolution_clarity_watch",
        "cost_drag_watch",
        "quality_score_watch",
    )

    passed = report.rows[2]
    assert passed.cost_efficiency_score == d("0.900000")
    assert passed.quality_score == d("0.887300")
    assert passed.reason_codes == (
        "cross_domain_review_ready",
        "cross_domain_edge_quality_gate_pass",
    )

    reason_count_by_code = {
        item.reason_code: item for item in report.reason_code_counts
    }
    assert reason_count_by_code["manual_review_requested"] == (
        module.ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount(
            reason_code="manual_review_requested",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
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
    assert report.average_quality_score == ZERO
    assert report.min_quality_score == ZERO
    assert report.min_domain_signal_score == ZERO
    assert report.min_evidence_quality_score == ZERO
    assert report.min_source_independence_score == ZERO
    assert report.min_probability_edge_score == ZERO
    assert report.min_liquidity_quality_score == ZERO
    assert report.min_resolution_clarity_score == ZERO
    assert report.max_cost_drag_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )


def test_payload_hashes_private_refs_and_serializes_decimal_strings() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "candidate=abc&market_slug=hidden-question&token=secret&wallet=0xabc",
            ),
        ),
    )

    payload = module.research_strategy_cross_domain_edge_quality_gate_report_payload(
        report,
    )
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["quality_score"] == "0.887300"
    assert payload["rows"][0]["edge_item_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "candidate=abc",
        "market_slug",
        "hidden-question",
        "token",
        "secret",
        "wallet",
        "0xabc",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(report)).casefold()


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    module = _module()

    assert is_dataclass(module.ResearchStrategyCrossDomainEdgeQualityGateConfig)
    assert is_dataclass(module.ResearchStrategyCrossDomainEdgeQualityGateInput)
    assert is_dataclass(module.ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyCrossDomainEdgeQualityGateRow)
    assert is_dataclass(module.ResearchStrategyCrossDomainEdgeQualityGateReport)

    cfg = _config(module)
    source_row = _input(module)
    report = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.cost_drag_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].quality_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_QUALITY_GATE_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_quality_score"):
        _config(module, pass_min_quality_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_quality_score"):
        _config(module, watch_min_quality_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="weights"):
        _config(module, cost_efficiency_weight=d("0.100000"))
    with pytest.raises(ValueError, match="edge_item_ref"):
        _input(module, _StringSubclass("cross-domain-alpha"))
    with pytest.raises(ValueError, match="edge_item_ref"):
        _input(module, " ")
    with pytest.raises(ValueError, match="domain_signal_score"):
        _input(module, domain_signal_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality_score"):
        _input(module, evidence_quality_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_independence_score"):
        _input(module, source_independence_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 9, 11, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        _report(module, (), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="config"):
        _report(module, (), cfg=object())
    with pytest.raises(ValueError, match="inputs"):
        _report(module, (object(),))
    with pytest.raises(ValueError, match="observed_at"):
        _report(
            module,
            (_input(module, observed_at=datetime(2026, 7, 9, 12, 1, tzinfo=UTC)),),
        )


def test_public_payload_rejects_forbidden_fields_values_statuses_and_digest_drift() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_cross_domain_edge_quality_gate_report_payload(
        report,
    )
    rendered = repr(payload).casefold()

    for token in (
        "candidate",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "sizing",
        "buy",
        "sell",
        "recommend",
        "live",
        "blocked",
    ):
        assert token not in rendered

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_cross_domain_edge_quality_gate_report_payload(
            tampered_status,
        )

    tampered_field = dict(payload)
    tampered_field["market_id"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_cross_domain_edge_quality_gate_report_payload(
            tampered_field,
        )

    tampered_value = dict(payload)
    tampered_value["reason_codes"] = ["source_text_copied_from_url"]
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_cross_domain_edge_quality_gate_report_payload(
            tampered_value,
        )

    tampered_digest = dict(payload)
    tampered_digest["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_cross_domain_edge_quality_gate_report_payload(
            tampered_digest,
        )


def test_public_payload_rejects_resigned_missing_or_false_phase_flags() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_cross_domain_edge_quality_gate_report_payload(
        report,
    )

    false_root_flag = _resign_payload({**payload, "paper_only": False})
    with pytest.raises(ValueError, match="paper_only"):
        module.research_strategy_cross_domain_edge_quality_gate_report_payload(
            false_root_flag,
        )

    missing_row_flag = json.loads(json.dumps(payload, sort_keys=True))
    missing_row_flag["rows"][0].pop("readonly")
    missing_row_flag = _resign_payload(missing_row_flag)
    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_cross_domain_edge_quality_gate_report_payload(
            missing_row_flag,
        )

    false_reason_count_flag = json.loads(json.dumps(payload, sort_keys=True))
    false_reason_count_flag["reason_code_counts"][0]["report_only"] = False
    false_reason_count_flag = _resign_payload(false_reason_count_flag)
    with pytest.raises(ValueError, match="report_only"):
        module.research_strategy_cross_domain_edge_quality_gate_report_payload(
            false_reason_count_flag,
        )


def test_hard_flags_and_manual_drift_are_rejected() -> None:
    module = _module()

    with pytest.raises(ValueError, match="paper_only"):
        _config(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _config(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        _config(module, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        _input(module, paper_only=False)

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
        replace(
            passed,
            reason_codes=(
                "cross_domain_edge_quality_gate_pass",
                "quality_score_watch",
            ),
        )
    with pytest.raises(ValueError, match="quality_score"):
        replace(passed, quality_score=ZERO, validation_config=_config(module))
    with pytest.raises(ValueError, match="edge_item_digest"):
        replace(passed, edge_item_digest="candidate-market")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_order() -> None:
    module = _module()
    rows = (
        _input(module, "quality-c", cost_drag_score=d("0.700000")),
        _input(module, "quality-a"),
        _input(module, "quality-b", evidence_quality_score=d("0.700000")),
    )

    report_a = _report(module, rows)
    report_b = _report(module, tuple(reversed(rows)))

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_cross_domain_edge_quality_gate_report_digest(
        report_a,
    ) == report_a.derived_validation_digest
    assert module.research_strategy_cross_domain_edge_quality_gate_report_payload(
        report_a,
    ) == module.research_strategy_cross_domain_edge_quality_gate_report_payload(
        report_b,
    )


def test_public_numeric_fields_are_decimals() -> None:
    module = _module()
    source_row = _input(module)
    report = _report(module, (source_row,))

    _assert_decimal_numeric_fields(source_row)
    _assert_decimal_numeric_fields(report)
    _assert_decimal_numeric_fields(report.rows[0])
    _assert_decimal_numeric_fields(report.reason_code_counts[0])


def test_module_scope_is_read_only_report_only_and_public_api_is_narrow() -> None:
    module = _module()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_QUALITY_GATE_REPORT_CONFIG_VERSION",
        "ResearchStrategyCrossDomainEdgeQualityGateConfig",
        "ResearchStrategyCrossDomainEdgeQualityGateInput",
        "ResearchStrategyCrossDomainEdgeQualityGateReasonCodeCount",
        "ResearchStrategyCrossDomainEdgeQualityGateReport",
        "ResearchStrategyCrossDomainEdgeQualityGateRow",
        "build_research_strategy_cross_domain_edge_quality_gate_report",
        "research_strategy_cross_domain_edge_quality_gate_report_digest",
        "research_strategy_cross_domain_edge_quality_gate_report_payload",
    )

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
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
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

    lowered = source.lower()
    for forbidden in (
        "place_order",
        "execute_trade",
        "position_size",
        "private_key",
        "database_url",
    ):
        assert forbidden not in lowered
