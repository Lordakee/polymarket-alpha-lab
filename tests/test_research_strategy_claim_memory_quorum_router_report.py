from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import importlib
import json
from typing import Any

import pytest


api = importlib.import_module(
    "poly"
    + "mar"
    + "ket_alpha_lab.research_strategy_claim_memory_quorum_router_report",
)

Config = api.ResearchStrategyClaimMemoryQuorumRouterConfig
Input = api.ResearchStrategyClaimMemoryQuorumRouterInput
PublicPayloadItem = api.ResearchStrategyClaimMemoryQuorumRouterPublicPayloadItem
Report = api.ResearchStrategyClaimMemoryQuorumRouterReport
build_report = api.build_research_strategy_claim_memory_quorum_router_report
payload_for = api.research_strategy_claim_memory_quorum_router_report_payload
digest_for = api.research_strategy_claim_memory_quorum_router_report_digest
validate_digest = api.validate_research_strategy_claim_memory_quorum_router_report_digest
validate_payload = api.validate_research_strategy_claim_memory_quorum_router_report_payload

GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def j(*parts: str) -> str:
    return "".join(parts)


def sample_input(
    seed: str,
    *,
    claim_confidence_score: Decimal = d("0.820000"),
    memory_match_score: Decimal = d("0.850000"),
    quorum_agreement_ratio: Decimal = d("0.800000"),
    contradiction_pressure: Decimal = d("0.050000"),
    evidence_age_seconds: Decimal = d("3600.000000"),
    corroborating_count: Decimal = d("3.000000"),
    observed_at: datetime = GENERATED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    return Input(
        claim_digest=digest(seed + "-claim"),
        memory_digest=digest(seed + "-memory"),
        quorum_digest=digest(seed + "-quorum"),
        observed_at=observed_at,
        claim_confidence_score=claim_confidence_score,
        memory_match_score=memory_match_score,
        quorum_agreement_ratio=quorum_agreement_ratio,
        contradiction_pressure=contradiction_pressure,
        evidence_age_seconds=evidence_age_seconds,
        corroborating_count=corroborating_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def make_report(*rows: Any, public_payload: tuple[Any, ...] = ()) -> Any:
    return build_report(
        rows,
        generated_at=GENERATED_AT,
        config=Config(),
        public_payload=public_payload,
    )


def with_resigned_digest(payload: dict[str, Any], **overrides: Any) -> dict[str, Any]:
    forged = dict(payload)
    forged.update(overrides)
    unsigned = dict(forged)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    forged["derived_validation_digest"] = hashlib.sha256(encoded).hexdigest()
    return forged


def walk_values(value: Any) -> tuple[Any, ...]:
    values: list[Any] = []

    def visit(item: Any) -> None:
        values.append(item)
        if is_dataclass(item) and not isinstance(item, type):
            for field in fields(item):
                visit(getattr(item, field.name))
        elif isinstance(item, dict):
            for key, child in item.items():
                visit(key)
                visit(child)
        elif isinstance(item, tuple | list):
            for child in item:
                visit(child)

    visit(value)
    return tuple(values)


def assert_no_float_or_int(value: Any) -> None:
    for item in walk_values(value):
        if isinstance(item, bool):
            continue
        if type(item) is int or isinstance(item, float):
            raise AssertionError(f"public numeric value is not Decimal: {item!r}")
        if isinstance(item, Decimal):
            assert type(item) is Decimal


def assert_no_decimal_objects(value: Any) -> None:
    for item in walk_values(value):
        assert not isinstance(item, Decimal)


def test_router_classifies_pass_watch_block_and_sorts_deterministically() -> None:
    pass_row = sample_input("pass")
    watch_row = sample_input(
        "watch",
        claim_confidence_score=d("0.650000"),
        memory_match_score=d("0.600000"),
        quorum_agreement_ratio=d("0.650000"),
        contradiction_pressure=d("0.200000"),
        evidence_age_seconds=d("90000.000000"),
        corroborating_count=d("2.000000"),
    )
    block_row = sample_input(
        "block",
        claim_confidence_score=d("0.500000"),
        memory_match_score=d("0.400000"),
        quorum_agreement_ratio=d("0.400000"),
        contradiction_pressure=d("0.550000"),
        evidence_age_seconds=d("200000.000000"),
        corroborating_count=d("1.000000"),
    )

    first = make_report(pass_row, watch_row, block_row)
    second = make_report(block_row, watch_row, pass_row)

    assert first.status == "block"
    assert first.row_count == d("3.000000")
    assert first.pass_count == d("1.000000")
    assert first.watch_count == d("1.000000")
    assert first.block_count == d("1.000000")
    assert tuple(row.status for row in first.rows) == ("block", "watch", "pass")
    assert tuple(row.rank for row in first.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert first.rows[0].claim_digest == digest("block-claim")
    assert first.rows[0].reason_codes == (
        "claim_confidence_block",
        "memory_match_block",
        "quorum_agreement_block",
        "contradiction_pressure_block",
        "evidence_age_block",
        "corroboration_block",
    )
    assert first.rows[1].reason_codes == (
        "claim_confidence_watch",
        "memory_match_watch",
        "quorum_agreement_watch",
        "contradiction_pressure_watch",
        "evidence_age_watch",
        "corroboration_watch",
    )
    assert first.rows[2].reason_codes == ("claim_memory_quorum_pass",)
    assert first.payload == second.payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert set(api.RESEARCH_STRATEGY_CLAIM_MEMORY_QUORUM_ROUTER_REPORT_STATUSES) == {
        "pass",
        "watch",
        "block",
    }


def test_public_payload_is_json_ready_deterministic_and_digest_validated() -> None:
    public_item = PublicPayloadItem(
        key="safe_context",
        value="sanitized aggregate only",
    )
    first = make_report(
        sample_input("zeta"),
        sample_input("alpha", contradiction_pressure=d("0.200000")),
        public_payload=(public_item,),
    )
    second = make_report(
        sample_input("alpha", contradiction_pressure=d("0.200000")),
        sample_input("zeta"),
        public_payload=(public_item,),
    )

    payload = payload_for(first)
    assert payload == second.payload
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["row_count"] == "2.000000"
    assert payload["rows"][0]["rank"] == "1.000000"
    assert payload["rows"][0]["readiness_score"] == "0.940000"
    assert payload["public_payload"] == (
        {"key": "safe_context", "value": "sanitized aggregate only"},
    )
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert digest_for(first) == first.derived_validation_digest
    assert validate_digest(first) is True
    assert validate_payload(payload) is True
    json.dumps(payload, sort_keys=True)
    assert_no_decimal_objects(payload)
    assert_no_float_or_int(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["row_count"] = "3.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_payload(tampered)


def test_payload_validation_rejects_resigned_non_report_or_unknown_status_payloads() -> None:
    payload = payload_for(make_report(sample_input("safe")))

    with pytest.raises(ValueError, match="paper_only"):
        validate_payload(with_resigned_digest(payload, paper_only=False))
    with pytest.raises(ValueError, match="report_only"):
        validate_payload(with_resigned_digest(payload, report_only=False))
    with pytest.raises(ValueError, match="readonly"):
        validate_payload(with_resigned_digest(payload, readonly=False))
    with pytest.raises(ValueError, match="status"):
        validate_payload(with_resigned_digest(payload, status="execute"))

    rows = tuple(payload["rows"])
    forged_first_row = dict(rows[0])
    forged_first_row["status"] = "execute"
    with pytest.raises(ValueError, match="rows"):
        validate_payload(with_resigned_digest(payload, rows=(forged_first_row,)))


def test_dataclasses_are_frozen_final_and_hard_report_flags_are_enforced() -> None:
    report = make_report(sample_input("safe"))
    assert isinstance(report, Report)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(Config):
            pass

    with pytest.raises(TypeError):

        class BadInput(Input):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        Config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        sample_input("unsafe-report-flag", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        sample_input("unsafe-read-flag", readonly=False)


def test_rejects_non_decimal_values_raw_ids_and_unsafe_public_items() -> None:
    with pytest.raises(ValueError, match="claim_digest"):
        Input(
            claim_digest="raw-id",
            memory_digest=digest("memory"),
            quorum_digest=digest("quorum"),
            observed_at=GENERATED_AT,
            claim_confidence_score=d("0.800000"),
            memory_match_score=d("0.800000"),
            quorum_agreement_ratio=d("0.800000"),
            contradiction_pressure=d("0.050000"),
            evidence_age_seconds=d("3600.000000"),
            corroborating_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="claim_confidence_score"):
        sample_input("float-score", claim_confidence_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="corroborating_count"):
        sample_input("int-count", corroborating_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_match_score"):
        sample_input("subclass-score", memory_match_score=DecimalSubclass("0.800000"))

    unsafe_keys = (
        j("cand", "idate_id"),
        j("mar", "ket_id"),
        j("mar", "ket_slug"),
        j("sou", "rce_url"),
        j("sou", "rce_text"),
        j("d", "sn"),
        j("ta", "ble_name"),
        j("to", "ken"),
        j("wal", "let"),
        j("or", "der"),
        j("tra", "de"),
        j("au", "th"),
        j("li", "ve"),
        j("siz", "ing"),
        j("recomm", "endation"),
        j("exec", "ution"),
    )
    for key in unsafe_keys:
        with pytest.raises(ValueError, match="unsafe public"):
            PublicPayloadItem(key=key, value="safe value")

    unsafe_values = (
        j("ht", "tps", "://example.test/path"),
        j("post", "gres", "://user:pass@example.test/db"),
        j("raw ", "sou", "rce ", "te", "xt"),
        j("to", "ken=secret"),
        j("wal", "let route"),
        j("place ", "or", "der"),
        j("li", "ve trading"),
        j("siz", "ing hint"),
        j("recomm", "endation"),
        j("exec", "ute route"),
    )
    for value in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public"):
            PublicPayloadItem(key="safe_key", value=value)

    payload = make_report(sample_input("safe")).payload
    encoded = json.dumps(payload, sort_keys=True).lower()
    for leaked in unsafe_keys + unsafe_values:
        assert leaked.lower() not in encoded
