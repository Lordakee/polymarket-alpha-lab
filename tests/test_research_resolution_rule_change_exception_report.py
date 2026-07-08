from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, dataclass, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_rule_change_exception_report import (
    DEFAULT_RESEARCH_RESOLUTION_RULE_CHANGE_EXCEPTION_REPORT_CONFIG_VERSION,
    ResearchResolutionRuleChangeExceptionConfig,
    ResearchResolutionRuleChangeExceptionInput,
    ResearchResolutionRuleChangeExceptionReasonCodeCount,
    ResearchResolutionRuleChangeExceptionReport,
    ResearchResolutionRuleChangeExceptionRow,
    build_research_resolution_rule_change_exception_report,
    research_resolution_rule_change_exception_report_payload,
    validate_research_resolution_rule_change_exception_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_resolution_rule_change_exception_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedExceptionShape:
    exception_group: str
    baseline_rule_version: Decimal
    observed_rule_version: Decimal
    official_source_freshness: Decimal
    unresolved_ambiguity_count: Decimal
    impacted_packet_count: Decimal
    manual_review_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionRuleChangeExceptionConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_RESOLUTION_RULE_CHANGE_EXCEPTION_REPORT_CONFIG_VERSION
        ),
        "rule_version_drift_watch_threshold": d("1.000000"),
        "rule_version_drift_block_threshold": d("3.000000"),
        "official_source_freshness_watch_threshold": d("0.800000"),
        "official_source_freshness_block_threshold": d("0.500000"),
        "unresolved_ambiguity_watch_threshold": d("1.000000"),
        "unresolved_ambiguity_block_threshold": d("3.000000"),
        "manual_review_urgency_watch_threshold": d("0.400000"),
        "manual_review_urgency_block_threshold": d("0.750000"),
        "impacted_packet_watch_threshold": d("5.000000"),
        "impacted_packet_block_threshold": d("20.000000"),
    }
    values.update(overrides)
    return ResearchResolutionRuleChangeExceptionConfig(**values)


def exception_item(
    exception_group: str = "rulebook-settlement",
    *,
    baseline_rule_version: Decimal = d("10.000000"),
    observed_rule_version: Decimal = d("10.000000"),
    official_source_freshness: Decimal = d("0.950000"),
    unresolved_ambiguity_count: Decimal = d("0.000000"),
    impacted_packet_count: Decimal = d("1.000000"),
    manual_review_urgency: Decimal = d("0.050000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchResolutionRuleChangeExceptionInput:
    return ResearchResolutionRuleChangeExceptionInput(
        exception_group=exception_group,
        baseline_rule_version=baseline_rule_version,
        observed_rule_version=observed_rule_version,
        official_source_freshness=official_source_freshness,
        unresolved_ambiguity_count=unresolved_ambiguity_count,
        impacted_packet_count=impacted_packet_count,
        manual_review_urgency=manual_review_urgency,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchResolutionRuleChangeExceptionConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionRuleChangeExceptionReport:
    return build_research_resolution_rule_change_exception_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_public_safe_pass_report_with_digest() -> None:
    exception_report = report(())

    assert type(exception_report) is ResearchResolutionRuleChangeExceptionReport
    assert exception_report.__dataclass_params__.frozen is True
    assert exception_report.generated_at == GENERATED_AT
    assert exception_report.config_version == (
        DEFAULT_RESEARCH_RESOLUTION_RULE_CHANGE_EXCEPTION_REPORT_CONFIG_VERSION
    )
    assert exception_report.exception_group_count == ZERO
    assert exception_report.impacted_packet_count == ZERO
    assert exception_report.rule_version_drift_exception_count == ZERO
    assert exception_report.stale_official_source_count == ZERO
    assert exception_report.unresolved_ambiguity_count == ZERO
    assert exception_report.manual_review_urgency_peak == ZERO
    assert exception_report.average_official_source_freshness is None
    assert exception_report.max_rule_version_drift == ZERO
    assert exception_report.pass_count == ZERO
    assert exception_report.watch_count == ZERO
    assert exception_report.block_count == ZERO
    assert exception_report.status == "pass"
    assert exception_report.reason_codes == ("no_rule_change_exceptions",)
    assert exception_report.reason_code_counts == (
        ResearchResolutionRuleChangeExceptionReasonCodeCount(
            reason_code="no_rule_change_exceptions",
            count=ONE,
        ),
    )
    assert exception_report.rows == ()
    assert len(exception_report.derived_validation_digest) == 64
    assert exception_report.paper_only is True
    assert exception_report.report_only is True
    assert exception_report.readonly is True


def test_rule_change_exceptions_aggregate_drift_freshness_ambiguity_and_urgency() -> None:
    exception_report = report(
        (
            exception_item(
                "settlement-policy",
                observed_rule_version=d("11.000000"),
                official_source_freshness=d("0.700000"),
                unresolved_ambiguity_count=d("1.000000"),
                impacted_packet_count=d("6.000000"),
                manual_review_urgency=d("0.450000"),
            ),
            exception_item(
                "oracle-adjudication",
                observed_rule_version=d("14.000000"),
                official_source_freshness=d("0.300000"),
                unresolved_ambiguity_count=d("4.000000"),
                impacted_packet_count=d("25.000000"),
                manual_review_urgency=d("0.850000"),
                reason_codes=("requires_policy_owner_review",),
            ),
            exception_item("baseline-controls"),
        ),
    )

    assert tuple(row.exception_group for row in exception_report.rows) == (
        "baseline-controls",
        "oracle-adjudication",
        "settlement-policy",
    )
    assert exception_report.status == "block"
    assert exception_report.exception_group_count == d("3.000000")
    assert exception_report.impacted_packet_count == d("32.000000")
    assert exception_report.rule_version_drift_exception_count == d("2.000000")
    assert exception_report.stale_official_source_count == d("2.000000")
    assert exception_report.unresolved_ambiguity_count == d("5.000000")
    assert exception_report.manual_review_urgency_peak == d("0.850000")
    assert exception_report.average_official_source_freshness == d("0.650000")
    assert exception_report.max_rule_version_drift == d("4.000000")
    assert exception_report.pass_count == d("1.000000")
    assert exception_report.watch_count == d("1.000000")
    assert exception_report.block_count == d("1.000000")

    pass_row, block_row, watch_row = exception_report.rows
    assert type(pass_row) is ResearchResolutionRuleChangeExceptionRow
    assert pass_row.status == "pass"
    assert pass_row.rule_version_drift == ZERO
    assert pass_row.reason_codes == ("resolution_rule_change_exception_pass",)
    assert watch_row.status == "watch"
    assert watch_row.rule_version_drift == d("1.000000")
    assert "rule_version_drift_watch" in watch_row.reason_codes
    assert "official_source_freshness_watch" in watch_row.reason_codes
    assert "unresolved_ambiguity_watch" in watch_row.reason_codes
    assert "manual_review_urgency_watch" in watch_row.reason_codes
    assert "impacted_packet_count_watch" in watch_row.reason_codes
    assert block_row.status == "block"
    assert block_row.rule_version_drift == d("4.000000")
    assert "rule_version_drift_block" in block_row.reason_codes
    assert "official_source_freshness_block" in block_row.reason_codes
    assert "unresolved_ambiguity_block" in block_row.reason_codes
    assert "manual_review_urgency_block" in block_row.reason_codes
    assert "impacted_packet_count_block" in block_row.reason_codes
    assert "input_requires_policy_owner_review" in block_row.reason_codes
    assert exception_report.reason_code_counts == tuple(
        sorted(exception_report.reason_code_counts, key=lambda item: item.reason_code),
    )


def test_payload_digest_is_deterministic_public_safe_and_decimal_string_only() -> None:
    rows = (
        SuppliedExceptionShape(
            exception_group="settlement-policy",
            baseline_rule_version=d("10.000000"),
            observed_rule_version=d("11.000000"),
            official_source_freshness=d("0.700000"),
            unresolved_ambiguity_count=d("1.000000"),
            impacted_packet_count=d("6.000000"),
            manual_review_urgency=d("0.450000"),
            reason_codes=("manual_policy_review_pending",),
        ),
        exception_item("baseline-controls"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_resolution_rule_change_exception_report_payload(first_report)
    second_payload = research_resolution_rule_change_exception_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["rule_version_drift"] == "0.000000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert validate_research_resolution_rule_change_exception_report_payload(first_payload)
    assert not any(type(value) in (float, int) for value in _walk_payload_values(first_payload))
    assert all(row["status"] in {"pass", "watch", "block"} for row in first_payload["rows"])
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "http",
            "source_url",
            "source_text",
            "source_ref",
            "source_identifier",
            "raw_source",
            "market_slug",
            "market_id",
            "condition_id",
            "question",
            "wallet",
            "order",
            "trade",
            "sizing",
            "recommendation",
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_and_public_leaks() -> None:
    with pytest.raises(ValueError, match="rule_version_drift_watch_threshold"):
        config(rule_version_drift_watch_threshold=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="official_source_freshness_block_threshold"):
        config(official_source_freshness_block_threshold=d("0.900000"))
    with pytest.raises(ValueError, match="manual_review_urgency_block_threshold"):
        config(manual_review_urgency_block_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="baseline_rule_version"):
        exception_item(baseline_rule_version=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="official_source_freshness"):
        exception_item(official_source_freshness=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="official_source_freshness"):
        exception_item(official_source_freshness=d("1.100000"))
    with pytest.raises(ValueError, match="impacted_packet_count"):
        exception_item(impacted_packet_count=d("1.500000"))
    with pytest.raises(ValueError, match="exception_group"):
        exception_item("market-0xabc")
    with pytest.raises(ValueError, match="exception_group"):
        exception_item("source-feed-primary")
    with pytest.raises(ValueError, match="paper_only"):
        replace(exception_item(), paper_only=False)
    with pytest.raises(ValueError, match="generated_at"):
        report((exception_item(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (exception_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )

    exception_report = report((exception_item(),))
    with pytest.raises(FrozenInstanceError):
        exception_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(exception_report, paper_only=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(exception_report, impacted_packet_count=d("99.000000"))

    payload = research_resolution_rule_change_exception_report_payload(exception_report)
    tampered_payload = dict(payload)
    tampered_payload["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_resolution_rule_change_exception_report_payload(tampered_payload)
    leaky_payload = dict(payload)
    leaky_payload["rows"] = tuple(payload["rows"]) + (
        {"exception_group": "https://example.invalid/raw-source"},
    )
    with pytest.raises(ValueError, match="unsafe public"):
        validate_research_resolution_rule_change_exception_report_payload(leaky_payload)

    for cls in (
        ResearchResolutionRuleChangeExceptionConfig,
        ResearchResolutionRuleChangeExceptionInput,
        ResearchResolutionRuleChangeExceptionRow,
        ResearchResolutionRuleChangeExceptionReport,
    ):
        public_field_names = {field.name for field in fields(cls)}
        for forbidden in ("market", "condition", "url", "raw", "identifier"):
            assert not any(forbidden in field_name.lower() for field_name in public_field_names)


def test_module_is_pure_readonly_report_scope_without_forbidden_surfaces() -> None:
    source = MODULE_PATH.read_text()
    tree = ast.parse(source)

    forbidden_import_roots = {
        "asyncio",
        "http",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.AsyncFunctionDef):
            assert False, f"unexpected async surface: {node.name}"
    assert not (imports & forbidden_import_roots)

    lowered = source.lower()
    for forbidden in (
        "private_key",
        "wallet",
        "auth",
        "order",
        "trade",
        "live_trading",
        "sizing",
        "recommendation",
        "database",
        "network",
    ):
        assert forbidden not in lowered


def _walk_payload_values(value: object) -> list[object]:
    if isinstance(value, dict):
        items: list[object] = []
        for key, item in value.items():
            items.append(key)
            items.extend(_walk_payload_values(item))
        return items
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_walk_payload_values(item))
        return items
    return [value]
