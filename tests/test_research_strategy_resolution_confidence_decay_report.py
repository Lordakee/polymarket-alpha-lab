from __future__ import annotations

import ast
import inspect
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_strategy_resolution_confidence_decay_report import (
    DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION,
    RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_STATUSES,
    ResearchStrategyResolutionConfidenceDecayConfig,
    ResearchStrategyResolutionConfidenceDecayInput,
    ResearchStrategyResolutionConfidenceDecayReport,
    ResearchStrategyResolutionConfidenceDecayRow,
    build_research_strategy_resolution_confidence_decay_report,
    research_strategy_resolution_confidence_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyResolutionConfidenceDecayConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION
        ),
        "official_evidence_watch_age_seconds": d("3600"),
        "official_evidence_block_age_seconds": d("21600"),
        "corroboration_watch_age_seconds": d("3600"),
        "corroboration_block_age_seconds": d("21600"),
        "rule_ambiguity_watch_threshold": d("0.300000"),
        "rule_ambiguity_block_threshold": d("0.700000"),
        "contradiction_pressure_watch_threshold": d("0.300000"),
        "contradiction_pressure_block_threshold": d("0.700000"),
        "manual_recheck_watch_age_seconds": d("3600"),
        "manual_recheck_block_age_seconds": d("21600"),
        "manual_recheck_urgency_watch_threshold": d("0.500000"),
        "manual_recheck_urgency_block_threshold": d("0.850000"),
    }
    values.update(overrides)
    return ResearchStrategyResolutionConfidenceDecayConfig(**values)


def decay_input(**overrides: object) -> ResearchStrategyResolutionConfidenceDecayInput:
    values = {
        "resolution_assumption_ref": "alpha-case",
        "official_evidence_observed_at": GENERATED_AT - timedelta(minutes=30),
        "corroboration_observed_at": GENERATED_AT - timedelta(minutes=30),
        "rule_clarity_score": d("0.900000"),
        "unresolved_contradiction_count": d("0"),
        "contradiction_severity_score": d("0.000000"),
        "last_manual_recheck_at": GENERATED_AT - timedelta(minutes=30),
    }
    values.update(overrides)
    return ResearchStrategyResolutionConfidenceDecayInput(**values)


def report(
    *rows: ResearchStrategyResolutionConfidenceDecayInput,
    cfg: ResearchStrategyResolutionConfidenceDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyResolutionConfidenceDecayReport:
    return build_research_strategy_resolution_confidence_decay_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_report_aggregates_resolution_confidence_decay_pressures() -> None:
    summary = report(
        decay_input(),
        decay_input(
            resolution_assumption_ref="beta-case",
            official_evidence_observed_at=GENERATED_AT - timedelta(seconds=12600),
            corroboration_observed_at=GENERATED_AT - timedelta(seconds=12600),
            rule_clarity_score=d("0.500000"),
            unresolved_contradiction_count=d("1"),
            contradiction_severity_score=d("0.500000"),
            last_manual_recheck_at=GENERATED_AT - timedelta(seconds=12600),
        ),
        decay_input(
            resolution_assumption_ref="gamma-case",
            official_evidence_observed_at=GENERATED_AT - timedelta(seconds=21600),
            corroboration_observed_at=GENERATED_AT - timedelta(seconds=21600),
            rule_clarity_score=d("0.200000"),
            unresolved_contradiction_count=d("2"),
            contradiction_severity_score=d("0.400000"),
            last_manual_recheck_at=GENERATED_AT - timedelta(seconds=21600),
        ),
    )

    assert summary.generated_at == GENERATED_AT
    assert (
        summary.config_version
        == DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION
    )
    assert summary.source_row_count == d("3")
    assert summary.pass_count == d("1")
    assert summary.watch_count == d("1")
    assert summary.block_count == d("1")
    assert summary.mean_official_evidence_age_pressure == d("0.500000")
    assert summary.mean_corroboration_freshness_score == d("0.500000")
    assert summary.mean_rule_ambiguity_score == d("0.466667")
    assert summary.mean_unresolved_contradiction_pressure == d("0.433333")
    assert summary.mean_manual_recheck_urgency_score == d("0.480000")
    assert summary.mean_resolution_confidence_decay_score == d("0.476000")
    assert summary.status == "block"
    assert summary.reason_codes == (
        "corroboration_freshness_review",
        "manual_recheck_review",
        "official_evidence_age_review",
        "resolution_confidence_decay_block",
        "rule_ambiguity_review",
        "unresolved_contradiction_review",
    )

    blocked = summary.rows[0]
    assert isinstance(blocked, ResearchStrategyResolutionConfidenceDecayRow)
    assert blocked.aggregate_row_number == d("1")
    assert len(blocked.aggregate_row_hash) == 64
    assert blocked.official_evidence_age_seconds == d("21600")
    assert blocked.official_evidence_age_pressure == d("1.000000")
    assert blocked.corroboration_freshness_score == d("0.000000")
    assert blocked.rule_ambiguity_score == d("0.800000")
    assert blocked.unresolved_contradiction_pressure == d("0.800000")
    assert blocked.manual_recheck_urgency_score == d("0.920000")
    assert blocked.resolution_confidence_decay_score == d("0.904000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "corroboration_freshness_block",
        "manual_recheck_urgency_block",
        "official_evidence_age_block",
        "rule_ambiguity_block",
        "unresolved_contradiction_block",
    )

    watched = summary.rows[1]
    assert watched.aggregate_row_number == d("2")
    assert watched.status == "watch"
    assert watched.manual_recheck_urgency_score == d("0.500000")
    assert watched.reason_codes == (
        "corroboration_freshness_watch",
        "manual_recheck_urgency_watch",
        "official_evidence_age_watch",
        "rule_ambiguity_watch",
        "unresolved_contradiction_watch",
    )

    passed = summary.rows[2]
    assert passed.aggregate_row_number == d("3")
    assert passed.status == "pass"
    assert passed.reason_codes == ("resolution_confidence_decay_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True
    assert len(passed.derived_validation_digest) == 64


def test_public_payload_is_deterministic_hashed_decimal_and_digest_guarded() -> None:
    sensitive_ref = (
        "candidate-alpha market-alpha will this resolve yes "
        "https://private.example/path?api_key=hidden-token table=db.events"
    )
    first_payload = research_strategy_resolution_confidence_decay_report_payload(
        report(decay_input(resolution_assumption_ref=sensitive_ref)),
    )
    second_payload = research_strategy_resolution_confidence_decay_report_payload(
        report(decay_input(resolution_assumption_ref=sensitive_ref)),
    )
    encoded = json.dumps(first_payload, sort_keys=True).lower()

    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["source_row_count"] == "1.000000"
    assert first_payload["rows"][0]["aggregate_row_number"] == "1.000000"
    assert len(first_payload["rows"][0]["aggregate_row_hash"]) == 64
    assert first_payload["rows"][0]["official_evidence_age_pressure"] == "0.000000"
    assert first_payload["rows"][0]["paper_only"] is True
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert len(first_payload["derived_validation_digest"]) == 64
    assert not any(type(value) in (Decimal, int, float) for value in _walk_payload_values(first_payload))

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
        "resolution_assumption_ref",
    )
    assert all(fragment not in encoded for fragment in forbidden_payload_fragments)

    tampered_payload = json.loads(json.dumps(first_payload))
    tampered_payload["rows"][0]["manual_recheck_urgency_score"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_resolution_confidence_decay_report_payload(tampered_payload)

    numeric_payload = json.loads(json.dumps(first_payload))
    numeric_payload["source_row_count"] = 1
    with pytest.raises(ValueError, match="source_row_count"):
        research_strategy_resolution_confidence_decay_report_payload(numeric_payload)

    unsafe_payload = json.loads(json.dumps(first_payload))
    unsafe_payload["source_url"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_resolution_confidence_decay_report_payload(unsafe_payload)


def test_validation_rejects_non_decimal_times_duplicates_flags_and_tampering() -> None:
    with pytest.raises(ValueError, match="rule_clarity_score"):
        decay_input(rule_clarity_score=0.7)
    with pytest.raises(ValueError, match="unresolved_contradiction_count"):
        decay_input(unresolved_contradiction_count=d("-1"))
    with pytest.raises(ValueError, match="official_evidence_observed_at"):
        decay_input(official_evidence_observed_at=datetime(2026, 7, 8, 11, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(decay_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="must not be after generated_at"):
        report(
            decay_input(
                official_evidence_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(
            decay_input(resolution_assumption_ref="same-case"),
            decay_input(resolution_assumption_ref="same-case"),
        )
    with pytest.raises(ValueError, match="threshold"):
        config(rule_ambiguity_watch_threshold=d("0.800000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    summary = report(decay_input())
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary.rows[0],
            manual_recheck_urgency_score=d("0.500000"),
            derived_validation_digest=summary.rows[0].derived_validation_digest,
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            summary,
            source_row_count=d("0"),
            derived_validation_digest=summary.derived_validation_digest,
        )


def test_public_dataclasses_are_frozen_and_module_has_no_forbidden_surfaces() -> None:
    import polymarket_alpha_lab.research_strategy_resolution_confidence_decay_report as module

    summary = report(decay_input())
    row = summary.rows[0]

    assert is_dataclass(row)
    assert RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_STATUSES == (
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
        "DEFAULT_RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_RESOLUTION_CONFIDENCE_DECAY_STATUSES",
        "ResearchStrategyResolutionConfidenceDecayConfig",
        "ResearchStrategyResolutionConfidenceDecayInput",
        "ResearchStrategyResolutionConfidenceDecayRow",
        "ResearchStrategyResolutionConfidenceDecayReport",
        "build_research_strategy_resolution_confidence_decay_report",
        "research_strategy_resolution_confidence_decay_report_payload",
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
        "pathlib",
        "source_url",
        "source_text",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "dsn",
        "private_key",
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
