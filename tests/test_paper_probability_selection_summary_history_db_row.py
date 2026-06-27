from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.paper_probability_selection_summary_history import (
    PaperProbabilitySelectionSummaryHistoryReport,
)


GENERATED_AT = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
FIRST_GENERATED_AT = datetime(2026, 6, 22, 10, 0, tzinfo=UTC)
LATEST_GENERATED_AT = datetime(2026, 6, 22, 11, 45, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _codec_module():
    from polymarket_alpha_lab import paper_probability_selection_summary_history_db_row

    return paper_probability_selection_summary_history_db_row


def _report() -> PaperProbabilitySelectionSummaryHistoryReport:
    return PaperProbabilitySelectionSummaryHistoryReport(
        generated_at=GENERATED_AT,
        config_version="paper-probability-selection-summary-history-v0",
        source_report_count=3,
        first_generated_at=FIRST_GENERATED_AT,
        latest_generated_at=LATEST_GENERATED_AT,
        history_span_seconds=6300,
        latest_age_seconds=900,
        latest_queue_count=6,
        latest_selected_count=4,
        latest_pending_count=1,
        latest_rejected_count=1,
        latest_skipped_count=1,
        aggregate_queue_count=15,
        aggregate_selected_count=9,
        aggregate_pending_count=3,
        aggregate_rejected_count=3,
        aggregate_skipped_count=2,
        latest_selected_share=d("0.666667"),
        average_selected_share=d("0.600000"),
        distinct_config_versions=("paper-probability-selection-summary-v0",),
        reason_code_counts=(
            ("cost_stress_passed", 6),
            ("source_edge", 5),
            ("watch_selection_rows_present", 4),
        ),
        history_status="watch",
        recommended_next_step="review_probability_selection",
        reason_codes=(
            "latest_selection_has_blocked_rows",
            "latest_selection_has_watch_rows",
        ),
    )


def _empty_report() -> PaperProbabilitySelectionSummaryHistoryReport:
    return PaperProbabilitySelectionSummaryHistoryReport(
        generated_at=GENERATED_AT,
        config_version="paper-probability-selection-summary-history-v0",
        source_report_count=0,
        first_generated_at=None,
        latest_generated_at=None,
        history_span_seconds=None,
        latest_age_seconds=None,
        latest_queue_count=0,
        latest_selected_count=0,
        latest_pending_count=0,
        latest_rejected_count=0,
        latest_skipped_count=0,
        aggregate_queue_count=0,
        aggregate_selected_count=0,
        aggregate_pending_count=0,
        aggregate_rejected_count=0,
        aggregate_skipped_count=0,
        latest_selected_share=d("0.000000"),
        average_selected_share=d("0.000000"),
        distinct_config_versions=(),
        reason_code_counts=(),
        history_status="blocked",
        recommended_next_step="collect_more_history",
        reason_codes=(
            "no_selection_summary_history",
            "insufficient_selection_summary_history",
        ),
    )


def _all_selected_report() -> PaperProbabilitySelectionSummaryHistoryReport:
    return PaperProbabilitySelectionSummaryHistoryReport(
        generated_at=GENERATED_AT,
        config_version="paper-probability-selection-summary-history-v0",
        source_report_count=3,
        first_generated_at=FIRST_GENERATED_AT,
        latest_generated_at=LATEST_GENERATED_AT,
        history_span_seconds=6300,
        latest_age_seconds=900,
        latest_queue_count=6,
        latest_selected_count=6,
        latest_pending_count=0,
        latest_rejected_count=0,
        latest_skipped_count=0,
        aggregate_queue_count=15,
        aggregate_selected_count=15,
        aggregate_pending_count=0,
        aggregate_rejected_count=0,
        aggregate_skipped_count=0,
        latest_selected_share=d("1.000000"),
        average_selected_share=d("1.000000"),
        distinct_config_versions=("paper-probability-selection-summary-v0",),
        reason_code_counts=(("selection_summary_history_stable", 15),),
        history_status="ready",
        recommended_next_step="proceed_to_paper_allocation",
        reason_codes=("selection_summary_history_stable",),
    )


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
        pytest.fail("DB payload must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_history_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperProbabilitySelectionSummaryHistoryDbRow
    assert len(row.report_sha256) == 64
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-probability-selection-summary-history-v0"
    assert row.source_report_count == 3
    assert row.latest_generated_at == LATEST_GENERATED_AT
    assert row.latest_age_seconds == 900
    assert row.latest_queue_count == 6
    assert row.latest_selected_count == 4
    assert row.latest_selected_share == d("0.666667")
    assert row.average_selected_share == d("0.600000")
    assert row.history_status == "watch"
    assert row.recommended_next_step == "review_probability_selection"
    assert row.reason_codes_json == [
        "latest_selection_has_blocked_rows",
        "latest_selection_has_watch_rows",
    ]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-22T12:00:00+00:00"
    assert row.payload_json["first_generated_at"] == "2026-06-22T10:00:00+00:00"
    assert row.payload_json["latest_generated_at"] == "2026-06-22T11:45:00+00:00"
    assert row.payload_json["latest_selected_share"] == "0.666667"
    assert row.payload_json["average_selected_share"] == "0.600000"
    assert row.payload_json["distinct_config_versions"] == [
        "paper-probability-selection-summary-v0",
    ]
    assert row.payload_json["reason_code_counts"] == [
        ["cost_stress_passed", 6],
        ["source_edge", 5],
        ["watch_selection_rows_present", 4],
    ]
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.payload_json)
    _assert_no_floats(row.reason_codes_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_probability_selection_summary_history_report_to_db_row(report) == row
    assert codec.paper_probability_selection_summary_history_report_from_db_row(row) == report


def test_history_db_row_hash_is_deterministic() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperProbabilitySelectionSummaryHistoryReport(**report.__dict__)
    different_report = PaperProbabilitySelectionSummaryHistoryReport(
        **{
            **report.__dict__,
            "config_version": "paper-probability-selection-summary-history-v1",
        },
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_history_db_row_writes_fixed_six_place_share_payloads() -> None:
    codec = _codec_module()
    zero_report = _empty_report()
    object.__setattr__(zero_report, "latest_selected_share", d("0"))
    object.__setattr__(zero_report, "average_selected_share", d("0.0"))
    one_report = _all_selected_report()
    object.__setattr__(one_report, "latest_selected_share", d("1"))
    object.__setattr__(one_report, "average_selected_share", d("1.0"))

    zero_row = codec.to_db_row(zero_report)
    one_row = codec.to_db_row(one_report)

    assert zero_row.payload_json["latest_selected_share"] == "0.000000"
    assert zero_row.payload_json["average_selected_share"] == "0.000000"
    assert one_row.payload_json["latest_selected_share"] == "1.000000"
    assert one_row.payload_json["average_selected_share"] == "1.000000"


def test_history_db_row_equivalent_share_decimal_exponents_hash_identically() -> None:
    codec = _codec_module()
    zero_report = _empty_report()
    zero_equivalent = _empty_report()
    object.__setattr__(zero_equivalent, "latest_selected_share", d("0"))
    object.__setattr__(zero_equivalent, "average_selected_share", d("0.0"))
    one_report = _all_selected_report()
    one_equivalent = _all_selected_report()
    object.__setattr__(one_equivalent, "latest_selected_share", d("1"))
    object.__setattr__(one_equivalent, "average_selected_share", d("1.0"))

    zero_row = codec.to_db_row(zero_report)
    zero_equivalent_row = codec.to_db_row(zero_equivalent)
    one_row = codec.to_db_row(one_report)
    one_equivalent_row = codec.to_db_row(one_equivalent)

    assert zero_equivalent_row.payload_json == zero_row.payload_json
    assert zero_equivalent_row.report_sha256 == zero_row.report_sha256
    assert one_equivalent_row.payload_json == one_row.payload_json
    assert one_equivalent_row.report_sha256 == one_row.report_sha256


@pytest.mark.parametrize("field_name", ("latest_selected_share", "average_selected_share"))
def test_history_db_row_rejects_overprecision_share_writes_without_rounding(
    field_name: str,
) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, field_name, d("0.6000001"))

    with pytest.raises(ValueError, match=f"{field_name}|six decimal places"):
        codec.to_db_row(report)


def test_history_db_row_accepts_self_hashed_legacy_share_payload_strings() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    legacy_payload = deepcopy(row.payload_json)
    legacy_payload["latest_selected_share"] = "0.6666670"
    legacy_payload["average_selected_share"] = "0.6"

    legacy_row = codec.PaperProbabilitySelectionSummaryHistoryDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(legacy_payload),
            "payload_json": legacy_payload,
        },
    )

    assert codec.from_db_row(legacy_row) == _report()


def test_history_from_db_row_validates_raw_hash_before_legacy_share_normalization() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    legacy_payload = deepcopy(row.payload_json)
    legacy_payload["latest_selected_share"] = "0.6666670"
    legacy_payload["average_selected_share"] = "0.6"
    stale_row = _bypassed_row(row, payload_json=legacy_payload)

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(stale_row)


def test_history_db_row_rejects_raw_payload_values_before_normalization() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    payloads = (
        {**row.payload_json, "latest_selected_share": d("0.666667")},
        {**row.payload_json, "generated_at": GENERATED_AT},
        {**row.payload_json, "average_selected_share": 0.6},
    )
    for payload in payloads:
        with pytest.raises(ValueError, match="payload_json"):
            codec.PaperProbabilitySelectionSummaryHistoryDbRow(
                **{**_row_values(row), "payload_json": payload},
            )
        with pytest.raises(ValueError, match="payload_json"):
            codec.from_db_row(_bypassed_row(row, payload_json=payload))


def test_history_db_row_rejects_value_changing_legacy_share_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["latest_selected_share"] = "0.666666"

    with pytest.raises(ValueError, match="latest_selected_share|payload_json"):
        codec.PaperProbabilitySelectionSummaryHistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_history_from_db_row_rejects_bool_int_confusion_and_missing_vs_null() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="paper_only"):
        codec.from_db_row(_bypassed_row(row, paper_only=1))

    bool_payload = {**row.payload_json, "source_report_count": True}
    with pytest.raises(ValueError, match="source_report_count|payload_json"):
        codec.from_db_row(
            _bypassed_row(
                row,
                source_report_count=True,
                report_sha256=_canonical_payload_sha256(bool_payload),
                payload_json=bool_payload,
            ),
        )

    null_payload = {**row.payload_json, "latest_age_seconds": None}
    with pytest.raises(ValueError, match="latest_age_seconds|payload_json"):
        codec.from_db_row(
            _bypassed_row(
                row,
                latest_age_seconds=None,
                report_sha256=_canonical_payload_sha256(null_payload),
                payload_json=null_payload,
            ),
        )

    missing_payload = {
        key: value for key, value in row.payload_json.items() if key != "latest_age_seconds"
    }
    with pytest.raises(ValueError, match="latest_age_seconds|payload_json"):
        codec.from_db_row(
            _bypassed_row(
                row,
                report_sha256=_canonical_payload_sha256(missing_payload),
                payload_json=missing_payload,
            ),
        )


def test_history_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_history_db_row_rejects_wrong_report_types() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryHistoryReport"):
        codec.to_db_row(object())


def test_history_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    class HistoryDbRowSubclass(codec.PaperProbabilitySelectionSummaryHistoryDbRow):
        pass

    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryHistoryDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryHistoryDbRow"):
        codec.from_db_row(HistoryDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_history_db_row_rejects_false_report_flags_before_write(flag_name: str) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_history_db_row_rejects_corrupted_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "readonly": False,
    }

    with pytest.raises(ValueError, match="readonly"):
        codec.PaperProbabilitySelectionSummaryHistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_history_db_row_rejects_missing_payload_flags_at_construction(
    flag_name: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {
        key: value for key, value in row.payload_json.items() if key != flag_name
    }

    with pytest.raises(ValueError, match=flag_name):
        codec.PaperProbabilitySelectionSummaryHistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


@pytest.mark.parametrize("field_name", ("latest_generated_at", "latest_age_seconds"))
def test_history_db_row_rejects_missing_none_payload_fields_at_construction(
    field_name: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_empty_report())
    payload = {
        key: value for key, value in row.payload_json.items() if key != field_name
    }

    with pytest.raises(ValueError, match=field_name):
        codec.PaperProbabilitySelectionSummaryHistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_history_db_row_rejects_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperProbabilitySelectionSummaryHistoryDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 22, 12, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-probability-selection-summary-history-v1"}, "config_version"),
        ({"source_report_count": 2}, "source_report_count"),
        ({"latest_generated_at": datetime(2026, 6, 22, 11, 44, tzinfo=UTC)}, "latest_generated_at"),
        ({"latest_age_seconds": 901}, "latest_age_seconds"),
        ({"latest_queue_count": 5}, "latest_queue_count"),
        ({"latest_selected_count": 3}, "latest_selected_count"),
        ({"latest_selected_share": d("0.500000")}, "latest_selected_share"),
        ({"average_selected_share": d("0.500000")}, "average_selected_share"),
        ({"history_status": "blocked"}, "history_status"),
        ({"recommended_next_step": "collect_more_history"}, "recommended_next_step"),
        ({"reason_codes_json": ["latest_selection_has_watch_rows"]}, "reason_codes_json"),
    ),
)
def test_history_db_row_rejects_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperProbabilitySelectionSummaryHistoryDbRow(
            **{**_row_values(row), **overrides},
        )


def test_history_db_row_rejects_payload_mismatch_on_replace() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="latest_queue_count"):
        replace(row, latest_queue_count=5)


def test_history_from_db_row_rejects_constructor_bypassed_mismatch() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = _bypassed_row(row, latest_queue_count=5)

    with pytest.raises(ValueError, match="latest_queue_count"):
        codec.from_db_row(malformed)


def test_history_from_db_row_rejects_constructor_bypassed_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "readonly": False,
    }
    malformed = _bypassed_row(
        row,
        report_sha256=_canonical_payload_sha256(payload),
        payload_json=payload,
    )

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"source_report_count": True}, "source_report_count"),
        ({"latest_age_seconds": -1}, "latest_age_seconds"),
        ({"latest_selected_share": "0.666667"}, "latest_selected_share"),
        ({"latest_selected_share": Decimal("1.000001")}, "latest_selected_share"),
        ({"average_selected_share": 0.6}, "average_selected_share"),
        ({"average_selected_share": Decimal("-0.000001")}, "average_selected_share"),
        ({"history_status": "stable"}, "history_status"),
        ({"recommended_next_step": "place_live_order"}, "recommended_next_step"),
        ({"reason_codes_json": "latest_selection_has_watch_rows"}, "reason_codes_json"),
        ({"reason_codes_json": [1]}, "reason_codes_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_history_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperProbabilitySelectionSummaryHistoryDbRow(
            **{**_row_values(row), **overrides},
        )


def test_history_db_row_module_is_pure_paper_only_codec() -> None:
    _codec_module()
    source = Path(
        "src/polymarket_alpha_lab/paper_probability_selection_summary_history_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "sql",
        "network",
        "client",
        "auth",
        "wallet",
        "account",
        "signing",
        "submission",
        "cancellation",
        "replacement",
        "exchange",
        "live_trading",
    ):
        assert banned not in source.lower()
