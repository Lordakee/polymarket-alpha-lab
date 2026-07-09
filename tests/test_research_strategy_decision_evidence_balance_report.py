from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_strategy_decision_evidence_balance_report"
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_strategy_decision_evidence_balance_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 16, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def load_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_DECISION_EVIDENCE_BALANCE_REPORT_CONFIG_VERSION
        ),
        "probability_model_pass_floor": d("0.800000"),
        "probability_model_watch_floor": d("0.600000"),
        "team_memory_pass_floor": d("0.800000"),
        "team_memory_watch_floor": d("0.600000"),
        "source_corroboration_pass_floor": d("0.800000"),
        "source_corroboration_watch_floor": d("0.600000"),
        "market_mechanics_pass_floor": d("0.800000"),
        "market_mechanics_watch_floor": d("0.600000"),
        "resolution_risk_pass_floor": d("0.800000"),
        "resolution_risk_watch_floor": d("0.600000"),
        "imbalance_watch_threshold": d("0.250000"),
        "imbalance_block_threshold": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchStrategyDecisionEvidenceBalanceConfig(**values)


def candidate(
    module: Any,
    evidence_key: str = "evidence-alpha",
    *,
    probability_model_score: Decimal = d("0.900000"),
    team_memory_score: Decimal = d("0.900000"),
    source_corroboration_score: Decimal = d("0.900000"),
    market_mechanics_score: Decimal = d("0.900000"),
    resolution_risk_score: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.ResearchStrategyDecisionEvidenceBalanceCandidate(
        evidence_key=evidence_key,
        probability_model_score=probability_model_score,
        team_memory_score=team_memory_score,
        source_corroboration_score=source_corroboration_score,
        market_mechanics_score=market_mechanics_score,
        resolution_risk_score=resolution_risk_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    module: Any,
    *rows: Any,
    config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_decision_evidence_balance_report(
        rows,
        config=cfg(module) if config is None else config,
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


def test_balanced_evidence_rows_payload_and_digest_are_deterministic() -> None:
    module = load_module()
    pass_item = candidate(module, "balance-pass")
    watch_item = candidate(
        module,
        "balance-watch",
        probability_model_score=d("0.700000"),
        team_memory_score=d("0.850000"),
        source_corroboration_score=d("0.700000"),
        market_mechanics_score=d("0.850000"),
        resolution_risk_score=d("0.850000"),
    )
    block_item = candidate(
        module,
        "balance-block",
        probability_model_score=d("0.950000"),
        team_memory_score=d("0.500000"),
        source_corroboration_score=d("0.450000"),
        market_mechanics_score=d("0.500000"),
        resolution_risk_score=d("0.400000"),
    )

    first = report(module, watch_item, block_item, pass_item)
    second = report(module, pass_item, watch_item, block_item)

    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_DECISION_EVIDENCE_BALANCE_REPORT_CONFIG_VERSION
    )
    assert first.candidate_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.status == "block"
    assert first.probability_model_attention_count == d("1.000000")
    assert first.team_memory_attention_count == d("1.000000")
    assert first.source_corroboration_attention_count == d("2.000000")
    assert first.market_mechanics_attention_count == d("1.000000")
    assert first.resolution_risk_attention_count == d("1.000000")
    assert first.balance_imbalance_attention_count == d("1.000000")
    assert first.mean_probability_model_score == d("0.850000")
    assert first.mean_team_memory_score == d("0.750000")
    assert first.mean_source_corroboration_score == d("0.683333")
    assert first.mean_market_mechanics_score == d("0.750000")
    assert first.mean_resolution_risk_score == d("0.716667")
    assert first.mean_evidence_balance_score == d("0.750000")
    assert first.max_evidence_imbalance_score == d("0.550000")
    assert first.reason_codes == (
        "decision_evidence_balance_block",
        "evidence_balance_imbalance_block",
        "market_mechanics_block",
        "probability_model_watch",
        "resolution_risk_block",
        "source_corroboration_block",
        "source_corroboration_watch",
        "team_memory_block",
    )
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True

    assert tuple(row.aggregate_row_number for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert first.rows[0].aggregate_row_hash == hashlib.sha256(
        b"balance-block",
    ).hexdigest()
    assert first.rows[0].evidence_balance_score == d("0.560000")
    assert first.rows[0].evidence_imbalance_score == d("0.550000")
    assert first.rows[0].reason_codes == (
        "evidence_balance_imbalance_block",
        "market_mechanics_block",
        "resolution_risk_block",
        "source_corroboration_block",
        "team_memory_block",
    )
    assert first.rows[2].reason_codes == ("decision_evidence_balance_clear",)
    assert not hasattr(first.rows[0], "evidence_key")

    payload = module.research_strategy_decision_evidence_balance_report_payload(first)
    assert payload == module.research_strategy_decision_evidence_balance_report_payload(
        second,
    )
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload["candidate_count"] == "3.000000"
    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["rows"][0]["evidence_balance_score"] == "0.560000"
    assert payload["public_digest"] == first.public_digest
    payload_text = json.dumps(payload, sort_keys=True)
    assert "evidence_key" not in payload_text
    assert "balance-block" not in payload_text
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_or_int_values(payload)

    digest = module.research_strategy_decision_evidence_balance_report_digest(first)
    assert digest == first.public_digest
    assert_digest(digest)


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    module = load_module()

    balance = report(module)

    assert balance.status == "block"
    assert balance.candidate_count == ZERO
    assert balance.pass_count == ZERO
    assert balance.watch_count == ZERO
    assert balance.block_count == ZERO
    assert balance.mean_evidence_balance_score == ZERO
    assert balance.max_evidence_imbalance_score == ZERO
    assert balance.reason_codes == ("decision_evidence_balance_no_inputs",)
    assert balance.reason_code_counts == (
        module.ResearchStrategyDecisionEvidenceBalanceReasonCodeCount(
            reason_code="decision_evidence_balance_no_inputs",
            count=ONE,
        ),
    )
    assert balance.rows == ()


def test_decimal_datetime_and_public_boundary_validation() -> None:
    module = load_module()

    balance = report(
        module,
        candidate(module),
        generated_at=datetime(
            2026,
            7,
            8,
            12,
            45,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert balance.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="probability_model_pass_floor"):
        cfg(module, probability_model_pass_floor=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="probability_model_score"):
        candidate(module, probability_model_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="team_memory_score"):
        candidate(module, team_memory_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(module, candidate(module), generated_at=datetime(2026, 7, 8, 16, 45))
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(module, reason_codes=["balance_watch"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="duplicate evidence_key"):
        report(
            module,
            candidate(module, "duplicate-key"),
            candidate(module, "duplicate-key"),
        )

    for public_value in (balance, *balance.rows, *balance.reason_code_counts):
        for field in fields(public_value):
            value = getattr(public_value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_public_leak_rejection_at_construction_and_payload_boundary() -> None:
    module = load_module()
    for unsafe_value in (
        "raw_candidate_id:abc",
        "market_id:123",
        "market_slug:event",
        "question:will-it-happen",
        "source_url:https://example.invalid",
        "source_text:verbatim",
        "dsn=postgres://example",
        "table_name:research",
        "private_token=secret",
        "wallet-address",
        "order-ticket",
        "trade-ticket",
        "recommendation-note",
        "sizing-note",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            candidate(module, evidence_key=unsafe_value)

    balance = report(module, candidate(module, "safe-evidence-key"))
    object.__setattr__(balance.rows[0], "aggregate_row_hash", "source_url:https")
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_decision_evidence_balance_report_payload(balance)


def test_hard_flags_frozen_dataclasses_and_payload_revalidation() -> None:
    module = load_module()
    balance = report(module, candidate(module, "frozen-evidence"))

    assert is_dataclass(module.ResearchStrategyDecisionEvidenceBalanceConfig)
    assert is_dataclass(module.ResearchStrategyDecisionEvidenceBalanceCandidate)
    assert is_dataclass(module.ResearchStrategyDecisionEvidenceBalanceRow)
    assert is_dataclass(module.ResearchStrategyDecisionEvidenceBalanceReasonCodeCount)
    assert is_dataclass(module.ResearchStrategyDecisionEvidenceBalanceReport)
    with pytest.raises(FrozenInstanceError):
        balance.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        balance.rows[0].evidence_balance_score = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        candidate(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        cfg(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(balance, readonly=False)

    object.__setattr__(balance.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        module.research_strategy_decision_evidence_balance_report_payload(balance)


def test_reason_counts_public_exports_and_digest_validation() -> None:
    module = load_module()

    balance = report(
        module,
        candidate(
            module,
            "watch-one",
            probability_model_score=d("0.600000"),
            source_corroboration_score=d("0.700000"),
        ),
        candidate(
            module,
            "watch-two",
            team_memory_score=d("0.600000"),
            source_corroboration_score=d("0.700000"),
        ),
        candidate(module, "pass-one"),
    )

    assert tuple(row.status for row in balance.rows) == ("watch", "watch", "pass")
    assert balance.status == "watch"
    assert balance.reason_code_counts == (
        module.ResearchStrategyDecisionEvidenceBalanceReasonCodeCount(
            reason_code="evidence_balance_imbalance_watch",
            count=d("2.000000"),
        ),
        module.ResearchStrategyDecisionEvidenceBalanceReasonCodeCount(
            reason_code="source_corroboration_watch",
            count=d("2.000000"),
        ),
        module.ResearchStrategyDecisionEvidenceBalanceReasonCodeCount(
            reason_code="decision_evidence_balance_clear",
            count=ONE,
        ),
        module.ResearchStrategyDecisionEvidenceBalanceReasonCodeCount(
            reason_code="probability_model_watch",
            count=ONE,
        ),
        module.ResearchStrategyDecisionEvidenceBalanceReasonCodeCount(
            reason_code="team_memory_watch",
            count=ONE,
        ),
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_DECISION_EVIDENCE_BALANCE_REPORT_CONFIG_VERSION",
        "ResearchStrategyDecisionEvidenceBalanceCandidate",
        "ResearchStrategyDecisionEvidenceBalanceConfig",
        "ResearchStrategyDecisionEvidenceBalanceReasonCodeCount",
        "ResearchStrategyDecisionEvidenceBalanceReport",
        "ResearchStrategyDecisionEvidenceBalanceRow",
        "build_research_strategy_decision_evidence_balance_report",
        "research_strategy_decision_evidence_balance_report_digest",
        "research_strategy_decision_evidence_balance_report_payload",
    )

    with pytest.raises(ValueError, match="public_digest"):
        replace(balance, public_digest="0" * 64)
    with pytest.raises(ValueError, match="candidate_count"):
        replace(balance, candidate_count=d("9.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(balance, status="pass")
    with pytest.raises(ValueError, match="status"):
        replace(balance.rows[0], status="review")


def test_static_forbidden_public_surfaces_and_io_are_absent() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "order",
        "trade",
        "trading",
        "position_size",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "auth",
        "database",
        "network",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
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
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__", "asdict"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
            assert all(alias.name != "asdict" for alias in node.names)
