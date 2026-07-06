from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import strategy_candidate_resolution_evidence_weight_v2 as module
from polymarket_alpha_lab.strategy_candidate_resolution_evidence_weight_v2 import (
    StrategyCandidateResolutionEvidenceWeightV2Config,
    StrategyCandidateResolutionEvidenceWeightV2Evidence,
    StrategyCandidateResolutionEvidenceWeightV2Report,
    StrategyCandidateResolutionEvidenceWeightV2Row,
    build_strategy_candidate_resolution_evidence_weight_v2_report,
    strategy_candidate_resolution_evidence_weight_v2_payload,
    validate_strategy_candidate_resolution_evidence_weight_v2_public_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def generated_at() -> module.datetime:
    return module.datetime(2026, 7, 6, 12, 0, tzinfo=module.UTC)


def config(**overrides: object) -> StrategyCandidateResolutionEvidenceWeightV2Config:
    values: dict[str, object] = {
        "config_version": "resolution-evidence-weight-test",
        "official_source_bonus": d("0.100000"),
        "weak_evidence_penalty": d("0.150000"),
        "corroboration_bonus_per_extra_source": d("0.050000"),
        "min_strong_resolution_evidence_weight": d("0.700000"),
        "min_watch_resolution_evidence_weight": d("0.400000"),
    }
    values.update(overrides)
    return StrategyCandidateResolutionEvidenceWeightV2Config(**values)


def evidence(**overrides: object) -> StrategyCandidateResolutionEvidenceWeightV2Evidence:
    values: dict[str, object] = {
        "candidate_id": "candidate-alpha",
        "market_slug": "policy-rate-alpha",
        "question": "Will the policy rate finish above the threshold?",
        "resolution_outcome": "yes",
        "observed_at": module.datetime(2026, 7, 6, 11, 0, tzinfo=module.UTC),
        "evidence_source": "official-bulletin",
        "evidence_kind": "official-resolution-notice",
        "source_quality_score": d("0.800000"),
        "specificity_score": d("0.900000"),
        "recency_score": d("0.700000"),
        "independence_score": d("0.800000"),
        "official_source": True,
        "weak_evidence": False,
        "reason_codes": ("official_resolution_notice",),
    }
    values.update(overrides)
    return StrategyCandidateResolutionEvidenceWeightV2Evidence(**values)


def report(
    *items: StrategyCandidateResolutionEvidenceWeightV2Evidence,
) -> StrategyCandidateResolutionEvidenceWeightV2Report:
    return build_strategy_candidate_resolution_evidence_weight_v2_report(
        items or (evidence(),),
        config=config(),
        generated_at=generated_at(),
    )


def assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (float, int, Decimal):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_scalars(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_numeric_scalars(item)


def test_resolution_evidence_weighting_combines_base_quality_and_corroboration() -> None:
    first = evidence()
    second = evidence(
        evidence_source="research-summary",
        evidence_kind="independent-resolution-summary",
        source_quality_score=d("0.600000"),
        specificity_score=d("0.700000"),
        recency_score=d("0.500000"),
        independence_score=d("0.600000"),
        official_source=False,
        reason_codes=("independent_summary",),
    )

    result = report(first, second)

    assert result.candidate_count == d("1.000000")
    assert result.strong_count == d("1.000000")
    assert result.watch_count == d("0.000000")
    assert result.weak_count == d("0.000000")
    assert result.report_status == "strong"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    row = result.rows[0]
    assert row.evidence_count == d("2.000000")
    assert row.unique_source_count == d("2.000000")
    assert row.average_base_evidence_score == d("0.700000")
    assert row.official_evidence_boost == d("0.100000")
    assert row.corroboration_boost == d("0.050000")
    assert row.weak_evidence_penalty == d("0.000000")
    assert row.resolution_evidence_weight == d("0.850000")
    assert row.evidence_status == "strong"
    assert "official_evidence_boost_applied" in row.reason_codes
    assert "corroborated_resolution_evidence" in row.reason_codes


def test_weak_evidence_penalties_reduce_resolution_weight() -> None:
    weak = evidence(
        evidence_source="community-rumor",
        evidence_kind="low-confidence-summary",
        official_source=False,
        weak_evidence=True,
        reason_codes=("weak_evidence_flagged",),
    )

    row = report(weak).rows[0]

    assert row.average_base_evidence_score == d("0.800000")
    assert row.weak_evidence_penalty == d("0.150000")
    assert row.resolution_evidence_weight == d("0.650000")
    assert row.evidence_status == "watch"
    assert "weak_resolution_evidence_penalty" in row.reason_codes


def test_official_evidence_boosts_otherwise_watch_candidate_to_strong() -> None:
    without_official = evidence(
        evidence_source="research-summary",
        evidence_kind="independent-resolution-summary",
        source_quality_score=d("0.650000"),
        specificity_score=d("0.650000"),
        recency_score=d("0.650000"),
        independence_score=d("0.650000"),
        official_source=False,
        reason_codes=("independent_summary",),
    )
    with_official = replace(without_official, official_source=True)

    watch_row = report(without_official).rows[0]
    strong_row = report(with_official).rows[0]

    assert watch_row.resolution_evidence_weight == d("0.650000")
    assert watch_row.evidence_status == "watch"
    assert strong_row.resolution_evidence_weight == d("0.750000")
    assert strong_row.evidence_status == "strong"


def test_payload_serializes_decimal_strings_flags_and_digests() -> None:
    result = report(evidence())

    payload = strategy_candidate_resolution_evidence_weight_v2_payload(result)

    assert payload["candidate_count"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert len(payload["derived_validation_digest"]) == 64
    row = payload["rows"][0]
    assert row["average_base_evidence_score"] == "0.800000"
    assert row["resolution_evidence_weight"] == "0.900000"
    assert row["paper_only"] is True
    assert row["report_only"] is True
    assert row["readonly"] is True
    assert len(row["derived_validation_digest"]) == 64
    assert_no_public_numeric_scalars(payload)
    assert validate_strategy_candidate_resolution_evidence_weight_v2_public_payload(payload)
    assert strategy_candidate_resolution_evidence_weight_v2_payload(payload) == payload


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    cfg = config()
    item = evidence()
    result = report(item)

    with pytest.raises(FrozenInstanceError):
        item.candidate_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].evidence_status = "weak"  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_quality_score must be a Decimal"):
        replace(item, source_quality_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="candidate_count must be a Decimal"):
        replace(result, candidate_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(cfg, paper_only=False)
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        evidence(observed_at=module.datetime(2026, 7, 6, 11, 0))


def test_derived_validation_digest_rejects_dataclass_and_payload_tampering() -> None:
    result = report(evidence())
    row = result.rows[0]

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(row, resolution_evidence_weight=d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(result, strong_count=d("0.000000"))

    payload = strategy_candidate_resolution_evidence_weight_v2_payload(result)
    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_candidate_resolution_evidence_weight_v2_payload(missing_digest)

    tampered_report = dict(payload)
    tampered_report["strong_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_candidate_resolution_evidence_weight_v2_payload(tampered_report)

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0])]
    tampered_row["rows"][0]["evidence_status"] = "weak"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_candidate_resolution_evidence_weight_v2_payload(tampered_row)


def test_public_payload_rejects_unsafe_public_keys_and_values() -> None:
    payload = strategy_candidate_resolution_evidence_weight_v2_payload(report(evidence()))

    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_terms:
        unsafe_key_payload = dict(payload)
        unsafe_key_payload[f"{term}_field"] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            strategy_candidate_resolution_evidence_weight_v2_payload(unsafe_key_payload)

        unsafe_value_payload = dict(payload)
        unsafe_value_payload["market_slug"] = f"{term} reference"
        with pytest.raises(ValueError, match="unsafe"):
            strategy_candidate_resolution_evidence_weight_v2_payload(unsafe_value_payload)


def test_public_dataclasses_reject_subclassing() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):

        class ConfigSubclass(StrategyCandidateResolutionEvidenceWeightV2Config):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class EvidenceSubclass(StrategyCandidateResolutionEvidenceWeightV2Evidence):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class RowSubclass(StrategyCandidateResolutionEvidenceWeightV2Row):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ReportSubclass(StrategyCandidateResolutionEvidenceWeightV2Report):
            pass


def test_module_has_no_external_or_unsafe_execution_surface() -> None:
    source = inspect.getsource(module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "http",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
    }
    forbidden_attr_fragments = (
        "broker",
        "credential",
        "private_key",
        "secret",
        "token",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            if isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
        if isinstance(node, ast.Attribute):
            attr = node.attr.lower()
            assert not any(fragment in attr for fragment in forbidden_attr_fragments)

    public_names = set(module.__all__)
    assert public_names == {
        "StrategyCandidateResolutionEvidenceWeightV2Config",
        "StrategyCandidateResolutionEvidenceWeightV2Evidence",
        "StrategyCandidateResolutionEvidenceWeightV2Report",
        "StrategyCandidateResolutionEvidenceWeightV2Row",
        "build_strategy_candidate_resolution_evidence_weight_v2_report",
        "strategy_candidate_resolution_evidence_weight_v2_payload",
        "validate_strategy_candidate_resolution_evidence_weight_v2_public_payload",
    }
