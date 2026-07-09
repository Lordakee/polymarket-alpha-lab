from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

import pytest

from polymarket_alpha_lab.research_source_authority_claim_conflict_memory_report import (
    ResearchSourceAuthorityClaimConflictMemoryConfig,
    ResearchSourceAuthorityClaimConflictMemoryInput,
    ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount,
    ResearchSourceAuthorityClaimConflictMemoryReport,
    ResearchSourceAuthorityClaimConflictMemoryRow,
    build_research_source_authority_claim_conflict_memory_report,
    research_source_authority_claim_conflict_memory_report_digest,
    research_source_authority_claim_conflict_memory_report_payload,
    validate_research_source_authority_claim_conflict_memory_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0")
ONE = Decimal("1")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedInputShape:
    candidate_ref: str
    market_ref: str
    claim_text: str
    source_reference: str
    source_excerpt: str
    source_family: str
    claim_side: str
    authority_score: Decimal
    observed_at: datetime
    conflict_memory_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> ResearchSourceAuthorityClaimConflictMemoryConfig:
    values = {
        "config_version": "research-source-authority-claim-conflict-memory-report-v0",
        "fresh_age_seconds": d("86400.000000"),
        "stale_age_seconds": d("604800.000000"),
        "min_distinct_source_families": d("2"),
        "material_authority_score": d("0.650000"),
        "pass_authority_gap": d("0.250000"),
        "watch_conflict_memory_count": d("1"),
        "block_conflict_memory_count": d("2"),
    }
    values.update(overrides)
    return ResearchSourceAuthorityClaimConflictMemoryConfig(**values)


def item(
    index: int,
    *,
    candidate_ref: str = "candidate-private-alpha",
    market_ref: str = "market-private-alpha",
    claim_text: str = "Private claim text that must not leave the report builder",
    source_reference: str | None = None,
    source_excerpt: str = "Raw source text that must stay private",
    source_family: str = "official",
    claim_side: str = "support",
    authority_score: Decimal = d("0.900000"),
    observed_at: datetime | None = None,
    conflict_memory_count: Decimal = ZERO,
) -> ResearchSourceAuthorityClaimConflictMemoryInput:
    return ResearchSourceAuthorityClaimConflictMemoryInput(
        candidate_ref=candidate_ref,
        market_ref=market_ref,
        claim_text=claim_text,
        source_reference=(
            source_reference
            if source_reference is not None
            else f"https://private.example/source/{index}?token=secret-token"
        ),
        source_excerpt=source_excerpt,
        source_family=source_family,
        claim_side=claim_side,
        authority_score=authority_score,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(hours=2)
        ),
        conflict_memory_count=conflict_memory_count,
    )


def report(
    rows: tuple[object, ...],
    *,
    config: ResearchSourceAuthorityClaimConflictMemoryConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSourceAuthorityClaimConflictMemoryReport:
    return build_research_source_authority_claim_conflict_memory_report(
        rows,
        config=config or cfg(),
        generated_at=generated_at,
    )


def test_empty_input_returns_deterministic_report_only_pass_report() -> None:
    built = report(())
    payload = research_source_authority_claim_conflict_memory_report_payload(built)

    assert type(built) is ResearchSourceAuthorityClaimConflictMemoryReport
    assert built.generated_at == GENERATED_AT
    assert built.config_version == "research-source-authority-claim-conflict-memory-report-v0"
    assert built.claim_count == ZERO
    assert built.pass_count == ZERO
    assert built.watch_count == ZERO
    assert built.block_count == ZERO
    assert built.status == "pass"
    assert built.reason_codes == ("claim_conflict_memory_empty",)
    assert built.reason_code_counts == (
        ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount(
            reason_code="claim_conflict_memory_empty",
            count=ONE,
        ),
    )
    assert built.rows == ()
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True
    assert payload["derived_validation_digest"] == canonical_digest(payload)


def test_conflict_memory_rollup_uses_only_pass_watch_block_statuses() -> None:
    built = report(
        (
            item(
                4,
                candidate_ref="candidate-private-block",
                market_ref="market-private-block",
                claim_text="Block claim raw text",
                source_family="challenger",
                claim_side="challenge",
                authority_score=d("0.890000"),
                conflict_memory_count=d("2"),
            ),
            item(
                3,
                candidate_ref="candidate-private-block",
                market_ref="market-private-block",
                claim_text="Block claim raw text",
                source_family="official",
                claim_side="support",
                authority_score=d("0.900000"),
                conflict_memory_count=d("2"),
            ),
            item(
                2,
                candidate_ref="candidate-private-watch",
                market_ref="market-private-watch",
                claim_text="Watch claim raw text",
                source_family="official",
                claim_side="support",
                authority_score=d("0.710000"),
                conflict_memory_count=d("1"),
            ),
            item(
                1,
                candidate_ref="candidate-private-pass",
                market_ref="market-private-pass",
                claim_text="Pass claim raw text",
                source_family="filing",
                claim_side="support",
                authority_score=d("0.960000"),
            ),
            item(
                5,
                candidate_ref="candidate-private-pass",
                market_ref="market-private-pass",
                claim_text="Pass claim raw text",
                source_family="official",
                claim_side="support",
                authority_score=d("0.950000"),
            ),
        ),
    )

    assert built.status == "block"
    assert built.claim_count == d("3")
    assert built.pass_count == ONE
    assert built.watch_count == ONE
    assert built.block_count == ONE
    assert set(row.status for row in built.rows) == {"pass", "watch", "block"}
    assert tuple(row.status for row in built.rows) == ("block", "pass", "watch")
    assert built.rows[0].reason_codes == (
        "authority_conflict_memory_block",
        "material_authority_conflict",
        "remembered_conflict_block",
    )
    assert built.rows[1].reason_codes == (
        "authority_clear_pass",
        "distinct_source_families_met",
        "fresh_authority_claim",
    )
    assert built.rows[2].reason_codes == (
        "remembered_conflict_watch",
        "single_source_family_watch",
    )
    assert built.reason_codes == (
        "authority_conflict_memory_block",
        "material_authority_conflict",
        "remembered_conflict_block",
    )


def test_public_payload_is_deterministic_decimal_string_only_and_redacted() -> None:
    first = report(
        (
            item(
                1,
                candidate_ref="raw-candidate-secret",
                market_ref="raw-market-secret",
                claim_text="raw claim sentence that must not be public",
                source_reference="postgres://user:pass@host:5432/private_table",
                source_excerpt="token=top-secret-table-name raw source text",
                source_family="official",
                claim_side="support",
                authority_score=d("0.940000"),
            ),
            item(
                2,
                candidate_ref="raw-candidate-secret",
                market_ref="raw-market-secret",
                claim_text="raw claim sentence that must not be public",
                source_reference="https://example.invalid/private?token=hidden",
                source_excerpt="second raw source text",
                source_family="filing",
                claim_side="support",
                authority_score=d("0.910000"),
            ),
        ),
    )
    second = report(tuple(reversed(first_inputs_for_redaction())))

    first_payload = research_source_authority_claim_conflict_memory_report_payload(first)
    second_payload = research_source_authority_claim_conflict_memory_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True, separators=(",", ":"))

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert research_source_authority_claim_conflict_memory_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["rows"][0]["authority_support_score"] == "0.940000"
    assert first_payload["rows"][0]["source_count"] == "2"
    assert not any(isinstance(value, float) for value in walk_payload_values(first_payload))
    assert not any(type(value) is int for value in walk_payload_values(first_payload))
    for raw_value in (
        "raw-candidate-secret",
        "raw-market-secret",
        "raw claim sentence",
        "postgres://",
        "private_table",
        "token=top-secret",
        "https://example.invalid",
        "second raw source text",
    ):
        assert raw_value not in encoded
    for unsafe_key_fragment in (
        "candidate_ref",
        "market_ref",
        "source_reference",
        "source_excerpt",
        "claim_text",
        "dsn",
        "table",
        "token",
        "url",
    ):
        assert unsafe_key_fragment not in encoded


def test_payload_validation_rejects_tampering_unsafe_public_values_and_bad_digest() -> None:
    built = report((item(1), item(2, source_family="filing")))
    payload = research_source_authority_claim_conflict_memory_report_payload(built)

    assert validate_research_source_authority_claim_conflict_memory_report_payload(payload) == payload

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_source_authority_claim_conflict_memory_report_payload(tampered)

    missing = dict(payload)
    missing.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_source_authority_claim_conflict_memory_report_payload(missing)

    unsafe = dict(payload)
    unsafe["raw_candidate"] = "raw-candidate-secret"
    unsafe["derived_validation_digest"] = canonical_digest(unsafe)
    with pytest.raises(ValueError, match="unsafe public payload"):
        validate_research_source_authority_claim_conflict_memory_report_payload(unsafe)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)


def test_payload_validation_rejects_recomputed_numeric_and_private_surface_payloads() -> None:
    built = report((item(1), item(2, source_family="filing")))
    payload = research_source_authority_claim_conflict_memory_report_payload(built)

    integer_payload = dict(payload)
    integer_payload["claim_count"] = 1
    integer_payload["derived_validation_digest"] = canonical_digest(integer_payload)
    with pytest.raises(ValueError, match="Decimal-derived string"):
        validate_research_source_authority_claim_conflict_memory_report_payload(integer_payload)

    float_payload = dict(payload)
    float_rows = [dict(row) for row in payload["rows"]]
    float_rows[0]["latest_age_seconds"] = 7200.0
    float_payload["rows"] = float_rows
    float_payload["derived_validation_digest"] = canonical_digest(float_payload)
    with pytest.raises(ValueError, match="Decimal-derived string"):
        validate_research_source_authority_claim_conflict_memory_report_payload(float_payload)

    for unsafe_key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_text",
        "wallet_address",
        "order_id",
        "trade_id",
        "execution_id",
    ):
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "private-surface"
        unsafe_payload["derived_validation_digest"] = canonical_digest(unsafe_payload)
        with pytest.raises(ValueError, match="unsafe public payload"):
            validate_research_source_authority_claim_conflict_memory_report_payload(
                unsafe_payload,
            )


def test_public_dataclasses_are_frozen_decimal_only_and_validate_flags() -> None:
    built = report((item(1), item(2, source_family="filing")))

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].source_count = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="claim_key"):
        replace(built.rows[0], claim_key="market-private-alpha")
    with pytest.raises(ValueError, match="reason_code"):
        ResearchSourceAuthorityClaimConflictMemoryReasonCodeCount(
            reason_code="source_text",
            count=ONE,
        )
    with pytest.raises(ValueError, match="authority_score"):
        item(1, authority_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="authority_score"):
        item(1, authority_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((item(1),), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((item(1),), generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        replace(item(1), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(built.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)

    for public_value in (
        cfg(),
        item(1),
        *built.rows,
        *built.reason_code_counts,
        built,
    ):
        assert public_value.paper_only is True
        assert public_value.report_only is True
        assert public_value.readonly is True
        assert is_dataclass(public_value)
        for field in fields(public_value):
            value = getattr(public_value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert not isinstance(value, float)
            assert not (type(value) is int)


def test_manual_report_consistency_rejects_mismatched_counts_and_source_shapes() -> None:
    built = report((item(1), item(2, source_family="filing")))

    with pytest.raises(ValueError, match="claim_count"):
        replace(built, claim_count=d("2"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(built, reason_code_counts=())
    with pytest.raises(ValueError, match="source_count"):
        replace(built.rows[0], source_count=d("3"))
    with pytest.raises(ValueError, match="authority_gap_abs"):
        replace(built.rows[0], authority_gap_abs=d("0.010000"))


def test_module_scope_is_report_only_without_external_or_execution_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_source_authority_claim_conflict_memory_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "wallet",
        "live trading",
        "sizing",
        "recommendation",
    )

    assert all(term not in source for term in forbidden_terms)
    assert re.search(r"\bdb\b", source) is None
    assert re.search(r"\bauth\b", source) is None
    assert re.search(r"\border\b", source) is None


def first_inputs_for_redaction() -> tuple[ResearchSourceAuthorityClaimConflictMemoryInput, ...]:
    return (
        item(
            1,
            candidate_ref="raw-candidate-secret",
            market_ref="raw-market-secret",
            claim_text="raw claim sentence that must not be public",
            source_reference="postgres://user:pass@host:5432/private_table",
            source_excerpt="token=top-secret-table-name raw source text",
            source_family="official",
            claim_side="support",
            authority_score=d("0.940000"),
        ),
        item(
            2,
            candidate_ref="raw-candidate-secret",
            market_ref="raw-market-secret",
            claim_text="raw claim sentence that must not be public",
            source_reference="https://example.invalid/private?token=hidden",
            source_excerpt="second raw source text",
            source_family="filing",
            claim_side="support",
            authority_score=d("0.910000"),
        ),
    )


def canonical_digest(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item_value in value.values():
            values.extend(walk_payload_values(item_value))
    elif isinstance(value, list):
        for item_value in value:
            values.extend(walk_payload_values(item_value))
    else:
        values.append(value)
    return tuple(values)
