from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_event_resolution_claim_memory_latency_report"
CONFIG_VERSION = "research-event-resolution-claim-memory-latency-report-test"
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


RAW_PRIVATE_VALUES = (
    "candidate-alpha",
    "market-fed-cut-by-september",
    "https://example.test/resolution-note?token=secret-alpha",
    "raw source text says the event resolved yes",
    "postgres://user:pass@example.test:5432/claims",
    "resolution_claims_private_table",
    "secret-token-alpha",
)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "memory_latency_watch_seconds": d("300.000000"),
        "memory_latency_block_seconds": d("900.000000"),
        "resolution_latency_watch_seconds": d("3600.000000"),
        "resolution_latency_block_seconds": d("7200.000000"),
        "parser_confidence_watch_score": d("0.800000"),
        "parser_confidence_block_score": d("0.600000"),
        "claim_strength_watch_score": d("0.700000"),
        "claim_strength_block_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionClaimMemoryLatencyReportConfig(**values)


def claim(
    subject_ref: str = RAW_PRIVATE_VALUES[0],
    event_ref: str = RAW_PRIVATE_VALUES[1],
    *,
    observed_age_seconds: int = 1000,
    memory_lag_seconds: int = 120,
    resolved_lag_seconds: int | None = 600,
    **overrides: object,
) -> Any:
    module = api()
    claim_observed_at = GENERATED_AT - timedelta(seconds=observed_age_seconds)
    resolved_at = (
        None
        if resolved_lag_seconds is None
        else claim_observed_at + timedelta(seconds=resolved_lag_seconds)
    )
    values = {
        "private_subject_ref": subject_ref,
        "private_event_ref": event_ref,
        "private_evidence_locator": RAW_PRIVATE_VALUES[2],
        "private_evidence_excerpt": RAW_PRIVATE_VALUES[3],
        "private_store_locator": RAW_PRIVATE_VALUES[4],
        "private_set_name": RAW_PRIVATE_VALUES[5],
        "private_secret_marker": RAW_PRIVATE_VALUES[6],
        "claim_observed_at": claim_observed_at,
        "memory_recorded_at": claim_observed_at + timedelta(seconds=memory_lag_seconds),
        "resolved_at": resolved_at,
        "parser_confidence": d("0.950000"),
        "claim_strength": d("0.900000"),
        "reason_codes": ("resolution_claim_observed",),
    }
    values.update(overrides)
    return module.ResearchEventResolutionClaimMemoryLatencyInput(**values)


def report(*items: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_event_resolution_claim_memory_latency_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if type(item) is bool or item is None:
            continue
        assert type(item) is not float
        assert type(item) is not int
        if isinstance(item, tuple):
            for nested in item:
                if is_dataclass(nested):
                    assert_numeric_fields_are_decimal(nested)


def assert_no_float_values(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def assert_no_private_payload_terms(value: object) -> None:
    blocked_terms = (
        "candidate",
        "market",
        "source",
        "url",
        "text",
        "dsn",
        "table",
        "token",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert [term for term in blocked_terms if term in lowered] == []
            assert_no_private_payload_terms(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_private_payload_terms(item)
    elif isinstance(value, str):
        lowered = value.lower()
        assert [term for term in blocked_terms if term in lowered] == []


def test_report_rolls_up_pass_watch_block_with_decimal_digest_and_no_raw_public_leakage() -> None:
    module = api()

    result = report(
        claim(
            subject_ref="pass-subject",
            event_ref="pass-event",
            observed_age_seconds=1000,
            memory_lag_seconds=120,
            resolved_lag_seconds=600,
        ),
        claim(
            subject_ref="watch-subject",
            event_ref="watch-event",
            observed_age_seconds=5000,
            memory_lag_seconds=600,
            resolved_lag_seconds=4000,
            parser_confidence=d("0.750000"),
            claim_strength=d("0.650000"),
        ),
        claim(
            subject_ref="block-subject",
            event_ref="block-event",
            observed_age_seconds=10000,
            memory_lag_seconds=1200,
            resolved_lag_seconds=None,
            parser_confidence=d("0.550000"),
            claim_strength=d("0.400000"),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == CONFIG_VERSION
    assert result.claim_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.status == "block"
    assert result.reason_codes == (
        "claim_memory_latency_block",
        "claim_memory_latency_watch",
        "claim_memory_latency_pass",
        "memory_seen_latency_block",
        "resolution_latency_block",
        "parser_confidence_block",
        "claim_strength_block",
        "memory_seen_latency_watch",
        "resolution_latency_watch",
        "parser_confidence_watch",
        "claim_strength_watch",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.derived_validation_digest
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.claim_status for row in result.rows) == ("block", "watch", "pass")
    blocked, watched, passed = result.rows
    assert blocked.claim_memory_latency_seconds == d("1200.000000")
    assert blocked.resolution_latency_seconds == d("10000.000000")
    assert blocked.latency_score == ZERO
    assert watched.claim_memory_latency_seconds == d("600.000000")
    assert watched.resolution_latency_seconds == d("4000.000000")
    assert watched.latency_score == d("0.166667")
    assert passed.claim_memory_latency_seconds == d("120.000000")
    assert passed.resolution_latency_seconds == d("600.000000")
    assert passed.latency_score == d("0.850000")

    payload = module.research_event_resolution_claim_memory_latency_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)
    assert payload == module.research_event_resolution_claim_memory_latency_report_payload(result)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["claim_count"] == "3.000000"
    assert payload["rows"][0]["claim_memory_latency_seconds"] == "1200.000000"
    assert payload["rows"][0]["derived_validation_digest"] == (
        result.rows[0].derived_validation_digest
    )
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert_no_float_values(payload)
    assert_no_private_payload_terms(payload)
    for private_value in RAW_PRIVATE_VALUES:
        assert private_value not in encoded

    assert module.research_event_resolution_claim_memory_latency_report_payload(payload) == payload


def test_empty_report_is_block_readonly_and_decimal_zeroed() -> None:
    result = report()

    assert result.claim_count == ZERO
    assert result.pass_count == ZERO
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.status == "block"
    assert result.reason_codes == ("claim_memory_latency_report_empty",)
    assert result.rows == ()
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True


def test_inputs_config_and_datetimes_reject_invalid_values() -> None:
    module = api()

    with pytest.raises(ValueError, match="claim_strength must be a Decimal"):
        claim(claim_strength=1)
    with pytest.raises(ValueError, match="private_subject_ref must be a non-empty string"):
        claim(subject_ref="")
    with pytest.raises(ValueError, match="reason_codes must not contain duplicate values"):
        claim(reason_codes=("duplicate", "duplicate"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        claim(paper_only=False)
    with pytest.raises(ValueError, match="memory_latency_watch_seconds must be less than"):
        config(memory_latency_watch_seconds=d("1000.000000"))
    with pytest.raises(ValueError, match="parser_confidence_block_score must not exceed"):
        config(parser_confidence_block_score=d("0.900000"))
    with pytest.raises(ValueError, match="claim_strength_block_score must not exceed"):
        config(claim_strength_block_score=d("0.800000"))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_resolution_claim_memory_latency_report(
            (claim(),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_resolution_claim_memory_latency_report(
            (claim(),),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )

    future_at = GENERATED_AT + timedelta(seconds=1)
    with pytest.raises(ValueError, match="claim_observed_at must not be after"):
        report(
            claim(
                claim_observed_at=future_at,
                memory_recorded_at=future_at,
                resolved_at=None,
            ),
        )

    with pytest.raises(ValueError, match="memory_recorded_at must not be before"):
        claim(memory_recorded_at=GENERATED_AT - timedelta(seconds=1001))

    with pytest.raises(ValueError, match="resolved_at must not be before"):
        claim(resolved_at=GENERATED_AT - timedelta(seconds=1001))

    with pytest.raises(ValueError, match="claims must not contain duplicate"):
        report(claim(), claim())

    result = report(claim())
    with pytest.raises(FrozenInstanceError):
        result.rows[0].claim_status = "block"


def test_tamper_evident_result_and_payload_validation_recomputes_fields() -> None:
    module = api()
    result = report(claim())
    row = result.rows[0]

    with pytest.raises(ValueError, match="claim_memory_latency_seconds must match"):
        replace(
            row,
            claim_memory_latency_seconds=row.claim_memory_latency_seconds + d("0.000001"),
        )

    with pytest.raises(ValueError, match="latency_score must match"):
        replace(row, latency_score=row.latency_score + d("0.000001"))

    with pytest.raises(ValueError, match="claim_status must match"):
        replace(row, claim_status="block")

    unresolved = report(claim(resolved_lag_seconds=None))
    unresolved_row = unresolved.rows[0]
    tampered_unresolved_row = replace(
        unresolved_row,
        resolution_latency_seconds=d("600.000000"),
        latency_score=d("0.850000"),
        derived_validation_digest="",
    )
    with pytest.raises(ValueError, match="resolution_latency_seconds must match generated_at"):
        replace(unresolved, rows=(tampered_unresolved_row,), derived_validation_digest="")

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(row, derived_validation_digest="not-the-digest")

    with pytest.raises(ValueError, match="pass_count must match"):
        replace(result, pass_count=result.pass_count + d("1.000000"))

    sorted_result = report(claim("alpha-subject", "alpha-event"), claim("zeta-subject", "zeta-event"))
    with pytest.raises(ValueError, match="rows must be sorted deterministically"):
        replace(sorted_result, rows=tuple(reversed(sorted_result.rows)))

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(result, derived_validation_digest="not-the-digest")

    payload = module.research_event_resolution_claim_memory_latency_report_payload(result)
    with pytest.raises(ValueError, match="readonly"):
        module.research_event_resolution_claim_memory_latency_report_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.research_event_resolution_claim_memory_latency_report_payload(
            {**payload, "token": "secret-token-alpha"},
        )
    with pytest.raises(ValueError, match="Decimal\\|string"):
        module.research_event_resolution_claim_memory_latency_report_payload(
            {**payload, "claim_count": 1.0},
        )
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        module.research_event_resolution_claim_memory_latency_report_payload(
            {**payload, "claim_count": "2.000000"},
        )


def claim_result(subject_ref: str, event_ref: str, **overrides: object) -> Any:
    return report(claim(subject_ref=subject_ref, event_ref=event_ref, **overrides)).rows[0]


def test_module_is_pure_readonly_report_only_and_contains_no_io_surfaces() -> None:
    path = Path(
        "src/polymarket_alpha_lab/"
        "research_event_resolution_claim_memory_latency_report.py",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    source = path.read_text(encoding="utf-8").lower()

    def joined(*pieces: str) -> str:
        return "".join(pieces)

    banned_imports = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "submit",
        "post",
        "send",
        "login",
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}
    forbidden_terms = (
        joined("d", "b"),
        joined("live", " trading"),
        joined("au", "th"),
        joined("wallet"),
        joined("broker"),
        joined("or", "der"),
        joined("net", "work"),
        joined("database"),
        joined("private", "_key"),
        joined("sizing"),
        joined("recommendation"),
        joined("candidate"),
        joined("market"),
        joined("source"),
        joined("url"),
        joined("dsn"),
        joined("table"),
        joined("token"),
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert [term for term in forbidden_terms if term in source] == []
