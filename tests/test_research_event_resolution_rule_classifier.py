from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_resolution_rule_classifier import (
    ResearchEventResolutionRuleClassificationReport,
    ResearchEventResolutionRuleClassificationRow,
    ResearchEventResolutionRuleClassifierConfig,
    ResearchEventResolutionRuleInput,
    ResearchEventResolutionRuleReasonCodeCount,
    build_research_event_resolution_rule_classification_report,
    research_event_resolution_rule_classification_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedRuleShape:
    event_key: str
    rule_id: str
    resolver_authority_count: Decimal
    measurable_condition_count: Decimal
    objective_deadline_present: bool
    numeric_threshold_present: bool
    official_resolver_present: bool
    subjective_judgment_flag: bool = False
    discretionary_clause_flag: bool = False
    conflicting_clause_flag: bool = False
    missing_condition_flag: bool = False
    unresolved_dependency_flag: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventResolutionRuleClassifierConfig:
    values = {
        "config_version": "research-event-resolution-rule-classifier-v0",
        "min_resolver_authority_count": d("1"),
        "min_measurable_condition_count": d("2"),
        "pass_clarity_score": d("0.800000"),
        "watch_clarity_score": d("0.500000"),
        "block_ambiguity_score": d("0.500000"),
        "subjective_judgment_weight": d("0.250000"),
        "discretionary_clause_weight": d("0.300000"),
        "conflicting_clause_weight": d("0.500000"),
        "missing_condition_weight": d("0.250000"),
        "unresolved_dependency_weight": d("0.200000"),
    }
    values.update(overrides)
    return ResearchEventResolutionRuleClassifierConfig(**values)


def rule(
    index: int,
    *,
    event_key: str = "event-alpha",
    rule_id: str | None = None,
    resolver_authority_count: Decimal = d("1"),
    measurable_condition_count: Decimal = d("2"),
    objective_deadline_present: bool = True,
    numeric_threshold_present: bool = True,
    official_resolver_present: bool = True,
    subjective_judgment_flag: bool = False,
    discretionary_clause_flag: bool = False,
    conflicting_clause_flag: bool = False,
    missing_condition_flag: bool = False,
    unresolved_dependency_flag: bool = False,
    reason_codes: tuple[str, ...] = (),
) -> ResearchEventResolutionRuleInput:
    return ResearchEventResolutionRuleInput(
        event_key=event_key,
        rule_id=f"rule-{index:03d}" if rule_id is None else rule_id,
        resolver_authority_count=resolver_authority_count,
        measurable_condition_count=measurable_condition_count,
        objective_deadline_present=objective_deadline_present,
        numeric_threshold_present=numeric_threshold_present,
        official_resolver_present=official_resolver_present,
        subjective_judgment_flag=subjective_judgment_flag,
        discretionary_clause_flag=discretionary_clause_flag,
        conflicting_clause_flag=conflicting_clause_flag,
        missing_condition_flag=missing_condition_flag,
        unresolved_dependency_flag=unresolved_dependency_flag,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchEventResolutionRuleClassifierConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventResolutionRuleClassificationReport:
    return build_research_event_resolution_rule_classification_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_summary() -> None:
    classification_report = report(())

    assert type(classification_report) is ResearchEventResolutionRuleClassificationReport
    assert classification_report.generated_at == GENERATED_AT
    assert classification_report.config_version == "research-event-resolution-rule-classifier-v0"
    assert classification_report.rule_count == d("0")
    assert classification_report.pass_count == d("0")
    assert classification_report.watch_count == d("0")
    assert classification_report.block_count == d("0")
    assert classification_report.average_clarity_score is None
    assert classification_report.average_ambiguity_score is None
    assert classification_report.status == "block"
    assert classification_report.reason_codes == ("no_resolution_rules",)
    assert classification_report.reason_code_counts == (
        ResearchEventResolutionRuleReasonCodeCount(
            reason_code="no_resolution_rules",
            count=d("1"),
        ),
    )
    assert classification_report.rows == ()
    assert classification_report.paper_only is True
    assert classification_report.report_only is True
    assert classification_report.readonly is True


def test_objective_measurable_rule_passes_as_clear() -> None:
    classification_report = report((rule(1),))

    row = classification_report.rows[0]
    assert type(row) is ResearchEventResolutionRuleClassificationRow
    assert classification_report.status == "pass"
    assert classification_report.pass_count == d("1")
    assert classification_report.watch_count == d("0")
    assert classification_report.block_count == d("0")
    assert classification_report.average_clarity_score == d("1.000000")
    assert classification_report.average_ambiguity_score == d("0.000000")
    assert row.event_key == "event-alpha"
    assert row.rule_id == "rule-001"
    assert row.clarity_score == d("1.000000")
    assert row.ambiguity_score == d("0.000000")
    assert row.review_pressure_score == d("0.000000")
    assert row.status == "pass"
    assert row.resolution_rule_class == "clear"
    assert row.reason_codes == (
        "numeric_threshold_present",
        "objective_deadline_present",
        "official_resolver_present",
        "resolution_rule_clear",
        "resolver_authority_present",
        "sufficient_measurable_conditions",
    )


def test_subjective_or_thin_rule_returns_watch_manual_review() -> None:
    classification_report = report(
        (
            rule(
                1,
                measurable_condition_count=d("1"),
                objective_deadline_present=False,
                subjective_judgment_flag=True,
                reason_codes=("manual_review_seed",),
            ),
        ),
    )

    row = classification_report.rows[0]
    assert classification_report.status == "watch"
    assert classification_report.pass_count == d("0")
    assert classification_report.watch_count == d("1")
    assert classification_report.block_count == d("0")
    assert classification_report.average_clarity_score == d("0.700000")
    assert classification_report.average_ambiguity_score == d("0.250000")
    assert row.clarity_score == d("0.700000")
    assert row.ambiguity_score == d("0.250000")
    assert row.review_pressure_score == d("0.550000")
    assert row.status == "watch"
    assert row.resolution_rule_class == "manual_review"
    assert row.reason_codes == (
        "input_manual_review_seed",
        "manual_review_needed",
        "missing_deadline",
        "numeric_threshold_present",
        "official_resolver_present",
        "resolver_authority_present",
        "subjective_judgment_present",
        "thin_measurable_conditions",
    )


def test_conflicting_discretionary_rule_returns_block() -> None:
    classification_report = report(
        (
            rule(
                1,
                resolver_authority_count=d("0"),
                measurable_condition_count=d("0"),
                objective_deadline_present=False,
                numeric_threshold_present=False,
                official_resolver_present=False,
                discretionary_clause_flag=True,
                conflicting_clause_flag=True,
                missing_condition_flag=True,
                unresolved_dependency_flag=True,
            ),
        ),
    )

    row = classification_report.rows[0]
    assert classification_report.status == "block"
    assert classification_report.block_count == d("1")
    assert classification_report.average_clarity_score == d("0.000000")
    assert classification_report.average_ambiguity_score == d("1.000000")
    assert row.status == "block"
    assert row.resolution_rule_class == "ambiguity_block"
    assert row.reason_codes == (
        "ambiguity_block",
        "conflicting_clauses_present",
        "discretionary_clause_present",
        "missing_conditions_present",
        "missing_deadline",
        "missing_numeric_threshold",
        "missing_official_resolver",
        "missing_resolver_authority",
        "thin_measurable_conditions",
        "unresolved_dependency_present",
    )


def test_rows_reason_counts_and_payload_are_safe_and_decimal_only() -> None:
    classification_report = report(
        (
            rule(2, event_key="event-z"),
            rule(
                1,
                event_key="event-a",
                measurable_condition_count=d("1"),
                objective_deadline_present=False,
                subjective_judgment_flag=True,
                reason_codes=("zeta", "alpha"),
            ),
        ),
    )

    payload = research_event_resolution_rule_classification_report_payload(
        classification_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.event_key for row in classification_report.rows) == (
        "event-a",
        "event-z",
    )
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["clarity_score"] == str(
        classification_report.rows[0].clarity_score,
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    assert _public_payload_text_is_safe(encoded)


def test_validation_rejects_bad_types_subclasses_flags_and_public_identifiers() -> None:
    with pytest.raises(ValueError, match="pass_clarity_score"):
        config(pass_clarity_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_clarity_score"):
        config(watch_clarity_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((rule(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((rule(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="event_key"):
        rule(1, event_key=" market-alpha")
    with pytest.raises(ValueError, match="event_key"):
        rule(1, event_key="market-alpha")
    with pytest.raises(ValueError, match="rule_id"):
        rule(1, rule_id="rule 1")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="resolver_authority_count"):
        rule(1, resolver_authority_count=d("1.5"))
    with pytest.raises(ValueError, match="subjective_judgment_flag"):
        replace(rule(1), subjective_judgment_flag=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="reason_codes"):
        rule(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(rule(1), paper_only=False)


def test_supplied_shape_is_coerced_without_allowing_unsafe_payload_fields() -> None:
    classification_report = report(
        (
            SuppliedRuleShape(
                event_key="event-shape",
                rule_id="rule-shape",
                resolver_authority_count=d("1"),
                measurable_condition_count=d("2"),
                objective_deadline_present=True,
                numeric_threshold_present=True,
                official_resolver_present=True,
            ),
        ),
    )

    assert classification_report.rows[0].event_key == "event-shape"
    assert classification_report.rows[0].status == "pass"


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    classification_report = report((rule(1),))

    with pytest.raises(FrozenInstanceError):
        classification_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        classification_report.rows[0].clarity_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="clarity_score"):
        replace(classification_report.rows[0], clarity_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(classification_report, status="watch")


def test_owned_module_has_no_network_filesystem_execution_or_db_write_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_resolution_rule_classifier.py"
    )
    module_text = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "boto3",
    )

    assert all(term not in module_text for term in forbidden_terms)


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


def _public_payload_text_is_safe(value: str) -> bool:
    lowered = value.lower()
    forbidden_fragments = (
        "market",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "buy",
        "sell",
        "position",
        "recommend",
    )
    return not any(fragment in lowered for fragment in forbidden_fragments)
