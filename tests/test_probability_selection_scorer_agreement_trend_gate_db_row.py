from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate import (
    ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount,
    ProbabilitySelectionScorerAgreementTrendGateReport,
)


GENERATED_AT = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = GENERATED_AT - timedelta(minutes=1)


def d(value: str) -> Decimal:
    return Decimal(value)


def _report(
    *,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "probability-selection-scorer-agreement-trend-gate-v0",
    gate_status: str = "watch",
    average_selected_count: Decimal = d("2.500000"),
) -> ProbabilitySelectionScorerAgreementTrendGateReport:
    reason_codes = _reason_codes(gate_status)
    return ProbabilitySelectionScorerAgreementTrendGateReport(
        generated_at=generated_at,
        config_version=config_version,
        source_config_version="probability-selection-scorer-agreement-trend-v0",
        source_generated_at=generated_at - timedelta(minutes=1),
        trend_report_age_seconds=60,
        gate_status=gate_status,
        recommended_next_step=_next_step(gate_status),
        reason_code_counts=tuple(
            ProbabilitySelectionScorerAgreementTrendGateReasonCodeCount(
                reason_code=reason_code,
                report_count=1,
            )
            for reason_code in reason_codes
        ),
        source_report_count=4,
        source_trend_status="watch",
        source_recommended_next_step="review_selection_scorer_disagreement",
        latest_agreement_status="low_overlap",
        latest_agreement_status_streak=2,
        aligned_report_count=2,
        low_overlap_report_count=2,
        gate_blocked_report_count=0,
        missing_inputs_report_count=0,
        insufficient_identifiers_report_count=0,
        average_selected_count=average_selected_count,
        average_scorer_candidate_count=d("3.250000"),
        latest_source_reason_codes=("latest_agreement_low_overlap",),
        recurring_source_reason_code_counts=(("low_selection_scorer_overlap", 2),),
        reason_codes=reason_codes,
    )


def _reason_codes(gate_status: str) -> tuple[str, ...]:
    if gate_status == "pass":
        return ("probability_selection_scorer_agreement_trend_gate_passed",)
    if gate_status == "blocked":
        return ("latest_probability_selection_scorer_agreement_trend_blocked",)
    return ("latest_probability_selection_scorer_agreement_trend_watch",)


def _next_step(gate_status: str) -> str:
    return {
        "pass": "allow_probability_selection_scorer_agreement_trend_review",
        "watch": "throttle_probability_selection_scorer_agreement_trend_review",
        "blocked": "block_probability_selection_scorer_agreement_trend_review",
    }[gate_status]


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _bypassed_row(row: object, **overrides: object) -> object:
    bypassed = object.__new__(type(row))
    for field_name, value in {**_row_values(row), **overrides}.items():
        object.__setattr__(bypassed, field_name, value)
    return bypassed


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_copy(row: object) -> dict[str, object]:
    return deepcopy(row.payload_json)  # type: ignore[attr-defined]


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("trend-gate DB row JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_trend_gate_db_row_serializes_canonical_payload_and_round_trips() -> None:
    import polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_db_row as codec

    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.ProbabilitySelectionScorerAgreementTrendGateDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "probability-selection-scorer-agreement-trend-gate-v0"
    assert row.source_config_version == "probability-selection-scorer-agreement-trend-v0"
    assert row.source_generated_at == SOURCE_GENERATED_AT
    assert row.trend_report_age_seconds == 60
    assert row.gate_status == "watch"
    assert row.recommended_next_step == (
        "throttle_probability_selection_scorer_agreement_trend_review"
    )
    assert row.reason_code_counts_json == [
        {
            "paper_only": True,
            "readonly": True,
            "reason_code": "latest_probability_selection_scorer_agreement_trend_watch",
            "report_count": 1,
            "report_only": True,
        },
    ]
    assert row.source_report_count == 4
    assert row.source_trend_status == "watch"
    assert row.latest_agreement_status == "low_overlap"
    assert row.latest_agreement_status_streak == 2
    assert row.average_selected_count == d("2.500000")
    assert row.average_scorer_candidate_count == d("3.250000")
    assert row.latest_source_reason_codes_json == ["latest_agreement_low_overlap"]
    assert row.recurring_source_reason_code_counts_json == [
        ["low_selection_scorer_overlap", 2],
    ]
    assert row.reason_codes_json == [
        "latest_probability_selection_scorer_agreement_trend_watch",
    ]
    assert row.payload_json["generated_at"] == "2026-06-30T12:00:00+00:00"
    assert row.payload_json["source_generated_at"] == "2026-06-30T11:59:00+00:00"
    assert row.payload_json["average_selected_count"] == "2.500000"
    assert row.payload_json["average_scorer_candidate_count"] == "3.250000"
    assert row.payload_json["reason_code_counts"] == row.reason_code_counts_json
    assert row.payload_json["latest_source_reason_codes"] == (
        row.latest_source_reason_codes_json
    )
    assert row.payload_json["recurring_source_reason_code_counts"] == (
        row.recurring_source_reason_code_counts_json
    )
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_no_floats(row.reason_code_counts_json)
    _assert_no_floats(row.latest_source_reason_codes_json)
    _assert_no_floats(row.recurring_source_reason_code_counts_json)
    _assert_no_floats(row.reason_codes_json)
    _assert_no_floats(row.payload_json)
    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert (
        codec.probability_selection_scorer_agreement_trend_gate_report_to_db_row(
            report,
        )
        == row
    )
    assert (
        codec.probability_selection_scorer_agreement_trend_gate_report_from_db_row(row)
        == report
    )


def test_trend_gate_db_row_normalizes_utc_and_decimal_payload_before_hashing() -> None:
    import polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_db_row as codec

    same_in_pacific = GENERATED_AT.astimezone(timezone(timedelta(hours=-7)))

    utc_row = codec.to_db_row(_report(generated_at=GENERATED_AT))
    pacific_row = codec.to_db_row(_report(generated_at=same_in_pacific))
    terse_decimal_row = codec.to_db_row(_report(average_selected_count=d("2.5")))

    assert pacific_row.generated_at == GENERATED_AT
    assert pacific_row.source_generated_at == SOURCE_GENERATED_AT
    assert pacific_row.payload_json == utc_row.payload_json
    assert pacific_row.report_sha256 == utc_row.report_sha256
    assert terse_decimal_row.payload_json["average_selected_count"] == "2.500000"
    assert terse_decimal_row.payload_json == utc_row.payload_json
    assert terse_decimal_row.report_sha256 == utc_row.report_sha256


def test_trend_gate_db_row_canonicalizes_payload_decimal_strings_before_hashing() -> None:
    import polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = _payload_copy(row)
    payload["average_selected_count"] = "2.5"

    rebuilt = codec.ProbabilitySelectionScorerAgreementTrendGateDbRow(
        **{**_row_values(row), "payload_json": payload},
    )

    assert rebuilt.payload_json["average_selected_count"] == "2.500000"
    assert rebuilt.report_sha256 == row.report_sha256
    assert codec.from_db_row(rebuilt) == _report()

    with pytest.raises(ValueError, match="report_sha256"):
        codec.ProbabilitySelectionScorerAgreementTrendGateDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_trend_gate_db_row_is_frozen_and_rejects_wrong_types_and_flags() -> None:
    import polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="ProbabilitySelectionScorerAgreementTrendGateReport"):
        codec.to_db_row(object())
    with pytest.raises(ValueError, match="ProbabilitySelectionScorerAgreementTrendGateDbRow"):
        codec.from_db_row(object())

    class TrendGateDbRowSubclass(codec.ProbabilitySelectionScorerAgreementTrendGateDbRow):
        pass

    with pytest.raises(ValueError, match="ProbabilitySelectionScorerAgreementTrendGateDbRow"):
        codec.from_db_row(TrendGateDbRowSubclass(**_row_values(row)))

    report = _report()
    object.__setattr__(report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"gate_status": "blocked"}, "gate_status"),
        ({"reason_codes_json": []}, "reason_codes_json"),
        ({"average_selected_count": d("2.600000")}, "average_selected_count"),
        ({"reason_code_counts_json": []}, "reason_code_counts_json"),
    ),
)
def test_trend_gate_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.ProbabilitySelectionScorerAgreementTrendGateDbRow(
            **{**_row_values(row), **overrides},
        )

    malformed = _bypassed_row(row, **overrides)
    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_trend_gate_db_row_rejects_float_and_decimal_payload_values() -> None:
    import polymarket_alpha_lab.probability_selection_scorer_agreement_trend_gate_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="float|payload_json"):
        replace(row, payload_json={**_payload_copy(row), "bad_float": 0.1})

    with pytest.raises(ValueError, match="Decimal|payload_json"):
        replace(
            row,
            payload_json={**_payload_copy(row), "average_selected_count": d("2.500000")},
        )

    report = _report()
    object.__setattr__(report, "average_selected_count", d("2.5000001"))
    with pytest.raises(ValueError, match="average_selected_count|six decimal"):
        codec.to_db_row(report)


def test_trend_gate_db_row_source_has_no_market_or_live_trading_details() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "probability_selection_scorer_agreement_trend_gate_db_row.py",
    ).read_text(encoding="utf-8").lower()

    for token in (
        "auth",
        "cancel",
        "condition_id",
        "market_slug",
        "order",
        "private_key",
        "question",
        "submit",
        "trade",
        "wallet",
    ):
        assert token not in source
