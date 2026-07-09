from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_team_domain_edge_decay_router_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_team_domain_edge_decay_router_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 14, 0, tzinfo=UTC)
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
    assert spec is not None, "team-domain edge decay router report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ),
        "fresh_edge_age_seconds": d("86400.000000"),
        "stale_edge_age_seconds": d("604800.000000"),
        "min_pass_decay_adjusted_edge_score": d("0.650000"),
        "min_watch_decay_adjusted_edge_score": d("0.450000"),
        "min_pass_domain_fit_score": d("0.700000"),
        "min_watch_domain_fit_score": d("0.500000"),
        "min_pass_team_capacity_score": d("0.700000"),
        "min_watch_team_capacity_score": d("0.500000"),
        "min_pass_evidence_freshness_score": d("0.700000"),
        "min_watch_evidence_freshness_score": d("0.500000"),
        "max_pass_decay_pressure_score": d("0.200000"),
        "max_watch_decay_pressure_score": d("0.450000"),
    }
    values.update(overrides)
    return module.ResearchStrategyTeamDomainEdgeDecayRouterConfig(**values)


def _input(module: Any, route_ref: str = "route-alpha", **overrides: object) -> Any:
    values = {
        "route_ref": route_ref,
        "evaluated_at": GENERATED_AT - timedelta(minutes=30),
        "last_edge_observed_at": GENERATED_AT - timedelta(hours=12),
        "baseline_edge_score": d("1.000000"),
        "current_edge_score": d("0.900000"),
        "domain_fit_score": d("0.850000"),
        "team_capacity_score": d("0.880000"),
        "evidence_freshness_score": d("0.900000"),
        "decay_pressure_score": d("0.100000"),
        "reason_codes": ("edge_router_review_ready",),
    }
    values.update(overrides)
    return module.ResearchStrategyTeamDomainEdgeDecayRouterInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_team_domain_edge_decay_router_report(
        rows,
        generated_at=generated_at,
        config=cfg or _config(module),
    )


def _walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for key, item in value.items():
            nested.append(key)
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
        if field.name.endswith(
            (
                "_count",
                "_ratio",
                "_score",
                "_seconds",
                "_pressure",
                "_number",
            ),
        ):
            assert type(item) is Decimal


def test_builds_pass_watch_and_block_edge_decay_router_rows() -> None:
    module = _module()
    summary = _report(
        module,
        (
            _input(
                module,
                "candidate=alpha&market_id=secret&market_slug=hidden-question",
            ),
            _input(
                module,
                "route-watch",
                last_edge_observed_at=GENERATED_AT - timedelta(days=3),
                baseline_edge_score=d("0.960000"),
                current_edge_score=d("0.720000"),
                domain_fit_score=d("0.660000"),
                team_capacity_score=d("0.650000"),
                evidence_freshness_score=d("0.620000"),
                decay_pressure_score=d("0.300000"),
                reason_codes=("domain_router_review_requested",),
            ),
            _input(
                module,
                "route-block",
                last_edge_observed_at=GENERATED_AT - timedelta(days=9),
                baseline_edge_score=d("1.000000"),
                current_edge_score=d("0.500000"),
                domain_fit_score=d("0.420000"),
                team_capacity_score=d("0.350000"),
                evidence_freshness_score=d("0.400000"),
                decay_pressure_score=d("0.700000"),
                reason_codes=("team_capacity_review_requested",),
            ),
        ),
    )

    assert module.RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(summary)
    assert type(summary) is module.ResearchStrategyTeamDomainEdgeDecayRouterReport
    assert summary.status == "block"
    assert summary.row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_decay_adjusted_edge_score == d("0.475000")
    assert summary.lowest_decay_adjusted_edge_score == d("0.000000")
    assert summary.highest_edge_decay_ratio == d("0.500000")
    assert summary.highest_edge_age_seconds == d("777600.000000")
    assert summary.highest_decay_pressure_score == d("0.700000")
    assert summary.lowest_domain_fit_score == d("0.420000")
    assert summary.lowest_team_capacity_score == d("0.350000")
    assert summary.lowest_evidence_freshness_score == d("0.400000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked = summary.rows[0]
    assert type(blocked) is module.ResearchStrategyTeamDomainEdgeDecayRouterRow
    assert blocked.aggregate_row_number == d("1.000000")
    assert blocked.edge_age_seconds == d("777600.000000")
    assert blocked.edge_age_pressure == d("1.000000")
    assert blocked.edge_decay_ratio == d("0.500000")
    assert blocked.decay_adjusted_edge_score == d("0.000000")
    assert blocked.reason_codes == (
        "team_capacity_review_requested",
        "adjusted_edge_block",
        "decay_pressure_block",
        "domain_fit_block",
        "edge_age_block",
        "edge_decay_block",
        "evidence_freshness_block",
        "team_capacity_block",
    )

    watched = summary.rows[1]
    assert watched.aggregate_row_number == d("2.000000")
    assert watched.edge_age_pressure == d("0.333333")
    assert watched.edge_decay_ratio == d("0.250000")
    assert watched.decay_adjusted_edge_score == d("0.508000")
    assert watched.reason_codes == (
        "domain_router_review_requested",
        "adjusted_edge_watch",
        "decay_pressure_watch",
        "domain_fit_watch",
        "edge_age_watch",
        "edge_decay_watch",
        "evidence_freshness_watch",
        "team_capacity_watch",
    )

    passed = summary.rows[2]
    assert passed.aggregate_row_number == d("3.000000")
    assert passed.edge_age_pressure == d("0.000000")
    assert passed.edge_decay_ratio == d("0.100000")
    assert passed.decay_adjusted_edge_score == d("0.917000")
    assert passed.reason_codes == ("edge_decay_router_pass", "edge_router_review_ready")
    assert len(passed.route_digest) == 71
    assert passed.route_digest.startswith("sha256:")
    assert len(passed.derived_validation_digest) == 64

    reason_count_by_code = {
        item.reason_code: item for item in summary.reason_code_counts
    }
    assert reason_count_by_code["edge_age_watch"].count == d("1.000000")
    assert reason_count_by_code["edge_decay_router_pass"].row_ratio == d("0.333333")


def test_empty_report_blocks_without_public_rows() -> None:
    module = _module()
    summary = _report(module, ())

    assert summary.status == "block"
    assert summary.row_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == (
        "edge_decay_router_report_block",
        "edge_decay_router_no_inputs",
    )
    assert summary.reason_code_counts == (
        module.ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount(
            reason_code="edge_decay_router_no_inputs",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )


def test_payload_is_deterministic_digest_guarded_and_sanitized() -> None:
    module = _module()
    sensitive_ref = (
        "candidate=abc market_id=pm-123 market_slug=hidden-question "
        "source_url=https://private.invalid/path source_text=raw table=events "
        "dsn=postgres://secret token=hidden wallet=0xabc order=buy trade=live"
    )
    rows = (
        _input(module, "route-b", decay_pressure_score=d("0.700000")),
        _input(module, sensitive_ref),
        _input(module, "route-a", domain_fit_score=d("0.650000")),
    )

    report_a = _report(module, rows)
    report_b = _report(module, tuple(reversed(rows)))
    payload_a = module.research_strategy_team_domain_edge_decay_router_report_payload(
        report_a,
    )
    payload_b = module.research_strategy_team_domain_edge_decay_router_report_payload(
        report_b,
    )
    rendered = json.dumps(payload_a, sort_keys=True).casefold()

    assert payload_a == report_a.payload
    assert payload_a == payload_b
    assert payload_a["row_count"] == "3.000000"
    assert payload_a["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload_a["rows"][0]["route_digest"].startswith("sha256:")
    assert payload_a["rows"][0]["decay_adjusted_edge_score"] == "0.630000"
    assert payload_a["derived_validation_digest"] == report_a.derived_validation_digest
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert module.research_strategy_team_domain_edge_decay_router_report_digest(
        report_a,
    ) == report_a.derived_validation_digest
    assert not any(
        type(value) in (int, float, Decimal) for value in _walk_values(payload_a)
    )

    for leaked in (
        "candidate",
        "market_id",
        "market_slug",
        "hidden-question",
        "source_url",
        "source_text",
        "https://",
        "raw",
        "table",
        "dsn",
        "postgres://",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(report_a)).casefold()

    tampered = dict(payload_a)
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_team_domain_edge_decay_router_report_payload(tampered)


def test_decimal_exactness_frozen_dataclasses_and_validation_guards() -> None:
    module = _module()

    assert is_dataclass(module.ResearchStrategyTeamDomainEdgeDecayRouterConfig)
    assert is_dataclass(module.ResearchStrategyTeamDomainEdgeDecayRouterInput)
    assert is_dataclass(module.ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyTeamDomainEdgeDecayRouterRow)
    assert is_dataclass(module.ResearchStrategyTeamDomainEdgeDecayRouterReport)

    cfg = _config(module)
    source_row = _input(module)
    summary = _report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.current_edge_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        _config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="fresh_edge_age_seconds"):
        _config(module, fresh_edge_age_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_pass_domain_fit_score"):
        _config(module, min_pass_domain_fit_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="min_pass_domain_fit_score"):
        _config(module, min_pass_domain_fit_score=d("0.400000"))
    with pytest.raises(ValueError, match="max_pass_decay_pressure_score"):
        _config(module, max_pass_decay_pressure_score=d("0.800000"))
    with pytest.raises(ValueError, match="route_ref"):
        _input(module, _StringSubclass("route-alpha"))
    with pytest.raises(ValueError, match="route_ref"):
        _input(module, " ")
    with pytest.raises(ValueError, match="current_edge_score"):
        _input(module, current_edge_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_fit_score"):
        _input(module, domain_fit_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="evaluated_at"):
        _input(module, evaluated_at=_DatetimeSubclass(2026, 7, 9, 13, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        _report(module, (), generated_at=datetime(2026, 7, 9, 14, 0))
    with pytest.raises(ValueError, match="config"):
        _report(module, (), cfg=object())
    with pytest.raises(ValueError, match="inputs"):
        _report(module, (object(),))
    with pytest.raises(ValueError, match="evaluated_at"):
        _report(
            module,
            (_input(module, evaluated_at=GENERATED_AT + timedelta(seconds=1)),),
        )


def test_public_payload_rejects_forbidden_surfaces_statuses_and_flags() -> None:
    module = _module()
    payload = module.research_strategy_team_domain_edge_decay_router_report_payload(
        _report(module, (_input(module),)),
    )

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_team_domain_edge_decay_router_report_payload(
            tampered_status,
        )

    tampered_field = dict(payload)
    tampered_field["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_team_domain_edge_decay_router_report_payload(
            tampered_field,
        )

    tampered_value = dict(payload)
    tampered_value["reason_codes"] = ["source_text_copied_from_url"]
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_team_domain_edge_decay_router_report_payload(
            tampered_value,
        )

    with pytest.raises(ValueError, match="paper_only"):
        _config(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _input(module, report_only=False)

    summary = _report(module, (_input(module),))
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(summary.rows[0], status="watch")
    with pytest.raises(ValueError, match="route_digest"):
        replace(summary.rows[0], route_digest="candidate-market")


def test_public_numeric_fields_are_decimals_and_scope_is_readonly() -> None:
    module = _module()
    source_row = _input(module)
    summary = _report(module, (source_row,))

    _assert_decimal_numeric_fields(source_row)
    _assert_decimal_numeric_fields(summary)
    _assert_decimal_numeric_fields(summary.rows[0])
    _assert_decimal_numeric_fields(summary.reason_code_counts[0])

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_TEAM_DOMAIN_EDGE_DECAY_ROUTER_STATUSES",
        "ResearchStrategyTeamDomainEdgeDecayRouterConfig",
        "ResearchStrategyTeamDomainEdgeDecayRouterInput",
        "ResearchStrategyTeamDomainEdgeDecayRouterReasonCodeCount",
        "ResearchStrategyTeamDomainEdgeDecayRouterReport",
        "ResearchStrategyTeamDomainEdgeDecayRouterRow",
        "build_research_strategy_team_domain_edge_decay_router_report",
        "research_strategy_team_domain_edge_decay_router_report_digest",
        "research_strategy_team_domain_edge_decay_router_report_payload",
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
