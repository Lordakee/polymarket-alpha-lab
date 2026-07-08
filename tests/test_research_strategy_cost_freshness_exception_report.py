from __future__ import annotations

import ast
import hashlib
import inspect
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_cost_freshness_exception_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_COST_FRESHNESS_EXCEPTION_REPORT_CONFIG_VERSION
        ),
        "max_pass_fee_observation_age_seconds": d("3600.000000"),
        "max_watch_fee_observation_age_seconds": d("14400.000000"),
        "max_pass_spread_observation_age_seconds": d("300.000000"),
        "max_watch_spread_observation_age_seconds": d("1200.000000"),
        "max_pass_slippage_assumption_age_seconds": d("86400.000000"),
        "max_watch_slippage_assumption_age_seconds": d("259200.000000"),
        "max_pass_settlement_friction_age_seconds": d("604800.000000"),
        "max_watch_settlement_friction_age_seconds": d("1209600.000000"),
        "max_pass_stale_cost_pressure": d("0.300000"),
        "max_watch_stale_cost_pressure": d("0.700000"),
        "max_pass_manual_recheck_urgency": d("0.300000"),
        "max_watch_manual_recheck_urgency": d("0.700000"),
    }
    values.update(overrides)
    return module.ResearchStrategyCostFreshnessExceptionConfig(**values)


def cost_input(
    aggregation_key: str = "private-row-alpha",
    *,
    fee_observation_age_seconds: Decimal = d("1800.000000"),
    spread_observation_age_seconds: Decimal = d("120.000000"),
    slippage_assumption_age_seconds: Decimal = d("43200.000000"),
    settlement_friction_age_seconds: Decimal = d("302400.000000"),
    stale_cost_pressure: Decimal = d("0.100000"),
    manual_recheck_urgency: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyCostFreshnessExceptionInput(
        aggregation_key=aggregation_key,
        fee_observation_age_seconds=fee_observation_age_seconds,
        spread_observation_age_seconds=spread_observation_age_seconds,
        slippage_assumption_age_seconds=slippage_assumption_age_seconds,
        settlement_friction_age_seconds=settlement_friction_age_seconds,
        stale_cost_pressure=stale_cost_pressure,
        manual_recheck_urgency=manual_recheck_urgency,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*items: object, generated_at: datetime = GENERATED_AT, cfg=None):
    module = api()
    return module.build_research_strategy_cost_freshness_exception_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_manual_cost_freshness_exception_review() -> None:
    module = api()
    summary = report()

    assert module.RESEARCH_STRATEGY_COST_FRESHNESS_EXCEPTION_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_COST_FRESHNESS_EXCEPTION_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_COST_FRESHNESS_EXCEPTION_STATUSES",
        "ResearchStrategyCostFreshnessExceptionConfig",
        "ResearchStrategyCostFreshnessExceptionInput",
        "ResearchStrategyCostFreshnessExceptionReasonCodeCount",
        "ResearchStrategyCostFreshnessExceptionRow",
        "ResearchStrategyCostFreshnessExceptionReport",
        "build_research_strategy_cost_freshness_exception_report",
        "research_strategy_cost_freshness_exception_report_payload",
        "research_strategy_cost_freshness_exception_report_digest",
    )
    assert type(summary) is module.ResearchStrategyCostFreshnessExceptionReport
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert (
        summary.config_version
        == "research-strategy-cost-freshness-exception-report-v0"
    )
    assert summary.input_row_count == ZERO
    assert summary.pass_count == ZERO
    assert summary.watch_count == ZERO
    assert summary.block_count == ZERO
    assert summary.mean_fee_observation_age_seconds == ZERO
    assert summary.mean_spread_observation_age_seconds == ZERO
    assert summary.mean_slippage_assumption_age_seconds == ZERO
    assert summary.mean_settlement_friction_age_seconds == ZERO
    assert summary.max_stale_cost_pressure == ZERO
    assert summary.max_manual_recheck_urgency == ZERO
    assert summary.mean_cost_freshness_exception_score == ZERO
    assert summary.status == "block"
    assert summary.reason_codes == ("cost_freshness_exception_report_empty",)
    assert summary.reason_code_counts == ()
    assert summary.rows == ()
    assert len(summary.derived_validation_digest) == 64
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_report_aggregates_cost_age_exceptions_into_pass_watch_and_block() -> None:
    summary = report(
        cost_input(
            "raw-candidate-id-should-only-appear-as-a-hash",
            fee_observation_age_seconds=d("20000.000000"),
            spread_observation_age_seconds=d("1800.000000"),
            slippage_assumption_age_seconds=d("400000.000000"),
            settlement_friction_age_seconds=d("1300000.000000"),
            stale_cost_pressure=d("0.900000"),
            manual_recheck_urgency=d("0.900000"),
        ),
        cost_input("private-row-pass"),
        cost_input(
            "private-row-watch",
            fee_observation_age_seconds=d("7200.000000"),
            spread_observation_age_seconds=d("600.000000"),
            slippage_assumption_age_seconds=d("129600.000000"),
            settlement_friction_age_seconds=d("907200.000000"),
            stale_cost_pressure=d("0.500000"),
            manual_recheck_urgency=d("0.500000"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.input_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_fee_observation_age_seconds == d("9666.666667")
    assert summary.mean_spread_observation_age_seconds == d("840.000000")
    assert summary.mean_slippage_assumption_age_seconds == d("190933.333333")
    assert summary.mean_settlement_friction_age_seconds == d("836533.333333")
    assert summary.max_stale_cost_pressure == d("0.900000")
    assert summary.max_manual_recheck_urgency == d("0.900000")
    assert summary.mean_cost_freshness_exception_score == d("0.439352")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "cost_freshness_exception_report_block",
        "fee_observation_age_exception",
        "spread_observation_age_exception",
        "slippage_assumption_age_exception",
        "settlement_friction_age_exception",
        "stale_cost_pressure_exception",
        "manual_recheck_urgency_exception",
    )

    blocked, watched, passed = summary.rows
    assert tuple(row.aggregate_row_number for row in summary.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")
    assert blocked.aggregate_hash == hashlib.sha256(
        b"raw-candidate-id-should-only-appear-as-a-hash",
    ).hexdigest()
    assert blocked.cost_freshness_exception_score == ZERO
    assert blocked.reason_codes == (
        "cost_freshness_exception_block",
        "fee_observation_age_block",
        "spread_observation_age_block",
        "slippage_assumption_age_block",
        "settlement_friction_age_block",
        "stale_cost_pressure_block",
        "manual_recheck_urgency_block",
    )
    assert watched.cost_freshness_exception_score == d("0.458333")
    assert watched.reason_codes == (
        "cost_freshness_exception_watch",
        "fee_observation_age_watch",
        "spread_observation_age_watch",
        "slippage_assumption_age_watch",
        "settlement_friction_age_watch",
        "stale_cost_pressure_watch",
        "manual_recheck_urgency_watch",
    )
    assert passed.cost_freshness_exception_score == d("0.859722")
    assert passed.reason_codes == ("cost_freshness_exception_pass",)

    counts = {item.reason_code: item for item in summary.reason_code_counts}
    assert counts["fee_observation_age_block"] == (
        api().ResearchStrategyCostFreshnessExceptionReasonCodeCount(
            reason_code="fee_observation_age_block",
            count=d("1.000000"),
            input_ratio=d("0.333333"),
        )
    )


def test_payload_is_deterministic_public_safe_decimal_stringed_and_digest_guarded() -> None:
    module = api()
    first = report(
        cost_input("private-row-z"),
        cost_input("private-row-a"),
    )
    second = report(
        cost_input("private-row-a"),
        cost_input("private-row-z"),
    )

    first_payload = module.research_strategy_cost_freshness_exception_report_payload(first)
    second_payload = module.research_strategy_cost_freshness_exception_report_payload(second)

    assert first_payload == second_payload
    assert module.research_strategy_cost_freshness_exception_report_digest(first) == (
        module.research_strategy_cost_freshness_exception_report_digest(second)
    )
    assert len(module.research_strategy_cost_freshness_exception_report_digest(first)) == 64
    assert first_payload["generated_at"] == "2026-07-08T16:00:00+00:00"
    assert first_payload["input_row_count"] == "2.000000"
    assert first_payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert len(first_payload["rows"][0]["aggregate_hash"]) == 64
    assert first_payload["rows"][0]["cost_freshness_exception_score"] == "0.859722"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(
        type(value) in (int, float, Decimal)
        for value in _walk_payload_values(first_payload)
    )

    payload_text = repr(first_payload).lower()
    forbidden_public_fragments = (
        "private-row",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
    )
    assert all(fragment not in payload_text for fragment in forbidden_public_fragments)

    tampered_payload = module.research_strategy_cost_freshness_exception_report_payload(
        report(cost_input()),
    )
    tampered_payload["rows"][0]["fee_observation_age_seconds"] = "999999.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_cost_freshness_exception_report_payload(tampered_payload)

    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_cost_freshness_exception_report_payload(
            {
                "market_id": "hidden",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_validation_rejects_non_decimal_bad_flags_bad_times_and_duplicates() -> None:
    module = api()
    summary = report(cost_input())
    row = summary.rows[0]

    for value in (config(), cost_input(), row, summary, *summary.reason_code_counts):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item_value is None or item.name in {
                "aggregation_key",
                "aggregate_hash",
                "config_version",
                "derived_validation_digest",
                "paper_only",
                "reason_codes",
                "reason_code_counts",
                "readonly",
                "report_only",
                "rows",
                "status",
            }:
                continue
            if any(
                token in item.name
                for token in ("age", "count", "number", "pressure", "ratio", "score", "urgency")
            ):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        row.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="fee_observation_age_seconds"):
        cost_input(fee_observation_age_seconds=1800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_observation_age_seconds"):
        cost_input(spread_observation_age_seconds=_DecimalSubclass("120.000000"))
    with pytest.raises(ValueError, match="stale_cost_pressure"):
        cost_input(stale_cost_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="manual_recheck_urgency"):
        cost_input(manual_recheck_urgency=-d("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(cost_input(), generated_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            cost_input(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(cost_input("same"), cost_input("same"))
    with pytest.raises(ValueError, match="max_pass_fee_observation_age_seconds"):
        config(max_pass_fee_observation_age_seconds=d("20000.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        cost_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            row,
            cost_freshness_exception_score=d("0.100000"),
            derived_validation_digest=row.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            input_row_count=d("2.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="report"):
        module.research_strategy_cost_freshness_exception_report_payload(object())


def test_owned_module_has_no_external_execution_or_private_public_surfaces() -> None:
    module = api()
    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }

    forbidden_terms = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "reco" + "mmendation",
        "siz" + "ing",
        "b" + "uy",
        "se" + "ll",
        "wal" + "let",
        "or" + "der",
        "li" + "ve",
        "trad" + "ing",
        "data" + "base",
        "net" + "work",
        "request",
        "socket",
        "subprocess",
        "open(",
        "connect(",
    )
    assert all(term not in source.lower() for term in forbidden_terms)

    forbidden_call_names = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_call_names


def _walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(_walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_walk_payload_values(item))
        return tuple(values)
    return (value,)
