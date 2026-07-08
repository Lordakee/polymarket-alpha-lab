from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

import polymarket_alpha_lab.research_event_resolution_rule_clarity_scorecard as api
from polymarket_alpha_lab.research_event_resolution_rule_clarity_scorecard import (
    ResearchEventResolutionRuleCategoryInput,
    ResearchEventResolutionRuleClarityReasonCodeCount,
    ResearchEventResolutionRuleClarityScorecardConfig,
    ResearchEventResolutionRuleClarityScorecardReport,
    ResearchEventResolutionRuleClarityScorecardRow,
    build_research_event_resolution_rule_clarity_scorecard,
    research_event_resolution_rule_clarity_scorecard_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 9, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def category(
    event_category: str = "sports",
    *,
    rule_specificity_score: Decimal = d("0.900000"),
    oracle_consistency_score: Decimal = d("0.900000"),
    deadline_clarity_score: Decimal = d("0.800000"),
    subjective_wording_flag: bool = False,
    discretionary_resolution_flag: bool = False,
    conflicting_resolution_flag: bool = False,
    missing_deadline_flag: bool = False,
) -> ResearchEventResolutionRuleCategoryInput:
    return ResearchEventResolutionRuleCategoryInput(
        event_category=event_category,
        rule_specificity_score=rule_specificity_score,
        oracle_consistency_score=oracle_consistency_score,
        deadline_clarity_score=deadline_clarity_score,
        subjective_wording_flag=subjective_wording_flag,
        discretionary_resolution_flag=discretionary_resolution_flag,
        conflicting_resolution_flag=conflicting_resolution_flag,
        missing_deadline_flag=missing_deadline_flag,
    )


def report(
    rows: tuple[ResearchEventResolutionRuleCategoryInput, ...],
    *,
    config: ResearchEventResolutionRuleClarityScorecardConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventResolutionRuleClarityScorecardReport:
    return build_research_event_resolution_rule_clarity_scorecard(
        rows,
        config=config,
        generated_at=generated_at,
    )


def test_clear_category_passes_with_public_workflow_status() -> None:
    scorecard = report((category(),))

    row = scorecard.rows[0]
    assert type(scorecard) is ResearchEventResolutionRuleClarityScorecardReport
    assert type(row) is ResearchEventResolutionRuleClarityScorecardRow
    assert scorecard.workflow_status == "pass"
    assert scorecard.category_count == d("1.000000")
    assert scorecard.pass_count == d("1.000000")
    assert scorecard.watch_count == d("0.000000")
    assert scorecard.block_count == d("0.000000")
    assert scorecard.average_clarity_score == d("0.870000")
    assert scorecard.max_ambiguity_flag_count == d("0.000000")
    assert row.event_category == "sports"
    assert row.clarity_score == d("0.870000")
    assert row.ambiguity_flag_count == d("0.000000")
    assert row.workflow_status == "pass"
    assert row.reason_codes == (
        "rule_specificity_ready",
        "oracle_consistency_ready",
        "deadline_clear",
        "ambiguity_clear",
        "clarity_pass",
    )
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True


def test_weak_specificity_and_ambiguity_flags_return_watch() -> None:
    scorecard = report(
        (
            category(
                rule_specificity_score=d("0.600000"),
                oracle_consistency_score=d("0.750000"),
                deadline_clarity_score=d("0.700000"),
                subjective_wording_flag=True,
            ),
        ),
    )

    row = scorecard.rows[0]
    assert scorecard.workflow_status == "watch"
    assert scorecard.pass_count == d("0.000000")
    assert scorecard.watch_count == d("1.000000")
    assert scorecard.block_count == d("0.000000")
    assert scorecard.average_clarity_score == d("0.582500")
    assert scorecard.max_ambiguity_flag_count == d("1.000000")
    assert row.clarity_score == d("0.582500")
    assert row.ambiguity_flag_count == d("1.000000")
    assert row.workflow_status == "watch"
    assert row.reason_codes == (
        "rule_specificity_gap",
        "oracle_consistency_ready",
        "deadline_clear",
        "ambiguity_flag_present",
        "clarity_watch",
    )


def test_conflicting_resolution_and_low_clarity_block_category() -> None:
    scorecard = report(
        (
            category(
                event_category="politics",
                rule_specificity_score=d("0.400000"),
                oracle_consistency_score=d("0.300000"),
                deadline_clarity_score=d("0.200000"),
                conflicting_resolution_flag=True,
            ),
        ),
    )

    row = scorecard.rows[0]
    assert scorecard.workflow_status == "block"
    assert scorecard.block_count == d("1.000000")
    assert scorecard.average_clarity_score == d("0.205000")
    assert row.clarity_score == d("0.205000")
    assert row.workflow_status == "block"
    assert row.reason_codes == (
        "rule_specificity_gap",
        "oracle_consistency_gap",
        "deadline_gap",
        "ambiguity_block",
        "clarity_block",
    )


def test_empty_categories_block_with_public_reason_count() -> None:
    scorecard = report(())

    assert scorecard.workflow_status == "block"
    assert scorecard.category_count == d("0.000000")
    assert scorecard.average_clarity_score == d("0.000000")
    assert scorecard.rows == ()
    assert scorecard.reason_codes == ("no_event_categories",)
    assert scorecard.reason_code_counts == (
        ResearchEventResolutionRuleClarityReasonCodeCount(
            reason_code="no_event_categories",
            count=d("1.000000"),
        ),
    )


def test_payload_is_deterministic_digest_backed_and_decimal_string_only() -> None:
    scorecard = report(
        (
            category("zeta"),
            category(
                "alpha",
                rule_specificity_score=d("0.600000"),
                oracle_consistency_score=d("0.750000"),
                deadline_clarity_score=d("0.700000"),
                subjective_wording_flag=True,
            ),
        ),
    )
    repeated = report(
        (
            category(
                "alpha",
                rule_specificity_score=d("0.600000"),
                oracle_consistency_score=d("0.750000"),
                deadline_clarity_score=d("0.700000"),
                subjective_wording_flag=True,
            ),
            category("zeta"),
        ),
    )

    payload = research_event_resolution_rule_clarity_scorecard_payload(scorecard)
    encoded = json.dumps(payload, sort_keys=True)
    assert tuple(row.event_category for row in scorecard.rows) == ("alpha", "zeta")
    assert scorecard.derived_validation_digest == repeated.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T09:30:00+00:00"
    assert payload["category_count"] == "2.000000"
    assert payload["average_clarity_score"] == "0.726250"
    assert payload["rows"][0]["clarity_score"] == "0.582500"
    assert payload["derived_validation_digest"] == scorecard.derived_validation_digest
    assert len(scorecard.derived_validation_digest) == 64
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0." not in encoded
    _assert_no_decimal_objects(payload)
    _assert_public_payload_text_is_safe(encoded)


def test_validation_rejects_non_decimal_inputs_bad_times_and_unsafe_labels() -> None:
    with pytest.raises(ValueError, match="rule_specificity_score"):
        category(rule_specificity_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="oracle_consistency_score"):
        category(oracle_consistency_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((category(),), generated_at=datetime(2026, 7, 8, 9, 30))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (category(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 9, 30, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="event_category"):
        category("market-politics")
    with pytest.raises(ValueError, match="event_category"):
        category("source-news")
    with pytest.raises(ValueError, match="subjective_wording_flag"):
        replace(category(), subjective_wording_flag=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(category(), paper_only=False)
    with pytest.raises(ValueError, match="workflow_status"):
        replace(report((category(),)).rows[0], workflow_status="ready")


def test_dataclasses_are_frozen_reject_subclasses_and_validate_digest() -> None:
    scorecard = report((category(),))

    with pytest.raises(FrozenInstanceError):
        scorecard.workflow_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        scorecard.rows[0].clarity_score = d("0")  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadConfig(ResearchEventResolutionRuleClarityScorecardConfig):
            pass

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(scorecard, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="pass_count"):
        replace(scorecard, pass_count=d("2.000000"))


def test_public_surface_exposes_no_raw_or_operational_identifiers() -> None:
    forbidden_public_fragments = (
        "raw",
        "market",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
        "private-key",
        "recommend",
    )
    for public_name in api.__all__:
        lowered = public_name.lower()
        assert not any(fragment in lowered for fragment in forbidden_public_fragments)

    for cls in (
        ResearchEventResolutionRuleCategoryInput,
        ResearchEventResolutionRuleClarityScorecardConfig,
        ResearchEventResolutionRuleClarityScorecardRow,
        ResearchEventResolutionRuleClarityReasonCodeCount,
        ResearchEventResolutionRuleClarityScorecardReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_public_fragments)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_resolution_rule_clarity_scorecard.py"
    )
    module_text = module_path.read_text(encoding="utf-8").lower()
    forbidden_io_fragments = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "boto3",
        "web3",
        "ccxt",
    )
    assert all(fragment not in module_text for fragment in forbidden_io_fragments)
    _assert_no_non_decimal_public_numbers(report((category(),)))


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


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))


def _assert_public_payload_text_is_safe(value: str) -> None:
    lowered = value.lower()
    forbidden_fragments = (
        "raw",
        "market",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "wallet",
        "auth",
        "order",
        "trade",
        "private-key",
        "recommend",
    )
    assert not any(fragment in lowered for fragment in forbidden_fragments)
