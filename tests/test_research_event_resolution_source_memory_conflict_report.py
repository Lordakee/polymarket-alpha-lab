from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any, get_type_hints

import pytest

from polymarket_alpha_lab.research_event_resolution_source_memory_conflict_report import (
    DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_REPORT_CONFIG_VERSION,
    EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_STATUSES,
    ResearchEventResolutionSourceMemoryConflictConfig,
    ResearchEventResolutionSourceMemoryConflictObservation,
    ResearchEventResolutionSourceMemoryConflictPublicPayloadItem,
    ResearchEventResolutionSourceMemoryConflictReasonCodeCount,
    ResearchEventResolutionSourceMemoryConflictReport,
    ResearchEventResolutionSourceMemoryConflictRow,
    build_research_event_resolution_source_memory_conflict_report,
    research_event_resolution_source_memory_conflict_report_digest,
    research_event_resolution_source_memory_conflict_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_resolution_source_memory_conflict_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def observation(
    event_key: str = "event-alpha",
    family_key: str = "family-alpha",
    memory_key: str = "memory-alpha",
    *,
    source_claim_count: Decimal = d("4.000000"),
    conflicting_memory_count: Decimal = d("0.000000"),
    corroborating_memory_count: Decimal = d("4.000000"),
    newest_memory_age_seconds: Decimal = d("86400.000000"),
    current_evidence_age_seconds: Decimal = d("3600.000000"),
    signal_alignment_score: Decimal = d("0.900000"),
    memory_consistency_score: Decimal = d("0.850000"),
    resolution_rule_match_score: Decimal = d("0.900000"),
    observed_at: datetime = GENERATED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventResolutionSourceMemoryConflictObservation:
    return ResearchEventResolutionSourceMemoryConflictObservation(
        event_digest=digest(event_key),
        source_family_digest=digest(family_key),
        memory_snapshot_digest=digest(memory_key),
        observed_at=observed_at,
        source_claim_count=source_claim_count,
        conflicting_memory_count=conflicting_memory_count,
        corroborating_memory_count=corroborating_memory_count,
        newest_memory_age_seconds=newest_memory_age_seconds,
        current_evidence_age_seconds=current_evidence_age_seconds,
        signal_alignment_score=signal_alignment_score,
        memory_consistency_score=memory_consistency_score,
        resolution_rule_match_score=resolution_rule_match_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchEventResolutionSourceMemoryConflictObservation,
    config: ResearchEventResolutionSourceMemoryConflictConfig | None = None,
    public_payload: tuple[
        ResearchEventResolutionSourceMemoryConflictPublicPayloadItem,
        ...,
    ] = (),
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventResolutionSourceMemoryConflictReport:
    return build_research_event_resolution_source_memory_conflict_report(
        items,
        config=config or ResearchEventResolutionSourceMemoryConflictConfig(),
        public_payload=public_payload,
        generated_at=generated_at,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def resigned_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload["derived_validation_digest"] = canonical_digest(payload)
    return payload


def test_empty_observations_block_as_readonly_report_only_memory_gap() -> None:
    conflict = report()

    assert type(conflict) is ResearchEventResolutionSourceMemoryConflictReport
    assert EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_STATUSES == ("pass", "watch", "block")
    assert conflict.config_version == (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_MEMORY_CONFLICT_REPORT_CONFIG_VERSION
    )
    assert conflict.status == "block"
    assert conflict.observation_count == d("0.000000")
    assert conflict.pass_count == d("0.000000")
    assert conflict.watch_count == d("0.000000")
    assert conflict.block_count == d("0.000000")
    assert conflict.average_conflict_ratio == d("0.000000")
    assert conflict.average_resolution_confidence_score == d("0.000000")
    assert conflict.max_conflict_ratio == d("0.000000")
    assert conflict.rows == ()
    assert conflict.reason_codes == ("empty_source_memory_conflict_set",)
    assert conflict.reason_code_counts == (
        ResearchEventResolutionSourceMemoryConflictReasonCodeCount(
            reason_code="empty_source_memory_conflict_set",
            count=d("1.000000"),
            row_ratio=d("0.000000"),
        ),
    )
    assert conflict.paper_only is True
    assert conflict.report_only is True
    assert conflict.readonly is True
    assert len(conflict.derived_validation_digest) == 64


def test_report_scores_source_memory_conflicts_into_pass_watch_block_rows() -> None:
    conflict = report(
        observation(),
        observation(
            "event-watch",
            "family-watch",
            "memory-watch",
            conflicting_memory_count=d("1.000000"),
            corroborating_memory_count=d("3.000000"),
            signal_alignment_score=d("0.750000"),
            memory_consistency_score=d("0.700000"),
            resolution_rule_match_score=d("0.700000"),
        ),
        observation(
            "event-block",
            "family-block",
            "memory-block",
            conflicting_memory_count=d("2.000000"),
            corroborating_memory_count=d("2.000000"),
            newest_memory_age_seconds=d("700000.000000"),
            current_evidence_age_seconds=d("90000.000000"),
            signal_alignment_score=d("0.400000"),
            memory_consistency_score=d("0.500000"),
            resolution_rule_match_score=d("0.400000"),
        ),
    )

    assert conflict.status == "block"
    assert conflict.observation_count == d("3.000000")
    assert conflict.pass_count == d("1.000000")
    assert conflict.watch_count == d("1.000000")
    assert conflict.block_count == d("1.000000")
    assert conflict.average_conflict_ratio == d("0.250000")
    assert conflict.average_resolution_confidence_score == d("0.687460")
    assert conflict.max_conflict_ratio == d("0.500000")
    assert conflict.reason_codes == (
        "conflict_ratio_block",
        "conflict_ratio_watch",
        "signal_alignment_block",
        "signal_alignment_watch",
        "memory_consistency_block",
        "memory_consistency_watch",
        "rule_match_block",
        "rule_match_watch",
        "current_evidence_stale_block",
        "memory_recency_stale_watch",
        "resolution_source_memory_conflict_pass",
    )

    blocked, watched, passed = conflict.rows
    assert tuple(row.status for row in conflict.rows) == ("block", "watch", "pass")
    assert blocked.conflict_ratio == d("0.500000")
    assert blocked.resolution_confidence_score == d("0.385000")
    assert blocked.reason_codes == (
        "conflict_ratio_block",
        "signal_alignment_block",
        "memory_consistency_block",
        "rule_match_block",
        "current_evidence_stale_block",
        "memory_recency_stale_watch",
    )
    assert watched.conflict_ratio == d("0.250000")
    assert watched.resolution_confidence_score == d("0.758690")
    assert watched.reason_codes == (
        "conflict_ratio_watch",
        "signal_alignment_watch",
        "memory_consistency_watch",
        "rule_match_watch",
    )
    assert passed.conflict_ratio == d("0.000000")
    assert passed.current_freshness_score == d("0.958333")
    assert passed.memory_recency_score == d("0.857143")
    assert passed.resolution_confidence_score == d("0.918690")
    assert passed.reason_codes == ("resolution_source_memory_conflict_pass",)


def test_public_payload_is_deterministic_digest_bound_decimal_string_only_and_safe() -> None:
    first = report(
        observation("event-b", "family-b", "memory-b"),
        observation("event-a", "family-a", "memory-a"),
        public_payload=(
            ResearchEventResolutionSourceMemoryConflictPublicPayloadItem(
                "safe_context",
                "redacted digest summary only",
            ),
        ),
    )
    second = report(
        observation("event-a", "family-a", "memory-a"),
        observation("event-b", "family-b", "memory-b"),
        public_payload=(
            ResearchEventResolutionSourceMemoryConflictPublicPayloadItem(
                "safe_context",
                "redacted digest summary only",
            ),
        ),
    )

    first_payload = research_event_resolution_source_memory_conflict_report_payload(first)
    second_payload = research_event_resolution_source_memory_conflict_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["derived_validation_digest"] == canonical_digest(first_payload)
    assert research_event_resolution_source_memory_conflict_report_digest(first) == (
        first.derived_validation_digest
    )
    assert first_payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert first_payload["observation_count"] == "2.000000"
    assert first_payload["rows"][0]["resolution_confidence_score"] == "0.918690"
    assert first_payload["public_payload"] == [
        {
            "key": "safe_context",
            "value": "redacted digest summary only",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert '"0.918690"' in encoded
    assert_no_raw_numeric_payload_values(first_payload)
    assert_no_forbidden_public_payload_surface(first_payload)

    tampered = dict(first_payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_event_resolution_source_memory_conflict_report_payload(tampered)


def test_mapping_payload_revalidates_exact_public_schema_before_digest() -> None:
    payload = research_event_resolution_source_memory_conflict_report_payload(
        report(
            observation(),
            public_payload=(
                ResearchEventResolutionSourceMemoryConflictPublicPayloadItem(
                    "safe_context",
                    "redacted digest summary only",
                ),
            ),
        ),
    )

    extra_report_field = json.loads(json.dumps(payload))
    extra_report_field["safe_extension"] = "redacted summary"
    with pytest.raises(ValueError, match="report payload schema"):
        research_event_resolution_source_memory_conflict_report_payload(
            resigned_payload(extra_report_field),
        )

    missing_report_field = json.loads(json.dumps(payload))
    missing_report_field.pop("reason_codes")
    with pytest.raises(ValueError, match="report payload schema"):
        research_event_resolution_source_memory_conflict_report_payload(
            resigned_payload(missing_report_field),
        )

    extra_row_field = json.loads(json.dumps(payload))
    extra_row_field["rows"][0]["safe_extension"] = "redacted summary"
    with pytest.raises(ValueError, match="row payload schema"):
        research_event_resolution_source_memory_conflict_report_payload(
            resigned_payload(extra_row_field),
        )

    noncanonical_decimal = json.loads(json.dumps(payload))
    noncanonical_decimal["observation_count"] = "1"
    with pytest.raises(ValueError, match="observation_count"):
        research_event_resolution_source_memory_conflict_report_payload(
            resigned_payload(noncanonical_decimal),
        )

    disabled_hard_flag = json.loads(json.dumps(payload))
    disabled_hard_flag["rows"][0]["readonly"] = False
    with pytest.raises(ValueError, match="readonly must be True"):
        research_event_resolution_source_memory_conflict_report_payload(
            resigned_payload(disabled_hard_flag),
        )

    inconsistent_row = json.loads(json.dumps(payload))
    inconsistent_row["rows"][0]["conflict_ratio"] = "0.500000"
    with pytest.raises(ValueError, match="conflict_ratio must match row counts"):
        research_event_resolution_source_memory_conflict_report_payload(
            resigned_payload(inconsistent_row),
        )


def test_validation_freezing_flags_decimal_only_status_digest_and_input_safety() -> None:
    conflict = report(observation())

    for public_type in (
        ResearchEventResolutionSourceMemoryConflictConfig,
        ResearchEventResolutionSourceMemoryConflictObservation,
        ResearchEventResolutionSourceMemoryConflictPublicPayloadItem,
        ResearchEventResolutionSourceMemoryConflictRow,
        ResearchEventResolutionSourceMemoryConflictReasonCodeCount,
        ResearchEventResolutionSourceMemoryConflictReport,
    ):
        assert is_dataclass(public_type)
        assert public_type.__dataclass_params__.frozen is True
        hints = get_type_hints(public_type)
        for item in fields(public_type):
            if is_numeric_public_field(item.name):
                assert hints[item.name] is Decimal

    for instance in (
        ResearchEventResolutionSourceMemoryConflictConfig(),
        observation(),
        ResearchEventResolutionSourceMemoryConflictPublicPayloadItem(
            "safe_context",
            "redacted digest summary only",
        ),
        conflict.rows[0],
        conflict.reason_code_counts[0],
        conflict,
    ):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for item in fields(instance):
            if is_numeric_public_field(item.name):
                assert type(getattr(instance, item.name)) is Decimal

    with pytest.raises(FrozenInstanceError):
        conflict.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="event_digest"):
        observation().__class__(
            event_digest="raw-candidate-id",
            source_family_digest=digest("family"),
            memory_snapshot_digest=digest("memory"),
            observed_at=GENERATED_AT,
            source_claim_count=d("4.000000"),
            conflicting_memory_count=d("0.000000"),
            corroborating_memory_count=d("4.000000"),
            newest_memory_age_seconds=d("86400.000000"),
            current_evidence_age_seconds=d("3600.000000"),
            signal_alignment_score=d("0.900000"),
            memory_consistency_score=d("0.850000"),
            resolution_rule_match_score=d("0.900000"),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        observation(observed_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        observation(observed_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="source_claim_count must be exactly Decimal"):
        observation(source_claim_count=_DecimalSubclass("4.000000"))
    with pytest.raises(ValueError, match="source_claim_count must be positive"):
        observation(source_claim_count=d("0.000000"))
    with pytest.raises(ValueError, match="memory totals must not exceed"):
        observation(
            conflicting_memory_count=d("3.000000"),
            corroborating_memory_count=d("3.000000"),
        )
    with pytest.raises(ValueError, match="readonly must be True"):
        observation(readonly=False)
    with pytest.raises(ValueError, match="triples must be unique"):
        report(observation(), observation())
    with pytest.raises(ValueError, match="status must be one of pass, watch, block"):
        replace(conflict.rows[0], status="ready")
    with pytest.raises(ValueError, match="conflict_ratio must match row counts"):
        replace(conflict.rows[0], conflict_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(conflict, derived_validation_digest="0" * 64)


def test_public_payload_rejects_raw_surfaces_and_module_has_no_action_surfaces() -> None:
    for key in (
        "candidate_id",
        "market_slug",
        "question_text",
        "source_url",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "execution_plan",
        "source-url",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            ResearchEventResolutionSourceMemoryConflictPublicPayloadItem(key, "safe value")

    for value in (
        "https://example.com/raw-source",
        "https://example.com/resolution-evidence",
        "postgres://user:pass@example/db",
        "wallet surface",
        "place order",
        "trade execution",
        "execute action",
        "source text excerpt",
        "candidate linked note",
    ):
        with pytest.raises(ValueError, match="unsafe public payload"):
            ResearchEventResolutionSourceMemoryConflictPublicPayloadItem(
                "safe_key",
                value,
            )

    source_body = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_body.lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question_text",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "live",
        "database",
        "network",
        "requests",
        "httpx",
        "socket",
        "postgres",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "supabase",
        "execute",
        "execution",
        "execute(",
        "open(",
        "recommend",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source_body)
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


def assert_no_raw_numeric_payload_values(value: object) -> None:
    if type(value) in (Decimal, float, int):
        pytest.fail(f"payload contains raw numeric value {value!r}")
    if type(value) is dict:
        for item in value.values():
            assert_no_raw_numeric_payload_values(item)
    elif type(value) is list:
        for item in value:
            assert_no_raw_numeric_payload_values(item)


def assert_no_forbidden_public_payload_surface(payload: dict[str, Any]) -> None:
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question_text",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "live",
        "database",
        "network",
        "execute",
        "execution",
        "recommend",
        "sizing",
    ):
        assert forbidden not in encoded


def is_numeric_public_field(name: str) -> bool:
    return (
        name.endswith("_count")
        or name.endswith("_ratio")
        or name.endswith("_score")
        or name.endswith("_seconds")
    )
