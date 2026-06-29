from __future__ import annotations

import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from polymarket_alpha_lab.probability_selection_scorer_agreement import (
    ProbabilitySelectionScorerAgreementReport,
)


GENERATED_AT = datetime(2026, 6, 27, 12, 0, tzinfo=UTC)


def _codec_module():
    from polymarket_alpha_lab import probability_selection_scorer_agreement_db_row

    return probability_selection_scorer_agreement_db_row


def _report(
    *,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "probability-selection-scorer-agreement-v0",
    agreement_status: str = "aligned",
) -> ProbabilitySelectionScorerAgreementReport:
    return ProbabilitySelectionScorerAgreementReport(
        generated_at=generated_at,
        config_version=config_version,
        selection_generated_at=generated_at - timedelta(minutes=2),
        scorer_generated_at=generated_at - timedelta(minutes=1),
        selected_count=2,
        scorer_candidate_count=3,
        selected_market_overlap_count=2,
        selected_condition_overlap_count=2,
        rejected_but_scored_count=0,
        scored_but_unselected_count=1,
        scorer_gate_status="pass" if agreement_status != "gate_blocked" else "blocked",
        agreement_status=agreement_status,
        recommended_next_step=_next_step(agreement_status),
        reason_codes=_reason_codes(agreement_status),
        reason_code_divergence_counts=(("model_passed", 1),),
    )


def _next_step(agreement_status: str) -> str:
    if agreement_status == "gate_blocked":
        return "review_scorer_gate"
    if agreement_status == "low_overlap":
        return "review_selection_scorer_disagreement"
    if agreement_status in ("missing_inputs", "insufficient_identifiers"):
        return "enrich_inputs"
    return "continue_monitoring"


def _reason_codes(agreement_status: str) -> tuple[str, ...]:
    if agreement_status == "gate_blocked":
        return ("scorer_gate_blocked",)
    if agreement_status == "low_overlap":
        return ("low_selection_scorer_overlap",)
    if agreement_status == "missing_inputs":
        return ("missing_inputs",)
    if agreement_status == "insufficient_identifiers":
        return ("insufficient_identifiers",)
    return ("scored_but_unselected", "selection_scorer_aligned")


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


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("agreement DB row JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_agreement_db_row_serializes_canonical_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.ProbabilitySelectionScorerAgreementDbRow
    assert len(row.report_sha256) == 64
    assert row.report_sha256 == row.report_sha256.lower()
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "probability-selection-scorer-agreement-v0"
    assert row.selection_generated_at == GENERATED_AT - timedelta(minutes=2)
    assert row.scorer_generated_at == GENERATED_AT - timedelta(minutes=1)
    assert row.selected_count == 2
    assert row.scorer_candidate_count == 3
    assert row.selected_market_overlap_count == 2
    assert row.selected_condition_overlap_count == 2
    assert row.rejected_but_scored_count == 0
    assert row.scored_but_unselected_count == 1
    assert row.scorer_gate_status == "pass"
    assert row.agreement_status == "aligned"
    assert row.recommended_next_step == "continue_monitoring"
    assert row.reason_codes_json == ["scored_but_unselected", "selection_scorer_aligned"]
    assert row.reason_code_divergence_counts_json == [["model_passed", 1]]
    assert row.payload_json["generated_at"] == "2026-06-27T12:00:00+00:00"
    assert row.payload_json["selection_generated_at"] == "2026-06-27T11:58:00+00:00"
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    assert (
        row.payload_json["reason_code_divergence_counts"]
        == row.reason_code_divergence_counts_json
    )
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_no_floats(row.reason_codes_json)
    _assert_no_floats(row.reason_code_divergence_counts_json)
    _assert_no_floats(row.payload_json)
    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.probability_selection_scorer_agreement_report_to_db_row(report) == row
    assert codec.probability_selection_scorer_agreement_report_from_db_row(row) == report


def test_agreement_db_row_hash_is_deterministic_and_changes_with_payload() -> None:
    codec = _codec_module()
    report = _report()
    same_report = ProbabilitySelectionScorerAgreementReport(**report.__dict__)
    different_report = _report(config_version="probability-selection-scorer-agreement-v1")

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_agreement_db_row_is_frozen_and_rejects_wrong_types() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="ProbabilitySelectionScorerAgreementReport"):
        codec.to_db_row(object())
    with pytest.raises(ValueError, match="ProbabilitySelectionScorerAgreementDbRow"):
        codec.from_db_row(object())

    class AgreementDbRowSubclass(codec.ProbabilitySelectionScorerAgreementDbRow):
        pass

    with pytest.raises(ValueError, match="ProbabilitySelectionScorerAgreementDbRow"):
        codec.from_db_row(AgreementDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_agreement_db_row_rejects_false_hard_flags(flag_name: str) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)

    row = codec.to_db_row(_report())
    payload = {**row.payload_json, flag_name: False}
    with pytest.raises(ValueError, match=flag_name):
        codec.ProbabilitySelectionScorerAgreementDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 27, 12, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "probability-selection-scorer-agreement-v1"}, "config_version"),
        ({"selected_count": 3}, "selected_count"),
        ({"scorer_candidate_count": 4}, "scorer_candidate_count"),
        ({"selected_market_overlap_count": 1}, "selected_market_overlap_count"),
        ({"selected_condition_overlap_count": 1}, "selected_condition_overlap_count"),
        ({"rejected_but_scored_count": 1}, "rejected_but_scored_count"),
        ({"scored_but_unselected_count": 0}, "scored_but_unselected_count"),
        ({"scorer_gate_status": "blocked"}, "scorer_gate_status"),
        ({"agreement_status": "low_overlap"}, "agreement_status"),
        ({"recommended_next_step": "enrich_inputs"}, "recommended_next_step"),
        ({"reason_codes_json": ["selection_scorer_aligned"]}, "reason_codes_json"),
        ({"reason_code_divergence_counts_json": []}, "reason_code_divergence_counts_json"),
    ),
)
def test_agreement_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.ProbabilitySelectionScorerAgreementDbRow(**{**_row_values(row), **overrides})

    malformed = _bypassed_row(row, **overrides)
    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_agreement_db_row_rejects_recursive_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="reason_code_divergence_counts_json"):
        replace(
            row,
            reason_code_divergence_counts_json=[["model_passed", 1.0]],
        )
    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})


def test_agreement_db_row_source_has_no_market_or_live_trading_details() -> None:
    source = Path(
        "src/polymarket_alpha_lab/probability_selection_scorer_agreement_db_row.py",
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
