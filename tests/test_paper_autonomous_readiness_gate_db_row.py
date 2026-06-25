from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timezone, timedelta
import hashlib
import json
import re

import pytest

from polymarket_alpha_lab.paper_autonomous_readiness_gate import (
    ALLOCATION_SOURCE_NAME,
    INVESTMENT_LEDGER_SOURCE_NAME,
    SCREENING_SOURCE_NAME,
    PaperAutonomousReadinessGateReasonCodeCount,
    PaperAutonomousReadinessGateReport,
    PaperAutonomousReadinessGateSourceStatus,
)


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=-4))
SOURCE_GENERATED_AT = datetime(2026, 6, 25, 8, 0, tzinfo=SOURCE_TZ)
CONFIG_VERSION = "paper-autonomous-readiness-gate-test-v0"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def _codec_module():
    import polymarket_alpha_lab.paper_autonomous_readiness_gate_db_row as codec

    return codec


def _source_status(
    source_name: str,
    status: str,
    config_version: str,
) -> PaperAutonomousReadinessGateSourceStatus:
    return PaperAutonomousReadinessGateSourceStatus(
        source_name=source_name,
        status=status,
        recommended_next_step=f"review_{source_name}",
        generated_at=SOURCE_GENERATED_AT,
        config_version=config_version,
    )


def _report(
    *,
    config_version: str = CONFIG_VERSION,
    readiness_status: str = "watch",
    recommended_next_step: str = "throttle_paper_autonomous_readiness_review",
    source_statuses: tuple[PaperAutonomousReadinessGateSourceStatus, ...] | None = None,
    reason_codes: tuple[str, ...] = (
        "allocation_proposal_db_history_health_trend_gate_watch",
        "investment_ledger_db_history_health_trend_gate_pass",
        "screening_decision_support_gate_db_history_health_pass",
    ),
) -> PaperAutonomousReadinessGateReport:
    if source_statuses is None:
        source_statuses = (
            _source_status(
                SCREENING_SOURCE_NAME,
                "pass",
                "screening-health-v0",
            ),
            _source_status(
                ALLOCATION_SOURCE_NAME,
                "watch",
                "allocation-trend-gate-v0",
            ),
            _source_status(
                INVESTMENT_LEDGER_SOURCE_NAME,
                "pass",
                "ledger-trend-gate-v0",
            ),
        )
    return PaperAutonomousReadinessGateReport(
        generated_at=GENERATED_AT,
        config_version=config_version,
        readiness_status=readiness_status,
        recommended_next_step=recommended_next_step,
        source_statuses=source_statuses,
        source_config_versions=tuple(
            (row.source_name, row.config_version)
            for row in source_statuses
        ),
        reason_code_counts=tuple(
            PaperAutonomousReadinessGateReasonCodeCount(reason_code, 1)
            for reason_code in reason_codes
        ),
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
        pytest.fail("readiness gate DB JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_readiness_gate_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousReadinessGateDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == CONFIG_VERSION
    assert row.readiness_status == "watch"
    assert row.recommended_next_step == "throttle_paper_autonomous_readiness_review"
    assert row.source_statuses_json == [
        {
            "source_name": SCREENING_SOURCE_NAME,
            "status": "pass",
            "recommended_next_step": f"review_{SCREENING_SOURCE_NAME}",
            "generated_at": "2026-06-25T12:00:00+00:00",
            "config_version": "screening-health-v0",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "source_name": ALLOCATION_SOURCE_NAME,
            "status": "watch",
            "recommended_next_step": f"review_{ALLOCATION_SOURCE_NAME}",
            "generated_at": "2026-06-25T12:00:00+00:00",
            "config_version": "allocation-trend-gate-v0",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "source_name": INVESTMENT_LEDGER_SOURCE_NAME,
            "status": "pass",
            "recommended_next_step": f"review_{INVESTMENT_LEDGER_SOURCE_NAME}",
            "generated_at": "2026-06-25T12:00:00+00:00",
            "config_version": "ledger-trend-gate-v0",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.source_config_versions_json == [
        [SCREENING_SOURCE_NAME, "screening-health-v0"],
        [ALLOCATION_SOURCE_NAME, "allocation-trend-gate-v0"],
        [INVESTMENT_LEDGER_SOURCE_NAME, "ledger-trend-gate-v0"],
    ]
    assert row.reason_code_counts_json == [
        {
            "reason_code": "allocation_proposal_db_history_health_trend_gate_watch",
            "report_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_code": "investment_ledger_db_history_health_trend_gate_pass",
            "report_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_code": "screening_decision_support_gate_db_history_health_pass",
            "report_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.reason_codes_json == [
        "allocation_proposal_db_history_health_trend_gate_watch",
        "investment_ledger_db_history_health_trend_gate_pass",
        "screening_decision_support_gate_db_history_health_pass",
    ]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-25T12:00:00+00:00"
    assert row.payload_json["source_statuses"] == row.source_statuses_json
    assert row.payload_json["source_config_versions"] == row.source_config_versions_json
    assert row.payload_json["reason_code_counts"] == row.reason_code_counts_json
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    _assert_no_floats(row.source_statuses_json)
    _assert_no_floats(row.source_config_versions_json)
    _assert_no_floats(row.reason_code_counts_json)
    _assert_no_floats(row.reason_codes_json)
    _assert_no_floats(row.payload_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_autonomous_readiness_gate_report_to_db_row(report) == row
    assert codec.paper_autonomous_readiness_gate_report_from_db_row(row) == report
    assert codec.paper_autonomous_readiness_gate_to_db_row(report) == row
    assert codec.paper_autonomous_readiness_gate_from_db_row(row) == report


def test_readiness_gate_db_row_hash_is_deterministic_and_uses_full_payload() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperAutonomousReadinessGateReport(**report.__dict__)
    changed_report = _report(config_version="paper-autonomous-readiness-gate-test-v1")

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(changed_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_readiness_gate_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_readiness_gate_db_row_rejects_wrong_report_and_row_types() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperAutonomousReadinessGateReport"):
        codec.to_db_row(object())

    with pytest.raises(ValueError, match="PaperAutonomousReadinessGateDbRow"):
        codec.from_db_row(object())


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_readiness_gate_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_readiness_gate_db_row_rejects_false_nested_source_status_flags() -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report.source_statuses[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


def test_readiness_gate_db_row_rejects_corrupted_stored_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "source_statuses": [
            {**row.payload_json["source_statuses"][0], "paper_only": False},
            *row.payload_json["source_statuses"][1:],
        ],
    }
    malformed = codec.PaperAutonomousReadinessGateDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
            "source_statuses_json": payload["source_statuses"],
        },
    )

    with pytest.raises(ValueError, match="paper_only"):
        codec.from_db_row(malformed)


def test_readiness_gate_db_row_rejects_non_materialized_payload_hash_mismatch() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {**row.payload_json, "paper_only": False}
    malformed = codec.PaperAutonomousReadinessGateDbRow(
        **{**_row_values(row), "payload_json": payload},
    )

    with pytest.raises(ValueError, match="report_sha256"):
        codec.from_db_row(malformed)


def test_readiness_gate_db_row_rejects_recursive_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="source_statuses_json"):
        codec.PaperAutonomousReadinessGateDbRow(
            **{
                **_row_values(row),
                "source_statuses_json": [
                    {**row.source_statuses_json[0], "bad_float": 1.0},
                ],
            },
        )
    with pytest.raises(ValueError, match="source_config_versions_json"):
        codec.PaperAutonomousReadinessGateDbRow(
            **{
                **_row_values(row),
                "source_config_versions_json": [
                    [SCREENING_SOURCE_NAME, 1.0],
                ],
            },
        )
    with pytest.raises(ValueError, match="reason_code_counts_json"):
        codec.PaperAutonomousReadinessGateDbRow(
            **{
                **_row_values(row),
                "reason_code_counts_json": [
                    {**row.reason_code_counts_json[0], "report_count": 1.0},
                ],
            },
        )
    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperAutonomousReadinessGateDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad_float": 0.1}},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 25, 12, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-autonomous-readiness-gate-test-v1"}, "config_version"),
        ({"readiness_status": "pass"}, "readiness_status"),
        (
            {"recommended_next_step": "allow_paper_autonomous_readiness_review"},
            "recommended_next_step",
        ),
        ({"source_statuses_json": []}, "source_statuses_json"),
        ({"source_config_versions_json": []}, "source_config_versions_json"),
        ({"reason_code_counts_json": []}, "reason_code_counts_json"),
        (
            {
                "reason_codes_json": [
                    "allocation_proposal_db_history_health_trend_gate_pass",
                ],
            },
            "reason_codes_json",
        ),
    ),
)
def test_readiness_gate_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    malformed = codec.PaperAutonomousReadinessGateDbRow(
        **{**_row_values(row), **overrides},
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 25, 12, 0)}, "generated_at"),
        ({"config_version": " paper-autonomous-readiness-gate-test-v0"}, "config_version"),
        ({"readiness_status": "live"}, "readiness_status"),
        ({"source_statuses_json": "sources"}, "source_statuses_json"),
        ({"source_config_versions_json": "versions"}, "source_config_versions_json"),
        ({"reason_code_counts_json": "reasons"}, "reason_code_counts_json"),
        ({"reason_codes_json": [1]}, "reason_codes_json"),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
        ({"readonly": False}, "readonly"),
    ),
)
def test_readiness_gate_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousReadinessGateDbRow(
            **{**_row_values(row), **overrides},
        )
