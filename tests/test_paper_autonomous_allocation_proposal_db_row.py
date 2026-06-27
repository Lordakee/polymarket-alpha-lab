from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
from types import ModuleType

import pytest

from polymarket_alpha_lab.paper_recommendation_allocation import (
    PaperRecommendationAllocationConfig,
    PaperRecommendationAllocationReport,
    build_paper_recommendation_allocation_report,
)
from tests.test_paper_recommendation_allocation import _input_row


REDUCER_MODULE_NAME = "polymarket_alpha_lab.paper_autonomous_allocation_proposal"
GENERATED_AT = datetime(2026, 6, 23, 20, 0, tzinfo=UTC)
SCREENING_GATE_AT = datetime(2026, 6, 23, 19, 30, tzinfo=UTC)
QUEUE_RISK_AT = datetime(2026, 6, 23, 19, 40, tzinfo=UTC)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
FIXED_SIX_DECIMAL_RE = re.compile(r"^-?\d+\.\d{6}$")
ALLOCATION_REPORT_DECIMAL_FIELDS = (
    "total_requested_paper_notional",
    "total_allocated_paper_notional",
    "remaining_paper_budget",
    "total_paper_budget",
    "max_paper_notional_per_market",
    "max_paper_notional_per_event",
    "max_paper_notional_per_theme",
    "max_paper_notional_per_correlation_group",
)
ALLOCATION_ROW_DECIMAL_FIELDS = (
    "recommendation_score",
    "net_probability_edge",
    "executable_paper_shares",
    "side_price",
    "market_implied_probability",
    "requested_paper_notional",
    "allocated_paper_notional",
    "allocated_paper_shares",
)


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalSourceQueueSummary:
    generated_at: datetime
    config_version: str
    action_status: str
    ready_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperAutonomousAllocationProposalReport:
    generated_at: datetime
    config_version: str
    proposal_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperAutonomousAllocationProposalReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    screening_gate_generated_at: datetime
    screening_gate_config_version: str
    screening_gate_status: str
    screening_gate_recommended_next_step: str
    queue_risk_generated_at: datetime
    queue_risk_config_version: str
    queue_risk_status: str
    queue_risk_recommended_next_step: str
    source_queue_count: int
    source_queue_ready_count: int
    source_queue_watch_count: int
    source_queue_blocked_count: int
    allocation_report: PaperRecommendationAllocationReport
    source_queue_summaries: tuple[
        PaperAutonomousAllocationProposalSourceQueueSummary,
        ...,
    ]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class ProposalReportSubclass(PaperAutonomousAllocationProposalReport):
    pass


def _install_fake_reducer_module() -> None:
    module = ModuleType(REDUCER_MODULE_NAME)
    module.datetime = datetime
    module.Decimal = Decimal
    module.PaperRecommendationAllocationReport = PaperRecommendationAllocationReport
    PaperAutonomousAllocationProposalReasonCodeCount.__module__ = REDUCER_MODULE_NAME
    PaperAutonomousAllocationProposalSourceQueueSummary.__module__ = REDUCER_MODULE_NAME
    PaperAutonomousAllocationProposalReport.__module__ = REDUCER_MODULE_NAME
    module.PaperAutonomousAllocationProposalReasonCodeCount = (
        PaperAutonomousAllocationProposalReasonCodeCount
    )
    module.PaperAutonomousAllocationProposalSourceQueueSummary = (
        PaperAutonomousAllocationProposalSourceQueueSummary
    )
    module.PaperAutonomousAllocationProposalReport = (
        PaperAutonomousAllocationProposalReport
    )
    module.build_paper_autonomous_allocation_proposal_report = (
        lambda *args, **kwargs: None
    )
    sys.modules[REDUCER_MODULE_NAME] = module


@pytest.fixture(autouse=True)
def fake_reducer_module():
    previous = sys.modules.get(REDUCER_MODULE_NAME)
    _install_fake_reducer_module()
    try:
        yield
    finally:
        if previous is None:
            sys.modules.pop(REDUCER_MODULE_NAME, None)
        else:
            sys.modules[REDUCER_MODULE_NAME] = previous


def d(value: str) -> Decimal:
    return Decimal(value)


def _allocation_report(
    *,
    config_version: str = "allocation-v0",
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationAllocationReport:
    return build_paper_recommendation_allocation_report(
        (
            _input_row(
                "alpha-market",
                recommendation_score=d("0.600000"),
                net_probability_edge=d("0.100000"),
                executable_paper_shares=d("10.000000"),
                side_price=d("1.000000"),
                event_id="event-alpha",
                theme_id="theme-alpha",
                correlation_group="corr-alpha",
                reason_codes=("source_ready",),
            ),
        ),
        config=PaperRecommendationAllocationConfig(
            config_version=config_version,
            total_paper_budget=d("100.000000"),
            max_paper_notional_per_market=d("25.000000"),
            max_paper_notional_per_event=d("25.000000"),
            max_paper_notional_per_theme=d("25.000000"),
            max_paper_notional_per_correlation_group=d("25.000000"),
        ),
        generated_at=generated_at,
    )


def _reason_count(
    reason_code: str = "paper_autonomous_allocation_proposal_passed",
    report_count: int = 1,
) -> PaperAutonomousAllocationProposalReasonCodeCount:
    return PaperAutonomousAllocationProposalReasonCodeCount(
        reason_code=reason_code,
        report_count=report_count,
    )


def _source_summary() -> PaperAutonomousAllocationProposalSourceQueueSummary:
    return PaperAutonomousAllocationProposalSourceQueueSummary(
        generated_at=QUEUE_RISK_AT,
        config_version="action-gated-queue-v0",
        action_status="research_ready",
        ready_count=1,
    )


def _report(
    *,
    config_version: str = "paper-autonomous-allocation-proposal-v0",
    proposal_status: str = "pass",
    recommended_next_step: str = "review_paper_autonomous_allocation_proposal",
    reason_codes: tuple[str, ...] = (
        "paper_autonomous_allocation_proposal_passed",
    ),
    screening_gate_status: str = "pass",
    screening_gate_recommended_next_step: str = (
        "advance_paper_autonomous_screening_recommendations"
    ),
    queue_risk_status: str = "pass",
    queue_risk_recommended_next_step: str = "allocate_paper_research_queue",
    allocation_report: PaperRecommendationAllocationReport | None = None,
) -> PaperAutonomousAllocationProposalReport:
    return PaperAutonomousAllocationProposalReport(
        generated_at=GENERATED_AT,
        config_version=config_version,
        proposal_status=proposal_status,
        recommended_next_step=recommended_next_step,
        reason_code_counts=tuple(_reason_count(code) for code in reason_codes),
        reason_codes=reason_codes,
        screening_gate_generated_at=SCREENING_GATE_AT,
        screening_gate_config_version=(
            "paper-autonomous-screening-decision-support-gate-v0"
        ),
        screening_gate_status=screening_gate_status,
        screening_gate_recommended_next_step=screening_gate_recommended_next_step,
        queue_risk_generated_at=QUEUE_RISK_AT,
        queue_risk_config_version="action-gated-queue-risk-v0",
        queue_risk_status=queue_risk_status,
        queue_risk_recommended_next_step=queue_risk_recommended_next_step,
        source_queue_count=1,
        source_queue_ready_count=1,
        source_queue_watch_count=0,
        source_queue_blocked_count=0,
        allocation_report=allocation_report or _allocation_report(),
        source_queue_summaries=(_source_summary(),),
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _without_hard_flags(value: dict[str, object]) -> dict[str, object]:
    return {
        key: item
        for key, item in value.items()
        if key not in ("paper_only", "report_only", "readonly")
    }


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


def _json_clone(value: object) -> object:
    return json.loads(json.dumps(value, allow_nan=False))


def _legacy_decimal_string(value: object) -> str:
    text = format(Decimal(str(value)), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _compact_allocation_report_decimals(report: PaperRecommendationAllocationReport) -> None:
    for field_name in ALLOCATION_REPORT_DECIMAL_FIELDS:
        object.__setattr__(
            report,
            field_name,
            Decimal(_legacy_decimal_string(getattr(report, field_name))),
        )
    for row in report.rows:
        for field_name in ALLOCATION_ROW_DECIMAL_FIELDS:
            value = getattr(row, field_name)
            if value is not None:
                object.__setattr__(row, field_name, Decimal(_legacy_decimal_string(value)))


def _legacy_allocation_decimal_payload(
    payload_json: dict[str, object],
) -> dict[str, object]:
    payload = _json_clone(payload_json)
    assert isinstance(payload, dict)
    allocation_report = payload["allocation_report"]
    assert isinstance(allocation_report, dict)
    for field_name in ALLOCATION_REPORT_DECIMAL_FIELDS:
        allocation_report[field_name] = _legacy_decimal_string(allocation_report[field_name])
    allocation_rows = allocation_report["rows"]
    assert isinstance(allocation_rows, list)
    for allocation_row in allocation_rows:
        assert isinstance(allocation_row, dict)
        for field_name in ALLOCATION_ROW_DECIMAL_FIELDS:
            value = allocation_row.get(field_name)
            if value is not None:
                allocation_row[field_name] = _legacy_decimal_string(value)
    return payload


def _row_from_self_hashed_payload(row: object, payload_json: dict[str, object]) -> object:
    allocation_report = payload_json["allocation_report"]
    assert isinstance(allocation_report, dict)
    allocation_rows = allocation_report["rows"]
    assert isinstance(allocation_rows, list)
    return type(row)(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload_json),
            "payload_json": payload_json,
            "allocation_rows_json": allocation_rows,
        },
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("proposal DB JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_proposal_db_row_serializes_payload_and_round_trips() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousAllocationProposalDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-autonomous-allocation-proposal-v0"
    assert row.proposal_status == "pass"
    assert row.recommended_next_step == (
        "review_paper_autonomous_allocation_proposal"
    )
    assert row.reason_codes_json == [
        "paper_autonomous_allocation_proposal_passed",
    ]
    assert row.screening_gate_generated_at == SCREENING_GATE_AT
    assert row.screening_gate_config_version == (
        "paper-autonomous-screening-decision-support-gate-v0"
    )
    assert row.screening_gate_status == "pass"
    assert row.queue_risk_generated_at == QUEUE_RISK_AT
    assert row.queue_risk_config_version == "action-gated-queue-risk-v0"
    assert row.queue_risk_status == "pass"
    assert row.source_queue_report_count == 1
    assert row.source_queue_ready_count == 1
    assert row.source_queue_watch_count == 0
    assert row.source_queue_blocked_count == 0
    assert row.allocation_config_version == "allocation-v0"
    assert row.allocation_input_count == 1
    assert row.allocation_row_count == 1
    assert row.allocation_allocated_count == 1
    assert row.allocation_capped_count == 0
    assert row.allocation_no_budget_count == 0
    assert row.allocation_non_recommend_count == 0
    assert row.allocation_skipped_count == 0
    assert row.allocation_total_requested_paper_notional == d("10.000000")
    assert row.allocation_total_allocated_paper_notional == d("10.000000")
    assert row.allocation_remaining_paper_budget == d("90.000000")
    assert row.allocation_total_paper_budget == d("100.000000")
    assert row.allocation_rows_json == row.payload_json["allocation_report"]["rows"]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-23T20:00:00+00:00"
    assert row.payload_json["allocation_report"]["rows"][0][
        "allocated_paper_notional"
    ] == "10.000000"
    assert row.payload_json["reason_code_counts"][0]["readonly"] is True
    _assert_no_floats(row.reason_code_counts_json)
    _assert_no_floats(row.allocation_rows_json)
    _assert_no_floats(row.payload_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_autonomous_allocation_proposal_report_to_db_row(report) == row
    assert codec.paper_autonomous_allocation_proposal_report_from_db_row(row) == report


def test_proposal_db_row_writes_allocation_decimals_as_fixed_six_places() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    report = _report()
    _compact_allocation_report_decimals(report.allocation_report)

    row = codec.to_db_row(report)
    allocation_report_json = row.payload_json["allocation_report"]
    assert isinstance(allocation_report_json, dict)
    allocation_rows_json = allocation_report_json["rows"]
    assert isinstance(allocation_rows_json, list)
    allocation_row_json = allocation_rows_json[0]
    assert isinstance(allocation_row_json, dict)

    for field_name in ALLOCATION_REPORT_DECIMAL_FIELDS:
        value = allocation_report_json[field_name]
        assert isinstance(value, str)
        assert FIXED_SIX_DECIMAL_RE.fullmatch(value)
        assert str(getattr(row, f"allocation_{field_name}")) == value
    for field_name in ALLOCATION_ROW_DECIMAL_FIELDS:
        value = allocation_row_json[field_name]
        if value is not None:
            assert isinstance(value, str)
            assert FIXED_SIX_DECIMAL_RE.fullmatch(value)
    assert row.allocation_rows_json == allocation_rows_json
    assert codec.from_db_row(row) == report


def test_proposal_from_db_row_recovers_equivalent_legacy_self_hashed_decimal_payload() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    report = _report()
    row = codec.to_db_row(report)
    payload = _legacy_allocation_decimal_payload(row.payload_json)

    legacy_row = _row_from_self_hashed_payload(row, payload)

    assert legacy_row.report_sha256 == _canonical_payload_sha256(payload)
    assert codec.from_db_row(legacy_row) == report


def test_proposal_from_db_row_rejects_stale_hash_after_legacy_decimal_normalization() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())
    payload = _legacy_allocation_decimal_payload(row.payload_json)
    allocation_report = payload["allocation_report"]
    assert isinstance(allocation_report, dict)
    allocation_rows = allocation_report["rows"]
    assert isinstance(allocation_rows, list)
    malformed = _bypassed_row(
        row,
        payload_json=payload,
        allocation_rows_json=allocation_rows,
    )

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("payload_path", "bad_value", "message"),
    (
        (
            ("allocation_report", "total_paper_budget"),
            "100.0000001",
            "six decimal places",
        ),
        (
            ("allocation_report", "rows", 0, "allocated_paper_notional"),
            "10.0000001",
            "six decimal places",
        ),
    ),
)
def test_proposal_from_db_row_rejects_value_changing_overprecision_decimal_payloads(
    payload_path: tuple[object, ...],
    bad_value: str,
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())
    payload = _json_clone(row.payload_json)
    assert isinstance(payload, dict)
    target: object = payload
    for key in payload_path[:-1]:
        if isinstance(target, dict):
            target = target[key]
        elif isinstance(target, list) and isinstance(key, int):
            target = target[key]
        else:
            raise AssertionError("bad test path")
    assert isinstance(target, dict)
    target[payload_path[-1]] = bad_value
    allocation_report = payload["allocation_report"]
    assert isinstance(allocation_report, dict)
    allocation_rows = allocation_report["rows"]
    assert isinstance(allocation_rows, list)
    malformed = _bypassed_row(
        row,
        report_sha256=_canonical_payload_sha256(payload),
        payload_json=payload,
        allocation_rows_json=allocation_rows,
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_proposal_from_db_row_rejects_non_allowlisted_decimal_like_payload_strings() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())
    payload = _json_clone(row.payload_json)
    assert isinstance(payload, dict)
    source_queue_summaries = payload["source_queue_summaries"]
    assert isinstance(source_queue_summaries, list)
    source_summary = source_queue_summaries[0]
    assert isinstance(source_summary, dict)
    source_summary["config_version"] = "1.000000"
    malformed = _bypassed_row(
        row,
        report_sha256=_canonical_payload_sha256(payload),
        payload_json=payload,
    )

    with pytest.raises(ValueError, match="not an allowed Decimal path"):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("raw_value", "hash_value", "message"),
    (
        (Decimal("100.000000"), "100.000000", "raw Decimal"),
        (GENERATED_AT, GENERATED_AT.isoformat(), "raw datetime"),
        (0.5, "0.500000", "float"),
    ),
)
def test_proposal_from_db_row_rejects_raw_json_values_before_hashing(
    raw_value: object,
    hash_value: object,
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())
    payload = _json_clone(row.payload_json)
    hash_payload = _json_clone(row.payload_json)
    assert isinstance(payload, dict)
    assert isinstance(hash_payload, dict)
    allocation_report = payload["allocation_report"]
    hash_allocation_report = hash_payload["allocation_report"]
    assert isinstance(allocation_report, dict)
    assert isinstance(hash_allocation_report, dict)
    allocation_report["total_paper_budget"] = raw_value
    hash_allocation_report["total_paper_budget"] = hash_value
    malformed = _bypassed_row(
        row,
        report_sha256=_canonical_payload_sha256(hash_payload),
        payload_json=payload,
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_proposal_db_row_hash_is_deterministic_for_equivalent_reports() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    report = _report()
    same_report = PaperAutonomousAllocationProposalReport(**report.__dict__)
    different_report = _report(
        config_version="paper-autonomous-allocation-proposal-v1",
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_proposal_db_row_is_frozen() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_proposal_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    with pytest.raises(ValueError, match="PaperAutonomousAllocationProposalReport"):
        codec.to_db_row(object())

    report = _report()
    subclass = ProposalReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="PaperAutonomousAllocationProposalReport"):
        codec.to_db_row(subclass)


def test_proposal_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())

    class ProposalDbRowSubclass(codec.PaperAutonomousAllocationProposalDbRow):
        pass

    with pytest.raises(ValueError, match="PaperAutonomousAllocationProposalDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperAutonomousAllocationProposalDbRow"):
        codec.from_db_row(ProposalDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_proposal_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_proposal_db_row_rejects_false_nested_allocation_row_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    report = _report()
    object.__setattr__(report.allocation_report.rows[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


def test_proposal_db_row_rejects_corrupted_stored_payload_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())
    allocation_report = {
        **row.payload_json["allocation_report"],
        "rows": [
            {
                **row.payload_json["allocation_report"]["rows"][0],
                "paper_only": False,
            },
        ],
    }
    payload = {**row.payload_json, "allocation_report": allocation_report}
    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperAutonomousAllocationProposalDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
                "allocation_rows_json": allocation_report["rows"],
            },
        )


@pytest.mark.parametrize(
    "nested_field",
    (
        "reason_code_counts",
        "allocation_report",
        "allocation_report.rows",
        "source_queue_summaries",
    ),
)
def test_proposal_db_row_rejects_nested_json_objects_missing_all_hard_flags(
    nested_field: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())
    payload = row.payload_json
    overrides: dict[str, object]
    if nested_field == "reason_code_counts":
        reason_code_counts = [
            _without_hard_flags(row.payload_json["reason_code_counts"][0]),
        ]
        payload = {**row.payload_json, "reason_code_counts": reason_code_counts}
        overrides = {"reason_code_counts_json": reason_code_counts}
    elif nested_field == "allocation_report":
        payload = {
            **row.payload_json,
            "allocation_report": _without_hard_flags(
                row.payload_json["allocation_report"],
            ),
        }
        overrides = {}
    elif nested_field == "allocation_report.rows":
        allocation_rows = [
            _without_hard_flags(
                row.payload_json["allocation_report"]["rows"][0],
            ),
        ]
        allocation_report = {
            **row.payload_json["allocation_report"],
            "rows": allocation_rows,
        }
        payload = {**row.payload_json, "allocation_report": allocation_report}
        overrides = {"allocation_rows_json": allocation_rows}
    else:
        payload = {
            **row.payload_json,
            "source_queue_summaries": [
                _without_hard_flags(row.payload_json["source_queue_summaries"][0]),
            ],
        }
        overrides = {}

    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperAutonomousAllocationProposalDbRow(
            **{
                **_row_values(row),
                **overrides,
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_proposal_from_db_row_defends_against_bypassed_payload_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())
    allocation_report = {
        **row.payload_json["allocation_report"],
        "rows": [
            {
                **row.payload_json["allocation_report"]["rows"][0],
                "paper_only": False,
            },
        ],
    }
    payload = {**row.payload_json, "allocation_report": allocation_report}
    malformed = _bypassed_row(
        row,
        report_sha256=_canonical_payload_sha256(payload),
        payload_json=payload,
        allocation_rows_json=allocation_report["rows"],
    )

    with pytest.raises(ValueError, match="paper_only"):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_proposal_db_row_rejects_non_materialized_payload_hash_mismatch() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "source_queue_summaries": [
            {
                **row.payload_json["source_queue_summaries"][0],
                "readonly": False,
            },
        ],
    }
    with pytest.raises(ValueError, match="report_sha256"):
        codec.PaperAutonomousAllocationProposalDbRow(
            **{
                **_row_values(row),
                "payload_json": payload,
            },
        )


def test_proposal_from_db_row_defends_against_bypassed_payload_hash_mismatch() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "source_queue_summaries": [
            {
                **row.payload_json["source_queue_summaries"][0],
                "readonly": False,
            },
        ],
    }
    malformed = _bypassed_row(row, payload_json=payload)

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_proposal_db_row_rejects_recursive_floats_in_json_payloads() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="reason_code_counts_json"):
        replace(
            row,
            reason_code_counts_json=[
                {**row.reason_code_counts_json[0], "report_count": 1.0},
            ],
        )
    with pytest.raises(ValueError, match="allocation_rows_json"):
        replace(
            row,
            allocation_rows_json=[
                {**row.allocation_rows_json[0], "side_price": 1.0},
            ],
        )
    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})


PROPOSAL_MATERIALIZED_MISMATCH_CASES = (
    ({"report_sha256": "b" * 64}, "report_sha256"),
    ({"generated_at": datetime(2026, 6, 23, 20, 1, tzinfo=UTC)}, "generated_at"),
    ({"config_version": "paper-autonomous-allocation-proposal-v1"}, "config_version"),
    (
        {
            "proposal_status": "watch",
            "recommended_next_step": "hold_paper_autonomous_allocation_proposal",
        },
        "proposal_status",
    ),
    ({"reason_codes_json": ["queue_risk_watch"]}, "reason_codes_json"),
    ({"screening_gate_status": "watch"}, "screening_gate_status"),
    ({"queue_risk_status": "watch"}, "queue_risk_status"),
    ({"source_queue_report_count": 2}, "source_queue_report_count"),
    ({"allocation_config_version": "allocation-v1"}, "allocation_config_version"),
    ({"allocation_allocated_count": 0}, "allocation_allocated_count"),
    (
        {"allocation_total_allocated_paper_notional": d("9.000000")},
        "allocation_total_allocated_paper_notional",
    ),
    ({"allocation_rows_json": []}, "allocation_rows_json"),
)


@pytest.mark.parametrize(("overrides", "message"), PROPOSAL_MATERIALIZED_MISMATCH_CASES)
def test_proposal_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousAllocationProposalDbRow(
            **{**_row_values(row), **overrides},
        )


@pytest.mark.parametrize(("overrides", "message"), PROPOSAL_MATERIALIZED_MISMATCH_CASES)
def test_proposal_from_db_row_defends_against_bypassed_materialized_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())
    malformed = _bypassed_row(row, **overrides)

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_proposal_db_row_replace_rejects_payload_mismatches() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="source_queue_ready_count"):
        replace(row, source_queue_ready_count=2)
    with pytest.raises(ValueError, match="allocation_total_paper_budget"):
        replace(row, allocation_total_paper_budget=d("99.000000"))

    payload = {key: value for key, value in row.payload_json.items() if key != "readonly"}
    with pytest.raises(ValueError, match="readonly"):
        replace(
            row,
            report_sha256=_canonical_payload_sha256(payload),
            payload_json=payload,
        )


@pytest.mark.parametrize(
    ("status", "next_step"),
    (
        ("pass", "hold_paper_autonomous_allocation_proposal"),
        ("watch", "review_paper_autonomous_allocation_proposal"),
        ("blocked", "hold_paper_autonomous_allocation_proposal"),
    ),
)
def test_proposal_db_row_rejects_proposal_status_next_step_mismatches(
    status: str,
    next_step: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    with pytest.raises(ValueError, match="recommended_next_step"):
        codec.to_db_row(
            _report(
                proposal_status=status,
                recommended_next_step=next_step,
            ),
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"proposal_status": "paused"}, "proposal_status"),
        ({"screening_gate_status": "paused"}, "screening_gate_status"),
        ({"queue_risk_status": "paused"}, "queue_risk_status"),
        ({"source_queue_report_count": True}, "source_queue_report_count"),
        ({"allocation_total_paper_budget": d("-1.000000")}, "allocation_total_paper_budget"),
        ({"reason_codes_json": "reason"}, "reason_codes_json"),
        ({"reason_code_counts_json": {"reason_code": "reason"}}, "reason_code_counts_json"),
        ({"allocation_rows_json": {"market_slug": "alpha"}}, "allocation_rows_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_proposal_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousAllocationProposalDbRow(
            **{**_row_values(row), **overrides},
        )


def test_proposal_db_row_module_is_pure_codec() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row as codec

    assert codec.__name__.endswith("_db_row")
    source = Path(
        "src/polymarket_alpha_lab/paper_autonomous_allocation_proposal_db_row.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
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
