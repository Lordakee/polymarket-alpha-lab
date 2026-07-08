from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.research_resolution_outcome_evidence_gap_report"


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "watch_official_evidence_coverage_ratio": d("0.900000"),
        "block_official_evidence_coverage_ratio": d("0.700000"),
        "watch_independent_corroboration_ratio": d("0.800000"),
        "block_independent_corroboration_ratio": d("0.500000"),
        "watch_rule_ambiguity_ratio": d("0.150000"),
        "block_rule_ambiguity_ratio": d("0.300000"),
        "watch_stale_outcome_evidence_ratio": d("0.200000"),
        "block_stale_outcome_evidence_ratio": d("0.400000"),
        "watch_escalation_urgency_ratio": d("0.250000"),
        "block_escalation_urgency_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchResolutionOutcomeEvidenceGapReportConfig(**values)


def aggregate(outcome_group: str, **overrides: object) -> Any:
    module = api()
    values = {
        "outcome_group": outcome_group,
        "outcome_count": d("10.000000"),
        "official_evidence_count": d("10.000000"),
        "independently_corroborated_count": d("9.000000"),
        "rule_ambiguous_count": d("0.000000"),
        "stale_outcome_evidence_count": d("0.000000"),
        "escalation_due_count": d("0.000000"),
        "max_outcome_evidence_age_seconds": d("600.000000"),
    }
    values.update(overrides)
    return module.ResearchResolutionOutcomeEvidenceGapAggregate(**values)


def build_report(*values: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_resolution_outcome_evidence_gap_report(
        values,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def payload(report_value: Any | None = None) -> dict[str, object]:
    module = api()
    return module.research_resolution_outcome_evidence_gap_report_payload(
        report_value if report_value is not None else build_report(),
    )


def test_report_rolls_up_official_corroboration_ambiguity_stale_and_urgency_gaps() -> None:
    module = api()
    report = build_report(
        aggregate("official_final_results"),
        aggregate(
            "sports_settlement",
            outcome_count=d("8.000000"),
            official_evidence_count=d("7.000000"),
            independently_corroborated_count=d("5.000000"),
            rule_ambiguous_count=d("1.000000"),
            stale_outcome_evidence_count=d("2.000000"),
            escalation_due_count=d("2.000000"),
            max_outcome_evidence_age_seconds=d("7200.000000"),
        ),
        aggregate(
            "regulatory_resolution",
            outcome_count=d("5.000000"),
            official_evidence_count=d("3.000000"),
            independently_corroborated_count=d("1.000000"),
            rule_ambiguous_count=d("2.000000"),
            stale_outcome_evidence_count=d("2.000000"),
            escalation_due_count=d("3.000000"),
            max_outcome_evidence_age_seconds=d("14400.000000"),
        ),
    )

    assert type(report) is module.ResearchResolutionOutcomeEvidenceGapReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-resolution-outcome-evidence-gap-report-v0"
    assert report.status == "block"
    assert report.outcome_group_count == d("3.000000")
    assert report.outcome_count == d("23.000000")
    assert report.official_evidence_count == d("20.000000")
    assert report.missing_official_evidence_count == d("3.000000")
    assert report.independently_corroborated_count == d("15.000000")
    assert report.uncorroborated_evidence_count == d("5.000000")
    assert report.rule_ambiguous_count == d("3.000000")
    assert report.stale_outcome_evidence_count == d("4.000000")
    assert report.escalation_due_count == d("5.000000")
    assert report.official_evidence_coverage_ratio == d("0.869565")
    assert report.independent_corroboration_ratio == d("0.750000")
    assert report.rule_ambiguity_ratio == d("0.130435")
    assert report.stale_outcome_evidence_ratio == d("0.200000")
    assert report.escalation_urgency_ratio == d("0.217391")
    assert report.max_outcome_evidence_age_seconds == d("14400.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.outcome_group for row in report.rows) == (
        "regulatory_resolution",
        "sports_settlement",
        "official_final_results",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert report.rows[0].reason_codes == (
        "outcome_evidence_gap_block",
        "official_evidence_coverage_block",
        "independent_corroboration_block",
        "rule_ambiguity_block",
        "stale_outcome_evidence_block",
        "escalation_urgency_block",
    )
    assert report.rows[1].reason_codes == (
        "outcome_evidence_gap_watch",
        "official_evidence_coverage_watch",
        "independent_corroboration_watch",
        "stale_outcome_evidence_watch",
        "escalation_urgency_watch",
    )
    assert report.rows[2].reason_codes == ("outcome_evidence_gap_pass",)
    assert report.reason_codes == (
        "outcome_evidence_gap_report_block",
        "official_evidence_coverage_block",
        "independent_corroboration_block",
        "rule_ambiguity_block",
        "stale_outcome_evidence_block",
        "escalation_urgency_block",
        "official_evidence_coverage_watch",
        "independent_corroboration_watch",
        "stale_outcome_evidence_watch",
        "escalation_urgency_watch",
    )

    public_payload = module.research_resolution_outcome_evidence_gap_report_payload(report)
    assert public_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert public_payload["official_evidence_coverage_ratio"] == "0.869565"
    assert public_payload["rows"][0]["outcome_group"] == "regulatory_resolution"  # type: ignore[index]
    assert public_payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    json.dumps(public_payload, sort_keys=True)
    _assert_no_public_numeric_scalars(public_payload)
    _assert_no_raw_market_or_source_identifiers(public_payload)


def test_report_contract_is_frozen_decimal_only_deterministic_and_tamper_checked() -> None:
    module = api()
    values = (
        aggregate("official_final_results"),
        aggregate(
            "sports_settlement",
            outcome_count=d("8.000000"),
            official_evidence_count=d("7.000000"),
            independently_corroborated_count=d("5.000000"),
            rule_ambiguous_count=d("1.000000"),
            stale_outcome_evidence_count=d("2.000000"),
            escalation_due_count=d("2.000000"),
            max_outcome_evidence_age_seconds=d("7200.000000"),
        ),
    )
    first = build_report(*values)
    second = build_report(*reversed(values))

    assert first == second
    assert payload(first) == payload(second)
    assert module.OUTCOME_EVIDENCE_GAP_STATUSES == ("pass", "watch", "block")
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)
    for cls in (
        module.ResearchResolutionOutcomeEvidenceGapReportConfig,
        module.ResearchResolutionOutcomeEvidenceGapAggregate,
        module.ResearchResolutionOutcomeEvidenceGapRow,
        module.ResearchResolutionOutcomeEvidenceGapReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        first.status = "pass"  # type: ignore[misc]
    _assert_decimal_public_fields(first)
    for row in first.rows:
        _assert_decimal_public_fields(row)

    with pytest.raises(ValueError, match="watch_official_evidence_coverage_ratio"):
        config(watch_official_evidence_coverage_ratio=1)
    with pytest.raises(ValueError, match="block_independent_corroboration_ratio"):
        config(block_independent_corroboration_ratio=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="outcome_group"):
        aggregate("https://example.invalid/outcome")
    with pytest.raises(ValueError, match="outcome_group"):
        aggregate("raw_market_slug")
    with pytest.raises(ValueError, match="outcome_count"):
        aggregate("bad_count", outcome_count=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="official_evidence_count"):
        aggregate("bad_official", official_evidence_count=d("11.000000"))
    with pytest.raises(ValueError, match="independently_corroborated_count"):
        aggregate("bad_corrob", independently_corroborated_count=d("11.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(aggregate("bad_flag"), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(first, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(first.rows[0], status="ready")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="report"):
        module.research_resolution_outcome_evidence_gap_report_payload(object())

    tampered = payload(first)
    tampered["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_resolution_outcome_evidence_gap_report_payload(tampered)


def test_empty_report_is_pass_and_public_safe() -> None:
    module = api()
    report = build_report()

    assert report.status == "pass"
    assert report.outcome_group_count == d("0.000000")
    assert report.outcome_count == d("0.000000")
    assert report.official_evidence_coverage_ratio == d("1.000000")
    assert report.independent_corroboration_ratio == d("1.000000")
    assert report.rule_ambiguity_ratio == d("0.000000")
    assert report.stale_outcome_evidence_ratio == d("0.000000")
    assert report.escalation_urgency_ratio == d("0.000000")
    assert report.reason_codes == ("outcome_evidence_gap_report_pass",)
    assert report.rows == ()
    public_payload = module.research_resolution_outcome_evidence_gap_report_payload(report)
    module.validate_research_resolution_outcome_evidence_gap_report_payload(public_payload)
    _assert_no_public_numeric_scalars(public_payload)
    _assert_no_raw_market_or_source_identifiers(public_payload)


def test_module_has_no_external_io_or_action_surface() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_import_roots = {
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
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "buy",
        "sell",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")

    lowered_source = source.lower()
    forbidden_text = (
        "wallet",
        "private_key",
        "live execution",
        "position sizing",
        "place_order",
        "recommendation",
    )
    assert not any(token in lowered_source for token in forbidden_text)


def _assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (float, int, Decimal):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_numeric_scalars(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_public_numeric_scalars(item)


def _assert_no_raw_market_or_source_identifiers(value: Any) -> None:
    raw_keys = {
        "condition_id",
        "event_id",
        "event_slug",
        "market_id",
        "market_slug",
        "question",
        "raw_market",
        "raw_source",
        "source_id",
        "source_reference",
        "source_url",
        "url",
    }
    if isinstance(value, dict):
        assert set(value).isdisjoint(raw_keys)
        for item in value.values():
            _assert_no_raw_market_or_source_identifiers(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_raw_market_or_source_identifiers(item)


def _assert_decimal_public_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if (
            field.name.endswith("_count")
            or field.name.endswith("_ratio")
            or field.name.endswith("_seconds")
        ):
            assert type(item) is Decimal
