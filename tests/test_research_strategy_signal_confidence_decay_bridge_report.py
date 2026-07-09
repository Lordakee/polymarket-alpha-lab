from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_signal_confidence_decay_bridge_report import (
    DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_STATUSES,
    ResearchStrategySignalConfidenceDecayBridgeConfig,
    ResearchStrategySignalConfidenceDecayBridgeInput,
    ResearchStrategySignalConfidenceDecayBridgeReport,
    ResearchStrategySignalConfidenceDecayBridgeRow,
    build_research_strategy_signal_confidence_decay_bridge_report,
    research_strategy_signal_confidence_decay_bridge_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategySignalConfidenceDecayBridgeConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_REPORT_CONFIG_VERSION
        ),
        "fresh_age_seconds": d("1800"),
        "stale_age_seconds": d("7200"),
        "min_pass_freshness_score": d("0.700000"),
        "min_watch_freshness_score": d("0.500000"),
        "min_pass_authority_score": d("0.650000"),
        "min_watch_authority_score": d("0.450000"),
        "min_pass_corroboration_score": d("0.650000"),
        "min_watch_corroboration_score": d("0.450000"),
        "max_pass_contradiction_pressure": d("0.150000"),
        "max_watch_contradiction_pressure": d("0.350000"),
        "max_pass_market_movement_pressure": d("0.200000"),
        "max_watch_market_movement_pressure": d("0.400000"),
        "max_pass_cost_drag_score": d("0.100000"),
        "max_watch_cost_drag_score": d("0.250000"),
        "min_pass_liquidity_reliability_score": d("0.700000"),
        "min_watch_liquidity_reliability_score": d("0.500000"),
        "max_pass_resolution_ambiguity_score": d("0.150000"),
        "max_watch_resolution_ambiguity_score": d("0.350000"),
        "min_pass_bridge_confidence_score": d("0.700000"),
        "min_watch_bridge_confidence_score": d("0.500000"),
    }
    values.update(overrides)
    return ResearchStrategySignalConfidenceDecayBridgeConfig(**values)


def signal_input(**overrides: object) -> ResearchStrategySignalConfidenceDecayBridgeInput:
    values = {
        "signal_ref": "alpha-signal",
        "observed_at": GENERATED_AT - timedelta(seconds=600),
        "base_signal_confidence_score": d("0.900000"),
        "source_authority_score": d("0.900000"),
        "corroboration_score": d("0.850000"),
        "contradiction_pressure": d("0.050000"),
        "market_movement_pressure": d("0.050000"),
        "cost_drag_score": d("0.020000"),
        "liquidity_reliability_score": d("0.900000"),
        "resolution_ambiguity_score": d("0.050000"),
    }
    values.update(overrides)
    return ResearchStrategySignalConfidenceDecayBridgeInput(**values)


def report(
    *rows: ResearchStrategySignalConfidenceDecayBridgeInput,
    cfg: ResearchStrategySignalConfidenceDecayBridgeConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategySignalConfidenceDecayBridgeReport:
    return build_research_strategy_signal_confidence_decay_bridge_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_bridges_signal_confidence_and_evidence_decay_pressures() -> None:
    summary = report(
        signal_input(),
        signal_input(
            signal_ref="beta-signal",
            observed_at=GENERATED_AT - timedelta(seconds=4500),
            base_signal_confidence_score=d("0.800000"),
            source_authority_score=d("0.550000"),
            corroboration_score=d("0.550000"),
            contradiction_pressure=d("0.200000"),
            market_movement_pressure=d("0.250000"),
            cost_drag_score=d("0.200000"),
            liquidity_reliability_score=d("0.600000"),
            resolution_ambiguity_score=d("0.200000"),
        ),
        signal_input(
            signal_ref="gamma-signal",
            observed_at=GENERATED_AT - timedelta(seconds=7200),
            base_signal_confidence_score=d("0.500000"),
            source_authority_score=d("0.300000"),
            corroboration_score=d("0.400000"),
            contradiction_pressure=d("0.700000"),
            market_movement_pressure=d("0.650000"),
            cost_drag_score=d("0.400000"),
            liquidity_reliability_score=d("0.300000"),
            resolution_ambiguity_score=d("0.600000"),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert (
        summary.config_version
        == DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_REPORT_CONFIG_VERSION
    )
    assert summary.source_row_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.mean_source_age_pressure == d("0.500000")
    assert summary.mean_evidence_decay_score == d("0.355000")
    assert summary.mean_confidence_decay_bridge_score == d("0.514042")
    assert summary.lowest_confidence_decay_bridge_score == d("0.165625")
    assert summary.highest_evidence_decay_score == d("0.668750")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "signal_confidence_decay_bridge_block",
        "source_age_review",
        "authority_review",
        "corroboration_review",
        "contradiction_pressure_review",
        "market_movement_review",
        "cost_drag_review",
        "liquidity_reliability_review",
        "resolution_ambiguity_review",
        "bridge_confidence_review",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategySignalConfidenceDecayBridgeRow)
    assert blocked.aggregate_row_number == d("1.000000")
    assert len(blocked.aggregate_signal_hash) == 64
    assert blocked.source_age_seconds == d("7200.000000")
    assert blocked.source_age_pressure == d("1.000000")
    assert blocked.freshness_score == d("0.000000")
    assert blocked.evidence_decay_score == d("0.668750")
    assert blocked.confidence_decay_bridge_score == d("0.165625")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "authority_block",
        "bridge_confidence_block",
        "contradiction_pressure_block",
        "corroboration_block",
        "cost_drag_block",
        "liquidity_reliability_block",
        "market_movement_block",
        "resolution_ambiguity_block",
        "source_age_block",
    )

    watched = summary.rows[1]
    assert watched.aggregate_row_number == d("2.000000")
    assert watched.source_age_pressure == d("0.500000")
    assert watched.evidence_decay_score == d("0.331250")
    assert watched.confidence_decay_bridge_score == d("0.535000")
    assert watched.status == "watch"
    assert watched.reason_codes == (
        "authority_watch",
        "bridge_confidence_watch",
        "contradiction_pressure_watch",
        "corroboration_watch",
        "cost_drag_watch",
        "liquidity_reliability_watch",
        "market_movement_watch",
        "resolution_ambiguity_watch",
        "source_age_watch",
    )

    passed = summary.rows[2]
    assert passed.aggregate_row_number == d("3.000000")
    assert passed.source_age_pressure == d("0.000000")
    assert passed.evidence_decay_score == d("0.065000")
    assert passed.confidence_decay_bridge_score == d("0.841500")
    assert passed.status == "pass"
    assert passed.reason_codes == ("signal_confidence_decay_bridge_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True
    assert len(passed.derived_validation_digest) == 64


def test_public_payload_is_deterministic_hashed_decimal_and_digest_guarded() -> None:
    sensitive_ref = (
        "candidate-alpha market-alpha will this resolve yes "
        "https://private.example/path?api_key=hidden-token table=db.events"
    )
    first_payload = research_strategy_signal_confidence_decay_bridge_report_payload(
        report(signal_input(signal_ref=sensitive_ref)),
    )
    second_payload = research_strategy_signal_confidence_decay_bridge_report_payload(
        report(signal_input(signal_ref=sensitive_ref)),
    )
    encoded = json.dumps(first_payload, sort_keys=True).lower()

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert len(first_payload["rows"][0]["aggregate_signal_hash"]) == 64
    assert first_payload["rows"][0]["confidence_decay_bridge_score"] == "0.841500"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert_no_decimal_or_raw_numeric_values(first_payload)

    forbidden_payload_fragments = (
        "candidate-alpha",
        "market-alpha",
        "will this resolve yes",
        "https://",
        "private.example",
        "api_key",
        "hidden-token",
        "table=",
        "db.events",
        "signal_ref",
    )
    assert all(fragment not in encoded for fragment in forbidden_payload_fragments)

    tampered_payload = json.loads(json.dumps(first_payload))
    tampered_payload["rows"][0]["confidence_decay_bridge_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_signal_confidence_decay_bridge_report_payload(tampered_payload)

    numeric_payload = json.loads(json.dumps(first_payload))
    numeric_payload["source_row_count"] = 1
    with pytest.raises(ValueError, match="source_row_count"):
        research_strategy_signal_confidence_decay_bridge_report_payload(numeric_payload)

    unsafe_payload = json.loads(json.dumps(first_payload))
    unsafe_payload["raw_candidate_id"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_signal_confidence_decay_bridge_report_payload(unsafe_payload)


def test_public_payload_dict_validation_rejects_recomputed_schema_tampering() -> None:
    payload = research_strategy_signal_confidence_decay_bridge_report_payload(
        report(signal_input()),
    )

    row_digest_payload = json.loads(json.dumps(payload))
    row_digest_payload["rows"][0]["confidence_decay_bridge_score"] = "0.841499"
    _refresh_report_payload_digest(row_digest_payload)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_signal_confidence_decay_bridge_report_payload(row_digest_payload)

    status_payload = json.loads(json.dumps(payload))
    status_payload["status"] = "review"
    status_payload["rows"][0]["status"] = "review"
    _refresh_row_payload_digest(status_payload["rows"][0])
    _refresh_report_payload_digest(status_payload)
    with pytest.raises(ValueError, match="status"):
        research_strategy_signal_confidence_decay_bridge_report_payload(status_payload)

    flag_payload = json.loads(json.dumps(payload))
    flag_payload["rows"][0]["readonly"] = False
    _refresh_row_payload_digest(flag_payload["rows"][0])
    _refresh_report_payload_digest(flag_payload)
    with pytest.raises(ValueError, match="readonly"):
        research_strategy_signal_confidence_decay_bridge_report_payload(flag_payload)

    decimal_payload = json.loads(json.dumps(payload))
    decimal_payload["source_row_count"] = "1"
    _refresh_report_payload_digest(decimal_payload)
    with pytest.raises(ValueError, match="source_row_count"):
        research_strategy_signal_confidence_decay_bridge_report_payload(decimal_payload)


def test_validation_rejects_non_decimal_times_duplicates_flags_and_tampering() -> None:
    with pytest.raises(ValueError, match="base_signal_confidence_score"):
        signal_input(base_signal_confidence_score=0.7)
    with pytest.raises(ValueError, match="cost_drag_score"):
        signal_input(cost_drag_score=d("-0.1"))
    with pytest.raises(ValueError, match="observed_at"):
        signal_input(observed_at=datetime(2026, 7, 8, 11, 50))
    with pytest.raises(ValueError, match="generated_at"):
        report(signal_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="must not be after generated_at"):
        report(signal_input(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="duplicate"):
        report(signal_input(signal_ref="same"), signal_input(signal_ref="same"))
    with pytest.raises(ValueError, match="threshold"):
        config(min_pass_authority_score=d("0.400000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    summary = report(signal_input())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary.rows[0],
            confidence_decay_bridge_score=d("0.500000"),
            derived_validation_digest=summary.rows[0].derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            source_row_count=d("0.000000"),
            derived_validation_digest=summary.derived_validation_digest,
        )
    with pytest.raises(ValueError, match="config_version"):
        replace(
            summary,
            config_version="research-strategy-signal-confidence-decay-bridge-report-v9",
            derived_validation_digest="",
        )


def test_public_dataclasses_are_frozen_and_module_has_no_forbidden_surfaces() -> None:
    import polymarket_alpha_lab.research_strategy_signal_confidence_decay_bridge_report as module

    summary = report(signal_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    with pytest.raises(FrozenInstanceError):
        row.status = "block"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)

    source = inspect.getsource(module)
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_SIGNAL_CONFIDENCE_DECAY_BRIDGE_STATUSES",
        "ResearchStrategySignalConfidenceDecayBridgeConfig",
        "ResearchStrategySignalConfidenceDecayBridgeInput",
        "ResearchStrategySignalConfidenceDecayBridgeRow",
        "ResearchStrategySignalConfidenceDecayBridgeReport",
        "build_research_strategy_signal_confidence_decay_bridge_report",
        "research_strategy_signal_confidence_decay_bridge_report_payload",
    )
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

    forbidden_source_terms = (
        "cand" + "idate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "private_key",
        "wal" + "let",
        "or" + "der",
        "trad" + "e",
        "pos" + "ition",
        "siz" + "ing",
        "reco" + "mmend",
        "request",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    )
    assert all(term not in source.lower() for term in forbidden_source_terms)

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


def assert_no_decimal_or_raw_numeric_values(value: object) -> None:
    assert not any(
        type(item) in (Decimal, int, float)
        for item in _walk_payload_values(value)
    )


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _refresh_report_payload_digest(payload: dict[str, Any]) -> None:
    comparable = dict(payload)
    comparable.pop("derived_validation_digest", None)
    payload["derived_validation_digest"] = _payload_digest(comparable)


def _refresh_row_payload_digest(payload: dict[str, Any]) -> None:
    comparable = dict(payload)
    comparable.pop("derived_validation_digest", None)
    payload["derived_validation_digest"] = _payload_digest(comparable)


def _payload_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
