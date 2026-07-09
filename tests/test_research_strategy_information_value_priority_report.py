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
    "research_strategy_information_value_priority_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_information_value_priority_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
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
    assert spec is not None, "information value priority report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_PRIORITY_REPORT_CONFIG_VERSION
        ),
        "priority_score_block_threshold": d("0.650000"),
        "priority_score_watch_threshold": d("0.450000"),
        "high_uncertainty_reduction_threshold": d("0.700000"),
        "stale_information_gap_threshold": d("0.700000"),
        "evidence_quality_gap_threshold": d("0.650000"),
        "liquidity_reliability_support_threshold": d("0.750000"),
        "cost_drag_constraint_threshold": d("0.600000"),
        "resolution_clarity_gap_threshold": d("0.650000"),
        "uncertainty_reduction_weight": d("0.300000"),
        "freshness_gap_weight": d("0.150000"),
        "evidence_quality_gap_weight": d("0.200000"),
        "liquidity_reliability_weight": d("0.150000"),
        "cost_efficiency_weight": d("0.100000"),
        "resolution_clarity_gap_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyInformationValuePriorityConfig(**values)


def _input(module: Any, research_item_ref: str = "research-item-alpha", **overrides: object) -> Any:
    values = {
        "research_item_ref": research_item_ref,
        "uncertainty_reduction_score": d("0.200000"),
        "freshness_score": d("0.900000"),
        "evidence_quality_score": d("0.850000"),
        "liquidity_reliability_score": d("0.800000"),
        "cost_drag_score": d("0.200000"),
        "resolution_clarity_score": d("0.800000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return module.ResearchStrategyInformationValuePriorityInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_information_value_priority_report(
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


def _without_validation_digests(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_validation_digests(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_without_validation_digests(item) for item in value]
    return value


def _public_digest(value: dict[str, Any]) -> str:
    return sha256(
        json.dumps(
            _without_validation_digests(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()


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


def test_builds_pass_watch_and_block_manual_research_priority_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate-id/market-slug?token=hidden&wallet=private&question=copy",
                uncertainty_reduction_score=d("0.850000"),
                freshness_score=d("0.200000"),
                evidence_quality_score=d("0.300000"),
                liquidity_reliability_score=d("0.900000"),
                cost_drag_score=d("0.100000"),
                resolution_clarity_score=d("0.200000"),
            ),
            _input(
                module,
                "research-item-watch",
                uncertainty_reduction_score=d("0.600000"),
                freshness_score=d("0.500000"),
                evidence_quality_score=d("0.600000"),
                liquidity_reliability_score=d("0.700000"),
                cost_drag_score=d("0.300000"),
                resolution_clarity_score=d("0.600000"),
            ),
            _input(module, "research-item-pass"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyInformationValuePriorityReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_PRIORITY_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_expected_information_value_score == d("0.565000")
    assert report.highest_expected_information_value_score == d("0.820000")
    assert report.average_uncertainty_reduction_score == d("0.550000")
    assert report.average_freshness_gap_score == d("0.466667")
    assert report.average_evidence_quality_gap_score == d("0.416667")
    assert report.average_liquidity_reliability_score == d("0.800000")
    assert report.average_cost_drag_score == d("0.200000")
    assert report.average_resolution_clarity_gap_score == d("0.466667")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategyInformationValuePriorityRow
    assert blocked.freshness_gap_score == d("0.800000")
    assert blocked.evidence_quality_gap_score == d("0.700000")
    assert blocked.cost_efficiency_score == d("0.900000")
    assert blocked.resolution_clarity_gap_score == d("0.800000")
    assert blocked.expected_information_value_score == d("0.820000")
    assert blocked.reason_codes == (
        "priority_score_block",
        "high_uncertainty_reduction",
        "stale_information_gap",
        "evidence_quality_gap",
        "liquidity_reliability_support",
        "resolution_clarity_gap",
    )

    watched = report.rows[1]
    assert watched.expected_information_value_score == d("0.550000")
    assert watched.reason_codes == ("priority_score_watch",)

    passed = report.rows[2]
    assert passed.expected_information_value_score == d("0.325000")
    assert passed.reason_codes == (
        "priority_score_pass",
        "liquidity_reliability_support",
    )

    assert report.reason_code_counts[0] == (
        module.ResearchStrategyInformationValuePriorityReasonCodeCount(
            reason_code="evidence_quality_gap",
            count=d("1.000000"),
            row_ratio=d("0.333333"),
        )
    )


def test_empty_report_is_report_only_pass() -> None:
    module = _module()
    report = _report(module, ())

    assert report.status == "pass"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_expected_information_value_score == ZERO
    assert report.highest_expected_information_value_score == ZERO
    assert report.average_uncertainty_reduction_score == ZERO
    assert report.average_freshness_gap_score == ZERO
    assert report.average_evidence_quality_gap_score == ZERO
    assert report.average_liquidity_reliability_score == ZERO
    assert report.average_cost_drag_score == ZERO
    assert report.average_resolution_clarity_gap_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyInformationValuePriorityReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )


def test_payload_redacts_private_refs_and_serializes_decimal_strings() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate-id/market-slug?token=hidden&wallet=private&question=copy",
                uncertainty_reduction_score=d("0.850000"),
                freshness_score=d("0.200000"),
                evidence_quality_score=d("0.300000"),
                liquidity_reliability_score=d("0.900000"),
                cost_drag_score=d("0.100000"),
                resolution_clarity_score=d("0.200000"),
            ),
        ),
    )

    payload = module.research_strategy_information_value_priority_report_payload(report)
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["expected_information_value_score"] == "0.820000"
    assert payload["rows"][0]["research_item_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "raw-candidate-id",
        "market-slug",
        "candidate",
        "market",
        "slug",
        "question",
        "token",
        "hidden",
        "wallet",
        "private",
        "order",
        "trade",
        "live",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(report)).casefold()


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    module = _module()

    assert is_dataclass(module.ResearchStrategyInformationValuePriorityConfig)
    assert is_dataclass(module.ResearchStrategyInformationValuePriorityInput)
    assert is_dataclass(module.ResearchStrategyInformationValuePriorityReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyInformationValuePriorityRow)
    assert is_dataclass(module.ResearchStrategyInformationValuePriorityReport)

    cfg = _config(module)
    source_row = _input(module)
    report = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.cost_drag_score = d("0.900000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].expected_information_value_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_PRIORITY_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="priority_score_block_threshold"):
        _config(module, priority_score_block_threshold=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="priority_score_watch_threshold"):
        _config(module, priority_score_watch_threshold=_DecimalSubclass("0.450000"))
    with pytest.raises(ValueError, match="priority_score_block_threshold"):
        _config(module, priority_score_block_threshold=d("0.400000"))
    with pytest.raises(ValueError, match="priority weights"):
        _config(module, uncertainty_reduction_weight=d("0.350000"))
    with pytest.raises(ValueError, match="research_item_ref"):
        _input(module, _StringSubclass("research-item-alpha"))
    with pytest.raises(ValueError, match="research_item_ref"):
        _input(module, " ")
    with pytest.raises(ValueError, match="uncertainty_reduction_score"):
        _input(module, uncertainty_reduction_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="freshness_score"):
        _input(module, freshness_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality_score"):
        _input(module, evidence_quality_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 8, 15, 30, tzinfo=UTC))
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


def test_public_payload_rejects_forbidden_fields_values_and_statuses() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_information_value_priority_report_payload(report)
    rendered = repr(payload).casefold()

    for token in (
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "sizing",
        "buy",
        "sell",
        "recommendation",
        "private key",
        "live",
        "blocked",
    ):
        assert token not in rendered

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_information_value_priority_report_payload(
            tampered_status,
        )

    tampered_field = dict(payload)
    tampered_field["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_information_value_priority_report_payload(
            tampered_field,
        )

    tampered_value = dict(payload)
    tampered_value["analysis_note"] = "https://example.test/source text copied here"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_information_value_priority_report_payload(
            tampered_value,
        )

    tampered_extra_field = dict(payload)
    tampered_extra_field["analysis_note"] = "benign public-looking memo"
    tampered_extra_field["derived_validation_digest"] = _public_digest(tampered_extra_field)
    with pytest.raises(ValueError, match="unsupported public payload field"):
        module.research_strategy_information_value_priority_report_payload(
            tampered_extra_field,
        )

    tampered_raw_ref = dict(payload)
    tampered_raw_ref["rows"] = [dict(payload["rows"][0])]
    tampered_raw_ref["rows"][0]["research_item_digest"] = "plain-safe-looking-id"
    tampered_raw_ref["rows"][0]["derived_validation_digest"] = _public_digest(
        tampered_raw_ref["rows"][0],
    )
    tampered_raw_ref["derived_validation_digest"] = _public_digest(tampered_raw_ref)
    with pytest.raises(ValueError, match="research_item_digest"):
        module.research_strategy_information_value_priority_report_payload(
            tampered_raw_ref,
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
    cfg = _config(module)
    report = _report(module, (_input(module),), cfg=cfg)
    passed = report.rows[0]

    with pytest.raises(ValueError, match="status"):
        replace(passed, status="watch", validation_config=cfg)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            passed,
            reason_codes=("priority_score_pass", "priority_score_watch"),
            validation_config=cfg,
        )
    with pytest.raises(ValueError, match="expected_information_value_score"):
        replace(passed, expected_information_value_score=ZERO, validation_config=cfg)
    with pytest.raises(ValueError, match="research_item_digest"):
        replace(passed, research_item_digest="raw-candidate-market")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = _report(
            module,
            (
                _input(
                    module,
                    "research-item-z",
                    uncertainty_reduction_score=d("0.850000"),
                    freshness_score=d("0.200000"),
                    evidence_quality_score=d("0.300000"),
                    liquidity_reliability_score=d("0.900000"),
                    cost_drag_score=d("0.100000"),
                    resolution_clarity_score=d("0.200000"),
                ),
                _input(module, "research-item-a"),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_order() -> None:
    module = _module()
    rows = (
        _input(module, "research-item-c"),
        _input(
            module,
            "research-item-a",
            uncertainty_reduction_score=d("0.850000"),
            freshness_score=d("0.200000"),
            evidence_quality_score=d("0.300000"),
            liquidity_reliability_score=d("0.900000"),
            cost_drag_score=d("0.100000"),
            resolution_clarity_score=d("0.200000"),
        ),
        _input(
            module,
            "research-item-b",
            uncertainty_reduction_score=d("0.600000"),
            freshness_score=d("0.500000"),
            evidence_quality_score=d("0.600000"),
            liquidity_reliability_score=d("0.700000"),
            cost_drag_score=d("0.300000"),
            resolution_clarity_score=d("0.600000"),
        ),
    )

    report_a = _report(module, rows)
    report_b = _report(module, tuple(reversed(rows)))

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_information_value_priority_report_payload(
        report_a,
    ) == module.research_strategy_information_value_priority_report_payload(report_b)

    tampered = module.research_strategy_information_value_priority_report_payload(report_a)
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_information_value_priority_report_payload(tampered)


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
        "DEFAULT_RESEARCH_STRATEGY_INFORMATION_VALUE_PRIORITY_REPORT_CONFIG_VERSION",
        "ResearchStrategyInformationValuePriorityConfig",
        "ResearchStrategyInformationValuePriorityInput",
        "ResearchStrategyInformationValuePriorityReasonCodeCount",
        "ResearchStrategyInformationValuePriorityReport",
        "ResearchStrategyInformationValuePriorityRow",
        "build_research_strategy_information_value_priority_report",
        "research_strategy_information_value_priority_report_payload",
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
        "place_order",
        "create_order",
        "submit_order",
    }

    assert imported_modules.isdisjoint(forbidden_import_roots)
    assert not any(call in forbidden_calls for call in call_names)
