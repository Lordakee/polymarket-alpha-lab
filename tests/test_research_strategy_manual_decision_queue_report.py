from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_strategy_manual_decision_queue_report"
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "min_evidence_item_count": d("2"),
        "evidence_completeness_pass_floor": d("0.850000"),
        "evidence_completeness_watch_floor": d("0.650000"),
        "min_specialist_count": d("2"),
        "specialist_coverage_pass_floor": d("0.800000"),
        "specialist_coverage_watch_floor": d("0.600000"),
        "cost_sanity_pass_floor": d("0.800000"),
        "cost_sanity_watch_floor": d("0.600000"),
        "resolution_rule_check_pass_floor": d("0.850000"),
        "resolution_rule_check_watch_floor": d("0.650000"),
        "recheck_urgency_watch_minutes": d("90.000000"),
        "recheck_urgency_block_minutes": d("15.000000"),
    }
    values.update(overrides)
    return module.ResearchStrategyManualDecisionQueueReportConfig(**values)


def queue_item(**overrides: object) -> Any:
    module = api()
    values = {
        "queue_item_id": "queue-alpha",
        "market_slug": "macro-fed-july",
        "evidence_item_count": d("4"),
        "required_evidence_item_count": d("4"),
        "specialist_count": d("3"),
        "required_specialist_count": d("3"),
        "cost_sanity_score": d("0.900000"),
        "resolution_rule_check_score": d("0.920000"),
        "minutes_until_recheck": d("240.000000"),
    }
    values.update(overrides)
    return module.ResearchStrategyManualDecisionQueueItem(**values)


def report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_strategy_manual_decision_queue_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def assert_no_float_or_int_values(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_manual_decision_queue_report_aggregates_readiness_deterministically() -> None:
    result = report(
        queue_item(
            queue_item_id="queue-pass",
            market_slug="macro-fed",
            evidence_item_count=d("4"),
            required_evidence_item_count=d("4"),
            specialist_count=d("3"),
            required_specialist_count=d("3"),
            cost_sanity_score=d("0.900000"),
            resolution_rule_check_score=d("0.920000"),
            minutes_until_recheck=d("240.000000"),
        ),
        queue_item(
            queue_item_id="queue-watch",
            market_slug="weather-rain",
            evidence_item_count=d("3"),
            required_evidence_item_count=d("4"),
            specialist_count=d("2"),
            required_specialist_count=d("3"),
            cost_sanity_score=d("0.700000"),
            resolution_rule_check_score=d("0.700000"),
            minutes_until_recheck=d("45.000000"),
        ),
        queue_item(
            queue_item_id="queue-block",
            market_slug="policy-vote",
            evidence_item_count=d("1"),
            required_evidence_item_count=d("4"),
            specialist_count=d("1"),
            required_specialist_count=d("3"),
            cost_sanity_score=d("0.500000"),
            resolution_rule_check_score=d("0.500000"),
            minutes_until_recheck=d("10.000000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-strategy-manual-decision-queue-report"
    assert result.queue_item_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.evidence_incomplete_count == d("2")
    assert result.specialist_gap_count == d("2")
    assert result.cost_sanity_gap_count == d("2")
    assert result.resolution_rule_gap_count == d("2")
    assert result.recheck_urgent_count == d("2")
    assert result.min_readiness_score == d("0.316667")
    assert result.queue_status == "block"
    assert result.reason_codes == (
        "evidence_completeness_block",
        "evidence_completeness_watch",
        "specialist_coverage_block",
        "specialist_coverage_watch",
        "cost_sanity_block",
        "cost_sanity_watch",
        "resolution_rule_check_block",
        "resolution_rule_check_watch",
        "recheck_urgency_block",
        "recheck_urgency_watch",
        "manual_decision_queue_ready",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.queue_item_id for row in result.rows) == (
        "queue-block",
        "queue-watch",
        "queue-pass",
    )

    blocked = result.rows[0]
    assert blocked.market_slug == "policy-vote"
    assert blocked.evidence_completeness_score == d("0.250000")
    assert blocked.specialist_coverage_score == d("0.333333")
    assert blocked.recheck_urgency_score == d("0.000000")
    assert blocked.readiness_score == d("0.316667")
    assert blocked.recheck_due_now is True
    assert blocked.queue_status == "block"
    assert blocked.reason_codes == (
        "evidence_completeness_block",
        "specialist_coverage_block",
        "cost_sanity_block",
        "resolution_rule_check_block",
        "recheck_urgency_block",
    )
    assert_digest(blocked.validation_digest)

    watched = result.rows[1]
    assert watched.evidence_completeness_score == d("0.750000")
    assert watched.specialist_coverage_score == d("0.666667")
    assert watched.recheck_urgency_score == d("0.400000")
    assert watched.readiness_score == d("0.643333")
    assert watched.recheck_due_now is False
    assert watched.queue_status == "watch"
    assert watched.reason_codes == (
        "evidence_completeness_watch",
        "specialist_coverage_watch",
        "cost_sanity_watch",
        "resolution_rule_check_watch",
        "recheck_urgency_watch",
    )

    passed = result.rows[2]
    assert passed.evidence_completeness_score == d("1.000000")
    assert passed.specialist_coverage_score == d("1.000000")
    assert passed.recheck_urgency_score == d("1.000000")
    assert passed.readiness_score == d("0.964000")
    assert passed.queue_status == "pass"
    assert passed.reason_codes == ("manual_decision_queue_ready",)
    assert blocked.readiness_score < watched.readiness_score
    assert watched.readiness_score < passed.readiness_score

    same_result = report(
        queue_item(
            queue_item_id="queue-pass",
            market_slug="macro-fed",
            evidence_item_count=d("4"),
            required_evidence_item_count=d("4"),
            specialist_count=d("3"),
            required_specialist_count=d("3"),
            cost_sanity_score=d("0.900000"),
            resolution_rule_check_score=d("0.920000"),
            minutes_until_recheck=d("240.000000"),
        ),
        queue_item(
            queue_item_id="queue-watch",
            market_slug="weather-rain",
            evidence_item_count=d("3"),
            required_evidence_item_count=d("4"),
            specialist_count=d("2"),
            required_specialist_count=d("3"),
            cost_sanity_score=d("0.700000"),
            resolution_rule_check_score=d("0.700000"),
            minutes_until_recheck=d("45.000000"),
        ),
        queue_item(
            queue_item_id="queue-block",
            market_slug="policy-vote",
            evidence_item_count=d("1"),
            required_evidence_item_count=d("4"),
            specialist_count=d("1"),
            required_specialist_count=d("3"),
            cost_sanity_score=d("0.500000"),
            resolution_rule_check_score=d("0.500000"),
            minutes_until_recheck=d("10.000000"),
        ),
    )
    assert same_result.validation_digest == result.validation_digest


def test_empty_report_is_block_status_readonly_and_decimal_zeroed() -> None:
    result = report()

    assert result.queue_item_count == d("0")
    assert result.pass_count == d("0")
    assert result.watch_count == d("0")
    assert result.block_count == d("0")
    assert result.min_readiness_score is None
    assert result.queue_status == "block"
    assert result.reason_codes == ("manual_decision_queue_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)


def test_payload_helper_is_json_ready_and_rejects_unsafe_surfaces() -> None:
    module = api()
    result = report(queue_item())

    payload = module.research_strategy_manual_decision_queue_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["queue_item_count"] == "1"
    assert payload["rows"][0]["evidence_item_count"] == "4"
    assert payload["rows"][0]["minutes_until_recheck"] == "240.000000"
    assert payload["rows"][0]["validation_digest"] == result.rows[0].validation_digest
    assert "private_key" not in encoded
    assert_no_float_or_int_values(payload)
    assert module.research_strategy_manual_decision_queue_report_payload(payload) == payload

    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_manual_decision_queue_report_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_manual_decision_queue_report_payload(
            {**payload, "private" "_" "key": "redacted"},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_manual_decision_queue_report_payload(
            {**payload, "queue_item_count": 1},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_manual_decision_queue_report_payload(
            {**payload, "pass_count": 1.0},
        )


def test_inputs_config_and_datetimes_reject_invalid_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="evidence_item_count must be a Decimal"):
        queue_item(evidence_item_count=3)
    with pytest.raises(ValueError, match="evidence_item_count must be an integer"):
        queue_item(evidence_item_count=d("3.5"))
    with pytest.raises(ValueError, match="required_evidence_item_count must be positive"):
        queue_item(required_evidence_item_count=d("0"))
    with pytest.raises(ValueError, match="cost_sanity_score must be between 0 and 1"):
        queue_item(cost_sanity_score=d("1.100000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        queue_item(paper_only=False)
    with pytest.raises(ValueError, match="evidence completeness watch floor"):
        config(
            evidence_completeness_watch_floor=d("0.900000"),
            evidence_completeness_pass_floor=d("0.800000"),
        )
    with pytest.raises(ValueError, match="recheck urgency block minutes"):
        config(
            recheck_urgency_block_minutes=d("120.000000"),
            recheck_urgency_watch_minutes=d("90.000000"),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_manual_decision_queue_report(
            (queue_item(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_manual_decision_queue_report(
            (queue_item(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    with pytest.raises(ValueError, match="queue_item_id values must be unique"):
        report(queue_item(), queue_item())

    result = report(queue_item())
    with pytest.raises(FrozenInstanceError):
        result.rows[0].queue_status = "block"


def test_validation_digest_and_report_validation_recompute_fields() -> None:
    result = report(queue_item())
    row = result.rows[0]

    with pytest.raises(ValueError, match="readiness_score must match"):
        replace(row, readiness_score=row.readiness_score - d("0.000001"))

    with pytest.raises(ValueError, match="queue_status must match"):
        replace(row, queue_status="block")

    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)

    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=result.pass_count + d("1"))

    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(
            result,
            rows=(
                manual_decision_queue_row("queue-zeta"),
                manual_decision_queue_row("queue-alpha"),
            ),
        )

    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)


def manual_decision_queue_row(queue_item_id: str) -> Any:
    return report(queue_item(queue_item_id=queue_item_id)).rows[0]


def test_module_is_pure_readonly_report_only_and_contains_no_io_surfaces() -> None:
    path = Path(
        "src/polymarket_alpha_lab/"
        "research_strategy_manual_decision_queue_report.py",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    source = path.read_text(encoding="utf-8").lower()

    banned_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "submit",
        "update",
        "urlopen",
        "write",
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}
    forbidden_terms = (
        "recommend" "ation",
        "siz" "ing",
        "b" "uy",
        "s" "ell",
        "wal" "let",
        "or" "der",
        "live " "trading",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert [term for term in forbidden_terms if term in source] == []
