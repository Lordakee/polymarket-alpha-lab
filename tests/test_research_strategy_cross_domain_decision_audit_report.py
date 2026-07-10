from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_cross_domain_decision_audit_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_cross_domain_decision_audit_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


class _DictSubclass(dict[str, Any]):
    pass


class _ListSubclass(list[Any]):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "cross-domain decision audit report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_DECISION_AUDIT_CONFIG_VERSION
        ),
        "pass_min_audit_score": d("0.800000"),
        "watch_min_audit_score": d("0.600000"),
        "min_pass_domain_quorum_ratio": d("0.750000"),
        "min_watch_domain_quorum_ratio": d("0.500000"),
        "max_pass_conflict_ratio": d("0.200000"),
        "max_watch_conflict_ratio": d("0.400000"),
        "max_pass_stale_evidence_ratio": d("0.150000"),
        "max_watch_stale_evidence_ratio": d("0.350000"),
        "max_pass_unresolved_blocker_count": ZERO,
        "max_watch_unresolved_blocker_count": ONE,
        "domain_quorum_weight": d("0.220000"),
        "evidence_alignment_weight": d("0.180000"),
        "decision_trace_weight": d("0.170000"),
        "resolution_readiness_weight": d("0.150000"),
        "stale_evidence_control_weight": d("0.130000"),
        "conflict_control_weight": d("0.100000"),
        "memory_calibration_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCrossDomainDecisionAuditConfig(**values)


def _input(
    module: Any,
    audit_item_ref: str = "decision-audit-alpha",
    **overrides: object,
) -> Any:
    values = {
        "audit_item_ref": audit_item_ref,
        "domain_quorum_ratio": d("0.950000"),
        "evidence_alignment_score": d("0.900000"),
        "decision_trace_score": d("0.880000"),
        "resolution_readiness_score": d("0.860000"),
        "stale_evidence_ratio": d("0.050000"),
        "cross_domain_conflict_ratio": d("0.100000"),
        "memory_calibration_score": d("0.840000"),
        "unresolved_blocker_count": ZERO,
        "observed_at": OBSERVED_AT,
        "reason_codes": ("cross_domain_decision_ready",),
    }
    values.update(overrides)
    return module.ResearchStrategyCrossDomainDecisionAuditInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_cross_domain_decision_audit_report(
        rows,
        generated_at=generated_at,
        config=cfg or _config(module),
    )


def _assert_no_float_or_int_values(value: Any) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_float_or_int_values(item)


def _assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def _resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    canonical = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return {
        **unsigned,
        "derived_validation_digest": sha256(canonical.encode("utf-8")).hexdigest(),
    }


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


def test_status_vocabulary_is_exact() -> None:
    module = _module()

    assert module.RESEARCH_STRATEGY_CROSS_DOMAIN_DECISION_AUDIT_STATUSES == (
        "pass",
        "watch",
        "block",
    )


def test_builds_deterministic_pass_watch_block_audit_without_raw_leakage() -> None:
    module = _module()
    pass_item = _input(
        module,
        "candidate_id=pass market_slug=hidden question=private "
        "source_url=https://private.example/token",
    )
    watch_item = _input(
        module,
        "candidate_id=watch market_slug=hidden source_text=private",
        domain_quorum_ratio=d("0.700000"),
        evidence_alignment_score=d("0.720000"),
        decision_trace_score=d("0.700000"),
        resolution_readiness_score=d("0.740000"),
        stale_evidence_ratio=d("0.250000"),
        cross_domain_conflict_ratio=d("0.300000"),
        memory_calibration_score=d("0.720000"),
        unresolved_blocker_count=ONE,
        reason_codes=("domain_conflict_observed", "manual_review_requested"),
    )
    block_item = _input(
        module,
        "candidate_id=block market_id=private table=secret wallet=0xabc",
        domain_quorum_ratio=d("0.400000"),
        evidence_alignment_score=d("0.450000"),
        decision_trace_score=d("0.500000"),
        resolution_readiness_score=d("0.550000"),
        stale_evidence_ratio=d("0.500000"),
        cross_domain_conflict_ratio=d("0.650000"),
        memory_calibration_score=d("0.400000"),
        unresolved_blocker_count=d("2.000000"),
        reason_codes=(
            "domain_conflict_observed",
            "evidence_trace_gap_observed",
            "memory_calibration_review_requested",
        ),
    )

    first = _report(
        module,
        (watch_item, block_item, pass_item),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    second = _report(module, (pass_item, watch_item, block_item))

    assert is_dataclass(first)
    assert type(first) is module.ResearchStrategyCrossDomainDecisionAuditReport
    assert first.generated_at == GENERATED_AT
    assert first.generated_at.tzinfo is UTC
    assert first.status == "block"
    assert first.row_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.average_decision_audit_score == d("0.692900")
    assert first.min_decision_audit_score == d("0.456500")
    assert first.min_domain_quorum_ratio == d("0.400000")
    assert first.max_cross_domain_conflict_ratio == d("0.650000")
    assert first.max_stale_evidence_ratio == d("0.500000")
    assert first.max_unresolved_blocker_count == d("2.000000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    _assert_digest(first.derived_validation_digest)

    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert len({row.audit_item_digest for row in first.rows}) == 3
    assert all(row.audit_item_digest.startswith("sha256:") for row in first.rows)
    assert all("candidate_id" not in row.audit_item_digest for row in first.rows)

    blocked = first.rows[0]
    assert type(blocked) is module.ResearchStrategyCrossDomainDecisionAuditRow
    assert blocked.stale_evidence_control_score == d("0.500000")
    assert blocked.conflict_control_score == d("0.350000")
    assert blocked.decision_audit_score == d("0.456500")
    assert blocked.weakest_dimension_score == d("0.350000")
    assert blocked.reason_codes == (
        "domain_conflict_observed",
        "evidence_trace_gap_observed",
        "memory_calibration_review_requested",
        "domain_quorum_block",
        "evidence_alignment_block",
        "decision_trace_watch",
        "resolution_readiness_watch",
        "stale_evidence_block",
        "cross_domain_conflict_block",
        "memory_calibration_block",
        "unresolved_blocker_block",
        "decision_audit_score_block",
    )

    watched = first.rows[1]
    assert watched.stale_evidence_control_score == d("0.750000")
    assert watched.conflict_control_score == d("0.700000")
    assert watched.decision_audit_score == d("0.717100")
    assert watched.reason_codes == (
        "domain_conflict_observed",
        "manual_review_requested",
        "domain_quorum_watch",
        "evidence_alignment_watch",
        "decision_trace_watch",
        "resolution_readiness_watch",
        "stale_evidence_watch",
        "cross_domain_conflict_watch",
        "memory_calibration_watch",
        "unresolved_blocker_watch",
        "decision_audit_score_watch",
    )

    passed = first.rows[2]
    assert passed.decision_audit_score == d("0.905100")
    assert passed.reason_codes == (
        "cross_domain_decision_ready",
        "cross_domain_decision_audit_pass",
    )

    reason_count_by_code = {
        item.reason_code: item for item in first.reason_code_counts
    }
    assert reason_count_by_code["domain_conflict_observed"] == (
        module.ResearchStrategyCrossDomainDecisionAuditReasonCodeCount(
            reason_code="domain_conflict_observed",
            count=d("2.000000"),
            row_ratio=d("0.666667"),
        )
    )

    payload = module.research_strategy_cross_domain_decision_audit_report_payload(first)
    assert payload == module.research_strategy_cross_domain_decision_audit_report_payload(
        second,
    )
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["row_count"] == "3.000000"
    assert payload["average_decision_audit_score"] == "0.692900"
    assert payload["rows"][0]["decision_audit_score"] == "0.456500"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    _assert_no_float_or_int_values(payload)

    serialized = json.dumps(payload, sort_keys=True)
    for raw_fragment in (
        "candidate_id",
        "market_id",
        "market_slug",
        "hidden",
        "question",
        "source_url",
        "source_text",
        "https://private",
        "wallet",
        "table",
        "token",
        "audit_item_ref",
    ):
        assert raw_fragment not in serialized

    assert module.research_strategy_cross_domain_decision_audit_report_digest(first) == (
        first.derived_validation_digest
    )


def test_empty_report_is_readonly_block() -> None:
    module = _module()
    report = _report(module, ())

    assert report.status == "block"
    assert report.row_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.average_decision_audit_score == ZERO
    assert report.min_decision_audit_score == ZERO
    assert report.reason_codes == ("empty_input",)
    assert report.rows == ()

    payload = module.research_strategy_cross_domain_decision_audit_report_payload(report)
    assert payload["rows"] == []
    assert payload["reason_code_counts"] == [
        {
            "reason_code": "empty_input",
            "count": "1.000000",
            "row_ratio": "1.000000",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]


def test_digest_validation_rejects_tampered_payloads() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_cross_domain_decision_audit_report_payload(report)

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_cross_domain_decision_audit_report_payload(tampered)

    tampered_status = dict(payload)
    tampered_status["status"] = "review"
    with pytest.raises(ValueError, match="status"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            tampered_status,
        )


def test_rejects_non_decimal_numbers_subclasses_bad_flags_and_future_times() -> None:
    module = _module()

    with pytest.raises(ValueError, match="Decimal"):
        _config(module, pass_min_audit_score=0.8)
    with pytest.raises(ValueError, match="weights must sum"):
        _config(module, domain_quorum_weight=d("0.320000"))
    with pytest.raises(ValueError, match="Decimal"):
        _input(module, domain_quorum_ratio=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="datetime"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 8, tzinfo=UTC))
    with pytest.raises(ValueError, match="string"):
        _input(module, audit_item_ref=_StringSubclass("private-ref"))
    with pytest.raises(ValueError, match="paper_only"):
        _input(module, paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            module,
            (_input(module, observed_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="unresolved_blocker_count"):
        _input(module, unresolved_blocker_count=d("1.500000"))


def test_dataclasses_are_frozen_and_do_not_support_subclassing() -> None:
    module = _module()
    report = _report(module, (_input(module),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):
        class _BadConfig(module.ResearchStrategyCrossDomainDecisionAuditConfig):
            pass


def test_dataclass_reconstruction_revalidates_score_reasons_and_config() -> None:
    module = _module()
    report = _report(module, (_input(module),))

    with pytest.raises(ValueError, match="validation_config"):
        replace(
            report.rows[0],
            decision_audit_score=d("0.800000"),
        )
    with pytest.raises(ValueError, match="validation_config"):
        replace(
            report.rows[0],
            status="watch",
            reason_codes=(
                "cross_domain_decision_ready",
                "decision_audit_score_watch",
            ),
        )

    custom_report = _report(
        module,
        (_input(module),),
        cfg=_config(
            module,
            domain_quorum_weight=d("0.230000"),
            evidence_alignment_weight=d("0.170000"),
        ),
    )
    with pytest.raises(ValueError, match="decision_audit_score"):
        replace(
            custom_report,
            config=_config(module),
            derived_validation_digest="",
        )


def test_payload_rejects_unsafe_public_surface_and_numeric_types() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_cross_domain_decision_audit_report_payload(report)

    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            {**payload, "source_url": "https://private.example/secret"},
        )
    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            {**payload, "row_count": 1},
        )


def test_payload_rejects_resigned_schema_and_consistency_tampering() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_cross_domain_decision_audit_report_payload(report)

    missing_required = json.loads(json.dumps(payload))
    missing_required.pop("row_count")
    with pytest.raises(ValueError, match="payload fields"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(missing_required),
        )

    extra_field = json.loads(json.dumps(payload))
    extra_field["note"] = "pass"
    with pytest.raises(ValueError, match="payload fields"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(extra_field),
        )

    missing_flag = json.loads(json.dumps(payload))
    missing_flag.pop("readonly")
    with pytest.raises(ValueError, match="payload fields"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(missing_flag),
        )

    inconsistent_count = json.loads(json.dumps(payload))
    inconsistent_count["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="row_count"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(inconsistent_count),
        )

    nested_extra_field = json.loads(json.dumps(payload))
    nested_extra_field["rows"][0]["note"] = "pass"
    with pytest.raises(ValueError, match=r"payload\.rows\[0\] fields"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(nested_extra_field),
        )

    nested_missing_flag = json.loads(json.dumps(payload))
    nested_missing_flag["reason_code_counts"][0].pop("report_only")
    with pytest.raises(
        ValueError,
        match=r"payload\.reason_code_counts\[0\] fields",
    ):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(nested_missing_flag),
        )

    future_observation = json.loads(json.dumps(payload))
    future_observation["rows"][0]["observed_at"] = (
        GENERATED_AT + timedelta(seconds=1)
    ).isoformat()
    with pytest.raises(ValueError, match="observed_at"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(future_observation),
        )


def test_payload_rejects_resigned_derived_score_tampering() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_cross_domain_decision_audit_report_payload(report)

    tampered = json.loads(json.dumps(payload))
    tampered["rows"][0]["decision_audit_score"] = "0.800000"
    tampered["average_decision_audit_score"] = "0.800000"
    tampered["min_decision_audit_score"] = "0.800000"

    with pytest.raises(ValueError, match="decision_audit_score"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(tampered),
        )


def test_rejects_signed_zero_in_dataclasses_and_resigned_payloads() -> None:
    module = _module()

    with pytest.raises(ValueError, match="negative zero"):
        _config(
            module,
            max_pass_unresolved_blocker_count=d("-0.000000"),
        )
    with pytest.raises(ValueError, match="negative zero"):
        _input(module, stale_evidence_ratio=d("-0.000000"))

    report = _report(module, (_input(module),))
    payload = module.research_strategy_cross_domain_decision_audit_report_payload(report)

    signed_zero_count = json.loads(json.dumps(payload))
    signed_zero_count["block_count"] = "-0.000000"
    with pytest.raises(ValueError, match="negative zero"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(signed_zero_count),
        )

    signed_zero_config = json.loads(json.dumps(payload))
    signed_zero_config["config"]["max_pass_unresolved_blocker_count"] = "-0.000000"
    with pytest.raises(ValueError, match="negative zero"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(signed_zero_config),
        )


def test_payload_round_trips_custom_config_and_revalidates_with_it() -> None:
    module = _module()
    cfg = _config(
        module,
        domain_quorum_weight=d("0.230000"),
        evidence_alignment_weight=d("0.170000"),
    )
    report = _report(module, (_input(module),), cfg=cfg)

    payload = module.research_strategy_cross_domain_decision_audit_report_payload(report)

    assert payload["config"]["domain_quorum_weight"] == "0.230000"
    assert payload["config"]["evidence_alignment_weight"] == "0.170000"
    assert payload["rows"][0]["decision_audit_score"] == "0.905600"

    tampered = json.loads(json.dumps(payload))
    tampered["config"]["domain_quorum_weight"] = "0.220000"
    tampered["config"]["evidence_alignment_weight"] = "0.180000"
    with pytest.raises(ValueError, match="decision_audit_score"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(tampered),
        )


def test_payload_rejects_nested_json_container_subclasses() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_cross_domain_decision_audit_report_payload(report)

    rows_subclass = dict(payload)
    rows_subclass["rows"] = _ListSubclass(payload["rows"])
    with pytest.raises(ValueError, match="JSON array"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(rows_subclass),
        )

    row_subclass = json.loads(json.dumps(payload))
    row_subclass["rows"][0] = _DictSubclass(row_subclass["rows"][0])
    with pytest.raises(ValueError, match="JSON object"):
        module.research_strategy_cross_domain_decision_audit_report_payload(
            _resign_payload(row_subclass),
        )


def test_report_contract_static_safety_and_decimal_only_payloads() -> None:
    module = _module()
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "web3",
        "ccxt",
        "subprocess",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom):
            root = "" if node.module is None else node.module.split(".", 1)[0]
            assert root not in forbidden_import_roots

    cfg = _config(module)
    row_input = _input(module)
    report = _report(module, (row_input,))
    for value in (cfg, row_input, report, report.rows[0], report.reason_code_counts[0]):
        assert is_dataclass(value)
        _assert_decimal_numeric_fields(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True

    payload = module.research_strategy_cross_domain_decision_audit_report_payload(report)
    _assert_no_float_or_int_values(payload)
    for field in fields(module.ResearchStrategyCrossDomainDecisionAuditReport):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        if field.name.endswith(("_count", "_score", "_weight", "_ratio")):
            assert type(getattr(report, field.name)) is Decimal

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
