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
    "research_strategy_cost_evidence_quorum_router_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_cost_evidence_quorum_router_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 14, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 13, 30, tzinfo=UTC)
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
    assert spec is not None, "quorum router report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_CONFIG_VERSION
        ),
        "pass_min_router_score": d("0.800000"),
        "watch_min_router_score": d("0.600000"),
        "max_pass_cost_pressure_score": d("0.250000"),
        "max_watch_cost_pressure_score": d("0.450000"),
        "min_pass_evidence_strength_score": d("0.800000"),
        "min_watch_evidence_strength_score": d("0.600000"),
        "min_pass_quorum_score": d("0.800000"),
        "min_watch_quorum_score": d("0.600000"),
        "min_pass_freshness_score": d("0.750000"),
        "min_watch_freshness_score": d("0.500000"),
        "cost_efficiency_weight": d("0.300000"),
        "evidence_strength_weight": d("0.300000"),
        "quorum_weight": d("0.250000"),
        "freshness_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCostEvidenceQuorumRouterConfig(**values)


def _input(module: Any, route_ref: str = "route-alpha", **overrides: object) -> Any:
    values = {
        "route_ref": route_ref,
        "cost_pressure_score": d("0.100000"),
        "evidence_strength_score": d("0.950000"),
        "quorum_score": d("0.900000"),
        "freshness_score": d("0.900000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("evidence_packet_available",),
    }
    values.update(overrides)
    return module.ResearchStrategyCostEvidenceQuorumRouterInput(**values)


def _note(module: Any, key: str = "review_scope", value: str | None = None) -> Any:
    return module.ResearchStrategyCostEvidenceQuorumRouterPublicNote(
        key=key,
        value=value or "cost evidence quorum routing report only",
    )


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
    public_notes: tuple[Any, ...] = (),
) -> Any:
    return module.build_research_strategy_cost_evidence_quorum_router_report(
        rows,
        generated_at=generated_at,
        config=cfg or _config(module),
        public_notes=public_notes,
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


def test_builds_pass_watch_and_block_router_rows() -> None:
    module = _module()
    report = _report(
        module,
        (
            _input(
                module,
                "raw-candidate-id/market-slug?token=hidden&wallet=private",
                reason_codes=("evidence_packet_available",),
            ),
            _input(
                module,
                "route-watch",
                cost_pressure_score=d("0.350000"),
                evidence_strength_score=d("0.700000"),
                quorum_score=d("0.650000"),
                freshness_score=d("0.650000"),
                reason_codes=("manual_review_requested",),
            ),
            _input(
                module,
                "route-block",
                cost_pressure_score=d("0.700000"),
                evidence_strength_score=d("0.450000"),
                quorum_score=d("0.400000"),
                freshness_score=d("0.300000"),
                reason_codes=("scope_reviewed", "manual_review_requested"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
        public_notes=(_note(module),),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyCostEvidenceQuorumRouterReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_CONFIG_VERSION
    )
    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_router_score == d("0.650000")
    assert report.min_router_score == d("0.370000")
    assert report.max_cost_pressure_score == d("0.700000")
    assert report.min_evidence_strength_score == d("0.450000")
    assert report.min_quorum_score == d("0.400000")
    assert report.min_freshness_score == d("0.300000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")

    blocked = report.rows[0]
    assert type(blocked) is module.ResearchStrategyCostEvidenceQuorumRouterRow
    assert blocked.cost_efficiency_score == d("0.300000")
    assert blocked.evidence_gap_score == d("0.550000")
    assert blocked.quorum_gap_score == d("0.600000")
    assert blocked.freshness_gap_score == d("0.700000")
    assert blocked.router_score == d("0.370000")
    assert blocked.reason_codes == (
        "scope_reviewed",
        "manual_review_requested",
        "cost_pressure_block",
        "evidence_strength_block",
        "quorum_block",
        "freshness_block",
        "router_score_block",
    )

    watched = report.rows[1]
    assert watched.router_score == d("0.665000")
    assert watched.reason_codes == (
        "manual_review_requested",
        "cost_pressure_watch",
        "evidence_strength_watch",
        "quorum_watch",
        "freshness_watch",
        "router_score_watch",
    )

    passed = report.rows[2]
    assert passed.router_score == d("0.915000")
    assert passed.reason_codes == (
        "evidence_packet_available",
        "router_ready_pass",
    )

    assert report.reason_code_counts[0] == (
        module.ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount(
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
    assert report.average_router_score == ZERO
    assert report.min_router_score == ZERO
    assert report.max_cost_pressure_score == ZERO
    assert report.min_evidence_strength_score == ZERO
    assert report.min_quorum_score == ZERO
    assert report.min_freshness_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("empty_input",)
    assert report.reason_code_counts == (
        module.ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount(
            reason_code="empty_input",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_payload_redacts_private_refs_serializes_decimals_and_validates_digest() -> None:
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

    payload = module.research_strategy_cost_evidence_quorum_router_report_payload(report)
    rendered = repr(payload).casefold()
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["row_count"] == "1.000000"
    assert payload["rows"][0]["router_score"] == "0.915000"
    assert payload["rows"][0]["route_digest"].startswith("sha256:")
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert module.validate_research_strategy_cost_evidence_quorum_router_report_digest(
        report,
    )
    assert module.validate_research_strategy_cost_evidence_quorum_router_report_payload(
        payload,
    )
    assert not any(isinstance(value, float) for value in _walk_values(payload))
    assert ": 1.0" not in encoded
    for leaked in (
        "raw-candidate-id",
        "market-slug",
        "market",
        "slug",
        "token",
        "hidden",
        "wallet",
        "private",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(report)).casefold()

    tampered = dict(payload)
    tampered["row_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_cost_evidence_quorum_router_report_payload(tampered)


def test_decimal_type_rejection_and_frozen_public_dataclasses() -> None:
    module = _module()

    assert is_dataclass(module.ResearchStrategyCostEvidenceQuorumRouterConfig)
    assert is_dataclass(module.ResearchStrategyCostEvidenceQuorumRouterInput)
    assert is_dataclass(module.ResearchStrategyCostEvidenceQuorumRouterPublicNote)
    assert is_dataclass(module.ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyCostEvidenceQuorumRouterRow)
    assert is_dataclass(module.ResearchStrategyCostEvidenceQuorumRouterReport)

    cfg = _config(module)
    source_row = _input(module)
    report = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.cost_pressure_score = d("0.200000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].router_score = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="pass_min_router_score"):
        _config(module, pass_min_router_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_min_router_score"):
        _config(module, watch_min_router_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_min_router_score"):
        _config(module, pass_min_router_score=d("0.500000"))
    with pytest.raises(ValueError, match="max_pass_cost_pressure_score"):
        _config(module, max_pass_cost_pressure_score=d("0.600000"))
    with pytest.raises(ValueError, match="router weights"):
        _config(module, cost_efficiency_weight=d("0.350000"))
    with pytest.raises(ValueError, match="route_ref"):
        _input(module, _StringSubclass("route-alpha"))
    with pytest.raises(ValueError, match="route_ref"):
        _input(module, " ")
    with pytest.raises(ValueError, match="cost_pressure_score"):
        _input(module, cost_pressure_score="0.100000")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_strength_score"):
        _input(module, evidence_strength_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="quorum_score"):
        _input(module, quorum_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="observed_at"):
        _input(module, observed_at=_DatetimeSubclass(2026, 7, 9, 13, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        _report(module, (), generated_at=datetime(2026, 7, 9, 14, 0))
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
                    observed_at=datetime(2026, 7, 9, 14, 1, tzinfo=UTC),
                ),
            ),
        )


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    (
        ("key", "source_url"),
        ("key", "wallet"),
        ("value", "https://example.test/source"),
        ("value", "raw source text copied here"),
        ("value", "buy or sell recommendation"),
        ("value", "wallet auth token"),
        ("value", "order trade position"),
        ("value", "database table dsn"),
    ),
)
def test_public_leak_rejection_for_notes(field_name: str, field_value: str) -> None:
    module = _module()
    values = {"key": "review_scope", "value": "cost evidence quorum routing report only"}
    values[field_name] = field_value
    with pytest.raises(ValueError, match="unsafe public"):
        module.ResearchStrategyCostEvidenceQuorumRouterPublicNote(**values)


def test_public_payload_rejects_forbidden_fields_values_and_statuses() -> None:
    module = _module()
    report = _report(module, (_input(module),))
    payload = module.research_strategy_cost_evidence_quorum_router_report_payload(report)
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
        "blocked",
    ):
        assert token not in rendered

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_cost_evidence_quorum_router_report_payload(
            tampered_status,
        )

    tampered_field = dict(payload)
    tampered_field["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_cost_evidence_quorum_router_report_payload(
            tampered_field,
        )

    tampered_value = dict(payload)
    tampered_value["public_notes"] = [
        {
            "key": "review_scope",
            "value": "source text copied here",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_cost_evidence_quorum_router_report_payload(
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
    with pytest.raises(ValueError, match="report_only"):
        module.ResearchStrategyCostEvidenceQuorumRouterPublicNote(
            key="review_scope",
            value="cost evidence quorum routing report only",
            report_only=False,
        )

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
        replace(passed, reason_codes=("router_ready_pass", "router_score_watch"))
    with pytest.raises(ValueError, match="router_score"):
        replace(passed, router_score=ZERO, validation_config=_config(module))
    with pytest.raises(ValueError, match="route_digest"):
        replace(passed, route_digest="raw-candidate-market")

    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = _report(
            module,
            (
                _input(module, "route-z", cost_pressure_score=d("0.700000")),
                _input(module, "route-a"),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_deterministic_payload_and_digest_independent_of_input_order() -> None:
    module = _module()
    rows = (
        _input(module, "route-c", cost_pressure_score=d("0.700000")),
        _input(module, "route-a"),
        _input(module, "route-b", evidence_strength_score=d("0.700000")),
    )
    notes = (_note(module),)

    report_a = _report(module, rows, public_notes=notes)
    report_b = _report(module, tuple(reversed(rows)), public_notes=notes)

    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_cost_evidence_quorum_router_report_payload(
        report_a,
    ) == module.research_strategy_cost_evidence_quorum_router_report_payload(report_b)

    tampered = module.research_strategy_cost_evidence_quorum_router_report_payload(
        report_a,
    )
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_strategy_cost_evidence_quorum_router_report_payload(
            tampered,
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
        "DEFAULT_RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_COST_EVIDENCE_QUORUM_ROUTER_REPORT_STATUSES",
        "ResearchStrategyCostEvidenceQuorumRouterConfig",
        "ResearchStrategyCostEvidenceQuorumRouterInput",
        "ResearchStrategyCostEvidenceQuorumRouterPublicNote",
        "ResearchStrategyCostEvidenceQuorumRouterReasonCodeCount",
        "ResearchStrategyCostEvidenceQuorumRouterReport",
        "ResearchStrategyCostEvidenceQuorumRouterRow",
        "build_research_strategy_cost_evidence_quorum_router_report",
        "research_strategy_cost_evidence_quorum_router_report_payload",
        "validate_research_strategy_cost_evidence_quorum_router_report_digest",
        "validate_research_strategy_cost_evidence_quorum_router_report_payload",
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

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
