from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.research_event_claim_authority_memory_conflict_report import (
    DEFAULT_RESEARCH_EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_CONFIG_VERSION,
    EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_STATUSES,
    ResearchEventClaimAuthorityMemoryConflictConfig,
    ResearchEventClaimAuthorityMemoryConflictObservation,
    ResearchEventClaimAuthorityMemoryConflictReasonCodeCount,
    ResearchEventClaimAuthorityMemoryConflictReport,
    ResearchEventClaimAuthorityMemoryConflictRow,
    build_research_event_claim_authority_memory_conflict_report,
    research_event_claim_authority_memory_conflict_report_digest,
    research_event_claim_authority_memory_conflict_report_payload,
    validate_research_event_claim_authority_memory_conflict_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_claim_authority_memory_conflict_report.py"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedObservationShape:
    event_ref: str
    candidate_ref: str
    market_ref: str
    claim_text: str
    source_ref: str
    source_detail: str
    source_family: str
    claim_side: str
    authority_score: Decimal
    observed_at: datetime
    memory_conflict_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchEventClaimAuthorityMemoryConflictConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_CONFIG_VERSION
        ),
        "fresh_claim_age_seconds": d("86400.000000"),
        "stale_claim_age_seconds": d("604800.000000"),
        "min_family_quorum_count": d("2.000000"),
        "material_authority_score": d("0.650000"),
        "pass_authority_margin": d("0.250000"),
        "watch_memory_conflict_count": d("1.000000"),
        "block_memory_conflict_count": d("2.000000"),
    }
    values.update(overrides)
    return ResearchEventClaimAuthorityMemoryConflictConfig(**values)


def observation(
    index: int,
    *,
    event_ref: str = "event-private-alpha",
    candidate_ref: str = "candidate-private-alpha",
    market_ref: str = "market-private-alpha",
    claim_text: str = "Private claim text that must not leave the builder",
    source_ref: str | None = None,
    source_detail: str = "Raw evidence text that must stay private",
    source_family: str = "official",
    claim_side: str = "support",
    authority_score: Decimal = d("0.900000"),
    observed_at: datetime | None = None,
    memory_conflict_count: Decimal = ZERO,
) -> ResearchEventClaimAuthorityMemoryConflictObservation:
    return ResearchEventClaimAuthorityMemoryConflictObservation(
        event_ref=event_ref,
        candidate_ref=candidate_ref,
        market_ref=market_ref,
        claim_text=claim_text,
        source_ref=(
            source_ref
            if source_ref is not None
            else f"https://private.example/evidence/{index}?token=secret-token"
        ),
        source_detail=source_detail,
        source_family=source_family,
        claim_side=claim_side,
        authority_score=authority_score,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(hours=2)
        ),
        memory_conflict_count=memory_conflict_count,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchEventClaimAuthorityMemoryConflictConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventClaimAuthorityMemoryConflictReport:
    return build_research_event_claim_authority_memory_conflict_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_deterministic_readonly_report_only_pass_report() -> None:
    built = report(())
    payload = research_event_claim_authority_memory_conflict_report_payload(built)

    assert type(built) is ResearchEventClaimAuthorityMemoryConflictReport
    assert EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_STATUSES == ("pass", "watch", "block")
    assert built.generated_at == GENERATED_AT
    assert built.config_version == (
        DEFAULT_RESEARCH_EVENT_CLAIM_AUTHORITY_MEMORY_CONFLICT_CONFIG_VERSION
    )
    assert built.claim_count == ZERO
    assert built.pass_count == ZERO
    assert built.watch_count == ZERO
    assert built.block_count == ZERO
    assert built.status == "pass"
    assert built.rows == ()
    assert built.reason_codes == ("authority_memory_conflict_empty",)
    assert built.reason_code_counts == (
        ResearchEventClaimAuthorityMemoryConflictReasonCodeCount(
            reason_code="authority_memory_conflict_empty",
            count=ONE,
        ),
    )
    assert built.paper_only is True
    assert built.report_only is True
    assert built.readonly is True
    assert payload["derived_validation_digest"] == canonical_digest(payload)


def test_claim_authority_memory_conflicts_roll_up_pass_watch_block_only() -> None:
    built = report(
        (
            observation(
                5,
                event_ref="event-private-pass",
                candidate_ref="candidate-private-pass",
                market_ref="market-private-pass",
                claim_text="Pass claim private text",
                source_family="official",
                claim_side="support",
                authority_score=d("0.950000"),
            ),
            observation(
                4,
                event_ref="event-private-pass",
                candidate_ref="candidate-private-pass",
                market_ref="market-private-pass",
                claim_text="Pass claim private text",
                source_family="filing",
                claim_side="support",
                authority_score=d("0.940000"),
            ),
            observation(
                3,
                event_ref="event-private-watch",
                candidate_ref="candidate-private-watch",
                market_ref="market-private-watch",
                claim_text="Watch claim private text",
                source_family="official",
                claim_side="support",
                authority_score=d("0.710000"),
                memory_conflict_count=d("1.000000"),
            ),
            observation(
                2,
                event_ref="event-private-block",
                candidate_ref="candidate-private-block",
                market_ref="market-private-block",
                claim_text="Block claim private text",
                source_family="official",
                claim_side="support",
                authority_score=d("0.900000"),
                memory_conflict_count=d("2.000000"),
            ),
            observation(
                1,
                event_ref="event-private-block",
                candidate_ref="candidate-private-block",
                market_ref="market-private-block",
                claim_text="Block claim private text",
                source_family="challenger",
                claim_side="challenge",
                authority_score=d("0.890000"),
                memory_conflict_count=d("2.000000"),
            ),
        ),
    )

    assert built.status == "block"
    assert built.claim_count == d("3.000000")
    assert built.pass_count == ONE
    assert built.watch_count == ONE
    assert built.block_count == ONE
    assert set(row.status for row in built.rows) == {"pass", "watch", "block"}
    assert tuple(row.status for row in built.rows) == ("block", "watch", "pass")
    blocked, watched, passed = built.rows
    assert blocked.reason_codes == (
        "authority_memory_conflict_block",
        "material_authority_conflict",
        "memory_conflict_block",
    )
    assert watched.reason_codes == (
        "authority_memory_conflict_watch",
        "memory_conflict_watch",
        "single_family_watch",
    )
    assert passed.reason_codes == (
        "authority_clear_pass",
        "family_quorum_met",
        "fresh_claim_pass",
    )
    assert built.reason_codes == (
        "authority_memory_conflict_block",
        "material_authority_conflict",
        "memory_conflict_block",
    )


def test_public_payload_is_deterministic_digest_bound_decimal_string_only_and_redacted() -> None:
    left = first_inputs_for_redaction()
    first = report(left)
    second = report(tuple(reversed(left)))

    first_payload = research_event_claim_authority_memory_conflict_report_payload(first)
    second_payload = research_event_claim_authority_memory_conflict_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True, separators=(",", ":"))

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert research_event_claim_authority_memory_conflict_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["rows"][0]["support_authority_score"] == "0.940000"
    assert first_payload["rows"][0]["evidence_count"] == "2.000000"
    assert_no_raw_numeric_payload_values(first_payload)
    for raw_value in (
        "raw-candidate-secret",
        "raw-market-secret",
        "raw claim sentence",
        "postgres://",
        "private_table",
        "token=top-secret",
        "https://example.invalid",
        "second raw evidence text",
    ):
        assert raw_value not in encoded
    for unsafe_key_fragment in (
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "raw",
    ):
        assert unsafe_key_fragment not in encoded.lower()


def test_payload_validation_rejects_tampering_unsafe_public_values_and_bad_digest() -> None:
    built = report((observation(1), observation(2, source_family="filing")))
    payload = research_event_claim_authority_memory_conflict_report_payload(built)

    assert validate_research_event_claim_authority_memory_conflict_report_payload(payload) == payload

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_event_claim_authority_memory_conflict_report_payload(tampered)

    missing = dict(payload)
    missing.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_event_claim_authority_memory_conflict_report_payload(missing)

    unsafe = dict(payload)
    unsafe["raw_candidate"] = "raw-candidate-secret"
    unsafe["derived_validation_digest"] = canonical_digest(unsafe)
    with pytest.raises(ValueError, match="unsafe public payload"):
        validate_research_event_claim_authority_memory_conflict_report_payload(unsafe)

    unexpected = dict(payload)
    unexpected["safe_note"] = "innocuous extra public field"
    unexpected["derived_validation_digest"] = canonical_digest(unexpected)
    with pytest.raises(ValueError, match="unexpected public payload key"):
        validate_research_event_claim_authority_memory_conflict_report_payload(
            unexpected,
        )

    action_surface = dict(payload)
    action_surface["reason_codes"] = ["authority_clear_pass", "order_router_surface"]
    action_surface["derived_validation_digest"] = canonical_digest(action_surface)
    with pytest.raises(ValueError, match="unsafe public payload"):
        validate_research_event_claim_authority_memory_conflict_report_payload(
            action_surface,
        )

    numeric_payload = dict(payload)
    numeric_payload["claim_count"] = d("1.000000")
    numeric_payload["derived_validation_digest"] = payload["derived_validation_digest"]
    with pytest.raises(ValueError, match="numerics must be serialized strings"):
        validate_research_event_claim_authority_memory_conflict_report_payload(
            numeric_payload,
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)


def test_public_dataclasses_are_frozen_decimal_only_and_validate_flags() -> None:
    built = report((observation(1), observation(2, source_family="filing")))

    for public_type in (
        ResearchEventClaimAuthorityMemoryConflictConfig,
        ResearchEventClaimAuthorityMemoryConflictObservation,
        ResearchEventClaimAuthorityMemoryConflictRow,
        ResearchEventClaimAuthorityMemoryConflictReasonCodeCount,
        ResearchEventClaimAuthorityMemoryConflictReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        hints = get_type_hints(public_type)
        for field in fields(public_type):
            if is_numeric_public_field(field.name):
                assert hints[field.name] is Decimal

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        built.rows[0].evidence_count = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(built.rows[0], status="blocked")
    with pytest.raises(ValueError, match="authority_score"):
        observation(1, authority_score=Decimal("1.100000"))
    with pytest.raises(ValueError, match="authority_score"):
        observation(1, authority_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(built.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)

    for public_value in (
        config(),
        observation(1),
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


def test_manual_report_consistency_rejects_mismatched_counts_and_shapes() -> None:
    built = report((observation(1), observation(2, source_family="filing")))

    with pytest.raises(ValueError, match="claim_count"):
        replace(built, claim_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(built, reason_code_counts=())
    with pytest.raises(ValueError, match="evidence_count"):
        replace(built.rows[0], evidence_count=d("3.000000"))
    with pytest.raises(ValueError, match="authority_margin_abs"):
        replace(built.rows[0], authority_margin_abs=d("0.010000"))

    supplied = SuppliedObservationShape(
        event_ref="event-private-supplied",
        candidate_ref="candidate-private-supplied",
        market_ref="market-private-supplied",
        claim_text="Supplied private claim",
        source_ref="private-ref",
        source_detail="private detail",
        source_family="official",
        claim_side="support",
        authority_score=d("0.900000"),
        observed_at=GENERATED_AT,
    )
    assert report((supplied,)).claim_count == ONE


def test_module_scope_is_report_only_without_external_action_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "database",
        "network",
        "wallet",
        "live trading",
        "sizing",
        "recommendation",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute(",
        "open(",
    ):
        assert forbidden not in lowered
    for exact_forbidden in ("db", "auth", "order"):
        assert re.search(rf"\b{exact_forbidden}\b", lowered) is None

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
    forbidden_calls = {"connect", "execute", "open", "request", "write_bytes", "write_text"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports


def first_inputs_for_redaction() -> tuple[ResearchEventClaimAuthorityMemoryConflictObservation, ...]:
    return (
        observation(
            1,
            event_ref="event-private-redaction",
            candidate_ref="raw-candidate-secret",
            market_ref="raw-market-secret",
            claim_text="raw claim sentence that must not be public",
            source_ref="postgres://user:pass@host:5432/private_table",
            source_detail="token=top-secret-table-name raw evidence text",
            source_family="official",
            claim_side="support",
            authority_score=d("0.940000"),
        ),
        observation(
            2,
            event_ref="event-private-redaction",
            candidate_ref="raw-candidate-secret",
            market_ref="raw-market-secret",
            claim_text="raw claim sentence that must not be public",
            source_ref="https://example.invalid/private?token=hidden",
            source_detail="second raw evidence text",
            source_family="filing",
            claim_side="support",
            authority_score=d("0.910000"),
        ),
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def assert_no_raw_numeric_payload_values(value: object) -> None:
    if type(value) in (Decimal, float, int):
        pytest.fail(f"payload contains raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_raw_numeric_payload_values(item)
    elif type(value) is list:
        for item in value:
            assert_no_raw_numeric_payload_values(item)


def is_numeric_public_field(name: str) -> bool:
    return (
        name.endswith("_count")
        or name.endswith("_score")
        or name.endswith("_seconds")
        or name in {"authority_margin_abs"}
    )
