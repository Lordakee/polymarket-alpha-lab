from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_authority_scrapling_memory_quorum_report.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_authority_scrapling_memory_quorum_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": (
            "research-source-authority-scrapling-memory-quorum-report-v0"
        ),
        "min_pass_score": d("0.750000"),
        "min_watch_score": d("0.500000"),
        "min_pass_family_count": d("2"),
        "min_pass_quorum_weight": d("2.000000"),
        "max_stale_age_seconds": d("604800.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityScraplingMemoryQuorumConfig(**values)


def finding(**overrides: object):
    module = api()
    values = {
        "private_subject_ref": "candidate:raw-polymarket-question",
        "private_locator_ref": "https://example.test/raw/source?token=hidden",
        "family_ref": "official-release",
        "observed_at": GENERATED_AT - timedelta(hours=1),
        "authority_score": d("0.900000"),
        "support_weight": d("1.000000"),
        "conflict_weight": d("0.000000"),
    }
    values.update(overrides)
    return module.ResearchSourceAuthorityScraplingMemoryQuorumFinding(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_source_authority_scrapling_memory_quorum_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def public_payload(report_or_payload: object):
    module = api()
    return module.research_source_authority_scrapling_memory_quorum_report_payload(
        report_or_payload,
    )


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    resigned = dict(payload)
    resigned.pop("derived_validation_digest", None)
    encoded = json.dumps(resigned, sort_keys=True, separators=(",", ":")).encode()
    resigned["derived_validation_digest"] = hashlib.sha256(encoded).hexdigest()
    return resigned


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float) or type(value) is int:
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for item in value.values():
            assert_public_numeric_values_are_decimal(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)


def test_quorum_report_sorts_redacts_and_summarizes_statuses() -> None:
    report = build_report(
        finding(
            private_subject_ref="market-secret:block",
            private_locator_ref="raw://internal/table/a",
            family_ref="forum",
            observed_at=GENERATED_AT - timedelta(days=10),
            authority_score=d("0.300000"),
            support_weight=d("1.000000"),
        ),
        finding(
            private_subject_ref="market-secret:pass",
            private_locator_ref="postgres://hidden-dsn",
            family_ref="official",
            authority_score=d("0.900000"),
            support_weight=d("1.000000"),
        ),
        finding(
            private_subject_ref="market-secret:pass",
            private_locator_ref="token:private-transcript",
            family_ref="analysis",
            authority_score=d("0.800000"),
            support_weight=d("1.000000"),
        ),
        finding(
            private_subject_ref="market-secret:watch",
            private_locator_ref="raw-text:internal-note",
            family_ref="official",
            authority_score=d("0.550000"),
            support_weight=d("1.000000"),
        ),
    )

    assert report.report_status == "block"
    assert report.memory_count == d("4")
    assert report.subject_count == d("3")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("1")
    assert report.average_score == d("0.566667")
    assert tuple(row.row_status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.finding_count for row in report.rows) == (d("1"), d("1"), d("2"))
    assert report.reason_codes == (
        "block_present",
        "pass_present",
        "watch_present",
    )

    blocked, watched, passed = report.rows
    assert blocked.latest_age_seconds == d("864000.000000")
    assert blocked.reason_codes == (
        "stale_memory",
        "below_watch_score",
        "quorum_block",
    )
    assert watched.weighted_score == d("0.550000")
    assert watched.reason_codes == (
        "insufficient_family_quorum",
        "insufficient_weight_quorum",
        "watch_score",
        "quorum_watch",
    )
    assert passed.family_count == d("2")
    assert passed.weighted_score == d("0.850000")
    assert passed.reason_codes == ("pass_score", "quorum_pass")


def test_payload_is_deterministic_digest_validated_and_redacted() -> None:
    left = build_report(
        finding(private_subject_ref="private-candidate-a", family_ref="official"),
        finding(private_subject_ref="private-candidate-a", family_ref="analysis"),
    )
    right = build_report(
        finding(private_subject_ref="private-candidate-a", family_ref="analysis"),
        finding(private_subject_ref="private-candidate-a", family_ref="official"),
    )

    left_payload = public_payload(left)
    right_payload = public_payload(right)

    assert left_payload == right_payload
    assert left_payload["paper_only"] is True
    assert left_payload["report_only"] is True
    assert left_payload["readonly"] is True
    assert left_payload["memory_count"] == "2"
    assert left_payload["rows"][0]["weighted_score"] == "0.900000"
    assert isinstance(left_payload["derived_validation_digest"], str)
    assert len(left_payload["derived_validation_digest"]) == 64
    assert_no_float_or_int_values(left_payload)

    serialized = repr(left_payload)
    for raw_fragment in (
        "private-candidate-a",
        "https://example.test",
        "token=hidden",
        "postgres://hidden-dsn",
        "raw-text",
        "internal/table",
    ):
        assert raw_fragment not in serialized

    tampered = dict(left_payload)
    tampered["pass_count"] = "9"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        public_payload(tampered)


def test_locator_digest_uses_unambiguous_canonical_input() -> None:
    left = build_report(
        finding(private_locator_ref="a|a"),
    )
    right = build_report(
        finding(private_locator_ref="a"),
        finding(private_locator_ref="a", family_ref="analysis"),
    )

    assert left.rows[0].locator_digest != right.rows[0].locator_digest


@pytest.mark.parametrize(
    "mutate",
    (
        lambda payload: payload.__setitem__("extra", "safe"),
        lambda payload: payload.__setitem__("memory_count", "02"),
        lambda payload: payload.__setitem__("memory_count", "1.0"),
        lambda payload: payload.__setitem__("rows", {}),
        lambda payload: payload["rows"][0].__setitem__("extra", "safe"),
    ),
)
def test_public_payload_rejects_self_signed_schema_mutations(mutate) -> None:
    payload = public_payload(build_report(finding()))
    mutate(payload)

    with pytest.raises(ValueError):
        public_payload(resign_payload(payload))


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    sample_config = config()
    sample_finding = finding()
    sample_report = build_report(sample_finding)
    sample_row = sample_report.rows[0]

    for item in (sample_config, sample_finding, sample_row, sample_report):
        assert is_dataclass(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        finding(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        build_report(finding(readonly=False))


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("authority_score", Decimal("1.000001"), "authority_score"),
        ("authority_score", 1, "authority_score must be a Decimal"),
        ("support_weight", d("-0.000001"), "support_weight"),
        ("conflict_weight", d("-0.000001"), "conflict_weight"),
    ),
)
def test_validation_rejects_non_decimal_and_out_of_range_finding_inputs(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        finding(**{field_name: bad_value})


def test_report_rejects_unsupported_status_and_digest_tampering() -> None:
    module = api()
    report = build_report(finding())
    row_values = {field.name: getattr(report.rows[0], field.name) for field in fields(report.rows[0])}
    row_values["row_status"] = "ready"

    with pytest.raises(ValueError, match="row_status"):
        module.ResearchSourceAuthorityScraplingMemoryQuorumRow(**row_values)

    report_values = {field.name: getattr(report, field.name) for field in fields(report)}
    report_values["derived_validation_digest"] = "f" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.ResearchSourceAuthorityScraplingMemoryQuorumReport(**report_values)


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("memory_count", d("3"), "memory_count"),
        ("average_score", d("0.100000"), "average_score"),
        ("reason_codes", ("pass_present",), "reason_codes"),
        (
            "rows",
            lambda report: tuple(reversed(report.rows)),
            "rows",
        ),
    ),
)
def test_direct_report_validation_rejects_contradictory_or_unsorted_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    module = api()
    report = build_report(
        finding(private_subject_ref="private-subject-a"),
        finding(
            private_subject_ref="private-subject-b",
            authority_score=d("0.600000"),
        ),
    )
    report_values = {field.name: getattr(report, field.name) for field in fields(report)}
    report_values["derived_validation_digest"] = ""
    report_values[field_name] = bad_value(report) if callable(bad_value) else bad_value

    with pytest.raises(ValueError, match=message):
        module.ResearchSourceAuthorityScraplingMemoryQuorumReport(**report_values)


@pytest.mark.parametrize(
    "unsafe_field",
    (
        "candidate_id",
        "market_id",
        "source_url",
        "raw_text",
        "dsn",
        "table_name",
        "token",
        "wallet_id",
        "order_id",
        "trade_id",
    ),
)
def test_public_payload_rejects_self_signed_raw_identifier_leakage(
    unsafe_field: str,
) -> None:
    payload = public_payload(build_report(finding()))
    payload[unsafe_field] = "private"

    with pytest.raises(ValueError):
        public_payload(resign_payload(payload))


def test_public_payload_rejects_flag_downgrades() -> None:
    payload = public_payload(build_report(finding()))
    payload["report_only"] = False

    with pytest.raises(ValueError, match="report_only"):
        public_payload(resign_payload(payload))


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "auth-ref",
        "live trade",
        "sizing hint",
        "recommendation",
        "execution path",
        "buy order",
        "sell signal",
        "signature",
        "submit intent",
    ),
)
def test_public_payload_rejects_self_signed_execution_surface_values(
    unsafe_value: str,
) -> None:
    payload = public_payload(build_report(finding()))
    payload["rows"][0]["reason_codes"] = [unsafe_value]

    with pytest.raises(ValueError):
        public_payload(resign_payload(payload))


def test_module_scope_has_no_db_network_wallet_order_or_trading_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                call_names.append(func.id)
            elif isinstance(func, ast.Attribute):
                call_names.append(func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_imports = {
        "os",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
        "http",
        "requests",
    }
    assert not (set(imports) & forbidden_imports)

    forbidden_calls = {
        "connect",
        "execute",
        "request",
        "send",
        "post",
        "get",
        "open",
    }
    assert not (set(call_names) & forbidden_calls)
    assert "total_seconds" not in attribute_names

    forbidden_names = {
        "authenticate",
        "authorize",
        "buy",
        "cancel",
        "connect",
        "execute",
        "insert",
        "persist",
        "recommend",
        "sell",
        "sign",
        "size_position",
        "submit",
        "trade",
        "write",
    }
    assert not (set(call_names) & forbidden_names)
    assert not (set(attribute_names) & forbidden_names)
