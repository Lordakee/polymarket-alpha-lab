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
    "research_strategy_probability_update_audit_trail_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_probability_update_audit_trail_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 20, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 19, 30, tzinfo=UTC)
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
    assert spec is not None, "probability update audit trail report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_PROBABILITY_UPDATE_AUDIT_TRAIL_REPORT_CONFIG_VERSION
        ),
        "pass_min_auditability_score": d("0.800000"),
        "watch_min_auditability_score": d("0.600000"),
        "min_pass_prior_estimate_trace_score": d("0.800000"),
        "min_watch_prior_estimate_trace_score": d("0.600000"),
        "min_pass_new_evidence_type_score": d("0.800000"),
        "min_watch_new_evidence_type_score": d("0.600000"),
        "max_pass_source_age_minutes": d("60.000000"),
        "max_watch_source_age_minutes": d("180.000000"),
        "max_pass_cost_change_ratio": d("0.150000"),
        "max_watch_cost_change_ratio": d("0.350000"),
        "min_pass_liquidity_change_trace_score": d("0.750000"),
        "min_watch_liquidity_change_trace_score": d("0.550000"),
        "min_pass_reviewer_rationale_score": d("0.800000"),
        "min_watch_reviewer_rationale_score": d("0.600000"),
        "prior_estimate_weight": d("0.200000"),
        "new_evidence_type_weight": d("0.150000"),
        "source_freshness_weight": d("0.150000"),
        "cost_stability_weight": d("0.150000"),
        "liquidity_change_weight": d("0.150000"),
        "reviewer_rationale_weight": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchStrategyProbabilityUpdateAuditTrailConfig(**values)


def _input(
    module: Any,
    update_ref: str = "update-ref-alpha",
    **overrides: object,
) -> Any:
    values = {
        "update_ref": update_ref,
        "prior_estimate_trace_score": d("0.950000"),
        "new_evidence_type_score": d("0.900000"),
        "source_age_minutes": d("20.000000"),
        "cost_change_ratio": d("0.050000"),
        "liquidity_change_trace_score": d("0.850000"),
        "reviewer_rationale_completeness_score": d("0.900000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return module.ResearchStrategyProbabilityUpdateAuditTrailInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_probability_update_audit_trail_report(
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


def _with_recomputed_digest(payload: dict[str, object]) -> dict[str, object]:
    updated = dict(payload)
    unsigned = dict(updated)
    unsigned.pop("derived_validation_digest", None)
    updated["derived_validation_digest"] = sha256(
        json.dumps(
            unsigned,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    return updated


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
        if field.name.endswith(("_count", "_score", "_ratio", "_minutes", "_weight")):
            assert type(item) is Decimal


def test_builds_pass_watch_and_block_auditability_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate-id/market-slug?token=hidden&wallet=private",
            ),
            _input(
                module,
                "update-ref-watch",
                prior_estimate_trace_score=d("0.700000"),
                new_evidence_type_score=d("0.700000"),
                source_age_minutes=d("90.000000"),
                cost_change_ratio=d("0.250000"),
                liquidity_change_trace_score=d("0.600000"),
                reviewer_rationale_completeness_score=d("0.700000"),
            ),
            _input(
                module,
                "update-ref-block",
                prior_estimate_trace_score=d("0.450000"),
                new_evidence_type_score=d("0.500000"),
                source_age_minutes=d("240.000000"),
                cost_change_ratio=d("0.650000"),
                liquidity_change_trace_score=d("0.350000"),
                reviewer_rationale_completeness_score=d("0.500000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyProbabilityUpdateAuditTrailReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_PROBABILITY_UPDATE_AUDIT_TRAIL_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_auditability_score == d("0.646944")
    assert report.min_auditability_score == d("0.370000")
    assert report.min_prior_estimate_trace_score == d("0.450000")
    assert report.min_new_evidence_type_score == d("0.500000")
    assert report.max_source_age_minutes == d("240.000000")
    assert report.max_cost_change_ratio == d("0.650000")
    assert report.min_liquidity_change_trace_score == d("0.350000")
    assert report.min_reviewer_rationale_completeness_score == d("0.500000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategyProbabilityUpdateAuditTrailRow
    assert blocked.source_freshness_score == ZERO
    assert blocked.cost_stability_score == d("0.350000")
    assert blocked.auditability_score == d("0.370000")
    assert blocked.reason_codes == (
        "prior_estimate_trace_block",
        "new_evidence_type_block",
        "source_freshness_block",
        "cost_change_block",
        "liquidity_change_trace_block",
        "reviewer_rationale_block",
        "auditability_score_block",
    )

    watched = report.rows[1]
    assert watched.source_freshness_score == d("0.500000")
    assert watched.cost_stability_score == d("0.750000")
    assert watched.auditability_score == d("0.662500")
    assert watched.reason_codes == (
        "prior_estimate_trace_watch",
        "new_evidence_type_watch",
        "source_freshness_watch",
        "cost_change_watch",
        "liquidity_change_trace_watch",
        "reviewer_rationale_watch",
        "auditability_score_watch",
    )

    passed = report.rows[2]
    assert passed.source_freshness_score == d("0.888889")
    assert passed.cost_stability_score == d("0.950000")
    assert passed.auditability_score == d("0.908333")
    assert passed.reason_codes == ("probability_update_audit_trail_pass",)

    assert report.reason_code_counts[0] == (
        module.ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount(
            reason_code="auditability_score_block",
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
    assert report.average_auditability_score == ZERO
    assert report.min_auditability_score == ZERO
    assert report.min_prior_estimate_trace_score == ZERO
    assert report.min_new_evidence_type_score == ZERO
    assert report.max_source_age_minutes == ZERO
    assert report.max_cost_change_ratio == ZERO
    assert report.min_liquidity_change_trace_score == ZERO
    assert report.min_reviewer_rationale_completeness_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount(
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

    payload = module.research_strategy_probability_update_audit_trail_report_payload(
        report,
    )
    encoded = json.dumps(payload, sort_keys=True)
    rendered = repr(payload).casefold()

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["auditability_score"] == "0.908333"
    assert payload["rows"][0]["update_ref_digest"].startswith("sha256:")
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
        "sizing",
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
        module.research_strategy_probability_update_audit_trail_report_payload(
            tampered,
        )


def test_decimal_type_rejection_frozen_dataclasses_and_hard_flags() -> None:
    module = _module()

    assert is_dataclass(module.ResearchStrategyProbabilityUpdateAuditTrailConfig)
    assert is_dataclass(module.ResearchStrategyProbabilityUpdateAuditTrailInput)
    assert is_dataclass(module.ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyProbabilityUpdateAuditTrailRow)
    assert is_dataclass(module.ResearchStrategyProbabilityUpdateAuditTrailReport)

    cfg = _config(module)
    source_row = _input(module)
    report = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.cost_change_ratio = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].auditability_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_PROBABILITY_UPDATE_AUDIT_TRAIL_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_auditability_score"):
        _config(module, pass_min_auditability_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_auditability_score"):
        _config(module, watch_min_auditability_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_min_auditability_score"):
        _config(module, pass_min_auditability_score=d("0.500000"))
    with pytest.raises(ValueError, match="max_pass_source_age_minutes"):
        _config(module, max_pass_source_age_minutes=d("240.000000"))
    with pytest.raises(ValueError, match="max_pass_cost_change_ratio"):
        _config(module, max_pass_cost_change_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="auditability weights"):
        _config(module, prior_estimate_weight=d("0.250000"))
    with pytest.raises(ValueError, match="update_ref"):
        _input(module, _StringSubclass("update-ref-alpha"))
    with pytest.raises(ValueError, match="update_ref"):
        _input(module, " ")
    with pytest.raises(ValueError, match="prior_estimate_trace_score"):
        _input(module, prior_estimate_trace_score="0.900000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_age_minutes"):
        _input(module, source_age_minutes=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_change_ratio"):
        _input(module, cost_change_ratio=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 8, 19, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        _config(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _input(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report.rows[0], readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        _report(module, (), generated_at=datetime(2026, 7, 8, 20, 0))
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
                    observed_at=datetime(2026, 7, 8, 20, 1, tzinfo=UTC),
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
    payload = module.research_strategy_probability_update_audit_trail_report_payload(
        report,
    )

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_probability_update_audit_trail_report_payload(
            tampered_status,
        )

    tampered_field = dict(payload)
    tampered_field["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_probability_update_audit_trail_report_payload(
            tampered_field,
        )

    tampered_value = dict(payload)
    tampered_value["review_scope"] = "https://example.test/source"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_probability_update_audit_trail_report_payload(
            tampered_value,
        )


def test_public_payload_rejects_flag_tampering_with_recomputed_digest() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_probability_update_audit_trail_report_payload(
        report,
    )

    tampered_report_flag = dict(payload)
    tampered_report_flag["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        module.research_strategy_probability_update_audit_trail_report_payload(
            _with_recomputed_digest(tampered_report_flag),
        )

    tampered_row_flag = dict(payload)
    rows = [dict(row) for row in tampered_row_flag["rows"]]  # type: ignore[union-attr]
    rows[0]["readonly"] = False
    tampered_row_flag["rows"] = rows
    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_probability_update_audit_trail_report_payload(
            _with_recomputed_digest(tampered_row_flag),
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
            reason_codes=(
                "probability_update_audit_trail_pass",
                "auditability_score_watch",
            ),
        )
    with pytest.raises(ValueError, match="auditability_score"):
        replace(passed, auditability_score=ZERO, validation_config=_config(module))
    with pytest.raises(ValueError, match="update_ref_digest"):
        replace(passed, update_ref_digest="raw-candidate-market")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = _report(
            module,
            (
                _input(module, "update-ref-z", cost_change_ratio=d("0.650000")),
                _input(module, "update-ref-a"),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_order() -> None:
    module = _module()
    rows = (
        _input(module, "update-ref-c", cost_change_ratio=d("0.650000")),
        _input(module, "update-ref-a"),
        _input(module, "update-ref-b", prior_estimate_trace_score=d("0.700000")),
    )

    report_a = _report(module, rows)
    report_b = _report(module, tuple(reversed(rows)))

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_probability_update_audit_trail_report_payload(
        report_a,
    ) == module.research_strategy_probability_update_audit_trail_report_payload(
        report_b,
    )


def test_module_scope_is_read_only_report_only_and_public_api_is_narrow() -> None:
    module = _module()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_UPDATE_AUDIT_TRAIL_REPORT_CONFIG_VERSION",
        "PROBABILITY_UPDATE_AUDIT_TRAIL_STATUSES",
        "ResearchStrategyProbabilityUpdateAuditTrailConfig",
        "ResearchStrategyProbabilityUpdateAuditTrailInput",
        "ResearchStrategyProbabilityUpdateAuditTrailReport",
        "ResearchStrategyProbabilityUpdateAuditTrailRow",
        "ResearchStrategyProbabilityUpdateAuditTrailReasonCodeCount",
        "build_research_strategy_probability_update_audit_trail_report",
        "research_strategy_probability_update_audit_trail_report_payload",
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
