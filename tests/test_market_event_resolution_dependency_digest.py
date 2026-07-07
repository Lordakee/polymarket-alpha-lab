import ast
import inspect
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import market_event_resolution_dependency_digest as digest_module
from polymarket_alpha_lab.market_event_resolution_dependency_digest import (
    MarketEventResolutionDependencyConfig,
    MarketEventResolutionDependencyInput,
    MarketEventResolutionDependencyReport,
    build_market_event_resolution_dependency_digest,
    market_event_resolution_dependency_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (Decimal, float, int):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_numeric_scalars(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_public_numeric_scalars(item)


def _config(**overrides: object) -> MarketEventResolutionDependencyConfig:
    values: dict[str, object] = {
        "config_version": "market-event-resolution-dependency-digest-v0",
        "lag_warning_seconds": Decimal("3600"),
        "lag_blocking_seconds": Decimal("7200"),
        "min_evidence_chain_link_count": Decimal("2"),
    }
    values.update(overrides)
    return MarketEventResolutionDependencyConfig(**values)


def _dependency(
    condition_id: str,
    *,
    upstream_event_key: str = "fed-rate-decision-2026-07",
    authority_key: str = "fomc_statement",
    authority_resolved: bool = False,
    evidence_chain_keys: tuple[str, ...] = ("calendar", "official_statement"),
    upstream_resolved_at: datetime | None = None,
    dependent_last_checked_at: datetime | None = None,
    evidence_references: tuple[str, ...] = ("https://secret.example/token=abc",),
) -> MarketEventResolutionDependencyInput:
    return MarketEventResolutionDependencyInput(
        dependent_condition_id=condition_id,
        upstream_event_key=upstream_event_key,
        authority_key=authority_key,
        authority_resolved=authority_resolved,
        evidence_chain_keys=evidence_chain_keys,
        upstream_resolved_at=upstream_resolved_at,
        dependent_last_checked_at=dependent_last_checked_at,
        evidence_references=evidence_references,
    )


def test_digest_summarizes_dependencies_without_sensitive_market_references():
    stale_resolved = _dependency(
        "0xccc",
        upstream_resolved_at=GENERATED_AT - timedelta(hours=3),
        dependent_last_checked_at=GENERATED_AT - timedelta(hours=1),
        authority_resolved=True,
    )
    unresolved_missing_evidence = _dependency(
        "0xaaa",
        authority_key="county_election_board",
        evidence_chain_keys=("official_results",),
    )
    fresh_resolved = _dependency(
        "0xbbb",
        upstream_event_key="jobs-report-2026-07",
        authority_key="bls_release",
        authority_resolved=True,
        upstream_resolved_at=GENERATED_AT - timedelta(minutes=30),
    )

    report = build_market_event_resolution_dependency_digest(
        (stale_resolved, unresolved_missing_evidence, fresh_resolved),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, MarketEventResolutionDependencyReport)
    assert report.generated_at == GENERATED_AT
    assert report.dependent_condition_count == Decimal("3")
    assert report.upstream_event_count == Decimal("2")
    assert report.unresolved_authority_count == Decimal("1")
    assert report.shared_evidence_chain_gap_count == Decimal("1")
    assert report.lag_pressure_count == Decimal("1")
    assert report.max_lag_seconds == Decimal("10800.000000")
    assert report.mean_lag_seconds == Decimal("3600.000000")
    assert report.unresolved_authority_mappings == (
        ("fed-rate-decision-2026-07", ("county_election_board",)),
    )
    assert report.dependency_rows == (
        (
            "fed-rate-decision-2026-07",
            "county_election_board",
            Decimal("1"),
            Decimal("1"),
            Decimal("0.000000"),
            ("0xaaa",),
        ),
        (
            "fed-rate-decision-2026-07",
            "fomc_statement",
            Decimal("1"),
            Decimal("0"),
            Decimal("10800.000000"),
            ("0xccc",),
        ),
        (
            "jobs-report-2026-07",
            "bls_release",
            Decimal("1"),
            Decimal("0"),
            Decimal("1800.000000"),
            ("0xbbb",),
        ),
    )
    assert report.status == "blocked"
    assert report.reason_codes == (
        "lag_pressure_blocking",
        "shared_evidence_chain_gap",
        "unresolved_authority_mapping",
    )
    assert report.redacted_evidence_references == (
        ("0xaaa", ("<redacted>",)),
        ("0xbbb", ("<redacted>",)),
        ("0xccc", ("<redacted>",)),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    public_field_names = {field.name for field in fields(report)}
    assert "market_slug" not in public_field_names
    assert "question" not in public_field_names
    assert "url" not in public_field_names
    assert all(
        "<redacted>" in refs
        for _condition_id, refs in report.redacted_evidence_references
    )


def test_digest_payload_is_research_report_only_and_redacted() -> None:
    report = build_market_event_resolution_dependency_digest(
        (
            _dependency(
                "0xaaa",
                authority_resolved=False,
                evidence_chain_keys=("official_results",),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    payload = market_event_resolution_dependency_digest_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["reason_codes"] == [
        "shared_evidence_chain_gap",
        "unresolved_authority_mapping",
    ]
    assert payload["dependent_condition_count"] == "1"
    assert payload["shared_evidence_chain_gap_count"] == "1"
    assert payload["redacted_evidence_references"] == [["0xaaa", ["<redacted>"]]]
    assert len(payload["derived_validation_digest"]) == 64
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    _assert_no_public_numeric_scalars(payload)
    payload_text = repr(payload).lower()
    assert "token=abc" not in payload_text
    assert "https://secret.example" not in payload_text
    assert "live" not in payload_text
    assert "execute" not in payload_text


def test_digest_uses_tamper_evident_derived_validation_digest() -> None:
    report = build_market_event_resolution_dependency_digest(
        (
            _dependency(
                "0xaaa",
                authority_resolved=True,
                upstream_resolved_at=GENERATED_AT - timedelta(hours=1),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert len(report.derived_validation_digest) == 64
    assert all(
        character in "0123456789abcdef"
        for character in report.derived_validation_digest
    )

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, max_lag_seconds=Decimal("0.000000"))


def test_digest_validation_digest_delimits_nested_public_payload_values() -> None:
    report = build_market_event_resolution_dependency_digest(
        (
            _dependency(
                "condition-a",
                upstream_event_key="event-a",
                authority_key="authority-b",
                authority_resolved=True,
                evidence_chain_keys=("alpha", "beta"),
                evidence_references=(),
            ),
            _dependency(
                "condition-b",
                upstream_event_key="event-b",
                authority_key="authority-c",
                authority_resolved=True,
                evidence_chain_keys=("alpha", "beta"),
                evidence_references=(),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    payload = market_event_resolution_dependency_digest_payload(report)
    tampered = dict(payload)
    tampered["redacted_evidence_references"] = [
        ["condition-a,[]],[condition-b", []],
    ]

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        market_event_resolution_dependency_digest_payload(tampered)


def test_digest_public_payload_revalidates_decimal_strings_and_unsafe_surface() -> None:
    payload = market_event_resolution_dependency_digest_payload(
        build_market_event_resolution_dependency_digest(
            (_dependency("0xaaa", authority_resolved=True),),
            config=_config(),
            generated_at=GENERATED_AT,
        ),
    )

    assert market_event_resolution_dependency_digest_payload(payload) == payload

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        market_event_resolution_dependency_digest_payload(missing_digest)

    decimal_not_string = dict(payload)
    decimal_not_string["dependent_condition_count"] = Decimal("1")
    with pytest.raises(ValueError, match="Decimal-derived string"):
        market_event_resolution_dependency_digest_payload(decimal_not_string)

    tampered = dict(payload)
    tampered["status"] = "blocked"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        market_event_resolution_dependency_digest_payload(tampered)

    unsafe_keys = (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_client",
        "database_url",
        "persist_path",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            market_event_resolution_dependency_digest_payload(unsafe_payload)

    unsafe_values = (
        "live mode configured",
        "auth token configured",
        "wallet transfer configured",
        "submit order configured",
        "network request configured",
        "database writer configured",
        "persist report configured",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_payload["reason_codes"] = [unsafe_value]
        with pytest.raises(ValueError, match="unsafe"):
            market_event_resolution_dependency_digest_payload(unsafe_payload)


def test_digest_passes_with_no_dependencies_and_has_deterministic_reason_code():
    report = build_market_event_resolution_dependency_digest(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.dependent_condition_count == Decimal("0")
    assert report.upstream_event_count == Decimal("0")
    assert report.unresolved_authority_count == Decimal("0")
    assert report.shared_evidence_chain_gap_count == Decimal("0")
    assert report.lag_pressure_count == Decimal("0")
    assert report.max_lag_seconds == Decimal("0.000000")
    assert report.mean_lag_seconds == Decimal("0.000000")
    assert report.unresolved_authority_mappings == ()
    assert report.dependency_rows == ()
    assert report.status == "pass"
    assert report.reason_codes == ("market_event_resolution_dependency_digest_passed",)


def test_digest_rejects_float_decimal_subclasses_and_false_safety_flags():
    good_input = _dependency("0xaaa")
    report = build_market_event_resolution_dependency_digest(
        (good_input,),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.dependent_condition_count = Decimal("2")
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="lag_warning_seconds"):
        _config(lag_warning_seconds=3600.0)
    with pytest.raises(ValueError, match="lag_blocking_seconds"):
        _config(lag_blocking_seconds=_DecimalSubclass("7200"))
    with pytest.raises(ValueError, match="generated_at"):
        build_market_event_resolution_dependency_digest(
            (good_input,),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_event_resolution_dependency_digest(
            (good_input,),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_event_resolution_dependency_digest(
            (good_input,),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 7, 2, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="evidence_references"):
        replace(good_input, evidence_references=("plain-reference",))


def test_digest_validates_exact_public_types_and_input_sorting():
    good_input = _dependency("0xaaa")

    with pytest.raises(TypeError):

        class _BadConfig(MarketEventResolutionDependencyConfig):
            pass

    with pytest.raises(TypeError):

        class _BadInput(MarketEventResolutionDependencyInput):
            pass

    with pytest.raises(TypeError):

        class _BadReport(MarketEventResolutionDependencyReport):
            pass

    with pytest.raises(ValueError, match="dependencies"):
        build_market_event_resolution_dependency_digest(
            [good_input],
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="condition_id"):
        replace(good_input, dependent_condition_id=" not-canonical ")
    with pytest.raises(ValueError, match="authority_resolved"):
        replace(good_input, authority_resolved=1)


def test_module_is_readonly_report_scope_without_live_io_surface() -> None:
    source = inspect.getsource(digest_module)
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
        "connect",
        "fetch",
        "request",
        "submit",
        "cancel",
        "trade",
    }
    forbidden_attr_fragments = (
        "broker",
        "client",
        "connection",
        "cursor",
        "session",
    )

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = node.names if isinstance(node, ast.Import) else [node]
            for alias in names:
                root = (
                    alias.name
                    if isinstance(node, ast.Import)
                    else (node.module or "")
                ).split(".")[0]
                assert root not in forbidden_import_roots
        if isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            if isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
        if isinstance(node, ast.Attribute):
            assert not any(
                fragment in node.attr.lower()
                for fragment in forbidden_attr_fragments
            )
