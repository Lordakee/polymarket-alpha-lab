from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_pre_decision_cost_sanity_report import (
    DEFAULT_RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_STATUSES,
    ResearchStrategyPreDecisionCostSanityConfig,
    ResearchStrategyPreDecisionCostSanityInput,
    ResearchStrategyPreDecisionCostSanityReport,
    ResearchStrategyPreDecisionCostSanityRow,
    build_research_strategy_pre_decision_cost_sanity_report,
    research_strategy_pre_decision_cost_sanity_report_digest,
    research_strategy_pre_decision_cost_sanity_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_pre_decision_cost_sanity_report.py",
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyPreDecisionCostSanityConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_CONFIG_VERSION
        ),
        "component_pass_floor": d("0.800000"),
        "component_watch_floor": d("0.600000"),
    }
    values.update(overrides)
    return ResearchStrategyPreDecisionCostSanityConfig(**values)


def candidate(
    internal_candidate_key: str = (
        "raw-candidate-id:alpha|market-id:m-1|market-slug:alpha|"
        "question:will-alpha|source-url:https://example.invalid/a|"
        "source-text:private note|dsn:postgres://x|table:events|token:t"
    ),
    *,
    observed_at: datetime = datetime(2026, 7, 8, 15, 30, tzinfo=UTC),
    fee_accounted_score: Decimal = d("0.900000"),
    spread_accounted_score: Decimal = d("0.880000"),
    depth_haircut_accounted_score: Decimal = d("0.860000"),
    latency_haircut_accounted_score: Decimal = d("0.840000"),
    settlement_uncertainty_accounted_score: Decimal = d("0.820000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyPreDecisionCostSanityInput:
    return ResearchStrategyPreDecisionCostSanityInput(
        internal_candidate_key=internal_candidate_key,
        observed_at=observed_at,
        fee_accounted_score=fee_accounted_score,
        spread_accounted_score=spread_accounted_score,
        depth_haircut_accounted_score=depth_haircut_accounted_score,
        latency_haircut_accounted_score=latency_haircut_accounted_score,
        settlement_uncertainty_accounted_score=settlement_uncertainty_accounted_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *candidates: ResearchStrategyPreDecisionCostSanityInput,
    cfg: ResearchStrategyPreDecisionCostSanityConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyPreDecisionCostSanityReport:
    return build_research_strategy_pre_decision_cost_sanity_report(
        candidates,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def walk_payload_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_payload_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_payload_values(item))
        return tuple(values)
    return (value,)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def payload_digest(value: dict[str, Any]) -> str:
    payload = {key: item for key, item in value.items() if key != "validation_digest"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    signed = dict(payload)
    signed_rows = []
    for row in signed.get("rows", []):
        signed_row = dict(row)
        signed_row["validation_digest"] = payload_digest(signed_row)
        signed_rows.append(signed_row)
    signed["rows"] = signed_rows
    signed["validation_digest"] = payload_digest(signed)
    return signed


def test_report_scores_pre_decision_cost_sanity_for_manual_review() -> None:
    passed = candidate("raw-private-pass")
    watched = candidate(
        "raw-private-watch",
        fee_accounted_score=d("0.720000"),
        spread_accounted_score=d("0.740000"),
        depth_haircut_accounted_score=d("0.760000"),
        latency_haircut_accounted_score=d("0.780000"),
        settlement_uncertainty_accounted_score=d("0.700000"),
    )
    blocked = candidate(
        "raw-private-block",
        observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=timezone(timedelta(hours=-4))),
        fee_accounted_score=d("0.550000"),
        spread_accounted_score=d("0.500000"),
        depth_haircut_accounted_score=d("0.580000"),
        latency_haircut_accounted_score=d("0.400000"),
        settlement_uncertainty_accounted_score=d("0.350000"),
    )

    first = report(watched, blocked, passed)
    second = report(passed, watched, blocked)

    assert is_dataclass(first)
    assert type(first) is ResearchStrategyPreDecisionCostSanityReport
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        DEFAULT_RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_CONFIG_VERSION
    )
    assert first.candidate_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.average_cost_sanity_score == d("0.692000")
    assert first.minimum_component_score == d("0.350000")
    assert first.status == "block"
    assert first.manual_decision_review_state == "manual_decision_review_block"
    assert first.reason_codes == (
        "pre_decision_cost_sanity_report_block",
        "fee_accounting_review",
        "spread_accounting_review",
        "depth_haircut_accounting_review",
        "latency_haircut_accounting_review",
        "settlement_uncertainty_accounting_review",
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert_digest(first.validation_digest)
    assert tuple(row.row_number for row in first.rows) == (
        ONE,
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert first == second

    block_row = first.rows[0]
    assert type(block_row) is ResearchStrategyPreDecisionCostSanityRow
    assert block_row.observed_at == datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
    assert block_row.minimum_component_score == d("0.350000")
    assert block_row.cost_sanity_score == d("0.476000")
    assert block_row.manual_decision_review_state == "manual_decision_review_block"
    assert block_row.reason_codes == (
        "fee_accounting_block",
        "spread_accounting_block",
        "depth_haircut_accounting_block",
        "latency_haircut_accounting_block",
        "settlement_uncertainty_accounting_block",
    )
    assert_digest(block_row.validation_digest)

    watch_row = first.rows[1]
    assert watch_row.cost_sanity_score == d("0.740000")
    assert watch_row.manual_decision_review_state == "manual_decision_review_watch"
    assert watch_row.reason_codes == (
        "fee_accounting_watch",
        "spread_accounting_watch",
        "depth_haircut_accounting_watch",
        "latency_haircut_accounting_watch",
        "settlement_uncertainty_accounting_watch",
    )

    pass_row = first.rows[2]
    assert pass_row.cost_sanity_score == d("0.860000")
    assert pass_row.minimum_component_score == d("0.820000")
    assert pass_row.manual_decision_review_state == "manual_decision_review_ready"
    assert pass_row.reason_codes == ("pre_decision_cost_sanity_pass",)


def test_payload_is_deterministic_decimal_stringed_and_digest_guarded() -> None:
    generated_at = datetime(2026, 7, 8, 12, 0, tzinfo=timezone(timedelta(hours=-4)))
    summary = report(candidate(), generated_at=generated_at)
    first_payload = research_strategy_pre_decision_cost_sanity_report_payload(summary)
    second_payload = research_strategy_pre_decision_cost_sanity_report_payload(summary)

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T16:00:00+00:00"
    assert first_payload["candidate_count"] == "1.000000"
    assert first_payload["rows"][0]["row_number"] == "1.000000"
    assert first_payload["rows"][0]["cost_sanity_score"] == "0.860000"
    assert first_payload["rows"][0]["minimum_component_score"] == "0.820000"
    assert first_payload["rows"][0]["public_candidate_hash"].startswith("sha256:")
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(first_payload)
    )

    payload_text = json.dumps(first_payload, sort_keys=True).lower()
    for forbidden in (
        "raw-candidate-id",
        "internal_candidate_key",
        "market-id",
        "market_slug",
        "market-slug",
        "will-alpha",
        "source-url",
        "source-text",
        "postgres",
        "table:events",
        "token:t",
    ):
        assert forbidden not in payload_text

    digest = research_strategy_pre_decision_cost_sanity_report_digest(summary)
    assert "rows" not in digest
    assert digest["candidate_count"] == first_payload["candidate_count"]
    assert digest["status"] == "pass"
    assert digest["validation_digest"] == first_payload["validation_digest"]
    assert not any(
        type(value) in (int, float, Decimal)
        for value in walk_payload_values(digest)
    )

    assert research_strategy_pre_decision_cost_sanity_report_payload(first_payload) == (
        first_payload
    )
    tampered = dict(first_payload)
    tampered_rows = [dict(first_payload["rows"][0])]
    tampered_rows[0]["fee_accounted_score"] = "0.000001"
    tampered["rows"] = tampered_rows
    with pytest.raises(ValueError, match="validation_digest"):
        research_strategy_pre_decision_cost_sanity_report_payload(tampered)

    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_pre_decision_cost_sanity_report_payload(
            {
                "market_id": "m-1",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_payload_rejects_signed_non_report_schema_surfaces() -> None:
    summary = report(candidate())
    payload = research_strategy_pre_decision_cost_sanity_report_payload(summary)

    invalid_status = dict(payload)
    invalid_status["status"] = "ready"
    with pytest.raises(ValueError, match="status"):
        research_strategy_pre_decision_cost_sanity_report_payload(
            resign_payload(invalid_status),
        )

    candidate_identifier = dict(payload)
    candidate_identifier["candidate_id"] = "sha256:public-but-not-schema"
    with pytest.raises(ValueError, match="unexpected public payload fields"):
        research_strategy_pre_decision_cost_sanity_report_payload(
            resign_payload(candidate_identifier),
        )

    row_candidate_identifier = dict(payload)
    row = dict(payload["rows"][0])
    row["candidate_id"] = "sha256:public-but-not-schema"
    row_candidate_identifier["rows"] = [row]
    with pytest.raises(ValueError, match="unexpected row payload fields"):
        research_strategy_pre_decision_cost_sanity_report_payload(
            resign_payload(row_candidate_identifier),
        )


def test_empty_report_blocks_manual_decision_review() -> None:
    empty = report()

    assert empty.candidate_count == ZERO
    assert empty.pass_count == ZERO
    assert empty.watch_count == ZERO
    assert empty.block_count == ZERO
    assert empty.average_cost_sanity_score is None
    assert empty.minimum_component_score is None
    assert empty.status == "block"
    assert empty.manual_decision_review_state == "manual_decision_review_block"
    assert empty.reason_codes == ("pre_decision_cost_sanity_report_empty",)
    assert empty.rows == ()
    assert_digest(empty.validation_digest)


def test_validation_rejects_non_decimal_bad_flags_bad_times_and_duplicates() -> None:
    summary = report(candidate("raw-private-frozen"))
    row = summary.rows[0]

    assert is_dataclass(ResearchStrategyPreDecisionCostSanityConfig)
    assert is_dataclass(ResearchStrategyPreDecisionCostSanityInput)
    assert is_dataclass(ResearchStrategyPreDecisionCostSanityRow)
    assert is_dataclass(ResearchStrategyPreDecisionCostSanityReport)
    assert RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="fee_accounted_score"):
        candidate(fee_accounted_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_accounted_score"):
        candidate(spread_accounted_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_haircut_accounted_score"):
        candidate(depth_haircut_accounted_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="latency_haircut_accounted_score"):
        candidate(latency_haircut_accounted_score=d("1.200000"))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=datetime(2026, 7, 8, 15, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            candidate("raw-private-time"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report(candidate("raw-private-future", observed_at=datetime(2026, 7, 8, 16, 1, tzinfo=UTC)))
    with pytest.raises(ValueError, match="duplicate"):
        report(candidate("raw-private-dupe"), candidate("raw-private-dupe"))
    with pytest.raises(ValueError, match="component_pass_floor"):
        config(component_pass_floor=d("0.500000"), component_watch_floor=d("0.600000"))

    with pytest.raises(ValueError, match="cost_sanity_score must match"):
        replace(row, cost_sanity_score=row.cost_sanity_score - d("0.000001"))
    with pytest.raises(ValueError, match="status must match"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="validation_digest"):
        replace(row, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count must match"):
        replace(summary, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="validation_digest"):
        replace(summary, validation_digest="0" * 64)

    for value in (config(), candidate(), row, summary):
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "reason_codes",
                "rows",
                "config_version",
                "internal_candidate_key",
                "public_candidate_hash",
                "status",
                "manual_decision_review_state",
                "validation_digest",
            } or item_value is None:
                continue
            if type(item_value) is datetime:
                continue
            assert type(item_value) is Decimal, item.name


def test_public_exports_and_static_report_only_surface() -> None:
    import polymarket_alpha_lab.research_strategy_pre_decision_cost_sanity_report as module

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_STATUSES",
        "ResearchStrategyPreDecisionCostSanityConfig",
        "ResearchStrategyPreDecisionCostSanityInput",
        "ResearchStrategyPreDecisionCostSanityRow",
        "ResearchStrategyPreDecisionCostSanityReport",
        "build_research_strategy_pre_decision_cost_sanity_report",
        "research_strategy_pre_decision_cost_sanity_report_digest",
        "research_strategy_pre_decision_cost_sanity_report_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_terms = (
        "li" "ve",
        "au" "th",
        "wal" "let",
        "broker",
        "or" "der",
        "can" "cel",
        "re" "place",
        "exchange",
        "private" "_" "key",
        "api" "_" "key",
        "sec" "ret",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "po" "sition",
        "b" "uy",
        "se" "ll",
        "reco" "mmend",
        "siz" "ing",
        "data" "base",
        "net" "work",
        "req" "uests",
        "ht" "tp",
        "sock" "et",
        "sub" "process",
        "exec" "ute",
        "pla" "ce",
        "rout" "e",
        "trade",
        "open(",
        "pathlib",
    )
    assert [term for term in forbidden_terms if term in lowered] == []

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "sock" "et",
        "sub" "process",
        "req" "uests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "float",
        "open",
        "send",
        "submit",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in forbidden_calls
                assert func.id != "__import__"
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
