from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_strategy_review_decision_blocker_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_review_decision_blocker_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 17, 30, tzinfo=UTC)
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
    assert spec is not None, "review decision blocker report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_REVIEW_DECISION_BLOCKER_CONFIG_VERSION
        ),
        "watch_blocker_pressure": d("0.250000"),
        "block_blocker_pressure": d("0.550000"),
        "watch_evidence_gap_score": d("0.250000"),
        "block_evidence_gap_score": d("0.600000"),
        "watch_source_conflict_score": d("0.250000"),
        "block_source_conflict_score": d("0.600000"),
        "watch_cost_drag_score": d("0.250000"),
        "block_cost_drag_score": d("0.600000"),
        "watch_liquidity_risk_score": d("0.250000"),
        "block_liquidity_risk_score": d("0.600000"),
        "watch_resolution_ambiguity_score": d("0.250000"),
        "block_resolution_ambiguity_score": d("0.600000"),
        "watch_memory_capacity_gap_score": d("0.250000"),
        "block_memory_capacity_gap_score": d("0.600000"),
        "evidence_gap_weight": d("0.200000"),
        "source_conflict_weight": d("0.200000"),
        "cost_drag_weight": d("0.150000"),
        "liquidity_risk_weight": d("0.150000"),
        "resolution_ambiguity_weight": d("0.150000"),
        "memory_capacity_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchStrategyReviewDecisionBlockerConfig(**values)


def _input(
    module: Any,
    review_item_ref: str = "review-item-alpha",
    **overrides: object,
) -> Any:
    values = {
        "review_item_ref": review_item_ref,
        "evidence_gap_score": d("0.050000"),
        "source_conflict_score": d("0.050000"),
        "cost_drag_score": d("0.050000"),
        "liquidity_risk_score": d("0.050000"),
        "resolution_ambiguity_score": d("0.050000"),
        "memory_capacity_gap_score": d("0.050000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("analyst_review_inputs_present",),
    }
    values.update(overrides)
    return module.ResearchStrategyReviewDecisionBlockerInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_review_decision_blocker_report(
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


def _assert_decimal_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_score", "_pressure", "_weight", "_ratio")):
            assert type(item) is Decimal


def test_builds_pass_watch_and_block_review_blocker_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate-id/market-slug?question=private&token=hidden",
                reason_codes=("analyst_review_inputs_present",),
            ),
            _input(
                module,
                "review-item-watch",
                evidence_gap_score=d("0.300000"),
                source_conflict_score=d("0.200000"),
                cost_drag_score=d("0.250000"),
                liquidity_risk_score=d("0.200000"),
                resolution_ambiguity_score=d("0.200000"),
                memory_capacity_gap_score=d("0.200000"),
                reason_codes=("manual_review_requested",),
            ),
            _input(
                module,
                "review-item-block",
                evidence_gap_score=d("0.700000"),
                source_conflict_score=d("0.650000"),
                cost_drag_score=d("0.800000"),
                liquidity_risk_score=d("0.850000"),
                resolution_ambiguity_score=d("0.750000"),
                memory_capacity_gap_score=d("0.700000"),
                reason_codes=(
                    "manual_review_requested",
                    "decision_memory_missing",
                ),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyReviewDecisionBlockerReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_blocker_pressure == d("0.337500")
    assert report.max_blocker_pressure == d("0.735000")
    assert report.max_evidence_gap_score == d("0.700000")
    assert report.max_source_conflict_score == d("0.650000")
    assert report.max_cost_drag_score == d("0.800000")
    assert report.max_liquidity_risk_score == d("0.850000")
    assert report.max_resolution_ambiguity_score == d("0.750000")
    assert report.max_memory_capacity_gap_score == d("0.700000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategyReviewDecisionBlockerRow
    assert blocked.blocker_pressure == d("0.735000")
    assert blocked.reason_codes == (
        "manual_review_requested",
        "decision_memory_missing",
        "evidence_gap_block",
        "source_conflict_block",
        "cost_drag_block",
        "liquidity_risk_block",
        "resolution_ambiguity_block",
        "memory_capacity_block",
        "blocker_pressure_block",
    )

    watched = report.rows[1]
    assert watched.blocker_pressure == d("0.227500")
    assert watched.reason_codes == (
        "manual_review_requested",
        "evidence_gap_watch",
        "cost_drag_watch",
    )

    passed = report.rows[2]
    assert passed.blocker_pressure == d("0.050000")
    assert passed.reason_codes == (
        "analyst_review_inputs_present",
        "analyst_review_ready_pass",
    )


def test_empty_report_blocks_because_review_cannot_move_forward() -> None:
    module = _module()
    report = _report(module, ())

    assert report.status == "block"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_blocker_pressure == ZERO
    assert report.max_blocker_pressure == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyReviewDecisionBlockerReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_is_public_safe_decimal_only_deterministic_and_digest_checked() -> None:
    module = _module()
    rows = (
        _input(module, "review-item-b", evidence_gap_score=d("0.300000")),
        _input(
            module,
            "raw-candidate-id/market-slug?question=hidden"
            "&source_url=https://example.test/path&token=secret&wallet=private"
            "&order=123&trade=456&table=positions",
            liquidity_risk_score=d("0.800000"),
        ),
        _input(module, "review-item-a"),
    )

    first = _report(module, rows)
    second = _report(module, tuple(reversed(rows)))
    payload = module.research_strategy_review_decision_blocker_report_payload(first)
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == first.payload
    assert payload == module.research_strategy_review_decision_blocker_report_payload(
        second,
    )
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert payload["row_count"] == "3.000000"
    assert payload["rows"][0]["review_item_digest"].startswith("sha256:")
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "raw-candidate-id",
        "market-slug",
        "question=hidden",
        "source_url",
        "https://example.test",
        "token",
        "secret",
        "wallet",
        "private",
        "order=123",
        "trade=456",
        "positions",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(first)).casefold()

    tampered = dict(payload)
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_review_decision_blocker_report_payload(tampered)


def test_validation_rejects_bad_types_flags_statuses_and_manual_drift() -> None:
    module = _module()

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_REVIEW_DECISION_BLOCKER_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="watch_blocker_pressure"):
        _config(module, watch_blocker_pressure=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_blocker_pressure"):
        _config(module, block_blocker_pressure=d("0.200000"))
    with pytest.raises(ValueError, match="weights"):
        _config(module, evidence_gap_weight=d("0.250000"))
    with pytest.raises(ValueError, match="review_item_ref"):
        _input(module, _StringSubclass("review-item-alpha"))
    with pytest.raises(ValueError, match="evidence_gap_score"):
        _input(module, evidence_gap_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="source_conflict_score"):
        _input(module, source_conflict_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_drag_score"):
        _input(module, cost_drag_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 8, 17, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        _report(module, (), generated_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="config"):
        _report(module, (), cfg=object())
    with pytest.raises(ValueError, match="inputs"):
        _report(module, (object(),))
    with pytest.raises(ValueError, match="observed_at"):
        _report(module, (_input(module, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="unique"):
        _report(module, (_input(module), _input(module)))

    report = _report(module, (_input(module),))
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].blocker_pressure = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="watch")
    with pytest.raises(ValueError, match="blocker_pressure"):
        replace(report.rows[0], blocker_pressure=d("0.900000"), validation_config=_config(module))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report.rows[0], reason_codes=("analyst_review_ready_pass", "cost_drag_watch"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_hard_flags_and_payload_status_contract_are_enforced() -> None:
    module = _module()

    with pytest.raises(ValueError, match="paper_only"):
        _config(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _input(module, report_only=False)

    report = _report(module, (_input(module),))
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report.reason_code_counts[0], paper_only=False)

    payload = module.research_strategy_review_decision_blocker_report_payload(report)
    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_review_decision_blocker_report_payload(tampered_status)

    tampered_field = dict(payload)
    tampered_field["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_review_decision_blocker_report_payload(tampered_field)


def test_public_numeric_fields_are_decimals() -> None:
    module = _module()
    source_row = _input(module)
    report = _report(module, (source_row,))

    _assert_decimal_fields(source_row)
    _assert_decimal_fields(report)
    _assert_decimal_fields(report.rows[0])
    _assert_decimal_fields(report.reason_code_counts[0])


def test_module_scope_is_report_only_and_public_api_is_narrow() -> None:
    module = _module()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_REVIEW_DECISION_BLOCKER_CONFIG_VERSION",
        "ResearchStrategyReviewDecisionBlockerConfig",
        "ResearchStrategyReviewDecisionBlockerInput",
        "ResearchStrategyReviewDecisionBlockerReasonCodeCount",
        "ResearchStrategyReviewDecisionBlockerReport",
        "ResearchStrategyReviewDecisionBlockerRow",
        "build_research_strategy_review_decision_blocker_report",
        "research_strategy_review_decision_blocker_report_payload",
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
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "read",
        "write",
        "write_bytes",
        "write_text",
        "__import__",
    }

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            for field in fields(exported):
                assert "candidate" not in field.name.casefold()
                assert "market_id" not in field.name.casefold()
                assert "slug" not in field.name.casefold()
                assert "question" not in field.name.casefold()
                assert "url" not in field.name.casefold()
                assert "text" not in field.name.casefold()
                assert "dsn" not in field.name.casefold()
                assert "table" not in field.name.casefold()
                assert "token" not in field.name.casefold()
                assert "wallet" not in field.name.casefold()
                assert "order" not in field.name.casefold()
                assert "trade" not in field.name.casefold()
                assert "sizing" not in field.name.casefold()
