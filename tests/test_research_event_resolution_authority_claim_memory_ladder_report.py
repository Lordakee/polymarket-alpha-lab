from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_event_resolution_authority_claim_memory_ladder_report as api
from polymarket_alpha_lab.research_event_resolution_authority_claim_memory_ladder_report import (
    RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_MEMORY_LADDER_STATUSES,
    ResearchEventResolutionAuthorityClaimMemoryLadderConfig,
    ResearchEventResolutionAuthorityClaimMemoryLadderInput,
    ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem,
    ResearchEventResolutionAuthorityClaimMemoryLadderReport,
    ResearchEventResolutionAuthorityClaimMemoryLadderRow,
    build_research_event_resolution_authority_claim_memory_ladder_report,
    research_event_resolution_authority_claim_memory_ladder_digest,
    research_event_resolution_authority_claim_memory_ladder_public_payload,
    validate_research_event_resolution_authority_claim_memory_ladder_digest,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(minutes=5)
RAW_CANDIDATE_MARKET_SOURCE_TEXT = (
    "candidate-market-source-url-text-dsn-table-token"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def ladder_input(
    seed: str = "pass",
    *,
    observed_at: datetime = OBSERVED_AT,
    claim_age_hours: Decimal = d("2.000000"),
    authority_count: Decimal = d("3.000000"),
    evidence_family_count: Decimal = d("3.000000"),
    memory_match_count: Decimal = d("4.000000"),
    memory_conflict_count: Decimal = d("0.000000"),
    memory_recall_score: Decimal = d("0.950000"),
    ladder_depth_count: Decimal = d("3.000000"),
    contradiction_pressure: Decimal = d("0.050000"),
    resolution_rule_clarity_score: Decimal = d("0.900000"),
    claim_specificity_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventResolutionAuthorityClaimMemoryLadderInput:
    return ResearchEventResolutionAuthorityClaimMemoryLadderInput(
        event_digest=digest(f"{seed}-event"),
        authority_digest=digest(f"{seed}-authority"),
        claim_digest=digest(f"{seed}-claim"),
        observed_at=observed_at,
        claim_age_hours=claim_age_hours,
        authority_count=authority_count,
        evidence_family_count=evidence_family_count,
        memory_match_count=memory_match_count,
        memory_conflict_count=memory_conflict_count,
        memory_recall_score=memory_recall_score,
        ladder_depth_count=ladder_depth_count,
        contradiction_pressure=contradiction_pressure,
        resolution_rule_clarity_score=resolution_rule_clarity_score,
        claim_specificity_score=claim_specificity_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(
    *inputs: ResearchEventResolutionAuthorityClaimMemoryLadderInput,
    config: ResearchEventResolutionAuthorityClaimMemoryLadderConfig | None = None,
    public_payload: tuple[
        ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem,
        ...,
    ] = (),
) -> ResearchEventResolutionAuthorityClaimMemoryLadderReport:
    return build_research_event_resolution_authority_claim_memory_ladder_report(
        inputs,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
        config=config,
        public_payload=public_payload,
    )


def test_empty_input_returns_report_only_pass_digest() -> None:
    report = build_report()

    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research_event_resolution_authority_claim_memory_ladder_v1"
    )
    assert report.status == "pass"
    assert report.row_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_ladder_score == d("0.000000")
    assert report.weakest_ladder_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("authority_claim_memory_ladder_empty",)
    assert report.reason_code_counts == (
        ("authority_claim_memory_ladder_empty", d("1.000000")),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_MEMORY_LADDER_STATUSES == (
        "pass",
        "watch",
        "block",
    )

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]


def test_claim_memory_ladder_classifies_pass_watch_and_block_rows() -> None:
    report = build_report(
        ladder_input("pass"),
        ladder_input(
            "watch",
            claim_age_hours=d("30.000000"),
            authority_count=d("2.000000"),
            evidence_family_count=d("2.000000"),
            memory_match_count=d("2.000000"),
            memory_conflict_count=d("1.000000"),
            memory_recall_score=d("0.650000"),
            ladder_depth_count=d("2.000000"),
            contradiction_pressure=d("0.350000"),
            resolution_rule_clarity_score=d("0.650000"),
            claim_specificity_score=d("0.700000"),
        ),
        ladder_input(
            "block",
            claim_age_hours=d("96.000000"),
            authority_count=d("0.000000"),
            evidence_family_count=d("1.000000"),
            memory_match_count=d("1.000000"),
            memory_conflict_count=d("3.000000"),
            memory_recall_score=d("0.200000"),
            ladder_depth_count=d("0.000000"),
            contradiction_pressure=d("0.800000"),
            resolution_rule_clarity_score=d("0.250000"),
            claim_specificity_score=d("0.300000"),
        ),
    )

    rows = {row.claim_digest: row for row in report.rows}
    passed = rows[digest("pass-claim")]
    watched = rows[digest("watch-claim")]
    blocked = rows[digest("block-claim")]

    assert report.status == "block"
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert passed.status == "pass"
    assert passed.ladder_score == d("0.974722")
    assert passed.reason_codes == ("authority_claim_memory_ladder_pass", "pass")
    assert watched.status == "watch"
    assert watched.memory_conflict_pressure == d("0.333333")
    assert watched.ladder_score == d("0.655000")
    assert "authority_claim_quorum_gap" in watched.reason_codes
    assert "memory_conflict_pressure" in watched.reason_codes
    assert "watch" in watched.reason_codes
    assert blocked.status == "block"
    assert blocked.claim_freshness_score == d("0.000000")
    assert blocked.ladder_score == d("0.165000")
    assert blocked.reason_codes == (
        "authority_claim_ladder_score_block",
        "authority_claim_quorum_gap",
        "block",
        "claim_age_stale",
        "claim_specificity_gap",
        "contradiction_pressure",
        "evidence_family_gap",
        "memory_conflict_pressure",
        "memory_ladder_depth_gap",
        "memory_recall_gap",
        "resolution_rule_clarity_gap",
    )


def test_public_payload_is_deterministic_decimal_only_sanitized_and_validated() -> None:
    payload_item = ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem(
        key="safe_context",
        value="sanitized_digests_only",
    )
    inputs = (
        ladder_input("zeta"),
        ladder_input("alpha", contradiction_pressure=d("0.350000")),
    )
    first = build_report(*inputs, public_payload=(payload_item,))
    second = build_report(*reversed(inputs), public_payload=(payload_item,))

    first_payload = research_event_resolution_authority_claim_memory_ladder_public_payload(
        first,
    )
    second_payload = second.payload
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert research_event_resolution_authority_claim_memory_ladder_digest(first) == (
        first.derived_validation_digest
    )
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["public_payload"] == [
        {"key": "safe_context", "value": "sanitized_digests_only", "paper_only": True, "report_only": True, "readonly": True},
    ]
    assert [row["claim_digest"] for row in first_payload["rows"]] == sorted(
        row["claim_digest"] for row in first_payload["rows"]
    )
    assert not any(isinstance(value, Decimal) for value in walk_values(first_payload))
    assert not any(isinstance(value, float) for value in walk_values(first_payload))
    assert not any(type(value) is int for value in walk_values(first_payload))
    assert RAW_CANDIDATE_MARKET_SOURCE_TEXT not in encoded
    for leaked in ("candidate", "market", "source_url", "source_text", "dsn", "table", "token"):
        assert leaked not in encoded.lower()
    validate_research_event_resolution_authority_claim_memory_ladder_digest(first)

    tampered_payload = dict(first_payload)
    tampered_payload["row_count"] = "3.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_resolution_authority_claim_memory_ladder_public_payload(
            tampered_payload,
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_public_payload_rejects_nested_hard_flag_tampering() -> None:
    report = build_report(
        ladder_input("row-flags"),
        public_payload=(
            ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem(
                key="safe_context",
                value="sanitized_digests_only",
            ),
        ),
    )
    payload = research_event_resolution_authority_claim_memory_ladder_public_payload(
        report,
    )

    row_flag_payload = json.loads(json.dumps(payload, sort_keys=True))
    row_flag_payload["rows"][0]["readonly"] = False
    row_flag_payload["derived_validation_digest"] = payload_digest(row_flag_payload)
    with pytest.raises(ValueError, match="readonly"):
        research_event_resolution_authority_claim_memory_ladder_public_payload(
            row_flag_payload,
        )

    public_item_flag_payload = json.loads(json.dumps(payload, sort_keys=True))
    public_item_flag_payload["public_payload"][0]["report_only"] = False
    public_item_flag_payload["derived_validation_digest"] = payload_digest(
        public_item_flag_payload,
    )
    with pytest.raises(ValueError, match="report_only"):
        research_event_resolution_authority_claim_memory_ladder_public_payload(
            public_item_flag_payload,
        )


def test_report_rejects_mismatched_derived_summary_counts() -> None:
    report = build_report(
        ladder_input(
            "derived-counts",
            authority_count=d("1.000000"),
            claim_age_hours=d("96.000000"),
            evidence_family_count=d("1.000000"),
            memory_match_count=d("1.000000"),
            memory_conflict_count=d("3.000000"),
            contradiction_pressure=d("0.800000"),
        ),
    )

    for field_name in (
        "authority_gap_count",
        "stale_claim_count",
        "evidence_gap_count",
        "memory_conflict_count",
        "contradiction_count",
    ):
        values = {field.name: getattr(report, field.name) for field in fields(report)}
        values[field_name] = values[field_name] + d("1.000000")
        unsigned_values = dict(values)
        unsigned_values.pop("derived_validation_digest")
        values["derived_validation_digest"] = (
            api._report_digest_from_values(unsigned_values)
        )

        with pytest.raises(ValueError, match=field_name):
            ResearchEventResolutionAuthorityClaimMemoryLadderReport(**values)


def test_leak_prevention_rejects_raw_identifiers_and_unsafe_public_payloads() -> None:
    with pytest.raises(ValueError, match="sha256"):
        ResearchEventResolutionAuthorityClaimMemoryLadderInput(
            event_digest=RAW_CANDIDATE_MARKET_SOURCE_TEXT,
            authority_digest=digest("authority"),
            claim_digest=digest("claim"),
            observed_at=OBSERVED_AT,
            claim_age_hours=d("2.000000"),
            authority_count=d("3.000000"),
            evidence_family_count=d("3.000000"),
            memory_match_count=d("4.000000"),
            memory_conflict_count=d("0.000000"),
            memory_recall_score=d("0.950000"),
            ladder_depth_count=d("3.000000"),
            contradiction_pressure=d("0.050000"),
            resolution_rule_clarity_score=d("0.900000"),
            claim_specificity_score=d("0.900000"),
        )

    for key in (
        "candidate_id",
        "market_slug",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "live_trading",
        "position_sizing",
        "recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem(
                key=key,
                value="safe_value",
            )

    for value in (
        "https://example.test/source",
        "postgres://user:pass@example.test/db",
        "raw source text",
        "wallet surface",
        "place order",
        "live trading flow",
        "position sizing hint",
        "recommendation hint",
    ):
        with pytest.raises(ValueError, match="unsafe public"):
            ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem(
                key="safe_key",
                value=value,
            )


def test_validation_rejects_non_decimal_values_bad_statuses_flags_and_datetimes() -> None:
    class NoneOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> None:
            return None

        def dst(self, value: datetime | None) -> None:
            return None

    class DecimalSubclass(Decimal):
        pass

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_event_resolution_authority_claim_memory_ladder_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_research_event_resolution_authority_claim_memory_ladder_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="paper_only"):
        ladder_input(paper_only=False)
    with pytest.raises(ValueError, match="claim_age_hours must be a Decimal"):
        ladder_input(claim_age_hours=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_recall_score must be exactly Decimal"):
        ladder_input(memory_recall_score=DecimalSubclass("0.5"))
    with pytest.raises(ValueError, match="authority_count must be nonnegative"):
        ladder_input(authority_count=d("-1.000000"))
    with pytest.raises(ValueError, match="claim_age_hours must be finite"):
        ladder_input(claim_age_hours=Decimal("NaN"))
    with pytest.raises(ValueError, match="memory_recall_score must be between"):
        ladder_input(memory_recall_score=d("1.100000"))
    with pytest.raises(ValueError, match="weights must sum"):
        ResearchEventResolutionAuthorityClaimMemoryLadderConfig(
            authority_quorum_weight=d("0.160000"),
        )
    with pytest.raises(ValueError, match="block_ladder_threshold must be below"):
        ResearchEventResolutionAuthorityClaimMemoryLadderConfig(
            watch_ladder_threshold=d("0.400000"),
            block_ladder_threshold=d("0.400000"),
        )
    with pytest.raises(ValueError, match="status"):
        ResearchEventResolutionAuthorityClaimMemoryLadderRow(
            event_digest=digest("event"),
            authority_digest=digest("authority"),
            claim_digest=digest("claim"),
            observed_at=OBSERVED_AT,
            claim_age_hours=d("2.000000"),
            authority_count=d("3.000000"),
            evidence_family_count=d("3.000000"),
            memory_match_count=d("4.000000"),
            memory_conflict_count=d("0.000000"),
            memory_conflict_pressure=d("0.000000"),
            memory_recall_score=d("0.950000"),
            ladder_depth_count=d("3.000000"),
            contradiction_pressure=d("0.050000"),
            resolution_rule_clarity_score=d("0.900000"),
            claim_specificity_score=d("0.900000"),
            authority_quorum_score=d("1.000000"),
            claim_freshness_score=d("0.972222"),
            evidence_family_score=d("1.000000"),
            ladder_depth_score=d("1.000000"),
            ladder_score=d("0.974722"),
            status="ready",
            reason_codes=("ready",),
        )


def test_module_surface_has_no_execution_or_storage_dependencies() -> None:
    source = Path(api.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )

    assert imports <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "re",
        "typing",
        "polymarket_alpha_lab",
    }
    lower_source = source.lower()
    for banned in (
        "requests",
        "httpx",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "web3",
        "ccxt",
        "place_order",
        "trade_size",
    ):
        assert banned not in lower_source


def test_public_api_is_exactly_the_report_only_surface() -> None:
    assert api.__all__ == (
        "CONFIG_VERSION",
        "RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_MEMORY_LADDER_STATUSES",
        "ResearchEventResolutionAuthorityClaimMemoryLadderConfig",
        "ResearchEventResolutionAuthorityClaimMemoryLadderInput",
        "ResearchEventResolutionAuthorityClaimMemoryLadderPublicPayloadItem",
        "ResearchEventResolutionAuthorityClaimMemoryLadderReport",
        "ResearchEventResolutionAuthorityClaimMemoryLadderRow",
        "build_research_event_resolution_authority_claim_memory_ladder_report",
        "research_event_resolution_authority_claim_memory_ladder_digest",
        "research_event_resolution_authority_claim_memory_ladder_public_payload",
        "validate_research_event_resolution_authority_claim_memory_ladder_digest",
    )


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for key, item in value.items():
            values.extend(walk_values(key))
            values.extend(walk_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(walk_values(item))
    return tuple(values)


def payload_digest(payload: dict[str, object]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
