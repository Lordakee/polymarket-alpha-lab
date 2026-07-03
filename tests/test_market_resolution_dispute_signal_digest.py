from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 16, 0, tzinfo=UTC)


def module():
    return importlib.import_module(
        "polymarket_alpha_lab.market_resolution_dispute_signal_digest",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def signal(
    market_slug: str,
    *,
    category: str = "macro",
    source_name: str = "gamma",
    observed_at: datetime | None = None,
    dispute_signal_score: Decimal = d("0.000000"),
    resolution_source_count: Decimal = d("2"),
    conflicting_source_count: Decimal = d("0"),
    unresolved_evidence_count: Decimal = d("0"),
    sensitive_reference: str = "https://example.invalid/private?token=secret",
):
    digest = module()
    return digest.MarketResolutionDisputeSignalInput(
        market_slug=market_slug,
        category=category,
        source_name=source_name,
        observed_at=observed_at or (GENERATED_AT - timedelta(hours=1)),
        dispute_signal_score=dispute_signal_score,
        resolution_source_count=resolution_source_count,
        conflicting_source_count=conflicting_source_count,
        unresolved_evidence_count=unresolved_evidence_count,
        sensitive_reference=sensitive_reference,
    )


def config(**overrides: object):
    digest = module()
    values: dict[str, object] = {
        "watch_dispute_signal_score": d("0.300000"),
        "blocked_dispute_signal_score": d("0.700000"),
        "stale_signal_after_hours": d("24.000000"),
    }
    values.update(overrides)
    return digest.MarketResolutionDisputeSignalDigestConfig(**values)


def report(*rows, cfg=None, generated_at: datetime = GENERATED_AT):
    digest = module()
    return digest.build_market_resolution_dispute_signal_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if any(
            fragment in field.name
            for fragment in (
                "count",
                "score",
                "ratio",
                "hours",
            )
        ) and field.name not in {"reason_code_counts"}:
            assert type(getattr(value, field.name)) is Decimal
            assert value.__annotations__[field.name] is Decimal


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float leaked into payload: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def test_empty_digest_is_blocked_report_only_and_uses_decimal_zeroes() -> None:
    digest_report = report()

    assert is_dataclass(digest_report)
    assert digest_report.generated_at == GENERATED_AT
    assert digest_report.generated_at.tzinfo is UTC
    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == "review_resolution_dispute_signals"
    assert digest_report.market_count == d("0")
    assert digest_report.pass_count == d("0")
    assert digest_report.watch_count == d("0")
    assert digest_report.blocked_count == d("0")
    assert digest_report.conflict_ratio == d("0.000000")
    assert digest_report.blocked_ratio == d("0.000000")
    assert digest_report.max_dispute_signal_score == d("0.000000")
    assert digest_report.rows == ()
    assert digest_report.reason_code_counts == (
        module().MarketResolutionDisputeSignalReasonCodeCount(
            reason_code="market_resolution_dispute_signal_digest_empty_sources",
            count=d("1"),
        ),
    )
    assert digest_report.reason_codes == (
        "market_resolution_dispute_signal_digest_empty_sources",
    )
    assert digest_report.paper_only is True
    assert digest_report.report_only is True
    assert digest_report.readonly is True
    assert_decimal_public_numbers(digest_report)


def test_clear_inputs_pass_and_rows_sort_deterministically() -> None:
    digest_report = report(
        signal("z-market", category="sports"),
        signal("a-market", category="macro"),
    )

    assert digest_report.digest_status == "pass"
    assert digest_report.recommended_next_step == "continue_resolution_monitoring"
    assert digest_report.market_count == d("2")
    assert digest_report.pass_count == d("2")
    assert digest_report.watch_count == d("0")
    assert digest_report.blocked_count == d("0")
    assert digest_report.conflict_ratio == d("0.000000")
    assert digest_report.blocked_ratio == d("0.000000")
    assert digest_report.max_dispute_signal_score == d("0.000000")
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "a-market",
        "z-market",
    )
    assert digest_report.reason_codes == (
        "market_resolution_dispute_signal_digest_passed",
    )
    for row in digest_report.rows:
        assert row.status == "pass"
        assert row.reason_codes == ("market_resolution_dispute_signal_row_passed",)
        assert row.sensitive_reference == "<redacted-sensitive-reference>"
        assert_decimal_public_numbers(row)


def test_watch_and_blocked_reason_codes_counts_and_ratios_are_stable() -> None:
    digest_report = report(
        signal(
            "blocked-market",
            category="crypto",
            dispute_signal_score=d("0.800000"),
            resolution_source_count=d("3"),
            conflicting_source_count=d("2"),
            unresolved_evidence_count=d("1"),
        ),
        signal(
            "watch-market",
            category="macro",
            observed_at=GENERATED_AT - timedelta(days=2),
            dispute_signal_score=d("0.400000"),
            resolution_source_count=d("2"),
            conflicting_source_count=d("1"),
            unresolved_evidence_count=d("0"),
        ),
    )

    assert digest_report.digest_status == "blocked"
    assert digest_report.recommended_next_step == "pause_resolution_sensitive_review"
    assert digest_report.market_count == d("2")
    assert digest_report.pass_count == d("0")
    assert digest_report.watch_count == d("1")
    assert digest_report.blocked_count == d("1")
    assert digest_report.conflict_ratio == d("0.600000")
    assert digest_report.blocked_ratio == d("0.500000")
    assert digest_report.max_dispute_signal_score == d("0.800000")
    assert digest_report.reason_codes == (
        "market_resolution_dispute_signal_digest_blocked",
        "resolution_dispute_signal_high",
        "resolution_dispute_signal_watch",
        "resolution_evidence_stale",
        "resolution_source_conflict",
        "resolution_unresolved_evidence_present",
    )
    assert tuple(count.reason_code for count in digest_report.reason_code_counts) == (
        "resolution_source_conflict",
        "market_resolution_dispute_signal_digest_blocked",
        "resolution_dispute_signal_high",
        "resolution_dispute_signal_watch",
        "resolution_evidence_stale",
        "resolution_unresolved_evidence_present",
    )
    assert tuple(count.count for count in digest_report.reason_code_counts) == (
        d("2"),
        d("1"),
        d("1"),
        d("1"),
        d("1"),
        d("1"),
    )
    assert tuple(row.market_slug for row in digest_report.rows) == (
        "blocked-market",
        "watch-market",
    )
    assert digest_report.rows[0].status == "blocked"
    assert digest_report.rows[0].reason_codes == (
        "resolution_dispute_signal_high",
        "resolution_source_conflict",
        "resolution_unresolved_evidence_present",
    )
    assert digest_report.rows[1].status == "watch"
    assert digest_report.rows[1].reason_codes == (
        "resolution_dispute_signal_watch",
        "resolution_evidence_stale",
        "resolution_source_conflict",
    )


def test_payload_redacts_sensitive_references_and_uses_decimal_strings() -> None:
    digest_report = report(
        signal(
            "sensitive-market",
            dispute_signal_score=d("0.900000"),
            conflicting_source_count=d("1"),
            sensitive_reference="https://example.invalid/path?api_key=secret-token",
        ),
        generated_at=GENERATED_AT.replace(tzinfo=timezone(timedelta(hours=-5))),
    )

    payload = module().market_resolution_dispute_signal_digest_payload(digest_report)

    assert isinstance(payload, MappingProxyType)
    assert payload["generated_at"] == "2026-07-02T21:00:00+00:00"
    assert payload["market_count"] == "1"
    assert payload["blocked_ratio"] == "1.000000"
    assert payload["rows"][0]["sensitive_reference"] == "<redacted-sensitive-reference>"
    assert "secret-token" not in json.dumps(dict(payload))
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)


def test_rejects_float_nonfinite_decimal_naive_datetimes_duplicates_and_bad_flags() -> None:
    digest = module()

    with pytest.raises(ValueError, match="config"):
        digest.build_market_resolution_dispute_signal_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        report(generated_at=datetime(2026, 7, 2, 16, 0))

    with pytest.raises(ValueError, match="dispute_signal_score"):
        signal("float-market", dispute_signal_score=0.5)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="conflicting_source_count"):
        signal("nan-market", conflicting_source_count=Decimal("NaN"))

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    with pytest.raises(ValueError, match="unique"):
        report(signal("dup-market"), signal("dup-market"))


def test_public_dataclasses_are_frozen_decimal_only_and_exact_types() -> None:
    digest = module()
    digest_report = report(signal("clear-market"))
    values = (
        config(),
        signal("input-market"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    )

    for value in values:
        assert is_dataclass(value)
        assert_decimal_public_numbers(value)
        with pytest.raises(FrozenInstanceError):
            value.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(digest_report.rows[0], paper_only=False)

    class DerivedDecimal(Decimal):
        pass

    with pytest.raises(ValueError, match="dispute_signal_score must be a Decimal"):
        digest.MarketResolutionDisputeSignalInput(
            market_slug="derived-decimal-market",
            category="macro",
            source_name="gamma",
            observed_at=GENERATED_AT,
            dispute_signal_score=DerivedDecimal("0.1"),
            resolution_source_count=d("1"),
            conflicting_source_count=d("0"),
            unresolved_evidence_count=d("0"),
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_public_dataclasses_reject_truthy_non_true_hard_flags(flag_name: str) -> None:
    digest_report = report(signal("truthy-flag-market"))
    values = (
        config(),
        signal("truthy-input-market"),
        digest_report.rows[0],
        digest_report.reason_code_counts[0],
        digest_report,
    )

    for value in values:
        with pytest.raises(ValueError, match=flag_name):
            replace(value, **{flag_name: 1})


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_report_revalidates_nested_row_and_reason_count_hard_flags(
    flag_name: str,
) -> None:
    digest_report = report(signal("nested-row-flag-market"))
    bad_row = digest_report.rows[0]
    object.__setattr__(bad_row, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        replace(digest_report, rows=(bad_row,))

    digest_report = report(signal("nested-count-flag-market"))
    bad_count = digest_report.reason_code_counts[0]
    object.__setattr__(bad_count, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        replace(digest_report, reason_code_counts=(bad_count,))


def test_static_forbidden_surface_terms_imports_and_float_literals_are_absent() -> None:
    digest = module()
    source = digest.__loader__.get_source(digest.__name__)
    assert source is not None
    tree = ast.parse(source)

    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "auth",
        "broker",
        "cli",
        "db",
        "dotenv",
        "migrations",
        "network",
        "order",
        "psycopg",
        "requests",
        "sign",
        "socket",
        "sql",
        "trade",
        "wallet",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    forbidden_surface_terms = (
        "advice",
        "auth",
        "broker",
        "database",
        "db",
        "file",
        "live_trading",
        "network",
        "order",
        "signing",
        "trade",
        "wallet",
    )
    public_names = [
        name
        for name in vars(digest)
        if not name.startswith("_") and name != "annotations"
    ]
    public_surface = "\n".join(public_names).lower()
    for term in forbidden_surface_terms:
        if term == "auth":
            assert "auth_" not in public_surface
            assert "_auth" not in public_surface
            continue
        assert term not in public_surface
