from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_event_memory_authority_claim_scorecard_report import (
    DEFAULT_RESEARCH_EVENT_MEMORY_AUTHORITY_CLAIM_SCORECARD_CONFIG_VERSION,
    ResearchEventMemoryAuthorityClaimScorecardConfig,
    ResearchEventMemoryAuthorityClaimScorecardObservation,
    ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount,
    ResearchEventMemoryAuthorityClaimScorecardReport,
    ResearchEventMemoryAuthorityClaimScorecardRow,
    build_research_event_memory_authority_claim_scorecard_report,
    research_event_memory_authority_claim_scorecard_payload,
    research_event_memory_authority_claim_scorecard_sha256_digest,
    validate_research_event_memory_authority_claim_scorecard_digest,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_event_memory_authority_claim_scorecard_report.py",
)
ZERO = Decimal("0.000000")


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchEventMemoryAuthorityClaimScorecardConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_MEMORY_AUTHORITY_CLAIM_SCORECARD_CONFIG_VERSION
        ),
        "minimum_authority_score_pass": d("0.700000"),
        "minimum_authority_score_watch": d("0.500000"),
        "minimum_parser_confidence_pass": d("0.700000"),
        "minimum_parser_confidence_watch": d("0.500000"),
        "minimum_memory_match_pass": d("0.600000"),
        "minimum_source_recency_pass": d("0.500000"),
        "maximum_conflict_ratio_watch": d("0.250000"),
        "maximum_conflict_ratio_block": d("0.500000"),
    }
    values.update(overrides)
    return ResearchEventMemoryAuthorityClaimScorecardConfig(**values)


def observation(
    event_key: str = "event-alpha",
    *,
    claim_key: str = "claim-alpha",
    authority_key: str = "authority-public-alpha",
    event_family: str = "macro-policy",
    observed_at: datetime = GENERATED_AT - timedelta(hours=2),
    source_count: Decimal = d("4.000000"),
    independent_source_count: Decimal = d("3.000000"),
    authority_source_count: Decimal = d("1.000000"),
    conflicting_source_count: Decimal = d("0.000000"),
    memory_match_score: Decimal = d("0.800000"),
    authority_claim_score: Decimal = d("0.760000"),
    parser_confidence_score: Decimal = d("0.820000"),
    source_recency_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventMemoryAuthorityClaimScorecardObservation:
    return ResearchEventMemoryAuthorityClaimScorecardObservation(
        event_key=event_key,
        claim_key=claim_key,
        authority_key=authority_key,
        event_family=event_family,
        observed_at=observed_at,
        source_count=source_count,
        independent_source_count=independent_source_count,
        authority_source_count=authority_source_count,
        conflicting_source_count=conflicting_source_count,
        memory_match_score=memory_match_score,
        authority_claim_score=authority_claim_score,
        parser_confidence_score=parser_confidence_score,
        source_recency_score=source_recency_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchEventMemoryAuthorityClaimScorecardObservation,
    cfg: ResearchEventMemoryAuthorityClaimScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventMemoryAuthorityClaimScorecardReport:
    return build_research_event_memory_authority_claim_scorecard_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in public payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def iter_payload_keys(value: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(iter_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(iter_payload_keys(item))
    return keys


def iter_payload_strings(value: Any) -> list[str]:
    strings: list[str] = []
    if isinstance(value, str):
        strings.append(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            strings.append(key)
            strings.extend(iter_payload_strings(item))
    elif isinstance(value, list):
        for item in value:
            strings.extend(iter_payload_strings(item))
    return strings


def test_pass_report_has_deterministic_decimal_payload_and_validated_digest() -> None:
    digest = report(
        observation("event-clear", claim_key="claim-clear"),
    )

    assert is_dataclass(digest)
    with pytest.raises(FrozenInstanceError):
        digest.status = "watch"  # type: ignore[misc]
    assert digest.generated_at == GENERATED_AT
    assert digest.generated_at.tzinfo is UTC
    assert digest.config_version == (
        DEFAULT_RESEARCH_EVENT_MEMORY_AUTHORITY_CLAIM_SCORECARD_CONFIG_VERSION
    )
    assert digest.event_count == d("1.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == ZERO
    assert digest.block_count == ZERO
    assert digest.status == "pass"
    assert digest.reason_codes == ("authority_claim_scorecard_pass",)
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    row = digest.rows[0]
    assert row.status == "pass"
    assert row.event_age_seconds == d("7200.000000")
    assert row.conflict_ratio == d("0.000000")
    assert row.claim_score == d("0.782000")
    assert row.reason_codes == ("authority_claim_supported",)

    payload = research_event_memory_authority_claim_scorecard_payload(digest)
    assert payload["event_count"] == "1.000000"
    assert payload["rows"][0]["claim_score"] == "0.782000"
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float(payload)

    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    expected_digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    assert research_event_memory_authority_claim_scorecard_sha256_digest(digest) == (
        expected_digest
    )
    assert validate_research_event_memory_authority_claim_scorecard_digest(
        digest,
        expected_digest,
    )
    assert research_event_memory_authority_claim_scorecard_payload(digest) == payload


def test_watch_and_block_statuses_roll_up_with_reason_counts() -> None:
    digest = report(
        observation("event-watch", claim_key="claim-watch", authority_claim_score=d("0.620000")),
        observation(
            "event-block",
            claim_key="claim-block",
            authority_claim_score=d("0.400000"),
            independent_source_count=d("0.000000"),
            conflicting_source_count=d("3.000000"),
        ),
        observation("event-pass", claim_key="claim-pass"),
    )

    assert tuple(row.status for row in digest.rows) == ("block", "watch", "pass")
    assert digest.status == "block"
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.block_count == d("1.000000")
    assert digest.reason_codes == (
        "authority_claim_scorecard_block",
        "authority_claim_score_block",
        "authority_claim_score_watch",
        "conflict_ratio_block",
        "independent_support_missing_block",
    )
    assert "authority_claim_score_watch" in digest.rows[1].reason_codes
    assert "independent_support_missing_block" in digest.rows[0].reason_codes
    assert digest.reason_code_counts == (
        ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount(
            reason_code="authority_claim_score_block",
            count=d("1.000000"),
        ),
        ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount(
            reason_code="authority_claim_score_watch",
            count=d("1.000000"),
        ),
        ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount(
            reason_code="authority_claim_supported",
            count=d("1.000000"),
        ),
        ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount(
            reason_code="conflict_ratio_block",
            count=d("1.000000"),
        ),
        ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount(
            reason_code="independent_support_missing_block",
            count=d("1.000000"),
        ),
    )


def test_empty_inputs_are_report_only_blocked() -> None:
    digest = report()

    assert digest.status == "block"
    assert digest.event_count == ZERO
    assert digest.pass_count == ZERO
    assert digest.watch_count == ZERO
    assert digest.block_count == ZERO
    assert digest.mean_claim_score == ZERO
    assert digest.max_conflict_ratio == ZERO
    assert digest.reason_codes == (
        "research_event_memory_authority_claim_scorecard_no_inputs",
    )
    assert digest.reason_code_counts == (
        ResearchEventMemoryAuthorityClaimScorecardReasonCodeCount(
            reason_code="research_event_memory_authority_claim_scorecard_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert digest.rows == ()
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True


def test_strict_decimal_datetime_and_hard_flag_boundaries() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        observation(source_count=4)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Decimal"):
        observation(authority_claim_score=0.75)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)

    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 9, 10, 0))

    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 9, 10, 0, tzinfo=_NoneOffsetTimezone()))

    with pytest.raises(TypeError, match="exactly"):
        class BadRow(ResearchEventMemoryAuthorityClaimScorecardRow):
            pass


def test_public_dataclasses_expose_decimal_fields_only_for_numeric_values() -> None:
    digest = report(observation("event-decimal", claim_key="claim-decimal"))
    public_values = (
        config(),
        observation("event-decimal-field", claim_key="claim-decimal-field"),
        digest,
        digest.rows[0],
        digest.reason_code_counts[0],
    )

    for value in public_values:
        assert is_dataclass(value)
        for field in fields(value):
            field_value = getattr(value, field.name)
            if isinstance(field_value, float) or type(field_value) is int:
                pytest.fail(f"{type(value).__name__}.{field.name} is not Decimal-only")
            if type(field_value) is Decimal:
                assert field_value.as_tuple().exponent == -6


def test_public_payload_redacts_raw_inputs_and_rejects_tampered_digest() -> None:
    digest = report(observation("event-safe", claim_key="claim-safe"))
    payload = research_event_memory_authority_claim_scorecard_payload(digest)

    forbidden_key_fragments = (
        "candidate",
        "market",
        "source_url",
        "source_text",
        "raw_text",
        "dsn",
        "table",
        "token",
    )
    for key in iter_payload_keys(payload):
        lowered = key.lower()
        assert all(fragment not in lowered for fragment in forbidden_key_fragments)

    forbidden_string_fragments = (
        "://",
        "www.",
        "postgres",
        "mysql",
        "sqlite",
        "token=",
        "raw text",
    )
    for value in iter_payload_strings(payload):
        lowered = value.lower()
        assert all(fragment not in lowered for fragment in forbidden_string_fragments)

    with pytest.raises(ValueError, match="public"):
        observation(claim_key="https://example.test/raw")

    valid_digest = research_event_memory_authority_claim_scorecard_sha256_digest(digest)
    tampered_digest = "0" * 64 if valid_digest != "0" * 64 else "1" * 64
    assert not validate_research_event_memory_authority_claim_scorecard_digest(
        digest,
        tampered_digest,
    )
    with pytest.raises(ValueError, match="sha256"):
        validate_research_event_memory_authority_claim_scorecard_digest(digest, "not-a-digest")


def test_module_does_not_import_external_side_effect_facilities() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)

    assert imported_roots.isdisjoint(
        {
            "asyncio",
            "ccxt",
            "os",
            "requests",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "subprocess",
            "urllib",
            "web3",
        },
    )
    assert called_names.isdisjoint({"open", "connect", "request", "urlopen"})
