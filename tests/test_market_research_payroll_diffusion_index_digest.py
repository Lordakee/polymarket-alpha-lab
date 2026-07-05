from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_research_payroll_diffusion_index_digest"
GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoOffsetTimeZone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def test_payroll_diffusion_index_digest_public_api_exists() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_payroll_diffusion_index_digest_reduces_reports_deterministically() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
            input_row(
                digest,
                "research.payroll.diffusion.services",
                condition_id="condition_services",
                segment_key="services",
                segment_name="private-services",
                diffusion_index=Decimal("44.200000"),
                previous_diffusion_index=Decimal("51.400000"),
                consensus_diffusion_index=Decimal("52.000000"),
                payroll_change=Decimal("-12000.000000"),
                source_count=Decimal("1.000000"),
                observed_at=GENERATED_AT - timedelta(hours=5),
                acknowledged_at=None,
                source_reference="https://bls.example/payroll?token=secret-123",
                input_config_version="payroll-diffusion-v1",
            ),
            input_row(
                digest,
                "research.payroll.diffusion.manufacturing",
                condition_id="condition_manufacturing",
                segment_key="manufacturing",
                segment_name="manufacturing",
                diffusion_index=Decimal("49.500000"),
                previous_diffusion_index=Decimal("50.000000"),
                consensus_diffusion_index=Decimal("50.500000"),
                payroll_change=Decimal("8000.000000"),
                source_count=Decimal("2.000000"),
                observed_at=GENERATED_AT - timedelta(hours=1, minutes=30),
                acknowledged_at=GENERATED_AT - timedelta(minutes=70),
                source_reference="private-payroll-source",
                input_config_version="payroll-diffusion-v1",
            ),
            input_row(
                digest,
                "research.payroll.diffusion.construction",
                condition_id="condition_construction",
                segment_key="construction",
                segment_name="construction",
                diffusion_index=Decimal("55.000000"),
                previous_diffusion_index=Decimal("52.000000"),
                consensus_diffusion_index=Decimal("54.500000"),
                payroll_change=Decimal("18000.000000"),
                source_count=Decimal("3.000000"),
                observed_at=GENERATED_AT - timedelta(minutes=30),
                acknowledged_at=GENERATED_AT - timedelta(minutes=20),
                source_reference="public-payroll-table",
                input_config_version="payroll-diffusion-v0",
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        digest.DEFAULT_MARKET_RESEARCH_PAYROLL_DIFFUSION_INDEX_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_payroll_diffusion_index_digest"
    )
    assert summary.segment_count == Decimal("3.000000")
    assert summary.ready_segment_count == Decimal("1.000000")
    assert summary.watch_segment_count == Decimal("1.000000")
    assert summary.blocked_segment_count == Decimal("1.000000")
    assert summary.contraction_segment_count == Decimal("2.000000")
    assert summary.deep_contraction_segment_count == Decimal("1.000000")
    assert summary.negative_payroll_segment_count == Decimal("1.000000")
    assert summary.consensus_miss_count == Decimal("2.000000")
    assert summary.thin_source_count == Decimal("1.000000")
    assert summary.stale_report_count == Decimal("2.000000")
    assert summary.missing_acknowledgement_count == Decimal("1.000000")
    assert summary.slow_acknowledgement_count == Decimal("1.000000")
    assert summary.average_diffusion_index == Decimal("49.566667")
    assert summary.average_consensus_gap == Decimal("-2.766667")
    assert summary.contraction_ratio == Decimal("0.666667")
    assert summary.max_report_age_seconds == Decimal("18000.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.segment_key, row.research_key) for row in summary.rows) == (
        ("services", "research.payroll.diffusion.services"),
        ("manufacturing", "research.payroll.diffusion.manufacturing"),
        ("construction", "research.payroll.diffusion.construction"),
    )

    services = summary.rows[0]
    assert services.segment_status == "blocked"
    assert services.report_age_seconds == Decimal("18000.000000")
    assert services.acknowledgement_lag_seconds is None
    assert services.diffusion_index_change == Decimal("-7.200000")
    assert services.consensus_gap == Decimal("-7.800000")
    assert services.redacted_source_reference == redacted(
        "https://bls.example/payroll?token=secret-123",
    )
    assert services.reason_codes == (
        "market_research_payroll_diffusion_index_digest_contraction",
        "market_research_payroll_diffusion_index_digest_consensus_miss",
        "market_research_payroll_diffusion_index_digest_deep_contraction",
        "market_research_payroll_diffusion_index_digest_missing_acknowledgement",
        "market_research_payroll_diffusion_index_digest_negative_payroll",
        "market_research_payroll_diffusion_index_digest_stale_report",
        "market_research_payroll_diffusion_index_digest_thin_sources",
    )

    manufacturing = summary.rows[1]
    assert manufacturing.segment_status == "watch"
    assert manufacturing.report_age_seconds == Decimal("5400.000000")
    assert manufacturing.acknowledgement_lag_seconds == Decimal("1200.000000")
    assert manufacturing.diffusion_index_change == Decimal("-0.500000")
    assert manufacturing.consensus_gap == Decimal("-1.000000")
    assert manufacturing.reason_codes == (
        "market_research_payroll_diffusion_index_digest_contraction",
        "market_research_payroll_diffusion_index_digest_consensus_miss",
        "market_research_payroll_diffusion_index_digest_slow_acknowledgement",
        "market_research_payroll_diffusion_index_digest_stale_report",
    )

    construction = summary.rows[2]
    assert construction.segment_status == "ready"
    assert construction.report_age_seconds == Decimal("1800.000000")
    assert construction.acknowledgement_lag_seconds == Decimal("600.000000")
    assert construction.diffusion_index_change == Decimal("3.000000")
    assert construction.consensus_gap == Decimal("0.500000")
    assert construction.reason_codes == (
        "market_research_payroll_diffusion_index_digest_ready",
    )

    assert summary.reason_code_counts == (
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
            reason_code="market_research_payroll_diffusion_index_digest_contraction",
            count=Decimal("2.000000"),
            segment_ratio=Decimal("0.666667"),
        ),
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
            reason_code="market_research_payroll_diffusion_index_digest_consensus_miss",
            count=Decimal("2.000000"),
            segment_ratio=Decimal("0.666667"),
        ),
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
            reason_code="market_research_payroll_diffusion_index_digest_stale_report",
            count=Decimal("2.000000"),
            segment_ratio=Decimal("0.666667"),
        ),
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
            reason_code="market_research_payroll_diffusion_index_digest_deep_contraction",
            count=Decimal("1.000000"),
            segment_ratio=Decimal("0.333333"),
        ),
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
            reason_code="market_research_payroll_diffusion_index_digest_missing_acknowledgement",
            count=Decimal("1.000000"),
            segment_ratio=Decimal("0.333333"),
        ),
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
            reason_code="market_research_payroll_diffusion_index_digest_negative_payroll",
            count=Decimal("1.000000"),
            segment_ratio=Decimal("0.333333"),
        ),
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
            reason_code="market_research_payroll_diffusion_index_digest_ready",
            count=Decimal("1.000000"),
            segment_ratio=Decimal("0.333333"),
        ),
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
            reason_code="market_research_payroll_diffusion_index_digest_slow_acknowledgement",
            count=Decimal("1.000000"),
            segment_ratio=Decimal("0.333333"),
        ),
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
            reason_code="market_research_payroll_diffusion_index_digest_thin_sources",
            count=Decimal("1.000000"),
            segment_ratio=Decimal("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(row.reason_code for row in summary.reason_code_counts)


def test_empty_input_returns_no_inputs_report() -> None:
    digest = digest_module()

    summary = report(digest, ())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_payroll_diffusion_index_digest"
    )
    assert summary.segment_count == ZERO
    assert summary.contraction_ratio == ZERO
    assert summary.average_diffusion_index is None
    assert summary.average_consensus_gap is None
    assert summary.max_report_age_seconds is None
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
            reason_code="market_research_payroll_diffusion_index_digest_no_inputs",
            count=Decimal("1.000000"),
            segment_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_payroll_diffusion_index_digest_no_inputs",
    )


def test_manual_public_records_must_match_derived_digest_state() -> None:
    digest = digest_module()
    summary = report(digest, (input_row(digest),))
    row = summary.rows[0]
    mixed_summary = report(
        digest,
        (
            input_row(
                digest,
                "research.payroll.diffusion.services",
                condition_id="condition_services",
                segment_key="services",
                diffusion_index=Decimal("44.200000"),
                previous_diffusion_index=Decimal("51.400000"),
                consensus_diffusion_index=Decimal("52.000000"),
                payroll_change=Decimal("-12000.000000"),
                source_count=Decimal("1.000000"),
                observed_at=GENERATED_AT - timedelta(hours=5),
                acknowledged_at=None,
            ),
            input_row(
                digest,
                "research.payroll.diffusion.construction",
                condition_id="condition_construction",
                segment_key="construction",
            ),
        ),
    )
    blocked_row = mixed_summary.rows[0]

    with pytest.raises(ValueError, match="diffusion_index_change"):
        replace(row, diffusion_index_change=Decimal("2.000000"))

    with pytest.raises(ValueError, match="consensus_gap"):
        replace(row, consensus_gap=Decimal("1.000000"))

    with pytest.raises(ValueError, match="segment_status"):
        replace(row, segment_status="blocked")

    with pytest.raises(ValueError, match="report_age_seconds"):
        replace(row, report_age_seconds=Decimal("-1.000000"))

    with pytest.raises(ValueError, match="acknowledgement_lag_seconds"):
        replace(row, acknowledgement_lag_seconds=Decimal("-1.000000"))

    with pytest.raises(ValueError, match="source_count"):
        replace(row, source_count=Decimal("1.500000"))

    with pytest.raises(ValueError, match="segment_count"):
        replace(summary, segment_count=Decimal("2.000000"))

    with pytest.raises(ValueError, match="digest_status"):
        replace(summary, digest_status="blocked")

    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(
            summary,
            recommended_next_step="watch_report_only_market_research_payroll_diffusion_index_digest",
        )

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            summary,
            reason_codes=("market_research_payroll_diffusion_index_digest_no_inputs",),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(blocked_row, reason_codes=tuple(reversed(blocked_row.reason_codes)))
    with pytest.raises(ValueError, match="rows"):
        replace(mixed_summary, rows=tuple(reversed(mixed_summary.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            mixed_summary,
            reason_code_counts=tuple(reversed(mixed_summary.reason_code_counts)),
        )

    bad_reason_count = digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount(
        reason_code="market_research_payroll_diffusion_index_digest_ready",
        count=Decimal("2.000000"),
        segment_ratio=Decimal("1.000000"),
    )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=(bad_reason_count,))


def test_dataclasses_are_frozen_and_hard_flags_are_enforced() -> None:
    digest = digest_module()
    row = input_row(digest)
    summary = report(digest, (row,))

    with pytest.raises(FrozenInstanceError):
        row.source_count = Decimal("2.000000")  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "ready"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        input_row(digest, paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        config(digest, report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)

    reason_count = summary.reason_code_counts[0]
    for factory in (
        config,
        input_row,
        lambda module, **overrides: replace(summary.rows[0], **overrides),
        lambda module, **overrides: replace(reason_count, **overrides),
        lambda module, **overrides: replace(summary, **overrides),
    ):
        for flag_name in ("paper_only", "report_only", "readonly"):
            with pytest.raises(ValueError, match=flag_name):
                factory(digest, **{flag_name: False})


def test_public_numeric_count_and_ratio_fields_are_decimal_only() -> None:
    digest = digest_module()

    for type_ in (
        digest.MarketResearchPayrollDiffusionIndexDigestConfig,
        digest.MarketResearchPayrollDiffusionIndexDigestInputRow,
        digest.MarketResearchPayrollDiffusionIndexDigestRow,
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount,
        digest.MarketResearchPayrollDiffusionIndexDigestReport,
    ):
        assert is_dataclass(type_)
        assert all("float" not in str(field.type) for field in fields(type_))
        assert all("int" not in str(field.type) and field.type is not int for field in fields(type_))

    assert {
        field.name
        for field in fields(digest.MarketResearchPayrollDiffusionIndexDigestReport)
        if field.name.endswith("_count")
    } <= decimal_public_field_names(digest.MarketResearchPayrollDiffusionIndexDigestReport)
    assert "contraction_ratio" in decimal_public_field_names(
        digest.MarketResearchPayrollDiffusionIndexDigestReport,
    )
    assert "segment_ratio" in decimal_public_field_names(
        digest.MarketResearchPayrollDiffusionIndexDigestReasonCodeCount,
    )

    summary = report(digest, (input_row(digest),))
    public_payload = asdict(summary)
    assert_no_floats(public_payload)
    assert all(
        type(value) is Decimal or value is None
        for key, value in public_payload.items()
        if key.endswith("_count") or key.endswith("_ratio")
    )


def test_datetime_validation_and_utc_normalization() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="observed_at"):
        input_row(digest, observed_at=datetime(2026, 7, 3, 11, 0))

    with pytest.raises(ValueError, match="generated_at"):
        report(digest, (input_row(digest),), generated_at=datetime(2026, 7, 3, 12, 0))

    invalid_tzinfo = _NoOffsetTimeZone()
    with pytest.raises(ValueError, match="observed_at"):
        input_row(digest, observed_at=datetime(2026, 7, 3, 11, 0, tzinfo=invalid_tzinfo))

    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(
            digest,
            acknowledged_at=datetime(2026, 7, 3, 11, 30, tzinfo=invalid_tzinfo),
        )

    with pytest.raises(ValueError, match="generated_at"):
        report(
            digest,
            (input_row(digest),),
            generated_at=datetime(2026, 7, 3, 12, 0, tzinfo=invalid_tzinfo),
        )

    with pytest.raises(ValueError, match="acknowledged_at"):
        input_row(
            digest,
            observed_at=GENERATED_AT - timedelta(minutes=10),
            acknowledged_at=GENERATED_AT - timedelta(minutes=11),
        )

    with pytest.raises(ValueError, match="future"):
        report(
            digest,
            (
                input_row(
                    digest,
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                    acknowledged_at=GENERATED_AT + timedelta(seconds=2),
                ),
            ),
        )

    shifted = report(
        digest,
        (
            input_row(
                digest,
                observed_at=datetime(2026, 7, 3, 7, 30, tzinfo=timezone(timedelta(hours=-4))),
                acknowledged_at=datetime(2026, 7, 3, 7, 50, tzinfo=timezone(timedelta(hours=-4))),
            ),
        ),
    )
    assert shifted.rows[0].observed_at == datetime(2026, 7, 3, 11, 30, tzinfo=UTC)
    assert shifted.rows[0].acknowledged_at == datetime(2026, 7, 3, 11, 50, tzinfo=UTC)


def test_payload_uses_decimal_strings_iso_datetimes_and_no_floats() -> None:
    digest = digest_module()

    summary = report(
        digest,
        (
                input_row(
                    digest,
                    observed_at=datetime(2026, 7, 3, 11, 59, 59, 500000, tzinfo=UTC),
                    acknowledged_at=GENERATED_AT,
                ),
            ),
        )
    payload = digest.market_research_payroll_diffusion_index_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["segment_count"] == "1.000000"
    assert payload["contraction_ratio"] == "0.000000"
    assert payload["rows"][0]["observed_at"] == "2026-07-03T11:59:59.500000+00:00"
    assert payload["rows"][0]["report_age_seconds"] == "0.500000"
    assert_no_floats(payload)


def test_rejects_subclasses_and_invalid_decimal_public_inputs() -> None:
    digest = digest_module()

    with pytest.raises(TypeError, match="does not support subclassing"):
        type(
            "ConfigSubclass",
            (digest.MarketResearchPayrollDiffusionIndexDigestConfig,),
            {},
        )

    with pytest.raises(ValueError, match="source_count"):
        input_row(digest, source_count=1)

    with pytest.raises(ValueError, match="diffusion_index"):
        input_row(digest, diffusion_index=Decimal("NaN"))

    with pytest.raises(ValueError, match="research_key"):
        input_row(digest, research_key=_StringSubclass("research.payroll.diffusion"))

    with pytest.raises(ValueError, match="generated_at"):
        report(digest, (input_row(digest),), generated_at=_DateTimeSubclass(2026, 7, 3, tzinfo=UTC))

    with pytest.raises(ValueError, match="source_count"):
        input_row(digest, source_count=_DecimalSubclass("1.000000"))


def test_rejects_unsupported_versions_and_noncanonical_public_strings() -> None:
    digest = digest_module()

    with pytest.raises(ValueError, match="config_version"):
        config(digest, config_version="custom-payroll-diffusion-config")

    with pytest.raises(ValueError, match="research_key"):
        input_row(digest, research_key=" research.payroll.diffusion")

    with pytest.raises(ValueError, match="source_reference"):
        input_row(digest, source_reference="payroll-source ")


def test_module_is_pure_in_memory_report_only_and_contains_no_forbidden_primitives() -> None:
    source = Path("src/polymarket_alpha_lab/market_research_payroll_diffusion_index_digest.py").read_text()
    tree = ast.parse(source)

    forbidden_import_roots = {
        "asyncio",
        "http",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
        "websocket",
    }
    forbidden_call_names = {
        "connect",
        "delete",
        "open",
        "place_order",
        "post",
        "put",
        "read_text",
        "replace_order",
        "request",
        "submit",
        "write_text",
    }
    forbidden_fragments = {
        "auth",
        "cancel",
        "database",
        "db",
        "durable",
        "file",
        "live trading",
        "network",
        "order placement",
        "replace",
        "wallet",
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported_names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            assert all(
                name.split(".")[0] not in forbidden_import_roots
                for name in imported_names
            )
        if isinstance(node, ast.Call):
            called = call_name(node.func)
            assert called not in forbidden_call_names

    lowered = source.lower()
    assert all(fragment not in lowered for fragment in forbidden_fragments)


def digest_module() -> Any:
    return importlib.import_module(MODULE_NAME)


def config(digest: Any, **overrides: object) -> Any:
    values = {}
    values.update(overrides)
    return digest.MarketResearchPayrollDiffusionIndexDigestConfig(**values)


def input_row(digest: Any, research_key: str = "research.payroll.diffusion.default", **overrides: object) -> Any:
    values = {
        "research_key": research_key,
        "condition_id": "condition_default",
        "segment_key": "default-segment",
        "segment_name": "default-segment",
        "diffusion_index": Decimal("55.000000"),
        "previous_diffusion_index": Decimal("54.000000"),
        "consensus_diffusion_index": Decimal("53.000000"),
        "payroll_change": Decimal("10000.000000"),
        "source_count": Decimal("2.000000"),
        "observed_at": GENERATED_AT - timedelta(minutes=10),
        "acknowledged_at": GENERATED_AT - timedelta(minutes=5),
        "source_reference": "public-payroll-source",
        "input_config_version": "payroll-diffusion-v1",
    }
    values.update(overrides)
    return digest.MarketResearchPayrollDiffusionIndexDigestInputRow(**values)


def report(
    digest: Any,
    rows: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    cfg: Any | None = None,
) -> Any:
    return digest.build_market_research_payroll_diffusion_index_digest(
        rows,
        config=cfg or config(digest),
        generated_at=generated_at,
    )


def decimal_public_field_names(type_: type[Any]) -> set[str]:
    return {
        field.name
        for field in fields(type_)
        if "Decimal" in str(field.type) or field.type is Decimal
    }


def assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        raise AssertionError(f"float leaked: {value!r}")
    if isinstance(value, dict):
        for child in value.values():
            assert_no_floats(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            assert_no_floats(child)


def redacted(value: str) -> str:
    return "sha256:" + __import__("hashlib").sha256(value.encode("utf-8")).hexdigest()


def call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""
