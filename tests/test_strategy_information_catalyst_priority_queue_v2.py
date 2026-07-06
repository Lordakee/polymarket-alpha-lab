from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_information_catalyst_priority_queue_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 15, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 14, 50, tzinfo=UTC)
CONFIG_VERSION = "strategy-information-catalyst-priority-queue-v2-test"
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_information_catalyst_priority_queue_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "recency_boost_window_hours": d("6.000000"),
        "max_recency_boost": d("0.120000"),
        "low_confidence_floor": d("0.650000"),
        "max_low_confidence_penalty": d("0.250000"),
        "priority_score_floor": d("0.800000"),
        "watch_score_floor": d("0.600000"),
    }
    values.update(overrides)
    return module.StrategyInformationCatalystPriorityQueueV2Config(**values)


def catalyst(catalyst_id: str = "catalyst-alpha", **overrides: object):
    module = api()
    values = {
        "candidate_id": "candidate-alpha",
        "market_id": "market-alpha",
        "catalyst_id": catalyst_id,
        "catalyst_type": "official_update",
        "base_catalyst_score": d("0.720000"),
        "information_edge_score": d("0.720000"),
        "source_reliability_score": d("0.720000"),
        "resolution_clarity_score": d("0.720000"),
        "recency_age_hours": d("1.000000"),
        "confidence_score": d("0.850000"),
        "observed_at": OBSERVED_AT,
        "reason_codes": ("catalyst_evidence_ready",),
    }
    values.update(overrides)
    return module.StrategyInformationCatalystPriorityQueueV2Input(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_information_catalyst_priority_queue_v2_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_catalyst_priority_queue_scoring_recency_and_low_confidence_penalties() -> None:
    report = build_report(
        catalyst(
            "recent-priority",
            candidate_id="candidate-priority",
            recency_age_hours=d("1.000000"),
        ),
        catalyst(
            "stale-watch",
            candidate_id="candidate-watch",
            recency_age_hours=d("12.000000"),
        ),
        catalyst(
            "low-confidence",
            candidate_id="candidate-deferred",
            recency_age_hours=d("1.000000"),
            confidence_score=d("0.050000"),
        ),
        generated_at=datetime(2026, 7, 6, 10, 0, tzinfo=timezone(timedelta(hours=-5))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == CONFIG_VERSION
    assert report.catalyst_count == d("3.000000")
    assert report.priority_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.deferred_count == d("1.000000")
    assert report.status == "deferred"
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-priority",
        "candidate-watch",
        "candidate-deferred",
    )

    priority, watched, deferred = report.rows
    assert priority.recency_boost == d("0.100000")
    assert priority.low_confidence_penalty == ZERO
    assert priority.priority_score == d("0.820000")
    assert priority.priority_status == "priority"
    assert "recency_boost_applied" in priority.reason_codes

    assert watched.recency_boost == ZERO
    assert watched.low_confidence_penalty == ZERO
    assert watched.priority_score == d("0.720000")
    assert watched.priority_status == "watch"

    assert deferred.recency_boost == d("0.100000")
    assert deferred.low_confidence_penalty == d("0.230769")
    assert deferred.priority_score == d("0.589231")
    assert deferred.priority_status == "deferred"
    assert "low_confidence_penalty" in deferred.reason_codes

    assert report.average_priority_score == d("0.709744")
    assert report.top_priority_score == d("0.820000")
    assert report.bottom_priority_score == d("0.589231")
    assert report.reason_codes == (
        "priority_catalyst_available",
        "priority_catalyst_watch",
        "priority_catalyst_deferred",
        "recency_boost_applied",
        "low_confidence_penalty",
    )


def test_serialization_uses_decimal_strings_and_revalidates_payload() -> None:
    module = api()
    report = build_report(catalyst(), catalyst("watch", candidate_id="candidate-watch", recency_age_hours=d("12.000000")))

    payload = module.strategy_information_catalyst_priority_queue_v2_payload(report)

    assert payload["catalyst_count"] == "2.000000"
    assert payload["priority_count"] == "1.000000"
    assert payload["rows"][0]["priority_score"] == "0.820000"
    assert payload["rows"][0]["recency_boost"] == "0.100000"
    assert payload["rows"][0]["derived_validation_digest"] == report.rows[0].derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert module.strategy_information_catalyst_priority_queue_v2_payload(payload) == payload
    json.dumps(payload, sort_keys=True)
    assert_no_float_values(payload)


def test_frozen_dataclasses_decimal_only_inputs_and_hard_flags() -> None:
    module = api()
    report = build_report(catalyst(), catalyst("watch", candidate_id="candidate-watch", recency_age_hours=d("12.000000")))

    assert is_dataclass(module.StrategyInformationCatalystPriorityQueueV2Config)
    assert is_dataclass(module.StrategyInformationCatalystPriorityQueueV2Input)
    assert is_dataclass(module.StrategyInformationCatalystPriorityQueueV2Row)
    assert is_dataclass(module.StrategyInformationCatalystPriorityQueueV2Report)
    with pytest.raises(FrozenInstanceError):
        report.status = "priority"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].priority_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        catalyst(readonly=False)
    with pytest.raises(ValueError, match="confidence_score"):
        catalyst(confidence_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="base_catalyst_score"):
        catalyst(base_catalyst_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at"):
        catalyst(observed_at=_DatetimeSubclass(2026, 7, 6, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(catalyst(), generated_at=datetime(2026, 7, 6, 15, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(catalyst(observed_at=GENERATED_AT + timedelta(minutes=1)))
    with pytest.raises(ValueError, match="duplicate"):
        build_report(catalyst(), catalyst())
    with pytest.raises(ValueError, match="ordered"):
        catalyst(reason_codes={"alpha_reason", "beta_reason"})

    populated = build_report(catalyst())
    for value in (populated, *populated.rows):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly", "derived_validation_digest"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(("_count", "_score", "_boost", "_penalty", "_hours")):
                assert type(item_value) is Decimal


def test_digest_tampering_and_unsafe_public_payloads_are_rejected() -> None:
    module = api()
    report = build_report(catalyst(), catalyst("watch", candidate_id="candidate-watch", recency_age_hours=d("12.000000")))
    payload = module.strategy_information_catalyst_priority_queue_v2_payload(report)

    tampered_count = {**payload, "catalyst_count": "9.000000"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_information_catalyst_priority_queue_v2_payload(tampered_count)

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0]), dict(payload["rows"][1])]
    tampered_row["rows"][0]["priority_score"] = "0.111111"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_information_catalyst_priority_queue_v2_payload(tampered_row)

    downgraded = {**payload, "paper_only": False}
    with pytest.raises(ValueError, match="paper_only"):
        module.strategy_information_catalyst_priority_queue_v2_payload(downgraded)

    unsafe_key = {**payload, "wallet_reference": "paper"}
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_information_catalyst_priority_queue_v2_payload(unsafe_key)

    unsafe_value = {**payload, "status": "live_mode"}
    with pytest.raises(ValueError, match="unsafe"):
        module.strategy_information_catalyst_priority_queue_v2_payload(unsafe_value)

    decimal_drift = {**payload, "catalyst_count": d("2.000000")}
    with pytest.raises(ValueError, match="Decimal|string|numeric|JSON"):
        module.strategy_information_catalyst_priority_queue_v2_payload(decimal_drift)

    with pytest.raises(ValueError, match="unsafe"):
        catalyst(catalyst_type="sell_signal")


def test_module_scope_has_no_unsafe_io_or_execution_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "db",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_names = {
        "open",
        "read",
        "write",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "file",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )
    forbidden_attr_names = {
        "open",
        "read",
        "read_text",
        "read_bytes",
        "write",
        "write_text",
        "write_bytes",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert lowered not in forbidden_attr_names
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert not module_name.startswith("polymarket_alpha_lab.")
        lowered = module_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_import_fragments)
