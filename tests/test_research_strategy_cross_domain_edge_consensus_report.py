from __future__ import annotations

import ast
import hashlib
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
    "research_strategy_cross_domain_edge_consensus_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_cross_domain_edge_consensus_report.py",
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
    assert spec is not None, "cross-domain edge consensus report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_CONSENSUS_CONFIG_VERSION
        ),
        "pass_min_consensus_score": d("0.800000"),
        "watch_min_consensus_score": d("0.600000"),
        "min_pass_dimension_score": d("0.750000"),
        "min_watch_dimension_score": d("0.500000"),
        "max_pass_cost_drag_score": d("0.200000"),
        "max_watch_cost_drag_score": d("0.450000"),
        "domain_signal_agreement_weight": d("0.180000"),
        "evidence_strength_weight": d("0.170000"),
        "source_freshness_weight": d("0.130000"),
        "cost_efficiency_weight": d("0.130000"),
        "liquidity_quality_weight": d("0.140000"),
        "resolution_clarity_weight": d("0.130000"),
        "specialist_memory_confidence_weight": d("0.120000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCrossDomainEdgeConsensusConfig(**values)


def _input(
    module: Any,
    consensus_item_ref: str = "cross-domain-review-alpha",
    **overrides: object,
) -> Any:
    values = {
        "consensus_item_ref": consensus_item_ref,
        "domain_signal_agreement_score": d("0.900000"),
        "evidence_strength_score": d("0.920000"),
        "source_freshness_score": d("0.880000"),
        "cost_drag_score": d("0.100000"),
        "liquidity_quality_score": d("0.850000"),
        "resolution_clarity_score": d("0.900000"),
        "specialist_memory_confidence_score": d("0.860000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("cross_domain_review_ready",),
    }
    values.update(overrides)
    return module.ResearchStrategyCrossDomainEdgeConsensusInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_cross_domain_edge_consensus_report(
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
        if field.name.endswith(("_count", "_score", "_weight", "_ratio")):
            assert type(item) is Decimal


def test_builds_pass_watch_and_block_consensus_rows() -> None:
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
                "cross-domain-watch",
                domain_signal_agreement_score=d("0.700000"),
                evidence_strength_score=d("0.720000"),
                source_freshness_score=d("0.600000"),
                cost_drag_score=d("0.350000"),
                liquidity_quality_score=d("0.660000"),
                resolution_clarity_score=d("0.650000"),
                specialist_memory_confidence_score=d("0.700000"),
                reason_codes=(
                    "domain_disagreement_observed",
                    "manual_review_requested",
                ),
            ),
            _input(
                module,
                "cross-domain-block",
                domain_signal_agreement_score=d("0.450000"),
                evidence_strength_score=d("0.500000"),
                source_freshness_score=d("0.400000"),
                cost_drag_score=d("0.700000"),
                liquidity_quality_score=d("0.450000"),
                resolution_clarity_score=d("0.550000"),
                specialist_memory_confidence_score=d("0.350000"),
                reason_codes=(
                    "manual_review_requested",
                    "source_freshness_gap_observed",
                    "specialist_memory_review_requested",
                ),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyCrossDomainEdgeConsensusReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_CONSENSUS_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_consensus_score == d("0.664767")
    assert report.min_consensus_score == d("0.433500")
    assert report.min_domain_signal_agreement_score == d("0.450000")
    assert report.min_evidence_strength_score == d("0.500000")
    assert report.min_source_freshness_score == d("0.400000")
    assert report.max_cost_drag_score == d("0.700000")
    assert report.min_liquidity_quality_score == d("0.450000")
    assert report.min_resolution_clarity_score == d("0.550000")
    assert report.min_specialist_memory_confidence_score == d("0.350000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategyCrossDomainEdgeConsensusRow
    assert blocked.cost_efficiency_score == d("0.300000")
    assert blocked.consensus_score == d("0.433500")
    assert blocked.lowest_dimension_score == d("0.300000")
    assert blocked.reason_codes == (
        "manual_review_requested",
        "source_freshness_gap_observed",
        "specialist_memory_review_requested",
        "domain_signal_agreement_block",
        "evidence_strength_watch",
        "source_freshness_block",
        "cost_drag_block",
        "liquidity_quality_block",
        "resolution_clarity_watch",
        "specialist_memory_confidence_block",
        "consensus_score_block",
    )

    watched = report.rows[1]
    assert watched.cost_efficiency_score == d("0.650000")
    assert watched.consensus_score == d("0.671800")
    assert watched.reason_codes == (
        "domain_disagreement_observed",
        "manual_review_requested",
        "domain_signal_agreement_watch",
        "evidence_strength_watch",
        "source_freshness_watch",
        "cost_drag_watch",
        "liquidity_quality_watch",
        "resolution_clarity_watch",
        "specialist_memory_confidence_watch",
        "consensus_score_watch",
    )

    passed = report.rows[2]
    assert passed.cost_efficiency_score == d("0.900000")
    assert passed.consensus_score == d("0.889000")
    assert passed.reason_codes == (
        "cross_domain_review_ready",
        "cross_domain_edge_consensus_pass",
    )

    reason_count_by_code = {
        item.reason_code: item for item in report.reason_code_counts
    }
    assert reason_count_by_code["manual_review_requested"] == (
        module.ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount(
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
    assert report.average_consensus_score == ZERO
    assert report.min_consensus_score == ZERO
    assert report.min_domain_signal_agreement_score == ZERO
    assert report.min_evidence_strength_score == ZERO
    assert report.min_source_freshness_score == ZERO
    assert report.max_cost_drag_score == ZERO
    assert report.min_liquidity_quality_score == ZERO
    assert report.min_resolution_clarity_score == ZERO
    assert report.min_specialist_memory_confidence_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount(
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
    report = _report(
        module,
        (
            _input(
                module,
                "candidate=abc&market_slug=hidden-question&token=secret&wallet=0xabc",
            ),
        ),
    )

    payload = module.research_strategy_cross_domain_edge_consensus_report_payload(report)
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["consensus_score"] == "0.889000"
    assert payload["rows"][0]["consensus_item_digest"].startswith("sha256:")
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

    assert is_dataclass(module.ResearchStrategyCrossDomainEdgeConsensusConfig)
    assert is_dataclass(module.ResearchStrategyCrossDomainEdgeConsensusInput)
    assert is_dataclass(module.ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyCrossDomainEdgeConsensusRow)
    assert is_dataclass(module.ResearchStrategyCrossDomainEdgeConsensusReport)

    cfg = _config(module)
    source_row = _input(module)
    report = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.cost_drag_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].consensus_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_CONSENSUS_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_consensus_score"):
        _config(module, pass_min_consensus_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_consensus_score"):
        _config(module, watch_min_consensus_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_min_consensus_score"):
        _config(module, pass_min_consensus_score=d("0.500000"))
    with pytest.raises(ValueError, match="max_pass_cost_drag_score"):
        _config(module, max_pass_cost_drag_score=d("0.600000"))
    with pytest.raises(ValueError, match="weights"):
        _config(module, evidence_strength_weight=d("0.180000"))
    with pytest.raises(ValueError, match="consensus_item_ref"):
        _input(module, _StringSubclass("cross-domain-alpha"))
    with pytest.raises(ValueError, match="consensus_item_ref"):
        _input(module, " ")
    with pytest.raises(ValueError, match="domain_signal_agreement_score"):
        _input(module, domain_signal_agreement_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_strength_score"):
        _input(module, evidence_strength_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_freshness_score"):
        _input(module, source_freshness_score=Decimal("NaN"))
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
            (_input(module, observed_at=datetime(2026, 7, 8, 16, 1, tzinfo=UTC)),),
        )


def test_public_payload_rejects_forbidden_fields_values_and_statuses() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_cross_domain_edge_consensus_report_payload(report)
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
        "recommend",
        "live",
        "blocked",
    ):
        assert token not in rendered

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_cross_domain_edge_consensus_report_payload(
            tampered_status,
        )

    tampered_field = dict(payload)
    tampered_field["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_cross_domain_edge_consensus_report_payload(
            tampered_field,
        )

    tampered_value = dict(payload)
    tampered_value["reason_codes"] = ["source_text_copied_from_url"]
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_cross_domain_edge_consensus_report_payload(
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
                "cross_domain_edge_consensus_pass",
                "consensus_score_watch",
            ),
        )
    with pytest.raises(ValueError, match="consensus_score"):
        replace(passed, consensus_score=ZERO, validation_config=_config(module))
    with pytest.raises(ValueError, match="consensus_item_digest"):
        replace(passed, consensus_item_digest="candidate-market")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = _report(
            module,
            (
                _input(module, "cross-domain-z", cost_drag_score=d("0.700000")),
                _input(module, "cross-domain-a"),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_order() -> None:
    module = _module()
    rows = (
        _input(module, "cross-domain-c", cost_drag_score=d("0.700000")),
        _input(module, "cross-domain-a"),
        _input(module, "cross-domain-b", evidence_strength_score=d("0.700000")),
    )

    report_a = _report(module, rows)
    report_b = _report(module, tuple(reversed(rows)))

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_cross_domain_edge_consensus_report_digest(
        report_a,
    ) == report_a.derived_validation_digest
    assert module.research_strategy_cross_domain_edge_consensus_report_payload(
        report_a,
    ) == module.research_strategy_cross_domain_edge_consensus_report_payload(
        report_b,
    )

    tampered = module.research_strategy_cross_domain_edge_consensus_report_payload(
        report_a,
    )
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_cross_domain_edge_consensus_report_payload(tampered)


def test_payload_rejects_forged_noncanonical_report_schema_even_with_matching_digest() -> None:
    module = _module()
    forged_payload: dict[str, object] = {
        "status": "pass",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    encoded = json.dumps(
        forged_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    forged_payload["derived_validation_digest"] = hashlib.sha256(
        encoded.encode("utf-8"),
    ).hexdigest()

    with pytest.raises(ValueError, match="canonical report payload schema"):
        module.research_strategy_cross_domain_edge_consensus_report_payload(
            forged_payload,
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
        "DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_EDGE_CONSENSUS_CONFIG_VERSION",
        "ResearchStrategyCrossDomainEdgeConsensusConfig",
        "ResearchStrategyCrossDomainEdgeConsensusInput",
        "ResearchStrategyCrossDomainEdgeConsensusReasonCodeCount",
        "ResearchStrategyCrossDomainEdgeConsensusReport",
        "ResearchStrategyCrossDomainEdgeConsensusRow",
        "build_research_strategy_cross_domain_edge_consensus_report",
        "research_strategy_cross_domain_edge_consensus_report_digest",
        "research_strategy_cross_domain_edge_consensus_report_payload",
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
