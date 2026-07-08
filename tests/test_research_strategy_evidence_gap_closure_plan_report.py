from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_strategy_evidence_gap_closure_plan_report"
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 17, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_EVIDENCE_GAP_CLOSURE_PLAN_REPORT_CONFIG_VERSION
        ),
        "pass_min_closure_readiness_score": d("0.800000"),
        "watch_min_closure_readiness_score": d("0.600000"),
        "min_pass_source_readiness_score": d("0.800000"),
        "min_watch_source_readiness_score": d("0.600000"),
        "max_pass_contradiction_severity_score": d("0.200000"),
        "max_watch_contradiction_severity_score": d("0.450000"),
        "min_pass_update_freshness_score": d("0.800000"),
        "min_watch_update_freshness_score": d("0.600000"),
        "min_pass_domain_coverage_score": d("0.800000"),
        "min_watch_domain_coverage_score": d("0.600000"),
        "min_pass_resolution_rule_linkage_score": d("0.800000"),
        "min_watch_resolution_rule_linkage_score": d("0.600000"),
        "source_readiness_weight": d("0.250000"),
        "contradiction_clarity_weight": d("0.200000"),
        "update_freshness_weight": d("0.200000"),
        "domain_coverage_weight": d("0.150000"),
        "resolution_rule_linkage_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchStrategyEvidenceGapClosurePlanConfig(**values)


def _input(
    module: Any,
    evidence_gap_ref: str = "gap-alpha",
    **overrides: object,
) -> Any:
    values = {
        "evidence_gap_ref": evidence_gap_ref,
        "source_readiness_score": d("0.900000"),
        "contradiction_severity_score": d("0.100000"),
        "update_freshness_score": d("0.850000"),
        "domain_coverage_score": d("0.900000"),
        "resolution_rule_linkage_score": d("0.950000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("analyst_review_requested",),
    }
    values.update(overrides)
    return module.ResearchStrategyEvidenceGapClosurePlanInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_evidence_gap_closure_plan_report(
        rows,
        config=_config(module) if config is None else config,
        generated_at=generated_at,
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


def test_builds_pass_watch_and_block_gap_closure_plan_rows() -> None:
    module = api()
    passed = _input(
        module,
        "candidate-raw/market-slug?source_url=https://example.invalid&token=secret",
    )
    watched = _input(
        module,
        "gap-watch",
        source_readiness_score=d("0.700000"),
        contradiction_severity_score=d("0.350000"),
        update_freshness_score=d("0.650000"),
        domain_coverage_score=d("0.700000"),
        resolution_rule_linkage_score=d("0.650000"),
    )
    blocked = _input(
        module,
        "gap-block",
        source_readiness_score=d("0.400000"),
        contradiction_severity_score=d("0.700000"),
        update_freshness_score=d("0.500000"),
        domain_coverage_score=d("0.450000"),
        resolution_rule_linkage_score=d("0.300000"),
        reason_codes=("analyst_review_requested", "resolution_rule_missing"),
    )

    report = _report(
        module,
        (passed, watched, blocked),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    permuted = _report(module, (blocked, passed, watched))

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyEvidenceGapClosurePlanReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_EVIDENCE_GAP_CLOSURE_PLAN_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_closure_readiness_score == d("0.652500")
    assert report.min_source_readiness_score == d("0.400000")
    assert report.max_contradiction_severity_score == d("0.700000")
    assert report.min_update_freshness_score == d("0.500000")
    assert report.min_domain_coverage_score == d("0.450000")
    assert report.min_resolution_rule_linkage_score == d("0.300000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.closure_step for row in report.rows) == (
        "block_analyst_review_until_evidence_gap_closed",
        "refresh_public_evidence_before_analyst_review",
        "retain_analyst_review_packet_readiness",
    )

    blocked_row = report.rows[0]
    assert type(blocked_row) is module.ResearchStrategyEvidenceGapClosurePlanStep
    assert blocked_row.source_gap_score == d("0.600000")
    assert blocked_row.contradiction_clarity_score == d("0.300000")
    assert blocked_row.update_staleness_score == d("0.500000")
    assert blocked_row.domain_gap_score == d("0.550000")
    assert blocked_row.resolution_rule_gap_score == d("0.700000")
    assert blocked_row.closure_readiness_score == d("0.387500")
    assert blocked_row.reason_codes == (
        "analyst_review_requested",
        "resolution_rule_missing",
        "source_readiness_block",
        "contradiction_severity_block",
        "update_freshness_block",
        "domain_coverage_block",
        "resolution_rule_linkage_block",
        "closure_readiness_score_block",
    )

    watched_row = report.rows[1]
    assert watched_row.closure_readiness_score == d("0.670000")
    assert watched_row.reason_codes == (
        "analyst_review_requested",
        "source_readiness_watch",
        "contradiction_severity_watch",
        "update_freshness_watch",
        "domain_coverage_watch",
        "resolution_rule_linkage_watch",
        "closure_readiness_score_watch",
    )

    passed_row = report.rows[2]
    assert passed_row.closure_readiness_score == d("0.900000")
    assert passed_row.reason_codes == (
        "analyst_review_requested",
        "evidence_gap_closure_plan_pass",
    )

    assert report.reason_code_counts[0] == (
        module.ResearchStrategyEvidenceGapClosurePlanReasonCodeCount(
            reason_code="analyst_review_requested",
            count=d("3.000000"),
            row_ratio=d("1.000000"),
        )
    )
    assert report.payload == permuted.payload
    assert report.derived_validation_digest == permuted.derived_validation_digest


def test_empty_report_is_report_only_block() -> None:
    module = api()
    report = _report(module, ())
    payload = module.research_strategy_evidence_gap_closure_plan_report_payload(report)

    assert report.status == "block"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_closure_readiness_score == ZERO
    assert report.min_source_readiness_score == ZERO
    assert report.max_contradiction_severity_score == ZERO
    assert report.min_update_freshness_score == ZERO
    assert report.min_domain_coverage_score == ZERO
    assert report.min_resolution_rule_linkage_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyEvidenceGapClosurePlanReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert payload["rows"] == []
    assert payload["status"] == "block"
    assert payload["derived_validation_digest"] == report.derived_validation_digest


def test_payload_redacts_private_refs_and_uses_decimal_strings() -> None:
    module = api()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate-id/market-slug/question?source_text=hidden&wallet=secret",
            ),
        ),
    )

    payload = module.research_strategy_evidence_gap_closure_plan_report_payload(report)
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["closure_readiness_score"] == "0.900000"
    assert payload["rows"][0]["evidence_gap_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "raw-candidate-id",
        "market-slug",
        "question",
        "source_text",
        "hidden",
        "wallet",
        "secret",
    ):
        assert leaked not in rendered


def test_decimal_frozen_flags_and_report_consistency_are_validated() -> None:
    module = api()
    report = _report(module, (_input(module),))

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_readiness_score must be a Decimal"):
        _input(module, source_readiness_score=d("0.900000"))  # baseline works
        _input(module, source_readiness_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="contradiction_severity_score must be between zero and one"):
        _input(module, contradiction_severity_score=d("1.000001"))
    with pytest.raises(ValueError, match="config weights must sum to one"):
        _config(module, resolution_rule_linkage_weight=d("0.300000"))
    with pytest.raises(ValueError, match="max_pass_contradiction_severity_score"):
        _config(
            module,
            max_pass_contradiction_severity_score=d("0.500000"),
            max_watch_contradiction_severity_score=d("0.450000"),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_evidence_gap_closure_plan_report(
            (_input(module),),
            generated_at=datetime(2026, 7, 8, 18, 0),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        _report(
            module,
            (
                _input(
                    module,
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="duplicate evidence gap digest"):
        _report(module, (_input(module, "same-gap"), _input(module, "same-gap")))
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.ResearchStrategyEvidenceGapClosurePlanConfig(readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="rows must be sorted"):
        unordered = _report(
            module,
            (_input(module, "z-gap"), _input(module, "a-gap")),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report.rows[0], status="ready")


def test_public_contract_rejects_sensitive_public_values_and_tampered_payloads() -> None:
    module = api()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_evidence_gap_closure_plan_report_payload(report)

    for unsafe_ref in (
        "candidate_raw_id",
        "market_id_123",
        "market_slug_private",
        "source_url_private",
        "source_text_private",
        "dsn_private",
        "token_private",
        "wallet_private",
        "order_surface",
        "trade_surface",
        "recommendation_surface",
    ):
        accepted = _input(module, unsafe_ref)
        assert accepted.evidence_gap_ref == unsafe_ref

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        module.research_strategy_evidence_gap_closure_plan_report_payload(tampered)

    tampered_status = dict(payload)
    tampered_status["derived_validation_digest"] = payload["derived_validation_digest"]
    tampered_status["status"] = "ready"
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        module.research_strategy_evidence_gap_closure_plan_report_payload(tampered_status)

    with pytest.raises(ValueError, match="unsafe public"):
        module.research_strategy_evidence_gap_closure_plan_report_payload(
            {
                "status": "pass",
                "market_id": "leaked",
                "derived_validation_digest": "0" * 64,
            },
        )
    with pytest.raises(ValueError, match="report must be"):
        module.research_strategy_evidence_gap_closure_plan_report_payload(object())


def test_public_api_has_no_live_execution_or_private_surfaces() -> None:
    module = api()
    report = _report(module, (_input(module),))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_GAP_CLOSURE_PLAN_REPORT_CONFIG_VERSION",
        "ResearchStrategyEvidenceGapClosurePlanConfig",
        "ResearchStrategyEvidenceGapClosurePlanInput",
        "ResearchStrategyEvidenceGapClosurePlanReasonCodeCount",
        "ResearchStrategyEvidenceGapClosurePlanReport",
        "ResearchStrategyEvidenceGapClosurePlanStep",
        "build_research_strategy_evidence_gap_closure_plan_report",
        "research_strategy_evidence_gap_closure_plan_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    public_field_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            call_names.add(getattr(node.func, "attr", getattr(node.func, "id", "")))
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    for dataclass_type in (
        module.ResearchStrategyEvidenceGapClosurePlanInput,
        module.ResearchStrategyEvidenceGapClosurePlanStep,
        module.ResearchStrategyEvidenceGapClosurePlanReport,
    ):
        public_field_names.update(field.name for field in fields(dataclass_type))

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "post",
        "put",
        "patch",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_public_field_fragments = (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
        "raw_source",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "sizing",
        "recommendation",
        "recommended",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    assert not (call_names & forbidden_calls)
    assert not any(
        fragment in field_name
        for field_name in public_field_names
        for fragment in forbidden_public_field_fragments
    )
    for row in report.rows:
        for field in fields(row):
            if field.name.endswith(("_count", "_score", "_ratio", "_weight")):
                assert type(getattr(row, field.name)) is Decimal
