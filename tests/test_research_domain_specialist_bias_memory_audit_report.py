from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_domain_specialist_bias_memory_audit_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def item(domain_label: str, specialist_label: str, memory_lane: str, **overrides: object):
    module = api()
    values = {
        "domain_label": domain_label,
        "specialist_label": specialist_label,
        "memory_lane": memory_lane,
        "observed_at": GENERATED_AT - timedelta(seconds=3600),
        "long_term_memory_count": d("10"),
        "repeated_directional_bias_count": d("0"),
        "stale_lesson_count": d("0"),
        "post_outcome_error_count": d("1"),
        "unresolved_post_outcome_error_count": d("0"),
        "required_correction_count": d("3"),
        "covered_correction_count": d("3"),
        "redaction_confirmed": True,
    }
    values.update(overrides)
    return module.ResearchDomainSpecialistBiasMemoryAuditInput(**values)


def report(
    *items: object,
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = api()
    return module.build_research_domain_specialist_bias_memory_audit_report(
        items,
        config=cfg or module.ResearchDomainSpecialistBiasMemoryAuditConfig(),
        generated_at=generated_at,
    )


def test_bias_memory_audit_flags_repeated_bias_stale_lessons_errors_and_corrections() -> None:
    module = api()
    blocked = item(
        "macro-memory",
        "specialist-a",
        "policy-lessons",
        long_term_memory_count=d("10"),
        repeated_directional_bias_count=d("4"),
        stale_lesson_count=d("3"),
        post_outcome_error_count=d("4"),
        unresolved_post_outcome_error_count=d("2"),
        required_correction_count=d("6"),
        covered_correction_count=d("2"),
    )
    watched = item(
        "sports-memory",
        "specialist-b",
        "injury-lessons",
        repeated_directional_bias_count=d("1"),
        stale_lesson_count=d("1"),
        post_outcome_error_count=d("2"),
        required_correction_count=d("4"),
        covered_correction_count=d("3"),
    )
    passing = item("crypto-memory", "specialist-c", "liquidity-lessons")

    audit = report(passing, blocked, watched)
    rebuilt = report(watched, passing, blocked)
    changed = report(
        passing,
        watched,
        item(
            "macro-memory",
            "specialist-a",
            "policy-lessons",
            long_term_memory_count=d("10"),
            repeated_directional_bias_count=d("4"),
            stale_lesson_count=d("2"),
            post_outcome_error_count=d("4"),
            unresolved_post_outcome_error_count=d("2"),
            required_correction_count=d("6"),
            covered_correction_count=d("2"),
        ),
    )

    assert type(audit) is module.ResearchDomainSpecialistBiasMemoryAuditReport
    assert is_dataclass(audit)
    assert audit.status == "block"
    assert audit.input_count == d("3")
    assert audit.row_count == d("3")
    assert audit.domain_count == d("3")
    assert audit.specialist_count == d("3")
    assert audit.lane_count == d("3")
    assert audit.pass_count == d("1")
    assert audit.watch_count == d("1")
    assert audit.block_count == d("1")
    assert audit.repeated_directional_bias_count == d("5")
    assert audit.stale_lesson_count == d("4")
    assert audit.post_outcome_error_count == d("7")
    assert audit.unresolved_post_outcome_error_count == d("2")
    assert audit.required_correction_count == d("13")
    assert audit.covered_correction_count == d("8")
    assert audit.average_directional_bias_ratio == d("0.166667")
    assert audit.average_stale_lesson_ratio == d("0.133333")
    assert audit.average_unresolved_post_outcome_error_ratio == d("0.166667")
    assert audit.average_correction_coverage_ratio == d("0.694444")
    assert audit.average_bias_memory_audit_score == d("0.806944")
    assert audit.reason_codes == (
        "directional_bias_repeated_block",
        "directional_bias_repeated_watch",
        "stale_lessons_block",
        "stale_lessons_watch",
        "post_outcome_errors_unresolved_block",
        "correction_coverage_weak_block",
        "correction_coverage_weak_watch",
        "domain_specialist_bias_memory_audit_block",
        "domain_specialist_bias_memory_audit_watch",
    )
    assert audit.paper_only is True
    assert audit.report_only is True
    assert audit.readonly is True

    assert tuple(row.row_status for row in audit.rows) == ("block", "watch", "pass")
    assert audit.rows[0] == module.ResearchDomainSpecialistBiasMemoryAuditRow(
        domain_label="macro-memory",
        specialist_label="specialist-a",
        memory_lane="policy-lessons",
        observed_at=GENERATED_AT - timedelta(seconds=3600),
        snapshot_age_seconds=d("3600.000000"),
        long_term_memory_count=d("10"),
        repeated_directional_bias_count=d("4"),
        stale_lesson_count=d("3"),
        post_outcome_error_count=d("4"),
        unresolved_post_outcome_error_count=d("2"),
        required_correction_count=d("6"),
        covered_correction_count=d("2"),
        directional_bias_ratio=d("0.400000"),
        stale_lesson_ratio=d("0.300000"),
        unresolved_post_outcome_error_ratio=d("0.500000"),
        correction_coverage_ratio=d("0.333333"),
        bias_memory_audit_score=d("0.533333"),
        row_status="block",
        reason_codes=(
            "directional_bias_repeated_block",
            "stale_lessons_block",
            "post_outcome_errors_unresolved_block",
            "correction_coverage_weak_block",
            "domain_specialist_bias_memory_audit_block",
        ),
    )

    payload = module.research_domain_specialist_bias_memory_audit_report_payload(audit)
    assert payload == audit.payload
    assert payload["rows"][0]["bias_memory_audit_score"] == "0.533333"
    assert payload["rows"][0]["snapshot_age_seconds"] == "3600.000000"
    assert payload["derived_validation_digest"] == audit.derived_validation_digest
    assert len(audit.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in audit.derived_validation_digest)
    assert audit.derived_validation_digest == rebuilt.derived_validation_digest
    assert audit.derived_validation_digest != changed.derived_validation_digest
    _assert_no_floats(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_empty_bias_memory_audit_blocks_without_raw_public_identifiers() -> None:
    audit = report()

    assert audit.status == "block"
    assert audit.input_count == d("0")
    assert audit.row_count == d("0")
    assert audit.pass_count == d("0")
    assert audit.watch_count == d("0")
    assert audit.block_count == d("0")
    assert audit.average_bias_memory_audit_score == d("0.000000")
    assert audit.reason_codes == ("domain_specialist_bias_memory_audit_no_inputs",)
    assert audit.rows == ()

    payload_text = repr(audit.payload).lower()
    for forbidden in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden not in payload_text


def test_bias_memory_audit_is_frozen_decimal_only_public_safe_and_readonly() -> None:
    module = api()
    audit = report(item("ops-memory", "specialist-a", "decision-lessons"))

    assert module.RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_REPORT_CONFIG_VERSION",
        "RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_STATUSES",
        "RESEARCH_DOMAIN_SPECIALIST_BIAS_MEMORY_AUDIT_REASON_CODES",
        "ResearchDomainSpecialistBiasMemoryAuditConfig",
        "ResearchDomainSpecialistBiasMemoryAuditInput",
        "ResearchDomainSpecialistBiasMemoryAuditReport",
        "ResearchDomainSpecialistBiasMemoryAuditRow",
        "build_research_domain_specialist_bias_memory_audit_report",
        "research_domain_specialist_bias_memory_audit_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    with pytest.raises(FrozenInstanceError):
        audit.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="long_term_memory_count must be a Decimal"):
        item("ops-memory", "specialist-a", "decision-lessons", long_term_memory_count=10)
    with pytest.raises(ValueError, match="long_term_memory_count must be positive"):
        item("ops-memory", "specialist-a", "decision-lessons", long_term_memory_count=d("0"))
    with pytest.raises(ValueError, match="repeated_directional_bias_count must be a Decimal"):
        item(
            "ops-memory",
            "specialist-a",
            "decision-lessons",
            repeated_directional_bias_count=_DecimalSubclass("1"),
        )
    with pytest.raises(ValueError, match="repeated_directional_bias_count"):
        item(
            "ops-memory",
            "specialist-a",
            "decision-lessons",
            repeated_directional_bias_count=d("11"),
        )
    with pytest.raises(ValueError, match="observed_at"):
        item(
            "ops-memory",
            "specialist-a",
            "decision-lessons",
            observed_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at"):
        item(
            "ops-memory",
            "specialist-a",
            "decision-lessons",
            observed_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="domain_label"):
        item(_StringSubclass("ops-memory"), "specialist-a", "decision-lessons")
    with pytest.raises(ValueError, match="public-safe"):
        item("wallet", "specialist-a", "decision-lessons")
    with pytest.raises(ValueError, match="public-safe"):
        item("candidate-id-123", "specialist-a", "decision-lessons")
    with pytest.raises(ValueError, match="public-safe"):
        item("ops-memory", "market slug tracker", "decision-lessons")
    with pytest.raises(ValueError, match="redaction_confirmed"):
        item("ops-memory", "specialist-a", "decision-lessons", redaction_confirmed=False)
    with pytest.raises(ValueError, match="generated_at"):
        report(
            item(
                "ops-memory",
                "specialist-a",
                "decision-lessons",
                observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(module.ResearchDomainSpecialistBiasMemoryAuditConfig(), paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(audit, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="config_version"):
        replace(audit, config_version="other-safe-version")
    with pytest.raises(ValueError, match="repeated_directional_bias_count"):
        replace(audit, repeated_directional_bias_count=d("99"))
    with pytest.raises(ValueError, match="average_directional_bias_ratio"):
        replace(audit, average_directional_bias_ratio=d("0.990000"))
    with pytest.raises(ValueError, match="unsafe public-safe"):
        module.research_domain_specialist_bias_memory_audit_report_payload(
            {**audit.payload, "public_note": "source-url redacted upstream"},
        )
    assert (
        report(
            item("ops-memory", "specialist-a", "decision-lessons"),
            generated_at=datetime(2026, 7, 8, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
        ).generated_at
        == GENERATED_AT
    )

    _assert_public_numeric_values_are_decimal(audit)
    _assert_no_floats(audit.payload)


def test_module_scope_has_no_external_or_decision_action_surface() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_domain_specialist_bias_memory_audit_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "wallet",
        "account",
        "private_key",
        "api_key",
        "secret",
        "clob",
        "submit",
        "cancel",
        "signing",
        "trading",
        "client",
        "execute",
        "connect",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and type(node.value) is float
        for node in ast.walk(tree)
    )
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "typing",
    }


def _assert_no_floats(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def _assert_public_numeric_values_are_decimal(value: Any) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:
            _assert_public_numeric_values_are_decimal(getattr(value, field_name))
    if isinstance(value, dict):
        for item in value.values():
            _assert_public_numeric_values_are_decimal(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_public_numeric_values_are_decimal(item)
