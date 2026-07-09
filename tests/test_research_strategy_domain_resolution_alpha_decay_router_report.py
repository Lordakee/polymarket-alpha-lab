from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_domain_resolution_alpha_decay_router_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_domain_resolution_alpha_decay_router_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "domain resolution alpha decay router report module is missing"
    return importlib.import_module(MODULE_NAME)


def config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_REPORT_CONFIG_VERSION
        ),
        "fresh_resolution_age_seconds": d("3600.000000"),
        "stale_resolution_age_seconds": d("86400.000000"),
        "min_pass_router_score": d("0.700000"),
        "min_watch_router_score": d("0.500000"),
        "max_pass_alpha_decay_ratio": d("0.200000"),
        "max_watch_alpha_decay_ratio": d("0.450000"),
        "max_pass_resolution_age_pressure": d("0.200000"),
        "max_watch_resolution_age_pressure": d("0.750000"),
        "min_pass_resolution_confidence_score": d("0.750000"),
        "min_watch_resolution_confidence_score": d("0.500000"),
        "min_pass_domain_reliability_score": d("0.700000"),
        "min_watch_domain_reliability_score": d("0.500000"),
        "max_pass_decay_pressure_score": d("0.200000"),
        "max_watch_decay_pressure_score": d("0.450000"),
        "alpha_retention_weight": d("0.300000"),
        "resolution_confidence_weight": d("0.250000"),
        "domain_reliability_weight": d("0.200000"),
        "freshness_weight": d("0.150000"),
        "decay_relief_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainResolutionAlphaDecayRouterConfig(**values)


def router_input(
    module: Any,
    route_ref: str = "domain-resolution-route-alpha",
    **overrides: object,
) -> Any:
    values = {
        "route_ref": route_ref,
        "evaluated_at": GENERATED_AT - timedelta(minutes=10),
        "last_resolution_observed_at": GENERATED_AT - timedelta(minutes=30),
        "baseline_alpha_score": d("0.100000"),
        "current_alpha_score": d("0.095000"),
        "resolution_confidence_score": d("0.900000"),
        "domain_reliability_score": d("0.880000"),
        "decay_pressure_score": d("0.100000"),
        "reason_codes": ("domain_resolution_alpha_ready",),
    }
    values.update(overrides)
    return module.ResearchStrategyDomainResolutionAlphaDecayRouterInput(**values)


def report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_domain_resolution_alpha_decay_router_report(
        rows,
        config=cfg or config(module),
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for key, item in value.items():
            values.append(key)
            values.extend(walk_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_values(item))
        return tuple(values)
    return (value,)


def assert_public_numeric_fields_are_decimals(value: object) -> None:
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
                "_weight",
            ),
        ):
            assert type(item) is Decimal


def test_builds_pass_watch_and_block_domain_resolution_alpha_decay_rows() -> None:
    module = api()
    summary = report(
        module,
        (
            router_input(
                module,
                "candidate=abc market_id=pm-123 market_slug=hidden-question",
            ),
            router_input(
                module,
                "domain-resolution-watch",
                last_resolution_observed_at=GENERATED_AT - timedelta(hours=12, minutes=30),
                current_alpha_score=d("0.075000"),
                resolution_confidence_score=d("0.620000"),
                domain_reliability_score=d("0.640000"),
                decay_pressure_score=d("0.300000"),
                reason_codes=("domain_resolution_recheck_requested",),
            ),
            router_input(
                module,
                "domain-resolution-block",
                last_resolution_observed_at=GENERATED_AT - timedelta(days=2),
                current_alpha_score=d("0.040000"),
                resolution_confidence_score=d("0.450000"),
                domain_reliability_score=d("0.420000"),
                decay_pressure_score=d("0.700000"),
                reason_codes=("alpha_decay_review_requested",),
            ),
        ),
    )

    assert module.RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(summary)
    assert type(summary) is module.ResearchStrategyDomainResolutionAlphaDecayRouterReport
    assert summary.status == "block"
    assert summary.row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_router_score == d("0.641833")
    assert summary.lowest_router_score == d("0.346500")
    assert summary.highest_alpha_decay_ratio == d("0.600000")
    assert summary.highest_resolution_age_seconds == d("172800.000000")
    assert summary.lowest_resolution_confidence_score == d("0.450000")
    assert summary.lowest_domain_reliability_score == d("0.420000")
    assert summary.highest_decay_pressure_score == d("0.700000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked = summary.rows[0]
    assert type(blocked) is module.ResearchStrategyDomainResolutionAlphaDecayRouterRow
    assert blocked.aggregate_row_number == d("1.000000")
    assert blocked.resolution_age_seconds == d("172800.000000")
    assert blocked.resolution_age_pressure == d("1.000000")
    assert blocked.alpha_decay_ratio == d("0.600000")
    assert blocked.alpha_retention_score == d("0.400000")
    assert blocked.freshness_score == d("0.000000")
    assert blocked.decay_relief_score == d("0.300000")
    assert blocked.router_score == d("0.346500")
    assert blocked.reason_codes == (
        "alpha_decay_review_requested",
        "domain_resolution_alpha_decay_router_score_block",
        "domain_resolution_alpha_decay_block",
        "domain_resolution_age_block",
        "domain_resolution_confidence_block",
        "domain_reliability_block",
        "domain_resolution_decay_pressure_block",
    )

    watched = summary.rows[1]
    assert watched.aggregate_row_number == d("2.000000")
    assert watched.resolution_age_pressure == d("0.500000")
    assert watched.alpha_decay_ratio == d("0.250000")
    assert watched.router_score == d("0.653000")
    assert watched.reason_codes == (
        "domain_resolution_recheck_requested",
        "domain_resolution_alpha_decay_router_score_watch",
        "domain_resolution_alpha_decay_watch",
        "domain_resolution_age_watch",
        "domain_resolution_confidence_watch",
        "domain_reliability_watch",
        "domain_resolution_decay_pressure_watch",
    )

    passed = summary.rows[2]
    assert passed.aggregate_row_number == d("3.000000")
    assert passed.resolution_age_pressure == d("0.000000")
    assert passed.alpha_decay_ratio == d("0.050000")
    assert passed.router_score == d("0.926000")
    assert passed.reason_codes == (
        "domain_resolution_alpha_decay_router_pass",
        "domain_resolution_alpha_ready",
    )
    assert passed.route_digest.startswith("sha256:")
    assert len(passed.route_digest) == 71
    assert len(passed.derived_validation_digest) == 64

    reason_count_by_code = {
        item.reason_code: item for item in summary.reason_code_counts
    }
    assert reason_count_by_code["domain_resolution_age_watch"].count == d("1.000000")
    assert reason_count_by_code["domain_resolution_age_watch"].row_ratio == d("0.333333")


def test_empty_report_blocks_without_public_rows() -> None:
    module = api()
    summary = report(module, ())

    assert summary.status == "block"
    assert summary.row_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == (
        "domain_resolution_alpha_decay_router_report_block",
        "domain_resolution_alpha_decay_router_no_inputs",
    )
    assert summary.reason_code_counts == (
        module.ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount(
            reason_code="domain_resolution_alpha_decay_router_no_inputs",
            count=d("1.000000"),
            row_ratio=d("1.000000"),
        ),
    )


def test_payload_is_deterministic_digest_guarded_and_sanitized() -> None:
    module = api()
    sensitive_ref = (
        "candidate=abc market_id=pm-123 market_slug=hidden-question "
        "market_question=secret source_url=https://private.invalid/path "
        "source_text=raw table=events dsn=postgres://secret token=hidden "
        "wallet=0xabc order=buy trade=live sizing=recommendation"
    )
    rows = (
        router_input(module, "domain-route-b", decay_pressure_score=d("0.700000")),
        router_input(module, sensitive_ref),
        router_input(module, "domain-route-a", domain_reliability_score=d("0.620000")),
    )

    report_a = report(module, rows)
    report_b = report(module, tuple(reversed(rows)))
    payload_a = module.research_strategy_domain_resolution_alpha_decay_router_report_payload(
        report_a,
    )
    payload_b = module.research_strategy_domain_resolution_alpha_decay_router_report_payload(
        report_b,
    )
    rendered = json.dumps(payload_a, sort_keys=True).casefold()

    assert payload_a == report_a.payload
    assert payload_a == report_a.public_payload
    assert payload_a == payload_b
    assert payload_a["row_count"] == "3.000000"
    assert payload_a["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload_a["rows"][0]["route_digest"].startswith("sha256:")
    assert payload_a["derived_validation_digest"] == report_a.derived_validation_digest
    assert report_a.derived_validation_digest == report_b.derived_validation_digest
    assert (
        module.research_strategy_domain_resolution_alpha_decay_router_report_digest(report_a)
        == report_a.derived_validation_digest
    )
    module.validate_research_strategy_domain_resolution_alpha_decay_router_report_digest(
        payload_a,
    )
    assert payload_a["derived_validation_digest"] == canonical_digest(payload_a)
    assert not any(type(value) in (int, float, Decimal) for value in walk_values(payload_a))

    for leaked in (
        "candidate",
        "market_id",
        "market_slug",
        "hidden-question",
        "market_question",
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
        "sizing",
        "recommendation",
    ):
        assert leaked not in rendered
        assert leaked not in repr(asdict(report_a)).casefold()

    tampered = dict(payload_a)
    tampered["row_count"] = "4.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_domain_resolution_alpha_decay_router_report_payload(
            tampered,
        )


def test_decimal_exactness_frozen_dataclasses_and_validation_guards() -> None:
    module = api()

    assert is_dataclass(module.ResearchStrategyDomainResolutionAlphaDecayRouterConfig)
    assert is_dataclass(module.ResearchStrategyDomainResolutionAlphaDecayRouterInput)
    assert is_dataclass(module.ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyDomainResolutionAlphaDecayRouterRow)
    assert is_dataclass(module.ResearchStrategyDomainResolutionAlphaDecayRouterReport)

    cfg = config(module)
    source_row = router_input(module)
    summary = report(module, (source_row,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.current_alpha_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="fresh_resolution_age_seconds"):
        config(module, fresh_resolution_age_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_pass_router_score"):
        config(module, min_pass_router_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="min_pass_router_score"):
        config(module, min_pass_router_score=d("0.400000"))
    with pytest.raises(ValueError, match="max_pass_decay_pressure_score"):
        config(module, max_pass_decay_pressure_score=d("0.800000"))
    with pytest.raises(ValueError, match="route_ref"):
        router_input(module, _StringSubclass("domain-resolution-route-alpha"))
    with pytest.raises(ValueError, match="route_ref"):
        router_input(module, " ")
    with pytest.raises(ValueError, match="current_alpha_score"):
        router_input(module, current_alpha_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="domain_reliability_score"):
        router_input(module, domain_reliability_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="evaluated_at"):
        router_input(module, evaluated_at=_DatetimeSubclass(2026, 7, 9, 15, 50, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        report(module, (), generated_at=datetime(2026, 7, 9, 16, 0))
    with pytest.raises(ValueError, match="config"):
        report(module, (), cfg=object())
    with pytest.raises(ValueError, match="inputs"):
        report(module, (object(),))
    with pytest.raises(ValueError, match="evaluated_at"):
        report(
            module,
            (router_input(module, evaluated_at=GENERATED_AT + timedelta(seconds=1)),),
        )


def test_public_payload_rejects_forbidden_surfaces_statuses_flags_and_raw_numerics() -> None:
    module = api()
    payload = module.research_strategy_domain_resolution_alpha_decay_router_report_payload(
        report(module, (router_input(module),)),
    )

    tampered_status = dict(payload)
    tampered_status["status"] = "blocked"
    with pytest.raises(ValueError, match="pass, watch, or block"):
        module.research_strategy_domain_resolution_alpha_decay_router_report_payload(
            tampered_status,
        )

    tampered_field = dict(payload)
    tampered_field["market_slug"] = "hidden"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_strategy_domain_resolution_alpha_decay_router_report_payload(
            tampered_field,
        )

    tampered_value = dict(payload)
    tampered_value["reason_codes"] = ["source_text_copied_from_url"]
    with pytest.raises(ValueError, match="unsafe public value"):
        module.research_strategy_domain_resolution_alpha_decay_router_report_payload(
            tampered_value,
        )

    tampered_numeric = dict(payload)
    tampered_numeric["row_count"] = 3
    with pytest.raises(ValueError, match="raw numeric"):
        module.research_strategy_domain_resolution_alpha_decay_router_report_payload(
            tampered_numeric,
        )

    with pytest.raises(ValueError, match="paper_only"):
        config(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        router_input(module, report_only=False)

    summary = report(module, (router_input(module),))
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(summary, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(summary.rows[0], status="watch")
    with pytest.raises(ValueError, match="route_digest"):
        replace(summary.rows[0], route_digest="candidate-market")


def test_public_numeric_fields_are_decimals_and_module_scope_is_readonly() -> None:
    module = api()
    source_row = router_input(module)
    summary = report(module, (source_row,))

    assert_public_numeric_fields_are_decimals(config(module))
    assert_public_numeric_fields_are_decimals(source_row)
    assert_public_numeric_fields_are_decimals(summary)
    assert_public_numeric_fields_are_decimals(summary.rows[0])
    assert_public_numeric_fields_are_decimals(summary.reason_code_counts[0])

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_DOMAIN_RESOLUTION_ALPHA_DECAY_ROUTER_STATUSES",
        "ResearchStrategyDomainResolutionAlphaDecayRouterConfig",
        "ResearchStrategyDomainResolutionAlphaDecayRouterInput",
        "ResearchStrategyDomainResolutionAlphaDecayRouterReasonCodeCount",
        "ResearchStrategyDomainResolutionAlphaDecayRouterReport",
        "ResearchStrategyDomainResolutionAlphaDecayRouterRow",
        "build_research_strategy_domain_resolution_alpha_decay_router_report",
        "research_strategy_domain_resolution_alpha_decay_router_report_digest",
        "research_strategy_domain_resolution_alpha_decay_router_report_payload",
        "validate_research_strategy_domain_resolution_alpha_decay_router_report_digest",
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
        "urllib",
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
