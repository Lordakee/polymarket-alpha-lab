from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_local_supabase_retention_policy import (
    DEFAULT_RESEARCH_LOCAL_SUPABASE_RETENTION_POLICY_CONFIG_VERSION,
    ResearchLocalSupabaseRetentionPolicyConfig,
    ResearchLocalSupabaseRetentionPolicyInputRow,
    ResearchLocalSupabaseRetentionPolicyReasonCodeCount,
    ResearchLocalSupabaseRetentionPolicyReport,
    ResearchLocalSupabaseRetentionPolicyRow,
    build_research_local_supabase_retention_policy_report,
    research_local_supabase_retention_policy_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def fingerprint(value: str) -> str:
    return f"sha256:{sha256(value.encode()).hexdigest()[:12]}"


def config(**overrides: object) -> ResearchLocalSupabaseRetentionPolicyConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_LOCAL_SUPABASE_RETENTION_POLICY_CONFIG_VERSION,
        "max_memory_retention_days": d("365.000000"),
        "max_deidentification_lag_days": d("30.000000"),
        "min_review_retention_days": d("90.000000"),
        "max_review_retention_days": d("730.000000"),
        "min_source_summary_retention_days": d("90.000000"),
        "max_source_summary_retention_days": d("730.000000"),
        "min_audit_log_retention_days": d("180.000000"),
        "max_audit_log_retention_days": d("730.000000"),
    }
    values.update(overrides)
    return ResearchLocalSupabaseRetentionPolicyConfig(**values)


def input_row(
    record_class: str = "research_memory",
    *,
    retention_days: Decimal = d("180.000000"),
    deidentify_after_days: Decimal = d("7.000000"),
    review_retention_days: Decimal = d("180.000000"),
    source_summary_retention_days: Decimal = d("365.000000"),
    audit_log_retention_days: Decimal = d("365.000000"),
    unredacted_reference_present: bool = False,
    direct_identifier_present: bool = False,
    source_summary_present: bool = True,
    audit_log_present: bool = True,
    review_required: bool = True,
    review_age_days: Decimal = d("30.000000"),
    reference_locator: str | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchLocalSupabaseRetentionPolicyInputRow:
    return ResearchLocalSupabaseRetentionPolicyInputRow(
        record_class=record_class,
        retention_days=retention_days,
        deidentify_after_days=deidentify_after_days,
        review_retention_days=review_retention_days,
        source_summary_retention_days=source_summary_retention_days,
        audit_log_retention_days=audit_log_retention_days,
        unredacted_reference_present=unredacted_reference_present,
        direct_identifier_present=direct_identifier_present,
        source_summary_present=source_summary_present,
        audit_log_present=audit_log_present,
        review_required=review_required,
        review_age_days=review_age_days,
        reference_locator=reference_locator,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchLocalSupabaseRetentionPolicyInputRow, ...],
    *,
    cfg: ResearchLocalSupabaseRetentionPolicyConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchLocalSupabaseRetentionPolicyReport:
    return build_research_local_supabase_retention_policy_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_retention_policy_reports_pass_watch_and_block_without_sensitive_payload() -> None:
    unsafe_locator = (
        "postgres://user:pw@localhost:54322/app?"
        "token=super-secret&table=market_alpha_raw_source"
    )
    summary = report(
        (
            input_row(
                "source_summary",
                retention_days=d("90.000000"),
                review_retention_days=d("800.000000"),
                source_summary_retention_days=d("20.000000"),
                audit_log_retention_days=d("800.000000"),
                source_summary_present=False,
                review_required=False,
            ),
            input_row(
                "review_snapshot",
                retention_days=d("400.000000"),
                deidentify_after_days=d("45.000000"),
                review_retention_days=d("30.000000"),
                audit_log_retention_days=d("30.000000"),
                unredacted_reference_present=True,
                direct_identifier_present=True,
                audit_log_present=False,
                review_age_days=d("45.000000"),
                reference_locator=unsafe_locator,
            ),
            input_row("research_memory"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, ResearchLocalSupabaseRetentionPolicyReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_RESEARCH_LOCAL_SUPABASE_RETENTION_POLICY_CONFIG_VERSION
    )
    assert summary.policy_status == "block"
    assert summary.recommended_next_step == (
        "block_report_only_research_local_supabase_retention_policy"
    )
    assert summary.policy_subject_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.retention_gap_count == d("1.000000")
    assert summary.deidentification_gap_count == d("1.000000")
    assert summary.review_retention_gap_count == d("2.000000")
    assert summary.source_summary_gap_count == d("1.000000")
    assert summary.audit_log_gap_count == d("2.000000")
    assert summary.reference_fingerprint_count == d("1.000000")
    assert summary.source_summary_coverage_ratio == d("0.666667")
    assert summary.audit_log_coverage_ratio == d("0.666667")
    assert summary.average_retention_days == d("223.333333")
    assert summary.max_retention_days == d("400.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.policy_status for row in summary.rows) == ("block", "watch", "pass")
    blocked = summary.rows[0]
    assert blocked.record_class == "review_snapshot"
    assert blocked.reference_fingerprint == fingerprint(unsafe_locator)
    assert blocked.reason_codes == (
        "research_local_supabase_retention_policy_audit_log_missing",
        "research_local_supabase_retention_policy_audit_log_retention_shortfall",
        "research_local_supabase_retention_policy_deidentification_gap",
        "research_local_supabase_retention_policy_retention_period_exceeds_limit",
        "research_local_supabase_retention_policy_review_retention_shortfall",
        "research_local_supabase_retention_policy_review_window_expired",
    )

    watched = summary.rows[1]
    assert watched.record_class == "source_summary"
    assert watched.reason_codes == (
        "research_local_supabase_retention_policy_audit_log_retention_exceeds_limit",
        "research_local_supabase_retention_policy_review_retention_exceeds_limit",
        "research_local_supabase_retention_policy_source_summary_missing",
        "research_local_supabase_retention_policy_source_summary_retention_shortfall",
    )

    passed = summary.rows[2]
    assert passed.record_class == "research_memory"
    assert passed.reason_codes == ("research_local_supabase_retention_policy_pass",)

    assert summary.reason_code_counts == (
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code="research_local_supabase_retention_policy_audit_log_missing",
            count=d("1.000000"),
            subject_ratio=d("0.333333"),
        ),
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code=(
                "research_local_supabase_retention_policy_audit_log_retention_exceeds_limit"
            ),
            count=d("1.000000"),
            subject_ratio=d("0.333333"),
        ),
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code=(
                "research_local_supabase_retention_policy_audit_log_retention_shortfall"
            ),
            count=d("1.000000"),
            subject_ratio=d("0.333333"),
        ),
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code="research_local_supabase_retention_policy_deidentification_gap",
            count=d("1.000000"),
            subject_ratio=d("0.333333"),
        ),
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code="research_local_supabase_retention_policy_pass",
            count=d("1.000000"),
            subject_ratio=d("0.333333"),
        ),
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code=(
                "research_local_supabase_retention_policy_retention_period_exceeds_limit"
            ),
            count=d("1.000000"),
            subject_ratio=d("0.333333"),
        ),
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code=(
                "research_local_supabase_retention_policy_review_retention_exceeds_limit"
            ),
            count=d("1.000000"),
            subject_ratio=d("0.333333"),
        ),
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code=(
                "research_local_supabase_retention_policy_review_retention_shortfall"
            ),
            count=d("1.000000"),
            subject_ratio=d("0.333333"),
        ),
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code="research_local_supabase_retention_policy_review_window_expired",
            count=d("1.000000"),
            subject_ratio=d("0.333333"),
        ),
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code="research_local_supabase_retention_policy_source_summary_missing",
            count=d("1.000000"),
            subject_ratio=d("0.333333"),
        ),
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code=(
                "research_local_supabase_retention_policy_source_summary_retention_shortfall"
            ),
            count=d("1.000000"),
            subject_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )

    payload = research_local_supabase_retention_policy_payload(summary)
    encoded = json.dumps(payload, sort_keys=True)
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["retention_days"] == "400.000000"
    assert payload["rows"][0]["reference_fingerprint"] == fingerprint(unsafe_locator)
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 400.0" not in encoded
    assert ": 0." not in encoded

    public = repr(payload).lower()
    for unsafe in (
        "postgres://",
        "localhost",
        "super-secret",
        "token=",
        "table=",
        "market_alpha",
        "raw_source",
        unsafe_locator.lower(),
    ):
        assert unsafe not in public


def test_empty_inputs_return_report_only_block_policy() -> None:
    summary = report(())

    assert summary.policy_status == "block"
    assert summary.recommended_next_step == (
        "block_report_only_research_local_supabase_retention_policy"
    )
    assert summary.policy_subject_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == (
        "research_local_supabase_retention_policy_no_inputs",
    )
    assert summary.reason_code_counts == (
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount(
            reason_code="research_local_supabase_retention_policy_no_inputs",
            count=d("1.000000"),
            subject_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_validation_rejects_bad_decimal_datetime_flags_types_and_manual_rows() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        input_row(retention_days=180)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="Decimal"):
        input_row(retention_days=_DecimalSubclass("180.000000"))

    with pytest.raises(ValueError, match="nonnegative"):
        input_row(review_age_days=d("-1.000000"))

    with pytest.raises(TypeError, match="str"):
        input_row(record_class=_StringSubclass("research_memory"))

    with pytest.raises(ValueError, match="record class"):
        input_row(record_class="unknown_subject")

    with pytest.raises(TypeError, match="bool"):
        input_row(audit_log_present=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)

    with pytest.raises(ValueError, match="min_review_retention_days"):
        config(
            min_review_retention_days=d("731.000000"),
            max_review_retention_days=d("730.000000"),
        )

    with pytest.raises(TypeError, match="datetime"):
        report((input_row(),), generated_at="2026-07-06T12:00:00Z")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        report((input_row(),), generated_at=datetime(2026, 7, 6, 12, 0))

    with pytest.raises(ValueError, match="whole second"):
        report((input_row(),), generated_at=datetime(2026, 7, 6, 12, 0, 0, 1, tzinfo=UTC))

    with pytest.raises(TypeError, match="exactly"):
        report(
            (input_row(),),
            generated_at=_DateTimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.policy_status = "watch"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        summary.rows[0].retention_days = d("1.000000")  # type: ignore[misc]

    with pytest.raises(ValueError, match="policy_status"):
        replace(summary.rows[0], policy_status="block")

    with pytest.raises(ValueError, match="reference_fingerprint"):
        replace(summary.rows[0], reference_fingerprint="unsafe-public-reference")

    with pytest.raises(ValueError, match="pass_count"):
        replace(summary, pass_count=d("0.000000"))

    assert replace(input_row(), retention_days=d("181.000000")).retention_days == d(
        "181.000000",
    )


def test_public_dataclasses_are_frozen_and_payload_rejects_sensitive_tampering() -> None:
    summary = report((input_row(reference_locator="public-review-note"),))
    payload = research_local_supabase_retention_policy_payload(summary)

    assert payload["rows"][0]["reference_fingerprint"] == fingerprint("public-review-note")
    assert "public-review-note" not in repr(payload)

    for cls in (
        ResearchLocalSupabaseRetentionPolicyConfig,
        ResearchLocalSupabaseRetentionPolicyInputRow,
        ResearchLocalSupabaseRetentionPolicyRow,
        ResearchLocalSupabaseRetentionPolicyReasonCodeCount,
        ResearchLocalSupabaseRetentionPolicyReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    public = repr(asdict(summary)).lower()
    for unsafe in ("public-review-note", "token", "table", "raw_source"):
        assert unsafe not in public


def test_module_is_report_only_and_has_no_io_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_local_supabase_retention_policy.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "asyncpg",
        "builtins",
        "io",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "subprocess",
        "supabase",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "delete",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }
    forbidden_terms = (
        "wallet",
        "broker",
        "signing",
        "order",
        "cancel",
        "account",
        "advice",
        "trade",
    )

    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)
    assert not any(term in source.lower() for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
