from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_claim_authority_memory_ladder_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_claim_authority_memory_ladder_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_memory_age_seconds": d("3600.000000"),
        "stale_memory_age_seconds": d("86400.000000"),
        "watch_ladder_score": d("0.250000"),
        "block_ladder_score": d("0.700000"),
        "watch_authority_score": d("0.700000"),
        "block_authority_score": d("0.300000"),
        "watch_memory_reuse_score": d("0.600000"),
        "block_memory_reuse_score": d("0.300000"),
        "watch_claim_confidence_score": d("0.700000"),
        "block_claim_confidence_score": d("0.500000"),
        "watch_contradiction_score": d("0.300000"),
        "block_contradiction_score": d("0.700000"),
        "watch_support_gap_score": d("0.500000"),
        "block_support_gap_score": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchSourceClaimAuthorityMemoryLadderConfig(**values)


def input_row(
    index: int,
    *,
    claim_bucket: str = "alpha-pass",
    authority_bucket: str | None = None,
    claim_observed_at: datetime | None = None,
    memory_last_checked_at: datetime | None = None,
    authority_score: Decimal = d("0.950000"),
    memory_reuse_score: Decimal = d("0.900000"),
    claim_confidence_score: Decimal = d("0.920000"),
    contradiction_score: Decimal = d("0.050000"),
    supporting_evidence_count: Decimal = d("3.000000"),
    required_evidence_count: Decimal = d("3.000000"),
    reason_codes: tuple[str, ...] = (),
) -> Any:
    module = api()
    return module.ResearchSourceClaimAuthorityMemoryLadderInput(
        claim_bucket=claim_bucket,
        authority_bucket=authority_bucket or f"authority-{index:03d}",
        private_candidate_reference=(
            f"raw_candidate_id=CAND-{index:03d}; token=secret-{index}"
        ),
        private_market_reference=(
            f"market_id=0xMARKET{index:03d}; market_slug=will-alpha-{index}; "
            f"market_question=Will Alpha resolve {index}?"
        ),
        private_source_reference=(
            "https://authority.example.test/private?"
            f"dsn=postgres://user:pass@host/db&table=authority_table_{index}; "
            f"wallet=0xabc; order={index}; trade={index}; live feed; source text"
        ),
        claim_observed_at=claim_observed_at
        if claim_observed_at is not None
        else GENERATED_AT - timedelta(hours=1),
        memory_last_checked_at=memory_last_checked_at
        if memory_last_checked_at is not None
        else GENERATED_AT - timedelta(minutes=30),
        authority_score=authority_score,
        memory_reuse_score=memory_reuse_score,
        claim_confidence_score=claim_confidence_score,
        contradiction_score=contradiction_score,
        supporting_evidence_count=supporting_evidence_count,
        required_evidence_count=required_evidence_count,
        reason_codes=reason_codes,
    )


def build_report(
    rows: tuple[Any, ...],
    *,
    config: object | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    module = api()
    return module.build_research_source_claim_authority_memory_ladder_report(
        rows,
        generated_at=generated_at,
        config=config if config is not None else cfg(),
    )


def test_memory_ladder_scores_claim_authority_without_public_raw_surfaces() -> None:
    module = api()
    report = build_report(
        (
            input_row(
                1,
                claim_bucket="alpha-pass",
                authority_bucket="authority-pass",
            ),
            input_row(
                2,
                claim_bucket="beta-watch",
                authority_bucket="authority-watch",
                memory_last_checked_at=GENERATED_AT - timedelta(hours=12),
                authority_score=d("0.650000"),
                memory_reuse_score=d("0.450000"),
                claim_confidence_score=d("0.700000"),
                contradiction_score=d("0.350000"),
                supporting_evidence_count=d("1.000000"),
                required_evidence_count=d("3.000000"),
                reason_codes=("manual_memory_review",),
            ),
            input_row(
                3,
                claim_bucket="gamma-block",
                authority_bucket="authority-block",
                memory_last_checked_at=GENERATED_AT - timedelta(days=4),
                authority_score=d("0.200000"),
                memory_reuse_score=d("0.200000"),
                claim_confidence_score=d("0.400000"),
                contradiction_score=d("0.850000"),
                supporting_evidence_count=d("0.000000"),
                required_evidence_count=d("3.000000"),
                reason_codes=("primary_memory_stale",),
            ),
        ),
    )

    assert report.status == "block"
    assert report.row_count == d("3.000000")
    assert report.stale_memory_count == d("2.000000")
    assert report.authority_gap_count == d("2.000000")
    assert report.memory_reuse_gap_count == d("2.000000")
    assert report.claim_confidence_gap_count == d("1.000000")
    assert report.contradiction_count == d("2.000000")
    assert report.support_gap_count == d("2.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_memory_ladder_score == d("0.445830")
    assert report.max_memory_ladder_score == d("0.841667")

    block_row, watch_row, pass_row = report.rows
    assert type(block_row) is module.ResearchSourceClaimAuthorityMemoryLadderRow
    assert block_row.claim_digest.startswith("sha256:")
    assert block_row.status == "block"
    assert block_row.claim_age_seconds == d("3600.000000")
    assert block_row.memory_age_seconds == d("345600.000000")
    assert block_row.memory_decay_score == d("1.000000")
    assert block_row.authority_gap_score == d("0.800000")
    assert block_row.memory_reuse_gap_score == d("0.800000")
    assert block_row.claim_confidence_gap_score == d("0.600000")
    assert block_row.support_gap_score == d("1.000000")
    assert block_row.memory_ladder_score == d("0.841667")
    assert block_row.reason_codes == (
        "authority_memory_block",
        "authority_score_block",
        "claim_confidence_block",
        "claim_contradiction_block",
        "input_primary_memory_stale",
        "memory_reuse_block",
        "support_gap_block",
    )

    assert watch_row.status == "watch"
    assert watch_row.memory_age_seconds == d("43200.000000")
    assert watch_row.memory_decay_score == d("0.478261")
    assert watch_row.authority_gap_score == d("0.350000")
    assert watch_row.memory_reuse_gap_score == d("0.550000")
    assert watch_row.claim_confidence_gap_score == d("0.300000")
    assert watch_row.support_gap_score == d("0.666667")
    assert watch_row.memory_ladder_score == d("0.449155")
    assert "input_manual_memory_review" in watch_row.reason_codes

    assert pass_row.status == "pass"
    assert pass_row.memory_ladder_score == d("0.046667")
    assert pass_row.reason_codes == (
        "authority_memory_clear",
        "authority_score_clear",
        "claim_confidence_clear",
        "claim_contradiction_clear",
        "memory_reuse_clear",
        "support_gap_clear",
    )

    payload = module.research_source_claim_authority_memory_ladder_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "raw_candidate_id",
        "cand-001",
        "market_id",
        "market_slug",
        "market_question",
        "will alpha resolve",
        "https://authority.example.test",
        "dsn=postgres",
        "authority_table",
        "token=secret",
        "wallet=0xabc",
        "order=1",
        "trade=1",
        "live feed",
        "source text",
        "private_candidate_reference",
        "private_market_reference",
        "private_source_reference",
    ):
        assert forbidden not in encoded
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_payload_digest_is_deterministic_and_validated() -> None:
    module = api()
    first = build_report(
        (
            input_row(
                2,
                claim_bucket="beta-watch",
                memory_last_checked_at=GENERATED_AT - timedelta(hours=8),
                contradiction_score=d("0.400000"),
            ),
            input_row(1, claim_bucket="alpha-pass"),
        ),
    )
    second = build_report(
        (
            input_row(1, claim_bucket="alpha-pass"),
            input_row(
                2,
                claim_bucket="beta-watch",
                memory_last_checked_at=GENERATED_AT - timedelta(hours=8),
                contradiction_score=d("0.400000"),
            ),
        ),
    )

    payload = module.research_source_claim_authority_memory_ladder_report_payload(first)
    payload_again = module.research_source_claim_authority_memory_ladder_report_payload(
        second,
    )
    unsigned_payload = dict(payload)
    digest = unsigned_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert payload == payload_again
    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    assert len(module.research_source_claim_authority_memory_ladder_report_digest(first)) == 64

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["status"] = "watch"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered = dict(payload)
    tampered["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_source_claim_authority_memory_ladder_report_payload(tampered)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = cfg()
    sample_input = input_row(1)
    sample_report = build_report((sample_input,))
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_input, sample_row, sample_report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        cfg(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(sample_input, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(sample_row, readonly=False)


def test_validation_rejects_bad_numerics_statuses_times_and_payload_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="fresh_memory_age_seconds"):
        cfg(fresh_memory_age_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_ladder_score"):
        cfg(watch_ladder_score=DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="block_ladder_score"):
        cfg(watch_ladder_score=d("0.700000"), block_ladder_score=d("0.500000"))
    with pytest.raises(ValueError, match="authority_score"):
        input_row(1, authority_score=d("1.100000"))
    with pytest.raises(ValueError, match="supporting_evidence_count"):
        input_row(
            1,
            supporting_evidence_count=d("4.000000"),
            required_evidence_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        input_row(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="claim_observed_at"):
        build_report((input_row(1, claim_observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="memory_last_checked_at"):
        build_report(
            (
                input_row(
                    1,
                    memory_last_checked_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_source_claim_authority_memory_ladder_report(
            (),
            generated_at=datetime(2026, 7, 9, 12, 0),
            config=cfg(),
        )
    with pytest.raises(ValueError, match="status"):
        replace(build_report((input_row(1),)).rows[0], status="blocked")

    payload = module.research_source_claim_authority_memory_ladder_report_payload(
        build_report((input_row(1),)),
    )
    bad_payload = dict(payload)
    bad_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_source_claim_authority_memory_ladder_report_payload(bad_payload)
    unsafe_payload = dict(payload)
    unsafe_payload["raw_candidate"] = "CAND-001"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_source_claim_authority_memory_ladder_report_payload(
            unsafe_payload,
        )


@pytest.mark.parametrize(
    ("field_name", "wrong_value"),
    (
        ("stale_memory_count", d("0.000000")),
        ("authority_gap_count", d("0.000000")),
        ("memory_reuse_gap_count", d("0.000000")),
        ("claim_confidence_gap_count", d("0.000000")),
        ("contradiction_count", d("0.000000")),
        ("support_gap_count", d("0.000000")),
    ),
)
def test_report_rejects_tampered_aggregate_gap_counts(
    field_name: str,
    wrong_value: Decimal,
) -> None:
    report = build_report(
        (
            input_row(1),
            input_row(
                2,
                memory_last_checked_at=GENERATED_AT - timedelta(hours=12),
                authority_score=d("0.650000"),
                memory_reuse_score=d("0.450000"),
                claim_confidence_score=d("0.700000"),
                contradiction_score=d("0.350000"),
                supporting_evidence_count=d("1.000000"),
                required_evidence_count=d("3.000000"),
            ),
            input_row(
                3,
                memory_last_checked_at=GENERATED_AT - timedelta(days=4),
                authority_score=d("0.200000"),
                memory_reuse_score=d("0.200000"),
                claim_confidence_score=d("0.400000"),
                contradiction_score=d("0.850000"),
                supporting_evidence_count=d("0.000000"),
                required_evidence_count=d("3.000000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match=field_name):
        replace(report, **{field_name: wrong_value, "derived_validation_digest": ""})


def test_owned_module_has_no_side_effect_imports_or_live_execution_calls() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_imports = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "web3",
    )
    forbidden_calls = (
        "open(",
        "connect(",
        "request(",
        "post(",
        "get(",
        "send(",
        "submit(",
        "cancel(",
        "place_order(",
        "replace_order(",
        "recommendation",
        "position_size",
    )

    assert all(term not in lowered for term in forbidden_imports)
    assert all(term not in lowered for term in forbidden_calls)


def test_public_api_is_exactly_the_report_only_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_CLAIM_AUTHORITY_MEMORY_LADDER_REPORT_CONFIG_VERSION",
        "ResearchSourceClaimAuthorityMemoryLadderConfig",
        "ResearchSourceClaimAuthorityMemoryLadderInput",
        "ResearchSourceClaimAuthorityMemoryLadderReport",
        "ResearchSourceClaimAuthorityMemoryLadderRow",
        "build_research_source_claim_authority_memory_ladder_report",
        "research_source_claim_authority_memory_ladder_report_digest",
        "research_source_claim_authority_memory_ladder_report_payload",
    )


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
