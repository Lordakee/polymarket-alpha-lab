from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any

import pytest

from polymarket_alpha_lab.research_strategy_authority_claim_resolution_memory_guard_report import (
    AuthorityClaimResolutionMemoryGuardConfig,
    AuthorityClaimResolutionMemoryGuardInput,
    ResearchStrategyAuthorityClaimResolutionMemoryGuardRow,
    build_research_strategy_authority_claim_resolution_memory_guard_report,
    research_strategy_authority_claim_resolution_memory_guard_payload,
)


def _input(**overrides: object) -> AuthorityClaimResolutionMemoryGuardInput:
    values: dict[str, object] = {
        "raw_claim_reference": "candidate-raw-001::market-raw-777",
        "raw_authority_reference": "https://authority.example/resolution?id=secret-token",
        "authority_bucket": "official_resolution_memory",
        "claim_resolution_age_hours": Decimal("4.000000"),
        "authority_memory_age_hours": Decimal("6.000000"),
        "resolution_agreement_score": Decimal("0.960000"),
        "memory_recall_score": Decimal("0.940000"),
        "conflict_pressure": Decimal("0.040000"),
        "reason_codes": ("authority_memory_current",),
    }
    values.update(overrides)
    return AuthorityClaimResolutionMemoryGuardInput(**values)


def _digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _assert_no_json_number(value: object) -> None:
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, (int, float)):
        raise AssertionError(f"public payload leaked a JSON number: {value!r}")
    if isinstance(value, list):
        for item in value:
            _assert_no_json_number(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_json_number(item)
        return
    raise AssertionError(f"unexpected JSON payload type: {type(value)!r}")


def test_builds_deterministic_report_only_payload_without_raw_identifier_leakage() -> None:
    generated_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    report = build_research_strategy_authority_claim_resolution_memory_guard_report(
        (
            _input(),
            _input(
                raw_claim_reference="market_slug=will-sensitive-question-resolve",
                raw_authority_reference=(
                    "postgres://user:password@db.example/private_table"
                ),
                authority_bucket="appeal_resolution_memory",
                claim_resolution_age_hours=Decimal("19.000000"),
                authority_memory_age_hours=Decimal("44.000000"),
                resolution_agreement_score=Decimal("0.830000"),
                memory_recall_score=Decimal("0.760000"),
                conflict_pressure=Decimal("0.270000"),
                reason_codes=("authority_memory_stale",),
            ),
        ),
        generated_at=generated_at,
    )

    payload = research_strategy_authority_claim_resolution_memory_guard_payload(report)
    repeated = research_strategy_authority_claim_resolution_memory_guard_payload(report)

    assert payload == repeated
    assert payload == report.payload
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["status"] == "watch"
    assert payload["checked_count"] == "2"
    assert payload["pass_count"] == "1"
    assert payload["watch_count"] == "1"
    assert payload["block_count"] == "0"
    assert payload["derived_validation_digest"] == _digest(payload)
    assert {row["status"] for row in payload["rows"]} <= {"pass", "watch", "block"}
    assert payload["rows"][0]["memory_key"] != payload["rows"][1]["memory_key"]
    assert len(payload["rows"][0]["memory_key"]) == 64
    assert payload["rows"][0]["resolution_agreement_score"] == "0.960000"
    assert payload["rows"][1]["conflict_pressure"] == "0.270000"
    _assert_no_json_number(payload)

    encoded = json.dumps(payload, sort_keys=True)
    forbidden_fragments = (
        "candidate-raw-001",
        "market-raw-777",
        "will-sensitive-question-resolve",
        "https://",
        "postgres://",
        "private_table",
        "secret-token",
        "password",
        "wallet",
        "order",
        "trade",
    )
    for fragment in forbidden_fragments:
        assert fragment not in encoded


def test_blocks_when_resolution_memory_guard_thresholds_are_breached() -> None:
    report = build_research_strategy_authority_claim_resolution_memory_guard_report(
        (
            _input(
                claim_resolution_age_hours=Decimal("73.000000"),
                authority_memory_age_hours=Decimal("97.000000"),
                resolution_agreement_score=Decimal("0.610000"),
                memory_recall_score=Decimal("0.510000"),
                conflict_pressure=Decimal("0.890000"),
                reason_codes=("authority_claim_resolution_conflict",),
            ),
        ),
        generated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )

    payload = report.payload

    assert payload["status"] == "block"
    assert payload["rows"][0]["status"] == "block"
    assert payload["reason_codes"] == ["authority_claim_resolution_conflict"]


def test_payload_validation_rejects_tampering_and_unsafe_public_surfaces() -> None:
    report = build_research_strategy_authority_claim_resolution_memory_guard_report(
        (_input(),),
        generated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    payload = report.payload

    tampered = dict(payload)
    tampered["status"] = "ready"
    with pytest.raises(ValueError, match="status"):
        research_strategy_authority_claim_resolution_memory_guard_payload(tampered)

    tampered = dict(payload)
    tampered["status"] = "block"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_strategy_authority_claim_resolution_memory_guard_payload(tampered)

    unsafe = dict(payload)
    unsafe["source_url"] = "https://authority.example/private"
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_authority_claim_resolution_memory_guard_payload(unsafe)


def test_rejects_non_decimal_numerics_and_non_report_flags() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _input(claim_resolution_age_hours=4)

    with pytest.raises(ValueError, match="finite"):
        _input(conflict_pressure=Decimal("NaN"))

    with pytest.raises(ValueError, match="paper_only"):
        AuthorityClaimResolutionMemoryGuardConfig(paper_only=False)


def test_public_dataclasses_are_frozen() -> None:
    row = ResearchStrategyAuthorityClaimResolutionMemoryGuardRow(
        memory_key="a" * 64,
        authority_bucket="official_resolution_memory",
        status="pass",
        claim_resolution_age_hours=Decimal("4.000000"),
        authority_memory_age_hours=Decimal("6.000000"),
        resolution_agreement_score=Decimal("0.960000"),
        memory_recall_score=Decimal("0.940000"),
        conflict_pressure=Decimal("0.040000"),
        reason_codes=("authority_memory_current",),
    )

    with pytest.raises(FrozenInstanceError):
        row.status = "watch"
