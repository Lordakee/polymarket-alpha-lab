from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_research_latency_budget_report import (
    DEFAULT_RESEARCH_STRATEGY_RESEARCH_LATENCY_BUDGET_REPORT_CONFIG_VERSION,
    ResearchStrategyResearchLatencyBudgetCandidate,
    ResearchStrategyResearchLatencyBudgetConfig,
    ResearchStrategyResearchLatencyBudgetReport,
    ResearchStrategyResearchLatencyBudgetRow,
    build_research_strategy_research_latency_budget_report,
    research_strategy_research_latency_budget_report_digest,
    research_strategy_research_latency_budget_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_research_latency_budget_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyResearchLatencyBudgetConfig:
    values = {
        "discovery_budget_seconds": d("900.000000"),
        "discovery_watch_ceiling_seconds": d("1800.000000"),
        "evidence_collection_budget_seconds": d("1800.000000"),
        "evidence_collection_watch_ceiling_seconds": d("3600.000000"),
        "specialist_review_budget_seconds": d("2700.000000"),
        "specialist_review_watch_ceiling_seconds": d("5400.000000"),
        "manual_decision_queue_delay_budget_seconds": d("600.000000"),
        "manual_decision_queue_delay_watch_ceiling_seconds": d("1200.000000"),
        "total_research_latency_budget_seconds": d("6000.000000"),
        "total_research_latency_watch_ceiling_seconds": d("12000.000000"),
    }
    values.update(overrides)
    return ResearchStrategyResearchLatencyBudgetConfig(**values)


def candidate(
    packet_ref: str = "private-packet-alpha",
    *,
    discovery_latency_seconds: Decimal = d("600.000000"),
    evidence_collection_latency_seconds: Decimal = d("1200.000000"),
    specialist_review_latency_seconds: Decimal = d("1800.000000"),
    manual_decision_queue_delay_seconds: Decimal = d("300.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyResearchLatencyBudgetCandidate:
    return ResearchStrategyResearchLatencyBudgetCandidate(
        packet_ref=packet_ref,
        discovery_latency_seconds=discovery_latency_seconds,
        evidence_collection_latency_seconds=evidence_collection_latency_seconds,
        specialist_review_latency_seconds=specialist_review_latency_seconds,
        manual_decision_queue_delay_seconds=manual_decision_queue_delay_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *candidates: ResearchStrategyResearchLatencyBudgetCandidate,
    cfg: ResearchStrategyResearchLatencyBudgetConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyResearchLatencyBudgetReport:
    return build_research_strategy_research_latency_budget_report(
        candidates,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
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


def public_payload_digest(values: dict[str, Any]) -> str:
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "validation_digest": public_payload_digest(
            {key: value for key, value in payload.items() if key != "validation_digest"},
        ),
    }


def test_latency_budget_aggregates_pass_watch_block_deterministically() -> None:
    pass_candidate = candidate("private-pass")
    watch_candidate = candidate(
        "private-watch",
        discovery_latency_seconds=d("1200.000000"),
        evidence_collection_latency_seconds=d("2400.000000"),
        specialist_review_latency_seconds=d("3000.000000"),
        manual_decision_queue_delay_seconds=d("900.000000"),
    )
    block_candidate = candidate(
        "private-block",
        discovery_latency_seconds=d("2000.000000"),
        evidence_collection_latency_seconds=d("4000.000000"),
        specialist_review_latency_seconds=d("6000.000000"),
        manual_decision_queue_delay_seconds=d("1500.000000"),
    )

    first = report(pass_candidate, watch_candidate, block_candidate)
    second = report(block_candidate, watch_candidate, pass_candidate)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_RESEARCH_LATENCY_BUDGET_REPORT_CONFIG_VERSION
    )
    assert first.packet_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.max_total_latency_seconds == d("13500.000000")
    assert first.average_total_latency_seconds == d("8300.000000")
    assert first.max_total_budget_utilization_ratio == d("2.250000")
    assert first.status == "block"
    assert first.reason_codes == (
        "discovery_latency_block",
        "evidence_collection_latency_block",
        "specialist_review_latency_block",
        "manual_decision_queue_delay_block",
        "total_research_latency_block",
        "latency_budget_block",
        "discovery_latency_watch",
        "evidence_collection_latency_watch",
        "specialist_review_latency_watch",
        "manual_decision_queue_delay_watch",
        "total_research_latency_watch",
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert tuple(row.row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    blocked = first.rows[0]
    assert blocked.discovery_budget_utilization_ratio == d("2.222222")
    assert blocked.evidence_collection_budget_utilization_ratio == d("2.222222")
    assert blocked.specialist_review_budget_utilization_ratio == d("2.222222")
    assert blocked.manual_decision_queue_delay_budget_utilization_ratio == d("2.500000")
    assert blocked.total_research_latency_seconds == d("13500.000000")
    assert blocked.total_budget_utilization_ratio == d("2.250000")
    assert blocked.reason_codes == (
        "discovery_latency_block",
        "evidence_collection_latency_block",
        "specialist_review_latency_block",
        "manual_decision_queue_delay_block",
        "total_research_latency_block",
    )
    assert_digest(blocked.validation_digest)
    assert_digest(first.validation_digest)

    payload = research_strategy_research_latency_budget_report_payload(first)
    assert payload == research_strategy_research_latency_budget_report_payload(second)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    assert "private-pass" not in encoded
    assert "private-watch" not in encoded
    assert "private-block" not in encoded
    assert "market-" not in encoded
    assert "source" not in encoded.lower()
    assert payload["packet_count"] == "3.000000"
    assert payload["rows"][0]["row_number"] == "1.000000"
    assert payload["rows"][0]["total_budget_utilization_ratio"] == "2.250000"
    assert payload["rows"][0]["validation_digest"] == blocked.validation_digest
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = research_strategy_research_latency_budget_report_digest(first)
    assert "rows" not in digest
    assert digest["packet_count"] == payload["packet_count"]
    assert digest["status"] == "block"
    assert digest["validation_digest"] == first.validation_digest
    assert_no_float_or_int_values(digest)


def test_empty_report_blocks_without_candidate_identifiers() -> None:
    result = report()

    assert result.packet_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.max_total_latency_seconds is None
    assert result.average_total_latency_seconds is None
    assert result.max_total_budget_utilization_ratio is None
    assert result.status == "block"
    assert result.reason_codes == ("latency_budget_no_packets",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)


def test_decimal_only_frozen_flags_and_input_validation() -> None:
    result = report(candidate("private-frozen"))

    assert is_dataclass(ResearchStrategyResearchLatencyBudgetConfig)
    assert is_dataclass(ResearchStrategyResearchLatencyBudgetCandidate)
    assert is_dataclass(ResearchStrategyResearchLatencyBudgetRow)
    assert is_dataclass(ResearchStrategyResearchLatencyBudgetReport)
    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].total_research_latency_seconds = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="discovery_latency_seconds"):
        candidate(discovery_latency_seconds=600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_collection_latency_seconds"):
        candidate(evidence_collection_latency_seconds=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="specialist_review_latency_seconds"):
        candidate(specialist_review_latency_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="packet_ref values must be unique"):
        report(candidate("private-dupe"), candidate("private-dupe"))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("private-time"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate("private-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="discovery_watch_ceiling_seconds"):
        config(discovery_watch_ceiling_seconds=d("900.000000"))
    with pytest.raises(ValueError, match="total_research_latency_watch_ceiling_seconds"):
        config(total_research_latency_watch_ceiling_seconds=d("6000.000000"))

    for item in (result, *result.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, tuple):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_validation_digest_and_payload_reject_tampering() -> None:
    result = report(candidate("private-consistent"))
    row = result.rows[0]

    with pytest.raises(ValueError, match="total_research_latency_seconds must match"):
        replace(row, total_research_latency_seconds=row.total_research_latency_seconds + ONE)
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(
            result,
            rows=(
                report(candidate("private-zeta")).rows[0],
                row,
            ),
        )
    with pytest.raises(ValueError, match="validation_digest must match"):
        replace(result, validation_digest="0" * 64)

    payload = research_strategy_research_latency_budget_report_payload(result)
    assert research_strategy_research_latency_budget_report_payload(payload) == payload
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_research_latency_budget_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_research_latency_budget_report_payload(
            {**payload, "candidate" "_" "id": "private-consistent"},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_research_latency_budget_report_payload(
            {**payload, "market" "_" "slug": "market-hidden"},
        )
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_research_latency_budget_report_payload(
            {**payload, "dsn": "postgres://hidden"},
        )
    with pytest.raises(ValueError, match="numeric"):
        research_strategy_research_latency_budget_report_payload(
            {**payload, "packet_count": 1},
        )
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_research_latency_budget_report_payload(
            {**payload, "packet_count": "2.000000"},
        )
    tampered_row_payload = {
        **payload,
        "rows": [
            {
                **payload["rows"][0],
                "total_research_latency_seconds": "0.000000",
            },
        ],
    }
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_research_latency_budget_report_payload(tampered_row_payload)


def test_public_payload_rejects_recomputed_invalid_statuses() -> None:
    payload = research_strategy_research_latency_budget_report_payload(
        report(candidate("private-recomputed-status")),
    )

    forged_report = resign_payload({**payload, "status": "hold"})
    with pytest.raises(ValueError, match="status"):
        research_strategy_research_latency_budget_report_payload(forged_report)

    forged_row = resign_payload({**payload["rows"][0], "status": "hold"})
    forged_payload = resign_payload({**payload, "rows": [forged_row]})
    with pytest.raises(ValueError, match="status"):
        research_strategy_research_latency_budget_report_payload(forged_payload)


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_strategy_research_latency_budget_report as module

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_RESEARCH_LATENCY_BUDGET_REPORT_CONFIG_VERSION",
        "ResearchStrategyResearchLatencyBudgetCandidate",
        "ResearchStrategyResearchLatencyBudgetConfig",
        "ResearchStrategyResearchLatencyBudgetReport",
        "ResearchStrategyResearchLatencyBudgetRow",
        "build_research_strategy_research_latency_budget_report",
        "research_strategy_research_latency_budget_report_digest",
        "research_strategy_research_latency_budget_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "reco" "mmend",
        "siz" "ing",
        "b" "uy",
        "s" "ell",
        "wal" "let",
        "or" "der",
        "li" "ve " "trading",
    )
    assert [term for term in forbidden_terms if term in lowered] == []

    tree = ast.parse(source)
    forbidden_imports = {
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
    forbidden_calls = {
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
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & forbidden_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in forbidden_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_calls
