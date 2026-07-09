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
    "research_strategy_probability_review_readiness_index_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_probability_review_readiness_index_report.py",
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
    assert spec is not None, "probability review readiness index module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_PROBABILITY_REVIEW_READINESS_INDEX_REPORT_CONFIG_VERSION
        ),
        "pass_min_readiness_index": d("0.800000"),
        "watch_min_readiness_index": d("0.600000"),
        "min_pass_evidence_coverage_score": d("0.800000"),
        "min_watch_evidence_coverage_score": d("0.600000"),
        "min_pass_source_freshness_score": d("0.750000"),
        "min_watch_source_freshness_score": d("0.500000"),
        "max_pass_cost_drag_score": d("0.150000"),
        "max_watch_cost_drag_score": d("0.350000"),
        "min_pass_liquidity_reliability_score": d("0.750000"),
        "min_watch_liquidity_reliability_score": d("0.550000"),
        "min_pass_resolution_clarity_score": d("0.800000"),
        "min_watch_resolution_clarity_score": d("0.600000"),
        "min_pass_specialist_memory_readiness_score": d("0.750000"),
        "min_watch_specialist_memory_readiness_score": d("0.550000"),
        "evidence_coverage_weight": d("0.200000"),
        "source_freshness_weight": d("0.150000"),
        "cost_efficiency_weight": d("0.150000"),
        "liquidity_reliability_weight": d("0.150000"),
        "resolution_clarity_weight": d("0.200000"),
        "specialist_memory_readiness_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchStrategyProbabilityReviewReadinessIndexConfig(**values)


def _input(
    module: Any,
    review_item_ref: str = "review-item-alpha",
    **overrides: object,
) -> Any:
    values = {
        "review_item_ref": review_item_ref,
        "evidence_coverage_score": d("0.950000"),
        "source_freshness_score": d("0.900000"),
        "cost_drag_score": d("0.100000"),
        "liquidity_reliability_score": d("0.850000"),
        "resolution_clarity_score": d("0.900000"),
        "specialist_memory_readiness_score": d("0.850000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("review_packet_ready",),
    }
    values.update(overrides)
    return module.ResearchStrategyProbabilityReviewReadinessInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_probability_review_readiness_index_report(
        rows,
        generated_at=generated_at,
        config=cfg or _config(module),
    )


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(_walk_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return tuple(values)
    return (value,)


def _walk_keys(value: Any) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_keys(item))
    return tuple(keys)


def _payload_with_fresh_digest(payload: dict[str, object]) -> dict[str, object]:
    copied = json.loads(json.dumps(payload, sort_keys=True))
    assert type(copied) is dict
    copied.pop("derived_validation_digest", None)
    canonical = json.dumps(
        copied,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    copied["derived_validation_digest"] = sha256(
        canonical.encode("utf-8"),
    ).hexdigest()
    return copied


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
        if field.name.endswith(("_count", "_score", "_index", "_weight", "_ratio")):
            assert type(item) is Decimal


def test_builds_pass_watch_and_block_probability_review_readiness_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate-id/market-slug?token=hidden&wallet=private",
                reason_codes=("review_packet_ready",),
            ),
            _input(
                module,
                "review-item-watch",
                evidence_coverage_score=d("0.700000"),
                source_freshness_score=d("0.650000"),
                cost_drag_score=d("0.250000"),
                liquidity_reliability_score=d("0.600000"),
                resolution_clarity_score=d("0.700000"),
                specialist_memory_readiness_score=d("0.650000"),
                reason_codes=("manual_probability_review_requested",),
            ),
            _input(
                module,
                "review-item-block",
                evidence_coverage_score=d("0.450000"),
                source_freshness_score=d("0.400000"),
                cost_drag_score=d("0.650000"),
                liquidity_reliability_score=d("0.350000"),
                resolution_clarity_score=d("0.500000"),
                specialist_memory_readiness_score=d("0.450000"),
                reason_codes=(
                    "manual_probability_review_requested",
                    "specialist_memory_pending",
                ),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyProbabilityReviewReadinessIndexReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_PROBABILITY_REVIEW_READINESS_INDEX_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_readiness_index == d("0.665000")
    assert report.min_readiness_index == d("0.422500")
    assert report.min_evidence_coverage_score == d("0.450000")
    assert report.min_source_freshness_score == d("0.400000")
    assert report.max_cost_drag_score == d("0.650000")
    assert report.min_liquidity_reliability_score == d("0.350000")
    assert report.min_resolution_clarity_score == d("0.500000")
    assert report.min_specialist_memory_readiness_score == d("0.450000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategyProbabilityReviewReadinessIndexRow
    assert blocked.cost_efficiency_score == d("0.350000")
    assert blocked.readiness_index == d("0.422500")
    assert blocked.reason_codes == (
        "manual_probability_review_requested",
        "specialist_memory_pending",
        "evidence_coverage_block",
        "source_freshness_block",
        "cost_drag_block",
        "liquidity_reliability_block",
        "resolution_clarity_block",
        "specialist_memory_readiness_block",
        "readiness_index_block",
    )

    watched = report.rows[1]
    assert watched.cost_efficiency_score == d("0.750000")
    assert watched.readiness_index == d("0.677500")
    assert watched.reason_codes == (
        "manual_probability_review_requested",
        "evidence_coverage_watch",
        "source_freshness_watch",
        "cost_drag_watch",
        "liquidity_reliability_watch",
        "resolution_clarity_watch",
        "specialist_memory_readiness_watch",
        "readiness_index_watch",
    )

    passed = report.rows[2]
    assert passed.cost_efficiency_score == d("0.900000")
    assert passed.readiness_index == d("0.895000")
    assert passed.reason_codes == (
        "review_packet_ready",
        "probability_review_ready_pass",
    )

    assert report.reason_code_counts[0] == (
        module.ResearchStrategyProbabilityReviewReadinessReasonCodeCount(
            reason_code="manual_probability_review_requested",
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
    assert report.average_readiness_index == ZERO
    assert report.min_readiness_index == ZERO
    assert report.min_evidence_coverage_score == ZERO
    assert report.min_source_freshness_score == ZERO
    assert report.max_cost_drag_score == ZERO
    assert report.min_liquidity_reliability_score == ZERO
    assert report.min_resolution_clarity_score == ZERO
    assert report.min_specialist_memory_readiness_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyProbabilityReviewReadinessReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_redacts_private_refs_and_validates_digest() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate-id/market-slug?token=hidden&wallet=private",
            ),
        ),
    )

    payload = module.research_strategy_probability_review_readiness_index_report_payload(
        report,
    )
    encoded = json.dumps(payload, sort_keys=True)
    rendered = repr(payload).casefold()

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["readiness_index"] == "0.895000"
    assert payload["rows"][0]["review_item_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert not any(isinstance(value, Decimal) for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "raw-candidate-id",
        "market-slug",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "hidden",
        "wallet",
        "private",
        "order",
        "trade",
        "recommend",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(report)).casefold()
    assert not any(
        key
        in {
            "candidate_id",
            "market_id",
            "market_slug",
            "condition_id",
            "token_id",
            "question",
            "source_url",
            "source_text",
            "dsn",
            "table_name",
        }
        for key in _walk_keys(payload)
    )

    tampered = dict(payload)
    tampered["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_probability_review_readiness_index_report_payload(
            tampered,
        )


def test_decimal_type_rejection_frozen_dataclasses_and_hard_flags() -> None:
    module = _module()

    assert is_dataclass(module.ResearchStrategyProbabilityReviewReadinessIndexConfig)
    assert is_dataclass(module.ResearchStrategyProbabilityReviewReadinessInput)
    assert is_dataclass(module.ResearchStrategyProbabilityReviewReadinessReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyProbabilityReviewReadinessIndexRow)
    assert is_dataclass(module.ResearchStrategyProbabilityReviewReadinessIndexReport)

    cfg = _config(module)
    source_row = _input(module)
    report = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.cost_drag_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].readiness_index = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_PROBABILITY_REVIEW_READINESS_INDEX_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_readiness_index"):
        _config(module, pass_min_readiness_index=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_readiness_index"):
        _config(module, watch_min_readiness_index=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_min_readiness_index"):
        _config(module, pass_min_readiness_index=d("0.500000"))
    with pytest.raises(ValueError, match="max_pass_cost_drag_score"):
        _config(module, max_pass_cost_drag_score=d("0.500000"))
    with pytest.raises(ValueError, match="readiness weights"):
        _config(module, evidence_coverage_weight=d("0.250000"))
    with pytest.raises(ValueError, match="review_item_ref"):
        _input(module, _StringSubclass("review-item-alpha"))
    with pytest.raises(ValueError, match="review_item_ref"):
        _input(module, " ")
    with pytest.raises(ValueError, match="evidence_coverage_score"):
        _input(module, evidence_coverage_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_drag_score"):
        _input(module, cost_drag_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_freshness_score"):
        _input(module, source_freshness_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 8, 17, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="reason_codes"):
        _input(module, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        _config(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _input(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        _report(module, (), generated_at=datetime(2026, 7, 8, 18, 0))
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
                    observed_at=datetime(2026, 7, 8, 18, 1, tzinfo=UTC),
                ),
            ),
        )

    for value in (cfg, source_row, report, *report.rows, *report.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        _assert_decimal_numeric_fields(value)


def test_public_payload_rejects_unsafe_fields_values_and_statuses() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_probability_review_readiness_index_report_payload(
        report,
    )

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_probability_review_readiness_index_report_payload(
            tampered_status,
        )

    tampered_field = dict(payload)
    tampered_field["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_probability_review_readiness_index_report_payload(
            tampered_field,
        )

    tampered_value = dict(payload)
    tampered_value["review_scope"] = "https://example.test/source"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_probability_review_readiness_index_report_payload(
            tampered_value,
        )

    tampered_top_level_flag = dict(payload)
    tampered_top_level_flag["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        module.research_strategy_probability_review_readiness_index_report_payload(
            _payload_with_fresh_digest(tampered_top_level_flag),
        )

    tampered_nested_flag = json.loads(json.dumps(payload))
    tampered_nested_flag["rows"][0]["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_probability_review_readiness_index_report_payload(
            _payload_with_fresh_digest(tampered_nested_flag),
        )


def test_manual_report_and_row_drift_rejected() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    passed = report.rows[0]

    with pytest.raises(ValueError, match="status"):
        replace(passed, status="watch")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            passed,
            reason_codes=("probability_review_ready_pass", "readiness_index_watch"),
        )
    with pytest.raises(ValueError, match="readiness_index"):
        replace(passed, readiness_index=ZERO, validation_config=_config(module))
    with pytest.raises(ValueError, match="review_item_digest"):
        replace(passed, review_item_digest="raw-candidate-market")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = _report(
            module,
            (
                _input(module, "review-item-z", cost_drag_score=d("0.650000")),
                _input(module, "review-item-a"),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_order() -> None:
    module = _module()
    rows = (
        _input(module, "review-item-c", cost_drag_score=d("0.650000")),
        _input(module, "review-item-a"),
        _input(module, "review-item-b", evidence_coverage_score=d("0.700000")),
    )

    report_a = _report(module, rows)
    report_b = _report(module, tuple(reversed(rows)))

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_probability_review_readiness_index_report_payload(
        report_a,
    ) == module.research_strategy_probability_review_readiness_index_report_payload(
        report_b,
    )


def test_module_scope_is_read_only_report_only_and_public_api_is_narrow() -> None:
    module = _module()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_REVIEW_READINESS_INDEX_REPORT_CONFIG_VERSION",
        "PROBABILITY_REVIEW_READINESS_INDEX_STATUSES",
        "ResearchStrategyProbabilityReviewReadinessIndexConfig",
        "ResearchStrategyProbabilityReviewReadinessIndexReport",
        "ResearchStrategyProbabilityReviewReadinessIndexRow",
        "ResearchStrategyProbabilityReviewReadinessInput",
        "ResearchStrategyProbabilityReviewReadinessReasonCodeCount",
        "build_research_strategy_probability_review_readiness_index_report",
        "research_strategy_probability_review_readiness_index_report_payload",
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
    forbidden_terms = (
        "network",
        "database",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "question",
        "source_url",
        "source_text",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    lowered = source.lower()
    assert all(term not in lowered for term in forbidden_terms)
