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


REDUCER_MODULE_NAME = (
    "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate"
)
GENERATED_AT = datetime(2026, 6, 23, 19, 0, tzinfo=UTC)
OPERATOR_AT = datetime(2026, 6, 23, 18, 40, tzinfo=UTC)
QUEUE_AT = datetime(2026, 6, 23, 18, 45, tzinfo=UTC)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.report_count) is not int:
            raise ValueError("report_count must be an int")
        if self.paper_only is not True or self.report_only is not True or self.readonly is not True:
            raise ValueError("reason count must remain paper-only/report-only/readonly")


@dataclass(frozen=True)
class PaperAutonomousScreeningDecisionSupportGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperAutonomousScreeningDecisionSupportGateReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    operator_flow_gate_config_version: str
    operator_flow_gate_generated_at: datetime
    operator_flow_gate_status: str
    operator_flow_recommended_next_step: str
    queue_priority_generated_at: datetime
    queue_risk_generated_at: datetime
    queue_risk_config_version: str
    queue_risk_status: str
    queue_risk_recommended_next_step: str
    queue_source_report_count: int
    queue_research_ready_count: int
    queue_watch_count: int
    queue_blocked_count: int
    queue_candidate_count: int
    queue_ready_count: int
    queue_candidate_watch_count: int
    queue_candidate_blocked_count: int
    queue_total_ready_notional: Decimal
    queue_largest_ready_notional: Decimal
    queue_top_research_priority_score: Decimal
    queue_average_research_priority_score: Decimal
    trend_source_snapshot_count: int | None
    trend_latest_risk_status: str | None
    trend_consecutive_latest_watch_count: int | None
    trend_consecutive_latest_blocked_count: int | None
    trend_duplicate_generated_at_count: int | None
    rank_stability_status: str | None
    rank_stable_ready_count: int | None
    rank_unstable_ready_count: int | None
    rank_blocked_count: int | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "queue_source_report_count",
            "queue_research_ready_count",
            "queue_watch_count",
            "queue_blocked_count",
            "queue_candidate_count",
            "queue_ready_count",
            "queue_candidate_watch_count",
            "queue_candidate_blocked_count",
        ):
            if type(getattr(self, field_name)) is not int:
                raise ValueError(f"{field_name} must be an int")
        for field_name in (
            "trend_source_snapshot_count",
            "trend_consecutive_latest_watch_count",
            "trend_consecutive_latest_blocked_count",
            "trend_duplicate_generated_at_count",
            "rank_stable_ready_count",
            "rank_unstable_ready_count",
            "rank_blocked_count",
        ):
            value = getattr(self, field_name)
            if value is not None and type(value) is not int:
                raise ValueError(f"{field_name} must be an int")
        for field_name in (
            "queue_total_ready_notional",
            "queue_largest_ready_notional",
            "queue_top_research_priority_score",
            "queue_average_research_priority_score",
        ):
            value = getattr(self, field_name)
            if type(value) is not Decimal:
                raise ValueError(f"{field_name} must be a Decimal")
            object.__setattr__(self, field_name, value.quantize(Decimal("0.000001")))
        if self.paper_only is not True or self.report_only is not True or self.readonly is not True:
            raise ValueError("report must remain paper-only/report-only/readonly")


class GateReportSubclass(PaperAutonomousScreeningDecisionSupportGateReport):
    pass


def _install_fake_reducer_module() -> None:
    module = ModuleType(REDUCER_MODULE_NAME)
    module.datetime = datetime
    module.Decimal = Decimal
    module.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION = (
        "paper-autonomous-screening-decision-support-gate-v0"
    )
    module.GATE_STATUSES = ("pass", "watch", "blocked")
    PaperAutonomousScreeningDecisionSupportGateReasonCodeCount.__module__ = (
        REDUCER_MODULE_NAME
    )
    PaperAutonomousScreeningDecisionSupportGateReport.__module__ = REDUCER_MODULE_NAME
    module.PaperAutonomousScreeningDecisionSupportGateReasonCodeCount = (
        PaperAutonomousScreeningDecisionSupportGateReasonCodeCount
    )
    module.PaperAutonomousScreeningDecisionSupportGateReport = (
        PaperAutonomousScreeningDecisionSupportGateReport
    )
    module.build_paper_autonomous_screening_decision_support_gate_report = (
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


def _reason_count(
    reason_code: str = "paper_autonomous_screening_decision_support_gate_passed",
    report_count: int = 1,
) -> PaperAutonomousScreeningDecisionSupportGateReasonCodeCount:
    return PaperAutonomousScreeningDecisionSupportGateReasonCodeCount(
        reason_code=reason_code,
        report_count=report_count,
    )


def _report(
    *,
    config_version: str = "paper-autonomous-screening-decision-support-gate-v0",
    gate_status: str = "pass",
    recommended_next_step: str = (
        "advance_paper_autonomous_screening_recommendations"
    ),
    reason_codes: tuple[str, ...] = (
        "paper_autonomous_screening_decision_support_gate_passed",
    ),
    trend_source_snapshot_count: int | None = 2,
    trend_latest_risk_status: str | None = "pass",
    rank_stability_status: str | None = "stable",
) -> PaperAutonomousScreeningDecisionSupportGateReport:
    return PaperAutonomousScreeningDecisionSupportGateReport(
        generated_at=GENERATED_AT,
        config_version=config_version,
        gate_status=gate_status,
        recommended_next_step=recommended_next_step,
        reason_code_counts=tuple(_reason_count(code) for code in reason_codes),
        reason_codes=reason_codes,
        operator_flow_gate_config_version=(
            "paper-research-packet-operator-flow-db-history-gate-v0"
        ),
        operator_flow_gate_generated_at=OPERATOR_AT,
        operator_flow_gate_status="pass",
        operator_flow_recommended_next_step=(
            "allow_paper_autonomous_screening_decision_support"
        ),
        queue_priority_generated_at=QUEUE_AT,
        queue_risk_generated_at=QUEUE_AT,
        queue_risk_config_version="action-gated-queue-risk-v0",
        queue_risk_status="pass",
        queue_risk_recommended_next_step="allocate_paper_research_queue",
        queue_source_report_count=1,
        queue_research_ready_count=1,
        queue_watch_count=0,
        queue_blocked_count=0,
        queue_candidate_count=1,
        queue_ready_count=1,
        queue_candidate_watch_count=0,
        queue_candidate_blocked_count=0,
        queue_total_ready_notional=Decimal("10.000000"),
        queue_largest_ready_notional=Decimal("10.000000"),
        queue_top_research_priority_score=Decimal("4.700000"),
        queue_average_research_priority_score=Decimal("4.700000"),
        trend_source_snapshot_count=trend_source_snapshot_count,
        trend_latest_risk_status=trend_latest_risk_status,
        trend_consecutive_latest_watch_count=0
        if trend_source_snapshot_count is not None
        else None,
        trend_consecutive_latest_blocked_count=0
        if trend_source_snapshot_count is not None
        else None,
        trend_duplicate_generated_at_count=1
        if trend_source_snapshot_count is not None
        else None,
        rank_stability_status=rank_stability_status,
        rank_stable_ready_count=1 if rank_stability_status is not None else None,
        rank_unstable_ready_count=0 if rank_stability_status is not None else None,
        rank_blocked_count=0 if rank_stability_status is not None else None,
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _bypassed_row(row: object, **overrides: object) -> object:
    values = _row_values(row)
    values.update(overrides)
    bypassed = object.__new__(type(row))
    for field_name, value in values.items():
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


def _without_hard_flags(value: dict[str, object]) -> dict[str, object]:
    return {
        key: item
        for key, item in value.items()
        if key not in {"paper_only", "report_only", "readonly"}
    }


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("autonomous screening decision-support gate JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_autonomous_screening_gate_db_row_serializes_payload_and_round_trips() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousScreeningDecisionSupportGateDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "paper-autonomous-screening-decision-support-gate-v0"
    assert row.gate_status == "pass"
    assert row.recommended_next_step == (
        "advance_paper_autonomous_screening_recommendations"
    )
    assert row.reason_codes_json == [
        "paper_autonomous_screening_decision_support_gate_passed",
    ]
    assert row.operator_flow_gate_config_version == (
        "paper-research-packet-operator-flow-db-history-gate-v0"
    )
    assert row.operator_flow_gate_generated_at == OPERATOR_AT
    assert row.operator_flow_gate_status == "pass"
    assert row.queue_risk_config_version == "action-gated-queue-risk-v0"
    assert row.queue_risk_status == "pass"
    assert row.queue_source_report_count == 1
    assert row.queue_candidate_count == 1
    assert row.queue_total_ready_notional == Decimal("10.000000")
    assert row.queue_top_research_priority_score == Decimal("4.700000")
    assert row.trend_source_snapshot_count == 2
    assert row.trend_duplicate_generated_at_count == 1
    assert row.rank_stability_status == "stable"
    assert row.rank_stable_ready_count == 1
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-23T19:00:00+00:00"
    assert row.payload_json["queue_total_ready_notional"] == "10.000000"
    assert row.payload_json["reason_code_counts"][0]["readonly"] is True
    _assert_no_floats(row.reason_code_counts_json)
    _assert_no_floats(row.payload_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_autonomous_screening_decision_support_gate_report_to_db_row(
        report,
    ) == row
    assert codec.paper_autonomous_screening_decision_support_gate_report_from_db_row(
        row,
    ) == report


def test_autonomous_screening_gate_db_row_hash_is_deterministic() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    report = _report()
    same_report = PaperAutonomousScreeningDecisionSupportGateReport(
        **report.__dict__,
    )
    different_report = _report(
        config_version="paper-autonomous-screening-decision-support-gate-v1",
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_autonomous_screening_gate_db_row_writes_fixed_six_place_decimal_payloads() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    report = _report()
    object.__setattr__(report, "queue_total_ready_notional", Decimal("10"))
    object.__setattr__(report, "queue_largest_ready_notional", Decimal("10.0"))
    object.__setattr__(report, "queue_top_research_priority_score", Decimal("4.7"))
    object.__setattr__(
        report,
        "queue_average_research_priority_score",
        Decimal("4.7000"),
    )

    row = codec.to_db_row(report)

    assert row.payload_json["queue_total_ready_notional"] == "10.000000"
    assert row.payload_json["queue_largest_ready_notional"] == "10.000000"
    assert row.payload_json["queue_top_research_priority_score"] == "4.700000"
    assert row.payload_json["queue_average_research_priority_score"] == "4.700000"


def test_autonomous_screening_gate_db_row_rejects_overprecision_decimal_writes_without_rounding() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    report = _report()
    object.__setattr__(report, "queue_total_ready_notional", Decimal("10.0000001"))

    with pytest.raises(ValueError, match="queue_total_ready_notional|six decimal"):
        codec.to_db_row(report)


def test_autonomous_screening_gate_db_row_preserves_absent_optional_inputs() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    report = _report(
        gate_status="blocked",
        recommended_next_step="block_paper_autonomous_screening_recommendations",
        reason_codes=("queue_risk_blocked",),
        trend_source_snapshot_count=None,
        trend_latest_risk_status=None,
        rank_stability_status=None,
    )

    row = codec.to_db_row(report)

    assert row.gate_status == "blocked"
    assert row.trend_source_snapshot_count is None
    assert row.trend_latest_risk_status is None
    assert row.rank_stability_status is None
    assert row.rank_stable_ready_count is None
    assert codec.from_db_row(row) == report


def test_autonomous_screening_gate_db_row_is_frozen() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_autonomous_screening_gate_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    with pytest.raises(ValueError, match="PaperAutonomousScreeningDecisionSupportGateReport"):
        codec.to_db_row(object())

    report = _report()
    subclass = GateReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="PaperAutonomousScreeningDecisionSupportGateReport"):
        codec.to_db_row(subclass)


def test_autonomous_screening_gate_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())

    class GateDbRowSubclass(codec.PaperAutonomousScreeningDecisionSupportGateDbRow):
        pass

    with pytest.raises(ValueError, match="PaperAutonomousScreeningDecisionSupportGateDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperAutonomousScreeningDecisionSupportGateDbRow"):
        codec.from_db_row(GateDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_autonomous_screening_gate_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_autonomous_screening_gate_db_row_rejects_false_nested_reason_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    report = _report()
    object.__setattr__(report.reason_code_counts[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


def test_autonomous_screening_gate_db_row_rejects_corrupted_stored_payload_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "reason_code_counts": [
            {
                **row.payload_json["reason_code_counts"][0],
                "paper_only": False,
            },
        ],
    }
    values = {
        **_row_values(row),
        "report_sha256": _canonical_payload_sha256(payload),
        "payload_json": payload,
        "reason_code_counts_json": payload["reason_code_counts"],
    }

    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperAutonomousScreeningDecisionSupportGateDbRow(**values)
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, **values)

    malformed = object.__new__(codec.PaperAutonomousScreeningDecisionSupportGateDbRow)
    for field_name, value in values.items():
        object.__setattr__(malformed, field_name, value)

    with pytest.raises(ValueError, match="paper_only"):
        codec.from_db_row(malformed)


def test_autonomous_screening_gate_db_row_rejects_recursive_floats_in_json_payloads() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="reason_code_counts_json"):
        replace(
            row,
            reason_code_counts_json=[
                {**row.reason_code_counts_json[0], "report_count": 1.0},
            ],
        )
    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})


@pytest.mark.parametrize(
    ("payload_key", "raw_value", "message"),
    (
        ("queue_total_ready_notional", Decimal("10.000000"), "Decimal"),
        ("queue_total_ready_notional", 10.0, "float"),
        ("generated_at", GENERATED_AT, "datetime"),
    ),
)
def test_autonomous_screening_gate_db_row_rejects_raw_non_json_payload_values(
    payload_key: str,
    raw_value: object,
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = {**row.payload_json, payload_key: raw_value}

    with pytest.raises(ValueError, match=f"payload_json.*{message}"):
        codec.PaperAutonomousScreeningDecisionSupportGateDbRow(
            **{**_row_values(row), "payload_json": payload},
        )

    malformed = _bypassed_row(row, payload_json=payload)
    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_autonomous_screening_gate_db_row_rejects_stale_raw_payload_hash() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = {**row.payload_json, "queue_source_report_count": 2}

    with pytest.raises(ValueError, match="report_sha256"):
        codec.PaperAutonomousScreeningDecisionSupportGateDbRow(
            **{**_row_values(row), "payload_json": payload},
        )


def test_autonomous_screening_gate_db_row_accepts_self_hashed_legacy_decimal_payload() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "queue_total_ready_notional": "10",
        "queue_largest_ready_notional": "10.0",
        "queue_top_research_priority_score": "4.7",
        "queue_average_research_priority_score": "4.7000",
    }

    legacy_row = codec.PaperAutonomousScreeningDecisionSupportGateDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload),
            "queue_total_ready_notional": Decimal("10"),
            "queue_largest_ready_notional": Decimal("10.0"),
            "queue_top_research_priority_score": Decimal("4.7"),
            "queue_average_research_priority_score": Decimal("4.7000"),
            "payload_json": payload,
        },
    )

    assert codec.from_db_row(legacy_row) == _report()


def test_autonomous_screening_gate_from_db_row_accepts_bypassed_self_hashed_legacy_decimal_payload() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "queue_total_ready_notional": "10",
        "queue_largest_ready_notional": "10.0",
        "queue_top_research_priority_score": "4.7",
        "queue_average_research_priority_score": "4.7000",
    }
    legacy_row = _bypassed_row(
        row,
        report_sha256=_canonical_payload_sha256(payload),
        queue_total_ready_notional=Decimal("10"),
        queue_largest_ready_notional=Decimal("10.0"),
        queue_top_research_priority_score=Decimal("4.7"),
        queue_average_research_priority_score=Decimal("4.7000"),
        payload_json=payload,
    )

    assert codec.from_db_row(legacy_row) == _report()  # type: ignore[arg-type]


def test_autonomous_screening_gate_from_db_row_rejects_stale_legacy_decimal_payload_hash() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = {**row.payload_json, "queue_total_ready_notional": "10"}
    malformed = _bypassed_row(
        row,
        queue_total_ready_notional=Decimal("10"),
        payload_json=payload,
    )

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_autonomous_screening_gate_from_db_row_rejects_value_changing_legacy_decimal_payload() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = {**row.payload_json, "queue_total_ready_notional": "10.000001"}
    malformed = _bypassed_row(
        row,
        report_sha256=_canonical_payload_sha256(payload),
        payload_json=payload,
    )

    with pytest.raises(ValueError, match="queue_total_ready_notional|payload_json"):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_autonomous_screening_gate_from_db_row_rejects_overprecision_legacy_decimal_payload() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = {**row.payload_json, "queue_total_ready_notional": "10.0000000"}
    malformed = _bypassed_row(
        row,
        report_sha256=_canonical_payload_sha256(payload),
        payload_json=payload,
    )

    with pytest.raises(ValueError, match="queue_total_ready_notional|six decimal|payload_json"):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_autonomous_screening_gate_from_db_row_rejects_non_allowlisted_decimal_like_payload() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = {**row.payload_json, "config_version": "1.0"}
    malformed = _bypassed_row(
        row,
        report_sha256=_canonical_payload_sha256(payload),
        config_version="1.0",
        payload_json=payload,
    )

    with pytest.raises(ValueError, match="config_version|Decimal|payload_json"):
        codec.from_db_row(malformed)  # type: ignore[arg-type]


def test_autonomous_screening_gate_db_row_rejects_self_hashed_bool_payload_int_count() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "queue_source_report_count": True,
    }

    with pytest.raises(ValueError, match="queue_source_report_count|payload_json"):
        codec.PaperAutonomousScreeningDecisionSupportGateDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_autonomous_screening_gate_db_row_rejects_self_hashed_reason_count_missing_hard_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    reason_code_counts = [
        _without_hard_flags(row.payload_json["reason_code_counts"][0]),
    ]
    payload = {**row.payload_json, "reason_code_counts": reason_code_counts}

    with pytest.raises(ValueError, match="reason_code_counts|paper_only|payload_json"):
        codec.PaperAutonomousScreeningDecisionSupportGateDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "reason_code_counts_json": reason_code_counts,
                "payload_json": payload,
            },
        )


def test_autonomous_screening_gate_db_row_rejects_missing_nullable_payload_key() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(
        _report(
            gate_status="blocked",
            recommended_next_step="block_paper_autonomous_screening_recommendations",
            reason_codes=("queue_risk_blocked",),
            trend_source_snapshot_count=None,
            trend_latest_risk_status=None,
            rank_stability_status=None,
        ),
    )
    payload = {
        key: value
        for key, value in row.payload_json.items()
        if key != "trend_latest_risk_status"
    }

    with pytest.raises(ValueError, match="trend_latest_risk_status|payload_json"):
        codec.PaperAutonomousScreeningDecisionSupportGateDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_autonomous_screening_gate_from_db_row_rejects_bypassed_recursive_float_payload() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    malformed = object.__new__(
        codec.PaperAutonomousScreeningDecisionSupportGateDbRow,
    )
    for field_name, value in _row_values(row).items():
        object.__setattr__(malformed, field_name, value)
    object.__setattr__(
        malformed,
        "payload_json",
        {**row.payload_json, "bad_float": 0.1},
    )

    with pytest.raises(ValueError, match="float|payload_json"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 23, 19, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-autonomous-screening-gate-v1"}, "config_version"),
        ({"gate_status": "watch"}, "gate_status"),
        ({"recommended_next_step": "throttle_paper_autonomous_screening_recommendations"}, "recommended_next_step"),
        ({"reason_codes_json": ["queue_risk_watch"]}, "reason_codes_json"),
        ({"operator_flow_gate_config_version": "operator-flow-gate-v1"}, "operator_flow_gate_config_version"),
        ({"operator_flow_gate_status": "watch"}, "operator_flow_gate_status"),
        ({"queue_risk_config_version": "action-gated-queue-risk-v1"}, "queue_risk_config_version"),
        ({"queue_risk_status": "watch"}, "queue_risk_status"),
        ({"queue_source_report_count": 2}, "queue_source_report_count"),
        ({"queue_total_ready_notional": Decimal("11.000000")}, "queue_total_ready_notional"),
        ({"trend_duplicate_generated_at_count": 2}, "trend_duplicate_generated_at_count"),
        ({"rank_stability_status": "watch"}, "rank_stability_status"),
    ),
)
def test_autonomous_screening_gate_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousScreeningDecisionSupportGateDbRow(
            **{**_row_values(row), **overrides},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"queue_ready_count": 2}, "queue_ready_count"),
        ({"reason_code_counts_json": []}, "reason_code_counts_json"),
    ),
)
def test_autonomous_screening_gate_db_row_replace_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        replace(row, **overrides)


def test_autonomous_screening_gate_db_row_from_db_row_rejects_bypassed_payload_mismatch() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    malformed = object.__new__(
        codec.PaperAutonomousScreeningDecisionSupportGateDbRow,
    )
    for field_name, value in _row_values(row).items():
        object.__setattr__(malformed, field_name, value)
    object.__setattr__(malformed, "queue_source_report_count", 2)

    with pytest.raises(ValueError, match="queue_source_report_count"):
        codec.from_db_row(malformed)


def test_autonomous_screening_gate_from_db_row_rejects_bypassed_missing_payload_flags() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())
    payload = {
        key: value
        for key, value in row.payload_json.items()
        if key not in {"paper_only", "report_only", "readonly"}
    }
    malformed = object.__new__(
        codec.PaperAutonomousScreeningDecisionSupportGateDbRow,
    )
    for field_name, value in _row_values(row).items():
        object.__setattr__(malformed, field_name, value)
    object.__setattr__(
        malformed,
        "report_sha256",
        _canonical_payload_sha256(payload),
    )
    object.__setattr__(malformed, "payload_json", payload)

    with pytest.raises(ValueError, match="paper_only"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"gate_status": "paused"}, "gate_status"),
        ({"queue_source_report_count": True}, "queue_source_report_count"),
        ({"queue_total_ready_notional": Decimal("-1.000000")}, "queue_total_ready_notional"),
        ({"trend_source_snapshot_count": -1}, "trend_source_snapshot_count"),
        ({"rank_stability_status": "pass"}, "rank_stability_status"),
        ({"reason_codes_json": "reason"}, "reason_codes_json"),
        ({"reason_code_counts_json": {"reason_code": "reason"}}, "reason_code_counts_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_autonomous_screening_gate_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousScreeningDecisionSupportGateDbRow(
            **{**_row_values(row), **overrides},
        )


def test_autonomous_screening_gate_db_row_module_is_pure_codec() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row as codec

    assert codec.__name__.endswith("_db_row")
    source = Path(
        "src/polymarket_alpha_lab/"
        "paper_autonomous_screening_decision_support_gate_db_row.py",
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
