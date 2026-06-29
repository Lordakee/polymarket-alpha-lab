from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
import re
import sys
import types

import pytest


GENERATED_AT = datetime(2026, 6, 29, 15, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=-4))
SOURCE_GENERATED_AT = datetime(2026, 6, 29, 8, 0, tzinfo=SOURCE_TZ)
LATEST_SOURCE_GENERATED_AT = datetime(2026, 6, 29, 10, 45, tzinfo=SOURCE_TZ)
CONFIG_VERSION = "paper-strategy-cycle-report-history-gate-test-v0"
SOURCE_CONFIG_VERSION = "paper-strategy-cycle-report-history-test-v0"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryGateReasonCodeCount:
    reason_code: str
    report_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class PaperStrategyCycleReportHistoryGateReport:
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    recommended_next_step: str
    reason_code_counts: tuple[
        PaperStrategyCycleReportHistoryGateReasonCodeCount,
        ...,
    ]
    source_history_status: str
    source_report_count: int
    latest_source_generated_at: datetime | None
    latest_source_age_seconds: int | None
    latest_snapshot_ready_share: Decimal
    blocked_market_share: Decimal
    latest_snapshot_ready_count: int
    latest_considered_count: int
    total_blocked_market_count: int
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _install_gate_module_if_missing() -> types.ModuleType:
    module_name = "polymarket_alpha_lab.paper_strategy_cycle_report_history_gate"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            raise

    module = types.ModuleType(module_name)
    module.PaperStrategyCycleReportHistoryGateReasonCodeCount = (
        PaperStrategyCycleReportHistoryGateReasonCodeCount
    )
    module.PaperStrategyCycleReportHistoryGateReport = (
        PaperStrategyCycleReportHistoryGateReport
    )
    sys.modules[module_name] = module
    return module


def _codec_module():
    _install_gate_module_if_missing()
    return importlib.import_module(
        "polymarket_alpha_lab.paper_strategy_cycle_report_history_gate_db_row",
    )


def _gate_classes() -> tuple[type, type]:
    gate_module = _install_gate_module_if_missing()
    return (
        gate_module.PaperStrategyCycleReportHistoryGateReport,
        gate_module.PaperStrategyCycleReportHistoryGateReasonCodeCount,
    )


def _report(
    *,
    config_version: str = CONFIG_VERSION,
    gate_status: str = "pass",
    source_history_status: str = "pass",
    recommended_next_step: str = "allow_strategy_cycle_history_gate",
    latest_source_generated_at: datetime | None = LATEST_SOURCE_GENERATED_AT,
    latest_source_age_seconds: int | None = 900,
    latest_snapshot_ready_share: Decimal = Decimal("0.875"),
    blocked_market_share: Decimal = Decimal("0.125"),
    reason_codes: tuple[str, ...] = (
        "paper_strategy_cycle_report_history_gate_passed",
    ),
):
    report_cls, reason_cls = _gate_classes()
    return report_cls(
        generated_at=GENERATED_AT,
        config_version=config_version,
        source_config_version=SOURCE_CONFIG_VERSION,
        source_generated_at=SOURCE_GENERATED_AT,
        gate_status=gate_status,
        recommended_next_step=recommended_next_step,
        reason_code_counts=tuple(reason_cls(reason_code, 1) for reason_code in reason_codes),
        source_history_status=source_history_status,
        source_report_count=8,
        latest_source_generated_at=latest_source_generated_at,
        latest_source_age_seconds=latest_source_age_seconds,
        latest_snapshot_ready_share=latest_snapshot_ready_share,
        blocked_market_share=blocked_market_share,
        latest_snapshot_ready_count=7,
        latest_considered_count=8,
        total_blocked_market_count=1,
        reason_codes=reason_codes,
    )


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


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
        pytest.fail("strategy cycle history gate DB JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


@pytest.mark.parametrize(
    (
        "gate_status",
        "source_history_status",
        "recommended_next_step",
        "latest_source_generated_at",
        "latest_source_age_seconds",
        "reason_codes",
    ),
    (
        (
            "pass",
            "pass",
            "allow_strategy_cycle_history_gate",
            LATEST_SOURCE_GENERATED_AT,
            900,
            ("paper_strategy_cycle_report_history_gate_passed",),
        ),
        (
            "watch",
            "watch",
            "throttle_strategy_cycle_history_gate",
            LATEST_SOURCE_GENERATED_AT,
            900,
            ("source_strategy_cycle_report_history_watch",),
        ),
        (
            "blocked",
            "blocked",
            "block_strategy_cycle_history_gate",
            None,
            None,
            (
                "missing_latest_strategy_cycle_report_history_timestamp",
                "source_strategy_cycle_report_history_blocked",
            ),
        ),
    ),
)
def test_strategy_cycle_history_gate_db_row_round_trips_gate_reports(
    gate_status: str,
    source_history_status: str,
    recommended_next_step: str,
    latest_source_generated_at: datetime | None,
    latest_source_age_seconds: int | None,
    reason_codes: tuple[str, ...],
) -> None:
    codec = _codec_module()
    report = _report(
        gate_status=gate_status,
        source_history_status=source_history_status,
        recommended_next_step=recommended_next_step,
        latest_source_generated_at=latest_source_generated_at,
        latest_source_age_seconds=latest_source_age_seconds,
        reason_codes=reason_codes,
    )

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperStrategyCycleReportHistoryGateDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.source_generated_at == datetime(2026, 6, 29, 12, 0, tzinfo=UTC)
    if latest_source_generated_at is None:
        assert row.latest_source_generated_at is None
    else:
        assert row.latest_source_generated_at == datetime(
            2026,
            6,
            29,
            14,
            45,
            tzinfo=UTC,
        )
    assert row.config_version == CONFIG_VERSION
    assert row.source_config_version == SOURCE_CONFIG_VERSION
    assert row.gate_status == gate_status
    assert row.recommended_next_step == recommended_next_step
    assert row.reason_code_counts_json == [
        {
            "reason_code": reason_code,
            "report_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        for reason_code in reason_codes
    ]
    assert row.source_history_status == source_history_status
    assert row.source_report_count == 8
    assert row.latest_source_age_seconds == latest_source_age_seconds
    assert row.latest_snapshot_ready_share == Decimal("0.875")
    assert row.blocked_market_share == Decimal("0.125")
    assert row.latest_snapshot_ready_count == 7
    assert row.latest_considered_count == 8
    assert row.total_blocked_market_count == 1
    assert row.reason_codes_json == list(reason_codes)
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-29T15:00:00+00:00"
    assert row.payload_json["source_generated_at"] == "2026-06-29T12:00:00+00:00"
    assert row.payload_json["latest_snapshot_ready_share"] == "0.875"
    assert row.payload_json["blocked_market_share"] == "0.125"
    assert row.payload_json["reason_code_counts"] == row.reason_code_counts_json
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    _assert_no_floats(row.reason_code_counts_json)
    _assert_no_floats(row.reason_codes_json)
    _assert_no_floats(row.payload_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_strategy_cycle_report_history_gate_report_to_db_row(report) == row
    assert codec.paper_strategy_cycle_report_history_gate_report_from_db_row(row) == report
    assert codec.paper_strategy_cycle_report_history_gate_to_db_row(report) == row
    assert codec.paper_strategy_cycle_report_history_gate_from_db_row(row) == report


def test_strategy_cycle_history_gate_db_row_hash_is_deterministic() -> None:
    codec = _codec_module()
    report = _report()
    report_cls, _ = _gate_classes()
    same_report = report_cls(**report.__dict__)
    changed_report = _report(config_version="paper-strategy-cycle-report-history-gate-test-v1")

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(changed_report)

    assert first.payload_json == second.payload_json
    assert first.report_sha256 == second.report_sha256
    assert first.report_sha256 != third.report_sha256


def test_strategy_cycle_history_gate_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_strategy_cycle_history_gate_db_row_rejects_wrong_report_and_row_types() -> None:
    codec = _codec_module()
    report = _report()
    report_cls, _ = _gate_classes()

    class ReportSubclass(report_cls):
        pass

    class RowSubclass(codec.PaperStrategyCycleReportHistoryGateDbRow):
        pass

    with pytest.raises(ValueError, match="PaperStrategyCycleReportHistoryGateReport"):
        codec.to_db_row(object())
    with pytest.raises(ValueError, match="PaperStrategyCycleReportHistoryGateReport"):
        codec.to_db_row(ReportSubclass(**report.__dict__))

    row = codec.to_db_row(report)
    with pytest.raises(ValueError, match="PaperStrategyCycleReportHistoryGateDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperStrategyCycleReportHistoryGateDbRow"):
        codec.from_db_row(RowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_strategy_cycle_history_gate_db_row_rejects_false_report_flags(
    flag_name: str,
) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_strategy_cycle_history_gate_db_row_rejects_false_nested_reason_flags() -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report.reason_code_counts[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


def test_strategy_cycle_history_gate_db_row_rejects_corrupted_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "reason_code_counts": [
            {**row.payload_json["reason_code_counts"][0], "paper_only": False},
        ],
    }

    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperStrategyCycleReportHistoryGateDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "reason_code_counts_json": payload["reason_code_counts"],
                "payload_json": payload,
            },
        )


def test_strategy_cycle_history_gate_from_db_row_rejects_bypassed_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "reason_code_counts": [
            {**row.payload_json["reason_code_counts"][0], "readonly": False},
        ],
    }
    malformed = object.__new__(codec.PaperStrategyCycleReportHistoryGateDbRow)
    for key, value in {
        **_row_values(row),
        "report_sha256": _canonical_payload_sha256(payload),
        "reason_code_counts_json": payload["reason_code_counts"],
        "payload_json": payload,
    }.items():
        object.__setattr__(malformed, key, value)

    with pytest.raises(ValueError, match="readonly"):
        codec.from_db_row(malformed)


def test_strategy_cycle_history_gate_db_row_rejects_payload_hash_mismatch() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {**row.payload_json, "config_version": "changed"}

    with pytest.raises(ValueError, match="report_sha256"):
        codec.PaperStrategyCycleReportHistoryGateDbRow(
            **{**_row_values(row), "payload_json": payload},
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_strategy_cycle_history_gate_db_row_rejects_payload_flag_mismatches(
    flag_name: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {**row.payload_json, flag_name: False}

    with pytest.raises(ValueError, match=flag_name):
        codec.PaperStrategyCycleReportHistoryGateDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_strategy_cycle_history_gate_db_row_rejects_recursive_json_floats() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="reason_code_counts_json"):
        codec.PaperStrategyCycleReportHistoryGateDbRow(
            **{
                **_row_values(row),
                "reason_code_counts_json": [
                    {**row.reason_code_counts_json[0], "report_count": 1.0},
                ],
            },
        )

    payload = {**row.payload_json, "latest_snapshot_ready_share": 0.875}
    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperStrategyCycleReportHistoryGateDbRow(
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
        ({"generated_at": datetime(2026, 6, 29, 15, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-strategy-cycle-report-history-gate-test-v1"}, "config_version"),
        ({"source_config_version": "paper-strategy-cycle-report-history-test-v1"}, "source_config_version"),
        ({"source_generated_at": datetime(2026, 6, 29, 12, 1, tzinfo=UTC)}, "source_generated_at"),
        ({"gate_status": "watch"}, "gate_status"),
        ({"recommended_next_step": "throttle_strategy_cycle_history_gate"}, "recommended_next_step"),
        ({"reason_code_counts_json": []}, "reason_code_counts_json"),
        ({"source_history_status": "watch"}, "source_history_status"),
        ({"source_report_count": 9}, "source_report_count"),
        ({"latest_source_generated_at": None}, "latest_source_generated_at"),
        ({"latest_source_age_seconds": 901}, "latest_source_age_seconds"),
        ({"latest_snapshot_ready_share": Decimal("0.750")}, "latest_snapshot_ready_share"),
        ({"blocked_market_share": Decimal("0.250")}, "blocked_market_share"),
        ({"latest_snapshot_ready_count": 6}, "latest_snapshot_ready_count"),
        ({"latest_considered_count": 9}, "latest_considered_count"),
        ({"total_blocked_market_count": 2}, "total_blocked_market_count"),
        ({"reason_codes_json": ["source_strategy_cycle_report_history_watch"]}, "reason_codes_json"),
    ),
)
def test_strategy_cycle_history_gate_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperStrategyCycleReportHistoryGateDbRow(
            **{**_row_values(row), **overrides},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 29, 15, 0)}, "generated_at"),
        ({"config_version": " paper-strategy-cycle-report-history-gate-test-v0"}, "config_version"),
        ({"source_config_version": ""}, "source_config_version"),
        ({"source_generated_at": datetime(2026, 6, 29, 12, 0)}, "source_generated_at"),
        ({"gate_status": "live"}, "gate_status"),
        ({"recommended_next_step": ""}, "recommended_next_step"),
        ({"reason_code_counts_json": "reasons"}, "reason_code_counts_json"),
        ({"source_history_status": "live"}, "source_history_status"),
        ({"source_report_count": -1}, "source_report_count"),
        ({"latest_source_generated_at": datetime(2026, 6, 29, 14, 45)}, "latest_source_generated_at"),
        ({"latest_source_age_seconds": -1}, "latest_source_age_seconds"),
        ({"latest_snapshot_ready_share": 0.875}, "latest_snapshot_ready_share"),
        ({"blocked_market_share": Decimal("1.001")}, "blocked_market_share"),
        ({"latest_snapshot_ready_count": -1}, "latest_snapshot_ready_count"),
        ({"latest_considered_count": -1}, "latest_considered_count"),
        ({"total_blocked_market_count": -1}, "total_blocked_market_count"),
        ({"reason_codes_json": [1]}, "reason_codes_json"),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
        ({"readonly": False}, "readonly"),
    ),
)
def test_strategy_cycle_history_gate_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperStrategyCycleReportHistoryGateDbRow(
            **{**_row_values(row), **overrides},
        )
