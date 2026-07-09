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
    "polymarket_alpha_lab."
    "research_strategy_market_memory_confidence_guard_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_market_memory_confidence_guard_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 45, tzinfo=UTC)
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
    assert spec is not None, "market memory confidence guard report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_MARKET_MEMORY_CONFIDENCE_GUARD_CONFIG_VERSION
        ),
        "pass_min_guard_score": d("0.800000"),
        "watch_min_guard_score": d("0.600000"),
        "min_pass_support_score": d("0.700000"),
        "min_watch_support_score": d("0.500000"),
        "max_pass_risk_score": d("0.200000"),
        "max_watch_risk_score": d("0.450000"),
        "memory_confidence_weight": d("0.250000"),
        "evidence_recheck_weight": d("0.200000"),
        "cross_evidence_consistency_weight": d("0.200000"),
        "outcome_feedback_weight": d("0.150000"),
        "freshness_support_weight": d("0.100000"),
        "conflict_safety_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyMarketMemoryConfidenceGuardConfig(**values)


def _input(
    module: Any,
    private_memory_ref: str = (
        "candidate=alpha&market=hidden-question&source_url=https://example.test/a"
        "&source_text=private-summary&DSN=postgres://private/table&token=secret"
    ),
    **overrides: object,
) -> Any:
    values = {
        "private_memory_ref": private_memory_ref,
        "memory_confidence_score": d("0.900000"),
        "evidence_recheck_confidence_score": d("0.900000"),
        "cross_evidence_consistency_score": d("0.880000"),
        "outcome_feedback_confidence_score": d("0.850000"),
        "staleness_risk_score": d("0.100000"),
        "conflict_risk_score": d("0.080000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("memory_review_ready",),
    }
    values.update(overrides)
    return module.ResearchStrategyMarketMemoryConfidenceGuardInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_market_memory_confidence_guard_report(
        rows,
        generated_at=generated_at,
        config=cfg or _config(module),
    )


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        nested: list[object] = []
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
        if field.name.endswith(("_count", "_score", "_weight", "_ratio")):
            assert type(item) is Decimal


def test_builds_pass_watch_and_block_memory_confidence_guard_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                (
                    "candidate=abc&market_slug=hidden-question&source_url="
                    "https://example.test/private&token=secret&wallet=0xabc"
                ),
            ),
            _input(
                module,
                "memory-watch",
                cross_evidence_consistency_score=d("0.650000"),
                staleness_risk_score=d("0.300000"),
                conflict_risk_score=d("0.350000"),
                reason_codes=("manual_review_requested",),
            ),
            _input(
                module,
                "memory-block",
                memory_confidence_score=d("0.400000"),
                evidence_recheck_confidence_score=d("0.480000"),
                cross_evidence_consistency_score=d("0.550000"),
                outcome_feedback_confidence_score=d("0.500000"),
                staleness_risk_score=d("0.700000"),
                conflict_risk_score=d("0.600000"),
                reason_codes=(
                    "manual_review_requested",
                    "staleness_review_requested",
                    "conflict_review_requested",
                ),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyMarketMemoryConfidenceGuardReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_MARKET_MEMORY_CONFIDENCE_GUARD_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_guard_score == d("0.713000")
    assert report.min_guard_score == d("0.451000")
    assert report.min_memory_confidence_score == d("0.400000")
    assert report.min_evidence_recheck_confidence_score == d("0.480000")
    assert report.min_cross_evidence_consistency_score == d("0.550000")
    assert report.min_outcome_feedback_confidence_score == d("0.500000")
    assert report.max_staleness_risk_score == d("0.700000")
    assert report.max_conflict_risk_score == d("0.600000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategyMarketMemoryConfidenceGuardRow
    assert blocked.memory_item_digest.startswith("sha256:")
    assert blocked.freshness_support_score == d("0.300000")
    assert blocked.conflict_safety_score == d("0.400000")
    assert blocked.guard_score == d("0.451000")
    assert blocked.lowest_support_score == d("0.300000")
    assert blocked.reason_codes == (
        "manual_review_requested",
        "staleness_review_requested",
        "conflict_review_requested",
        "memory_confidence_block",
        "evidence_recheck_confidence_block",
        "cross_evidence_consistency_watch",
        "outcome_feedback_confidence_watch",
        "freshness_support_block",
        "conflict_safety_block",
        "staleness_risk_block",
        "conflict_risk_block",
        "guard_score_block",
    )

    watched = report.rows[1]
    assert watched.freshness_support_score == d("0.700000")
    assert watched.conflict_safety_score == d("0.650000")
    assert watched.guard_score == d("0.797500")
    assert watched.reason_codes == (
        "manual_review_requested",
        "cross_evidence_consistency_watch",
        "conflict_safety_watch",
        "staleness_risk_watch",
        "conflict_risk_watch",
        "guard_score_watch",
    )

    passed = report.rows[2]
    assert passed.guard_score == d("0.890500")
    assert passed.reason_codes == (
        "memory_review_ready",
        "memory_confidence_guard_pass",
    )


def test_empty_report_is_report_only_block() -> None:
    module = _module()
    report = _report(module, ())

    assert report.status == "block"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_guard_score == ZERO
    assert report.min_guard_score == ZERO
    assert report.min_memory_confidence_score == ZERO
    assert report.min_evidence_recheck_confidence_score == ZERO
    assert report.min_cross_evidence_consistency_score == ZERO
    assert report.min_outcome_feedback_confidence_score == ZERO
    assert report.max_staleness_risk_score == ZERO
    assert report.max_conflict_risk_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_hashes_private_refs_and_serializes_decimal_strings() -> None:
    module = _module()
    report = _report(module, (_input(module),))

    payload = module.research_strategy_market_memory_confidence_guard_report_payload(
        report,
    )
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["guard_score"] == "0.890500"
    assert payload["rows"][0]["memory_item_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "candidate=alpha",
        "hidden-question",
        "source_url",
        "source_text",
        "postgres://",
        "table",
        "token",
        "secret",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(report)).casefold()


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    module = _module()

    assert is_dataclass(module.ResearchStrategyMarketMemoryConfidenceGuardConfig)
    assert is_dataclass(module.ResearchStrategyMarketMemoryConfidenceGuardInput)
    assert is_dataclass(module.ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyMarketMemoryConfidenceGuardRow)
    assert is_dataclass(module.ResearchStrategyMarketMemoryConfidenceGuardReport)

    cfg = _config(module)
    source_row = _input(module)
    report = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.memory_confidence_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].guard_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_MARKET_MEMORY_CONFIDENCE_GUARD_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_guard_score"):
        _config(module, pass_min_guard_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_guard_score"):
        _config(module, watch_min_guard_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_min_guard_score"):
        _config(module, pass_min_guard_score=d("0.500000"))
    with pytest.raises(ValueError, match="max_pass_risk_score"):
        _config(module, max_pass_risk_score=d("0.600000"))
    with pytest.raises(ValueError, match="weights"):
        _config(module, evidence_recheck_weight=d("0.210000"))
    with pytest.raises(ValueError, match="private_memory_ref"):
        _input(module, _StringSubclass("memory-alpha"))
    with pytest.raises(ValueError, match="private_memory_ref"):
        _input(module, " ")
    with pytest.raises(ValueError, match="memory_confidence_score"):
        _input(module, memory_confidence_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_recheck_confidence_score"):
        _input(module, evidence_recheck_confidence_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cross_evidence_consistency_score"):
        _input(module, cross_evidence_consistency_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 9, 11, 45, tzinfo=UTC))
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


def test_public_payload_rejects_forbidden_fields_values_and_statuses() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_market_memory_confidence_guard_report_payload(
        report,
    )
    rendered = repr(payload).casefold()

    for token in (
        "candidate=alpha",
        "market_slug",
        "hidden-question",
        "source_url",
        "source_text",
        "dsn",
        "postgres://",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "size",
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
        module.research_strategy_market_memory_confidence_guard_report_payload(
            tampered_status,
        )

    tampered_field = dict(payload)
    tampered_field["candidate_ref"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_market_memory_confidence_guard_report_payload(
            tampered_field,
        )

    tampered_value = dict(payload)
    tampered_value["reason_codes"] = ["source_text_copied_from_url"]
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_market_memory_confidence_guard_report_payload(
            tampered_value,
        )


def test_hard_flags_are_enforced() -> None:
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
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.reason_code_counts[0], readonly=False)


def test_manual_report_and_row_drift_rejected() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    passed = report.rows[0]

    with pytest.raises(ValueError, match="status"):
        replace(passed, status="watch")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            passed,
            reason_codes=(
                "memory_confidence_guard_pass",
                "guard_score_watch",
            ),
        )
    with pytest.raises(ValueError, match="guard_score"):
        replace(passed, guard_score=ZERO, validation_config=_config(module))
    with pytest.raises(ValueError, match="memory_item_digest"):
        replace(passed, memory_item_digest="candidate-market")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = _report(
            module,
            (
                _input(module, "memory-z", staleness_risk_score=d("0.700000")),
                _input(module, "memory-a"),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_order() -> None:
    module = _module()
    rows = (
        _input(module, "memory-c", staleness_risk_score=d("0.700000")),
        _input(module, "memory-a"),
        _input(module, "memory-b", cross_evidence_consistency_score=d("0.650000")),
    )

    report_a = _report(module, rows)
    report_b = _report(module, tuple(reversed(rows)))

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_market_memory_confidence_guard_report_digest(
        report_a,
    ) == report_a.derived_validation_digest
    assert module.research_strategy_market_memory_confidence_guard_report_payload(
        report_a,
    ) == module.research_strategy_market_memory_confidence_guard_report_payload(
        report_b,
    )

    tampered = module.research_strategy_market_memory_confidence_guard_report_payload(
        report_a,
    )
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_market_memory_confidence_guard_report_payload(tampered)


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
        "DEFAULT_RESEARCH_STRATEGY_MARKET_MEMORY_CONFIDENCE_GUARD_CONFIG_VERSION",
        "ResearchStrategyMarketMemoryConfidenceGuardConfig",
        "ResearchStrategyMarketMemoryConfidenceGuardInput",
        "ResearchStrategyMarketMemoryConfidenceGuardReasonCodeCount",
        "ResearchStrategyMarketMemoryConfidenceGuardReport",
        "ResearchStrategyMarketMemoryConfidenceGuardRow",
        "build_research_strategy_market_memory_confidence_guard_report",
        "research_strategy_market_memory_confidence_guard_report_digest",
        "research_strategy_market_memory_confidence_guard_report_payload",
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
