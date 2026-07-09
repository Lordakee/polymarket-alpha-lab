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


MODULE_NAME = (
    "polymarket_alpha_lab.research_strategy_team_evidence_quorum_gate_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_team_evidence_quorum_gate_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 12, 15, tzinfo=UTC)
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
            module.DEFAULT_RESEARCH_STRATEGY_TEAM_EVIDENCE_QUORUM_GATE_REPORT_CONFIG_VERSION
        ),
        "min_research_team_count_pass": d("3.000000"),
        "min_research_team_count_watch": d("2.000000"),
        "min_primary_evidence_count_pass": d("2.000000"),
        "min_primary_evidence_count_watch": d("1.000000"),
        "min_total_evidence_count_pass": d("5.000000"),
        "min_total_evidence_count_watch": d("3.000000"),
        "min_independent_source_family_count_pass": d("3.000000"),
        "min_independent_source_family_count_watch": d("2.000000"),
        "fresh_evidence_share_pass_floor": d("0.750000"),
        "fresh_evidence_share_watch_floor": d("0.500000"),
        "consensus_support_score_pass_floor": d("0.800000"),
        "consensus_support_score_watch_floor": d("0.600000"),
        "contradiction_pressure_watch_ceiling": d("0.250000"),
        "contradiction_pressure_block_ceiling": d("0.500000"),
        "source_authority_score_pass_floor": d("0.750000"),
        "source_authority_score_watch_floor": d("0.500000"),
        "evidence_quorum_score_pass_floor": d("0.750000"),
        "evidence_quorum_score_watch_floor": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchStrategyTeamEvidenceQuorumGateConfig(**values)


def gate_input(
    module: Any,
    team_evidence_key: str = "team-pass",
    *,
    research_team_count: Decimal = d("3.000000"),
    primary_evidence_count: Decimal = d("2.000000"),
    corroborating_evidence_count: Decimal = d("3.000000"),
    independent_source_family_count: Decimal = d("3.000000"),
    fresh_evidence_share: Decimal = d("0.900000"),
    consensus_support_score: Decimal = d("0.900000"),
    contradiction_pressure_score: Decimal = d("0.050000"),
    source_authority_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return module.ResearchStrategyTeamEvidenceQuorumGateInput(
        team_evidence_key=team_evidence_key,
        research_team_count=research_team_count,
        primary_evidence_count=primary_evidence_count,
        corroborating_evidence_count=corroborating_evidence_count,
        independent_source_family_count=independent_source_family_count,
        fresh_evidence_share=fresh_evidence_share,
        consensus_support_score=consensus_support_score,
        contradiction_pressure_score=contradiction_pressure_score,
        source_authority_score=source_authority_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    module: Any,
    *rows: Any,
    config: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_team_evidence_quorum_gate_report(
        rows,
        config=cfg(module) if config is None else config,
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("public_digest")
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_team_evidence_quorum_gate_payload_digest_and_statuses() -> None:
    module = load_module()
    pass_item = gate_input(module, "team-pass")
    watch_item = gate_input(
        module,
        "team-watch",
        research_team_count=d("2.000000"),
        primary_evidence_count=d("1.000000"),
        corroborating_evidence_count=d("2.000000"),
        independent_source_family_count=d("2.000000"),
        fresh_evidence_share=d("0.650000"),
        consensus_support_score=d("0.700000"),
        contradiction_pressure_score=d("0.300000"),
        source_authority_score=d("0.650000"),
    )
    block_item = gate_input(
        module,
        "team-block",
        research_team_count=d("1.000000"),
        primary_evidence_count=d("0.000000"),
        corroborating_evidence_count=d("1.000000"),
        independent_source_family_count=d("1.000000"),
        fresh_evidence_share=d("0.400000"),
        consensus_support_score=d("0.500000"),
        contradiction_pressure_score=d("0.600000"),
        source_authority_score=d("0.400000"),
    )

    first = build_report(module, watch_item, block_item, pass_item)
    second = build_report(module, pass_item, watch_item, block_item)

    assert type(first) is module.ResearchStrategyTeamEvidenceQuorumGateReport
    assert is_dataclass(first)
    assert first.generated_at == GENERATED_AT
    assert first.config_version == (
        module.DEFAULT_RESEARCH_STRATEGY_TEAM_EVIDENCE_QUORUM_GATE_REPORT_CONFIG_VERSION
    )
    assert first.evidence_quorum_item_count == d("3.000000")
    assert first.pass_count == ONE
    assert first.watch_count == ONE
    assert first.block_count == ONE
    assert first.status == "block"
    assert first.research_team_attention_count == d("2.000000")
    assert first.primary_evidence_attention_count == d("2.000000")
    assert first.total_evidence_attention_count == d("2.000000")
    assert first.independent_source_family_attention_count == d("2.000000")
    assert first.fresh_evidence_attention_count == d("2.000000")
    assert first.consensus_support_attention_count == d("2.000000")
    assert first.contradiction_pressure_attention_count == d("2.000000")
    assert first.source_authority_attention_count == d("2.000000")
    assert first.mean_evidence_quorum_score == d("0.639583")
    assert first.lowest_evidence_quorum_score == d("0.320833")
    assert first.highest_contradiction_pressure_score == d("0.600000")
    assert first.reason_codes == (
        "research_strategy_team_evidence_quorum_gate_team_count_block",
        "research_strategy_team_evidence_quorum_gate_primary_evidence_block",
        "research_strategy_team_evidence_quorum_gate_total_evidence_block",
        "research_strategy_team_evidence_quorum_gate_source_family_block",
        "research_strategy_team_evidence_quorum_gate_fresh_evidence_block",
        "research_strategy_team_evidence_quorum_gate_consensus_support_block",
        "research_strategy_team_evidence_quorum_gate_contradiction_pressure_block",
        "research_strategy_team_evidence_quorum_gate_source_authority_block",
        "research_strategy_team_evidence_quorum_gate_score_block",
        "research_strategy_team_evidence_quorum_gate_team_count_watch",
        "research_strategy_team_evidence_quorum_gate_primary_evidence_watch",
        "research_strategy_team_evidence_quorum_gate_total_evidence_watch",
        "research_strategy_team_evidence_quorum_gate_source_family_watch",
        "research_strategy_team_evidence_quorum_gate_fresh_evidence_watch",
        "research_strategy_team_evidence_quorum_gate_consensus_support_watch",
        "research_strategy_team_evidence_quorum_gate_contradiction_pressure_watch",
        "research_strategy_team_evidence_quorum_gate_source_authority_watch",
        "research_strategy_team_evidence_quorum_gate_score_watch",
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
        b"team-block",
    ).hexdigest()
    assert first.rows[0].total_evidence_count == d("1.000000")
    assert first.rows[0].evidence_quorum_score == d("0.320833")
    assert first.rows[1].evidence_quorum_score == d("0.641667")
    assert first.rows[2].evidence_quorum_score == d("0.956250")
    assert first.rows[2].reason_codes == (
        "research_strategy_team_evidence_quorum_gate_clear",
    )
    assert not hasattr(first.rows[0], "team_evidence_key")

    payload = module.research_strategy_team_evidence_quorum_gate_report_payload(first)
    assert payload == (
        module.research_strategy_team_evidence_quorum_gate_report_payload(second)
    )
    assert payload["evidence_quorum_item_count"] == "3.000000"
    assert payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert payload["rows"][0]["evidence_quorum_score"] == "0.320833"
    assert payload["public_digest"] == first.public_digest
    assert payload["public_digest"] == canonical_digest(payload)
    assert json.dumps(payload, sort_keys=True, allow_nan=False)
    payload_text = json.dumps(payload, sort_keys=True)
    assert "team_evidence_key" not in payload_text
    assert "team-block" not in payload_text
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_values(payload)
    assert_payload_has_no_leaked_values(payload)

    digest = module.research_strategy_team_evidence_quorum_gate_report_digest(first)
    assert digest == first.public_digest
    assert len(digest) == 64
    int(digest, 16)
    module.validate_research_strategy_team_evidence_quorum_gate_report_digest(first)
    module.validate_research_strategy_team_evidence_quorum_gate_public_payload(payload)


def test_empty_inputs_block_with_no_inputs_reason_count() -> None:
    module = load_module()

    report = build_report(module)

    assert report.status == "block"
    assert report.evidence_quorum_item_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.mean_evidence_quorum_score == ZERO
    assert report.lowest_evidence_quorum_score == ZERO
    assert report.highest_contradiction_pressure_score == ZERO
    assert report.reason_codes == (
        "research_strategy_team_evidence_quorum_gate_no_inputs",
    )
    assert report.reason_code_counts == (
        module.ResearchStrategyTeamEvidenceQuorumGateReasonCodeCount(
            reason_code="research_strategy_team_evidence_quorum_gate_no_inputs",
            count=ONE,
        ),
    )
    assert report.rows == ()


def test_decimal_datetime_flags_and_frozen_dataclasses() -> None:
    module = load_module()

    report = build_report(
        module,
        gate_input(module),
        generated_at=datetime(
            2026,
            7,
            9,
            8,
            15,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )
    assert report.generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="min_research_team_count_pass"):
        cfg(module, min_research_team_count_pass=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fresh_evidence_share_pass_floor"):
        cfg(module, fresh_evidence_share_pass_floor=_DecimalSubclass("0.750000"))
    with pytest.raises(ValueError, match="min_research_team_count_pass"):
        cfg(module, min_research_team_count_pass=d("1.000000"))
    with pytest.raises(ValueError, match="contradiction_pressure_watch_ceiling"):
        cfg(module, contradiction_pressure_watch_ceiling=d("0.600000"))
    with pytest.raises(ValueError, match="research_team_count"):
        gate_input(module, research_team_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="fresh_evidence_share"):
        gate_input(module, fresh_evidence_share=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        cfg(module, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        gate_input(module, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        gate_input(module, readonly=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_report(module, gate_input(module), generated_at=datetime(2026, 7, 9, 12, 15))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TEAM_EVIDENCE_QUORUM_GATE_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_TEAM_EVIDENCE_QUORUM_GATE_REPORT_STATUSES",
        "ResearchStrategyTeamEvidenceQuorumGateConfig",
        "ResearchStrategyTeamEvidenceQuorumGateInput",
        "ResearchStrategyTeamEvidenceQuorumGateReasonCodeCount",
        "ResearchStrategyTeamEvidenceQuorumGateReport",
        "ResearchStrategyTeamEvidenceQuorumGateRow",
        "build_research_strategy_team_evidence_quorum_gate_report",
        "research_strategy_team_evidence_quorum_gate_report_digest",
        "research_strategy_team_evidence_quorum_gate_report_payload",
        "validate_research_strategy_team_evidence_quorum_gate_public_payload",
        "validate_research_strategy_team_evidence_quorum_gate_report_digest",
    )
    assert is_dataclass(cfg(module))
    assert is_dataclass(gate_input(module))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(TypeError):
        type("ConfigSubclass", (module.ResearchStrategyTeamEvidenceQuorumGateConfig,), {})
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        cfg(module).min_total_evidence_count_pass = d("4.000000")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="block")
    with pytest.raises(ValueError, match="evidence_quorum_score"):
        replace(report.rows[0], evidence_quorum_score=d("0.000000"))
    with pytest.raises(ValueError, match="public_digest"):
        replace(report, public_digest="0" * 64)


def test_public_payload_prevents_identifier_source_secret_and_execution_leaks() -> None:
    module = load_module()
    report = build_report(module, gate_input(module))
    payload = module.research_strategy_team_evidence_quorum_gate_report_payload(report)

    unsafe_keys = {
        "raw_candidate_id",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order_id",
        "trade_id",
        "live_surface",
        "position_size",
        "recommendation",
    }
    keys = {
        field.name
        for cls in (type(gate_input(module)), type(report), type(report.rows[0]))
        for field in fields(cls)
    }
    assert unsafe_keys.isdisjoint(keys)
    assert_payload_has_no_leaked_values(payload)

    for unsafe_value in (
        "candidate-123",
        "market_slug",
        "Will this question resolve?",
        "https://example.invalid/source",
        "source_text",
        "postgres://local.example/db",
        "wallet_token",
        "live order trade recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe text"):
            gate_input(module, unsafe_value)

    for unsafe_payload in (
        {"candidate_id": "safe"},
        {"safe": "https://example.invalid/source"},
        {"safe": "wallet token"},
        {"safe": "live order trade recommendation"},
        {"table_name": "public_summary"},
    ):
        with pytest.raises(ValueError, match="public payload"):
            module.validate_research_strategy_team_evidence_quorum_gate_public_payload(
                {
                    **payload,
                    **unsafe_payload,
                    "public_digest": payload["public_digest"],
                },
            )


def test_module_scope_is_pure_report_only_without_external_surfaces() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "submit_order",
                "place_order",
                "recommend",
                "size_position",
            }

    forbidden_import_fragments = (
        "auth",
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_public_numeric_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numeric_values(item)
    else:
        assert type(value) is not float
        assert type(value) is not int


def assert_payload_has_no_leaked_values(value: object) -> None:
    forbidden_fragments = (
        "http://",
        "https://",
        "postgres://",
        "mysql://",
        "jdbc:",
        "candidate-",
        "candidate_id",
        "market-",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live_surface",
        "position_size",
        "recommendation",
    )
    if isinstance(value, dict):
        for item in value.values():
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_payload_has_no_leaked_values(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
